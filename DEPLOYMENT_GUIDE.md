# NotificationSystem MCP Server - Production Deployment Guide

## Overview

The NotificationSystem MCP Server is a production-grade compliance and notification management platform providing:
- **Audit Database**: SQLite with full schema for case tracking
- **Case Management**: Unique ID generation with checksums (CASE-YYYYMMDD-RANDOM-CHECKSUM format)
- **Decision Notifications**: Email simulation with retry tracking
- **Compliance Audit Trail**: Regulatory action logging with evidence hashing
- **Summary Reports**: Multi-dimension reporting for compliance verification

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server (stdio)                         │
├─────────────────────────────────────────────────────────────┤
│                   Tool Handlers                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • create_case_record()                               │   │
│  │ • send_decision_notification()                       │   │
│  │ • log_compliance_action()                            │   │
│  │ • generate_summary_report()                          │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 AuditDatabase Manager                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • ID Generation (UUID + Timestamp + Checksum)       │   │
│  │ • Email Simulation Service                          │   │
│  │ • Hash Generation (SHA256, MD5)                     │   │
│  │ • Query & Reporting Engine                          │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│              SQLite Database (4 Tables)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ cases │ notifications │ compliance_actions │ reports │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- MCP SDK: `pip install mcp`
- Standard library modules (sqlite3, json, logging, etc.)

### Setup Steps

1. **Install Dependencies**
```bash
pip install mcp
```

2. **Place Server File**
```bash
cp notification_system_server.py /opt/notification-system/
chmod +x /opt/notification-system/notification_system_server.py
```

3. **Create Data Directory**
```bash
mkdir -p ~/.notification_system
chmod 700 ~/.notification_system
```

4. **Verify Database Initialization**
```bash
python notification_system_server.py
# The database will be created on first run at ~/.notification_system/audit_database.db
```

## Tool Specifications

### 1. create_case_record()

**Purpose**: Create a new case record with unique ID generation

**Input Parameters**:
- `case_type` (string, required): COMPLAINT | INCIDENT | REQUEST
- `subject` (string, required): Case subject line
- `description` (string, optional): Detailed description
- `priority` (string, optional): LOW | MEDIUM | HIGH | CRITICAL (default: MEDIUM)
- `assigned_to` (string, optional): Person/team name

**Output**:
```json
{
  "case_id": "CASE-20240115-A7B2C9D4-F8E2",
  "created_at": "2024-01-15T14:32:05.123456Z",
  "case_type": "COMPLAINT",
  "status": "OPEN",
  "subject": "Data handling concern",
  "priority": "HIGH",
  "success": true,
  "message": "Case record created successfully with ID: CASE-20240115-A7B2C9D4-F8E2"
}
```

**Key Features**:
- Format: CASE-YYYYMMDD-RANDOM-CHECKSUM (16 chars + 4 checksum)
- Automatic deduplication via case_hash (SHA256)
- ISO 8601 timestamps with UTC
- Priority-based tracking

**Example Usage**:
```python
result = audit_db.create_case_record(
    case_type="COMPLAINT",
    subject="Customer data privacy concern",
    description="Customer reported unauthorized data access",
    priority="HIGH",
    assigned_to="legal_team"
)
case_id = result["case_id"]  # Use in subsequent operations
```

---

### 2. send_decision_notification()

**Purpose**: Send decision notifications and maintain delivery log

**Input Parameters**:
- `case_id` (string, required): Valid case ID from create_case_record
- `recipient_email` (string, required): Valid email address
- `notification_type` (string, required): DECISION | UPDATE | RESOLUTION | ESCALATION
- `subject` (string, required): Email subject line
- `body` (string, required): Email body content

**Output**:
```json
{
  "notification_id": "NOTIF-A7B2C9D4F8E2",
  "case_id": "CASE-20240115-A7B2C9D4-F8E2",
  "recipient_email": "john@example.com",
  "notification_type": "DECISION",
  "status": "SENT",
  "created_at": "2024-01-15T14:35:10.654321Z",
  "success": true,
  "message": "Notification delivered to john@example.com"
}
```

