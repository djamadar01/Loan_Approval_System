"""Client example for NotificationSystem MCP Server.

Demonstrates how to use the NotificationSystem MCP server to:
- Send notifications
- Query notification status
- Retrieve audit trails
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


class NotificationSystemClient:
    """Client for interacting with NotificationSystem MCP Server."""

    def __init__(self, server_url: str = "http://localhost:3000"):
        """Initialize the client.

        Args:
            server_url: Base URL of the MCP server
        """
        self.server_url = server_url
        self.client = httpx.Client(timeout=30.0)

    def send_notification(
        self,
        recipient: str,
        subject: str,
        message: str,
        notification_type: str = "general",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a notification.

        Args:
            recipient: Recipient email or identifier
            subject: Notification subject
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            metadata: Additional metadata

        Returns:
            Response with Case ID and summary
        """
        payload = {
            "recipient": recipient,
            "subject": subject,
            "message": message,
            "notification_type": notification_type,
            "priority": priority,
        }

        if metadata:
            payload["metadata"] = json.dumps(metadata)

        response = self.client.post(
            f"{self.server_url}/tools/send_notification",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_notification_status(self, case_id: str) -> Dict[str, Any]:
        """Get the status of a notification.

        Args:
            case_id: The Case ID

        Returns:
            Status information including audit trail
        """
        response = self.client.get(
            f"{self.server_url}/tools/get_notification_status",
            params={"case_id": case_id}
        )
        response.raise_for_status()
        return response.json()

    def list_all_notifications(self) -> Dict[str, Any]:
        """List all notifications.

        Returns:
            List of all Case IDs
        """
        response = self.client.get(
            f"{self.server_url}/tools/list_all_notifications"
        )
        response.raise_for_status()
        return response.json()

    def get_audit_trail(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Get audit trail.

        Args:
            case_id: Optional case ID to filter

        Returns:
            Audit trail entries
        """
        params = {}
        if case_id:
            params["case_id"] = case_id

        response = self.client.get(
            f"{self.server_url}/tools/get_audit_trail",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information.

        Returns:
            System statistics and info
        """
        response = self.client.get(
            f"{self.server_url}/tools/get_system_info"
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the client."""
        self.client.close()


# ============================================================================
# Direct Usage Examples (without server)
# ============================================================================

def demo_direct_usage():
    """Demonstrate direct usage of NotificationSystem without MCP server.

    This imports the notification service directly for testing.
    """
    print("=" * 80)
    print("NotificationSystem - Direct Usage Demo")
    print("=" * 80)

    from notification_system_mcp import NotificationService

    # Initialize service
    service = NotificationService()

    # Example 1: Send a general notification
    print("\n[1] Sending general notification...")
    response1 = service.send_notification(
        recipient="alice@example.com",
        subject="Account Update",
        message="Your account has been successfully updated.",
        notification_type="general",
        priority="normal"
    )
    print(f"Response:\n{json.dumps(response1.model_dump(), indent=2, default=str)}")
    case_id_1 = response1.case_id

    # Example 2: Send an alert notification
    print("\n[2] Sending alert notification...")
    response2 = service.send_notification(
        recipient="bob@example.com",
        subject="Suspicious Activity Detected",
        message="Unusual login activity detected on your account.",
        notification_type="alert",
        priority="high",
        metadata={"activity_id": "ACT-123456", "ip_address": "192.168.1.1"}
    )
    print(f"Response:\n{json.dumps(response2.model_dump(), indent=2, default=str)}")
    case_id_2 = response2.case_id

    # Example 3: Send an urgent notification
    print("\n[3] Sending urgent notification...")
    response3 = service.send_notification(
        recipient="charlie@example.com",
        subject="System Maintenance - Action Required",
        message="Critical system maintenance scheduled. Please take action immediately.",
        notification_type="urgent",
        priority="critical",
        metadata={"maintenance_id": "MAINT-789", "window": "2-4 AM EST"}
    )
    print(f"Response:\n{json.dumps(response3.model_dump(), indent=2, default=str)}")
    case_id_3 = response3.case_id

    # Example 4: Check notification status
    print(f"\n[4] Checking status for Case ID: {case_id_1}...")
    status = service.get_notification_status(case_id_1)
    print(f"Status:\n{json.dumps(status, indent=2, default=str)}")

    # Example 5: List all Case IDs
    print("\n[5] Listing all notifications...")
    all_cases = service.case_id_manager.list_case_ids()
    print(f"Total notifications: {len(all_cases)}")
    for cid, info in all_cases.items():
        print(f"  - {cid}: {info['subject']} -> {info['recipient']}")

    # Example 6: Get full audit trail for a case
    print(f"\n[6] Getting audit trail for Case ID: {case_id_2}...")
    audit_trail = service.audit_trail_manager.get_audit_trail(case_id_2)
    print(f"Total audit entries: {len(audit_trail)}")
    for entry in audit_trail:
        print(f"  - {entry['timestamp']}: {entry['action']} ({entry['result']})")

    # Example 7: Get all audit entries
    print("\n[7] Getting all audit entries...")
    all_entries = service.audit_trail_manager.get_all_audit_entries()
    print(f"Total audit entries across all cases: {len(all_entries)}")

    # Example 8: Check audit log files
    print("\n[8] Audit log files location:")
    print(f"  - Audit trail log: {Path('audit_logs/audit_trail.log').resolve()}")
    print(f"  - Notifications JSONL: {Path('audit_logs/notifications.jsonl').resolve()}")
    print(f"  - Case IDs JSON: {Path('audit_logs/case_ids.json').resolve()}")

    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


async def demo_server_usage():
    """Demonstrate usage via MCP server.

    Note: Requires running the MCP server first.
    """
    print("=" * 80)
    print("NotificationSystem - Server Usage Demo")
    print("=" * 80)

    try:
        client = NotificationSystemClient()

        # Example 1: Send notification
        print("\n[1] Sending notification via server...")
        response = client.send_notification(
            recipient="user@example.com",
            subject="Test Notification",
            message="This is a test notification sent via MCP server.",
            notification_type="general",
            priority="normal",
            metadata={"test_id": "TEST-001"}
        )
        print(f"Response:\n{json.dumps(response, indent=2)}")

        # Extract Case ID
        try:
            result = json.loads(response)
            case_id = result.get("case_id")

            if case_id:
                # Example 2: Get status
                print(f"\n[2] Getting status for Case ID: {case_id}...")
                status = client.get_notification_status(case_id)
                print(f"Status:\n{json.dumps(status, indent=2)}")

        except (json.JSONDecodeError, KeyError):
            print("Could not extract Case ID from response")

        # Example 3: Get system info
        print("\n[3] Getting system info...")
        info = client.get_system_info()
        print(f"System Info:\n{json.dumps(info, indent=2)}")

        client.close()

    except Exception as e:
        print(f"Error: {e}")
        print("Note: This demo requires the MCP server to be running.")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the demo."""
    import argparse

    parser = argparse.ArgumentParser(
        description="NotificationSystem MCP Server Client"
    )
    parser.add_argument(
        "--mode",
        choices=["direct", "server"],
        default="direct",
        help="Demo mode: direct (no server) or server (requires running server)"
    )

    args = parser.parse_args()

    if args.mode == "direct":
        demo_direct_usage()
    else:
        asyncio.run(demo_server_usage())


if __name__ == "__main__":
    main()
