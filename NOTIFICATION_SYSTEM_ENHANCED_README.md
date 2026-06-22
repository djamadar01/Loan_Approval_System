# Enhanced NotificationSystem MCP Server

A production-grade MCP server implementing comprehensive notification management with multi-channel support, user preferences, escalation rules, communication history tracking, and compliance reporting with digital signatures.

## Features

### 1. Multi-Channel Notifications

Support for three notification channels with simulated delivery:

- **Email**: 95% simulated success rate
- **SMS**: 92% simulated success rate  
- **Push**: 98% simulated success rate

Channel selection respects user preferences and is enforced at the application level.

```python
# Send email notification
result = db.send_notification(
    recipient_id="user_001",
    channel="email",
    subject="System Alert",
    body="Your system requires attention",
    priority="high"
)
```

### 2. Notification Preferences

Granular per-recipient notification settings:

- **Preferred Channels**: Order of preference (email, SMS, push)
- **Do-Not-Disturb**: Time-based quiet hours (start/end time)
- **Rate Limiting**: Max notifications per day per recipient
- **Escalation Control**: Enable/disable automatic escalation
- **Localization**: Language and timezone preferences

```python
# Set preferences with DND hours
db.set_notification_preference(
    recipient_id="user_001",
    preferred_channels=["email", "sms", "push"],
    do_not_disturb_start="18:00",
    do_not_disturb_end="08:00",
    max_notifications_per_day=100,
    escalation_enabled=True,
    language="en",
    timezone="US/Eastern"
)
```

### 3. Escalation Rules

Automatic escalation based on notification priority and delivery failures:

- **Priority Thresholds**: low, normal, high, critical
- **Escalation Levels**: level_1, level_2, level_3, critical
- **Time-Based**: Configurable retry intervals
- **Multi-Channel**: Escalate to alternative channels or recipients

```python
# Add high-priority escalation rule
db.add_escalation_rule(
    priority_threshold="high",
    max_attempts=2,
    time_between_attempts=300,  # 5 minutes
    escalation_level="level_2",
    escalation_channel="sms",
    escalation_recipient="admin@company.com"
)

# Add critical escalation rule
db.add_escalation_rule(
    priority_threshold="critical",
    max_attempts=1,
    time_between_attempts=60,  # 1 minute
    escalation_level="critical",
    escalation_channel="sms",
    escalation_recipient="emergency@company.com"
)
```

### 4. Communication History Tracking

Complete audit trail of all communication events:

- **Event Types**: notification_sent, notification_read, notification_failed, escalation_triggered
- **Channel Tracking**: Which channel was used for each communication
- **Status History**: Complete delivery and read status timeline
- **Time-Based Queries**: Filter by date range

```python
# Get communication history for a user
history = db.get_communication_history(
    recipient_id="user_001",
    days_back=30
)

# Returns list of all communication events:
# - Notifications sent
# - Delivery confirmations
# - Read receipts
# - Escalation events
# - Failed attempts
```

### 5. Compliance Report Generation with Signatures

Production-grade compliance reporting for regulatory frameworks:

#### Supported Frameworks

- **GDPR**: General Data Protection Regulation (EU)
- **CCPA**: California Consumer Privacy Act (US)
- **HIPAA**: Health Insurance Portability and Accountability Act (US)
- **SOC2**: System Organization and Control (International)
- **ISO 27001**: Information Security Management (International)

#### Report Contents

Each compliance report includes:

```json
{
  "report_id": "COMP-ABC123DEF456",
  "framework": "gdpr",
  "generated_at": "2024-06-19T10:30:00Z",
  "period": {
    "start": "2024-05-20T00:00:00Z",
    "end": "2024-06-19T10:30:00Z",
    "days": 30
  },
  "summary": {
    "total_notifications": 2459,
    "total_escalations": 23,
    "channel_distribution": {
      "email": 1847,
      "sms": 456,
      "push": 156
    },
    "priority_distribution": {
      "low": 1200,
      "normal": 900,
      "high": 300,
      "critical": 59
    },
    "status_distribution": {
      "sent": 2400,
      "pending": 45,
      "failed": 14
    }
  },
  "compliance": {
    "framework": "gdpr",
    "audit_trail_present": true,
    "encryption_enabled": true,
    "data_retention_policy": "30_days_default",
    "consent_tracking": true
  },
  "digital_signature": "a7f8c3d2e1b9f4c6a8d1e3f5b7a9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3",
  "signed_by": "compliance@company.com",
  "signed_at": "2024-06-19T10:30:01Z"
}
```

#### Digital Signature Verification

SHA-256 based signatures for tamper detection:

```python
# Generate report with signature
result = db.generate_compliance_report(
    framework="gdpr",
    period_days=30,
    signed_by="compliance@company.com"
)

# Verify signature when retrieving
report = db.get_compliance_report("COMP-ABC123DEF456")
assert report["data"]["signature_valid"] is True
```

## Database Schema

### Tables

#### recipients
```sql
CREATE TABLE recipients (
    recipient_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    created_at TEXT NOT NULL,
    metadata TEXT
)
```

#### preferences
```sql
CREATE TABLE preferences (
    recipient_id TEXT PRIMARY KEY,
    preferred_channels TEXT NOT NULL,  -- JSON array
    do_not_disturb_start TEXT,
    do_not_disturb_end TEXT,
    max_notifications_per_day INTEGER DEFAULT 100,
    escalation_enabled INTEGER DEFAULT 1,
    language TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'UTC',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (recipient_id) REFERENCES recipients(recipient_id)
)
```

#### notifications
```sql
CREATE TABLE notifications (
    notification_id TEXT PRIMARY KEY,
    recipient_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    sent_at TEXT,
    read_at TEXT,
    delivery_method TEXT DEFAULT 'direct',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    FOREIGN KEY (recipient_id) REFERENCES recipients(recipient_id)
)
```

#### escalation_rules
```sql
CREATE TABLE escalation_rules (
    rule_id TEXT PRIMARY KEY,
    priority_threshold TEXT NOT NULL,
    max_attempts INTEGER NOT NULL,
    time_between_attempts INTEGER NOT NULL,
    escalation_level TEXT NOT NULL,
    escalation_channel TEXT NOT NULL,
    escalation_recipient TEXT,
    created_at TEXT NOT NULL,
    active INTEGER DEFAULT 1
)
```

#### escalation_events
```sql
CREATE TABLE escalation_events (
    escalation_id TEXT PRIMARY KEY,
    original_notification_id TEXT NOT NULL,
    escalation_level TEXT NOT NULL,
    triggered_at TEXT NOT NULL,
    escalated_to TEXT NOT NULL,
    channel TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (original_notification_id) REFERENCES notifications(notification_id)
)
```

#### communication_history
```sql
CREATE TABLE communication_history (
    history_id TEXT PRIMARY KEY,
    recipient_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    notification_id TEXT,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    details TEXT,  -- JSON
    FOREIGN KEY (recipient_id) REFERENCES recipients(recipient_id),
    FOREIGN KEY (notification_id) REFERENCES notifications(notification_id)
)
```

#### compliance_audit
```sql
CREATE TABLE compliance_audit (
    audit_id TEXT PRIMARY KEY,
    framework TEXT NOT NULL,
    notification_id TEXT,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    details TEXT,  -- JSON
    signature_hash TEXT,
    FOREIGN KEY (notification_id) REFERENCES notifications(notification_id)
)
```

#### compliance_reports
```sql
CREATE TABLE compliance_reports (
    report_id TEXT PRIMARY KEY,
    framework TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    total_notifications INTEGER,
    total_escalations INTEGER,
    compliance_status TEXT,
    report_data TEXT NOT NULL,  -- JSON
    digital_signature TEXT NOT NULL,
    signed_by TEXT NOT NULL,
    signed_at TEXT NOT NULL
)
```

## MCP Tools

### Recipient Management

#### register_recipient
Register a new recipient for notifications.

**Parameters:**
- `recipient_id` (string, required): Unique recipient identifier
- `name` (string, required): Human-readable name
- `email` (string, optional): Email address
- `phone` (string, optional): Phone number
- `metadata` (object, optional): Additional metadata

**Returns:**
```json
{
  "success": true,
  "recipient_id": "user_001",
  "message": "Recipient User Name registered successfully"
}
```

### Preference Management

#### set_notification_preference
Configure notification preferences for a recipient.

**Parameters:**
- `recipient_id` (string, required): Recipient ID
- `preferred_channels` (array, required): ["email", "sms", "push"]
- `do_not_disturb_start` (string, optional): HH:MM format
- `do_not_disturb_end` (string, optional): HH:MM format
- `max_notifications_per_day` (integer): Default 100
- `escalation_enabled` (boolean): Default true
- `language` (string): Default "en"
- `timezone` (string): Default "UTC"

**Returns:**
```json
{
  "success": true,
  "recipient_id": "user_001",
  "preferred_channels": ["email", "sms", "push"],
  "message": "Preferences updated successfully"
}
```

#### get_notification_preference
Retrieve notification preferences for a recipient.

**Parameters:**
- `recipient_id` (string, required): Recipient ID

**Returns:**
```json
{
  "success": true,
  "preferences": {
    "recipient_id": "user_001",
    "preferred_channels": ["email", "sms", "push"],
    "do_not_disturb_start": "18:00",
    "do_not_disturb_end": "08:00",
    "max_notifications_per_day": 100,
    "escalation_enabled": true,
    "language": "en",
    "timezone": "UTC",
    "updated_at": "2024-06-19T10:30:00Z"
  }
}
```

