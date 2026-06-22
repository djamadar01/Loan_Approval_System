"""
Comprehensive batch processing system with queue management, progress tracking,
parallel processing, and results export capabilities.
"""

import json
import csv
import queue
import threading
import time
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import traceback
from collections import defaultdict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"


class ExportFormat(Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


@dataclass
class BatchJob:
    """Represents a single batch job."""
    job_id: str
    task_data: Any
    status: JobStatus = JobStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for export."""
        return {
            "job_id": self.job_id,
            "task_data": str(self.task_data),
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "retry_count": self.retry_count,
            "duration_seconds": (self.end_time - self.start_time).total_seconds()
            if self.start_time and self.end_time else None,
            "metadata": self.metadata,
        }

    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class BatchProgress:
    """Tracks batch processing progress."""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    skipped_jobs: int = 0
    pending_jobs: int = 0
    running_jobs: int = 0
    total_retries: int = 0
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None

    def get_completion_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_jobs == 0:
            return 0.0
        return (self.completed_jobs + self.failed_jobs + self.skipped_jobs) / self.total_jobs * 100

    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        finished = self.completed_jobs + self.failed_jobs + self.skipped_jobs
        if finished == 0:
            return 0.0
        return self.completed_jobs / finished * 100

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0

    def get_estimated_time_remaining(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        elapsed = self.get_elapsed_time()
        if elapsed == 0 or self.completed_jobs == 0:
            return None
        avg_time_per_job = elapsed / self.completed_jobs
        remaining_jobs = self.total_jobs - self.completed_jobs
        return avg_time_per_job * remaining_jobs

    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary."""
        return {
            "total_jobs": self.total_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "skipped_jobs": self.skipped_jobs,
            "pending_jobs": self.pending_jobs,
            "running_jobs": self.running_jobs,
            "total_retries": self.total_retries,
            "completion_percentage": self.get_completion_percentage(),
            "success_rate": self.get_success_rate(),
            "elapsed_time_seconds": self.get_elapsed_time(),
            "estimated_time_remaining_seconds": self.get_estimated_time_remaining(),
        }


class ErrorRecoveryStrategy:
    """Handles error recovery and retry logic."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        """Initialize error recovery strategy.

        Args:
            max_retries: Maximum number of retries
            backoff_factor: Exponential backoff multiplier
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def should_retry(self, job: BatchJob, error: Exception) -> bool:
        """Determine if a job should be retried.

        Args:
            job: The failed job
            error: The exception that occurred

        Returns:
            Whether to retry the job
        """
        if job.retry_count >= self.max_retries:
            return False

        # Retry on transient errors
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            RuntimeError,
        )
        return isinstance(error, retryable_errors)

    def get_backoff_delay(self, retry_count: int) -> float:
        """Calculate backoff delay in seconds.

        Args:
            retry_count: Number of retries attempted

        Returns:
            Delay in seconds
        """
        return self.backoff_factor ** retry_count


