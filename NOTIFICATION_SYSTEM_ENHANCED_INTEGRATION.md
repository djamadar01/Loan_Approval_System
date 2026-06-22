# Enhanced NotificationSystem - Integration Guide

Complete guide for integrating the Enhanced NotificationSystem MCP server into your applications.

## Overview

The Enhanced NotificationSystem is an MCP server designed for enterprise notification management. It provides:

- Multi-channel delivery (email, SMS, push)
- User preference management
- Automatic escalation
- Complete audit trails
- Compliance reporting with digital signatures

## Installation

### 1. System Requirements

```bash
# Python 3.7+
python --version

# Required packages
pip install mcp>=0.1.0

# Optional: for async support
pip install asyncio-contextmanager
```

### 2. Deploy Files

```bash
# Copy server file
cp notification_system_enhanced.py /path/to/your/project/

# Copy client library (optional)
cp notification_system_enhanced_client.py /path/to/your/project/

# Copy tests (for validation)
cp test_notification_system_enhanced.py /path/to/your/project/
```

### 3. Verify Installation

```bash
# Run tests
python -m pytest test_notification_system_enhanced.py -v

# Or with unittest
python test_notification_system_enhanced.py

# Expected: All tests pass (35+ test cases)
```

## Integration Patterns

### Pattern 1: Direct Database Integration

Use the database class directly in your application:

```python
from notification_system_enhanced import EnhancedNotificationDB

# Initialize
db = EnhancedNotificationDB()

# Use directly
db.register_recipient("user_123", "John Doe", "john@company.com")
db.set_notification_preference("user_123", ["email", "sms"])
result = db.send_notification("user_123", "email", "Subject", "Body")
```

**Pros:**
- Direct control
- No network overhead
- Easy debugging

**Cons:**
- Tight coupling
- Database conflicts in multi-process

**Use Case:** Single-process applications, scripts

### Pattern 2: MCP Server Integration

Run as standalone MCP server, communicate via stdio:

```bash
# Start server
python notification_system_enhanced.py

# Connect via MCP client
# (in your application)
```

```python
import mcp.client
import subprocess

# Start server
process = subprocess.Popen(
    ["python", "notification_system_enhanced.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Create MCP client
client = mcp.client.StdioMCPClient(process)

# Call tools
result = client.call_tool("send_notification", {
    "recipient_id": "user_123",
    "channel": "email",
    "subject": "Subject",
    "body": "Body"
})
```

**Pros:**
- Decoupled architecture
- Safe for multi-process
- Easy to scale

**Cons:**
- Network latency
- Process management

**Use Case:** Microservices, distributed systems

### Pattern 3: Client Library Wrapper

Use the provided client library:

```python
from notification_system_enhanced_client import EnhancedNotificationClient

# Create client
client = EnhancedNotificationClient()

# Register recipient
client.register_recipient("user_123", "John Doe", "john@company.com")

# Send notification
result = client.send_notification(
    recipient_id="user_123",
    channel="email",
    subject="Subject",
    body="Body",
    priority="normal"
)
```

**Pros:**
- Convenient API
- Type hints
- Example workflows

**Cons:**
- Wrapper overhead

**Use Case:** Rapid prototyping, testing

## Django Integration

```python
# settings.py
NOTIFICATION_DB_PATH = Path.home() / ".notification_system_enhanced"

# models.py
class UserNotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_channels = models.JSONField(default=list)
    dnd_start = models.TimeField(null=True)
    dnd_end = models.TimeField(null=True)

# tasks.py (Celery)
from celery import shared_task
from notification_system_enhanced import EnhancedNotificationDB

db = EnhancedNotificationDB()

@shared_task
def send_notification_task(recipient_id, channel, subject, body, priority="normal"):
    result = db.send_notification(
        recipient_id=recipient_id,
        channel=channel,
        subject=subject,
        body=body,
        priority=priority
    )
    return result

# views.py
from django.shortcuts import render
from .tasks import send_notification_task

def send_alert_view(request, user_id):
    send_notification_task.delay(
        recipient_id=user_id,
        channel="email",
        subject="Alert",
        body="Something happened",
        priority="high"
    )
    return render(request, "alert_sent.html")

# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from notification_system_enhanced import EnhancedNotificationDB

db = EnhancedNotificationDB()

@receiver(post_save, sender=User)
def register_new_user(sender, instance, created, **kwargs):
    if created:
        db.register_recipient(
            recipient_id=str(instance.id),
            name=instance.get_full_name(),
            email=instance.email
        )
        db.set_notification_preference(
            recipient_id=str(instance.id),
            preferred_channels=["email"]
        )
```

## FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from notification_system_enhanced import EnhancedNotificationDB
from pydantic import BaseModel
from typing import List

app = FastAPI()
db = EnhancedNotificationDB()

class RecipientRequest(BaseModel):
    recipient_id: str
    name: str
    email: str
    phone: str = None

class PreferenceRequest(BaseModel):
    recipient_id: str
    preferred_channels: List[str]
    dnd_start: str = None
    dnd_end: str = None

