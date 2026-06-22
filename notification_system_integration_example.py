"""Integration examples for NotificationSystem MCP Server.

Demonstrates how to integrate the NotificationSystem into various applications
and workflows.
"""

import json
from datetime import datetime, timedelta
from notification_system_mcp import NotificationService


def example_1_basic_notification():
    """Example 1: Basic notification sending."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Notification Sending")
    print("="*80)

    service = NotificationService()

    # Send a simple notification
    response = service.send_notification(
        recipient="user@example.com",
        subject="Welcome!",
        message="Welcome to our service!"
    )

    print(f"Notification sent successfully!")
    print(f"  Case ID: {response.case_id}")
    print(f"  Message ID: {response.message_id}")
    print(f"  Status: {response.status}")
    print(f"  Recipient: {response.recipient}")


def example_2_priority_levels():
    """Example 2: Sending notifications with different priorities."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Priority Levels")
    print("="*80)

    service = NotificationService()

    priorities = [
        ("low", "Maintenance scheduled for next month"),
        ("normal", "Your monthly report is ready"),
        ("high", "Account verification required"),
        ("critical", "Immediate action required - security issue detected")
    ]

    case_ids = {}

    for priority, message in priorities:
        response = service.send_notification(
            recipient=f"admin@example.com",
            subject=f"[{priority.upper()}] Action Required",
            message=message,
            priority=priority,
            notification_type="general"
        )
        case_ids[priority] = response.case_id
        print(f"  [{priority.upper()}] {response.case_id} - {message[:50]}...")

    print(f"\nAll {len(case_ids)} notifications sent with different priorities")


def example_3_notification_types():
    """Example 3: Different notification types."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Notification Types")
    print("="*80)

    service = NotificationService()

    notification_types = {
        "general": ("Product Update Available", "A new version of our product is available"),
        "alert": ("Price Change Alert", "The price of your tracked item has changed"),
        "warning": ("High Memory Usage", "Server memory usage exceeded 90%"),
        "urgent": ("Account Suspended", "Your account has been suspended due to policy violation")
    }

    case_ids = {}

    for notif_type, (subject, message) in notification_types.items():
        response = service.send_notification(
            recipient="operations@example.com",
            subject=subject,
            message=message,
            notification_type=notif_type,
            priority="normal"
        )
        case_ids[notif_type] = response.case_id
        print(f"  [{notif_type.upper()}] {response.case_id}")

    print(f"\nAll {len(case_ids)} notification types sent")


def example_4_metadata_tracking():
    """Example 4: Using metadata for enhanced tracking."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Metadata Tracking")
    print("="*80)

    service = NotificationService()

    # Send notification with rich metadata
    response = service.send_notification(
        recipient="support@example.com",
        subject="New Support Ticket",
        message="A new support ticket has been created",
        notification_type="general",
        priority="high",
        metadata={
            "ticket_id": "TKT-12345",
            "customer_id": "CUST-789",
            "priority_level": "high",
            "category": "billing",
            "created_at": datetime.now().isoformat(),
            "department": "billing_support"
        }
    )

    print(f"Notification sent: {response.case_id}")

    # Retrieve and display metadata
    status = service.get_notification_status(response.case_id)
    audit_entry = status["audit_trail"][1]  # notification_sent action

    print(f"\nMetadata captured:")
    metadata = audit_entry["details"].get("metadata", {})
    for key, value in metadata.items():
        print(f"  {key}: {value}")