class BatchProcessor:
    """Main batch processing system."""

    def __init__(
        self,
        worker_count: int = 4,
        use_multiprocessing: bool = False,
        queue_maxsize: int = 1000,
        error_recovery: Optional[ErrorRecoveryStrategy] = None,
    ):
        """Initialize batch processor.

        Args:
            worker_count: Number of parallel workers
            use_multiprocessing: Use multiprocessing (True) or threading (False)
            queue_maxsize: Maximum queue size
            error_recovery: Error recovery strategy instance
        """
        self.worker_count = worker_count
        self.use_multiprocessing = use_multiprocessing
        self.job_queue: queue.Queue = queue.Queue(maxsize=queue_maxsize)
        self.results: Dict[str, BatchJob] = {}
        self.progress = BatchProgress()
        self.error_recovery = error_recovery or ErrorRecoveryStrategy()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.workers: List[threading.Thread] = []
        self.job_counter = 0

    def submit_job(self, task_data: Any, job_id: Optional[str] = None, **metadata) -> str:
        """Submit a job to the batch queue.

        Args:
            task_data: Data to process
            job_id: Optional job ID (auto-generated if not provided)
            **metadata: Additional metadata for the job

        Returns:
            Job ID
        """
        if job_id is None:
            with self.lock:
                self.job_counter += 1
                job_id = f"job_{self.job_counter:06d}"

        job = BatchJob(
            job_id=job_id,
            task_data=task_data,
            metadata=metadata,
        )

        self.job_queue.put(job)

        with self.lock:
            self.progress.total_jobs += 1
            self.progress.pending_jobs += 1

        logger.info(f"Job submitted: {job_id}")
        return job_id

    def submit_batch(self, tasks: List[Any], job_ids: Optional[List[str]] = None) -> List[str]:
        """Submit multiple jobs as a batch.

        Args:
            tasks: List of task data
            job_ids: Optional list of job IDs

        Returns:
            List of submitted job IDs
        """
        submitted_ids = []
        for i, task in enumerate(tasks):
            job_id = job_ids[i] if job_ids and i < len(job_ids) else None
            submitted_ids.append(self.submit_job(task, job_id))
        return submitted_ids

    def process_with_function(
        self,
        func: Callable[[Any], Any],
        max_workers: Optional[int] = None,
    ) -> None:
        """Process all queued jobs using provided function.

        Args:
            func: Function to process each job
            max_workers: Override worker count
        """
        workers = max_workers or self.worker_count

        if self.use_multiprocessing:
            self._process_with_multiprocessing(func, workers)
        else:
            self._process_with_threading(func, workers)

    def _process_with_threading(self, func: Callable[[Any], Any], workers: int) -> None:
        """Process jobs using threading.

        Args:
            func: Function to process each job
            workers: Number of worker threads
        """
        self.progress.start_time = datetime.now()
        self.stop_event.clear()

        def worker():
            while not self.stop_event.is_set():
                try:
                    job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    if self.job_queue.empty():
                        break
                    continue

                self._execute_job(job, func)
                self.job_queue.task_done()

        worker_threads = [
            threading.Thread(target=worker, daemon=False)
            for _ in range(workers)
        ]

        for thread in worker_threads:
            thread.start()

        for thread in worker_threads:
            thread.join()

        logger.info("All jobs processed (threading)")

    def _process_with_multiprocessing(self, func: Callable[[Any], Any], workers: int) -> None:
        """Process jobs using multiprocessing.

        Args:
            func: Function to process each job
            workers: Number of worker processes
        """
        self.progress.start_time = datetime.now()

        jobs_to_process = []
        while not self.job_queue.empty():
            try:
                jobs_to_process.append(self.job_queue.get_nowait())
            except queue.Empty:
                break

        if not jobs_to_process:
            logger.warning("No jobs to process")
            return

        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._execute_job_wrapper, job, func): job
                for job in jobs_to_process
            }

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Worker error: {e}")

        logger.info("All jobs processed (multiprocessing)")

    @staticmethod
    def _execute_job_wrapper(job: BatchJob, func: Callable[[Any], Any]) -> None:
        """Wrapper for multiprocessing job execution.

        Args:
            job: Job to execute
            func: Function to execute
        """
        # Note: In multiprocessing, state updates need to be handled via queues
        # This is a simplified version; production code would use proper IPC
        try:
            job.result = func(job.task_data)
            job.status = JobStatus.COMPLETED
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)

    def _execute_job(self, job: BatchJob, func: Callable[[Any], Any]) -> None:
        """Execute a single job with error recovery.

        Args:
            job: Job to execute
            func: Function to execute
        """
        with self.lock:
            self.progress.pending_jobs -= 1
            self.progress.running_jobs += 1

        job.start_time = datetime.now()
        job.status = JobStatus.RUNNING

        try:
            job.result = func(job.task_data)
            job.status = JobStatus.COMPLETED

            with self.lock:
                self.progress.completed_jobs += 1
                self.progress.last_update = datetime.now()

            logger.info(f"Job completed: {job.job_id}")

        except Exception as e:
            logger.error(f"Job failed: {job.job_id} - {str(e)}")
            job.error = traceback.format_exc()

            if self.error_recovery.should_retry(job, e):
                job.retry_count += 1
                job.status = JobStatus.RETRY

                with self.lock:
                    self.progress.total_retries += 1
                    self.progress.pending_jobs += 1

                backoff = self.error_recovery.get_backoff_delay(job.retry_count - 1)
                logger.info(f"Retrying job {job.job_id} in {backoff}s (attempt {job.retry_count})")

                time.sleep(backoff)
                self.job_queue.put(job)

            else:
                job.status = JobStatus.FAILED

                with self.lock:
                    self.progress.failed_jobs += 1

        finally:
            job.end_time = datetime.now()

            with self.lock:
                self.progress.running_jobs -= 1
                self.results[job.job_id] = job

    def get_progress(self) -> BatchProgress:
        """Get current batch progress.

        Returns:
            BatchProgress instance
        """
        with self.lock:
            return BatchProgress(
                total_jobs=self.progress.total_jobs,
                completed_jobs=self.progress.completed_jobs,
                failed_jobs=self.progress.failed_jobs,
                skipped_jobs=self.progress.skipped_jobs,
                pending_jobs=self.progress.pending_jobs,
                running_jobs=self.progress.running_jobs,
                total_retries=self.progress.total_retries,
                start_time=self.progress.start_time,
                last_update=self.progress.last_update,
            )

    def get_job_result(self, job_id: str) -> Optional[BatchJob]:
        """Get result for a specific job.

        Args:
            job_id: Job ID

        Returns:
            BatchJob instance or None if not found
        """
        with self.lock:
            return self.results.get(job_id)

    def get_all_results(self) -> Dict[str, BatchJob]:
        """Get all job results.

        Returns:
            Dictionary of job ID to BatchJob
        """
        with self.lock:
            return dict(self.results)

    def get_failed_jobs(self) -> Dict[str, BatchJob]:
        """Get all failed jobs.

        Returns:
            Dictionary of failed job ID to BatchJob
        """
        with self.lock:
            return {
                job_id: job
                for job_id, job in self.results.items()
                if job.status == JobStatus.FAILED
            }

    def export_results(
        self,
        output_path: Union[str, Path],
        format: ExportFormat = ExportFormat.JSON,
        include_metadata: bool = True,
    ) -> Path:
        """Export results to file.

        Args:
            output_path: Output file path
            format: Export format (CSV, JSON, or Parquet)
            include_metadata: Include metadata in export

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with self.lock:
            data = [job.to_dict() for job in self.results.values()]

        if format == ExportFormat.JSON:
            return self._export_json(output_path, data)
        elif format == ExportFormat.CSV:
            return self._export_csv(output_path, data)
        elif format == ExportFormat.PARQUET:
            return self._export_parquet(output_path, data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self, output_path: Path, data: List[Dict[str, Any]]) -> Path:
        """Export results as JSON.

        Args:
            output_path: Output file path
            data: Data to export

        Returns:
            Path to exported file
        """
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Results exported to JSON: {output_path}")
        return output_path

    def _export_csv(self, output_path: Path, data: List[Dict[str, Any]]) -> Path:
        """Export results as CSV.

        Args:
            output_path: Output file path
            data: Data to export

        Returns:
            Path to exported file
        """
        if not data:
            logger.warning("No data to export")
            return output_path

        fieldnames = data[0].keys()
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Results exported to CSV: {output_path}")
        return output_path

    def _export_parquet(self, output_path: Path, data: List[Dict[str, Any]]) -> Path:
        """Export results as Parquet.

        Args:
            output_path: Output file path
            data: Data to export

        Returns:
            Path to exported file
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for Parquet export")

        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError("pyarrow required for Parquet export")

        # Convert complex types to strings for Parquet compatibility
        processed_data = []
        for row in data:
            processed_row = {}
            for key, value in row.items():
                if isinstance(value, (dict, list)):
                    processed_row[key] = str(value)
                else:
                    processed_row[key] = value
            processed_data.append(processed_row)

        df = pd.DataFrame(processed_data)
        df.to_parquet(output_path)

        logger.info(f"Results exported to Parquet: {output_path}")
        return output_path

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary of statistics
        """
        progress = self.get_progress()
        results = self.get_all_results()

        durations = [job.get_duration() for job in results.values() if job.get_duration()]

        return {
            "progress": progress.to_dict(),
            "total_duration_seconds": progress.get_elapsed_time(),
            "average_job_duration_seconds": sum(durations) / len(durations)
            if durations else 0,
            "min_job_duration_seconds": min(durations) if durations else 0,
            "max_job_duration_seconds": max(durations) if durations else 0,
            "jobs_by_status": self._get_jobs_by_status(),
        }

    def _get_jobs_by_status(self) -> Dict[str, int]:
        """Get count of jobs by status.

        Returns:
            Dictionary of status to count
        """
        status_counts = defaultdict(int)
        with self.lock:
            for job in self.results.values():
                status_counts[job.status.value] += 1
        return dict(status_counts)

    def print_progress(self) -> str:
        """Get formatted progress string.

        Returns:
            Formatted progress string
        """
        progress = self.get_progress()
        elapsed = progress.get_elapsed_time()
        estimated_remaining = progress.get_estimated_time_remaining()

        return (
            f"Progress: {progress.completed_jobs}/{progress.total_jobs} "
            f"({progress.get_completion_percentage():.1f}%) | "
            f"Success: {progress.get_success_rate():.1f}% | "
            f"Elapsed: {elapsed:.1f}s | "
            f"ETA: {estimated_remaining:.1f}s" if estimated_remaining else "N/A"
        )

    def stop(self) -> None:
        """Stop all workers."""
        self.stop_event.set()
        logger.info("Stop signal sent to workers")


def example_worker_function(task_data: Any) -> Any:
    """Example worker function for demonstration.

    Args:
        task_data: Input data

    Returns:
        Processed result
    """
    time.sleep(0.1)  # Simulate processing
    if isinstance(task_data, dict):
        return {
            "input": task_data,
            "processed_at": datetime.now().isoformat(),
            "result": task_data.get("value", 0) * 2,
        }
    return {"input": task_data, "result": str(task_data).upper()}


if __name__ == "__main__":
    # Example usage
    print("=== Batch Processing System Demo ===\n")

    # Create processor
    processor = BatchProcessor(worker_count=4, use_multiprocessing=False)

    # Submit sample jobs
    print("Submitting batch jobs...")
    sample_tasks = [
        {"id": i, "value": i * 10} for i in range(20)
    ]
    job_ids = processor.submit_batch(sample_tasks)
    print(f"Submitted {len(job_ids)} jobs\n")

    # Process jobs
    print("Processing jobs...")
    processor.process_with_function(example_worker_function)

    # Get and display statistics
    stats = processor.get_statistics()
    print(f"\n=== Processing Statistics ===")
    print(f"Total jobs: {stats['progress']['total_jobs']}")
    print(f"Completed: {stats['progress']['completed_jobs']}")
    print(f"Failed: {stats['progress']['failed_jobs']}")
    print(f"Success rate: {stats['progress']['success_rate']:.1f}%")
    print(f"Total duration: {stats['total_duration_seconds']:.2f}s")
    print(f"Average job duration: {stats['average_job_duration_seconds']:.3f}s")

    # Export results
    print("\n=== Exporting Results ===")
    output_dir = Path("/home/ubuntu/Desktop/demo/batch_results")

    json_path = processor.export_results(
        output_dir / "results.json",
        format=ExportFormat.JSON,
    )
    print(f"JSON export: {json_path}")

    csv_path = processor.export_results(
        output_dir / "results.csv",
        format=ExportFormat.CSV,
    )
    print(f"CSV export: {csv_path}")

    try:
        parquet_path = processor.export_results(
            output_dir / "results.parquet",
            format=ExportFormat.PARQUET,
        )
        print(f"Parquet export: {parquet_path}")
    except ImportError as e:
        print(f"Parquet export skipped: {e}")

    print("\n=== Sample Results ===")
    for job_id, job in list(processor.get_all_results().items())[:3]:
        print(f"\nJob ID: {job_id}")
        print(f"Status: {job.status.value}")
        print(f"Result: {job.result}")
        print(f"Duration: {job.get_duration():.3f}s")