**Key Features**:
- Validates case existence before sending
- Email simulation (95% success rate)
- Automatic retry tracking (retry_count field)
- Delivery timestamp logging
- Supports multiple notification types

**Email Simulation**:
- In production, replace `_simulate_email_send()` with actual SMTP/SES integration
- Current implementation validates email format and simulates delivery

**Example Usage**:
```python
result = audit_db.send_decision_notification(
    case_id="CASE-20240115-A7B2C9D4-F8E2",
    recipient_email="customer@example.com",
    notification_type="DECISION",
    subject="Your Case Resolution",
    body="We have reviewed your complaint and made the following decision..."
)
```

---

### 3. log_compliance_action()

**Purpose**: Create regulatory audit trail with evidence hashing

**Input Parameters**:
- `case_id` (string, required): Valid case ID
- `action_type` (string, required): REVIEW | APPROVAL | REJECTION | ESCALATION
- `regulation` (string, required): GDPR | CCPA | SOC2 | HIPAA | etc
- `actor` (string, required): Person/system performing action
- `description` (string, required): Action details
- `evidence_hash` (string, optional): Hash of supporting evidence
- `tags` (string, optional): Comma-separated tags (e.g., "urgent,verified")

**Output**:
```json
{
  "action_id": "COMP-A7B2C9D4F8E2",
  "case_id": "CASE-20240115-A7B2C9D4-F8E2",
  "action_type": "REVIEW",
  "regulation": "GDPR",
  "actor": "compliance_officer_01",
  "evidence_hash": "a7b2c9d4f8e2a1b2",
  "created_at": "2024-01-15T14:37:15.987654Z",
  "success": true,
  "message": "Compliance action logged successfully"
}
```

**Key Features**:
- Automatic evidence hashing (SHA256, 16-char truncated)
- Regulatory tracking with full audit trail
- Actor identification for accountability
- ISO 8601 timestamps
- Tagging support for categorization

**Evidence Hash Generation**:
- Combines: case_id + action_type + actor + timestamp
- SHA256 hash with 16-character truncation
- Ensures data integrity for regulatory verification

**Example Usage**:
```python
result = audit_db.log_compliance_action(
    case_id="CASE-20240115-A7B2C9D4-F8E2",
    action_type="REVIEW",
    regulation="GDPR",
    actor="data_protection_officer",
    description="Conducted Article 5 compliance review - all requirements met",
    tags="urgent,verified,approved"
)
action_id = result["action_id"]
```

---

### 4. generate_summary_report()

**Purpose**: Generate compliance and audit reports

**Input Parameters**:
- `report_type` (string, optional): DAILY | WEEKLY | MONTHLY | QUARTERLY (default: DAILY)
- `days_back` (integer, optional): Number of days to include (default: 7)

**Output**:
```json
{
  "success": true,
  "report": {
    "report_id": "REPORT-A7B2C9D4F8E2",
    "report_type": "DAILY",
    "generated_at": "2024-01-15T15:00:00.000000Z",
    "period_days": 7,
    "summary": {
      "total_cases": 42,
      "high_priority_cases": 5,
      "notifications_sent": 38,
      "compliance_actions_logged": 127,
      "cases_by_status": {
        "OPEN": 12,
        "IN_PROGRESS": 18,
        "RESOLVED": 8,
        "CLOSED": 4
      },
      "cases_by_type": {
        "COMPLAINT": 18,
        "INCIDENT": 15,
        "REQUEST": 9
      },
      "compliance_by_regulation": {
        "GDPR": 52,
        "CCPA": 38,
        "SOC2": 37
      }
    }
  },
  "message": "Report generated successfully with ID: REPORT-A7B2C9D4F8E2"
}
```

**Key Features**:
- Multi-dimensional aggregation
- Status and type breakdown
- Regulatory compliance metrics
- High-priority case tracking
- JSON persistence for archival

**Report Storage**:
- Stored in `summary_reports` table
- Full JSON report data retained
- Sortable by type and date
- Retrievable for historical analysis

