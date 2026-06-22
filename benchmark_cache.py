"""
Performance benchmarking script for cache manager.
Measures throughput, latency, and cache efficiency.
"""

import time
import json
import statistics
from typing import Dict, List, Tuple
from cache_manager import (
    CacheManager,
    CacheConfiguration,
    CacheBackendType,
    InMemoryCache,
)
import logging

logging.basicConfig(level=logging.WARNING)


class CacheBenchmark:
    """Benchmark cache performance."""

    def __init__(self):
        self.results: Dict[str, Dict] = {}

    def benchmark_operation(
        self,
        name: str,
        operation,
        iterations: int = 1000,
        setup=None,
        teardown=None,
    ) -> Dict:
        """Benchmark a single operation."""
        times = []

        for _ in range(iterations):
            if setup:
                setup()

            start = time.perf_counter()
            operation()
            end = time.perf_counter()

            times.append((end - start) * 1000)  # Convert to ms

            if teardown:
                teardown()

        # Calculate statistics
        stats = {
            "operation": name,
            "iterations": iterations,
            "total_time_ms": sum(times),
            "avg_time_ms": statistics.mean(times),
            "median_time_ms": statistics.median(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "stdev_ms": (
                statistics.stdev(times) if len(times) > 1 else 0
            ),
            "throughput_ops_per_sec": iterations / (sum(times) / 1000),
        }

        self.results[name] = stats
        return stats

    def print_results(self):
        """Print benchmark results in table format."""
        print("\n" + "=" * 100)
        print("CACHE MANAGER PERFORMANCE BENCHMARK")
        print("=" * 100)

        for name, stats in self.results.items():
            print(f"\n{name}")
            print("-" * 100)
            print(f"  Iterations:           {stats['iterations']}")
            print(
                f"  Total time:           {stats['total_time_ms']:.2f} ms"
            )
            print(f"  Avg time/op:          {stats['avg_time_ms']:.4f} ms")
            print(
                f"  Median time:          {stats['median_time_ms']:.4f} ms"
            )
            print(f"  Min/Max time:         {stats['min_time_ms']:.4f} / {stats['max_time_ms']:.4f} ms")
            print(f"  Std Dev:              {stats['stdev_ms']:.4f} ms")
            print(
                f"  Throughput:           {stats['throughput_ops_per_sec']:.0f} ops/sec"
            )

    def export_results(self, filename: str = "benchmark_results.json"):
        """Export results to JSON."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults exported to {filename}")


def benchmark_in_memory_cache():
    """Benchmark in-memory cache operations."""
    benchmark = CacheBenchmark()
    cache = InMemoryCache(max_size=10000)

    test_value = {"id": 1, "name": "Test", "data": "x" * 1000}

    # Benchmark: Set operation
    def set_op():
        for i in range(100):
            cache.set(f"key_{i}", test_value, ttl=3600)

    benchmark.benchmark_operation(
        "InMemory: Set (100 keys)",
        set_op,
        iterations=100,
    )

    # Benchmark: Get operation (cache hit)
    cache.set("key_0", test_value, ttl=3600)

    def get_hit_op():
        for i in range(100):
            cache.get(f"key_{i % 100}")

    benchmark.benchmark_operation(
        "InMemory: Get (100 hits)",
        get_hit_op,
        iterations=100,
    )

    # Benchmark: Get operation (cache miss)
    def get_miss_op():
        cache.get(f"nonexistent_{time.time()}")

    benchmark.benchmark_operation(
        "InMemory: Get (miss)",
        get_miss_op,
        iterations=1000,
    )

    # Benchmark: Delete operation
    def delete_op():
        for i in range(100):
            cache.set(f"delete_key_{i}", test_value, ttl=3600)
            cache.delete(f"delete_key_{i}")

    benchmark.benchmark_operation(
        "InMemory: Delete (100 ops)",
        delete_op,
        iterations=100,
    )

    # Benchmark: Exists operation
    cache.set("exists_key", test_value, ttl=3600)

    def exists_op():
        for i in range(100):
            cache.exists(f"key_{i % 100}")

    benchmark.benchmark_operation(
        "InMemory: Exists (100 checks)",
        exists_op,
        iterations=100,
    )

    return benchmark


def benchmark_cache_manager():
    """Benchmark CacheManager operations."""
    benchmark = CacheBenchmark()
    config = CacheConfiguration(default_ttl=300)
    cache_mgr = CacheManager(
        backend_type=CacheBackendType.MEMORY,
        cache_config=config,
    )

    test_value = {"id": 1, "name": "Test", "data": "x" * 1000}

    # Benchmark: Generate cache key
    def key_gen_op():
        for i in range(100):
            cache_mgr.generate_cache_key(
                "/api/users", {"id": i, "filter": "active"}
            )

    benchmark.benchmark_operation(
        "CacheManager: Key generation (100 keys)",
        key_gen_op,
        iterations=100,
    )

    # Benchmark: Set with metrics
    def set_op():
        for i in range(100):
            cache_mgr.set(f"key_{i}", test_value, "/api/users")

    benchmark.benchmark_operation(
        "CacheManager: Set (100 ops with metrics)",
        set_op,
        iterations=100,
    )

    # Benchmark: Get with metrics
    cache_mgr.set("test_key", test_value, "/api/users")

    def get_op():
        for i in range(100):
            cache_mgr.get(f"key_{i % 100}", "/api/users")

    benchmark.benchmark_operation(
        "CacheManager: Get (100 ops with metrics)",
        get_op,
        iterations=100,
    )

    return benchmark


def benchmark_cache_key_strategies():
    """Benchmark different cache key generation strategies."""
    benchmark = CacheBenchmark()
    cache_mgr = CacheManager(
        backend_type=CacheBackendType.MEMORY,
    )

    # Simple key
    def simple_key():
        for i in range(100):
            key = f"user:{i}"

    benchmark.benchmark_operation(
        "Key Strategy: Simple string (100 keys)",
        simple_key,
        iterations=100,
    )

    # Generated key with dict
    def generated_key():
        for i in range(100):
            cache_mgr.generate_cache_key("/api/users", {"id": i})

    benchmark.benchmark_operation(
        "Key Strategy: Generated with params (100 keys)",
        generated_key,
        iterations=100,
    )

    # Complex generated key
    def complex_key():
        for i in range(100):
            cache_mgr.generate_cache_key(
                "/api/posts",
                {
                    "user_id": i,
                    "filter": "active",
                    "sort": "date",
                    "limit": 10,
                    "offset": 0,
                },
            )

    benchmark.benchmark_operation(
        "Key Strategy: Complex params (100 keys)",
        complex_key,
        iterations=100,
    )

    return benchmark


def benchmark_concurrent_access():
    """Benchmark concurrent cache access."""
    import threading
    from queue import Queue

    benchmark = CacheBenchmark()
    cache = InMemoryCache(max_size=10000)
    test_value = {"id": 1, "name": "Test"}

    # Pre-populate cache
    for i in range(100):
        cache.set(f"key_{i}", test_value, ttl=3600)

    # Concurrent reads
    def concurrent_read():
        def worker():
            for i in range(50):
                cache.get(f"key_{i % 100}")

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    benchmark.benchmark_operation(
        "Concurrent: 10 threads, 50 reads each (500 total)",
        concurrent_read,
        iterations=10,
    )

    # Concurrent writes
    counter = 0

    def concurrent_write():
        nonlocal counter
        def worker():
            nonlocal counter
            for i in range(50):
                cache.set(
                    f"concurrent_key_{counter}_{i}", test_value, ttl=3600
                )
                counter += 1

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    benchmark.benchmark_operation(
        "Concurrent: 10 threads, 50 writes each (500 total)",
        concurrent_write,
        iterations=1,
    )

    return benchmark


def benchmark_large_values():
    """Benchmark cache with different value sizes."""
    benchmark = CacheBenchmark()
    cache = InMemoryCache(max_size=1000)

    # Small value (1KB)
    small_value = {"data": "x" * 1000}

    def set_small():
        for i in range(100):
            cache.set(f"key_{i}", small_value, ttl=3600)

    benchmark.benchmark_operation(
        "Large Values: Set 1KB values (100 keys)",
        set_small,
        iterations=100,
    )

    # Medium value (100KB)
    medium_value = {"data": "x" * 100000}

    def set_medium():
        for i in range(100, 110):
            cache.set(f"key_{i}", medium_value, ttl=3600)

    benchmark.benchmark_operation(
        "Large Values: Set 100KB values (10 keys)",
        set_medium,
        iterations=10,
    )

    # Large value (1MB)
    large_value = {"data": "x" * 1000000}

    def set_large():
        cache.set("large_key", large_value, ttl=3600)

    benchmark.benchmark_operation(
        "Large Values: Set 1MB value",
        set_large,
        iterations=10,
    )

    return benchmark


def compare_backends():
    """Compare different cache backends."""
    print("\n" + "=" * 100)
    print("CACHE BACKEND COMPARISON")
    print("=" * 100)

    results = {}

    # In-memory cache
    print("\nBenchmarking In-Memory Cache...")
    in_mem_bench = benchmark_in_memory_cache()
    results["In-Memory"] = in_mem_bench.results

    # Cache Manager
    print("\nBenchmarking Cache Manager...")
    mgr_bench = benchmark_cache_manager()
    results["CacheManager"] = mgr_bench.results

    return results


def run_all_benchmarks():
    """Run all benchmarks."""
    print("Starting Cache Performance Benchmarks...")
    print("=" * 100)

    # 1. In-Memory Cache
    print("\n1. IN-MEMORY CACHE BENCHMARKS")
    in_mem_bench = benchmark_in_memory_cache()
    in_mem_bench.print_results()

    # 2. Cache Manager
    print("\n2. CACHE MANAGER BENCHMARKS")
    mgr_bench = benchmark_cache_manager()
    mgr_bench.print_results()

    # 3. Key Generation Strategies
    print("\n3. CACHE KEY STRATEGY BENCHMARKS")
    key_bench = benchmark_cache_key_strategies()
    key_bench.print_results()

    # 4. Concurrent Access
    print("\n4. CONCURRENT ACCESS BENCHMARKS")
    concurrent_bench = benchmark_concurrent_access()
    concurrent_bench.print_results()

    # 5. Large Values
    print("\n5. LARGE VALUES BENCHMARKS")
    large_bench = benchmark_large_values()
    large_bench.print_results()

    # Export combined results
    print("\n" + "=" * 100)
    print("Exporting benchmark results...")

    all_results = {
        "in_memory_cache": in_mem_bench.results,
        "cache_manager": mgr_bench.results,
        "key_strategies": key_bench.results,
        "concurrent_access": concurrent_bench.results,
        "large_values": large_bench.results,
    }

    with open("benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print("Results saved to benchmark_results.json")
    print("=" * 100)


if __name__ == "__main__":
    run_all_benchmarks()
