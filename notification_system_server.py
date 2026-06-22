#!/usr/bin/env python3
"""
Production NotificationSystem MCP Server
Implements audit database for case tracking and compliance management.
"""

import json
import sqlite3
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any
from pathlib import Path
import mcp.server.stdio
from mcp.server import Server, Request
from mcp.types import Tool, TextContent, ToolResponse


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = Path.home() / ".notification_system" / "audit_database.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class AuditDatabase:
    """Production-grade audit database for case tracking and compliance."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema with audit tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Cases table - Primary case tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    case_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    subject TEXT NOT NULL,
                    description TEXT,
                    priority TEXT DEFAULT 'MEDIUM',
                    assigned_to TEXT,
                    case_hash TEXT NOT NULL UNIQUE
                )
            ''')

            # Notifications table - Decision notification log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    recipient_email TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'SENT',
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    delivery_timestamp TEXT,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (case_id) REFERENCES cases(case_id)
                )
            ''')

            # Compliance audit trail
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_actions (
                    action_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    regulation TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    description TEXT NOT NULL,
                    evidence_hash TEXT,
                    status TEXT NOT NULL DEFAULT 'RECORDED',
                    tags TEXT,
                    FOREIGN KEY (case_id) REFERENCES cases(case_id)
                )
            ''')

            # Summary reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summary_reports (
                    report_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    total_cases INTEGER,
                    cases_by_status TEXT,
                    compliance_actions_count INTEGER,
                    notifications_sent INTEGER,
                    high_priority_cases INTEGER,
                    report_data TEXT NOT NULL
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_case_status ON cases(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_case_created ON cases(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_case ON notifications(case_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_compliance_case ON compliance_actions(case_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_compliance_regulation ON compliance_actions(regulation)')

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def create_case_id(self) -> str:
        """Generate a unique, production-grade Case ID."""
        # Format: CASE-YYYYMMDD-RANDOM-CHECKSUM
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = str(uuid.uuid4())[:8].upper()
        unique_str = f"{timestamp}-{random_part}"
        checksum = hashlib.md5(unique_str.encode()).hexdigest()[:4].upper()
        return f"CASE-{timestamp}-{random_part}-{checksum}"

    def generate_case_hash(self, case_id: str, subject: str, case_type: str) -> str:
        """Generate a hash to prevent duplicate case creation."""
        content = f"{case_id}:{subject}:{case_type}"
        return hashlib.sha256(content.encode()).hexdigest()

    def create_case_record(
        self,
        case_type: str,
        subject: str,
        description: str = "",
        priority: str = "MEDIUM",
        assigned_to: str = None
    ) -> dict:
        """Create a new case record in the audit database."""
        case_id = self.create_case_id()
        now = datetime.utcnow().isoformat() + "Z"
        case_hash = self.generate_case_hash(case_id, subject, case_type)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cases
                    (case_id, created_at, updated_at, case_type, status, subject, description, priority, assigned_to, case_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (case_id, now, now, case_type, 'OPEN', subject, description, priority, assigned_to, case_hash))
                conn.commit()

                logger.info(f"Case created: {case_id} (Type: {case_type}, Priority: {priority})")

                return {
                    "case_id": case_id,
                    "created_at": now,
                    "case_type": case_type,
                    "status": "OPEN",
                    "subject": subject,
                    "priority": priority,
                    "success": True,
                    "message": f"Case record created successfully with ID: {case_id}"
                }
        except sqlite3.IntegrityError as e:
            logger.error(f"Duplicate case hash detected: {e}")
            return {
                "success": False,
                "error": "Duplicate case detected",
                "message": "A similar case already exists in the system"
            }
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create case record"
            }

    def send_decision_notification(
        self,
        case_id: str,
        recipient_email: str,
        notification_type: str,
        subject: str,
        body: str
    ) -> dict:
        """Send a decision notification and log it (email simulation)."""
        notification_id = f"NOTIF-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow().isoformat() + "Z"

        try:
            # Verify case exists
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT case_id FROM cases WHERE case_id = ?', (case_id,))
                if not cursor.fetchone():
                    return {
                        "success": False,
                        "error": "Case not found",
                        "message": f"No case found with ID: {case_id}"
                    }

            # Simulate email sending (production would use actual email service)
            email_sent = self._simulate_email_send(recipient_email, subject, body)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notifications
                    (notification_id, case_id, created_at, recipient_email, notification_type, status, subject, body, delivery_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification_id, case_id, now, recipient_email,
                    notification_type, 'SENT' if email_sent else 'PENDING',
                    subject, body, now if email_sent else None
                ))
                conn.commit()

                logger.info(f"Notification sent for case {case_id}: {notification_id}")

                return {
                    "notification_id": notification_id,
                    "case_id": case_id,
                    "recipient_email": recipient_email,
                    "notification_type": notification_type,
                    "status": "SENT" if email_sent else "PENDING",
                    "created_at": now,
                    "success": True,
                    "message": f"Notification delivered to {recipient_email}"
                }
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send notification"
            }

    def _simulate_email_send(self, recipient: str, subject: str, body: str) -> bool:
        """Simulate email sending (replace with actual email service in production)."""
        # Validate email format
        if "@" not in recipient or "." not in recipient:
            return False
        # Simulate 95% success rate
        import random
        return random.random() < 0.95

    def log_compliance_action(
        self,
        case_id: str,
        action_type: str,
        regulation: str,
        actor: str,
        description: str,
        evidence_hash: str = None,
        tags: str = None
    ) -> dict:
        """Log a compliance action for regulatory audit trail."""
        action_id = f"COMP-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow().isoformat() + "Z"

        try:
            # Verify case exists
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT case_id FROM cases WHERE case_id = ?', (case_id,))
                if not cursor.fetchone():
                    return {
                        "success": False,
                        "error": "Case not found",
                        "message": f"No case found with ID: {case_id}"
                    }

            # Generate evidence hash if not provided
            if not evidence_hash:
                content = f"{case_id}:{action_type}:{actor}:{now}"
                evidence_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO compliance_actions
                    (action_id, case_id, created_at, action_type, regulation, actor, description, evidence_hash, status, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action_id, case_id, now, action_type, regulation, actor,
                    description, evidence_hash, 'RECORDED', tags
                ))
                conn.commit()

                logger.info(f"Compliance action recorded: {action_id} (Regulation: {regulation})")

                return {
                    "action_id": action_id,
                    "case_id": case_id,
                    "action_type": action_type,
                    "regulation": regulation,
                    "actor": actor,
                    "evidence_hash": evidence_hash,
                    "created_at": now,
                    "success": True,
                    "message": f"Compliance action logged successfully"
                }
        except Exception as e:
            logger.error(f"Error logging compliance action: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to log compliance action"
            }

    def generate_summary_report(
        self,
        report_type: str = "DAILY",
        days_back: int = 7
    ) -> dict:
        """Generate a comprehensive summary report for audit and compliance."""
        report_id = f"REPORT-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow().isoformat() + "Z"
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get cases data
                cursor.execute('''
                    SELECT status, COUNT(*) as count FROM cases
                    WHERE created_at >= ?
                    GROUP BY status
                ''', (cutoff_date,))
                cases_by_status = {row['status']: row['count'] for row in cursor.fetchall()}

                cursor.execute('''
                    SELECT COUNT(*) as total FROM cases
                    WHERE created_at >= ?
                ''', (cutoff_date,))
                total_cases = cursor.fetchone()['total']

                cursor.execute('''
                    SELECT COUNT(*) as count FROM cases
                    WHERE created_at >= ? AND priority = 'HIGH'
                ''', (cutoff_date,))
                high_priority_cases = cursor.fetchone()['count']

                # Get notification stats
                cursor.execute('''
                    SELECT COUNT(*) as count FROM notifications
                    WHERE created_at >= ? AND status = 'SENT'
                ''', (cutoff_date,))
                notifications_sent = cursor.fetchone()['count']

                # Get compliance stats
                cursor.execute('''
                    SELECT COUNT(*) as count FROM compliance_actions
                    WHERE created_at >= ?
                ''', (cutoff_date,))
                compliance_actions_count = cursor.fetchone()['count']

                # Get compliance by regulation
                cursor.execute('''
                    SELECT regulation, COUNT(*) as count FROM compliance_actions
                    WHERE created_at >= ?
                    GROUP BY regulation
                ''', (cutoff_date,))
                compliance_by_regulation = {row['regulation']: row['count'] for row in cursor.fetchall()}

                # Get top case types
                cursor.execute('''
                    SELECT case_type, COUNT(*) as count FROM cases
                    WHERE created_at >= ?
                    GROUP BY case_type
                    ORDER BY count DESC
                    LIMIT 5
                ''', (cutoff_date,))
                top_case_types = {row['case_type']: row['count'] for row in cursor.fetchall()}

                report_data = {
                    "report_id": report_id,
                    "report_type": report_type,
                    "generated_at": now,
                    "period_days": days_back,
                    "summary": {
                        "total_cases": total_cases,
                        "high_priority_cases": high_priority_cases,
                        "notifications_sent": notifications_sent,
                        "compliance_actions_logged": compliance_actions_count,
                        "cases_by_status": cases_by_status,
                        "cases_by_type": top_case_types,
                        "compliance_by_regulation": compliance_by_regulation
                    }
                }

                # Store report
                cursor.execute('''
                    INSERT INTO summary_reports
                    (report_id, created_at, report_type, total_cases, cases_by_status,
                     compliance_actions_count, notifications_sent, high_priority_cases, report_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_id, now, report_type, total_cases,
                    json.dumps(cases_by_status),
                    compliance_actions_count, notifications_sent, high_priority_cases,
                    json.dumps(report_data)
                ))
                conn.commit()

                logger.info(f"Summary report generated: {report_id}")

                return {
                    "success": True,
                    "report": report_data,
                    "message": f"Report generated successfully with ID: {report_id}"
                }
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate report"
            }


# Initialize database
audit_db = AuditDatabase()

# Create MCP server
server = Server("notification-system-server")


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> Any:
    """Handle tool calls from MCP clients."""

    if name == "create_case_record":
        result = audit_db.create_case_record(
            case_type=arguments.get("case_type"),
            subject=arguments.get("subject"),
            description=arguments.get("description", ""),
            priority=arguments.get("priority", "MEDIUM"),
            assigned_to=arguments.get("assigned_to")
        )
        return ToolResponse(content=[TextContent(type="text", text=json.dumps(result, indent=2))])

    elif name == "send_decision_notification":
        result = audit_db.send_decision_notification(
            case_id=arguments.get("case_id"),
            recipient_email=arguments.get("recipient_email"),
            notification_type=arguments.get("notification_type"),
            subject=arguments.get("subject"),
            body=arguments.get("body")
        )
        return ToolResponse(content=[TextContent(type="text", text=json.dumps(result, indent=2))])

    elif name == "log_compliance_action":
        result = audit_db.log_compliance_action(
            case_id=arguments.get("case_id"),
            action_type=arguments.get("action_type"),
            regulation=arguments.get("regulation"),
            actor=arguments.get("actor"),
            description=arguments.get("description"),
            evidence_hash=arguments.get("evidence_hash"),
            tags=arguments.get("tags")
        )
        return ToolResponse(content=[TextContent(type="text", text=json.dumps(result, indent=2))])

    elif name == "generate_summary_report":
        result = audit_db.generate_summary_report(
            report_type=arguments.get("report_type", "DAILY"),
            days_back=arguments.get("days_back", 7)
        )
        return ToolResponse(content=[TextContent(type="text", text=json.dumps(result, indent=2))])

    else:
        return ToolResponse(
            content=[TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
        )


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return list of available tools."""
    return [
        Tool(
            name="create_case_record",
            description="Create a new case record in the audit database with unique Case ID generation",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_type": {
                        "type": "string",
                        "description": "Type of case (e.g., COMPLAINT, INCIDENT, REQUEST)"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Case subject line"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed case description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        "description": "Case priority level (default: MEDIUM)"
                    },
                    "assigned_to": {
                        "type": "string",
                        "description": "Person/team assigned to handle the case"
                    }
                },
                "required": ["case_type", "subject"]
            }
        ),
        Tool(
            name="send_decision_notification",
            description="Send a decision notification via email (simulated) and log it to the case",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "The case ID to send notification for"
                    },
                    "recipient_email": {
                        "type": "string",
                        "description": "Email address of the recipient"
                    },
                    "notification_type": {
                        "type": "string",
                        "enum": ["DECISION", "UPDATE", "RESOLUTION", "ESCALATION"],
                        "description": "Type of notification"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    }
                },
                "required": ["case_id", "recipient_email", "notification_type", "subject", "body"]
            }
        ),
        Tool(
            name="log_compliance_action",
            description="Log a compliance action for regulatory audit trail with automatic evidence hashing",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "description": "The case ID this compliance action relates to"
                    },
                    "action_type": {
                        "type": "string",
                        "description": "Type of compliance action (e.g., REVIEW, APPROVAL, REJECTION)"
                    },
                    "regulation": {
                        "type": "string",
                        "description": "Applicable regulation (e.g., GDPR, CCPA, SOC2)"
                    },
                    "actor": {
                        "type": "string",
                        "description": "Person or system performing the action"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the compliance action"
                    },
                    "evidence_hash": {
                        "type": "string",
                        "description": "Optional hash of supporting evidence"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags for categorization"
                    }
                },
                "required": ["case_id", "action_type", "regulation", "actor", "description"]
            }
        ),
        Tool(
            name="generate_summary_report",
            description="Generate a comprehensive summary report for audit and compliance with statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"],
                        "description": "Type of report to generate (default: DAILY)"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to include in report (default: 7)"
                    }
                }
            }
        )
    ]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, logger)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