class NotificationRequest(BaseModel):
    recipient_id: str
    channel: str
    subject: str
    body: str
    priority: str = "normal"

@app.post("/recipients/")
async def register_recipient(req: RecipientRequest):
    result = db.register_recipient(
        recipient_id=req.recipient_id,
        name=req.name,
        email=req.email,
        phone=req.phone
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/preferences/")
async def set_preference(req: PreferenceRequest):
    result = db.set_notification_preference(
        recipient_id=req.recipient_id,
        preferred_channels=req.preferred_channels,
        do_not_disturb_start=req.dnd_start,
        do_not_disturb_end=req.dnd_end
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/notifications/")
async def send_notification(req: NotificationRequest):
    result = db.send_notification(
        recipient_id=req.recipient_id,
        channel=req.channel,
        subject=req.subject,
        body=req.body,
        priority=req.priority
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/preferences/{recipient_id}")
async def get_preference(recipient_id: str):
    result = db.get_notification_preference(recipient_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/compliance/reports/{framework}")
async def list_compliance_reports(framework: str):
    result = db.list_compliance_reports(framework=framework)
    return result
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir mcp

# Copy application files
COPY notification_system_enhanced.py .
COPY notification_system_enhanced_client.py .

# Create data directory
RUN mkdir -p /app/data

# Expose if needed
EXPOSE 8000

# Run server
CMD ["python", "notification_system_enhanced.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  notification-system:
    build: .
    volumes:
      - notification_data:/app/data
    environment:
      LOG_LEVEL: INFO
      TZ: UTC
    ports:
      - "8000:8000"
    restart: always

volumes:
  notification_data:
```

### Run

```bash
# Build image
docker build -t notification-system:latest .

# Run container
docker run -d \
  -v notification_data:/app/data \
  -e LOG_LEVEL=INFO \
  --name notification-system \
  notification-system:latest

# View logs
docker logs -f notification-system

# Stop container
docker stop notification-system
```

## Kubernetes Deployment

### notification-system-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-system
  labels:
    app: notification-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: notification-system
  template:
    metadata:
      labels:
        app: notification-system
    spec:
      containers:
      - name: notification-system
        image: notification-system:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: TZ
          value: "UTC"
        volumeMounts:
        - name: notification-data
          mountPath: /app/data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: notification-data
        persistentVolumeClaim:
          claimName: notification-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: notification-system-service
spec:
  selector:
    app: notification-system
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: notification-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

## AWS Lambda Integration

```python
# lambda_function.py
import json
import os
import sys
from pathlib import Path

# Add layer directory to path for dependencies
sys.path.insert(0, '/opt/python')

from notification_system_enhanced import EnhancedNotificationDB

db = EnhancedNotificationDB()

def lambda_handler(event, context):
    """Handle Lambda events for notification system."""
    action = event.get('action')
    
    if action == 'send_notification':
        result = db.send_notification(
            recipient_id=event['recipient_id'],
            channel=event['channel'],
            subject=event['subject'],
            body=event['body'],
            priority=event.get('priority', 'normal')
        )
    
    elif action == 'register_recipient':
        result = db.register_recipient(
            recipient_id=event['recipient_id'],
            name=event['name'],
            email=event.get('email'),
            phone=event.get('phone')
        )
    
    elif action == 'generate_compliance_report':
        result = db.generate_compliance_report(
            framework=event['framework'],
            period_days=event.get('period_days', 30),
            signed_by=event.get('signed_by', 'system@company.com')
        )
    
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Unknown action'})
        }
    
    return {
        'statusCode': 200 if result.get('success') else 400,
        'body': json.dumps(result, default=str)
    }
```

## Monitoring and Logging

### Application Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log operations
from notification_system_enhanced import EnhancedNotificationDB
db = EnhancedNotificationDB()

try:
    result = db.send_notification(
        recipient_id="user_123",
        channel="email",
        subject="Subject",
        body="Body"
    )
    logger.info(f"Notification sent: {result['notification_id']}")
except Exception as e:
    logger.error(f"Failed to send notification: {e}")
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram
import time

# Define metrics
notifications_sent = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['channel', 'priority']
)

notification_latency = Histogram(
    'notification_latency_seconds',
    'Notification send latency',
    ['channel']
)

# Use metrics
def send_with_metrics(db, recipient_id, channel, subject, body, priority):
    start = time.time()
    result = db.send_notification(recipient_id, channel, subject, body, priority)
    duration = time.time() - start
    
    if result['success']:
        notifications_sent.labels(channel=channel, priority=priority).inc()
        notification_latency.labels(channel=channel).observe(duration)
    
    return result
```

## Testing Integration

### Unit Tests

```python
import unittest
from notification_system_enhanced import EnhancedNotificationDB
import tempfile
from pathlib import Path

class TestNotificationIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = EnhancedNotificationDB(
            Path(self.temp_dir.name) / "test.db"
        )
    
    def test_full_workflow(self):
        # Register
        self.db.register_recipient("user_1", "Test User", "test@example.com")
        
        # Set preferences
        self.db.set_notification_preference("user_1", ["email"])
        
        # Send notification
        result = self.db.send_notification(
            "user_1", "email", "Test", "Body"
        )
        self.assertTrue(result['success'])
        
        # Verify history
        history = self.db.get_communication_history("user_1")
        self.assertGreater(history['total_entries'], 0)
```

### Integration Tests

```python
def test_multi_framework_compliance():
    db = EnhancedNotificationDB()
    
    frameworks = ["gdpr", "ccpa", "hipaa", "soc2", "iso27001"]
    reports = {}
    
    for framework in frameworks:
        report = db.generate_compliance_report(
            framework=framework,
            period_days=30
        )
        reports[framework] = report['report_id']
        assert report['success']
    
    # Verify all reports retrievable
    for framework, report_id in reports.items():
        retrieved = db.get_compliance_report(report_id)
        assert retrieved['success']
        assert retrieved['report']['framework'] == framework
```

## Performance Tuning

### Database Optimization

```python
# Enable WAL mode for better concurrency
import sqlite3
conn = sqlite3.connect('notification_db.sqlite')
conn.execute('PRAGMA journal_mode=WAL')

# Set connection timeout
conn.timeout = 20.0

# Enable query optimization
conn.execute('PRAGMA optimize')
```

### Batch Operations

```python
def send_bulk_notifications(db, recipients, subject, body, priority="normal"):
    """Send notifications to multiple recipients efficiently."""
    results = []
    for recipient_id in recipients:
        # Get preferred channel
        prefs = db.get_notification_preference(recipient_id)
        if not prefs['success']:
            continue
        
        channel = prefs['preferences']['preferred_channels'][0]
        
        # Send notification
        result = db.send_notification(
            recipient_id=recipient_id,
            channel=channel,
            subject=subject,
            body=body,
            priority=priority
        )
        results.append(result)
    
    return results

# Usage
recipients = ["user_1", "user_2", "user_3", ...]
send_bulk_notifications(db, recipients, "Subject", "Body")
```

## Error Handling

```python
def safe_send_notification(db, recipient_id, channel, subject, body):
    """Send notification with comprehensive error handling."""
    try:
        # Validate inputs
        if not recipient_id or not channel:
            raise ValueError("recipient_id and channel are required")
        
        # Check recipient exists
        prefs = db.get_notification_preference(recipient_id)
        if not prefs['success']:
            raise ValueError(f"Recipient {recipient_id} not found")
        
        # Send notification
        result = db.send_notification(
            recipient_id=recipient_id,
            channel=channel,
            subject=subject,
            body=body
        )
        
        if not result['success']:
            raise Exception(f"Send failed: {result.get('error')}")
        
        return result
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {'success': False, 'error': str(e)}
```

## Compliance and Audit

```python
def generate_audit_report(db, period_days=30):
    """Generate complete audit report."""
    frameworks = ["gdpr", "ccpa", "hipaa", "soc2", "iso27001"]
    audit_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "frameworks": {},
        "summary": {}
    }
    
    for framework in frameworks:
        report = db.generate_compliance_report(
            framework=framework,
            period_days=period_days,
            signed_by="audit@company.com"
        )
        audit_data['frameworks'][framework] = {
            'report_id': report['report_id'],
            'signature': report['digital_signature'],
            'summary': report['report']['summary']
        }
    
    return audit_data
```

## Troubleshooting Integration Issues

### Issue: Database Locked

```python
# Solution: Set timeout
import sqlite3
conn = sqlite3.connect('notification_db.sqlite', timeout=30.0)
```

### Issue: Out of Memory with Large Reports

```python
# Solution: Generate reports incrementally
def stream_compliance_report(db, framework, period_days=30):
    """Generate report with streaming output."""
    report = db.generate_compliance_report(
        framework=framework,
        period_days=period_days
    )
    
    # Process incrementally
    for key, value in report['report']['summary'].items():
        yield {key: value}
```

### Issue: Channel Delivery Failures

```python
# Solution: Implement retry with backoff
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def send_with_retry(db, recipient_id, channel, subject, body):
    result = db.send_notification(recipient_id, channel, subject, body)
    if not result['success']:
        raise Exception(result.get('error'))
    return result
```

## Support and Resources

- **Documentation:** See NOTIFICATION_SYSTEM_ENHANCED_README.md
- **Quick Start:** See NOTIFICATION_SYSTEM_ENHANCED_QUICK_START.md
- **Tests:** Run test_notification_system_enhanced.py
- **Examples:** See notification_system_enhanced_client.py

## Checklist

- [ ] Install dependencies
- [ ] Deploy server/library
- [ ] Run tests
- [ ] Configure database path
- [ ] Setup logging
- [ ] Implement error handling
- [ ] Configure compliance frameworks
- [ ] Setup monitoring
- [ ] Test with real data
- [ ] Document API endpoints
- [ ] Setup backup strategy
- [ ] Configure alerting

Integration complete!
