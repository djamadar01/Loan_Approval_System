# NotificationSystem MCP Server - Quick Start Guide

## Overview

A production-ready MCP server built with FastMCP for managing notifications with comprehensive audit trail logging, automatic Case ID generation, and timestamp recording.

## Key Features

- **Send Notifications**: Multiple types (general, alert, warning, urgent) and priorities (low, normal, high, critical)
- **Case ID Generation**: Automatic unique IDs in format `NOTIF-YYYYMMDD-XXXXXX`
- **Audit Trail**: Complete action history with timestamps, actors, and results
- **Status Tracking**: Query notification status and full audit history

## Files

| File | Purpose |
|------|---------|
| `notification_system_mcp.py` | Main FastMCP server implementation |
| `notification_system_client.py` | Client library and demo utilities |
| `test_notification_system.py` | Comprehensive test suite (25 tests) |
| `NOTIFICATION_SYSTEM_README.md` | Full documentation |
| `NOTIFICATION_SYSTEM_QUICK_START.md` | This file |

## Installation

```bash
pip install fastmcp pydantic
```

## Quick Usage

### 1. Direct Usage (No Server)

```python
from notification_system_mcp import NotificationService

service = NotificationService()

# Send notification
response = service.send_notification(
    recipient="user@example.com",
    subject="Hello",
    message="Test message",
    notification_type="general",
    priority="normal"
)

print(f"Case ID: {response.case_id}")
print(f"Status: {response.status}")
```

### 2. With Demo

```bash
# Run direct demo (no server required)
python notification_system_client.py --mode direct

# Example output shows:
# - Sending 3 notifications (general, alert, urgent)
# - Retrieving status with audit trail
# - Listing all Case IDs
# - Full audit trail entries
```

### 3. Run Tests

```bash
# Run all 25 tests
python -m unittest test_notification_system -v

# All tests pass covering:
# - Case ID generation and uniqueness
# - Audit trail logging
# - Notification sending
# - Status retrieval
# - Metadata handling
# - End-to-end workflows
```

## Core Components

### CaseIDManager
Generates and tracks Case IDs
```python
manager = CaseIDManager()
case_id = manager.generate_case_id()  # NOTIF-20260618-ABC123
manager.register_case_id(case_id, "user@example.com", "Subject", "general")
```

### AuditTrailManager
Manages audit trail logging
```python
manager = AuditTrailManager()
manager.log_action(
    case_id="NOTIF-20260618-ABC123",
    action="notification_sent",
    details={"recipient": "user@example.com"},
    result="success"
)
```

### NotificationService
Main notification business logic
```python
service = NotificationService()
response = service.send_notification(
    recipient="user@example.com",
    subject="Subject",
    message="Message",
    notification_type="general",
    priority="normal",
    metadata={"custom": "value"}
)
```

## Audit Log Files

The system creates three log files in `./audit_logs/`:

1. **audit_trail.log** - Human-readable log
   ```
   2026-06-18 10:38:16 - audit_trail - INFO - Processing notification - Case ID: NOTIF-20260618-6591DE, Recipient: alice@example.com, Type: general
   ```

2. **notifications.jsonl** - Machine-readable audit entries (one per line)
   ```json
   {"timestamp":"2026-06-18T05:08:16.648902+00:00","case_id":"NOTIF-20260618-6591DE","action":"notification_initiated","actor":"notification_service","details":{...},"result":"pending"}
   ```

3. **case_ids.json** - Case ID registry
   ```json
   {
     "NOTIF-20260618-6591DE": {
       "timestamp": "2026-06-18T05:08:16.649208+00:00",
       "recipient": "alice@example.com",
       "subject": "Account Update",
       "notification_type": "general"
     }
   }
   ```

## API Tools

### send_notification
Send a notification with audit trail logging

**Parameters:**
- `recipient` (string): Recipient email or identifier
- `subject` (string): Notification subject
- `message` (string): Notification message
- `notification_type` (string, optional): "general" | "alert" | "warning" | "urgent"
- `priority` (string, optional): "low" | "normal" | "high" | "critical"
- `metadata` (string, optional): JSON string of additional data

**Returns:**
```json
{
  "case_id": "NOTIF-20260618-ABC123",
  "timestamp": "2026-06-18T05:08:16.648587+00:00",
  "status": "sent",
  "recipient": "user@example.com",
  "summary": "Notification successfully sent with Case ID NOTIF-20260618-ABC123...",
  "message_id": "MSG-20260618050816-000001"
}
```

### get_notification_status
Get status and audit trail of a notification

**Parameters:**
- `case_id` (string): The Case ID to retrieve

**Returns:** Status, case info, and audit trail entries

### list_all_notifications
List all Case IDs and their information

