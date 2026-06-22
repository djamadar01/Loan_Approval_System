# Webhook Management System

A complete, production-ready webhook management system with registration, event triggering, retry logic with exponential backoff, event filtering, and comprehensive delivery logging.

## Features

### 1. **Endpoint Registration/Deregistration**
- Register webhook endpoints with custom configurations
- Support for multiple event types per endpoint
- Custom headers for authentication and metadata
- HMAC-SHA256 signature generation for security
- Enable/disable webhooks without deregistration

### 2. **Event Types**
- **APPLICATION_SUBMITTED**: Triggered when a new application is submitted
- **DECISION_MADE**: Triggered when a decision is made on an application
- **STATUS_CHANGED**: Triggered when application status changes
- Extensible design for adding custom event types

### 3. **Retry Logic with Exponential Backoff**
- Configurable maximum retry attempts (default: 5)
- Exponential backoff delay calculation
- Customizable initial delay and backoff factor
- Automatic scheduling of retry attempts
- Failed events tracked for manual intervention

### 4. **Event Filtering**
- Filter by event type subscriptions
- Custom filter functions for advanced filtering
- Per-endpoint active status
- Endpoint-level filtering support
- Event payload-based filtering

### 5. **Webhook Delivery Logs**
- Comprehensive logging of all delivery attempts
- Status tracking (success, failed, retrying, pending)
- HTTP status codes and response bodies
- Delivery time measurement in milliseconds
- Attempt number tracking
- Log retention and cleanup policies

## Installation

```bash
# Required dependencies
pip install requests
```

## Quick Start

### Basic Usage

```python
from webhooks import WebhookManager, EventType

# Initialize manager
manager = WebhookManager()

# Register a webhook endpoint
webhook_id = manager.register_webhook(
    url="https://api.example.com/webhooks",
    event_types=[
        EventType.APPLICATION_SUBMITTED,
        EventType.DECISION_MADE,
    ],
)

# Trigger an event
event_ids = manager.trigger_event(
    event_type=EventType.APPLICATION_SUBMITTED,
    payload={
        "application_id": "APP-001",
        "user_email": "user@example.com",
    }
)

# Deliver pending events
stats = manager.deliver_pending_events(async_mode=True)
```

### Advanced Registration

```python
# Register with custom headers and retry settings
webhook_id = manager.register_webhook(
    url="https://service.example.com/webhook",
    event_types=[EventType.STATUS_CHANGED],
    secret="custom-secret-key",  # For HMAC signing
    headers={
        "Authorization": "Bearer token123",
        "X-Service": "my-service",
    },
    custom_filter=lambda event: event["payload"].get("priority") == "high",
    retry_max_attempts=7,
    retry_initial_delay=2.0,        # seconds
    retry_backoff_factor=2.0,       # exponential factor
)
```

## API Reference

### WebhookManager

#### Methods

##### `register_webhook()`
Register a new webhook endpoint.

```python
webhook_id = manager.register_webhook(
    url: str,
    event_types: List[EventType],
    secret: Optional[str] = None,
    custom_filter: Optional[Callable] = None,
    headers: Optional[Dict[str, str]] = None,
    retry_max_attempts: int = 5,
    retry_initial_delay: float = 1.0,
    retry_backoff_factor: float = 2.0,
) -> str
```

**Parameters:**
- `url`: Target URL for webhook delivery
- `event_types`: List of event types to subscribe to
- `secret`: Secret key for HMAC signing (auto-generated if not provided)
- `custom_filter`: Function to filter events: `(event: Dict) -> bool`
- `headers`: Custom HTTP headers to include in requests
- `retry_max_attempts`: Maximum number of retry attempts
- `retry_initial_delay`: Initial delay in seconds for retry backoff
- `retry_backoff_factor`: Multiplier for exponential backoff

**Returns:** Webhook endpoint ID

**Raises:** `ValueError` if URL invalid or event types empty

---

##### `deregister_webhook()`
Remove a webhook endpoint.

