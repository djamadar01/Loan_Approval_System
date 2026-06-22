"""NotificationSystem MCP Server using FastMCP.

Provides comprehensive notification functionality with:
- send_notification tool for sending notifications
- Automatic Case ID generation
- Timestamp recording
- Comprehensive audit trail logging
- Summary generation
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp.server.server import FastMCP
from pydantic import BaseModel, Field


# ============================================================================
# Configuration and Setup
# ============================================================================

class Config:
    """Configuration for the notification system."""

    AUDIT_LOG_DIR = Path("./audit_logs")
    NOTIFICATION_LOG_FILE = AUDIT_LOG_DIR / "notifications.jsonl"
    CASE_ID_LOG_FILE = AUDIT_LOG_DIR / "case_ids.json"

    @staticmethod
    def ensure_dirs():
        """Ensure required directories exist."""
        Config.AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Data Models
# ============================================================================

class NotificationRequest(BaseModel):
    """Model for notification request."""

    recipient: str = Field(..., description="Recipient email or identifier")
    subject: str = Field(..., description="Notification subject/title")
    message: str = Field(..., description="Notification message content")
    notification_type: str = Field(
        default="general",
        description="Type of notification (general, alert, warning, urgent)"
    )
    priority: str = Field(
        default="normal",
        description="Priority level (low, normal, high, critical)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the notification"
    )


class NotificationResponse(BaseModel):
    """Model for notification response."""

    case_id: str = Field(..., description="Unique case ID for this notification")
    timestamp: str = Field(..., description="ISO 8601 timestamp of notification")
    status: str = Field(..., description="Status of notification (sent, pending, failed)")
    recipient: str = Field(..., description="Recipient of the notification")
    summary: str = Field(..., description="Summary of the action taken")
    message_id: Optional[str] = Field(
        default=None,
        description="Message ID for tracking"
    )


class AuditEntry(BaseModel):
    """Model for audit log entry."""

    timestamp: str = Field(..., description="ISO 8601 timestamp")
    case_id: str = Field(..., description="Associated case ID")
    action: str = Field(..., description="Action performed")
    actor: str = Field(default="system", description="Actor performing the action")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action details")
    result: str = Field(default="success", description="Result (success, failure, pending)")


# ============================================================================
# Logging Setup
# ============================================================================

def setup_audit_logging():
    """Set up audit logging infrastructure."""
    Config.ensure_dirs()

    # Create a logger for audit trail
    audit_logger = logging.getLogger("audit_trail")
    audit_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    audit_logger.handlers = []

    # Create file handler for audit log
    audit_handler = logging.FileHandler(
        Config.AUDIT_LOG_DIR / "audit_trail.log"
    )
    audit_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    audit_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    audit_logger.addHandler(audit_handler)
    audit_logger.addHandler(console_handler)

    return audit_logger


audit_logger = setup_audit_logging()


# ============================================================================
# Case ID Management
# ============================================================================

class CaseIDManager:
    """Manages Case ID generation and tracking."""

    def __init__(self, log_file: Path = Config.CASE_ID_LOG_FILE):
        """Initialize Case ID Manager."""
        self.log_file = log_file
        self.case_ids: Dict[str, Dict[str, Any]] = self._load_case_ids()

    def _load_case_ids(self) -> Dict[str, Dict[str, Any]]:
        """Load existing case IDs from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_case_ids(self) -> None:
        """Save case IDs to file."""
        Config.ensure_dirs()
        with open(self.log_file, "w") as f:
            json.dump(self.case_ids, f, indent=2, default=str)

    def generate_case_id(self) -> str:
        """Generate a new Case ID.

        Format: NOTIF-YYYY-MM-DD-XXXXX where XXXXX is a random component.

        Returns:
            str: Generated Case ID
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y%m%d")
        random_component = str(uuid.uuid4().hex[:6]).upper()
        case_id = f"NOTIF-{date_str}-{random_component}"

        return case_id

    def register_case_id(
        self,
        case_id: str,
        recipient: str,
        subject: str,
        notification_type: str
    ) -> None:
        """Register a new Case ID.

        Args:
            case_id: The case ID
            recipient: Recipient of the notification
            subject: Subject of the notification
            notification_type: Type of notification
        """
        self.case_ids[case_id] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recipient": recipient,
            "subject": subject,
            "notification_type": notification_type,
        }
        self._save_case_ids()

        audit_logger.info(
            f"Case ID registered: {case_id} for recipient: {recipient}"
        )

    def get_case_info(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a case.

        Args:
            case_id: The case ID

        Returns:
            Case information or None
        """
        return self.case_ids.get(case_id)

    def list_case_ids(self) -> Dict[str, Dict[str, Any]]:
        """List all case IDs.

        Returns:
            Dictionary of all case IDs and their info
        """
        return self.case_ids.copy()


