# NotificationSystem MCP Server

A production-ready MCP server for managing notifications with comprehensive audit trail logging, Case ID generation, and timestamp tracking. Built with FastMCP and Pydantic.

## Features

### Core Capabilities

- **Send Notifications**: Send notifications with multiple types and priority levels
- **Case ID Generation**: Automatic unique Case ID generation for each notification (Format: `NOTIF-YYYYMMDD-XXXXXX`)
- **Timestamp Recording**: ISO 8601 formatted timestamps for all operations
- **Audit Trail Logging**: Complete audit trail of all notification actions
- **Status Tracking**: Query notification status and full action history

### Audit Trail Features

- Action logging with timestamps
- Actor tracking (who performed the action)
- Result recording (success/failure/pending)
- Detailed action metadata
- JSONL format for easy streaming and analysis
- File-based persistence for durability

### Notification Features

- Multiple notification types: general, alert, warning, urgent
- Priority levels: low, normal, high, critical
- Metadata support for custom fields
- JSON API responses

## Architecture

### Components

1. **CaseIDManager**: Generates and tracks Case IDs
2. **AuditTrailManager**: Manages audit trail logging
3. **NotificationService**: Core notification business logic
4. **FastMCP Server**: REST/JSON-RPC interface

### Data Models

- `NotificationRequest`: Input validation
- `NotificationResponse`: Response structure
- `AuditEntry`: Audit trail record
- `Config`: Configuration management

## Installation

```bash
# Install dependencies
pip install fastmcp pydantic

# Or use the project requirements
pip install -r requirements.txt
```

## Usage

### 1. Direct Usage (No Server)

```python
from notification_system_mcp import NotificationService

# Initialize service
service = NotificationService()

# Send notification
response = service.send_notification(
    recipient="user@example.com",
    subject="Account Update",
    message="Your account has been successfully updated.",
    notification_type="general",
    priority="normal",
    metadata={"update_type": "profile"}
)

print(f"Case ID: {response.case_id}")
print(f"Summary: {response.summary}")

# Get notification status
status = service.get_notification_status(response.case_id)
print(f"Audit trail entries: {len(status['audit_trail'])}")
```

### 2. Running as MCP Server

```bash
# Start the server
python notification_system_mcp.py
```

The server will:
- Initialize the audit logging system
- Set up required directories
- Start listening for tool calls
- Display available tools

### 3. Using the Client

```python
from notification_system_client import NotificationSystemClient

client = NotificationSystemClient("http://localhost:3000")

# Send notification
response = client.send_notification(
    recipient="user@example.com",
    subject="Test",
    message="Test message"
)

# Get status
status = client.get_notification_status(case_id)

# Get system info
info = client.get_system_info()
```

### 4. Running Demo

```bash
# Direct usage demo (no server required)
python notification_system_client.py --mode direct

# Server demo (requires running server)
python notification_system_client.py --mode server
```

## Available Tools

### send_notification

Send a notification with audit trail logging.

**Parameters:**
- `recipient` (string): Recipient email or identifier
- `subject` (string): Notification subject
- `message` (string): Notification message content
- `notification_type` (string, optional): Type of notification
  - `general` (default): General notification
  - `alert`: Alert notification
  - `warning`: Warning notification
  - `urgent`: Urgent notification
- `priority` (string, optional): Priority level
  - `low`: Low priority
  - `normal` (default): Normal priority
  - `high`: High priority
  - `critical`: Critical priority
- `metadata` (string, optional): JSON string of additional metadata

**Returns:**
```json
{
  "case_id": "NOTIF-20240118-ABC123",
  "timestamp": "2024-01-18T14:30:45.123456+00:00",
  "status": "sent",
  "recipient": "user@example.com",
  "summary": "Notification successfully sent with Case ID NOTIF-20240118-ABC123...",
  "message_id": "MSG-20240118143045-000001"
}
```

### get_notification_status

Get the status and audit trail of a notification.

**Parameters:**
- `case_id` (string): The Case ID to retrieve

**Returns:**
```json
{
  "case_id": "NOTIF-20240118-ABC123",
  "case_info": {
    "timestamp": "2024-01-18T14:30:45.123456+00:00",
    "recipient": "user@example.com",
    "subject": "Account Update",
    "notification_type": "general"
  },
  "audit_trail": [
    {
      "timestamp": "2024-01-18T14:30:45.123456+00:00",
      "case_id": "NOTIF-20240118-ABC123",
      "action": "notification_initiated",
      "actor": "notification_service",
      "details": {...},
      "result": "pending"
    },
    {
      "timestamp": "2024-01-18T14:30:45.234567+00:00",
      "case_id": "NOTIF-20240118-ABC123",
      "action": "notification_sent",
      "actor": "notification_service",
      "details": {...},
      "result": "success"
    }
  ],
  "total_actions": 2
}
```

