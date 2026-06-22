# Webhook Management System - Quick Reference

## Installation & Setup

```python
from webhooks import WebhookManager, EventType, WebhookStatus

manager = WebhookManager()
```

## Core Operations

### 1. Register Webhook
```python
webhook_id = manager.register_webhook(
    url="https://api.example.com/webhooks",
    event_types=[EventType.APPLICATION_SUBMITTED, EventType.DECISION_MADE],
)
```

### 2. Trigger Event
```python
event_ids = manager.trigger_event(
    event_type=EventType.APPLICATION_SUBMITTED,
    payload={"application_id": "APP-001", "user": "john@example.com"}
)
```

### 3. Deliver Events
```python
stats = manager.deliver_pending_events(async_mode=True)
```

### 4. Get Logs
```python
logs = manager.get_delivery_logs(webhook_id=webhook_id, limit=10)
```

## Event Types

| Type | Description |
|------|-------------|
| `EventType.APPLICATION_SUBMITTED` | New application submitted |
| `EventType.DECISION_MADE` | Decision made on application |
| `EventType.STATUS_CHANGED` | Application status changed |

## Common Patterns

### Pattern 1: Multi-Service Integration
```python
# Analytics service
analytics = manager.register_webhook(
    url="https://analytics.example.com/events",
    event_types=[EventType.APPLICATION_SUBMITTED],
)

# CRM service
crm = manager.register_webhook(
    url="https://crm.example.com/webhook",
    event_types=[EventType.APPLICATION_SUBMITTED, EventType.DECISION_MADE],
)

# All events go to both services
manager.trigger_event(
    event_type=EventType.APPLICATION_SUBMITTED,
    payload={"application_id": "APP-001"}
)
```

### Pattern 2: Conditional Delivery (Filtering)
```python
# Only high-priority apps
premium = manager.register_webhook(
    url="https://premium.example.com/webhook",
    event_types=[EventType.APPLICATION_SUBMITTED],
    custom_filter=lambda e: e["payload"]["priority"] == "high"
)

# Department-specific
finance = manager.register_webhook(
    url="https://finance.example.com/webhook",
    event_types=[EventType.STATUS_CHANGED],
    custom_filter=lambda e: e["payload"]["department"] == "finance"
)
```

### Pattern 3: Secure Webhooks
```python
webhook_id = manager.register_webhook(
    url="https://secure.example.com/webhook",
    event_types=[EventType.APPLICATION_SUBMITTED],
    secret="my-secure-key",  # For HMAC signing
    headers={"Authorization": "Bearer token123"}
)
```

### Pattern 4: Retry Configuration
```python
webhook_id = manager.register_webhook(
    url="https://unreliable.example.com/webhook",
    event_types=[EventType.DECISION_MADE],
    retry_max_attempts=10,         # Try 10 times
    retry_initial_delay=5.0,       # Start with 5s
    retry_backoff_factor=1.5,      # Increase by 50%
)

# Retry schedule: 5s, 7.5s, 11.25s, 16.87s, ...
```

### Pattern 5: Monitoring
```python
# Global stats
stats = manager.get_webhook_statistics()
print(f"Active: {stats['active_webhooks']}")

# Per-webhook stats
webhook_stats = manager.get_webhook_statistics(webhook_id=webhook_id)
webhooks = webhook_stats['webhooks'][webhook_id]
print(f"Success rate: {webhooks['successful']}/{webhooks['total_events']}")

# Failed deliveries
failed = manager.get_delivery_logs(status=WebhookStatus.FAILED)
print(f"Failed deliveries: {len(failed)}")
```

### Pattern 6: Enable/Disable
```python
# Disable for maintenance
manager.update_webhook_status(webhook_id, active=False)

# Re-enable after maintenance
manager.update_webhook_status(webhook_id, active=True)

# Only trigger events to active webhooks
manager.trigger_event(event_type=EventType.APPLICATION_SUBMITTED, payload={...})
```

### Pattern 7: Logging & Auditing
```python
# Get all logs for specific webhook
logs = manager.get_delivery_logs(webhook_id=webhook_id, limit=100)
for log in logs:
    print(f"{log['timestamp']}: {log['status']} (code: {log['status_code']})")

# Export for archival
manager.export_logs_json("/backups/webhook_logs.json")
manager.export_webhooks_json("/backups/webhooks.json")

# Clean up old logs (> 30 days)
deleted = manager.clear_delivery_logs(older_than_days=30)
```

## Retry & Backoff Formula

```
delay = initial_delay * (backoff_factor ^ (attempt - 1))

Default: 1.0 * (2.0 ^ 0) = 1.0s
         1.0 * (2.0 ^ 1) = 2.0s
         1.0 * (2.0 ^ 2) = 4.0s
         1.0 * (2.0 ^ 3) = 8.0s
         1.0 * (2.0 ^ 4) = 16.0s
```

## Response Format

### Event Payload Sent to Webhook
```json
{
  "event_id": "evt-abc123",
  "event_type": "application_submitted",
  "timestamp": "2026-06-20T14:16:58.123456",
  "data": {
    "application_id": "APP-001",
    "user_email": "user@example.com"
  }
}
```

