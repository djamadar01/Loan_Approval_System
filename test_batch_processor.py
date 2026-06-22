"""
Comprehensive test suite for batch processing system.
Demonstrates all features including queue management, progress tracking,
parallel processing, error recovery, and results export.
"""

import pytest
import tempfile
import time
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from batch_processor import (
    BatchProcessor,
    BatchJob,
    BatchProgress,
    JobStatus,
    ExportFormat,
    ErrorRecoveryStrategy,
)


class TestBatchJob:
    """Tests for BatchJob class."""

    def test_job_creation(self):
        """Test creating a batch job."""
        job = BatchJob(job_id="test_1", task_data={"key": "value"})
        assert job.job_id == "test_1"
        assert job.task_data == {"key": "value"}
        assert job.status == JobStatus.PENDING
        assert job.result is None

    def test_job_to_dict(self):
        """Test converting job to dictionary."""
        job = BatchJob(
            job_id="test_1",
            task_data={"key": "value"},
            status=JobStatus.COMPLETED,
            result="success",
        )
        job.start_time = datetime(2026, 1, 1, 12, 0, 0)
        job.end_time = datetime(2026, 1, 1, 12, 0, 5)

        job_dict = job.to_dict()
        assert job_dict["job_id"] == "test_1"
        assert job_dict["status"] == "completed"
        assert job_dict["result"] == "success"
        assert job_dict["duration_seconds"] == 5.0

    def test_job_duration(self):
        """Test getting job duration."""
        job = BatchJob(job_id="test_1", task_data="data")
        job.start_time = datetime(2026, 1, 1, 12, 0, 0)
        job.end_time = datetime(2026, 1, 1, 12, 0, 3)

        assert job.get_duration() == 3.0

    def test_job_duration_incomplete(self):
        """Test duration for incomplete job."""
        job = BatchJob(job_id="test_1", task_data="data")
        assert job.get_duration() is None


class TestBatchProgress:
    """Tests for BatchProgress class."""

    def test_progress_creation(self):
        """Test creating batch progress."""
        progress = BatchProgress(total_jobs=100)
        assert progress.total_jobs == 100
        assert progress.completed_jobs == 0

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        progress = BatchProgress(total_jobs=100)
        progress.completed_jobs = 50
        assert progress.get_completion_percentage() == 50.0

    def test_completion_percentage_zero(self):
        """Test completion percentage when no jobs."""
        progress = BatchProgress(total_jobs=0)
        assert progress.get_completion_percentage() == 0.0

    def test_success_rate(self):
        """Test success rate calculation."""
        progress = BatchProgress(total_jobs=100)
        progress.completed_jobs = 80
        progress.failed_jobs = 20
        assert progress.get_success_rate() == 80.0

    def test_success_rate_no_finished_jobs(self):
        """Test success rate with no finished jobs."""
        progress = BatchProgress(total_jobs=100)
        assert progress.get_success_rate() == 0.0

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        progress = BatchProgress()
        progress.start_time = datetime.now()
        time.sleep(0.1)
        elapsed = progress.get_elapsed_time()
        assert elapsed >= 0.1

    def test_estimated_time_remaining(self):
        """Test ETA calculation."""
        progress = BatchProgress(total_jobs=100)
        progress.start_time = datetime.now()
        progress.completed_jobs = 50
        time.sleep(0.1)

        eta = progress.get_estimated_time_remaining()
        assert eta is not None
        assert eta > 0


class TestErrorRecoveryStrategy:
    """Tests for ErrorRecoveryStrategy class."""

    def test_should_retry_transient_error(self):
        """Test retry on transient error."""
        strategy = ErrorRecoveryStrategy(max_retries=3)
        job = BatchJob(job_id="test_1", task_data="data", retry_count=0)
        error = ConnectionError("Connection failed")

        assert strategy.should_retry(job, error) is True

    def test_should_not_retry_max_attempts(self):
        """Test no retry when max attempts reached."""
        strategy = ErrorRecoveryStrategy(max_retries=3)
        job = BatchJob(job_id="test_1", task_data="data", retry_count=3)
        error = ConnectionError("Connection failed")

        assert strategy.should_retry(job, error) is False

    def test_backoff_delay(self):
        """Test exponential backoff calculation."""
        strategy = ErrorRecoveryStrategy(backoff_factor=2.0)
        assert strategy.get_backoff_delay(0) == 1.0
        assert strategy.get_backoff_delay(1) == 2.0
        assert strategy.get_backoff_delay(2) == 4.0


