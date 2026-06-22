"""
Example usage scenarios for batch processing system.
Demonstrates real-world use cases and best practices.
"""

import time
import random
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from batch_processor import (
    BatchProcessor,
    ExportFormat,
    ErrorRecoveryStrategy,
    JobStatus,
)


# ============================================================================
# Example 1: Basic Image Processing
# ============================================================================

def example_image_processing():
    """Example: Batch processing images with resize operation."""
    print("\n" + "="*60)
    print("Example 1: Image Processing Batch")
    print("="*60)

    processor = BatchProcessor(worker_count=4)

    # Simulate image metadata
    images = [
        {"id": f"img_{i:04d}", "path": f"/data/img_{i:04d}.jpg", "size": 1920 + i*100}
        for i in range(20)
    ]

    # Submit batch
    print(f"Submitting {len(images)} images for processing...")
    processor.submit_batch(images)

    # Processing function
    def process_image(image_data):
        """Simulate image processing."""
        time.sleep(0.1)  # Simulate processing time
        return {
            "id": image_data["id"],
            "original_size": image_data["size"],
            "resized_size": image_data["size"] // 4,
            "processed_at": datetime.now().isoformat(),
        }

    # Process
    print("Processing images...")
    processor.process_with_function(process_image, max_workers=4)

    # Results
    stats = processor.get_statistics()
    print(f"\nCompleted: {stats['progress']['completed_jobs']}/{stats['progress']['total_jobs']}")
    print(f"Success rate: {stats['progress']['success_rate']:.1f}%")
    print(f"Total time: {stats['total_duration_seconds']:.2f}s")
    print(f"Avg per image: {stats['average_job_duration_seconds']:.3f}s")

    # Export
    output_dir = Path("/home/ubuntu/Desktop/demo/batch_results/images")
    processor.export_results(output_dir / "results.json", ExportFormat.JSON)
    print(f"\nResults exported to: {output_dir}")


# ============================================================================
# Example 2: Data Transformation with Error Recovery
# ============================================================================

def example_data_transformation():
    """Example: Transform data with error handling and retry."""
    print("\n" + "="*60)
    print("Example 2: Data Transformation with Error Recovery")
    print("="*60)

    processor = BatchProcessor(
        worker_count=3,
        error_recovery=ErrorRecoveryStrategy(max_retries=3, backoff_factor=1.5)
    )

    # Data records to transform
    records = [
        {"id": i, "value": str(i * 10), "category": chr(65 + i % 3)}
        for i in range(15)
    ]
    # Add some problematic records
    records.append({"id": 99, "value": "invalid"})
    records.append({"id": 100, "value": None})

    print(f"Submitting {len(records)} records for transformation...")
    processor.submit_batch(records)

    # Processing function with potential failures
    attempt_count = {"count": 0}

    def transform_record(record):
        """Transform record with simulated transient failures."""
        # Simulate occasional network errors
        if random.random() < 0.1:
            raise ConnectionError("Transient network error")

        try:
            return {
                "id": record["id"],
                "original_value": record["value"],
                "transformed_value": int(record["value"]) * 2,
                "category": record.get("category", "unknown"),
                "transformed_at": datetime.now().isoformat(),
            }
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Invalid record format: {str(e)}")

    # Process
    print("Transforming records with error recovery...")
    processor.process_with_function(transform_record)

    # Results
    stats = processor.get_statistics()
    failed = processor.get_failed_jobs()

    print(f"\nCompleted: {stats['progress']['completed_jobs']}/{stats['progress']['total_jobs']}")
    print(f"Failed: {stats['progress']['failed_jobs']}")
    print(f"Success rate: {stats['progress']['success_rate']:.1f}%")
    print(f"Total retries: {stats['progress']['total_retries']}")

    if failed:
        print("\nFailed records:")
        for job_id, job in list(failed.items())[:3]:
            print(f"  - {job_id}: {job.error.split(chr(10))[0]}")

    # Export all formats
    output_dir = Path("/home/ubuntu/Desktop/demo/batch_results/transformation")
    processor.export_results(output_dir / "results.json", ExportFormat.JSON)
    processor.export_results(output_dir / "results.csv", ExportFormat.CSV)
    print(f"\nResults exported to: {output_dir}")


# ============================================================================
# Example 3: Real-time Progress Monitoring
# ============================================================================

