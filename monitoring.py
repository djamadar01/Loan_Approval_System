"""
Comprehensive logging and monitoring module with structured logging,
middleware, performance metrics, error tracking, and health checks.
"""

import json
import logging
import logging.handlers
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from collections import deque
from functools import wraps
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
import psutil


# ============================================================================
# Configuration
# ============================================================================

class MonitoringConfig:
    """Configuration for monitoring and logging."""

    LOG_DIR = Path("./logs")
    LOG_FILE = LOG_DIR / "app.log"
    JSON_LOG_FILE = LOG_DIR / "app.json.log"
    ERROR_LOG_FILE = LOG_DIR / "errors.log"

    # Logging
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Metrics
    METRICS_PORT = 8001
    METRICS_ENDPOINT = "/metrics"

    # Health check
    HEALTH_CHECK_ENDPOINT = "/health"

    # Error tracking
    MAX_ERRORS_STORED = 1000
    ERROR_ALERT_THRESHOLD = 10  # Alert after 10 errors in time window
    ERROR_WINDOW_SECONDS = 300  # 5 minute window

    # Performance thresholds (in seconds)
    SLOW_REQUEST_THRESHOLD = 1.0
    SLOW_DECISION_THRESHOLD = 0.5

    # Create logs directory
    LOG_DIR.mkdir(exist_ok=True)


# ============================================================================
# JSON Formatter
# ============================================================================

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, default=str)


# ============================================================================
# Structured Logger
# ============================================================================

