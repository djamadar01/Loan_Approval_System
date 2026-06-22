# Production API Caching Layer - Implementation Guide

## Overview

A production-grade caching system with Redis integration, in-memory fallback, configurable TTL, cache warming, invalidation patterns, and comprehensive metrics.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CacheManager                             │
├─────────────────────────────────────────────────────────────┤
│  • Key generation & serialization                           │
│  • Metrics tracking (hit/miss/invalidate)                   │
│  • TTL configuration per endpoint                           │
│  • Cache invalidation patterns                              │
│  • Background warming tasks                                 │
└─────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────┐
         │                                         │
    ┌────▼─────────────┐            ┌─────────────▼──┐
    │  Primary Backend │            │ Fallback Cache │
    ├──────────────────┤            ├────────────────┤
    │ • RedisCache     │            │ InMemoryCache  │
    │ • Connection     │            │ • LRU Eviction │
    │ • JSON Serialize │            │ • Thread-safe  │
    │ • Pooling        │            │ • Max size     │
    └──────────────────┘            └────────────────┘
```

## Features

### 1. Redis Integration with Fallback
- Primary Redis backend for distributed caching
- Automatic fallback to in-memory cache on Redis unavailability
- Connection pooling and retry logic
- JSON serialization for complex objects

### 2. Configurable Cache TTL
```python
config = CacheConfiguration(default_ttl=300)
config.set_endpoint_ttl("/api/users", 600)      # 10 minutes
config.set_endpoint_ttl("/api/posts", 300)      # 5 minutes
config.set_endpoint_ttl("/api/analytics", 3600) # 1 hour
```

### 3. Cache Warming
- Proactive cache population for expensive operations
- Background thread for scheduled warming
- Custom warming strategies per endpoint
- Configurable warming intervals

### 4. Cache Invalidation
- Pattern-based invalidation with wildcards
- Invalidation triggers on data updates
- Atomic invalidation operations
- Multiple patterns per trigger

### 5. Metrics & Monitoring
- Cache hit/miss rates per endpoint
- Total requests and request distribution
- Backend statistics (memory, connections)
- Real-time metrics API endpoints

## Installation

```bash
# Required dependencies
pip install redis fastapi uvicorn pydantic

# Optional for development
pip install pytest pytest-asyncio
```

## Configuration

### Redis Configuration
```python
from cache_manager import CacheManager, CacheBackendType

cache_manager = CacheManager(
    backend_type=CacheBackendType.REDIS,
    redis_config={
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,  # Optional
        "connection_pool_kwargs": {
            "max_connections": 20,
            "socket_keepalive": True,
        }
    },
    memory_cache_size=1000,  # Fallback cache size
)
```

### In-Memory Only Configuration
```python
cache_manager = CacheManager(
    backend_type=CacheBackendType.MEMORY,
    memory_cache_size=1000,
)
```

## Usage Patterns

### 1. Basic Caching
```python
from cache_manager import CacheManager, CacheConfiguration

config = CacheConfiguration(default_ttl=300)
cache_mgr = CacheManager(cache_config=config)

# Set cache
cache_mgr.set("user:123", {"id": 123, "name": "Alice"}, "/api/users")

# Get cache
user = cache_mgr.get("user:123", "/api/users")

# Delete cache
cache_mgr.delete("user:123", "/api/users")
```

### 2. Using @cached Decorator
```python
@cached(cache_mgr, "/api/users")
def get_users():
    # Expensive operation
    return fetch_from_db()

# First call - executes function and caches result
result1 = get_users()

# Second call - returns cached result
result2 = get_users()
```

### 3. Custom Cache Key Generation
```python
def get_user_cache_key(user_id, **kwargs):
    return f"user:{user_id}"

@cached(cache_mgr, "/api/user", params_key=get_user_cache_key)
def get_user(user_id):
    return fetch_user(user_id)

# Cache keys: user:1, user:2, etc.
```

### 4. Cache Warming
```python
def warm_popular_users(manager):
    """Warm cache with popular users."""
    popular = fetch_popular_users()
    for user in popular:
        key = manager.generate_cache_key("/api/users", {"id": user.id})
        manager.set(key, user, "/api/users")