# ============================================================================
# Audit Trail Management
# ============================================================================

class AuditTrailManager:
    """Manages audit trail logging for notifications."""

    def __init__(self, log_file: Path = Config.NOTIFICATION_LOG_FILE):
        """Initialize Audit Trail Manager."""
        self.log_file = log_file

    def log_action(
        self,
        case_id: str,
        action: str,
        details: Dict[str, Any],
        actor: str = "system",
        result: str = "success"
    ) -> None:
        """Log an action to the audit trail.

        Args:
            case_id: Associated case ID
            action: Action performed
            details: Details about the action
            actor: Actor performing the action
            result: Result of the action (success, failure, pending)
        """
        Config.ensure_dirs()

        timestamp = datetime.now(timezone.utc).isoformat()
        audit_entry = AuditEntry(
            timestamp=timestamp,
            case_id=case_id,
            action=action,
            actor=actor,
            details=details,
            result=result
        )

        # Write to JSONL file
        with open(self.log_file, "a") as f:
            f.write(audit_entry.model_dump_json() + "\n")

        audit_logger.info(
            f"Audit logged - Case: {case_id}, Action: {action}, Result: {result}"
        )

    def get_audit_trail(self, case_id: str) -> list[Dict[str, Any]]:
        """Get audit trail for a specific case.

        Args:
            case_id: The case ID

        Returns:
            List of audit entries for the case
        """
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("case_id") == case_id:
                        entries.append(entry)

        return entries

    def get_all_audit_entries(self) -> list[Dict[str, Any]]:
        """Get all audit entries.

        Returns:
            List of all audit entries
        """
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries


# ============================================================================
# Notification Service
# ============================================================================

class NotificationService:
    """Main notification service."""

    def __init__(self):
        """Initialize the notification service."""
        self.case_id_manager = CaseIDManager()
        self.audit_trail_manager = AuditTrailManager()
        self.message_id_counter = 0

    def send_notification(
        self,
        recipient: str,
        subject: str,
        message: str,
        notification_type: str = "general",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationResponse:
        """Send a notification and log all actions.

        Args:
            recipient: Recipient identifier
            subject: Notification subject
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            metadata: Additional metadata

        Returns:
            NotificationResponse with case ID and summary
        """
        # Generate Case ID
        case_id = self.case_id_manager.generate_case_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        message_id = self._generate_message_id()

        audit_logger.info(
            f"Processing notification - Case ID: {case_id}, "
            f"Recipient: {recipient}, Type: {notification_type}"
        )

        # Log action taken
        self.audit_trail_manager.log_action(
            case_id=case_id,
            action="notification_initiated",
            details={
                "recipient": recipient,
                "subject": subject,
                "notification_type": notification_type,
                "priority": priority,
            },
            actor="notification_service",
            result="pending"
        )

        # Register the case ID
        self.case_id_manager.register_case_id(
            case_id=case_id,
            recipient=recipient,
            subject=subject,
            notification_type=notification_type
        )

        # Simulate notification sending (in production, would integrate with real service)
        status = "sent"
        send_details = {
            "recipient": recipient,
            "subject": subject,
            "message_id": message_id,
            "message_length": len(message),
            "metadata": metadata or {},
        }

        self.audit_trail_manager.log_action(
            case_id=case_id,
            action="notification_sent",
            details=send_details,
            actor="notification_service",
            result="success"
        )

        # Generate summary
        summary = self._generate_summary(
            case_id=case_id,
            recipient=recipient,
            subject=subject,
            message_id=message_id,
            timestamp=timestamp
        )

        audit_logger.info(f"Notification sent successfully - Case ID: {case_id}")

        return NotificationResponse(
            case_id=case_id,
            timestamp=timestamp,
            status=status,
            recipient=recipient,
            summary=summary,
            message_id=message_id
        )

    def _generate_message_id(self) -> str:
        """Generate a unique message ID.

        Returns:
            Message ID
        """
        self.message_id_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"MSG-{timestamp}-{self.message_id_counter:06d}"

    def _generate_summary(
        self,
        case_id: str,
        recipient: str,
        subject: str,
        message_id: str,
        timestamp: str
    ) -> str:
        """Generate a summary of the notification action.

        Args:
            case_id: Case ID
            recipient: Recipient
            subject: Subject
            message_id: Message ID
            timestamp: Timestamp

        Returns:
            Summary string
        """
        return (
            f"Notification successfully sent with Case ID {case_id}. "
            f"Recipient: {recipient}, Subject: {subject}, "
            f"Message ID: {message_id}, Timestamp: {timestamp}. "
            f"Full audit trail available for case review."
        )

    def get_notification_status(self, case_id: str) -> Dict[str, Any]:
        """Get the status of a notification by case ID.

        Args:
            case_id: The case ID

        Returns:
            Status information
        """
        case_info = self.case_id_manager.get_case_info(case_id)
        audit_trail = self.audit_trail_manager.get_audit_trail(case_id)

        if not case_info:
            return {"status": "not_found", "case_id": case_id}

        return {
            "case_id": case_id,
            "case_info": case_info,
            "audit_trail": audit_trail,
            "total_actions": len(audit_trail),
        }


# ============================================================================
# FastMCP Server Setup
# ============================================================================

# Initialize FastMCP server
server = FastMCP("NotificationSystem")

# Initialize notification service
notification_service = NotificationService()


@server.tool()
def send_notification(
    recipient: str,
    subject: str,
    message: str,
    notification_type: str = "general",
    priority: str = "normal",
    metadata: Optional[str] = None
) -> str:
    """Send a notification with audit trail logging.

    Args:
        recipient: Recipient email or identifier
        subject: Notification subject
        message: Notification message content
        notification_type: Type of notification (general, alert, warning, urgent)
        priority: Priority level (low, normal, high, critical)
        metadata: JSON string of additional metadata

    Returns:
        JSON string with notification response including Case ID and summary
    """
    try:
        # Parse metadata if provided
        metadata_dict = None
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                audit_logger.warning(
                    f"Invalid JSON metadata provided: {metadata}"
                )
                metadata_dict = {"raw_metadata": metadata}

        # Send notification
        response = notification_service.send_notification(
            recipient=recipient,
            subject=subject,
            message=message,
            notification_type=notification_type,
            priority=priority,
            metadata=metadata_dict
        )

        return response.model_dump_json(indent=2)

    except Exception as e:
        audit_logger.error(
            f"Error sending notification to {recipient}: {str(e)}"
        )
        return json.dumps({
            "status": "error",
            "error": str(e),
            "recipient": recipient
        }, indent=2)


@server.tool()
def get_notification_status(case_id: str) -> str:
    """Get the status and audit trail of a notification.

    Args:
        case_id: The Case ID to retrieve

    Returns:
        JSON string with status and audit trail
    """
    try:
        status = notification_service.get_notification_status(case_id)
        return json.dumps(status, indent=2, default=str)

    except Exception as e:
        audit_logger.error(f"Error retrieving status for case {case_id}: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "case_id": case_id
        }, indent=2)


