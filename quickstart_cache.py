#!/usr/bin/env python3
"""
Quick start guide for the production caching layer.
Demonstrates all key features with simple examples.
"""

import logging
from cache_manager import (
    CacheManager,
    CacheConfiguration,
    CacheBackendType,
    cached,
)

# Setup logging to see cache operations
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def example_1_basic_caching():
    """Example 1: Basic set, get, delete operations."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Caching")
    print("=" * 70)

    # Initialize cache manager with in-memory backend
    cache_mgr = CacheManager(backend_type=CacheBackendType.MEMORY)

    # Set a value in cache
    user_data = {"id": 1, "name": "Alice", "email": "alice@example.com"}
    cache_mgr.set("user:1", user_data, "/api/users")
    print("✓ Set user:1 in cache")

    # Get value from cache
    cached_user = cache_mgr.get("user:1", "/api/users")
    print(f"✓ Retrieved from cache: {cached_user}")

    # Check metrics
    metrics = cache_mgr.get_metrics("/api/users")
    print(f"✓ Metrics - Hit: {metrics['metrics']['hit']}, Miss: {metrics['metrics']['miss']}")

    # Delete value
    cache_mgr.delete("user:1", "/api/users")
    print("✓ Deleted user:1 from cache")

    # Try to get deleted value
    result = cache_mgr.get("user:1", "/api/users")
    print(f"✓ After delete, value is: {result}")


def example_2_cache_ttl():
    """Example 2: Configurable TTL per endpoint."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Configurable TTL per Endpoint")
    print("=" * 70)

    config = CacheConfiguration(default_ttl=300)
    config.set_endpoint_ttl("/api/users", 600)  # 10 minutes
    config.set_endpoint_ttl("/api/posts", 300)  # 5 minutes

    cache_mgr = CacheManager(
        backend_type=CacheBackendType.MEMORY, cache_config=config
    )

    # Set values with different endpoints (different TTLs)
    cache_mgr.set("key1", "user_data", "/api/users")
    cache_mgr.set("key2", "post_data", "/api/posts")

    ttl_users = config.get_endpoint_ttl("/api/users")
    ttl_posts = config.get_endpoint_ttl("/api/posts")

    print(f"✓ /api/users TTL: {ttl_users}s (10 minutes)")
    print(f"✓ /api/posts TTL: {ttl_posts}s (5 minutes)")
    print(f"✓ Default TTL: {config._default_ttl}s (for other endpoints)")


def example_3_decorated_function():
    """Example 3: Using @cached decorator."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: @cached Decorator")
    print("=" * 70)

    cache_mgr = CacheManager(backend_type=CacheBackendType.MEMORY)
    call_count = 0

    @cached(cache_mgr, "/api/expensive")
    def expensive_operation():
        nonlocal call_count
        call_count += 1
        print(f"  [Function called - execution #{call_count}]")
        return {"result": "expensive computation", "call_count": call_count}

    # First call - function executes
    result1 = expensive_operation()
    print(f"✓ First call result: {result1}")

    # Second call - returns cached result
    result2 = expensive_operation()
    print(f"✓ Second call result: {result2}")

    # Third call - still cached
    result3 = expensive_operation()
    print(f"✓ Third call result: {result3}")

    print(f"✓ Function was called {call_count} time(s) total (should be 1)")


def example_4_cache_invalidation():
    """Example 4: Cache invalidation patterns."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Cache Invalidation")
    print("=" * 70)

    cache_mgr = CacheManager(backend_type=CacheBackendType.MEMORY)

    # Populate cache with multiple keys
    for i in range(5):
        cache_mgr.set(f"user:{i}", {"id": i, "name": f"User{i}"}, "/api/users")

    print("✓ Populated cache with user:0 through user:4")

    # Invalidate pattern
    invalidated = cache_mgr.invalidate_pattern("/api/users", "user:*")
    print(f"✓ Invalidated {invalidated} keys matching pattern 'user:*'")

    # Verify keys are gone
    result = cache_mgr.get("user:0", "/api/users")
    print(f"✓ After invalidation, user:0 is: {result}")