class StructuredLogger:
    """Structured logging wrapper with both text and JSON output."""

    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(MonitoringConfig.LOG_LEVEL)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Text file handler
        text_handler = logging.FileHandler(MonitoringConfig.LOG_FILE)
        text_handler.setLevel(MonitoringConfig.LOG_LEVEL)
        text_formatter = logging.Formatter(MonitoringConfig.LOG_FORMAT)
        text_handler.setFormatter(text_formatter)
        self.logger.addHandler(text_handler)

        # JSON file handler
        json_handler = logging.FileHandler(MonitoringConfig.JSON_LOG_FILE)
        json_handler.setLevel(MonitoringConfig.LOG_LEVEL)
        json_formatter = JsonFormatter()
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)

        # Console handler for debugging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(MonitoringConfig.LOG_LEVEL)
        console_handler.setFormatter(logging.Formatter(MonitoringConfig.LOG_FORMAT))
        self.logger.addHandler(console_handler)

    def _log(self, level: int, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Internal logging method with extra fields support."""
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            None,
            0,
            message,
            (),
            None
        )

        if extra_fields:
            record.extra_fields = extra_fields

        self.logger.handle(record)

    def info(self, message: str, **kwargs):
        """Log info level."""
        self._log(logging.INFO, message, kwargs if kwargs else None)

    def debug(self, message: str, **kwargs):
        """Log debug level."""
        self._log(logging.DEBUG, message, kwargs if kwargs else None)

    def warning(self, message: str, **kwargs):
        """Log warning level."""
        self._log(logging.WARNING, message, kwargs if kwargs else None)

    def error(self, message: str, **kwargs):
        """Log error level."""
        self._log(logging.ERROR, message, kwargs if kwargs else None)

    def critical(self, message: str, **kwargs):
        """Log critical level."""
        self._log(logging.CRITICAL, message, kwargs if kwargs else None)


# ============================================================================
# Error Tracking
# ============================================================================

@dataclass
class ErrorRecord:
    """Record for tracking errors."""
    timestamp: datetime
    error_type: str
    error_message: str
    traceback: str
    request_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ErrorTracker:
    """Track and alert on errors."""

    def __init__(self, logger: StructuredLogger):
        """Initialize error tracker."""
        self.logger = logger
        self.errors: deque = deque(maxlen=MonitoringConfig.MAX_ERRORS_STORED)
        self.lock = threading.Lock()
        self.error_count_in_window = 0
        self.last_alert_time = None

    def record_error(
        self,
        error_type: str,
        error_message: str,
        traceback: str,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record an error and check for alert threshold."""
        error_record = ErrorRecord(
            timestamp=datetime.utcnow(),
            error_type=error_type,
            error_message=error_message,
            traceback=traceback,
            request_id=request_id,
            context=context
        )

        with self.lock:
            self.errors.append(error_record)
            self._check_alert_threshold()

            # Log error with context
            self.logger.error(
                f"Error recorded: {error_type}",
                error_type=error_type,
                error_message=error_message,
                request_id=request_id,
                context=context
            )

    def _check_alert_threshold(self):
        """Check if error rate exceeds threshold."""
        now = datetime.utcnow()
        time_window_start = now - timedelta(seconds=MonitoringConfig.ERROR_WINDOW_SECONDS)

        # Count errors in the time window
        recent_errors = [
            e for e in self.errors
            if e.timestamp >= time_window_start
        ]

        error_count = len(recent_errors)

        if error_count >= MonitoringConfig.ERROR_ALERT_THRESHOLD:
            if self.last_alert_time is None or \
               (now - self.last_alert_time).total_seconds() > 60:
                self._send_alert(error_count, recent_errors)
                self.last_alert_time = now

    def _send_alert(self, error_count: int, recent_errors: List[ErrorRecord]):
        """Send alert for high error rate."""
        alert_message = (
            f"ALERT: {error_count} errors in the last "
            f"{MonitoringConfig.ERROR_WINDOW_SECONDS} seconds"
        )

        self.logger.critical(
            alert_message,
            error_count=error_count,
            threshold=MonitoringConfig.ERROR_ALERT_THRESHOLD,
            errors_summary=[
                {"type": e.error_type, "message": e.error_message}
                for e in recent_errors[:5]
            ]
        )

    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent errors."""
        with self.lock:
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "error_type": e.error_type,
                    "error_message": e.error_message,
                    "request_id": e.request_id,
                    "context": e.context
                }
                for e in list(self.errors)[-limit:]
            ]

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self.lock:
            if not self.errors:
                return {
                    "total_errors": 0,
                    "errors_by_type": {},
                    "recent_error_rate": 0
                }

            now = datetime.utcnow()
            time_window_start = now - timedelta(seconds=MonitoringConfig.ERROR_WINDOW_SECONDS)

            # Count errors by type
            errors_by_type = {}
            recent_error_count = 0

            for error in self.errors:
                # Count by type
                errors_by_type[error.error_type] = errors_by_type.get(error.error_type, 0) + 1

                # Count recent errors
                if error.timestamp >= time_window_start:
                    recent_error_count += 1

            return {
                "total_errors": len(self.errors),
                "errors_by_type": errors_by_type,
                "recent_error_rate": recent_error_count / MonitoringConfig.ERROR_WINDOW_SECONDS
            }


# ============================================================================
# Performance Metrics
# ============================================================================

class MetricsCollector:
    """Collect and expose Prometheus metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.registry = CollectorRegistry()

        # Request metrics
        self.request_count = Counter(
            "requests_total",
            "Total number of requests",
            ["method", "endpoint", "status"],
            registry=self.registry
        )

        self.request_duration = Histogram(
            "request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
            registry=self.registry,
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
        )

        # Decision time metrics
        self.decision_duration = Histogram(
            "decision_duration_seconds",
            "Decision processing time in seconds",
            ["decision_type"],
            registry=self.registry,
            buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
        )

        # Error metrics
        self.error_count = Counter(
            "errors_total",
            "Total number of errors",
            ["error_type"],
            registry=self.registry
        )

        # System metrics
        self.cpu_usage = Gauge(
            "cpu_usage_percent",
            "CPU usage percentage",
            registry=self.registry
        )

        self.memory_usage = Gauge(
            "memory_usage_percent",
            "Memory usage percentage",
            registry=self.registry
        )

        self.disk_usage = Gauge(
            "disk_usage_percent",
            "Disk usage percentage",
            registry=self.registry
        )

        # Custom business metrics
        self.active_requests = Gauge(
            "active_requests",
            "Number of active requests",
            registry=self.registry
        )

        self.slow_requests = Counter(
            "slow_requests_total",
            "Total number of slow requests",
            ["endpoint"],
            registry=self.registry
        )

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ):
        """Record request metrics."""
        self.request_count.labels(method=method, endpoint=endpoint, status=status_code).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

        if duration > MonitoringConfig.SLOW_REQUEST_THRESHOLD:
            self.slow_requests.labels(endpoint=endpoint).inc()

    def record_decision(self, decision_type: str, duration: float):
        """Record decision processing time."""
        self.decision_duration.labels(decision_type=decision_type).observe(duration)

    def record_error(self, error_type: str):
        """Record error."""
        self.error_count.labels(error_type=error_type).inc()

    def update_system_metrics(self):
        """Update system resource metrics."""
        self.cpu_usage.set(psutil.cpu_percent(interval=0.1))
        self.memory_usage.set(psutil.virtual_memory().percent)
        self.disk_usage.set(psutil.disk_usage('/').percent)

    def set_active_requests(self, count: int):
        """Set active request count."""
        self.active_requests.set(count)

    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        self.update_system_metrics()
        return generate_latest(self.registry).decode('utf-8')