@server.tool()
def list_all_notifications() -> str:
    """List all Case IDs and their information.

    Returns:
        JSON string with all case IDs
    """
    try:
        case_ids = notification_service.case_id_manager.list_case_ids()
        return json.dumps({
            "total_cases": len(case_ids),
            "case_ids": case_ids
        }, indent=2, default=str)

    except Exception as e:
        audit_logger.error(f"Error listing notifications: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


@server.tool()
def get_audit_trail(case_id: Optional[str] = None) -> str:
    """Get audit trail for a specific case or all entries.

    Args:
        case_id: Optional case ID to filter by

    Returns:
        JSON string with audit trail entries
    """
    try:
        if case_id:
            entries = notification_service.audit_trail_manager.get_audit_trail(case_id)
            return json.dumps({
                "case_id": case_id,
                "entries": entries,
                "total_entries": len(entries)
            }, indent=2, default=str)
        else:
            entries = notification_service.audit_trail_manager.get_all_audit_entries()
            return json.dumps({
                "total_entries": len(entries),
                "entries": entries
            }, indent=2, default=str)

    except Exception as e:
        audit_logger.error(f"Error retrieving audit trail: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


@server.tool()
def get_system_info() -> str:
    """Get system information and statistics.

    Returns:
        JSON string with system stats
    """
    try:
        case_ids = notification_service.case_id_manager.list_case_ids()
        audit_entries = notification_service.audit_trail_manager.get_all_audit_entries()

        return json.dumps({
            "system": "NotificationSystem",
            "status": "operational",
            "statistics": {
                "total_notifications": len(case_ids),
                "total_audit_entries": len(audit_entries),
                "audit_log_file": str(Config.NOTIFICATION_LOG_FILE),
                "case_id_log_file": str(Config.CASE_ID_LOG_FILE),
            }
        }, indent=2, default=str)

    except Exception as e:
        audit_logger.error(f"Error getting system info: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("Starting NotificationSystem MCP Server...")
    print(f"Audit logs directory: {Config.AUDIT_LOG_DIR}")
    print(f"Notification log file: {Config.NOTIFICATION_LOG_FILE}")

    print("NotificationSystem MCP Server is ready...")
    print("Available tools:")
    print("  - send_notification: Send a notification with audit trail")
    print("  - get_notification_status: Get status of a notification")
    print("  - list_all_notifications: List all Case IDs")
    print("  - get_audit_trail: Get audit trail entries")
    print("  - get_system_info: Get system statistics")

    # Run the server with uvicorn via FastMCP
    server.run()