### Headers Sent
```
Content-Type: application/json
X-Webhook-Signature: <HMAC-SHA256>
X-Webhook-ID: <webhook-id>
X-Event-Type: application_submitted
[Custom headers from registration]
```

### Delivery Log Entry
```json
{
  "id": "log-123",
  "webhook_id": "webhook-456",
  "event_id": "evt-789",
  "status": "success",
  "timestamp": "2026-06-20T14:16:58.123456",
  "status_code": 200,
  "response_body": "...",
  "attempt_number": 1,
  "delivery_time_ms": 145.23
}
```

## Status Codes

| Status | Meaning | Auto-Retry |
|--------|---------|-----------|
| `SUCCESS` | Delivered (status < 300) | No |
| `FAILED` | Max retries exceeded | No |
| `PENDING` | Awaiting initial delivery | No |
| `RETRYING` | Scheduled for retry | Yes |

## Troubleshooting

### Event not being delivered?
1. Check webhook is registered: `manager.list_webhooks(active_only=True)`
2. Check webhook is active: `manager.get_webhook(webhook_id).active`
3. Check event type matches: `endpoint.event_types` includes event type
4. Check custom filter: `custom_filter(event)` returns True
5. Check pending events: `manager.pending_events`

### Delivery failing?
1. Check logs: `manager.get_delivery_logs(webhook_id=webhook_id)`
2. Check error message: `log['error_message']`
3. Check HTTP status code: `log['status_code']`
4. Check retry schedule: Is event scheduled for retry?

### Signature verification failing?
1. Verify secret matches: `endpoint.secret`
2. Verify payload format: JSON serialized with sorted keys
3. Use: `manager.verify_signature(payload, signature, secret)`

## Performance Tips

1. **Use async delivery**: `deliver_pending_events(async_mode=True)`
2. **Filter strategically**: Use custom filters to reduce unnecessary deliveries
3. **Disable unused webhooks**: `update_webhook_status(webhook_id, False)`
4. **Archive old logs**: `clear_delivery_logs(older_than_days=30)`
5. **Monitor statistics**: `get_webhook_statistics()` regularly

## File Structure

```
webhooks.py                 # Main module
test_webhooks.py           # Comprehensive test suite
webhook_example.py         # Integration examples
WEBHOOK_README.md          # Full documentation
WEBHOOK_QUICK_REFERENCE.md # This file
```

## Testing

Run all tests:
```bash
python -m unittest test_webhooks -v
```

Run examples:
```bash
python webhook_example.py
```

## API Cheat Sheet

| Method | Purpose |
|--------|---------|
| `register_webhook()` | Add webhook endpoint |
| `deregister_webhook()` | Remove webhook endpoint |
| `get_webhook()` | Get endpoint details |
| `list_webhooks()` | List all endpoints |
| `update_webhook_status()` | Enable/disable endpoint |
| `trigger_event()` | Create event(s) |
| `deliver_pending_events()` | Send all pending events |
| `get_delivery_logs()` | Query delivery history |
| `get_webhook_statistics()` | Get performance stats |
| `clear_delivery_logs()` | Delete old logs |
| `verify_signature()` | Validate webhook signature |
| `export_webhooks_json()` | Backup webhooks |
| `export_logs_json()` | Backup logs |

## Best Practices

1. **Always use HTTPS**: For production deployments
2. **Verify signatures**: Check `X-Webhook-Signature` header
3. **Implement idempotency**: Handle duplicate deliveries gracefully
4. **Set timeouts**: Default 10 seconds per request
5. **Monitor failures**: Track FAILED status webhooks
6. **Log everything**: Use delivery logs for auditing
7. **Clean up regularly**: Archive and delete old logs
8. **Test webhooks**: Use test endpoints during development
9. **Handle retries gracefully**: Implement exponential backoff on receiver
10. **Document payload schema**: For webhook consumers

## Example: Complete Integration

```python
from webhooks import WebhookManager, EventType, WebhookStatus

# Initialize
manager = WebhookManager()

# Register multiple endpoints
analytics = manager.register_webhook(
    url="https://analytics.example.com/events",
    event_types=[EventType.APPLICATION_SUBMITTED],
    headers={"X-API-Key": "key123"}
)

notifications = manager.register_webhook(
    url="https://notify.example.com/webhook",
    event_types=[EventType.DECISION_MADE],
    secret="secure-secret",
    retry_max_attempts=7,
    retry_initial_delay=2.0
)

# Trigger events
manager.trigger_event(
    event_type=EventType.APPLICATION_SUBMITTED,
    payload={"application_id": "APP-001", "priority": "high"}
)

# Deliver asynchronously
manager.deliver_pending_events(async_mode=True)

# Monitor
stats = manager.get_webhook_statistics()
print(f"Delivered {stats['webhooks'][analytics]['successful']} events")

# Export for backup
manager.export_webhooks_json("webhooks_backup.json")
manager.export_logs_json("logs_backup.json")
```