### list_all_notifications

List all Case IDs and their information.

**Returns:**
```json
{
  "total_cases": 3,
  "case_ids": {
    "NOTIF-20240118-ABC123": {
      "timestamp": "2024-01-18T14:30:45.123456+00:00",
      "recipient": "user@example.com",
      "subject": "Account Update",
      "notification_type": "general"
    },
    ...
  }
}
```

### get_audit_trail

Get audit trail for a specific case or all entries.

**Parameters:**
- `case_id` (string, optional): Case ID to filter by. If omitted, returns all entries.

**Returns (for specific case):**
```json
{
  "case_id": "NOTIF-20240118-ABC123",
  "entries": [...],
  "total_entries": 2
}
```

**Returns (all entries):**
```json
{
  "total_entries": 5,
  "entries": [...]
}
```

### get_system_info

Get system information and statistics.

**Returns:**
```json
{
  "system": "NotificationSystem",
  "status": "operational",
  "statistics": {
    "total_notifications": 3,
    "total_audit_entries": 6,
    "audit_log_file": "/path/to/audit_logs/notifications.jsonl",
    "case_id_log_file": "/path/to/audit_logs/case_ids.json"
  }
}
```

## Audit Trail Logging

### Log Structure

The audit system creates multiple log files:

1. **audit_trail.log**: Human-readable log
   ```
   2024-01-18 14:30:45 - audit_trail - INFO - Processing notification - Case ID: NOTIF-20240118-ABC123, Recipient: user@example.com, Type: general
   ```

2. **notifications.jsonl**: Machine-readable audit entries (JSONL format)
   ```json
   {"timestamp":"2024-01-18T14:30:45.123456+00:00","case_id":"NOTIF-20240118-ABC123","action":"notification_initiated","actor":"notification_service","details":{...},"result":"pending"}
   {"timestamp":"2024-01-18T14:30:45.234567+00:00","case_id":"NOTIF-20240118-ABC123","action":"notification_sent","actor":"notification_service","details":{...},"result":"success"}
   ```

3. **case_ids.json**: Case ID registry
   ```json
   {
     "NOTIF-20240118-ABC123": {
       "timestamp": "2024-01-18T14:30:45.123456+00:00",
       "recipient": "user@example.com",
       "subject": "Account Update",
       "notification_type": "general"
     }
   }
   ```

### Audit Entry Fields

- `timestamp`: ISO 8601 timestamp of the action
- `case_id`: Associated Case ID
- `action`: Type of action (e.g., "notification_initiated", "notification_sent")
- `actor`: Who performed the action (default: "system")
- `details`: Action-specific details and metadata
- `result`: Outcome of the action ("success", "failure", "pending")

### Log Directory

By default, logs are stored in:
```
./audit_logs/
├── audit_trail.log        # Main audit log
├── notifications.jsonl    # Audit entries in JSONL format
└── case_ids.json          # Case ID registry
```

Configure the location by modifying `Config.AUDIT_LOG_DIR`:

```python
from pathlib import Path
from notification_system_mcp import Config

Config.AUDIT_LOG_DIR = Path("/var/log/notification-system")
```

## Case ID Format

Case IDs follow a structured format for easy identification and sorting:

```
NOTIF-20240118-ABC123
 |    |        |
 |    |        └─ 6-character random hex component
 |    └────────── Date (YYYYMMDD)
 └─────────────── System identifier
```

**Benefits:**
- Chronologically sortable
- Human-readable prefix
- Unique random component
- Easy to query and search

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest test_notification_system.py -v

# Run specific test class
python -m pytest test_notification_system.py::TestNotificationService -v

# Run with coverage
python -m pytest test_notification_system.py --cov=notification_system_mcp --cov-report=html
```

### Test Coverage

- Case ID generation and uniqueness
- Case ID registration and persistence
- Audit trail logging
- Notification sending with different types/priorities
- Status retrieval
- Metadata handling
- End-to-end workflows
- Multiple notification tracking

## Configuration

### Environment Setup

The system automatically creates required directories:

```python
from notification_system_mcp import Config

# Customize audit log directory
Config.AUDIT_LOG_DIR = Path("./custom_audit_logs")
Config.ensure_dirs()  # Create directories
```

### Logging Configuration

Logging is automatically configured on module import:

```python
from notification_system_mcp import audit_logger