config.set_warming_strategy(
    "/api/users",
    warm_popular_users,
    interval=300  # Warm every 5 minutes
)

# Start background warming
cache_mgr.start_warming_background_tasks()
```

### 5. Cache Invalidation
```python
# Invalidate specific key
cache_mgr.delete("user:123", "/api/users")

# Invalidate pattern
cache_mgr.invalidate_pattern("/api/users", "user:*")

# Register invalidation triggers
cache_mgr.register_invalidation_trigger(
    "/api/users:update",
    "/api/users:*"
)

# When user is updated, invalidate user caches
cache_mgr.on_update("/api/users:update")
```

### 6. Metrics & Monitoring
```python
# Get metrics for specific endpoint
metrics = cache_mgr.get_metrics("/api/users")
print(metrics)
# {
#     "endpoint": "/api/users",
#     "metrics": {
#         "hit": 45,
#         "miss": 12,
#         "set": 12,
#         "invalidate": 2,
#         "evict": 0,
#         "error": 0
#     },
#     "total_requests": 57,
#     "hit_rate_percent": 78.95
# }

# Get all metrics
all_metrics = cache_mgr.get_metrics()

# Get backend stats
stats = cache_mgr.get_backend_stats()
print(stats)
# {
#     "type": "redis",
#     "connected": True,
#     "used_memory_mb": 12.34,
#     "connected_clients": 5,
#     "total_commands_processed": 1000
# }
```

## FastAPI Integration

### Basic Setup
```python
from fastapi import FastAPI
from cache_manager import CacheManager, CacheConfiguration

app = FastAPI()

# Initialize cache manager
config = CacheConfiguration(default_ttl=300)
cache_mgr = CacheManager(cache_config=config)

@app.on_event("startup")
async def startup():
    cache_mgr.start_warming_background_tasks()

@app.on_event("shutdown")
async def shutdown():
    cache_mgr.stop_warming_background_tasks()
```

### Caching Endpoint Response
```python
@app.get("/api/users")
async def get_users(skip: int = 0, limit: int = 10):
    cache_key = cache_mgr.generate_cache_key(
        "/api/users",
        {"skip": skip, "limit": limit}
    )
    
    # Try cache first
    cached = cache_mgr.get(cache_key, "/api/users")
    if cached:
        return cached
    
    # Fetch and cache
    users = await fetch_users(skip, limit)
    cache_mgr.set(cache_key, users, "/api/users")
    return users
```

### Cache Invalidation on Update
```python
from fastapi import BackgroundTasks

@app.post("/api/users")
async def create_user(user: User, background_tasks: BackgroundTasks):
    # Create user
    created = await db.create_user(user)
    
    # Invalidate user list cache in background
    background_tasks.add_task(
        cache_mgr.invalidate_pattern,
        "/api/users",
        "/api/users:*"
    )
    
    return created
```

### Cache Metrics Endpoint
```python
@app.get("/cache/metrics")
async def get_cache_metrics(endpoint: Optional[str] = None):
    return cache_mgr.get_metrics(endpoint)

@app.get("/cache/stats")
async def get_cache_stats():
    return cache_mgr.get_backend_stats()

@app.post("/cache/clear")
async def clear_cache():
    cache_mgr.clear_cache()
    return {"status": "cleared"}
```

## Performance Considerations

### Cache Hit Rate Targets
- **Warm data**: 80-95% hit rate (popular users, trending posts)
- **Moderate data**: 60-80% hit rate (search results, analytics)
- **Cold data**: 20-40% hit rate (user-specific data)

### TTL Configuration Guidelines
- **Frequently accessed, infrequently changed**: 10-30 minutes
- **Moderately accessed**: 5-10 minutes
- **Expensive computations**: 30-60 minutes
- **Real-time data**: 1-5 minutes

### In-Memory Cache Size
- Set based on typical working set size
- Monitor LRU evictions
- Adjust if eviction rate > 5%

### Redis Configuration
- Use connection pooling for concurrency
- Monitor memory usage (typical: 1-2 bytes per cached item)
- Use separate Redis databases for different environments

## Testing

### Run Test Suite
```bash
python -m pytest test_cache_manager.py -v
```

### Test Coverage
- In-memory cache operations
- Redis integration and fallback
- TTL expiration
- Pattern matching and invalidation
- Cache warming
- Metrics tracking
- Error handling

## Troubleshooting

### Redis Connection Issues
```python
# Check connection status
stats = cache_mgr.get_backend_stats()
print(stats["connected"])