def example_progress_monitoring():
    """Example: Monitor batch progress in real-time."""
    print("\n" + "="*60)
    print("Example 3: Real-time Progress Monitoring")
    print("="*60)

    processor = BatchProcessor(worker_count=2)

    # Large batch of tasks
    tasks = [{"task_id": i, "complexity": i % 5 + 1} for i in range(50)]
    print(f"Submitting {len(tasks)} tasks...")
    processor.submit_batch(tasks)

    # Processing function with variable duration
    def process_task(task):
        # Complexity affects processing time
        time.sleep(0.05 * task["complexity"])
        return {
            "task_id": task["task_id"],
            "complexity": task["complexity"],
            "processed_at": datetime.now().isoformat(),
        }

    # Process with progress monitoring in separate thread
    print("Processing tasks...")

    import threading

    def monitor_progress():
        """Monitor and print progress every 2 seconds."""
        while processor.get_progress().completed_jobs < processor.get_progress().total_jobs:
            progress = processor.get_progress()
            completion = progress.get_completion_percentage()
            eta = progress.get_estimated_time_remaining()
            print(f"  Progress: {completion:.1f}% complete, "
                  f"ETA: {eta:.1f}s" if eta else "  Progress: 0% complete")
            time.sleep(1)

    # Start monitoring in background
    monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
    monitor_thread.start()

    # Process
    processor.process_with_function(process_task)

    # Final results
    stats = processor.get_statistics()
    print(f"\nFinal Stats:")
    print(f"  Total time: {stats['total_duration_seconds']:.2f}s")
    print(f"  Success rate: {stats['progress']['success_rate']:.1f}%")
    print(f"  Jobs by status: {stats['jobs_by_status']}")

    monitor_thread.join(timeout=1)


# ============================================================================
# Example 4: Batch Export in Multiple Formats
# ============================================================================

def example_multi_format_export():
    """Example: Export results in multiple formats."""
    print("\n" + "="*60)
    print("Example 4: Multi-Format Export")
    print("="*60)

    processor = BatchProcessor(worker_count=2)

    # Generate sample data
    products = [
        {"sku": f"SKU{i:05d}", "price": 10 + i, "quantity": random.randint(1, 100)}
        for i in range(100)
    ]

    print(f"Processing {len(products)} products...")
    processor.submit_batch(products)

    def process_product(product):
        """Calculate product metrics."""
        time.sleep(0.01)
        return {
            "sku": product["sku"],
            "price": product["price"],
            "quantity": product["quantity"],
            "total_value": product["price"] * product["quantity"],
            "processed_at": datetime.now().isoformat(),
        }

    processor.process_with_function(process_product)

    # Export in all formats
    output_dir = Path("/home/ubuntu/Desktop/demo/batch_results/export_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\nExporting results...")

    # JSON
    json_path = processor.export_results(
        output_dir / "products.json",
        format=ExportFormat.JSON,
    )
    print(f"  ✓ JSON: {json_path}")

    # CSV
    csv_path = processor.export_results(
        output_dir / "products.csv",
        format=ExportFormat.CSV,
    )
    print(f"  ✓ CSV: {csv_path}")

    # Parquet (if pandas/pyarrow available)
    try:
        parquet_path = processor.export_results(
            output_dir / "products.parquet",
            format=ExportFormat.PARQUET,
        )
        print(f"  ✓ Parquet: {parquet_path}")
    except ImportError:
        print("  ⚠ Parquet: pandas/pyarrow not installed")

    # Statistics export
    stats = processor.get_statistics()
    stats_path = output_dir / "statistics.json"
    import json
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"  ✓ Statistics: {stats_path}")


# ============================================================================
# Example 5: Handling Large-Scale Processing with Optimal Worker Count
# ============================================================================

