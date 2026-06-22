"""
Async operations wrapper for handling concurrent I/O operations.

Provides:
- Async versions of blocking I/O (API calls, DB queries)
- asyncio task pooling and management
- Concurrent execution patterns
- Async context managers for resource management
- Comprehensive error handling in async contexts
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)
import aiohttp
import aiosqlite
import sqlite3
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar("T")
P = TypeVar("P")
E = TypeVar("E", bound=Exception)


class AsyncError(Exception):
    """Base exception for async operations."""

    pass


class AsyncTimeoutError(AsyncError):
    """Raised when an async operation times out."""

    pass


class AsyncPoolExhaustedError(AsyncError):
    """Raised when async pool is exhausted and no slots available."""

    pass


class AsyncResourceError(AsyncError):
    """Raised when async resource management fails."""

    pass


class TaskStatus(Enum):
    """Status of an async task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult(Generic[T]):
    """Container for task execution result."""

    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[T] = None,
        error: Optional[Exception] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.start_time = start_time
        self.end_time = end_time

    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def __repr__(self) -> str:
        return (
            f"TaskResult(id={self.task_id}, status={self.status.value}, "
            f"result={self.result}, error={self.error})"
        )


class RetryPolicy:
    """Policy for retrying failed async operations."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        import random

        delay = min(
            self.initial_delay * (self.backoff_multiplier ** attempt),
            self.max_delay,
        )
        if self.jitter:
            delay = delay * (0.5 + random.random())
        return delay


def async_retry(
    policy: Optional[RetryPolicy] = None,
    on_error: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """Decorator for retrying async operations with exponential backoff."""
    if policy is None:
        policy = RetryPolicy()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(policy.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < policy.max_retries:
                        delay = policy.get_delay(attempt)
                        if on_error:
                            on_error(e, attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{policy.max_retries} "
                            f"for {func.__name__} after {delay}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        if on_error:
                            on_error(e, attempt)
            raise last_error

        return wrapper

    return decorator


class AsyncTaskPool:
    """Pool for managing concurrent async tasks."""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, TaskResult] = {}
        self._task_counter = 0
        self._lock = asyncio.Lock()

    async def submit(
        self,
        coro: Coroutine[Any, Any, T],
        task_id: Optional[str] = None,
    ) -> str:
        """Submit a coroutine to the pool."""
        if task_id is None:
            async with self._lock:
                self._task_counter += 1
                task_id = f"task_{self._task_counter}"

        task = asyncio.create_task(self._run_task(task_id, coro))
        self.tasks[task_id] = task
        return task_id

    async def _run_task(self, task_id: str, coro: Coroutine[Any, Any, T]) -> None:
        """Run a task with semaphore control."""
        start_time = datetime.now()
        result = TaskResult(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            start_time=start_time,
        )

        try:
            async with self.semaphore:
                result_value = await coro
                result.status = TaskStatus.COMPLETED
                result.result = result_value
        except asyncio.CancelledError:
            result.status = TaskStatus.CANCELLED
            result.error = AsyncError("Task cancelled")
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = e
            logger.error(f"Task {task_id} failed: {e}")
        finally:
            result.end_time = datetime.now()
            self.results[task_id] = result

    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> T:
        """Get result of a submitted task."""
        if task_id not in self.tasks:
            raise AsyncError(f"Task {task_id} not found")

        try:
            await asyncio.wait_for(self.tasks[task_id], timeout=timeout)
        except asyncio.TimeoutError:
            raise AsyncTimeoutError(f"Task {task_id} timed out after {timeout}s")

        result = self.results[task_id]
        if result.status == TaskStatus.FAILED:
            raise AsyncError(f"Task {task_id} failed: {result.error}")
        if result.status == TaskStatus.CANCELLED:
            raise AsyncError(f"Task {task_id} was cancelled")

        return result.result

    async def get_all_results(self, timeout: Optional[float] = None) -> Dict[str, T]:
        """Get results of all tasks."""
        results = {}
        for task_id in self.tasks:
            try:
                results[task_id] = await self.get_result(task_id, timeout=timeout)
            except AsyncError as e:
                logger.error(f"Failed to get result for {task_id}: {e}")
                results[task_id] = None
        return results

    async def wait_all(self, timeout: Optional[float] = None) -> None:
        """Wait for all tasks to complete."""
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.tasks.values(), return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise AsyncTimeoutError(
                f"Not all tasks completed within {timeout}s timeout"
            )

    async def cancel_all(self) -> None:
        """Cancel all pending tasks."""
        for task in self.tasks.values():
            if not task.done():
                task.cancel()

    def get_status(self, task_id: str) -> TaskStatus:
        """Get current status of a task."""
        if task_id in self.results:
            return self.results[task_id].status
        if task_id in self.tasks:
            return TaskStatus.PENDING
        raise AsyncError(f"Task {task_id} not found")

    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics."""
        completed = sum(
            1
            for r in self.results.values()
            if r.status == TaskStatus.COMPLETED
        )
        failed = sum(1 for r in self.results.values() if r.status == TaskStatus.FAILED)
        cancelled = sum(
            1 for r in self.results.values() if r.status == TaskStatus.CANCELLED
        )

        total_time = sum(
            r.elapsed_time or 0
            for r in self.results.values()
            if r.elapsed_time is not None
        )

        return {
            "total_tasks": len(self.tasks),
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "pending": len(self.tasks) - (completed + failed + cancelled),
            "total_elapsed_seconds": total_time,
            "avg_task_time": total_time / len(self.results)
            if self.results
            else 0,
        }