# Use the audit logger
audit_logger.info("Custom message")
audit_logger.error("Error occurred")
```

## Example Workflows

### Workflow 1: Send Alert Notification

```python
from notification_system_mcp import NotificationService

service = NotificationService()

# Send high-priority alert
response = service.send_notification(
    recipient="admin@example.com",
    subject="Security Alert: Suspicious Activity",
    message="Unusual login detected from IP 192.168.1.1",
    notification_type="alert",
    priority="high",
    metadata={
        "alert_id": "SEC-12345",
        "ip_address": "192.168.1.1",
        "location": "Unknown"
    }
)

print(f"Alert sent with Case ID: {response.case_id}")

# Later, retrieve full audit trail
status = service.get_notification_status(response.case_id)
for entry in status["audit_trail"]:
    print(f"  {entry['timestamp']}: {entry['action']} - {entry['result']}")
```

### Workflow 2: Monitor Multiple Notifications

```python
from notification_system_mcp import NotificationService

service = NotificationService()

# Send multiple notifications
case_ids = []
for i in range(3):
    response = service.send_notification(
        recipient=f"team{i}@example.com",
        subject=f"Batch Notification {i}",
        message=f"Message {i}"
    )
    case_ids.append(response.case_id)

# Get comprehensive status
all_cases = service.case_id_manager.list_case_ids()
print(f"Total notifications: {len(all_cases)}")

# Get full audit
all_entries = service.audit_trail_manager.get_all_audit_entries()
print(f"Total audit entries: {len(all_entries)}")
```

### Workflow 3: Compliance Reporting

```python
from notification_system_mcp import NotificationService
from datetime import datetime

service = NotificationService()

# Get all audit entries
all_entries = service.audit_trail_manager.get_all_audit_entries()

# Generate compliance report
print("Compliance Report")
print("=" * 50)
print(f"Report generated: {datetime.now().isoformat()}")
print(f"Total audit entries: {len(all_entries)}")
print()

# Group by action
actions = {}
for entry in all_entries:
    action = entry["action"]
    actions[action] = actions.get(action, 0) + 1

print("Actions performed:")
for action, count in sorted(actions.items()):
    print(f"  {action}: {count}")

# Group by result
results = {}
for entry in all_entries:
    result = entry["result"]
    results[result] = results.get(result, 0) + 1

print("\nAction results:")
for result, count in sorted(results.items()):
    print(f"  {result}: {count}")
```

## Performance Considerations

1. **File I/O**: Audit entries are written to JSONL for efficient streaming
2. **Case ID Generation**: Uses UUID for randomness without database overhead
3. **Memory**: Case IDs loaded at startup; suitable for typical volumes
4. **Scalability**: JSONL format allows easy log rotation and archival

## Security Considerations

1. **Audit Immutability**: Audit logs are append-only
2. **Metadata Validation**: JSON metadata is validated before storage
3. **Access Control**: Implement at transport layer (HTTP headers, etc.)
4. **Encryption**: Consider encrypting audit logs at rest in production

## Troubleshooting

### Issue: Audit logs not created

**Solution**: Ensure the audit logs directory is writable:
```bash
chmod 755 ./audit_logs
```

### Issue: Case ID not found

**Solution**: Verify the Case ID format and check the case_ids.json file:
```bash
cat audit_logs/case_ids.json | jq
```

### Issue: Server won't start

**Solution**: Check dependencies are installed:
```bash
pip install fastmcp pydantic
```

## API Integration Examples

### cURL

```bash
# Send notification
curl -X POST http://localhost:3000/tools/send_notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "subject": "Test",
    "message": "Test message",
    "notification_type": "general",
    "priority": "normal"
  }'

# Get status
curl http://localhost:3000/tools/get_notification_status?case_id=NOTIF-20240118-ABC123

# Get system info
curl http://localhost:3000/tools/get_system_info
```

### Python requests

```python
import requests
import json

# Send notification
response = requests.post(
    "http://localhost:3000/tools/send_notification",
    json={
        "recipient": "user@example.com",
        "subject": "Test",
        "message": "Test message"
    }
)

data = response.json()
case_id = json.loads(data)["case_id"]

# Get status
status_response = requests.get(
    "http://localhost:3000/tools/get_notification_status",
    params={"case_id": case_id}
)

print(status_response.json())
```

## Files Overview

- `notification_system_mcp.py`: Main server implementation
- `notification_system_client.py`: Client library and demo
- `test_notification_system.py`: Comprehensive test suite
- `NOTIFICATION_SYSTEM_README.md`: This documentation

## License

This project is provided as-is for integration with MCP systems.

## Support

For issues or questions, refer to the test files for usage examples or the inline documentation in the source code.
