"""
Production FastAPI integration example with caching layer.
Demonstrates real-world usage patterns for API caching.
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime
import asyncio

from cache_manager import (
    CacheManager,
    CacheConfiguration,
    CacheBackendType,
    cached,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Cached API Example")

# ============================================================================
# Cache Setup
# ============================================================================

# Create cache configuration with different TTLs per endpoint
cache_config = CacheConfiguration(default_ttl=300)

# Configure per-endpoint TTLs
cache_config.set_endpoint_ttl("/api/users", 600)  # 10 minutes
cache_config.set_endpoint_ttl("/api/posts", 300)  # 5 minutes
cache_config.set_endpoint_ttl("/api/analytics", 3600)  # 1 hour

# Initialize cache manager (Redis with memory fallback)
cache_manager = CacheManager(
    backend_type=CacheBackendType.REDIS,
    redis_config={
        "host": "localhost",
        "port": 6379,
        "db": 0,
    },
    memory_cache_size=1000,
    cache_config=cache_config,
)

# ============================================================================
# Models
# ============================================================================


class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: str


class Post(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    created_at: str


class AnalyticsData(BaseModel):
    metric: str
    value: float
    timestamp: str


# ============================================================================
# Mock Database Simulation
# ============================================================================

# Simulated database
USERS_DB = [
    User(id=1, name="Alice", email="alice@example.com", created_at="2024-01-01"),
    User(id=2, name="Bob", email="bob@example.com", created_at="2024-01-02"),
    User(id=3, name="Charlie", email="charlie@example.com", created_at="2024-01-03"),
]

POSTS_DB = [
    Post(
        id=1,
        user_id=1,
        title="First Post",
        content="Hello World",
        created_at="2024-01-01",
    ),
    Post(
        id=2,
        user_id=1,
        title="Second Post",
        content="Python Tips",
        created_at="2024-01-02",
    ),
    Post(
        id=3,
        user_id=2,
        title="Bob's Post",
        content="FastAPI Guide",
        created_at="2024-01-03",
    ),
]

# ============================================================================
# Cache Warming Strategies
# ============================================================================


def warm_popular_users(cache_mgr: CacheManager) -> None:
    """Warm cache with popular users."""
    logger.info("Warming popular users cache...")
    popular_users = [u for u in USERS_DB[:2]]  # Top 2 users
    key = cache_mgr.generate_cache_key("/api/users", {"popular": True})
    cache_mgr.set(key, [u.dict() for u in popular_users], "/api/users")


def warm_trending_posts(cache_mgr: CacheManager) -> None:
    """Warm cache with trending posts."""
    logger.info("Warming trending posts cache...")
    trending = [p for p in POSTS_DB[:1]]  # Top post
    key = cache_mgr.generate_cache_key("/api/posts", {"trending": True})
    cache_mgr.set(key, [p.dict() for p in trending], "/api/posts")


# Configure cache warming
cache_config.set_warming_strategy("/api/users", warm_popular_users, interval=300)
cache_config.set_warming_strategy("/api/posts", warm_trending_posts, interval=300)

# Register invalidation patterns
# When a user is updated, invalidate user list caches
cache_manager.register_invalidation_trigger("/api/users:update", "/api/users:*")
# When a post is created, invalidate post list and analytics caches
cache_manager.register_invalidation_trigger("/api/posts:create", "/api/posts:*")
cache_manager.register_invalidation_trigger("/api/posts:create", "/api/analytics:*")

# ============================================================================
# Endpoints
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Start background cache warming on app startup."""
    logger.info("Starting cache warming background tasks...")
    cache_manager.start_warming_background_tasks()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop cache warming on app shutdown."""
    logger.info("Stopping cache warming background tasks...")
    cache_manager.stop_warming_background_tasks()


@app.get("/api/users", response_model=List[User])
async def get_users(
    popular: bool = False,
    limit: int = Query(10, ge=1, le=100),
):
    """
    Get list of users.
    Results are cached based on parameters.
    """
    # Generate cache key based on query parameters
    cache_key = cache_manager.generate_cache_key(
        "/api/users", {"popular": popular, "limit": limit}
    )

    # Try to get from cache
    cached_result = cache_manager.get(cache_key, "/api/users")
    if cached_result is not None:
        logger.info(f"Cache HIT for /api/users with popular={popular}")
        return cached_result

    logger.info(f"Cache MISS for /api/users with popular={popular}")

    # Query database (simulated delay)
    await asyncio.sleep(0.1)
    if popular:
        users = USERS_DB[:2]
    else:
        users = USERS_DB[:limit]

    # Cache the result
    cache_manager.set(cache_key, [u.dict() for u in users], "/api/users")

    return users


@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Get a specific user by ID.
    Cached with custom key generation.
    """
    cache_key = cache_manager.generate_cache_key("/api/users", {"id": user_id})

    # Check cache
    cached_result = cache_manager.get(cache_key, "/api/users")
    if cached_result is not None:
        logger.info(f"Cache HIT for /api/users/{user_id}")
        return cached_result

    logger.info(f"Cache MISS for /api/users/{user_id}")

    # Query database
    await asyncio.sleep(0.05)
    user = next((u for u in USERS_DB if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cache the result
    cache_manager.set(cache_key, user.dict(), "/api/users")

    return user


@app.post("/api/users")
async def create_user(user: User, background_tasks: BackgroundTasks):
    """
    Create a new user.
    Invalidates user list cache on creation.
    """
    USERS_DB.append(user)
    logger.info(f"Created user {user.id}")

    # Invalidate caches in background
    background_tasks.add_task(cache_manager.on_update, "/api/users:update")

    return {"status": "created", "user": user}


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user: User, background_tasks: BackgroundTasks):
    """
    Update an existing user.
    Invalidates relevant caches.
    """
    existing_user = next((u for u in USERS_DB if u.id == user_id), None)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user
    idx = USERS_DB.index(existing_user)
    USERS_DB[idx] = user

    logger.info(f"Updated user {user_id}")

    # Invalidate specific user cache and user list caches
    background_tasks.add_task(
        cache_manager.invalidate_pattern, "/api/users", f"/api/users:*{user_id}*"
    )
    background_tasks.add_task(cache_manager.on_update, "/api/users:update")

    return {"status": "updated", "user": user}


@app.get("/api/posts", response_model=List[Post])
async def get_posts(
    user_id: Optional[int] = None,
    trending: bool = False,
    limit: int = Query(10, ge=1, le=100),
):
    """
    Get list of posts.
    Supports filtering by user and trending flag.
    Results are cached.
    """
    cache_key = cache_manager.generate_cache_key(
        "/api/posts", {"user_id": user_id, "trending": trending, "limit": limit}
    )

    cached_result = cache_manager.get(cache_key, "/api/posts")
    if cached_result is not None:
        logger.info(f"Cache HIT for /api/posts with user_id={user_id}")
        return cached_result

    logger.info(f"Cache MISS for /api/posts with user_id={user_id}")

    # Query database (simulated delay)
    await asyncio.sleep(0.15)
    posts = POSTS_DB

    if user_id:
        posts = [p for p in posts if p.user_id == user_id]

    if trending:
        posts = posts[:1]

    posts = posts[:limit]

    # Cache result
    cache_manager.set(cache_key, [p.dict() for p in posts], "/api/posts")

    return posts


@app.post("/api/posts")
async def create_post(post: Post, background_tasks: BackgroundTasks):
    """
    Create a new post.
    Invalidates post and analytics caches.
    """
    POSTS_DB.append(post)
    logger.info(f"Created post {post.id}")

    # Invalidate related caches
    background_tasks.add_task(cache_manager.on_update, "/api/posts:create")

    return {"status": "created", "post": post}


@app.get("/api/analytics")
async def get_analytics(metric: Optional[str] = None):
    """
    Get analytics data.
    Cached with longer TTL due to expensive computation.
    """
    cache_key = cache_manager.generate_cache_key("/api/analytics", {"metric": metric})

    cached_result = cache_manager.get(cache_key, "/api/analytics")
    if cached_result is not None:
        logger.info(f"Cache HIT for /api/analytics/{metric}")
        return cached_result

    logger.info(f"Cache MISS for /api/analytics/{metric}")

    # Simulate expensive computation
    await asyncio.sleep(0.5)

    analytics = {
        "users_count": len(USERS_DB),
        "posts_count": len(POSTS_DB),
        "avg_posts_per_user": len(POSTS_DB) / len(USERS_DB),
        "timestamp": datetime.now().isoformat(),
    }

    # Cache result
    cache_manager.set(cache_key, analytics, "/api/analytics")

    return analytics


@app.get("/cache/metrics")
async def get_cache_metrics(endpoint: Optional[str] = None):
    """
    Get cache metrics.
    Shows hit rate, miss count, and other metrics.
    """
    if endpoint:
        return cache_manager.get_metrics(endpoint)
    return cache_manager.get_metrics()


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache backend statistics.
    Shows connection info and memory usage.
    """
    return cache_manager.get_backend_stats()


@app.post("/cache/clear")
async def clear_cache(endpoint: Optional[str] = None):
    """
    Clear cache for a specific endpoint or all cache.
    """
    if endpoint:
        invalidated = cache_manager.invalidate_pattern(endpoint, "*")
        return {"status": "cleared", "pattern": endpoint, "invalidated": invalidated}

    cache_manager.clear_cache()
    return {"status": "cleared", "message": "All cache cleared"}


@app.post("/cache/reset-metrics")
async def reset_cache_metrics(endpoint: Optional[str] = None):
    """
    Reset metrics for cache.
    """
    cache_manager.reset_metrics(endpoint)
    return {"status": "reset", "endpoint": endpoint or "all"}


@app.get("/cache/health")
async def cache_health():
    """
    Check cache backend health.
    """
    stats = cache_manager.get_backend_stats()
    is_healthy = stats.get("connected", True)

    return {
        "healthy": is_healthy,
        "backend": stats.get("type"),
        "stats": stats,
    }


# ============================================================================
# Health Checks
# ============================================================================


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============================================================================
# Documentation
# ============================================================================


@app.get("/")
async def root():
    """API documentation."""
    return {
        "title": "Cached API Example",
        "description": "FastAPI with production caching layer",
        "endpoints": {
            "users": "/api/users",
            "posts": "/api/posts",
            "analytics": "/api/analytics",
            "cache_metrics": "/cache/metrics",
            "cache_stats": "/cache/stats",
            "cache_health": "/cache/health",
        },
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