# ============================================================================
# Request/Response Logging Middleware
# ============================================================================

class RequestResponseLogger:
    """Middleware for logging requests and responses."""

    def __init__(
        self,
        app: Flask,
        logger: StructuredLogger,
        metrics: MetricsCollector,
        error_tracker: ErrorTracker
    ):
        """Initialize middleware."""
        self.app = app
        self.logger = logger
        self.metrics = metrics
        self.error_tracker = error_tracker
        self.active_requests = 0
        self.lock = threading.Lock()

        # Register before/after request hooks
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

    def _before_request(self):
        """Log incoming request."""
        request.start_time = time.time()
        request.request_id = self._generate_request_id()

        with self.lock:
            self.active_requests += 1
            self.metrics.set_active_requests(self.active_requests)

        self.logger.info(
            f"Request received: {request.method} {request.path}",
            request_id=request.request_id,
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
            user_agent=request.user_agent.string
        )

    def _after_request(self, response):
        """Log response."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            self.logger.info(
                f"Response sent: {request.method} {request.path} -> {response.status_code}",
                request_id=request.request_id,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration_seconds=duration,
                content_length=response.content_length
            )

            # Record metrics
            self.metrics.record_request(
                method=request.method,
                endpoint=request.path,
                status_code=response.status_code,
                duration=duration
            )

        return response

    def _teardown_request(self, exception=None):
        """Handle request cleanup."""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.metrics.set_active_requests(self.active_requests)

        if exception:
            self.logger.error(
                f"Request error: {str(exception)}",
                request_id=getattr(request, 'request_id', None),
                exception_type=type(exception).__name__,
                exception_message=str(exception)
            )

            self.error_tracker.record_error(
                error_type=type(exception).__name__,
                error_message=str(exception),
                traceback=str(exception),
                request_id=getattr(request, 'request_id', None)
            )

    @staticmethod
    def _generate_request_id() -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())


# ============================================================================
# Decision Timer
# ============================================================================

class DecisionTimer:
    """Context manager for timing decision processing."""

    def __init__(self, metrics: MetricsCollector, decision_type: str, logger: StructuredLogger):
        """Initialize timer."""
        self.metrics = metrics
        self.decision_type = decision_type
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timer and record metrics."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.record_decision(self.decision_type, duration)

            if duration > MonitoringConfig.SLOW_DECISION_THRESHOLD:
                self.logger.warning(
                    f"Slow decision: {self.decision_type}",
                    decision_type=self.decision_type,
                    duration_seconds=duration,
                    threshold_seconds=MonitoringConfig.SLOW_DECISION_THRESHOLD
                )


# ============================================================================
# Health Check
# ============================================================================

class HealthChecker:
    """Health check endpoint handler."""

    def __init__(
        self,
        logger: StructuredLogger,
        error_tracker: ErrorTracker,
        metrics: MetricsCollector
    ):
        """Initialize health checker."""
        self.logger = logger
        self.error_tracker = error_tracker
        self.metrics = metrics

    def check_health(self) -> Dict[str, Any]:
        """Perform health check."""
        error_stats = self.error_tracker.get_error_stats()

        # Determine status based on error rate
        error_rate = error_stats.get("recent_error_rate", 0)
        status = "healthy"

        if error_rate > 0.1:  # More than 1 error per 10 seconds
            status = "degraded"
        if error_rate > 0.5:  # More than 1 error per 2 seconds
            status = "unhealthy"

        health_data = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "errors": error_stats,
            "uptime_seconds": self._get_uptime()
        }

        self.logger.info(
            f"Health check: {status}",
            status=status,
            error_rate=error_rate
        )

        return health_data

    @staticmethod
    def _get_uptime() -> float:
        """Get application uptime in seconds."""
        try:
            process = psutil.Process(os.getpid())
            return time.time() - process.create_time()
        except:
            return 0


# ============================================================================
# Monitoring Setup
# ============================================================================

def setup_monitoring(app: Flask) -> tuple:
    """
    Set up complete monitoring for Flask app.

    Returns:
        Tuple of (logger, metrics, error_tracker, health_checker)
    """
    # Initialize components
    logger = StructuredLogger("app")
    metrics = MetricsCollector()
    error_tracker = ErrorTracker(logger)
    health_checker = HealthChecker(logger, error_tracker, metrics)

    # Set up middleware
    RequestResponseLogger(app, logger, metrics, error_tracker)

    # Register health check endpoint
    @app.route(MonitoringConfig.HEALTH_CHECK_ENDPOINT)
    def health():
        """Health check endpoint."""
        health_data = health_checker.check_health()
        status_code = 200 if health_data["status"] == "healthy" else 503
        return jsonify(health_data), status_code

    # Register metrics endpoint
    @app.route(MonitoringConfig.METRICS_ENDPOINT)
    def metrics():
        """Prometheus metrics endpoint."""
        return Response(
            metrics.get_metrics(),
            mimetype=CONTENT_TYPE_LATEST
        )

    # Register error logs endpoint
    @app.route("/api/errors")
    def get_errors():
        """Get recent errors."""
        limit = request.args.get("limit", default=50, type=int)
        return jsonify({
            "errors": error_tracker.get_recent_errors(limit),
            "stats": error_tracker.get_error_stats()
        })

    logger.info("Monitoring setup complete")

    return logger, metrics, error_tracker, health_checker


# ============================================================================
# Decorators
# ============================================================================

def track_decision(decision_type: str):
    """Decorator to track decision processing time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get metrics from app context if available
            from flask import current_app
            try:
                metrics = current_app.extensions.get('monitoring_metrics')
                logger = current_app.extensions.get('monitoring_logger')

                if metrics and logger:
                    with DecisionTimer(metrics, decision_type, logger):
                        return func(*args, **kwargs)
            except:
                pass

            return func(*args, **kwargs)
        return wrapper
    return decorator


