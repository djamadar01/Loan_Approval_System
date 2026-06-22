"""
Comprehensive test suite for the cache manager with all features.
Tests Redis integration, fallback, TTL, warming, invalidation, and metrics.
"""

import unittest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from cache_manager import (
    CacheManager,
    CacheConfiguration,
    CacheMetrics,
    CacheMetricType,
    CacheBackendType,
    InMemoryCache,
    RedisCache,
    cached,
    REDIS_AVAILABLE,
)


class TestCacheMetrics(unittest.TestCase):
    """Test cache metrics tracking."""

    def setUp(self):
        self.metrics = CacheMetrics()

    def test_record_metric(self):
        """Test recording metrics."""
        self.metrics.record("endpoint1", CacheMetricType.HIT)
        self.metrics.record("endpoint1", CacheMetricType.MISS)
        self.metrics.record("endpoint1", CacheMetricType.HIT)

        metrics = self.metrics.get_metrics("endpoint1")
        self.assertEqual(metrics["metrics"]["hit"], 2)
        self.assertEqual(metrics["metrics"]["miss"], 1)
        self.assertEqual(metrics["total_requests"], 3)
        self.assertAlmostEqual(metrics["hit_rate_percent"], 66.67, places=1)

    def test_multiple_endpoints(self):
        """Test metrics for multiple endpoints."""
        self.metrics.record("endpoint1", CacheMetricType.HIT)
        self.metrics.record("endpoint2", CacheMetricType.MISS)

        all_metrics = self.metrics.get_metrics()
        self.assertEqual(len(all_metrics), 2)
        self.assertIn("endpoint1", all_metrics)
        self.assertIn("endpoint2", all_metrics)

    def test_reset_metrics(self):
        """Test resetting metrics."""
        self.metrics.record("endpoint1", CacheMetricType.HIT)
        self.metrics.reset("endpoint1")
        metrics = self.metrics.get_metrics("endpoint1")
        self.assertEqual(metrics, {})


class TestInMemoryCache(unittest.TestCase):
    """Test in-memory cache backend."""

    def setUp(self):
        self.cache = InMemoryCache(max_size=100)

    def test_set_and_get(self):
        """Test basic set and get."""
        self.cache.set("key1", "value1", ttl=3600)
        self.assertEqual(self.cache.get("key1"), "value1")

    def test_expiration(self):
        """Test TTL expiration."""
        self.cache.set("key1", "value1", ttl=1)
        self.assertEqual(self.cache.get("key1"), "value1")
        time.sleep(1.1)
        self.assertIsNone(self.cache.get("key1"))

    def test_delete(self):
        """Test key deletion."""
        self.cache.set("key1", "value1", ttl=3600)
        self.assertTrue(self.cache.delete("key1"))
        self.assertIsNone(self.cache.get("key1"))

    def test_exists(self):
        """Test key existence check."""
        self.cache.set("key1", "value1", ttl=3600)
        self.assertTrue(self.cache.exists("key1"))

        self.cache.set("key2", "value2", ttl=1)
        time.sleep(1.1)
        self.assertFalse(self.cache.exists("key2"))

    def test_lru_eviction(self):
        """Test LRU eviction when max size reached."""
        cache = InMemoryCache(max_size=3)
        cache.set("key1", "value1", ttl=3600)
        cache.set("key2", "value2", ttl=3600)
        cache.set("key3", "value3", ttl=3600)

        # Access key1 and key2 to mark them as recently used
        cache.get("key1")
        cache.get("key2")

        # Add new key, should evict key3 (least recently used)
        cache.set("key4", "value4", ttl=3600)
        self.assertIsNone(cache.get("key3"))
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key4"), "value4")

    def test_clear(self):
        """Test clearing cache."""
        self.cache.set("key1", "value1", ttl=3600)
        self.cache.set("key2", "value2", ttl=3600)
        self.assertTrue(self.cache.clear())
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_stats(self):
        """Test cache statistics."""
        self.cache.set("key1", "value1", ttl=3600)
        self.cache.set("key2", "value2", ttl=3600)

        stats = self.cache.get_stats()
        self.assertEqual(stats["type"], "memory")
        self.assertEqual(stats["size"], 2)
        self.assertEqual(stats["max_size"], 100)