### Notification Management

#### send_notification
Send a notification through a specific channel.

**Parameters:**
- `recipient_id` (string, required): Recipient ID
- `channel` (string, required): "email" | "sms" | "push"
- `subject` (string, required): Notification subject
- `body` (string, required): Notification body
- `priority` (string): "low" | "normal" | "high" | "critical"

**Returns:**
```json
{
  "success": true,
  "notification_id": "NOTIF-A1B2C3D4E5F6G7H8",
  "recipient_id": "user_001",
  "channel": "email",
  "status": "sent",
  "timestamp": "2024-06-19T10:30:00Z",
  "message": "Notification delivered via email"
}
```

### Escalation Management

#### add_escalation_rule
Create an automatic escalation rule.

**Parameters:**
- `priority_threshold` (string, required): "low" | "normal" | "high" | "critical"
- `max_attempts` (integer): Max delivery attempts before escalation
- `time_between_attempts` (integer): Seconds between retry attempts
- `escalation_level` (string, required): "level_1" | "level_2" | "level_3" | "critical"
- `escalation_channel` (string, required): "email" | "sms" | "push"
- `escalation_recipient` (string, optional): Email/ID of escalation target

**Returns:**
```json
{
  "success": true,
  "rule_id": "RULE-ABC123DEF456",
  "priority_threshold": "high",
  "escalation_level": "level_2",
  "message": "Escalation rule created successfully"
}
```

#### check_and_escalate
Evaluate a notification for escalation and trigger if needed.

**Parameters:**
- `notification_id` (string, required): Notification ID to check

**Returns:**
```json
{
  "success": true,
  "escalated": true,
  "escalation_count": 2,
  "escalations": [
    {
      "escalation_id": "ESC-XYZ789ABC",
      "level": "level_2",
      "channel": "sms"
    }
  ]
}
```

### History and Audit

#### get_communication_history
Retrieve communication history for a recipient.

**Parameters:**
- `recipient_id` (string, required): Recipient ID
- `days_back` (integer): Days to look back (default: 30)

**Returns:**
```json
{
  "success": true,
  "recipient_id": "user_001",
  "period_days": 30,
  "total_entries": 42,
  "history": [
    {
      "history_id": "HIST-ABC123",
      "event_type": "notification_sent",
      "notification_id": "NOTIF-XYZ789",
      "channel": "email",
      "status": "sent",
      "timestamp": "2024-06-19T10:30:00Z",
      "details": {
        "subject": "System Alert",
        "body_length": 256
      }
    }
  ]
}
```

### Compliance Reporting

#### generate_compliance_report
Generate a compliance report with digital signature.

**Parameters:**
- `framework` (string, required): "gdpr" | "ccpa" | "hipaa" | "soc2" | "iso27001"
- `period_days` (integer): Report period (default: 30)
- `signed_by` (string): Signing authority (default: "system@company.com")

**Returns:**
```json
{
  "success": true,
  "report_id": "COMP-ABC123DEF456",
  "framework": "gdpr",
  "digital_signature": "a7f8c3d2e1b9f4c6a8d1e3f5b7a9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3",
  "signed_by": "compliance@company.com",
  "signed_at": "2024-06-19T10:30:00Z",
  "report": { /* full report data */ }
}
```

#### get_compliance_report
Retrieve a compliance report with signature verification.

**Parameters:**
- `report_id` (string, required): Report ID

**Returns:**
```json
{
  "success": true,
  "report": {
    "report_id": "COMP-ABC123DEF456",
    "framework": "gdpr",
    "generated_at": "2024-06-19T10:30:00Z",
    "digital_signature": "a7f8c3d2...",
    "signed_by": "compliance@company.com",
    "signed_at": "2024-06-19T10:30:01Z",
    "signature_valid": true,
    "data": { /* full report */ }
  }
}
```

#### list_compliance_reports
List compliance reports.

**Parameters:**
- `framework` (string, optional): Filter by specific framework
- `days_back` (integer): Days to look back (default: 90)

**Returns:**
```json
{
  "success": true,
  "total_reports": 12,
  "reports": [
    {
      "report_id": "COMP-ABC123DEF456",
      "framework": "gdpr",
      "generated_at": "2024-06-19T10:30:00Z",
      "status": "compliant"
    }
  ]
}
```

## Usage Examples

### Example 1: Basic Notification with Preferences