```python
success = manager.deregister_webhook(webhook_id: str) -> bool
```

**Parameters:**
- `webhook_id`: ID of webhook to remove

**Returns:** True if successful, False if not found

---

##### `get_webhook()`
Retrieve webhook endpoint by ID.

```python
endpoint = manager.get_webhook(webhook_id: str) -> Optional[WebhookEndpoint]
```

---

##### `list_webhooks()`
List all registered webhooks.

```python
webhooks = manager.list_webhooks(active_only: bool = False) -> List[Dict[str, Any]]
```

**Parameters:**
- `active_only`: If True, only return active webhooks

**Returns:** List of webhook dictionaries

---

##### `update_webhook_status()`
Enable or disable a webhook.

```python
success = manager.update_webhook_status(webhook_id: str, active: bool) -> bool
```

---

##### `trigger_event()`
Trigger an event to matching endpoints.

```python
event_ids = manager.trigger_event(
    event_type: EventType,
    payload: Dict[str, Any],
    endpoint_filter: Optional[Callable[[WebhookEndpoint], bool]] = None,
) -> List[str]
```

**Parameters:**
- `event_type`: Type of event to trigger
- `payload`: Event data payload
- `endpoint_filter`: Optional custom endpoint filter

**Returns:** List of created event IDs

---

##### `deliver_pending_events()`
Attempt to deliver all pending events.

```python
stats = manager.deliver_pending_events(async_mode: bool = False) -> Dict[str, Any]
```

**Parameters:**
- `async_mode`: If True, run in background threads

**Returns:** Dictionary with delivery statistics

---

##### `get_delivery_logs()`
Retrieve delivery logs with filtering.

```python
logs = manager.get_delivery_logs(
    webhook_id: Optional[str] = None,
    event_id: Optional[str] = None,
    status: Optional[WebhookStatus] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]
```

**Parameters:**
- `webhook_id`: Filter by webhook ID
- `event_id`: Filter by event ID
- `status`: Filter by delivery status
- `limit`: Maximum logs to return (default: 100)

**Returns:** List of delivery log dictionaries

---

##### `get_webhook_statistics()`
Get webhook statistics.

```python
stats = manager.get_webhook_statistics(webhook_id: Optional[str] = None) -> Dict[str, Any]
```

**Returns:** Dictionary containing:
- `total_webhooks`: Total number of webhooks
- `active_webhooks`: Number of active webhooks
- `webhooks`: Per-webhook statistics including:
  - `total_events`: Total delivery attempts
  - `successful`: Successful deliveries
  - `failed`: Failed deliveries
  - `retrying`: Events pending retry
  - `avg_delivery_time_ms`: Average delivery time

---

##### `clear_delivery_logs()`
Delete old delivery logs.

```python
deleted = manager.clear_delivery_logs(older_than_days: int = 30) -> int
```

**Returns:** Number of logs deleted

---

##### `verify_signature()`
Verify a webhook signature.

```python
is_valid = manager.verify_signature(
    payload: Dict[str, Any],
    signature: str,
    secret: str
) -> bool
```

---

##### `export_webhooks_json()`
Export webhooks to JSON file.

```python
manager.export_webhooks_json(filepath: str) -> None
```

---

##### `export_logs_json()`
Export delivery logs to JSON file.

```python
manager.export_logs_json(filepath: str) -> None
```

---

### EventType (Enum)

Supported event types:
- `EventType.APPLICATION_SUBMITTED`
- `EventType.DECISION_MADE`
- `EventType.STATUS_CHANGED`

### WebhookStatus (Enum)

Delivery status values:
- `WebhookStatus.SUCCESS`: Delivery successful (status code < 300)
- `WebhookStatus.FAILED`: Delivery failed after all retries
- `WebhookStatus.PENDING`: Pending initial delivery attempt
- `WebhookStatus.RETRYING`: Scheduled for retry

## Usage Examples

### Example 1: Multi-Tenant Webhook System