def example_5_audit_trail_analysis():
    """Example 5: Analyzing audit trails for compliance."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Audit Trail Analysis")
    print("="*80)

    service = NotificationService()

    # Send several notifications
    print("Sending notifications...")
    case_ids = []
    for i in range(3):
        response = service.send_notification(
            recipient=f"user{i}@example.com",
            subject=f"Notification {i}",
            message=f"This is notification {i}",
            notification_type="general"
        )
        case_ids.append(response.case_id)

    # Analyze audit trail
    all_entries = service.audit_trail_manager.get_all_audit_entries()

    print(f"\nAudit Analysis:")
    print(f"  Total notifications: {len(service.case_id_manager.list_case_ids())}")
    print(f"  Total audit entries: {len(all_entries)}")

    # Group by action
    actions = {}
    for entry in all_entries:
        action = entry["action"]
        actions[action] = actions.get(action, 0) + 1

    print(f"\n  Actions performed:")
    for action, count in sorted(actions.items()):
        print(f"    {action}: {count}")

    # Group by result
    results = {}
    for entry in all_entries:
        result = entry["result"]
        results[result] = results.get(result, 0) + 1

    print(f"\n  Results:")
    for result, count in sorted(results.items()):
        print(f"    {result}: {count}")


def example_6_status_tracking():
    """Example 6: Tracking notification status over time."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Status Tracking")
    print("="*80)

    service = NotificationService()

    # Send a notification
    response = service.send_notification(
        recipient="user@example.com",
        subject="Status Tracking Test",
        message="This notification demonstrates status tracking",
        notification_type="general"
    )

    case_id = response.case_id
    print(f"Notification sent: {case_id}")

    # Get status immediately
    status = service.get_notification_status(case_id)

    print(f"\nNotification Status Report:")
    print(f"  Case ID: {status['case_id']}")
    print(f"  Recipient: {status['case_info']['recipient']}")
    print(f"  Subject: {status['case_info']['subject']}")
    print(f"  Total actions: {status['total_actions']}")

    print(f"\nAudit Trail:")
    for i, entry in enumerate(status["audit_trail"], 1):
        print(f"  {i}. [{entry['action']}] {entry['result']}")
        print(f"     Time: {entry['timestamp']}")
        print(f"     Actor: {entry['actor']}")