def example_optimal_worker_count():
    """Example: Optimize worker count for different scenarios."""
    print("\n" + "="*60)
    print("Example 5: Worker Count Optimization")
    print("="*60)

    # Scenario 1: CPU-intensive tasks
    print("\nScenario 1: CPU-Intensive Tasks (4 workers)")
    processor_cpu = BatchProcessor(worker_count=4)

    tasks_cpu = [{"id": i, "data": list(range(1000))} for i in range(20)]
    processor_cpu.submit_batch(tasks_cpu)

    def cpu_intensive_task(task):
        """CPU-bound operation."""
        result = sum(x*x for x in task["data"] for _ in range(100))
        return {"id": task["id"], "result": result}

    start = time.time()
    processor_cpu.process_with_function(cpu_intensive_task)
    cpu_time = time.time() - start
    print(f"  Completed in {cpu_time:.2f}s")

    # Scenario 2: I/O-bound tasks
    print("\nScenario 2: I/O-Bound Tasks (8 workers)")
    processor_io = BatchProcessor(worker_count=8)

    tasks_io = [{"id": i, "path": f"/data/file_{i}.txt"} for i in range(20)]
    processor_io.submit_batch(tasks_io)

    def io_bound_task(task):
        """I/O-bound operation (simulated)."""
        time.sleep(0.1)  # Simulate file I/O
        return {"id": task["id"], "data_size": random.randint(100, 1000)}

    start = time.time()
    processor_io.process_with_function(io_bound_task)
    io_time = time.time() - start
    print(f"  Completed in {io_time:.2f}s")

    # Scenario 3: Mixed workload
    print("\nScenario 3: Mixed Workload (6 workers)")
    processor_mixed = BatchProcessor(worker_count=6)

    tasks_mixed = [
        {"id": i, "type": "cpu" if i % 2 == 0 else "io"}
        for i in range(20)
    ]
    processor_mixed.submit_batch(tasks_mixed)

    def mixed_task(task):
        """Mixed CPU and I/O."""
        if task["type"] == "cpu":
            result = sum(x*x for x in range(1000))
        else:
            time.sleep(0.05)
            result = random.randint(1, 100)
        return {"id": task["id"], "result": result}

    start = time.time()
    processor_mixed.process_with_function(mixed_task)
    mixed_time = time.time() - start
    print(f"  Completed in {mixed_time:.2f}s")


# ============================================================================
# Example 6: Advanced Error Analysis
# ============================================================================

def example_error_analysis():
    """Example: Detailed error analysis and recovery."""
    print("\n" + "="*60)
    print("Example 6: Error Analysis and Recovery")
    print("="*60)

    processor = BatchProcessor(
        worker_count=2,
        error_recovery=ErrorRecoveryStrategy(max_retries=2)
    )

    # Create problematic dataset
    data = []
    for i in range(30):
        if i % 10 == 0:
            # Add problematic entries
            data.append({"id": i, "value": None})
        else:
            data.append({"id": i, "value": i * 10})

    print(f"Submitting {len(data)} items (some problematic)...")
    processor.submit_batch(data)

    error_types = {"count": {}}

    def process_with_errors(item):
        """Processing function that may encounter errors."""
        if item["value"] is None:
            raise ValueError("Invalid value: None")
        if item["id"] % 15 == 0 and random.random() < 0.7:
            raise ConnectionError("Network timeout")
        return {"id": item["id"], "result": item["value"] * 2}

    processor.process_with_function(process_with_errors)

    # Analyze results
    results = processor.get_all_results()
    failed = processor.get_failed_jobs()

    print(f"\nProcessing Summary:")
    print(f"  Total: {len(results)}")
    print(f"  Successful: {len(results) - len(failed)}")
    print(f"  Failed: {len(failed)}")

    if failed:
        print(f"\nFailed Jobs Analysis:")
        error_types = {}
        for job_id, job in failed.items():
            error_line = job.error.split('\n')[-2] if job.error else "Unknown"
            error_type = error_line.split(':')[0] if ':' in error_line else "Unknown"
            error_types[error_type] = error_types.get(error_type, 0) + 1
            print(f"  {job_id}: {error_type}")

        print(f"\nError Distribution:")
        for error_type, count in error_types.items():
            print(f"  {error_type}: {count}")

    # Export failed jobs for analysis
    output_dir = Path("/home/ubuntu/Desktop/demo/batch_results/error_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    failed_export = [job.to_dict() for job in failed.values()]
    import json
    with open(output_dir / "failed_jobs.json", 'w') as f:
        json.dump(failed_export, f, indent=2, default=str)
    print(f"\nFailed jobs exported to: {output_dir / 'failed_jobs.json'}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Batch Processing System - Examples")
    print("="*60)

    try:
        example_image_processing()
    except Exception as e:
        print(f"Example 1 error: {e}")

    try:
        example_data_transformation()
    except Exception as e:
        print(f"Example 2 error: {e}")

    try:
        example_progress_monitoring()
    except Exception as e:
        print(f"Example 3 error: {e}")

    try:
        example_multi_format_export()
    except Exception as e:
        print(f"Example 4 error: {e}")

    try:
        example_optimal_worker_count()
    except Exception as e:
        print(f"Example 5 error: {e}")

    try:
        example_error_analysis()
    except Exception as e:
        print(f"Example 6 error: {e}")

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)
