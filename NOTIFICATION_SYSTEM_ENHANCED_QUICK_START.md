# Enhanced NotificationSystem - Quick Start Guide

Get up and running with the Enhanced NotificationSystem MCP server in 5 minutes.

## Installation

### 1. Clone/Copy Files

```bash
cd /path/to/project
# Files needed:
# - notification_system_enhanced.py (server)
# - notification_system_enhanced_client.py (client examples)
# - test_notification_system_enhanced.py (tests)
```

### 2. Install Dependencies

```bash
pip install mcp pydantic
```

### 3. Verify Installation

```bash
python notification_system_enhanced.py
# Should start the MCP server
```

## Quick Examples

### Initialize the System

```python
from notification_system_enhanced import EnhancedNotificationDB

# Create database connection
db = EnhancedNotificationDB()
```

### Scenario 1: Basic Email Notification

```python
# Step 1: Register a recipient
db.register_recipient(
    recipient_id="user@company.com",
    name="John Doe",
    email="john@company.com"
)

# Step 2: Set preferences (email only)
db.set_notification_preference(
    recipient_id="user@company.com",
    preferred_channels=["email"]
)

# Step 3: Send notification
result = db.send_notification(
    recipient_id="user@company.com",
    channel="email",
    subject="Hello from System",
    body="This is a test notification",
    priority="normal"
)

print(f"Notification sent: {result['notification_id']}")
```

### Scenario 2: Multi-Channel with DND Hours

```python
# Register user
db.register_recipient(
    recipient_id="alice",
    name="Alice",
    email="alice@company.com",
    phone="+1-555-1234"
)

# Set multi-channel preferences with DND
db.set_notification_preference(
    recipient_id="alice",
    preferred_channels=["email", "sms", "push"],
    do_not_disturb_start="18:00",  # 6 PM
    do_not_disturb_end="08:00",    # 8 AM
    max_notifications_per_day=50,
    timezone="US/Eastern"
)

# Send via different channels
for channel in ["email", "sms", "push"]:
    db.send_notification(
        recipient_id="alice",
        channel=channel,
        subject="Multi-channel Test",
        body=f"Message via {channel}",
        priority="normal"
    )
```

### Scenario 3: Critical Alerts with Escalation

```python
# Step 1: Add escalation rules
db.add_escalation_rule(
    priority_threshold="critical",
    max_attempts=1,
    time_between_attempts=60,
    escalation_level="critical",
    escalation_channel="sms",
    escalation_recipient="emergency@company.com"
)

# Step 2: Send critical notification
result = db.send_notification(
    recipient_id="alice",
    channel="email",
    subject="CRITICAL ALERT",
    body="System is down - immediate action required",
    priority="critical"
)

# Step 3: Check and trigger escalation
escalation = db.check_and_escalate(result['notification_id'])
if escalation['escalated']:
    print(f"Escalated {escalation['escalation_count']} times")
```

### Scenario 4: Communication History

```python
# Send some notifications
for i in range(5):
    db.send_notification(
        recipient_id="alice",
        channel="email",
        subject=f"Message {i+1}",
        body="Test message",
        priority="normal"
    )

# Get history
history = db.get_communication_history(
    recipient_id="alice",
    days_back=30
)

print(f"Total communications: {history['total_entries']}")
for entry in history['history']:
    print(f"- {entry['event_type']} via {entry['channel']} at {entry['timestamp']}")
```

### Scenario 5: Single Compliance Report

```python
# Generate GDPR compliance report
report = db.generate_compliance_report(
    framework="gdpr",
    period_days=30,
    signed_by="compliance@company.com"
)

print(f"Report ID: {report['report_id']}")
print(f"Status: {report['report']['compliance_status']}")
print(f"Signed: {report['signed_by']}")

# Summary statistics
summary = report['report']['summary']
print(f"Total notifications: {summary['total_notifications']}")
print(f"Email: {summary['channel_distribution']['email']}")
print(f"SMS: {summary['channel_distribution']['sms']}")
print(f"Push: {summary['channel_distribution']['push']}")
```

### Scenario 6: Multi-Framework Compliance

```python
# Generate reports for all frameworks
frameworks = ["gdpr", "ccpa", "hipaa", "soc2", "iso27001"]

for framework in frameworks:
    report = db.generate_compliance_report(
        framework=framework,
        period_days=30,
        signed_by="compliance@company.com"
    )
    print(f"{framework.upper()}: {report['report_id']}")

# List all GDPR reports
gdpr_reports = db.list_compliance_reports(
    framework="gdpr",
    days_back=90
)

print(f"Total GDPR reports: {gdpr_reports['total_reports']}")
for r in gdpr_reports['reports']:
    print(f"- {r['report_id']} ({r['generated_at']})")
```

## Common Patterns

### Pattern 1: User Onboarding

```python
def onboard_user(user_id, name, email, phone):
    """Onboard a new user with standard preferences."""
    # Register
    db.register_recipient(
        recipient_id=user_id,
        name=name,
        email=email,
        phone=phone
    )
    
    # Set preferences
    db.set_notification_preference(
        recipient_id=user_id,
        preferred_channels=["email", "sms"],
        max_notifications_per_day=100,
        escalation_enabled=True
    )
    
    return True

# Usage
onboard_user("new_user", "Jane Smith", "jane@company.com", "+1-555-5555")
```