**Returns:** Total count and all Case IDs with details

### get_audit_trail
Get audit trail for a specific case or all entries

**Parameters:**
- `case_id` (string, optional): Case ID to filter by

**Returns:** Audit entries with timestamps and results

### get_system_info
Get system information and statistics

**Returns:** System status and audit log statistics

## Example Workflows

### Workflow 1: Send and Track Alert

```python
from notification_system_mcp import NotificationService

service = NotificationService()

# Send alert
response = service.send_notification(
    recipient="admin@example.com",
    subject="Security Alert",
    message="Suspicious login detected",
    notification_type="alert",
    priority="high",
    metadata={"alert_id": "SEC-001", "ip": "192.168.1.1"}
)

# Get full audit trail
status = service.get_notification_status(response.case_id)
print(f"Case: {status['case_id']}")
print(f"Actions: {status['total_actions']}")
for entry in status['audit_trail']:
    print(f"  {entry['timestamp']}: {entry['action']} -> {entry['result']}")
```

### Workflow 2: Compliance Report

```python
from notification_system_mcp import NotificationService

service = NotificationService()

# Get all audit entries
all_entries = service.audit_trail_manager.get_all_audit_entries()

# Generate report
print(f"Total notifications: {len(service.case_id_manager.list_case_ids())}")
print(f"Total audit entries: {len(all_entries)}")

# Group by action
actions = {}
for entry in all_entries:
    action = entry["action"]
    actions[action] = actions.get(action, 0) + 1

print("\nActions performed:")
for action, count in sorted(actions.items()):
    print(f"  {action}: {count}")
```

## Configuration

### Customize Audit Log Directory

```python
from pathlib import Path
from notification_system_mcp import Config

Config.AUDIT_LOG_DIR = Path("/var/log/notification-system")
Config.ensure_dirs()
```

## Testing

All 25 tests pass covering:
- Case ID generation and uniqueness
- Case ID registration and persistence
- Audit trail logging and retrieval
- Notification sending with various types/priorities
- Status retrieval
- Metadata handling
- End-to-end notification flows
- Multiple notification tracking

Run tests:
```bash
python -m unittest test_notification_system -v
```

## Data Models

### NotificationRequest
Input validation for notifications

### NotificationResponse
Response structure with Case ID, timestamp, status, summary

### AuditEntry
Audit trail record with timestamp, case ID, action, actor, details, result

## Performance

- **File I/O**: JSONL format for efficient streaming
- **Case IDs**: UUID-based randomness, no database needed
- **Memory**: Case IDs loaded at startup
- **Scalability**: JSONL allows easy log rotation and archival

## Security Considerations

- Audit logs are append-only
- JSON metadata is validated before storage
- Implement transport-layer access control (HTTP headers, etc.)
- Consider encryption for audit logs at rest in production

## Troubleshooting

### Audit logs not created
```bash
chmod 755 ./audit_logs
```

### Case ID not found
Check `audit_logs/case_ids.json`:
```bash
cat audit_logs/case_ids.json | python -m json.tool
```

### Server won't start
```bash
pip install --upgrade fastmcp pydantic
```

## Example Output

### Sending 3 Notifications
```
[1] Sending general notification...
Response: Case ID NOTIF-20260618-6591DE, Status: sent

[2] Sending alert notification...
Response: Case ID NOTIF-20260618-5BE5A7, Status: sent

[3] Sending urgent notification...
Response: Case ID NOTIF-20260618-532A9F, Status: sent
```

### Checking Status
```
[4] Checking status for Case ID: NOTIF-20260618-6591DE...
Status:
  - case_info: recipient alice@example.com, type general
  - audit_trail: 2 entries
    1. notification_initiated (pending)
    2. notification_sent (success)
```

### Audit Trail Entry
```json
{
  "timestamp": "2026-06-18T05:08:16.648902+00:00",
  "case_id": "NOTIF-20260618-6591DE",
  "action": "notification_initiated",
  "actor": "notification_service",
  "details": {
    "recipient": "alice@example.com",
    "subject": "Account Update",
    "notification_type": "general",
    "priority": "normal"
  },
  "result": "pending"
}
```

## Next Steps

1. **Integration**: Import `NotificationService` into your application
2. **Customization**: Extend with your notification backends
3. **Deployment**: Configure audit log persistence and access
4. **Monitoring**: Use audit logs for compliance and debugging

## Additional Resources

- Full documentation: `NOTIFICATION_SYSTEM_README.md`
- Source code: `notification_system_mcp.py`
- Tests: `test_notification_system.py`
- Client: `notification_system_client.py`

## Support

For detailed API documentation and advanced usage, see `NOTIFICATION_SYSTEM_README.md`.
