"""
Production-grade API caching layer with Redis integration and fallback support.
Features: configurable TTL, cache warming, invalidation, and comprehensive metrics.
"""

import json
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from functools import wraps
from enum import Enum
import threading
from collections import defaultdict

try:
    import redis
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class CacheMetricType(Enum):
    """Cache operation metric types."""
    HIT = "hit"
    MISS = "miss"
    SET = "set"
    INVALIDATE = "invalidate"
    EVICT = "evict"
    ERROR = "error"


class CacheBackendType(Enum):
    """Supported cache backend types."""
    REDIS = "redis"
    MEMORY = "memory"


class CacheMetrics:
    """Track cache performance metrics."""

    def __init__(self):
        self._metrics: Dict[str, Dict[CacheMetricType, int]] = defaultdict(
            lambda: {metric_type: 0 for metric_type in CacheMetricType}
        )
        self._lock = threading.RLock()
        self._start_time = time.time()

    def record(self, endpoint: str, metric_type: CacheMetricType) -> None:
        """Record a cache metric."""
        with self._lock:
            self._metrics[endpoint][metric_type] += 1

    def get_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for an endpoint or all endpoints."""
        with self._lock:
            if endpoint:
                if endpoint not in self._metrics:
                    return {}
                metrics = self._metrics[endpoint].copy()
                total_requests = sum(metrics.values())
                hit_rate = (
                    (metrics[CacheMetricType.HIT] / total_requests * 100)
                    if total_requests > 0
                    else 0
                )
                return {
                    "endpoint": endpoint,
                    "metrics": {k.value: v for k, v in metrics.items()},
                    "total_requests": total_requests,
                    "hit_rate_percent": round(hit_rate, 2),
                }
            else:
                all_metrics = {}
                for ep, metrics in self._metrics.items():
                    total = sum(metrics.values())
                    hit_rate = (
                        (metrics[CacheMetricType.HIT] / total * 100)
                        if total > 0
                        else 0
                    )
                    all_metrics[ep] = {
                        "metrics": {k.value: v for k, v in metrics.items()},
                        "total_requests": total,
                        "hit_rate_percent": round(hit_rate, 2),
                    }
                return all_metrics

    def reset(self, endpoint: Optional[str] = None) -> None:
        """Reset metrics."""
        with self._lock:
            if endpoint:
                if endpoint in self._metrics:
                    del self._metrics[endpoint]
            else:
                self._metrics.clear()


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in cache with TTL in seconds."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all keys from cache."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics."""
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache backend with TTL support."""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._max_size = max_size
        self._lock = threading.RLock()
        self._access_count: Dict[str, int] = defaultdict(int)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None

            self._access_count[key] += 1
            return value

    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in cache with TTL."""
        with self._lock:
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_lru()

            expiry = time.time() + ttl
            self._cache[key] = (value, expiry)
            return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            if key not in self._cache:
                return False
            _, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return False
            return True

    def clear(self) -> bool:
        """Clear all keys from cache."""
        with self._lock:
            self._cache.clear()
            self._access_count.clear()
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            expired_count = sum(
                1
                for _, (_, expiry) in self._cache.items()
                if time.time() > expiry
            )
            return {
                "type": "memory",
                "size": len(self._cache),
                "max_size": self._max_size,
                "expired_entries": expired_count,
                "utilization_percent": round(
                    (len(self._cache) / self._max_size * 100), 2
                ),
            }

    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._cache:
            return
        lru_key = min(self._access_count, key=self._access_count.get)
        if lru_key in self._cache:
            del self._cache[lru_key]
            del self._access_count[lru_key]