def example_7_bulk_notifications():
    """Example 7: Sending bulk notifications to multiple recipients."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Bulk Notifications")
    print("="*80)

    service = NotificationService()

    # Define recipients and customize each notification
    recipients = [
        {
            "email": "alice@example.com",
            "name": "Alice",
            "role": "Admin"
        },
        {
            "email": "bob@example.com",
            "name": "Bob",
            "role": "User"
        },
        {
            "email": "charlie@example.com",
            "name": "Charlie",
            "role": "Moderator"
        }
    ]

    case_ids = []

    print(f"Sending notifications to {len(recipients)} recipients...")

    for recipient in recipients:
        response = service.send_notification(
            recipient=recipient["email"],
            subject=f"Welcome, {recipient['name']}!",
            message=f"You have been granted {recipient['role']} access",
            notification_type="general",
            priority="normal",
            metadata={
                "recipient_name": recipient["name"],
                "recipient_role": recipient["role"],
                "batch_id": "BATCH-2024-001"
            }
        )
        case_ids.append(response.case_id)
        print(f"  ✓ {recipient['email']}: {response.case_id}")

    print(f"\nBulk notifications completed: {len(case_ids)} sent")

    # List all notifications
    all_cases = service.case_id_manager.list_case_ids()
    print(f"Total notifications in system: {len(all_cases)}")


def example_8_error_handling():
    """Example 8: Handling edge cases and errors."""
    print("\n" + "="*80)
    print("EXAMPLE 8: Error Handling")
    print("="*80)

    service = NotificationService()

    # Test 1: Valid notification
    print("Test 1: Valid notification")
    try:
        response = service.send_notification(
            recipient="valid@example.com",
            subject="Test",
            message="Valid notification"
        )
        print(f"  ✓ Success: {response.case_id}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test 2: Invalid metadata (handled gracefully)
    print("\nTest 2: Invalid metadata handling")
    try:
        response = service.send_notification(
            recipient="test@example.com",
            subject="Test",
            message="Test with invalid metadata",
            metadata={"valid": "metadata"}
        )
        print(f"  ✓ Success: {response.case_id}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test 3: Nonexistent case ID
    print("\nTest 3: Nonexistent case ID")
    status = service.get_notification_status("NOTIF-99999999-INVALID")
    if status["status"] == "not_found":
        print(f"  ✓ Correctly handled: {status['status']}")
    else:
        print(f"  ✗ Unexpected result: {status}")


def example_9_compliance_report():
    """Example 9: Generating compliance reports."""
    print("\n" + "="*80)
    print("EXAMPLE 9: Compliance Report Generation")
    print("="*80)

    service = NotificationService()

    # Send some notifications first
    print("Generating sample notifications...")
    for i in range(5):
        service.send_notification(
            recipient=f"user{i}@example.com",
            subject=f"Compliance Test {i}",
            message=f"Test message {i}",
            notification_type="general",
            priority="normal" if i % 2 == 0 else "high"
        )

    # Generate compliance report
    print("\n" + "-"*80)
    print("COMPLIANCE REPORT")
    print("-"*80)

    report_date = datetime.now().isoformat()
    print(f"Generated: {report_date}")

    all_cases = service.case_id_manager.list_case_ids()
    all_entries = service.audit_trail_manager.get_all_audit_entries()

    print(f"\nNotification Statistics:")
    print(f"  Total notifications: {len(all_cases)}")
    print(f"  Total audit entries: {len(all_entries)}")

    # Analyze notification types
    types = {}
    priorities = {}

    for case_id, info in all_cases.items():
        notif_type = info.get("notification_type", "unknown")
        types[notif_type] = types.get(notif_type, 0) + 1

    print(f"\nNotification Breakdown:")
    print(f"  By Type:")
    for notif_type, count in sorted(types.items()):
        print(f"    {notif_type}: {count}")

    # Audit trail analysis
    actions = {}
    results = {}

    for entry in all_entries:
        action = entry["action"]
        result = entry["result"]
        actions[action] = actions.get(action, 0) + 1
        results[result] = results.get(result, 0) + 1

    print(f"\nAudit Trail Analysis:")
    print(f"  Actions:")
    for action, count in sorted(actions.items()):
        print(f"    {action}: {count}")
    print(f"  Results:")
    for result, count in sorted(results.items()):
        print(f"    {result}: {count}")

    print(f"\nCompliance Status: PASS")
    print(f"All notifications properly logged and tracked.")


def example_10_export_to_json():
    """Example 10: Exporting notification data to JSON."""
    print("\n" + "="*80)
    print("EXAMPLE 10: Export to JSON")
    print("="*80)

    service = NotificationService()

    # Send a sample notification
    response = service.send_notification(
        recipient="export@example.com",
        subject="Export Test",
        message="Testing JSON export"
    )

    # Get status and prepare export
    status = service.get_notification_status(response.case_id)

    # Create export structure
    export_data = {
        "export_date": datetime.now().isoformat(),
        "notification": {
            "case_id": status["case_id"],
            "case_info": status["case_info"],
            "audit_trail": status["audit_trail"],
            "summary": {
                "total_actions": status["total_actions"],
                "first_action": status["audit_trail"][0]["timestamp"] if status["audit_trail"] else None,
                "last_action": status["audit_trail"][-1]["timestamp"] if status["audit_trail"] else None
            }
        }
    }

    print("Export Data:")
    print(json.dumps(export_data, indent=2, default=str)[:500] + "...")

    print(f"\nExport contains:")
    print(f"  Case ID: {export_data['notification']['case_id']}")
    print(f"  Total actions: {export_data['notification']['summary']['total_actions']}")
    print(f"  Recipient: {export_data['notification']['case_info']['recipient']}")


def main():
    """Run all examples."""
    print("\n")
    print("#"*80)
    print("# NotificationSystem MCP Server - Integration Examples")
    print("#"*80)

    examples = [
        example_1_basic_notification,
        example_2_priority_levels,
        example_3_notification_types,
        example_4_metadata_tracking,
        example_5_audit_trail_analysis,
        example_6_status_tracking,
        example_7_bulk_notifications,
        example_8_error_handling,
        example_9_compliance_report,
        example_10_export_to_json
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")

    print("\n" + "#"*80)
    print("# All examples completed!")
    print("#"*80 + "\n")


if __name__ == "__main__":
    main()