```python
manager = WebhookManager()

# Register webhooks for different services
analytics_webhook = manager.register_webhook(
    url="https://analytics.company.com/events",
    event_types=[EventType.APPLICATION_SUBMITTED],
    headers={"X-API-Key": "analytics-key"},
)

crm_webhook = manager.register_webhook(
    url="https://crm.company.com/applications",
    event_types=[EventType.APPLICATION_SUBMITTED, EventType.DECISION_MADE],
    headers={"Authorization": "Bearer crm-token"},
)

# Trigger event - will send to both endpoints
manager.trigger_event(
    event_type=EventType.APPLICATION_SUBMITTED,
    payload={"application_id": "APP-123", "user": "john@example.com"}
)

# Deliver events
manager.deliver_pending_events(async_mode=True)
```

### Example 2: Priority-Based Filtering

```python
# Only send high-priority applications to premium service
premium_webhook = manager.register_webhook(
    url="https://premium.service.com/webhook",
    event_types=[EventType.APPLICATION_SUBMITTED],
    custom_filter=lambda event: event["payload"].get("priority") == "high",
)

# Trigger high-priority application
manager.trigger_event(
    event_type=EventType.APPLICATION_SUBMITTED,
    payload={
        "application_id": "APP-001",
        "priority": "high",
        "amount": 500000,
    }
)

# Trigger low-priority application (won't be sent to premium webhook)
manager.trigger_event(
    event_type=EventType.APPLICATION_SUBMITTED,
    payload={
        "application_id": "APP-002",
        "priority": "low",
        "amount": 5000,
    }
)
```

### Example 3: Unreliable Service with Retry

```python
# Configure webhook with aggressive retry strategy
webhook_id = manager.register_webhook(
    url="https://unreliable-service.com/webhook",
    event_types=[EventType.DECISION_MADE],
    retry_max_attempts=10,
    retry_initial_delay=5.0,        # Start with 5 second delay
    retry_backoff_factor=1.5,       # Increase delay by 50% each time
)

# Trigger event
manager.trigger_event(
    event_type=EventType.DECISION_MADE,
    payload={"application_id": "APP-001", "decision": "approved"}
)

# Attempt delivery with retries
manager.deliver_pending_events()

# Monitor delivery progress
logs = manager.get_delivery_logs(webhook_id=webhook_id)
for log in logs:
    print(f"Attempt {log['attempt_number']}: {log['status']} (code: {log['status_code']})")
```

### Example 4: Monitoring and Statistics

```python
# Get overall statistics
stats = manager.get_webhook_statistics()
print(f"Active webhooks: {stats['active_webhooks']}")

# Get specific webhook stats
webhook_stats = manager.get_webhook_statistics(webhook_id=webhook_id)
print(f"Success rate: {webhook_stats['webhooks'][webhook_id]['successful']} / "
      f"{webhook_stats['webhooks'][webhook_id]['total_events']}")

# Get recent failed deliveries
failed_logs = manager.get_delivery_logs(status=WebhookStatus.FAILED, limit=10)
for log in failed_logs:
    print(f"Failed: {log['error_message']} at {log['timestamp']}")
```

### Example 5: Webhook Security with Signatures

```python
# Register webhook with secret
webhook_id = manager.register_webhook(
    url="https://secure-service.com/webhook",
    event_types=[EventType.APPLICATION_SUBMITTED],
    secret="my-secure-secret",
)

# Get endpoint
endpoint = manager.get_webhook(webhook_id)

# Generate payload
payload = {
    "event_id": "evt-123",
    "event_type": "application_submitted",
    "data": {"application_id": "APP-001"}
}

# Generate signature for webhook verification
signature = manager._generate_signature(payload, endpoint.secret)

# Receiver can verify using:
# is_valid = manager.verify_signature(payload, signature, endpoint.secret)
```

## Retry Logic Details

The system uses exponential backoff for failed deliveries:

```
Attempt 1: immediate
Attempt 2: delay = initial_delay * (backoff_factor ^ 0) = 1.0s
Attempt 3: delay = initial_delay * (backoff_factor ^ 1) = 2.0s
Attempt 4: delay = initial_delay * (backoff_factor ^ 2) = 4.0s
Attempt 5: delay = initial_delay * (backoff_factor ^ 3) = 8.0s
```

For an unreliable service with default settings:
- Initial delay: 1.0 second
- Backoff factor: 2.0
- Max attempts: 5
- Total time window: ~15 seconds

Customize for your needs:
```python
# Quick retries for reliable services
webhook_1 = manager.register_webhook(..., retry_initial_delay=0.5, retry_backoff_factor=1.5)

# Aggressive retries for unreliable services
webhook_2 = manager.register_webhook(..., retry_max_attempts=10, retry_initial_delay=2.0)
```

## Data Models

### WebhookEndpoint
```python
@dataclass
class WebhookEndpoint:
    id: str                          # Unique identifier
    url: str                         # Target URL
    event_types: List[EventType]     # Subscribed event types
    secret: str                      # HMAC signing secret
    active: bool                     # Enable/disable status
    created_at: datetime             # Registration timestamp
    updated_at: datetime             # Last update timestamp
    custom_filter: Callable          # Event filter function
    headers: Dict[str, str]          # Custom HTTP headers
    retry_max_attempts: int          # Max retry count
    retry_initial_delay: float       # Initial retry delay
    retry_backoff_factor: float      # Exponential backoff factor
```

### WebhookEvent
```python
@dataclass
class WebhookEvent:
    id: str                          # Unique event identifier
    type: EventType                  # Event type
    timestamp: datetime              # Event creation time
    payload: Dict[str, Any]          # Event data
    endpoint_id: str                 # Target webhook ID
    attempt: int                     # Current attempt number
    next_retry: Optional[datetime]   # Scheduled retry time
```

### DeliveryLog
```python
@dataclass
class DeliveryLog:
    id: str                          # Log entry ID
    webhook_id: str                  # Webhook that attempted delivery
    event_id: str                    # Event that was delivered
    status: WebhookStatus            # Delivery status
    timestamp: datetime              # Log creation time
    status_code: Optional[int]       # HTTP status code
    response_body: Optional[str]     # HTTP response body (truncated)
    error_message: Optional[str]     # Error description
    attempt_number: int              # Delivery attempt number
    next_retry_at: Optional[datetime] # When next retry is scheduled
    delivery_time_ms: float          # Delivery duration in milliseconds
```

## Testing

Run the comprehensive test suite:

```bash
python test_webhooks.py
```

The test suite includes:
- Webhook registration and deregistration
- Event triggering and filtering
- Retry logic and exponential backoff
- Signature generation and verification
- Delivery logging and retrieval
- Statistics calculation
- Data serialization

## Performance Considerations

1. **Concurrent Deliveries**: Default max 5 concurrent delivery threads
2. **Log Retention**: Implement `clear_delivery_logs()` for cleanup
3. **Memory**: Store logs in memory; export to file for archival
4. **Retry Window**: Default max 15-31 seconds (depends on backoff factor)
5. **Event Queue**: Pending events stay in memory; implement persistence for production

## Production Deployment

For production use, consider:

1. **Persistence Layer**: Add database storage for webhooks, events, and logs
2. **Message Queue**: Use Redis/RabbitMQ for event queuing
3. **Monitoring**: Integrate with logging/alerting systems
4. **Rate Limiting**: Implement per-endpoint rate limits
5. **Signature Verification**: Always verify signatures on receiver side
6. **Webhook Validation**: Implement endpoint health checks
7. **Idempotency**: Implement idempotency keys for safe retries
8. **Circuit Breaker**: Add circuit breaker pattern for failing endpoints

## Error Handling

The system handles:
- Network timeouts (default 10s)
- HTTP error responses
- Network connection failures
- Invalid URLs
- Missing webhooks
- Duplicate event delivery
- Signature verification failures

## License

MIT License

## Support

For issues, feature requests, or contributions, please refer to the project documentation.