# Check logs for connection errors
import logging
logging.getLogger("cache_manager").setLevel(logging.DEBUG)
```

### Low Cache Hit Rate
```python
# Analyze metrics
metrics = cache_mgr.get_metrics()
for endpoint, data in metrics.items():
    hit_rate = data["hit_rate_percent"]
    if hit_rate < 50:
        print(f"Low hit rate for {endpoint}: {hit_rate}%")
        # Consider: increase TTL, improve cache key generation, add warming
```

### High Memory Usage
```python
# Check in-memory cache size
stats = cache_mgr.get_backend_stats()
if stats["type"] == "memory":
    utilization = stats["utilization_percent"]
    print(f"Cache utilization: {utilization}%")
    # Consider: reduce memory_cache_size, implement more aggressive eviction
```

### Stale Cache Issues
```python
# Reduce TTL for problematic endpoints
config.set_endpoint_ttl("/api/volatile-data", 60)

# Or manually invalidate after updates
cache_mgr.on_update("/api/endpoint:update")
```

## Production Deployment

### Environment Variables
```bash
# Redis configuration
REDIS_HOST=redis.internal
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=secret

# Cache configuration
DEFAULT_CACHE_TTL=300
CACHE_MAX_SIZE=10000
CACHE_WARMING_ENABLED=true
```

### Monitoring Setup
```python
# Export metrics to Prometheus
from prometheus_client import Counter, Gauge

cache_hits = Counter('cache_hits', 'Cache hits', ['endpoint'])
cache_misses = Counter('cache_misses', 'Cache misses', ['endpoint'])
cache_size = Gauge('cache_size', 'Cache size in bytes')

# Update metrics
metrics = cache_mgr.get_metrics(endpoint)
cache_hits.labels(endpoint=endpoint).inc(metrics["metrics"]["hit"])
cache_misses.labels(endpoint=endpoint).inc(metrics["metrics"]["miss"])
```

### Alerting
```python
# Alert on low hit rate
ALERT_HIT_RATE_THRESHOLD = 0.5

metrics = cache_mgr.get_metrics()
for endpoint, data in metrics.items():
    if data["hit_rate_percent"] / 100 < ALERT_HIT_RATE_THRESHOLD:
        send_alert(f"Low cache hit rate for {endpoint}")

# Alert on Redis connection loss
if not cache_mgr.get_backend_stats().get("connected"):
    send_alert("Redis connection lost, using memory fallback")
```

## Advanced Patterns

### Distributed Cache Warming
```python
# Warm cache from database in batches
def warm_users_cache_batch(manager, batch_size=100):
    users = fetch_users_batch(batch_size)
    for user in users:
        key = manager.generate_cache_key(
            "/api/users",
            {"id": user.id}
        )
        manager.set(key, user, "/api/users")

# Schedule with APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    warm_users_cache_batch,
    'interval',
    minutes=5,
    args=[cache_mgr]
)
scheduler.start()
```

### Cache Preloading
```python
# Preload cache on startup
def preload_cache():
    # Load critical data
    popular_users = fetch_popular_users()
    for user in popular_users:
        key = cache_mgr.generate_cache_key("/api/users", {"id": user.id})
        cache_mgr.set(key, user, "/api/users")

# Call on app startup
app.add_event_handler("startup", preload_cache)
```

### Conditional Caching
```python
# Only cache if certain conditions are met
def should_cache(endpoint, response):
    if endpoint == "/api/large-data" and len(response) > 100:
        return False
    return True

# In decorator
if should_cache(endpoint, result):
    cache_mgr.set(cache_key, result, endpoint)
```

## References

- FastAPI Caching: https://fastapi.tiangolo.com/
- Redis Documentation: https://redis.io/documentation
- Cache Design Patterns: https://martinfowler.com/bliki/CacheAsidePattern.html
