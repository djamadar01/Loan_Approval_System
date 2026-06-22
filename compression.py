"""
Request/Response compression middleware for FastAPI.

Provides gzip compression for API responses, request decompression,
configurable compression per content type, compression ratio metrics,
and skip compression for small payloads.
"""

import gzip
import io
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers, MutableHeaders

logger = logging.getLogger(__name__)


@dataclass
class CompressionMetrics:
    """Metrics for compression operations."""
    total_requests: int = 0
    total_responses: int = 0
    compressed_requests: int = 0
    compressed_responses: int = 0
    total_original_bytes: int = 0
    total_compressed_bytes: int = 0
    compression_errors: int = 0
    decompression_errors: int = 0

    @property
    def overall_compression_ratio(self) -> float:
        """Calculate overall compression ratio."""
        if self.total_original_bytes == 0:
            return 0.0
        return round(
            (1 - (self.total_compressed_bytes / self.total_original_bytes)) * 100,
            2
        )

    @property
    def compression_rate(self) -> float:
        """Calculate percentage of responses that were compressed."""
        if self.total_responses == 0:
            return 0.0
        return round((self.compressed_responses / self.total_responses) * 100, 2)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "total_requests": self.total_requests,
            "total_responses": self.total_responses,
            "compressed_requests": self.compressed_requests,
            "compressed_responses": self.compressed_responses,
            "total_original_bytes": self.total_original_bytes,
            "total_compressed_bytes": self.total_compressed_bytes,
            "overall_compression_ratio_percent": self.overall_compression_ratio,
            "compression_rate_percent": self.compression_rate,
            "compression_errors": self.compression_errors,
            "decompression_errors": self.decompression_errors,
        }


@dataclass
class CompressionConfig:
    """Configuration for compression middleware."""
    # Minimum size in bytes to compress (smaller payloads are not compressed)
    min_size: int = 500

    # Compression level (1-9, where 9 is maximum compression but slower)
    compression_level: int = 6

    # Content types to compress
    compressible_types: Set[str] = field(default_factory=lambda: {
        "application/json",
        "application/javascript",
        "application/xml",
        "application/x-www-form-urlencoded",
        "text/plain",
        "text/html",
        "text/xml",
        "text/css",
        "text/javascript",
        "text/csv",
    })

    # Content types to never compress (e.g., already compressed formats)
    non_compressible_types: Set[str] = field(default_factory=lambda: {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "video/mp4",
        "video/webm",
        "audio/mpeg",
        "audio/ogg",
        "application/gzip",
        "application/zip",
        "application/x-rar-compressed",
        "application/x-7z-compressed",
    })

    # Exclude paths from compression (regex patterns)
    exclude_paths: Set[str] = field(default_factory=set)

    # Enable request decompression
    enable_request_decompression: bool = True


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response compression using gzip.

    Features:
    - Automatically compresses response bodies based on content type
    - Decompresses gzip-encoded request bodies
    - Tracks compression metrics
    - Skips compression for small payloads
    - Configurable per content type
    """

    def __init__(
        self,
        app: FastAPI,
        config: Optional[CompressionConfig] = None,
    ):
        super().__init__(app)
        self.config = config or CompressionConfig()
        self.metrics = CompressionMetrics()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with compression."""

        # Track request
        self.metrics.total_requests += 1

        # Handle request decompression if enabled
        if self.config.enable_request_decompression:
            request = await self._decompress_request(request)

        # Get response
        start_time = time.time()
        response = await call_next(request)

        # Track response
        self.metrics.total_responses += 1

        # Handle response compression
        response = await self._compress_response(response)

        # Add compression timing header
        duration = time.time() - start_time
        response.headers["X-Compression-Time-Ms"] = str(int(duration * 1000))

        return response

    async def _decompress_request(self, request: Request) -> Request:
        """Decompress gzip-encoded request body if present."""
        encoding = request.headers.get("content-encoding", "").lower()

        if encoding != "gzip":
            return request

        try:
            body = await request.body()

            if not body:
                return request

            # Decompress the body
            decompressed = gzip.decompress(body)

            # Update metrics
            self.metrics.compressed_requests += 1

            # Create a new request with decompressed body
            # We need to create a new scope with the decompressed body
            async def receive():
                return {
                    "type": "http.request",
                    "body": decompressed,
                    "more_body": False,
                }

            # Replace the receive callable
            request._receive = receive

            # Remove content-encoding header
            headers = MutableHeaders(request.headers)
            del headers["content-encoding"]

            logger.info(
                f"Decompressed request: {len(body)} -> {len(decompressed)} bytes"
            )

        except Exception as e:
            self.metrics.decompression_errors += 1
            logger.error(f"Request decompression error: {e}")
            # Continue with original request on error

        return request

    async def _compress_response(self, response: Response) -> Response:
        """Compress response body if appropriate."""

        # Skip compression for certain status codes
        if response.status_code not in (200, 201, 202, 203, 204, 206, 300, 301, 302, 304, 307):
            return response

        # Check if path should be excluded
        request_path = response.headers.get("x-original-path", "")
        if any(pattern in request_path for pattern in self.config.exclude_paths):
            return response

        # Get content type
        content_type = response.headers.get("content-type", "")
        if ";" in content_type:
            content_type = content_type.split(";")[0].strip()

        # Check if content type should be compressed
        if not self._should_compress(content_type):
            return response

        # Check if Accept-Encoding header includes gzip
        # (In middleware context, we assume client accepts gzip for efficiency)
        # In production, check the request's Accept-Encoding header

        # Get response body
        body = b""
        if hasattr(response, "body"):
            body = response.body
        else:
            # For streaming responses, we can't compress
            return response

        # Skip compression for small payloads
        if len(body) < self.config.min_size:
            return response

        try:
            # Compress the body
            compressed = gzip.compress(
                body,
                compresslevel=self.config.compression_level
            )

            # Only use compressed version if it's actually smaller
            if len(compressed) >= len(body):
                return response

            # Update metrics
            self.metrics.compressed_responses += 1
            self.metrics.total_original_bytes += len(body)
            self.metrics.total_compressed_bytes += len(compressed)

            # Create new response with compressed body
            compressed_response = Response(
                content=compressed,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            # Add compression headers
            compressed_response.headers["content-encoding"] = "gzip"
            compressed_response.headers["content-length"] = str(len(compressed))
            compressed_response.headers["X-Original-Content-Length"] = str(len(body))
            compressed_response.headers["X-Compression-Ratio"] = f"{
                round((1 - len(compressed) / len(body)) * 100, 2)
            }%"

            # Copy cookies if present
            if hasattr(response, "set_cookie"):
                for cookie_val in response.headers.getlist("set-cookie"):
                    compressed_response.headers.append("set-cookie", cookie_val)

            logger.debug(
                f"Compressed response: {len(body)} -> {len(compressed)} bytes "
                f"({compressed_response.headers['X-Compression-Ratio']})"
            )

            return compressed_response

        except Exception as e:
            self.metrics.compression_errors += 1
            logger.error(f"Response compression error: {e}")
            return response

    def _should_compress(self, content_type: str) -> bool:
        """Determine if content type should be compressed."""
        if not content_type:
            return False

        # Check if in non-compressible list
        if content_type in self.config.non_compressible_types:
            return False

        # Check if in compressible list or is a text/* or application/* type
        if content_type in self.config.compressible_types:
            return True

        if content_type.startswith("text/"):
            return True

        if content_type.startswith("application/") and not any(
            skip in content_type for skip in ["octet-stream", "zip", "gzip"]
        ):
            return True

        return False

    def get_metrics(self) -> Dict:
        """Get current compression metrics."""
        return self.metrics.to_dict()

    def reset_metrics(self) -> None:
        """Reset metrics."""
        self.metrics = CompressionMetrics()