class TestBatchProcessor:
    """Tests for BatchProcessor class."""

    def test_processor_creation(self):
        """Test creating batch processor."""
        processor = BatchProcessor(worker_count=4)
        assert processor.worker_count == 4
        assert processor.progress.total_jobs == 0

    def test_submit_single_job(self):
        """Test submitting a single job."""
        processor = BatchProcessor()
        job_id = processor.submit_job({"data": "test"})

        assert job_id is not None
        assert processor.progress.total_jobs == 1
        assert processor.progress.pending_jobs == 1

    def test_submit_job_with_custom_id(self):
        """Test submitting job with custom ID."""
        processor = BatchProcessor()
        job_id = processor.submit_job({"data": "test"}, job_id="custom_123")

        assert job_id == "custom_123"

    def test_submit_batch(self):
        """Test submitting batch of jobs."""
        processor = BatchProcessor()
        tasks = [{"id": i} for i in range(10)]
        job_ids = processor.submit_batch(tasks)

        assert len(job_ids) == 10
        assert processor.progress.total_jobs == 10

    def test_submit_batch_with_ids(self):
        """Test submitting batch with custom IDs."""
        processor = BatchProcessor()
        tasks = [{"id": i} for i in range(5)]
        custom_ids = [f"job_{i}" for i in range(5)]
        job_ids = processor.submit_batch(tasks, custom_ids)

        assert job_ids == custom_ids

    def test_get_progress(self):
        """Test getting progress."""
        processor = BatchProcessor()
        processor.submit_job({"data": "test"})
        progress = processor.get_progress()

        assert progress.total_jobs == 1
        assert progress.pending_jobs == 1

    def test_get_job_result_not_found(self):
        """Test getting result for non-existent job."""
        processor = BatchProcessor()
        result = processor.get_job_result("nonexistent")
        assert result is None

    def test_process_simple_function(self):
        """Test processing with simple function."""
        processor = BatchProcessor(worker_count=2)

        # Submit jobs
        tasks = [{"value": i} for i in range(5)]
        processor.submit_batch(tasks)

        # Define processing function
        def process_fn(task):
            return {"result": task["value"] * 2}

        # Process
        processor.process_with_function(process_fn)

        # Verify results
        results = processor.get_all_results()
        assert len(results) == 5
        assert all(job.status == JobStatus.COMPLETED for job in results.values())
        assert all(job.result["result"] % 2 == 0 for job in results.values())

    def test_process_with_failure(self):
        """Test processing with failures."""
        processor = BatchProcessor(worker_count=2)

        # Submit jobs
        processor.submit_job({"value": 1})
        processor.submit_job({"value": "invalid"})  # Will fail

        # Define processing function that fails on invalid data
        def process_fn(task):
            return {"result": int(task["value"]) * 2}

        # Process
        processor.process_with_function(process_fn)

        # Verify results
        results = processor.get_all_results()
        failed = processor.get_failed_jobs()

        assert len(results) == 2
        assert len(failed) == 1
        assert list(failed.values())[0].error is not None

    def test_get_statistics(self):
        """Test getting statistics."""
        processor = BatchProcessor(worker_count=2)

        # Submit and process jobs
        processor.submit_batch([{"value": i} for i in range(5)])

        def process_fn(task):
            time.sleep(0.01)
            return {"result": task["value"]}

        processor.process_with_function(process_fn)

        stats = processor.get_statistics()
        assert "progress" in stats
        assert "total_duration_seconds" in stats
        assert "average_job_duration_seconds" in stats
        assert "jobs_by_status" in stats

    def test_print_progress(self):
        """Test progress string formatting."""
        processor = BatchProcessor()
        processor.submit_batch([{"value": i} for i in range(10)])

        progress_str = processor.print_progress()
        assert "Progress:" in progress_str
        assert "Success:" in progress_str


