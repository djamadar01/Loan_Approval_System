# Monitoring and Logging Module - Complete Guide

## Overview

This comprehensive monitoring module provides production-ready logging, metrics collection, and health checking for Flask applications. It includes structured JSON logging, Prometheus metrics integration, request/response tracking, error monitoring, and system health checks.

## Features

### 1. **Structured Logging**
- JSON format logging to file for structured data collection
- Text format logging to file for human readability
- Console output for development
- Extra fields support for contextual data
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### 2. **Request/Response Middleware**
- Automatic logging of all HTTP requests and responses
- Unique request ID generation and tracking
- Request duration tracking
- Status code monitoring
- Request context preservation

### 3. **Performance Metrics Collection**
- Request count by method and endpoint
- Request duration histograms with bucketed latencies
- Decision processing time tracking
- Slow request detection and counting
- Active request count monitoring

### 4. **Error Tracking & Alerts**
- Centralized error recording
- Error classification by type
- Configurable alert thresholds
- Time-windowed error rate calculation
- Error history with timestamps
- Exception traceback capture

### 5. **Health Check Endpoint**
- System resource monitoring (CPU, Memory, Disk)
- Health status determination (healthy/degraded/unhealthy)
- Application uptime tracking
- Error rate-based status
- Detailed health report

### 6. **Prometheus Metrics**
- Automatic metrics exposure on dedicated endpoint
- System resource metrics
- Custom business metrics
- Prometheus-compatible text format
- Compatible with Grafana and other visualization tools

## Installation

```bash
pip install -r requirements_monitoring.txt
```

Required dependencies:
- Flask 2.3.0+
- prometheus-client 0.16.0+
- psutil 5.9.4+

## Configuration

### MonitoringConfig Class

Customize monitoring behavior in `monitoring.py`:

```python
class MonitoringConfig:
    LOG_DIR = Path("./logs")
    LOG_FILE = LOG_DIR / "app.log"
    JSON_LOG_FILE = LOG_DIR / "app.json.log"
    ERROR_LOG_FILE = LOG_DIR / "errors.log"
    
    # Error tracking
    MAX_ERRORS_STORED = 1000
    ERROR_ALERT_THRESHOLD = 10
    ERROR_WINDOW_SECONDS = 300
    
    # Performance thresholds
    SLOW_REQUEST_THRESHOLD = 1.0  # seconds
    SLOW_DECISION_THRESHOLD = 0.5  # seconds
```

## Quick Start

### Basic Setup

```python
from flask import Flask
from monitoring import setup_monitoring

app = Flask(__name__)

# Set up monitoring
logger, metrics, error_tracker, health_checker = setup_monitoring(app)

# Store in app extensions for decorator use
app.extensions['monitoring_logger'] = logger
app.extensions['monitoring_metrics'] = metrics
app.extensions['monitoring_error_tracker'] = error_tracker

# Your routes here...

if __name__ == '__main__':
    app.run(debug=True)
```

### Using the Logger

```python
# Simple logging
logger.info("Application started")
logger.warning("Configuration missing", config_key="API_KEY")
logger.error("Database connection failed", retry_count=3)

# With structured context
logger.info(
    "User created",
    user_id=123,
    user_name="Alice",
    email="alice@example.com"
)

# Error logging
try:
    # code
except Exception as e:
    logger.error(f"Operation failed: {e}", operation="data_processing")
```

### Decision Timing

```python
from monitoring import DecisionTimer

# Using decorator
@app.route("/api/recommend")
@track_decision("recommendation_engine")
def get_recommendation():
    # Your decision logic
    return jsonify(recommendation)

# Using context manager
@app.route("/api/process")
def process_data():
    with DecisionTimer(metrics, "data_processing", logger):
        # Your processing logic
        pass
    return jsonify(result)
```

### Error Tracking

```python
from monitoring import track_errors

@app.route("/api/users", methods=["POST"])
@track_errors
def create_user():
    # If this raises an exception, it's automatically tracked
    data = request.get_json()
    # Process user creation
    return jsonify(user)
```

## Endpoints

### Health Check Endpoint
```
GET /health

Response (200 OK - Healthy):
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456",
  "cpu_percent": 25.5,
  "memory_percent": 60.2,
  "disk_percent": 45.0,
  "errors": {
    "total_errors": 5,
    "errors_by_type": {"ValueError": 2, "KeyError": 3},
    "recent_error_rate": 0.01
  },
  "uptime_seconds": 3600
}
```

### Prometheus Metrics Endpoint
```
GET /metrics

Returns Prometheus-format metrics:
# HELP requests_total Total number of requests
# TYPE requests_total counter
requests_total{endpoint="/api/users",method="GET",status="200"} 15.0

# HELP request_duration_seconds Request duration in seconds
# TYPE request_duration_seconds histogram
request_duration_seconds_bucket{endpoint="/api/users",le="0.01",method="GET"} 5.0
...
```

### Error Logs Endpoint
```
GET /api/errors?limit=50

Response:
{
  "errors": [
    {
      "timestamp": "2024-01-15T10:30:45.123456",
      "error_type": "ValueError",
      "error_message": "Invalid input",
      "request_id": "abc-123-def"
    }
  ],
  "stats": {
    "total_errors": 42,
    "errors_by_type": {"ValueError": 25, "KeyError": 17},
    "recent_error_rate": 0.05
  }
}
```

## Log Files

### app.log (Text Format)
```
2024-01-15 10:30:45 - app - INFO - Request received: GET /api/users
2024-01-15 10:30:46 - app - INFO - Response sent: GET /api/users -> 200
```