def track_errors(func: Callable) -> Callable:
    """Decorator to track function errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from flask import current_app
            try:
                error_tracker = current_app.extensions.get('monitoring_error_tracker')
                logger = current_app.extensions.get('monitoring_logger')

                if error_tracker and logger:
                    import traceback
                    error_tracker.record_error(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        traceback=traceback.format_exc()
                    )
            except:
                pass

            raise
    return wrapper


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Create a simple Flask app with monitoring
    app = Flask(__name__)

    logger, metrics, error_tracker, health_checker = setup_monitoring(app)

    # Store components in app extensions for decorator access
    app.extensions['monitoring_logger'] = logger
    app.extensions['monitoring_metrics'] = metrics
    app.extensions['monitoring_error_tracker'] = error_tracker

    @app.route("/")
    def index():
        """Example endpoint."""
        logger.info("Index endpoint called")
        return jsonify({"message": "Hello, World!"})

    @app.route("/decision/<decision_type>")
    @track_decision("example_decision")
    def make_decision(decision_type):
        """Example decision endpoint."""
        import time
        time.sleep(0.1)  # Simulate decision processing
        return jsonify({"decision": decision_type, "result": "processed"})

    @app.route("/error")
    @track_errors
    def trigger_error():
        """Endpoint that triggers an error."""
        raise ValueError("This is a test error")

    logger.info("Starting monitoring example app")
    app.run(debug=True, host="0.0.0.0", port=5000)
