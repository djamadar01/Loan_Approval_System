# Monitoring & Logging Module - Complete Implementation

A production-ready monitoring and logging system for Flask applications with comprehensive support for structured logging, Prometheus metrics, error tracking, health checks, and performance monitoring.

## 📋 Features

### ✅ Core Components

1. **Structured JSON Logging**
   - JSON-formatted logs for structured data collection
   - Text logs for human readability
   - Console output for development
   - Contextual field support
   - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

2. **Request/Response Middleware**
   - Automatic HTTP request/response logging
   - Unique request ID generation
   - Request duration tracking
   - Active connection monitoring
   - Exception handling and logging

3. **Performance Metrics**
   - Request count by method and endpoint
   - Request duration histograms
   - Decision processing time tracking
   - Slow request detection
   - System resource monitoring (CPU, Memory, Disk)

4. **Error Tracking & Alerts**
   - Centralized error recording
   - Error classification by type
   - Time-windowed alert thresholds
   - Error history with context
   - Exception traceback capture

5. **Health Check Endpoint**
   - System resource monitoring
   - Error rate-based health status
   - Application uptime tracking
   - Detailed health reports

6. **Prometheus Metrics**
   - Production-ready metrics format
   - System resource tracking
   - Custom business metrics
   - Grafana-compatible

## 📁 File Structure

```
demo/
├── monitoring.py                 # Main monitoring module (600+ lines)
├── monitoring_example.py        # Complete example app
├── test_monitoring.py           # Comprehensive test suite
├── requirements_monitoring.txt  # Dependencies
├── prometheus.yml              # Prometheus config
├── docker-compose.yml          # Docker setup
├── Dockerfile                  # Container image
├── MONITORING_GUIDE.md         # Detailed guide
└── README_MONITORING.md        # This file
```

## 🚀 Quick Start

### Option 1: Direct Installation

```bash
# Install dependencies
pip install -r requirements_monitoring.txt

# Run example app
python monitoring_example.py

# In another terminal, run tests
python test_monitoring.py

# Access endpoints
curl http://localhost:5000/health
curl http://localhost:5000/metrics
```

### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up

# Access services
# Flask app:     http://localhost:5000
# Prometheus:    http://localhost:9090
# Grafana:       http://localhost:3000 (admin/admin)
```

## 🔍 Key Endpoints

### Health & Monitoring
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics
- `GET /api/errors` - Recent errors
- `GET /api/stats` - Application statistics

### Example API (from monitoring_example.py)
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/<id>` - Get user
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user
- `POST /api/decision` - Make decision
- `POST /api/process` - Process data
- `POST /api/error/simulate` - Trigger error
- `POST /api/stress` - Stress test

## 💻 Basic Usage

### Setup in Your Flask App

```python
from flask import Flask
from monitoring import setup_monitoring

app = Flask(__name__)

# One line setup
logger, metrics, error_tracker, health_checker = setup_monitoring(app)

# Store in extensions
app.extensions['monitoring_logger'] = logger
app.extensions['monitoring_metrics'] = metrics
app.extensions['monitoring_error_tracker'] = error_tracker

@app.route("/api/example")
def example_endpoint():
    logger.info("Endpoint called", user_id=123)
    return {"status": "ok"}

if __name__ == '__main__':
    app.run()
```

### Using the Logger

```python
# Simple logging with context
logger.info("User logged in", user_id=user.id, email=user.email)
logger.warning("Rate limit approaching", user_id=user.id, remaining=5)
logger.error("Database error", operation="user_update", retries=3)

# Error logging
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", operation="risky_operation")
```

### Tracking Decisions

```python
from monitoring import track_decision, DecisionTimer

# Using decorator
@app.route("/api/recommend")
@track_decision("recommendation_engine")
def get_recommendation():
    # Automatic timing
    return recommendation

# Using context manager
@app.route("/api/process")
def process():
    with DecisionTimer(metrics, "data_processing", logger):
        # Your code
        pass
```

### Tracking Errors

```python
from monitoring import track_errors

@app.route("/api/action")
@track_errors
def action():
    # Errors are automatically tracked
    perform_action()
    return {"status": "done"}
```

## 📊 Log Files

Generated in `./logs/` directory:

- **app.log** - Human-readable text logs
- **app.json.log** - Structured JSON logs (parseable)
- **errors.log** - Error-specific logs

### JSON Log Example

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "app",
  "message": "User created",
  "module": "monitoring",
  "function": "create_user",
  "line": 245,
  "user_id": 42,
  "email": "user@example.com"
}
```

## 📈 Prometheus Integration

### Metrics Available

```
# Request metrics
requests_total{method="GET",endpoint="/api/users",status="200"}
request_duration_seconds_bucket{method="GET",endpoint="/api/users",le="0.1"}

# Decision metrics
decision_duration_seconds_bucket{decision_type="recommendation_engine",le="0.1"}

# Error metrics
errors_total{error_type="ValueError"}

# System metrics
cpu_usage_percent
memory_usage_percent
disk_usage_percent
active_requests
```

### Prometheus Queries

```promql
# Request rate (req/s)
rate(requests_total[1m])

# 95th percentile response time
histogram_quantile(0.95, request_duration_seconds_bucket)

# Error rate
rate(errors_total[5m])

# Slow requests
rate(slow_requests_total[5m])