class AsyncAPIClient:
    """Async HTTP client for API calls."""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_policy = RetryPolicy(max_retries=max_retries)
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None

    @asynccontextmanager
    async def _get_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        """Get or create aiohttp session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        try:
            yield self.session
        except Exception as e:
            logger.error(f"Session error: {e}")
            raise

    async def close(self) -> None:
        """Close the client session."""
        if self.session:
            await self.session.close()

    @async_retry()
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make async GET request."""
        url = f"{self.base_url}{endpoint}"
        merged_headers = {**self.headers, **(headers or {})}

        async with self._get_session() as session:
            async with session.get(
                url, params=params, headers=merged_headers
            ) as response:
                if response.status != 200:
                    raise AsyncError(
                        f"GET {url} failed with status {response.status}"
                    )
                return await response.json()

    @async_retry()
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make async POST request."""
        url = f"{self.base_url}{endpoint}"
        merged_headers = {**self.headers, **(headers or {})}

        async with self._get_session() as session:
            kwargs = {"headers": merged_headers}
            if data:
                kwargs["data"] = data
            if json_data:
                kwargs["json"] = json_data

            async with session.post(url, **kwargs) as response:
                if response.status not in (200, 201):
                    raise AsyncError(
                        f"POST {url} failed with status {response.status}"
                    )
                return await response.json()

    @async_retry()
    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make async PUT request."""
        url = f"{self.base_url}{endpoint}"
        merged_headers = {**self.headers, **(headers or {})}

        async with self._get_session() as session:
            async with session.put(url, json=json_data, headers=merged_headers) as response:
                if response.status not in (200, 204):
                    raise AsyncError(
                        f"PUT {url} failed with status {response.status}"
                    )
                if response.status == 204:
                    return {}
                return await response.json()

    @async_retry()
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make async DELETE request."""
        url = f"{self.base_url}{endpoint}"
        merged_headers = {**self.headers, **(headers or {})}

        async with self._get_session() as session:
            async with session.delete(url, headers=merged_headers) as response:
                if response.status not in (200, 204):
                    raise AsyncError(
                        f"DELETE {url} failed with status {response.status}"
                    )
                if response.status == 204:
                    return {}
                return await response.json()


class AsyncDatabaseManager:
    """Async database manager for SQLite operations."""

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connection pool."""
        if self._initialized:
            return

        for _ in range(self.pool_size):
            try:
                conn = await aiosqlite.connect(self.db_path)
                await self.connections.put(conn)
            except Exception as e:
                logger.error(f"Failed to create database connection: {e}")
                raise AsyncResourceError(f"Database pool initialization failed: {e}")

        self._initialized = True

    @asynccontextmanager
    async def get_connection(
        self, timeout: float = 5.0
    ) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get a connection from the pool."""
        if not self._initialized:
            await self.initialize()

        try:
            conn = await asyncio.wait_for(self.connections.get(), timeout=timeout)
        except asyncio.TimeoutError:
            raise AsyncPoolExhaustedError(
                f"Could not get connection within {timeout}s"
            )

        try:
            yield conn
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
        finally:
            await self.connections.put(conn)

    async def execute(
        self, query: str, params: Optional[Tuple] = None
    ) -> List[Tuple]:
        """Execute query and return results."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            return await cursor.fetchall()

    async def execute_many(
        self, query: str, params_list: List[Tuple]
    ) -> None:
        """Execute query multiple times with different parameters."""
        async with self.get_connection() as conn:
            await conn.executemany(query, params_list)
            await conn.commit()

    async def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute insert query and return last row id."""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            await conn.commit()
            return cursor.lastrowid

    async def close_pool(self) -> None:
        """Close all connections in pool."""
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                await conn.close()
            except asyncio.QueueEmpty:
                break

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Context manager for database transaction."""
        async with self.get_connection() as conn:
            try:
                async with conn:
                    yield conn
            except Exception as e:
                await conn.rollback()
                logger.error(f"Transaction failed: {e}")
                raise