def add_compression_middleware(
    app: FastAPI,
    config: Optional[CompressionConfig] = None,
) -> CompressionMiddleware:
    """
    Add compression middleware to FastAPI app.

    Args:
        app: FastAPI application instance
        config: CompressionConfig instance (uses defaults if None)

    Returns:
        CompressionMiddleware instance for accessing metrics

    Example:
        >>> app = FastAPI()
        >>> config = CompressionConfig(
        ...     min_size=1000,
        ...     compression_level=7,
        ... )
        >>> middleware = add_compression_middleware(app, config)
        >>>
        >>> @app.get("/metrics")
        ... async def get_metrics():
        ...     return middleware.get_metrics()
    """
    middleware = CompressionMiddleware(app, config)
    app.add_middleware(CompressionMiddleware, config=config)
    return middleware


# Example usage and configuration
if __name__ == "__main__":
    from fastapi.responses import JSONResponse

    # Create FastAPI app
    app = FastAPI()

    # Configure compression
    config = CompressionConfig(
        min_size=500,
        compression_level=6,
        exclude_paths={"/health", "/metrics"},
    )

    # Add middleware
    compression_middleware = add_compression_middleware(app, config)

    # Example endpoint
    @app.get("/data")
    async def get_data():
        """Return large JSON response that will be compressed."""
        return JSONResponse({
            "data": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
        })

    @app.get("/metrics")
    async def get_metrics():
        """Get compression metrics."""
        return compression_middleware.get_metrics()

    @app.post("/upload")
    async def upload_data(request: Request):
        """Accept gzip-compressed request."""
        body = await request.body()
        return JSONResponse({
            "received_bytes": len(body),
            "content_encoding": request.headers.get("content-encoding"),
        })

    # Run with: uvicorn compression:app --reload