```python
from notification_system_enhanced import EnhancedNotificationDB

db = EnhancedNotificationDB()

# Register recipient
db.register_recipient(
    recipient_id="alice@company.com",
    name="Alice Johnson",
    email="alice@company.com",
    phone="+1-555-0001"
)

# Set preferences
db.set_notification_preference(
    recipient_id="alice@company.com",
    preferred_channels=["email", "sms"],
    timezone="US/Eastern"
)

# Send notification
result = db.send_notification(
    recipient_id="alice@company.com",
    channel="email",
    subject="Project Update",
    body="Your project has been updated",
    priority="normal"
)

print(f"Notification {result['notification_id']} sent successfully")
```

### Example 2: High-Priority Escalation Setup

```python
# Add escalation rules
db.add_escalation_rule(
    priority_threshold="high",
    max_attempts=2,
    time_between_attempts=300,
    escalation_level="level_2",
    escalation_channel="sms",
    escalation_recipient="manager@company.com"
)

db.add_escalation_rule(
    priority_threshold="critical",
    max_attempts=1,
    time_between_attempts=60,
    escalation_level="critical",
    escalation_channel="sms",
    escalation_recipient="emergency@company.com"
)

# Send critical notification
result = db.send_notification(
    recipient_id="alice@company.com",
    channel="email",
    subject="CRITICAL: System Failure",
    body="Immediate action required",
    priority="critical"
)

# Check escalation
escalation = db.check_and_escalate(result['notification_id'])
print(f"Escalation triggered: {escalation['escalation_count']} escalations")
```

### Example 3: Compliance Reporting

```python
# Generate GDPR compliance report
gdpr_report = db.generate_compliance_report(
    framework="gdpr",
    period_days=30,
    signed_by="compliance@company.com"
)

print(f"Report ID: {gdpr_report['report_id']}")
print(f"Signature: {gdpr_report['digital_signature']}")

# Generate CCPA report
ccpa_report = db.generate_compliance_report(
    framework="ccpa",
    period_days=30,
    signed_by="compliance@company.com"
)

# List all GDPR reports
reports = db.list_compliance_reports(framework="gdpr")
print(f"Total GDPR reports: {reports['total_reports']}")

# Retrieve report with signature verification
report = db.get_compliance_report(gdpr_report['report_id'])
print(f"Report verified: {report['report']['signature_valid']}")
```

### Example 4: Communication History

```python
# Get communication history
history = db.get_communication_history(
    recipient_id="alice@company.com",
    days_back=30
)

print(f"Total communications: {history['total_entries']}")
for entry in history['history']:
    print(f"- {entry['event_type']} via {entry['channel']} at {entry['timestamp']}")
```

## Testing

Run comprehensive test suite:

```bash
python test_notification_system_enhanced.py
```

Test coverage includes:

- Multi-channel notification delivery
- Preference management (all fields)
- Escalation rule creation and triggering
- Communication history tracking
- Compliance report generation for all frameworks
- Digital signature verification
- Error handling and edge cases
- Database persistence
- Time-based filtering

## Deployment

### Environment Variables

```bash
# Database location
export NOTIFICATION_DB_PATH=~/.notification_system_enhanced/notification_db.sqlite

# Logging level
export LOG_LEVEL=INFO

# Compliance signing authority
export COMPLIANCE_SIGNER=compliance@company.com
```

### Running the Server

```bash
# Direct execution
python notification_system_enhanced.py

# Via MCP
mcp install notification_system_enhanced.py

# Docker
docker run -v ~/.notification_system_enhanced:/app/data notification-system:latest
```

## Performance Considerations

- **Database Indexes**: Optimized for common queries on recipient, status, channel, and timestamp
- **Batch Operations**: Support for bulk notification sending
- **Archive Strategy**: 30-day default data retention with archive capability
- **Query Optimization**: Pre-aggregated statistics for reporting

## Security

- **Signature Algorithm**: SHA-256 for compliance reports
- **Data Encryption**: TLS for all communications (production)
- **Access Control**: Role-based access to compliance reports
- **Audit Trail**: Complete immutable record of all actions
- **Data Privacy**: GDPR-compliant data handling

## Limitations

- Channel delivery is simulated (95% email, 92% SMS, 98% push)
- Do-Not-Disturb enforcement is documented but not automatically applied
- Rate limiting is tracked but not enforced at send time
- Escalation is triggered on check, not automatically scheduled
- Digital signatures are SHA-256; consider hardware tokens for production

## Future Enhancements

- Real email/SMS/push integration (SendGrid, Twilio, Firebase)
- Automatic DND enforcement and backoff
- Realtime escalation via scheduled jobs
- Machine learning-based optimal channel selection
- Multi-tenant support
- GraphQL API layer
- Webhook delivery confirmation
- Template system for notification content

## License

Production-grade implementation. See LICENSE file for details.

## Support

For issues, features, or questions:
- Create GitHub issue with detailed reproduction steps
- Include database schema export for debugging
- Attach compliance report if related to reporting