**Example Usage**:
```python
result = audit_db.generate_summary_report(
    report_type="WEEKLY",
    days_back=30
)
report_data = result["report"]["summary"]
```

---

## Database Schema

### Tables

#### cases
```sql
CREATE TABLE cases (
    case_id TEXT PRIMARY KEY,           -- CASE-YYYYMMDD-RANDOM-CHECKSUM
    created_at TEXT NOT NULL,           -- ISO 8601 UTC
    updated_at TEXT NOT NULL,           -- ISO 8601 UTC
    case_type TEXT NOT NULL,            -- COMPLAINT, INCIDENT, REQUEST
    status TEXT DEFAULT 'OPEN',         -- OPEN, IN_PROGRESS, RESOLVED, CLOSED
    subject TEXT NOT NULL,              -- Case subject
    description TEXT,                   -- Detailed description
    priority TEXT DEFAULT 'MEDIUM',     -- LOW, MEDIUM, HIGH, CRITICAL
    assigned_to TEXT,                   -- Person/team
    case_hash TEXT UNIQUE NOT NULL      -- SHA256 for deduplication
)
```

#### notifications
```sql
CREATE TABLE notifications (
    notification_id TEXT PRIMARY KEY,   -- NOTIF-XXXXXXXXXX
    case_id TEXT NOT NULL,              -- FK to cases
    created_at TEXT NOT NULL,           -- ISO 8601 UTC
    recipient_email TEXT NOT NULL,      -- Email address
    notification_type TEXT NOT NULL,    -- DECISION, UPDATE, RESOLUTION, ESCALATION
    status TEXT DEFAULT 'SENT',         -- SENT, PENDING, FAILED
    subject TEXT NOT NULL,              -- Email subject
    body TEXT NOT NULL,                 -- Email body
    delivery_timestamp TEXT,            -- When sent
    retry_count INTEGER DEFAULT 0,      -- Number of retries
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
)
```

#### compliance_actions
```sql
CREATE TABLE compliance_actions (
    action_id TEXT PRIMARY KEY,         -- COMP-XXXXXXXXXX
    case_id TEXT NOT NULL,              -- FK to cases
    created_at TEXT NOT NULL,           -- ISO 8601 UTC
    action_type TEXT NOT NULL,          -- REVIEW, APPROVAL, REJECTION, ESCALATION
    regulation TEXT NOT NULL,           -- GDPR, CCPA, SOC2, HIPAA
    actor TEXT NOT NULL,                -- Person/system
    description TEXT NOT NULL,          -- Action details
    evidence_hash TEXT,                 -- SHA256 evidence hash
    status TEXT DEFAULT 'RECORDED',     -- RECORDED, VERIFIED, APPROVED
    tags TEXT,                          -- Comma-separated tags
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
)
```

#### summary_reports
```sql
CREATE TABLE summary_reports (
    report_id TEXT PRIMARY KEY,         -- REPORT-XXXXXXXXXX
    created_at TEXT NOT NULL,           -- ISO 8601 UTC
    report_type TEXT NOT NULL,          -- DAILY, WEEKLY, MONTHLY, QUARTERLY
    total_cases INTEGER,                -- Count
    cases_by_status TEXT,               -- JSON
    compliance_actions_count INTEGER,   -- Count
    notifications_sent INTEGER,         -- Count
    high_priority_cases INTEGER,        -- Count
    report_data TEXT NOT NULL           -- Full JSON report
)
```

### Indexes

- `idx_case_status`: Fast case lookup by status
- `idx_case_created`: Fast date range queries
- `idx_notification_case`: Notification lookups
- `idx_compliance_case`: Compliance lookups
- `idx_compliance_regulation`: Regulation queries

## Production Configuration

### Environment Variables

```bash
# Database path (optional, defaults to ~/.notification_system/audit_database.db)
export NOTIFICATION_DB_PATH=/var/lib/notification-system/audit.db

# Log level (DEBUG, INFO, WARNING, ERROR)
export LOG_LEVEL=INFO

# Email service configuration (for production SMTP)
export SMTP_HOST=mail.example.com
export SMTP_PORT=587
export SMTP_USER=notifications@example.com
export SMTP_PASSWORD=secure_password
```