class TestExportFunctionality:
    """Tests for export functionality."""

    def test_export_json(self):
        """Test exporting to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BatchProcessor()
            processor.submit_batch([{"id": i} for i in range(3)])

            def process_fn(task):
                return {"result": task["id"] * 2}

            processor.process_with_function(process_fn)

            output_path = Path(tmpdir) / "results.json"
            processor.export_results(output_path, format=ExportFormat.JSON)

            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
            assert len(data) == 3

    def test_export_csv(self):
        """Test exporting to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BatchProcessor()
            processor.submit_batch([{"id": i} for i in range(3)])

            def process_fn(task):
                return {"result": task["id"] * 2}

            processor.process_with_function(process_fn)

            output_path = Path(tmpdir) / "results.csv"
            processor.export_results(output_path, format=ExportFormat.CSV)

            assert output_path.exists()
            with open(output_path) as f:
                lines = f.readlines()
            assert len(lines) == 4  # Header + 3 data rows

    def test_export_creates_directory(self):
        """Test that export creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BatchProcessor()
            processor.submit_job({"data": "test"})

            def process_fn(task):
                return {"result": "processed"}

            processor.process_with_function(process_fn)

            output_path = Path(tmpdir) / "nested" / "dir" / "results.json"
            processor.export_results(output_path, format=ExportFormat.JSON)

            assert output_path.parent.exists()
            assert output_path.exists()


class TestErrorRecovery:
    """Tests for error recovery and retry logic."""

    def test_retry_on_connection_error(self):
        """Test retry on connection error."""
        processor = BatchProcessor(worker_count=1)
        error_recovery = ErrorRecoveryStrategy(max_retries=2)
        processor.error_recovery = error_recovery

        call_count = {"count": 0}

        def failing_process_fn(task):
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ConnectionError("Network error")
            return {"result": "success"}

        processor.submit_job({"data": "test"})
        processor.process_with_function(failing_process_fn)

        results = processor.get_all_results()
        job = list(results.values())[0]
        assert job.status == JobStatus.COMPLETED
        assert job.retry_count >= 2

    def test_max_retries_exceeded(self):
        """Test that job fails after max retries."""
        processor = BatchProcessor(worker_count=1)
        error_recovery = ErrorRecoveryStrategy(max_retries=2)
        processor.error_recovery = error_recovery

        def always_failing_fn(task):
            raise ConnectionError("Network error")

        processor.submit_job({"data": "test"})
        processor.process_with_function(always_failing_fn)

        results = processor.get_all_results()
        job = list(results.values())[0]
        assert job.status == JobStatus.FAILED


class TestParallelProcessing:
    """Tests for parallel processing optimization."""

    def test_multiple_workers(self):
        """Test processing with multiple workers."""
        processor = BatchProcessor(worker_count=4)

        # Submit many jobs
        processor.submit_batch([{"id": i} for i in range(20)])

        def process_fn(task):
            time.sleep(0.01)
            return {"result": task["id"]}

        start_time = time.time()
        processor.process_with_function(process_fn)
        sequential_time = time.time() - start_time

        # With 4 workers processing 20 jobs with 0.01s each
        # Sequential would take ~0.2s
        # Parallel should be much faster (around 0.05s)
        assert sequential_time < 0.15  # Allow some overhead

    def test_threading_mode(self):
        """Test threading mode processing."""
        processor = BatchProcessor(worker_count=2, use_multiprocessing=False)
        processor.submit_batch([{"id": i} for i in range(5)])

        def process_fn(task):
            return {"result": task["id"]}

        processor.process_with_function(process_fn)

        results = processor.get_all_results()
        assert len(results) == 5
        assert all(job.status == JobStatus.COMPLETED for job in results.values())


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