# CPU usage
cpu_usage_percent
```

### Grafana Dashboard Setup

1. Access Grafana: http://localhost:3000
2. Add Prometheus as data source: http://prometheus:9090
3. Import dashboards or create custom ones
4. Use queries above

## ⚙️ Configuration

Customize in `monitoring.py` `MonitoringConfig` class:

```python
class MonitoringConfig:
    # Directories
    LOG_DIR = Path("./logs")
    
    # Error tracking
    MAX_ERRORS_STORED = 1000          # Max errors in memory
    ERROR_ALERT_THRESHOLD = 10        # Alert after N errors
    ERROR_WINDOW_SECONDS = 300        # Time window: 5 minutes
    
    # Performance thresholds
    SLOW_REQUEST_THRESHOLD = 1.0      # Request > 1s = slow
    SLOW_DECISION_THRESHOLD = 0.5     # Decision > 0.5s = slow
```

## 🧪 Testing

### Run Full Test Suite

```bash
python test_monitoring.py
```

Includes:
- ✓ Basic endpoint functionality
- ✓ Health check verification
- ✓ Metrics collection
- ✓ User CRUD operations
- ✓ Decision processing
- ✓ Error tracking
- ✓ Log file creation
- ✓ Slow request detection
- ✓ Statistics gathering
- ✓ Stress testing

### Manual Testing

```bash
# Health check
curl http://localhost:5000/health

# Metrics
curl http://localhost:5000/metrics

# Create user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'

# Make decision
curl -X POST http://localhost:5000/api/decision \
  -H "Content-Type: application/json" \
  -d '{"user_id":1}'

# Simulate error
curl http://localhost:5000/api/error/simulate?type=value_error

# View errors
curl http://localhost:5000/api/errors?limit=10

# Run stress test
curl "http://localhost:5000/api/stress?iterations=20"
```

## 📚 Documentation

See `MONITORING_GUIDE.md` for comprehensive documentation including:
- Detailed API reference
- Configuration options
- Advanced usage patterns
- Performance optimization
- Troubleshooting guide
- Best practices
- Prometheus integration

## 🔧 Decorators

### @track_decision(decision_type)
Automatically times decision processing:
```python
@app.route("/api/recommend")
@track_decision("recommendation_engine")
def get_recommendation():
    # Timing captured automatically
    return recommendation
```

### @track_errors
Automatically catches and logs errors:
```python
@app.route("/api/action")
@track_errors
def perform_action():
    # Errors are tracked automatically
    perform_operation()
```

## 🎯 Context Manager

### DecisionTimer
Manual timing of code blocks:
```python
with DecisionTimer(metrics, "operation_name", logger):
    # Code block is timed
    expensive_operation()
```

## 📊 Performance Considerations

| Component | Memory | CPU | Notes |
|-----------|--------|-----|-------|
| Core logger | ~50KB | Minimal | Text+JSON output |
| Metrics collector | ~100KB | Minimal | Prometheus client |
| Error tracker | Depends | Minimal | Max 1000 errors |
| Health checks | ~10KB | Low | Calls psutil |
| Middleware | ~20KB | Low | Per-request tracking |

## 🚨 Error Alerts

Automatic alerts triggered when:
- Error rate exceeds threshold in time window
- Logged with critical severity
- Includes error summary and context

Example alert:
```
ALERT: 15 errors in the last 300 seconds
Threshold: 10
Recent errors: [ValueError, KeyError, RuntimeError...]
```

## 📋 Log Rotation

For production, implement log rotation:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
```

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t flask-monitoring .
```

### Run with Docker Compose
```bash
docker-compose up
```

### Access Services
- Flask: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Node Exporter: http://localhost:9100

## 🔐 Security Considerations

1. **Metrics Endpoint**: Consider authentication for `/metrics`
2. **Error Logs**: Don't expose sensitive data in logs
3. **Health Checks**: May reveal system information
4. **Log Files**: Store securely with appropriate permissions
5. **Prometheus Access**: Secure with firewall rules

## 🌟 Best Practices

1. **Always use structured logging** with context fields
2. **Include request IDs** for tracing
3. **Monitor decision times** for optimization
4. **Set appropriate thresholds** for your use case
5. **Rotate log files** regularly
6. **Export metrics** to Prometheus/Grafana
7. **Set up alerts** for errors and performance
8. **Review logs** for patterns

## 📞 Support

For issues or questions:
1. Check `MONITORING_GUIDE.md` for detailed documentation
2. Review `monitoring_example.py` for usage examples
3. Run `test_monitoring.py` to validate setup
4. Check log files in `./logs/` directory

## 📝 Example Queries

### Find all errors of a type
```python
errors = [e for e in error_tracker.errors if e.error_type == "ValueError"]
```

### Get error rate
```python
error_stats = error_tracker.get_error_stats()
recent_rate = error_stats['recent_error_rate']
```

### Export metrics
```python
metrics_text = metrics.get_metrics()
with open('metrics_export.txt', 'w') as f:
    f.write(metrics_text)
```

## 📦 Dependencies

- Flask 2.3.0+ - Web framework
- prometheus-client 0.16.0+ - Metrics
- psutil 5.9.4+ - System metrics

## 📄 License

Production-ready implementation provided as-is.

## 🎓 Learning Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Structured Logging](https://www.kartar.net/2015/12/structured-logging/)

---

**Created**: 2024  
**Status**: Production Ready  
**Maintenance**: Active