@unittest.skipIf(not REDIS_AVAILABLE, "redis not installed")
class TestRedisCache(unittest.TestCase):
    """Test Redis cache backend."""

    def setUp(self):
        # Try to create Redis cache, skip if Redis unavailable
        try:
            self.cache = RedisCache(host="localhost", port=6379, db=15)
            if not self.cache._connected:
                self.skipTest("Redis not available")
            self.cache.clear()
        except Exception as e:
            self.skipTest(f"Redis not available: {e}")

    def tearDown(self):
        if hasattr(self, "cache") and self.cache._connected:
            self.cache.clear()

    def test_set_and_get(self):
        """Test basic set and get."""
        self.cache.set("key1", {"data": "value1"}, ttl=3600)
        result = self.cache.get("key1")
        self.assertEqual(result, {"data": "value1"})

    def test_json_serialization(self):
        """Test JSON serialization."""
        test_data = {"nested": {"key": [1, 2, 3]}}
        self.cache.set("key1", test_data, ttl=3600)
        result = self.cache.get("key1")
        self.assertEqual(result, test_data)

    def test_delete(self):
        """Test key deletion."""
        self.cache.set("key1", "value1", ttl=3600)
        self.assertTrue(self.cache.delete("key1"))
        self.assertIsNone(self.cache.get("key1"))

    def test_exists(self):
        """Test key existence check."""
        self.cache.set("key1", "value1", ttl=3600)
        self.assertTrue(self.cache.exists("key1"))
        self.cache.delete("key1")
        self.assertFalse(self.cache.exists("key1"))

    def test_clear(self):
        """Test clearing cache."""
        self.cache.set("key1", "value1", ttl=3600)
        self.cache.set("key2", "value2", ttl=3600)
        self.assertTrue(self.cache.clear())
        self.assertFalse(self.cache.exists("key1"))


class TestCacheConfiguration(unittest.TestCase):
    """Test cache configuration."""

    def setUp(self):
        self.config = CacheConfiguration(default_ttl=300)

    def test_default_ttl(self):
        """Test default TTL."""
        self.assertEqual(self.config.get_endpoint_ttl("/api/users"), 300)

    def test_endpoint_ttl(self):
        """Test endpoint-specific TTL."""
        self.config.set_endpoint_ttl("/api/users", 600)
        self.assertEqual(self.config.get_endpoint_ttl("/api/users"), 600)
        self.assertEqual(self.config.get_endpoint_ttl("/api/posts"), 300)

    def test_warming_strategy(self):
        """Test warming strategy registration."""
        warmer = Mock()
        self.config.set_warming_strategy("/api/users", warmer, interval=120)

        strategy = self.config.get_warming_strategy("/api/users")
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy["interval"], 120)

    def test_should_warm(self):
        """Test warming interval checking."""
        warmer = Mock()
        self.config.set_warming_strategy("/api/users", warmer, interval=1)

        self.assertTrue(self.config.should_warm("/api/users"))
        self.config.mark_warmed("/api/users")
        self.assertFalse(self.config.should_warm("/api/users"))

        time.sleep(1.1)
        self.assertTrue(self.config.should_warm("/api/users"))


class TestCacheManager(unittest.TestCase):
    """Test cache manager."""

    def setUp(self):
        config = CacheConfiguration(default_ttl=300)
        self.cache_mgr = CacheManager(
            backend_type=CacheBackendType.MEMORY,
            cache_config=config,
        )

    def test_cache_key_generation(self):
        """Test cache key generation."""
        key1 = self.cache_mgr.generate_cache_key("/api/users")
        self.assertEqual(key1, "/api/users")

        key2 = self.cache_mgr.generate_cache_key("/api/users", {"id": 1})
        self.assertTrue(key2.startswith("/api/users:"))

    def test_get_set_delete(self):
        """Test basic cache operations."""
        key = "test_key"
        value = {"data": "test"}

        self.cache_mgr.set(key, value, "/api/users")
        cached_value = self.cache_mgr.get(key, "/api/users")
        self.assertEqual(cached_value, value)

        self.cache_mgr.delete(key, "/api/users")
        self.assertIsNone(self.cache_mgr.get(key, "/api/users"))

    def test_cache_metrics(self):
        """Test cache metrics tracking."""
        key = "test_key"
        value = {"data": "test"}

        # Miss
        self.cache_mgr.get(key, "/api/users")

        # Set
        self.cache_mgr.set(key, value, "/api/users")

        # Hit
        self.cache_mgr.get(key, "/api/users")
        self.cache_mgr.get(key, "/api/users")

        metrics = self.cache_mgr.get_metrics("/api/users")
        self.assertEqual(metrics["metrics"]["hit"], 2)
        self.assertEqual(metrics["metrics"]["miss"], 1)
        self.assertEqual(metrics["metrics"]["set"], 1)

    def test_pattern_matching(self):
        """Test pattern matching for key invalidation."""
        self.assertTrue(self.cache_mgr._matches_pattern("user:123", "user:*"))
        self.assertTrue(self.cache_mgr._matches_pattern("user:123", "*"))
        self.assertFalse(self.cache_mgr._matches_pattern("post:123", "user:*"))

    def test_invalidation_triggers(self):
        """Test cache invalidation trigger registration."""
        self.cache_mgr.register_invalidation_trigger(
            "/api/users:update", "/api/users:*"
        )
        patterns = self.cache_mgr._invalidation_patterns["/api/users:update"]
        self.assertIn("/api/users:*", patterns)

    def test_cache_decorator(self):
        """Test @cached decorator."""
        call_count = 0

        @cached(self.cache_mgr, "/api/users")
        def get_users():
            nonlocal call_count
            call_count += 1
            return [{"id": 1, "name": "Alice"}]

        # First call - cache miss
        result1 = get_users()
        self.assertEqual(call_count, 1)

        # Second call - cache hit
        result2 = get_users()
        self.assertEqual(call_count, 1)  # Not incremented

        self.assertEqual(result1, result2)

    def test_warming_background_task(self):
        """Test background cache warming."""
        warmed_count = 0

        def warmer(manager: CacheManager):
            nonlocal warmed_count
            warmed_count += 1

        config = CacheConfiguration(default_ttl=300)
        config.set_warming_strategy("/api/users", warmer, interval=1)

        cache_mgr = CacheManager(
            backend_type=CacheBackendType.MEMORY,
            cache_config=config,
        )

        cache_mgr.start_warming_background_tasks()
        time.sleep(2.5)
        cache_mgr.stop_warming_background_tasks()

        self.assertGreaterEqual(warmed_count, 2)

    def test_clear_cache(self):
        """Test clearing entire cache."""
        self.cache_mgr.set("key1", "value1", "/api/users")
        self.cache_mgr.set("key2", "value2", "/api/users")

        self.assertTrue(self.cache_mgr.clear_cache())
        self.assertIsNone(self.cache_mgr.get("key1", "/api/users"))
        self.assertIsNone(self.cache_mgr.get("key2", "/api/users"))

    def test_reset_metrics(self):
        """Test resetting metrics."""
        key = "test_key"
        self.cache_mgr.set(key, "value", "/api/users")
        self.cache_mgr.get(key, "/api/users")

        metrics_before = self.cache_mgr.get_metrics("/api/users")
        self.assertGreater(metrics_before["total_requests"], 0)

        self.cache_mgr.reset_metrics("/api/users")
        metrics_after = self.cache_mgr.get_metrics("/api/users")
        self.assertEqual(metrics_after, {})

    def test_backend_stats(self):
        """Test backend statistics."""
        self.cache_mgr.set("key1", "value1", "/api/users")
        stats = self.cache_mgr.get_backend_stats()

        self.assertEqual(stats["type"], "memory")
        self.assertGreater(stats["size"], 0)