### Logging Configuration

Default: INFO level to stdout and file
- Log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- File location: Configured in logging setup
- Rotation: Implement with RotatingFileHandler for production

### Security Considerations

1. **Database Access**
   - Store database in restricted directory (700 permissions)
   - Use database encryption at rest in production
   - Regular backups with secure storage

2. **Email Service**
   - Never log email credentials
   - Use environment variables for secrets
   - Implement rate limiting for notifications

3. **Audit Trail**
   - Immutable compliance action logs
   - Digital signatures for critical actions
   - Encrypted evidence storage

4. **Data Retention**
   - Implement retention policies per regulation
   - Archive old records to secure storage
   - Maintain deletion audit logs

## Running the Server

### Via stdio (MCP Standard)

```bash
python notification_system_server.py
```

The server will:
1. Initialize the database at `~/.notification_system/audit_database.db`
2. Start listening on stdin/stdout
3. Accept MCP tool calls from connected clients

### Integration with Claude

Configure in your MCP client:

```json
{
  "mcpServers": {
    "notification-system": {
      "command": "python",
      "args": ["/path/to/notification_system_server.py"]
    }
  }
}
```

## Testing & Validation

### Unit Test Template

```python
import unittest
from notification_system_server import AuditDatabase

class TestNotificationSystem(unittest.TestCase):
    def setUp(self):
        self.db = AuditDatabase(":memory:")  # Use in-memory for tests
    
    def test_create_case_record(self):
        result = self.db.create_case_record(
            case_type="COMPLAINT",
            subject="Test case"
        )
        self.assertTrue(result["success"])
        self.assertIn("CASE-", result["case_id"])
    
    def test_case_id_uniqueness(self):
        ids = set()
        for _ in range(100):
            case_id = self.db.create_case_id()
            self.assertNotIn(case_id, ids)
            ids.add(case_id)
```

### Integration Test Workflow

1. Create case record
2. Verify case exists in database
3. Send notification for that case
4. Log compliance action for case
5. Generate report including that case
6. Verify all data persisted correctly

## Monitoring & Maintenance

### Key Metrics to Monitor

- **Case Volume**: Total cases by type/priority
- **Notification Delivery**: Success/failure rates
- **Compliance Actions**: Logged per regulation
- **Database Size**: Growth over time
- **Query Performance**: Index effectiveness

### Maintenance Tasks

- Daily: Monitor case backlogs and high-priority cases
- Weekly: Generate compliance reports
- Monthly: Archive old records, verify backups
- Quarterly: Audit trail review, access control audit

## Troubleshooting

### Issue: Database Lock Errors

**Solution**: Ensure only one server instance running; implement connection pooling for concurrent access.

### Issue: Email Notifications Not Sending

**Solution**: 
1. Verify recipient email format is valid
2. Check SMTP credentials in production
3. Review retry_count in notifications table

### Issue: Slow Report Generation

**Solution**:
1. Verify indexes are created
2. Archive old records to separate database
3. Consider partitioning compliance_actions table

## Migration & Upgrades

### Schema Migration Example

```python
# Add new column to cases table
cursor.execute('ALTER TABLE cases ADD COLUMN resolved_at TEXT')
conn.commit()
```

### Backup & Recovery

```bash
# Backup
sqlite3 ~/.notification_system/audit_database.db ".backup backup.db"

# Restore
sqlite3 ~/.notification_system/audit_database.db ".restore backup.db"
```

## Compliance Framework

Supports regulatory frameworks:
- **GDPR**: Data protection, audit trails
- **CCPA**: Privacy rights, notification logs
- **SOC2**: Compliance tracking, evidence
- **HIPAA**: Protected health information audit
- **Custom**: Extensible regulation field

## Support & Documentation

- Schema: See Database Schema section above
- Tools: See Tool Specifications section above
- Examples: See notification_client_example.py
- Logs: Review application logs for diagnostic info