### Pattern 2: Urgent Alert Flow

```python
def send_urgent_alert(recipient_id, subject, body):
    """Send urgent alert with automatic escalation."""
    # Send via primary channel
    result = db.send_notification(
        recipient_id=recipient_id,
        channel="email",
        subject=subject,
        body=body,
        priority="critical"
    )
    
    # Immediately check for escalation
    escalation = db.check_and_escalate(result['notification_id'])
    
    return {
        'notification_id': result['notification_id'],
        'escalated': escalation['escalated']
    }

# Usage
send_urgent_alert(
    "alice",
    "Database Down",
    "Primary database is unavailable"
)
```

### Pattern 3: Batch Notifications

```python
def send_batch_notifications(recipients, subject, body, priority="normal"):
    """Send notification to multiple recipients."""
    results = []
    for recipient_id in recipients:
        # Get their preferred channel
        prefs = db.get_notification_preference(recipient_id)
        if not prefs['success']:
            continue
        
        # Send via preferred channel
        channel = prefs['preferences']['preferred_channels'][0]
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
recipients = ["alice", "bob", "charlie"]
send_batch_notifications(
    recipients,
    "System Maintenance",
    "System will be down for maintenance tonight"
)
```

### Pattern 4: Compliance Audit

```python
def generate_compliance_audit(frameworks=None):
    """Generate compliance reports for all frameworks."""
    if not frameworks:
        frameworks = ["gdpr", "ccpa", "hipaa", "soc2", "iso27001"]
    
    audit_reports = {}
    for framework in frameworks:
        report = db.generate_compliance_report(
            framework=framework,
            period_days=30,
            signed_by="audit@company.com"
        )
        audit_reports[framework] = report['report_id']
    
    return audit_reports

# Usage
audit = generate_compliance_audit()
for framework, report_id in audit.items():
    print(f"{framework}: {report_id}")
```

## API Reference (Quick)

### Core Functions

| Function | Purpose | Key Params |
|----------|---------|-----------|
| `register_recipient()` | Add new user | recipient_id, name, email, phone |
| `set_notification_preference()` | Configure preferences | recipient_id, preferred_channels, dnd_start/end |
| `send_notification()` | Send message | recipient_id, channel, subject, body, priority |
| `add_escalation_rule()` | Setup escalation | priority_threshold, escalation_level, channel |
| `check_and_escalate()` | Trigger escalation | notification_id |
| `get_communication_history()` | View history | recipient_id, days_back |
| `generate_compliance_report()` | Create report | framework, period_days, signed_by |

### Channels

- `email` - Email delivery (95% simulated success)
- `sms` - SMS delivery (92% simulated success)
- `push` - Push notifications (98% simulated success)

### Priorities

- `low` - Standard/informational
- `normal` - Regular notifications
- `high` - Important, needs attention
- `critical` - Urgent, time-sensitive

### Frameworks

- `gdpr` - EU data protection
- `ccpa` - California privacy
- `hipaa` - Healthcare data
- `soc2` - System controls
- `iso27001` - Information security

## Troubleshooting

### Issue: "Recipient not configured"

```python
# Solution: Register recipient first
db.register_recipient("user_id", "User Name")
db.set_notification_preference(
    recipient_id="user_id",
    preferred_channels=["email"]
)
```

### Issue: "Channel not in recipient's preferred channels"

```python
# Solution: Add channel to preferences
prefs = db.get_notification_preference("user_id")
current_channels = prefs['preferences']['preferred_channels']
current_channels.append("sms")  # Add SMS
db.set_notification_preference(
    recipient_id="user_id",
    preferred_channels=current_channels
)
```

### Issue: Database not found

```python
# Solution: Check database path
import os
from pathlib import Path
db_path = Path.home() / ".notification_system_enhanced" / "notification_db.sqlite"
print(f"Database location: {db_path}")
print(f"Database exists: {db_path.exists()}")
```

## Next Steps

1. **Run Tests**: `python test_notification_system_enhanced.py`
2. **Review Examples**: `python notification_system_enhanced_client.py`
3. **Read Full Docs**: See `NOTIFICATION_SYSTEM_ENHANCED_README.md`
4. **Integrate with Your App**: Use client classes or direct DB access
5. **Setup Compliance**: Generate initial compliance reports

## File Structure

```
notification_system_enhanced/
├── notification_system_enhanced.py         # Main server
├── notification_system_enhanced_client.py  # Client examples
├── test_notification_system_enhanced.py    # Test suite
├── NOTIFICATION_SYSTEM_ENHANCED_README.md  # Full documentation
└── NOTIFICATION_SYSTEM_ENHANCED_QUICK_START.md  # This file
```

## Performance Baseline

- Register recipient: < 50ms
- Send notification: < 100ms
- Add escalation rule: < 50ms
- Generate compliance report: < 500ms
- Get communication history: < 200ms (30-day window)

## Production Checklist

- [ ] Install dependencies
- [ ] Run test suite
- [ ] Configure database path
- [ ] Setup compliance signing authority
- [ ] Test with real email/SMS (replace simulation)
- [ ] Configure DND enforcement
- [ ] Setup automated escalation scheduler
- [ ] Enable audit logging
- [ ] Configure backup strategy
- [ ] Setup monitoring/alerting

For more details, see the full README.