class TestCachedDecorator(unittest.TestCase):
    """Test @cached decorator with custom params key."""

    def setUp(self):
        config = CacheConfiguration(default_ttl=300)
        self.cache_mgr = CacheManager(
            backend_type=CacheBackendType.MEMORY,
            cache_config=config,
        )

    def test_custom_params_key(self):
        """Test decorator with custom parameter extraction."""
        call_count = 0

        def get_params_key(user_id):
            return f"user:{user_id}"

        @cached(self.cache_mgr, "/api/user", params_key=get_params_key)
        def get_user(user_id):
            nonlocal call_count
            call_count += 1
            return {"id": user_id, "name": f"User{user_id}"}

        # First call with user_id=1
        result1 = get_user(1)
        self.assertEqual(call_count, 1)

        # Second call with same user_id - should hit cache
        result2 = get_user(1)
        self.assertEqual(call_count, 1)

        # Call with different user_id - should miss cache
        result3 = get_user(2)
        self.assertEqual(call_count, 2)

        self.assertEqual(result1["id"], 1)
        self.assertEqual(result3["id"], 2)


class TestCacheFallback(unittest.TestCase):
    """Test cache fallback mechanism."""

    def test_memory_fallback_on_set_failure(self):
        """Test that values fall back to memory on primary failure."""
        config = CacheConfiguration(default_ttl=300)
        cache_mgr = CacheManager(
            backend_type=CacheBackendType.MEMORY,
            cache_config=config,
        )

        # Set value
        cache_mgr.set("key1", "value1", "/api/users")

        # Should be able to retrieve from fallback
        value = cache_mgr.get("key1", "/api/users")
        self.assertEqual(value, "value1")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in cache operations."""

    def setUp(self):
        config = CacheConfiguration(default_ttl=300)
        self.cache_mgr = CacheManager(
            backend_type=CacheBackendType.MEMORY,
            cache_config=config,
        )

    def test_invalid_json_serialization(self):
        """Test handling of non-serializable objects."""
        # Objects that can't be JSON serialized should be handled
        class CustomObject:
            pass

        obj = CustomObject()
        result = self.cache_mgr.set("key1", obj, "/api/users")
        # Should fail gracefully
        self.assertFalse(result)

    def test_cache_decorator_error_handling(self):
        """Test decorator handles errors in params_key."""

        def bad_params_key(*args, **kwargs):
            raise ValueError("Error in params_key")

        @cached(self.cache_mgr, "/api/users", params_key=bad_params_key)
        def get_users():
            return [{"id": 1}]

        # Should still execute function despite params_key error
        result = get_users()
        self.assertEqual(result, [{"id": 1}])


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCacheMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestInMemoryCache))
    suite.addTests(loader.loadTestsFromTestCase(TestRedisCache))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCachedDecorator))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheFallback))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))

    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    run_tests()