class RedisCache(CacheBackend):
    """Redis cache backend."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        connection_pool_kwargs: Optional[Dict[str, Any]] = None,
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required for RedisCache")

        self._host = host
        self._port = port
        self._db = db
        self._client: Optional[redis.Redis] = None
        self._connected = False
        self._connection_pool_kwargs = connection_pool_kwargs or {}

        self._connect(password)

    def _connect(self, password: Optional[str] = None) -> None:
        """Establish Redis connection."""
        try:
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                **self._connection_pool_kwargs,
            )
            self._client.ping()
            self._connected = True
            logger.info(
                f"Connected to Redis at {self._host}:{self._port}/{self._db}"
            )
        except (RedisConnectionError, RedisError) as e:
            self._connected = False
            logger.warning(f"Failed to connect to Redis: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self._connected or not self._client:
            return None

        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except RedisError as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in Redis with TTL."""
        if not self._connected or not self._client:
            return False

        try:
            serialized = json.dumps(value)
            self._client.setex(key, ttl, serialized)
            return True
        except (RedisError, TypeError) as e:
            logger.error(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._connected or not self._client:
            return False

        try:
            result = self._client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._connected or not self._client:
            return False

        try:
            return bool(self._client.exists(key))
        except RedisError as e:
            logger.error(f"Redis exists error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all keys from Redis database."""
        if not self._connected or not self._client:
            return False

        try:
            self._client.flushdb()
            return True
        except RedisError as e:
            logger.error(f"Redis clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics."""
        if not self._connected or not self._client:
            return {"type": "redis", "connected": False}

        try:
            info = self._client.info()
            return {
                "type": "redis",
                "connected": True,
                "host": self._host,
                "port": self._port,
                "db": self._db,
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        except RedisError as e:
            logger.error(f"Redis stats error: {e}")
            return {"type": "redis", "connected": False, "error": str(e)}


class CacheConfiguration:
    """Cache configuration for endpoints."""

    def __init__(
        self,
        default_ttl: int = 300,
        enable_warming: bool = False,
        warming_interval: int = 60,
    ):
        self._endpoint_ttls: Dict[str, int] = {}
        self._warming_config: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._enable_warming = enable_warming
        self._warming_interval = warming_interval

    def set_endpoint_ttl(self, endpoint: str, ttl: int) -> None:
        """Set TTL for specific endpoint."""
        self._endpoint_ttls[endpoint] = ttl

    def get_endpoint_ttl(self, endpoint: str) -> int:
        """Get TTL for endpoint."""
        return self._endpoint_ttls.get(endpoint, self._default_ttl)

    def set_warming_strategy(
        self, endpoint: str, warmer_func: Callable, interval: Optional[int] = None
    ) -> None:
        """Configure cache warming for an endpoint."""
        self._warming_config[endpoint] = {
            "warmer_func": warmer_func,
            "interval": interval or self._warming_interval,
            "last_warmed": 0,
        }

    def get_warming_strategy(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get warming strategy for endpoint."""
        return self._warming_config.get(endpoint)

    def should_warm(self, endpoint: str) -> bool:
        """Check if endpoint should be warmed."""
        if endpoint not in self._warming_config:
            return False

        config = self._warming_config[endpoint]
        now = time.time()
        last_warmed = config.get("last_warmed", 0)
        interval = config.get("interval", self._warming_interval)

        return (now - last_warmed) >= interval

    def mark_warmed(self, endpoint: str) -> None:
        """Mark endpoint as warmed."""
        if endpoint in self._warming_config:
            self._warming_config[endpoint]["last_warmed"] = time.time()


class CacheManager:
    """Production-grade cache manager with multiple backends and features."""

    def __init__(
        self,
        backend_type: CacheBackendType = CacheBackendType.REDIS,
        redis_config: Optional[Dict[str, Any]] = None,
        memory_cache_size: int = 1000,
        cache_config: Optional[CacheConfiguration] = None,
    ):
        """
        Initialize cache manager.

        Args:
            backend_type: Primary backend (redis or memory)
            redis_config: Redis connection config
            memory_cache_size: Max entries for in-memory fallback
            cache_config: Cache configuration
        """
        self._backend: CacheBackend
        self._fallback_backend = InMemoryCache(max_size=memory_cache_size)
        self._backend_type = backend_type
        self._metrics = CacheMetrics()
        self._config = cache_config or CacheConfiguration()
        self._warming_thread: Optional[threading.Thread] = None
        self._warming_active = False
        self._invalidation_patterns: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.RLock()

        # Initialize primary backend
        if backend_type == CacheBackendType.REDIS and REDIS_AVAILABLE:
            try:
                redis_config = redis_config or {}
                self._backend = RedisCache(**redis_config)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}. Using in-memory.")
                self._backend = InMemoryCache(max_size=memory_cache_size)
        else:
            self._backend = InMemoryCache(max_size=memory_cache_size)

    def generate_cache_key(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key from endpoint and parameters."""
        key_parts = [endpoint]
        if params:
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()
            key_parts.append(params_hash)

        return ":".join(key_parts)

    def get(self, key: str, endpoint: str) -> Optional[Any]:
        """Get value from cache with fallback."""
        try:
            value = self._backend.get(key)
            if value is not None:
                self._metrics.record(endpoint, CacheMetricType.HIT)
                return value

            # Try fallback if primary fails
            if isinstance(self._backend, RedisCache):
                value = self._fallback_backend.get(key)
                if value is not None:
                    self._metrics.record(endpoint, CacheMetricType.HIT)
                    return value

            self._metrics.record(endpoint, CacheMetricType.MISS)
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._metrics.record(endpoint, CacheMetricType.ERROR)
            return None

    def set(self, key: str, value: Any, endpoint: str) -> bool:
        """Set value in cache."""
        ttl = self._config.get_endpoint_ttl(endpoint)

        try:
            success = self._backend.set(key, value, ttl)

            # Also store in fallback for reliability
            if isinstance(self._backend, RedisCache):
                self._fallback_backend.set(key, value, ttl)

            self._metrics.record(endpoint, CacheMetricType.SET)
            return success

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._metrics.record(endpoint, CacheMetricType.ERROR)
            return False

    def delete(self, key: str, endpoint: str) -> bool:
        """Delete key from cache."""
        try:
            success = self._backend.delete(key)
            if isinstance(self._backend, RedisCache):
                self._fallback_backend.delete(key)

            self._metrics.record(endpoint, CacheMetricType.INVALIDATE)
            return success

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self._metrics.record(endpoint, CacheMetricType.ERROR)
            return False

    def invalidate_pattern(self, endpoint: str, pattern: str) -> int:
        """
        Invalidate cache keys matching a pattern.
        Pattern uses wildcards: * for any characters.
        """
        invalidated = 0

        try:
            if isinstance(self._backend, RedisCache) and self._backend._connected:
                # Use Redis pattern matching
                keys = self._backend._client.keys(pattern)
                for key in keys:
                    self._backend.delete(key)
                    invalidated += 1
            else:
                # For in-memory, match against stored keys
                for key in list(self._fallback_backend._cache.keys()):
                    if self._matches_pattern(key, pattern):
                        self._fallback_backend.delete(key)
                        invalidated += 1

            self._metrics.record(endpoint, CacheMetricType.INVALIDATE)
            return invalidated

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    @staticmethod
    def _matches_pattern(key: str, pattern: str) -> bool:
        """Check if key matches wildcard pattern."""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)

    def register_invalidation_trigger(
        self, trigger_endpoint: str, invalidate_pattern: str
    ) -> None:
        """Register a cache invalidation pattern for a trigger endpoint."""
        self._invalidation_patterns[trigger_endpoint].append(invalidate_pattern)

    def on_update(self, endpoint: str) -> None:
        """Call when endpoint data is updated to invalidate dependent caches."""
        patterns = self._invalidation_patterns.get(endpoint, [])
        for pattern in patterns:
            self.invalidate_pattern(endpoint, pattern)

    def warm_cache(self, endpoint: str) -> bool:
        """Warm cache for an endpoint using configured strategy."""
        strategy = self._config.get_warming_strategy(endpoint)
        if not strategy:
            return False

        try:
            warmer_func = strategy["warmer_func"]
            warmer_func(self)
            self._config.mark_warmed(endpoint)
            return True

        except Exception as e:
            logger.error(f"Cache warming error for {endpoint}: {e}")
            return False

    def start_warming_background_tasks(self) -> None:
        """Start background thread for cache warming."""
        if self._warming_active:
            return

        self._warming_active = True
        self._warming_thread = threading.Thread(
            target=self._warming_loop, daemon=True
        )
        self._warming_thread.start()
        logger.info("Cache warming background thread started")

    def stop_warming_background_tasks(self) -> None:
        """Stop background cache warming thread."""
        self._warming_active = False
        if self._warming_thread:
            self._warming_thread.join(timeout=5)
        logger.info("Cache warming background thread stopped")

    def _warming_loop(self) -> None:
        """Background loop for cache warming."""
        while self._warming_active:
            try:
                # Get all endpoints with warming strategies
                for endpoint in list(
                    self._config._warming_config.keys()
                ):
                    if self._config.should_warm(endpoint):
                        self.warm_cache(endpoint)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Warming loop error: {e}")
                time.sleep(5)

    def get_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get cache metrics."""
        return self._metrics.get_metrics(endpoint)

    def get_backend_stats(self) -> Dict[str, Any]:
        """Get backend statistics."""
        return self._backend.get_stats()

    def clear_cache(self) -> bool:
        """Clear all cache."""
        try:
            self._backend.clear()
            self._fallback_backend.clear()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def reset_metrics(self, endpoint: Optional[str] = None) -> None:
        """Reset metrics."""
        self._metrics.reset(endpoint)


def cached(
    cache_manager: CacheManager,
    endpoint: str,
    params_key: Optional[Callable] = None,
):
    """
    Decorator for caching function results.

    Args:
        cache_manager: CacheManager instance
        endpoint: Endpoint name for metrics and TTL lookup
        params_key: Optional function to extract cache key from parameters
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if params_key:
                try:
                    cache_key = params_key(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Error generating cache key: {e}")
                    return func(*args, **kwargs)
            else:
                params_dict = {
                    "args": str(args),
                    "kwargs": json.dumps(kwargs, default=str),
                }
                cache_key = cache_manager.generate_cache_key(endpoint, params_dict)

            # Try to get from cache
            cached_value = cache_manager.get(cache_key, endpoint)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, endpoint)
            return result

        return wrapper

    return decorator


# Example usage and configuration
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create cache configuration
    config = CacheConfiguration(default_ttl=300)
    config.set_endpoint_ttl("/api/users", 600)
    config.set_endpoint_ttl("/api/posts", 300)

    # Create cache manager with Redis fallback to memory
    cache_mgr = CacheManager(
        backend_type=CacheBackendType.REDIS,
        redis_config={
            "host": "localhost",
            "port": 6379,
            "db": 0,
        },
        memory_cache_size=1000,
        cache_config=config,
    )

    # Example: Register cache warming
    def warm_users_cache(manager: CacheManager):
        """Warm users cache with popular users."""
        # This would be called periodically
        key = manager.generate_cache_key("/api/users", {"limit": 10})
        manager.set(key, [{"id": 1, "name": "User 1"}], "/api/users")

    config.set_warming_strategy("/api/users", warm_users_cache, interval=300)

    # Register invalidation triggers
    cache_mgr.register_invalidation_trigger("/api/users:update", "/api/users:*")

    # Example caching
    @cached(cache_mgr, "/api/users")
    def get_users():
        """Get users from API."""
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    # Test caching
    print("First call (miss):", get_users())
    print("Second call (hit):", get_users())

    # Get metrics
    print("\nCache Metrics:", cache_mgr.get_metrics("/api/users"))
    print("Backend Stats:", cache_mgr.get_backend_stats())

    # Cache warming
    cache_mgr.start_warming_background_tasks()
    time.sleep(2)
    cache_mgr.stop_warming_background_tasks()

    # Clear cache
    cache_mgr.clear_cache()
    print("\nCache cleared")