def example_5_cache_warming():
    """Example 5: Cache warming strategy."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Cache Warming")
    print("=" * 70)

    config = CacheConfiguration(default_ttl=300)

    # Define a warming strategy
    warming_executed = []

    def warm_popular_items(manager):
        popular_items = [
            {"id": 1, "name": "Popular Item 1"},
            {"id": 2, "name": "Popular Item 2"},
        ]
        for item in popular_items:
            key = manager.generate_cache_key("/api/items", {"id": item["id"]})
            manager.set(key, item, "/api/items")
        warming_executed.append(True)
        print(f"  [Warming executed - populated {len(popular_items)} items]")

    # Register warming strategy
    config.set_warming_strategy("/api/items", warm_popular_items, interval=60)

    cache_mgr = CacheManager(
        backend_type=CacheBackendType.MEMORY, cache_config=config
    )

    # Manually trigger warming
    cache_mgr.warm_cache("/api/items")
    print(f"✓ Cache warming executed: {len(warming_executed) > 0}")

    # Verify warmed data is in cache
    key = cache_mgr.generate_cache_key("/api/items", {"id": 1})
    warmed_item = cache_mgr.get(key, "/api/items")
    print(f"✓ Retrieved warmed item: {warmed_item}")


def example_6_metrics():
    """Example 6: Cache metrics and monitoring."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Metrics & Monitoring")
    print("=" * 70)

    cache_mgr = CacheManager(backend_type=CacheBackendType.MEMORY)

    # Perform various cache operations
    cache_mgr.set("key1", "value1", "/api/test")
    cache_mgr.set("key2", "value2", "/api/test")

    # Cache hits
    for _ in range(5):
        cache_mgr.get("key1", "/api/test")

    # Cache miss
    cache_mgr.get("nonexistent", "/api/test")

    # Get metrics
    metrics = cache_mgr.get_metrics("/api/test")
    print(f"✓ Endpoint: {metrics['endpoint']}")
    print(f"✓ Total requests: {metrics['total_requests']}")
    print(f"✓ Cache hits: {metrics['metrics']['hit']}")
    print(f"✓ Cache misses: {metrics['metrics']['miss']}")
    print(f"✓ Cache sets: {metrics['metrics']['set']}")
    print(f"✓ Hit rate: {metrics['hit_rate_percent']}%")

    # Backend stats
    stats = cache_mgr.get_backend_stats()
    print(f"✓ Backend type: {stats['type']}")
    print(f"✓ Cache size: {stats['size']}")
    print(f"✓ Utilization: {stats['utilization_percent']}%")


def example_7_key_generation():
    """Example 7: Cache key generation."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Cache Key Generation")
    print("=" * 70)

    cache_mgr = CacheManager(backend_type=CacheBackendType.MEMORY)

    # Simple key
    key1 = cache_mgr.generate_cache_key("/api/users")
    print(f"✓ Simple key: {key1}")

    # Key with parameters
    params = {"user_id": 123, "filter": "active"}
    key2 = cache_mgr.generate_cache_key("/api/users", params)
    print(f"✓ Parameterized key: {key2}")

    # Different parameters = different key
    params2 = {"user_id": 456, "filter": "inactive"}
    key3 = cache_mgr.generate_cache_key("/api/users", params2)
    print(f"✓ Different params key: {key3}")
    print(f"✓ Keys are different: {key2 != key3}")


def example_8_fallback_behavior():
    """Example 8: Fallback to memory cache."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Fallback to Memory Cache")
    print("=" * 70)

    # Try to create Redis cache (will fail if Redis not available)
    # but will fall back to memory cache automatically
    config = CacheConfiguration(default_ttl=300)

    cache_mgr = CacheManager(
        backend_type=CacheBackendType.REDIS,
        redis_config={"host": "localhost", "port": 6379},
        memory_cache_size=1000,
        cache_config=config,
    )

    # Check backend status
    stats = cache_mgr.get_backend_stats()
    print(f"✓ Backend type: {stats['type']}")
    print(f"✓ Redis connected: {stats.get('connected', 'N/A')}")

    # Store data (works regardless of Redis availability)
    cache_mgr.set("test_key", {"data": "test"}, "/api/test")
    value = cache_mgr.get("test_key", "/api/test")
    print(f"✓ Data stored and retrieved: {value}")

    if stats["type"] == "memory":
        print("✓ Using memory cache (Redis not available)")
    else:
        print("✓ Using Redis cache")


def example_9_invalidation_triggers():
    """Example 9: Invalidation triggers."""
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Cache Invalidation Triggers")
    print("=" * 70)

    cache_mgr = CacheManager(backend_type=CacheBackendType.MEMORY)

    # Register invalidation patterns
    cache_mgr.register_invalidation_trigger("/api/users:update", "/api/users:*")
    cache_mgr.register_invalidation_trigger("/api/users:delete", "/api/user:*")

    print("✓ Registered invalidation trigger for /api/users:update → /api/users:*")
    print("✓ Registered invalidation trigger for /api/users:delete → /api/user:*")

    # Populate cache
    for i in range(3):
        cache_mgr.set(f"/api/users:{i}", {"id": i}, "/api/users")

    print("✓ Populated cache with /api/users:0, /api/users:1, /api/users:2")

    # Trigger invalidation
    cache_mgr.on_update("/api/users:update")
    print("✓ Called on_update('/api/users:update')")

    # Verify cache is cleared
    value = cache_mgr.get("/api/users:0", "/api/users")
    print(f"✓ After invalidation, cache contains: {value}")


def main():
    """Run all examples."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     Production Cache Manager - Quick Start Examples             ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    examples = [
        ("Basic Caching", example_1_basic_caching),
        ("TTL Configuration", example_2_cache_ttl),
        ("Decorator Pattern", example_3_decorated_function),
        ("Cache Invalidation", example_4_cache_invalidation),
        ("Cache Warming", example_5_cache_warming),
        ("Metrics & Monitoring", example_6_metrics),
        ("Key Generation", example_7_key_generation),
        ("Fallback Behavior", example_8_fallback_behavior),
        ("Invalidation Triggers", example_9_invalidation_triggers),
    ]

    for i, (name, example_func) in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the FastAPI example: python fastapi_cache_example.py")
    print("2. Run the test suite: python -m pytest test_cache_manager.py -v")
    print("3. Run benchmarks: python benchmark_cache.py")
    print("4. Read the guide: CACHE_IMPLEMENTATION_GUIDE.md")
    print()


if __name__ == "__main__":
    main()