class ConcurrentBatchProcessor:
    """Process items in batches with concurrency control."""

    def __init__(
        self,
        batch_size: int = 10,
        max_concurrent_batches: int = 3,
        timeout: float = 60.0,
    ):
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent_batches)

    async def process_items(
        self,
        items: List[T],
        processor: Callable[[List[T]], Coroutine[Any, Any, List[Any]]],
    ) -> List[Any]:
        """Process items in concurrent batches."""
        batches = [
            items[i : i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        tasks = [
            self._process_batch(batch, processor) for batch in batches
        ]

        try:
            batch_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            raise AsyncTimeoutError(
                f"Batch processing timed out after {self.timeout}s"
            )

        results = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                logger.error(f"Batch processing error: {batch_result}")
                raise batch_result
            results.extend(batch_result)

        return results

    async def _process_batch(
        self,
        batch: List[T],
        processor: Callable[[List[T]], Coroutine[Any, Any, List[Any]]],
    ) -> List[Any]:
        """Process a single batch with semaphore control."""
        async with self.semaphore:
            return await processor(batch)


class StreamProcessor:
    """Process async streams with transformation."""

    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size

    @asynccontextmanager
    async def process_stream(
        self,
        source: AsyncIterator[T],
        transformer: Callable[[T], Coroutine[Any, Any, Any]],
        error_handler: Optional[Callable[[Exception], Coroutine[Any, Any, None]]] = None,
    ) -> AsyncGenerator[Any, None]:
        """Process async stream with transformation and error handling."""
        try:
            async for item in source:
                try:
                    transformed = await transformer(item)
                    yield transformed
                except Exception as e:
                    if error_handler:
                        await error_handler(e)
                    else:
                        logger.error(f"Stream processing error: {e}")
                        raise
        except Exception as e:
            logger.error(f"Stream source error: {e}")
            raise


class ResourcePool(ABC, Generic[T]):
    """Abstract base class for managing resource pools."""

    def __init__(self, factory: Callable[[], T], pool_size: int = 10):
        self.factory = factory
        self.pool_size = pool_size
        self.available: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self.in_use: Set[T] = set()
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the resource pool."""
        for _ in range(self.pool_size):
            resource = self.factory()
            await self.available.put(resource)

    @asynccontextmanager
    async def acquire(self, timeout: float = 5.0) -> AsyncGenerator[T, None]:
        """Acquire a resource from the pool."""
        try:
            resource = await asyncio.wait_for(self.available.get(), timeout=timeout)
        except asyncio.TimeoutError:
            raise AsyncPoolExhaustedError(
                f"Could not acquire resource within {timeout}s"
            )

        async with self._lock:
            self.in_use.add(resource)

        try:
            yield resource
        finally:
            async with self._lock:
                self.in_use.discard(resource)
            await self.available.put(resource)

    async def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
        async with self._lock:
            for resource in self.in_use:
                await self._cleanup_resource(resource)
            while not self.available.empty():
                try:
                    resource = self.available.get_nowait()
                    await self._cleanup_resource(resource)
                except asyncio.QueueEmpty:
                    break

    @abstractmethod
    async def _cleanup_resource(self, resource: T) -> None:
        """Cleanup a resource (override in subclass)."""
        pass


class RateLimiter:
    """Rate limiter for async operations."""

    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until rate limit allows next call."""
        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.time_window)

            # Remove old calls outside the time window
            self.calls = [call for call in self.calls if call > cutoff]

            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                wait_until = self.calls[0] + timedelta(seconds=self.time_window)
                wait_time = (wait_until - now).total_seconds()
                if wait_time > 0:
                    logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    self.calls = []
                    self.calls.append(datetime.now())
            else:
                self.calls.append(now)


# Example usage and integration helpers
async def run_concurrent_operations(
    operations: List[Coroutine[Any, Any, T]],
    max_concurrent: int = 10,
    timeout: Optional[float] = None,
) -> List[T]:
    """
    Run multiple concurrent operations with concurrency limit.

    Args:
        operations: List of coroutines to run
        max_concurrent: Maximum concurrent operations
        timeout: Timeout for all operations

    Returns:
        List of results from operations
    """
    pool = AsyncTaskPool(max_concurrent=max_concurrent)

    for op in operations:
        await pool.submit(op)

    try:
        await pool.wait_all(timeout=timeout)
        return await pool.get_all_results(timeout=timeout)
    finally:
        await pool.cancel_all()


async def batch_async_requests(
    items: List[T],
    request_func: Callable[[T], Coroutine[Any, Any, Any]],
    batch_size: int = 10,
    timeout: float = 60.0,
) -> List[Any]:
    """
    Process items in batches concurrently.

    Args:
        items: Items to process
        request_func: Async function to process each item
        batch_size: Size of each batch
        timeout: Timeout for entire batch

    Returns:
        List of results
    """

    async def batch_processor(batch: List[T]) -> List[Any]:
        return await asyncio.gather(
            *[request_func(item) for item in batch],
            return_exceptions=True,
        )

    processor = ConcurrentBatchProcessor(batch_size=batch_size, timeout=timeout)
    return await processor.process_items(items, batch_processor)


if __name__ == "__main__":
    # Example usage
    async def example_usage():
        """Demonstrate async operations wrapper."""

        # Example 1: Task pool
        print("=== Example 1: AsyncTaskPool ===")
        pool = AsyncTaskPool(max_concurrent=3)

        async def sample_task(task_num: int) -> str:
            await asyncio.sleep(1)
            return f"Task {task_num} completed"

        task_ids = []
        for i in range(5):
            task_id = await pool.submit(sample_task(i))
            task_ids.append(task_id)

        await pool.wait_all()
        results = await pool.get_all_results()
        print(f"Results: {results}")
        print(f"Statistics: {pool.get_statistics()}")

        # Example 2: API Client
        print("\n=== Example 2: AsyncAPIClient ===")
        client = AsyncAPIClient(base_url="https://jsonplaceholder.typicode.com")
        try:
            result = await client.get("/posts/1")
            print(f"API Response: {result.get('title', 'N/A')}")
        finally:
            await client.close()

        # Example 3: Database operations
        print("\n=== Example 3: AsyncDatabaseManager ===")
        db = AsyncDatabaseManager(":memory:")
        await db.initialize()

        # Create table
        async with db.get_connection() as conn:
            await conn.execute(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
            )
            await conn.commit()

        # Insert data
        user_id = await db.execute_insert(
            "INSERT INTO users (name) VALUES (?)", ("Alice",)
        )
        print(f"Inserted user with id: {user_id}")

        # Query data
        results = await db.execute("SELECT * FROM users")
        print(f"Users: {results}")

        await db.close_pool()

        # Example 4: Batch processing
        print("\n=== Example 4: Batch Processing ===")

        async def process_item(item: int) -> int:
            await asyncio.sleep(0.1)
            return item * 2

        items = list(range(10))
        batch_results = await batch_async_requests(
            items, process_item, batch_size=3, timeout=30.0
        )
        print(f"Batch results: {batch_results}")

        # Example 5: Rate limiting
        print("\n=== Example 5: Rate Limiting ===")
        limiter = RateLimiter(max_calls=3, time_window=1.0)

        async def rate_limited_task(num: int) -> str:
            await limiter.acquire()
            print(f"Task {num} executed at {datetime.now().isoformat()}")
            return f"Task {num}"

        await asyncio.gather(*[rate_limited_task(i) for i in range(5)])

    # Run examples
    asyncio.run(example_usage())