### app.json.log (Structured JSON Format)
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "app",
  "message": "Request received: GET /api/users",
  "module": "monitoring",
  "function": "_before_request",
  "line": 145,
  "request_id": "abc-123-def",
  "method": "GET",
  "path": "/api/users",
  "remote_addr": "127.0.0.1"
}
```

## Metrics Explained

### Request Metrics
- `requests_total`: Counter of all requests by method, endpoint, and status
- `request_duration_seconds`: Histogram of request durations with percentile buckets
- `slow_requests_total`: Counter of requests exceeding threshold
- `active_requests`: Gauge of currently active requests

### Decision Metrics
- `decision_duration_seconds`: Histogram of decision processing times
- Automatic detection of slow decisions

### Error Metrics
- `errors_total`: Counter of errors by type
- Integration with error tracking system

### System Metrics
- `cpu_usage_percent`: CPU utilization
- `memory_usage_percent`: Memory usage
- `disk_usage_percent`: Disk usage

## Advanced Usage

### Custom Metrics Recording

```python
# Record custom request
metrics.record_request(
    method="POST",
    endpoint="/api/custom",
    status_code=201,
    duration=0.5
)

# Record custom decision
metrics.record_decision("custom_decision", 0.25)

# Record custom error
metrics.record_error("CustomError")
```

### Manual Error Tracking

```python
# Track error without raising
error_tracker.record_error(
    error_type="DatabaseError",
    error_message="Connection timeout",
    traceback="...",
    request_id=request_id,
    context={"database": "primary", "retry_count": 3}
)
```

### Monitoring Multiple Decision Points

```python
@app.route("/api/process")
def complex_process():
    # Track overall process
    with DecisionTimer(metrics, "full_process", logger):
        
        # Track validation step
        with DecisionTimer(metrics, "validation", logger):
            # Validation logic
            pass
        
        # Track processing step
        with DecisionTimer(metrics, "processing", logger):
            # Processing logic
            pass
        
        # Track storage step
        with DecisionTimer(metrics, "storage", logger):
            # Storage logic
            pass
    
    return jsonify({"status": "complete"})
```

## Prometheus Integration

### Scrape Configuration Example

In your Prometheus `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'flask-app'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard Queries

```
# Request Rate (requests per second)
rate(requests_total[1m])

# 95th Percentile Request Duration
histogram_quantile(0.95, request_duration_seconds_bucket)

# Error Rate
rate(errors_total[5m])

# CPU Usage Trend
cpu_usage_percent

# Active Requests
active_requests
```

## Performance Considerations

1. **Log File Size**: Monitor log file size and implement log rotation
2. **Metrics Memory**: Prometheus client library uses ~100KB base memory
3. **Error Storage**: Max 1000 errors stored in memory (configurable)
4. **System Metrics**: Updated on metrics endpoint access (minimal overhead)

## Troubleshooting

### High Memory Usage
- Reduce `MAX_ERRORS_STORED` in MonitoringConfig
- Clear log files periodically
- Monitor active connection count

### Slow Health Checks
- Health check calls `psutil` which may be slow on some systems
- Consider caching health check results
- Adjust scrape intervals

### Missing Metrics
- Ensure endpoints are being accessed
- Check that Flask app initialization includes `setup_monitoring()`
- Verify Prometheus client is properly installed

## Testing

Run the example application:

```bash
python monitoring_example.py
```

Test endpoints:

```bash
# Test basic functionality
curl http://localhost:5000/api/users

# Create a user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie", "email": "charlie@example.com"}'

# Make a decision
curl -X POST http://localhost:5000/api/decision \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# Check health
curl http://localhost:5000/health

# View metrics
curl http://localhost:5000/metrics

# View errors
curl "http://localhost:5000/api/errors?limit=10"

# Simulate stress
curl "http://localhost:5000/api/stress?iterations=20"
```

## Best Practices

1. **Always use structured logging** with context fields
2. **Set request IDs** for tracing across logs
3. **Monitor decision times** for performance optimization
4. **Configure appropriate thresholds** for your use case
5. **Rotate logs** to prevent disk space issues
6. **Export metrics** to Prometheus/Grafana for visualization
7. **Set up alerts** based on error rates and performance metrics
8. **Review logs regularly** for patterns and issues

## API Reference

### StructuredLogger
- `info(message, **kwargs)` - Log info level
- `debug(message, **kwargs)` - Log debug level
- `warning(message, **kwargs)` - Log warning level
- `error(message, **kwargs)` - Log error level
- `critical(message, **kwargs)` - Log critical level

### MetricsCollector
- `record_request(method, endpoint, status_code, duration)` - Record request
- `record_decision(decision_type, duration)` - Record decision
- `record_error(error_type)` - Record error
- `set_active_requests(count)` - Set active request count
- `get_metrics()` - Get Prometheus metrics

### ErrorTracker
- `record_error(error_type, error_message, traceback, request_id, context)` - Record error
- `get_recent_errors(limit)` - Get recent errors
- `get_error_stats()` - Get error statistics

### HealthChecker
- `check_health()` - Get complete health report

### Decorators
- `@track_decision(decision_type)` - Track decision timing
- `@track_errors` - Track and log errors

### Context Managers
- `DecisionTimer(metrics, decision_type, logger)` - Time a code block

## Files

- `monitoring.py` - Main monitoring module (500+ lines)
- `monitoring_example.py` - Complete example application
- `requirements_monitoring.txt` - Dependencies
- `MONITORING_GUIDE.md` - This guide

## License

This monitoring module is provided as-is for production use.
