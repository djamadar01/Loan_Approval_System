# Batch Processing System - Quick Reference

## Minimum Viable Example

```python
from batch_processor import BatchProcessor

# Create processor
processor = BatchProcessor(worker_count=4)

# Submit jobs
processor.submit_batch([{"id": i} for i in range(10)])

# Process
processor.process_with_function(lambda task: {"result": task["id"] * 2})

# Export
processor.export_results("results.json")
```

## Common Tasks

### Initialize Processor

```python
# Default (4 workers, threading)
processor = BatchProcessor()

# CPU-bound (multiprocessing)
processor = BatchProcessor(worker_count=4, use_multiprocessing=True)

# I/O-bound (many threads)
processor = BatchProcessor(worker_count=16, use_multiprocessing=False)

# With error recovery
from batch_processor import ErrorRecoveryStrategy
recovery = ErrorRecoveryStrategy(max_retries=3, backoff_factor=2.0)
processor = BatchProcessor(error_recovery=recovery)
```

### Submit Jobs

```python
# Single job
job_id = processor.submit_job({"data": "value"})

# Batch
processor.submit_batch([{"id": i} for i in range(100)])

# With metadata
processor.submit_job({"data": "value"}, source="api", priority="high")
```

### Monitor Progress

```python
# Get progress object
progress = processor.get_progress()
print(f"Completion: {progress.get_completion_percentage():.1f}%")
print(f"Success Rate: {progress.get_success_rate():.1f}%")
print(f"ETA: {progress.get_estimated_time_remaining():.1f}s")

# Print formatted string
print(processor.print_progress())
```

### Process Jobs

```python
# Simple function
def process(task):
    return {"result": task["value"] * 2}

processor.process_with_function(process)

# With custom worker count
processor.process_with_function(process, max_workers=8)
```

### Access Results

```python
# Single result
job = processor.get_job_result("job_123")
print(f"Status: {job.status.value}")
print(f"Result: {job.result}")
print(f"Duration: {job.get_duration():.3f}s")

# All results
results = processor.get_all_results()
for job_id, job in results.items():
    print(f"{job_id}: {job.status.value}")

# Failed jobs
failed = processor.get_failed_jobs()
for job_id, job in failed.items():
    print(f"Error: {job.error}")
```

### Export Results

```python
from batch_processor import ExportFormat

# JSON
processor.export_results("results.json", ExportFormat.JSON)

# CSV
processor.export_results("results.csv", ExportFormat.CSV)

# Parquet (requires pandas, pyarrow)
processor.export_results("results.parquet", ExportFormat.PARQUET)
```

### Get Statistics

```python
stats = processor.get_statistics()

print(f"Total jobs: {stats['progress']['total_jobs']}")
print(f"Completed: {stats['progress']['completed_jobs']}")
print(f"Failed: {stats['progress']['failed_jobs']}")
print(f"Success rate: {stats['progress']['success_rate']:.1f}%")
print(f"Total time: {stats['total_duration_seconds']:.2f}s")
print(f"Avg job time: {stats['average_job_duration_seconds']:.3f}s")
```

## Class Reference

| Method | Purpose |
|---|---|
| `submit_job(data, job_id, **metadata)` | Submit single job |
| `submit_batch(tasks, job_ids)` | Submit multiple jobs |
| `process_with_function(func, max_workers)` | Execute all jobs |
| `get_progress()` | Get progress snapshot |
| `get_job_result(job_id)` | Get specific result |
| `get_all_results()` | Get all results dict |
| `get_failed_jobs()` | Get failed jobs dict |
| `export_results(path, format)` | Export results to file |
| `get_statistics()` | Get comprehensive stats |

## Files

- **batch_processor.py**: Main implementation (700+ lines)
- **test_batch_processor.py**: Comprehensive tests (40+ tests)
- **batch_examples.py**: Real-world examples (6 scenarios)
- **BATCH_PROCESSOR_GUIDE.md**: Full documentation
- **README_BATCH_PROCESSOR.md**: Feature overview

## Next Steps

1. Read BATCH_PROCESSOR_GUIDE.md for details
2. Review batch_examples.py for usage
3. Run test_batch_processor.py to verify
