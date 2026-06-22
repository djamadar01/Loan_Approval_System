"""
Webhook Management System - Integration Example

This example demonstrates:
1. Webhook registration with various configurations
2. Event triggering with payload data
3. Custom filters for targeted delivery
4. Monitoring and statistics
5. Webhook management (enable/disable)
"""

import json
from datetime import datetime
from webhooks import WebhookManager, EventType, WebhookStatus


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def example_basic_webhook_registration():
    """Example 1: Basic webhook registration."""
    print_section("Example 1: Basic Webhook Registration")

    manager = WebhookManager()

    # Register a simple webhook
    webhook_id = manager.register_webhook(
        url="https://api.example.com/webhooks",
        event_types=[EventType.APPLICATION_SUBMITTED, EventType.DECISION_MADE],
    )

    print(f"✓ Webhook registered with ID: {webhook_id}")
    print(f"✓ Subscribing to: APPLICATION_SUBMITTED, DECISION_MADE")

    webhooks = manager.list_webhooks()
    print(f"\nTotal registered webhooks: {len(webhooks)}")
    for webhook in webhooks:
        print(f"  - {webhook['url']}")
        print(f"    Event types: {', '.join(webhook['event_types'])}")
        print(f"    Active: {webhook['active']}")

    return manager, webhook_id


def example_multiple_webhooks_with_filters():
    """Example 2: Multiple webhooks with custom filters."""
    print_section("Example 2: Multiple Webhooks with Custom Filters")

    manager = WebhookManager()

    # Webhook 1: High-priority applications
    print("Registering webhook for HIGH-PRIORITY applications...")
    webhook_1 = manager.register_webhook(
        url="https://priority.example.com/webhooks",
        event_types=[EventType.APPLICATION_SUBMITTED],
        custom_filter=lambda event: event["payload"].get("priority") == "high",
        headers={"Authorization": "Bearer HIGH_PRIORITY_TOKEN"},
    )
    print(f"✓ High-priority webhook: {webhook_1}")

    # Webhook 2: Specific departments
    print("\nRegistering webhook for FINANCE department...")
    webhook_2 = manager.register_webhook(
        url="https://finance.example.com/webhooks",
        event_types=[EventType.STATUS_CHANGED],
        custom_filter=lambda event: event["payload"].get("department") == "finance",
        headers={"Authorization": "Bearer FINANCE_TOKEN"},
    )
    print(f"✓ Finance department webhook: {webhook_2}")

    # Webhook 3: All decision events
    print("\nRegistering webhook for ALL decision events...")
    webhook_3 = manager.register_webhook(
        url="https://notifications.example.com/decisions",
        event_types=[EventType.DECISION_MADE],
        headers={"X-Service": "notification-system"},
    )
    print(f"✓ Decision notification webhook: {webhook_3}")

    print("\n--- Triggering Events ---\n")

    # Trigger high-priority application (will send to webhook 1 only)
    print("Triggering: High-priority application submitted...")
    event_ids_1 = manager.trigger_event(
        event_type=EventType.APPLICATION_SUBMITTED,
        payload={
            "application_id": "APP-HI-001",
            "user_email": "vip@company.com",
            "priority": "high",
            "amount": 500000,
        }
    )
    print(f"✓ Events created: {len(event_ids_1)}")
    print(f"  Webhook targeted: {event_ids_1}")

    # Trigger low-priority application (won't send to webhook 1)
    print("\nTriggering: Low-priority application submitted...")
    event_ids_2 = manager.trigger_event(
        event_type=EventType.APPLICATION_SUBMITTED,
        payload={
            "application_id": "APP-LO-001",
            "user_email": "user@company.com",
            "priority": "low",
            "amount": 5000,
        }
    )
    print(f"✓ Events created: {len(event_ids_2)}")

    # Trigger status change for finance
    print("\nTriggering: Status change in finance department...")
    event_ids_3 = manager.trigger_event(
        event_type=EventType.STATUS_CHANGED,
        payload={
            "application_id": "APP-FIN-001",
            "department": "finance",
            "old_status": "pending_review",
            "new_status": "approved",
        }
    )
    print(f"✓ Events created: {len(event_ids_3)}")

    # Trigger decision event (sends to webhook 3)
    print("\nTriggering: Decision made event...")
    event_ids_4 = manager.trigger_event(
        event_type=EventType.DECISION_MADE,
        payload={
            "application_id": "APP-DEC-001",
            "decision": "approved",
            "decision_date": datetime.utcnow().isoformat(),
            "approved_by": "manager@company.com",
        }
    )
    print(f"✓ Events created: {len(event_ids_4)}")

    print(f"\nTotal pending events: {len(manager.pending_events)}")

    return manager, [webhook_1, webhook_2, webhook_3]


def example_retry_configuration():
    """Example 3: Configure retry behavior."""
    print_section("Example 3: Retry Configuration")

    manager = WebhookManager()

    print("Configuring webhook with custom retry settings...\n")

    webhook_id = manager.register_webhook(
        url="https://unreliable-service.example.com/webhook",
        event_types=[EventType.APPLICATION_SUBMITTED],
        retry_max_attempts=5,           # Try up to 5 times
        retry_initial_delay=2.0,        # Start with 2 second delay
        retry_backoff_factor=2.0,       # Double delay each attempt
    )

    endpoint = manager.get_webhook(webhook_id)

    print(f"Webhook ID: {webhook_id}")
    print(f"Max retry attempts: {endpoint.retry_max_attempts}")
    print(f"Initial delay: {endpoint.retry_initial_delay}s")
    print(f"Backoff factor: {endpoint.retry_backoff_factor}")

    print("\n--- Exponential Backoff Schedule ---\n")
    for attempt in range(1, endpoint.retry_max_attempts + 1):
        delay = endpoint.retry_initial_delay * (
            endpoint.retry_backoff_factor ** (attempt - 1)
        )
        print(f"  Attempt {attempt}: wait {delay:.1f}s before retry")

    return manager, webhook_id


def example_webhook_management():
    """Example 4: Managing webhooks (enable/disable)."""
    print_section("Example 4: Managing Webhooks")

    manager = WebhookManager()

    # Register two webhooks
    webhook_1 = manager.register_webhook(
        url="https://active.example.com/webhook",
        event_types=[EventType.APPLICATION_SUBMITTED],
    )
    webhook_2 = manager.register_webhook(
        url="https://maintenance.example.com/webhook",
        event_types=[EventType.APPLICATION_SUBMITTED],
    )

    print(f"Registered webhooks:")
    print(f"  1. {webhook_1}")
    print(f"  2. {webhook_2}")

    print("\n--- Active Webhooks ---")
    for webhook in manager.list_webhooks(active_only=True):
        print(f"✓ {webhook['url']}")

    print(f"\n--- Disabling webhook {webhook_2} for maintenance ---")
    manager.update_webhook_status(webhook_2, active=False)

    print("\n--- Active Webhooks (after disabling) ---")
    active_count = len(manager.list_webhooks(active_only=True))
    for webhook in manager.list_webhooks(active_only=True):
        print(f"✓ {webhook['url']}")
    print(f"Total active: {active_count}")

    print(f"\n--- Triggering event with disabled webhook ---")
    event_ids = manager.trigger_event(
        event_type=EventType.APPLICATION_SUBMITTED,
        payload={"application_id": "APP-001"},
    )
    print(f"✓ Events created: {len(event_ids)} (only for active webhooks)")

    print(f"\n--- Re-enabling webhook ---")
    manager.update_webhook_status(webhook_2, active=True)
    print("✓ Webhook re-enabled")

    return manager


def example_statistics_monitoring():
    """Example 5: Statistics and monitoring."""
    print_section("Example 5: Statistics and Monitoring")

    from webhooks import DeliveryLog

    manager = WebhookManager()

    # Register webhooks
    webhook_1 = manager.register_webhook(
        url="https://api1.example.com/webhook",
        event_types=[EventType.APPLICATION_SUBMITTED],
    )
    webhook_2 = manager.register_webhook(
        url="https://api2.example.com/webhook",
        event_types=[EventType.DECISION_MADE],
    )

    # Simulate delivery logs
    for i in range(10):
        log = DeliveryLog(
            id=f"log-1-{i}",
            webhook_id=webhook_1,
            event_id=f"event-1-{i}",
            status=WebhookStatus.SUCCESS if i % 2 == 0 else WebhookStatus.FAILED,
            status_code=200 if i % 2 == 0 else 500,
            delivery_time_ms=100 + i * 5,
        )
        manager.delivery_logs.append(log)

    for i in range(5):
        log = DeliveryLog(
            id=f"log-2-{i}",
            webhook_id=webhook_2,
            event_id=f"event-2-{i}",
            status=WebhookStatus.SUCCESS,
            status_code=200,
            delivery_time_ms=150 + i * 10,
        )
        manager.delivery_logs.append(log)

    # Get global statistics
    print("--- Global Statistics ---\n")
    stats = manager.get_webhook_statistics()
    print(f"Total webhooks: {stats['total_webhooks']}")
    print(f"Active webhooks: {stats['active_webhooks']}")

    # Get per-webhook statistics
    print("\n--- Per-Webhook Statistics ---\n")
    for webhook_id, wstats in stats["webhooks"].items():
        endpoint = manager.get_webhook(webhook_id)
        print(f"Webhook: {endpoint.url}")
        print(f"  Total events: {wstats['total_events']}")
        print(f"  Successful: {wstats['successful']}")
        print(f"  Failed: {wstats['failed']}")
        print(f"  Retrying: {wstats['retrying']}")
        print(f"  Avg delivery time: {wstats['avg_delivery_time_ms']:.2f}ms")
        print()

    # Get logs for specific webhook
    print(f"--- Recent Logs for {webhook_1} ---\n")
    logs = manager.get_delivery_logs(webhook_id=webhook_1, limit=5)
    for log in logs:
        status_symbol = "✓" if log["status"] == "success" else "✗"
        print(f"{status_symbol} {log['timestamp']}: {log['status']} "
              f"(code: {log['status_code']}, time: {log['delivery_time_ms']:.2f}ms)")

    return manager


def example_signature_verification():
    """Example 6: Signature verification for security."""
    print_section("Example 6: Webhook Signature Verification")

    manager = WebhookManager()

    webhook_id = manager.register_webhook(
        url="https://secure.example.com/webhook",
        event_types=[EventType.APPLICATION_SUBMITTED],
        secret="my-secure-secret-key",
    )

    endpoint = manager.get_webhook(webhook_id)

    # Simulate webhook delivery
    payload = {
        "event_id": "evt-123",
        "event_type": "application_submitted",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "application_id": "APP-001",
            "user_email": "user@example.com",
        }
    }

    # Generate signature
    signature = manager._generate_signature(payload, endpoint.secret)

    print(f"Webhook Secret: {endpoint.secret}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    print(f"\nGenerated Signature: {signature}")

    # Verify signature (correct secret)
    print(f"\n--- Verification with correct secret ---")
    is_valid = manager.verify_signature(payload, signature, endpoint.secret)
    print(f"✓ Signature valid: {is_valid}")

    # Try with wrong secret
    print(f"\n--- Verification with incorrect secret ---")
    is_valid = manager.verify_signature(payload, signature, "wrong-secret")
    print(f"✗ Signature valid: {is_valid}")

    return manager


def example_data_export():
    """Example 7: Export webhooks and logs."""
    print_section("Example 7: Data Export")

    manager = WebhookManager()

    # Register webhooks
    for i in range(3):
        manager.register_webhook(
            url=f"https://webhook{i}.example.com/endpoint",
            event_types=[EventType.APPLICATION_SUBMITTED, EventType.DECISION_MADE],
            headers={"X-Webhook-ID": str(i)},
        )

    # Add some delivery logs
    from webhooks import DeliveryLog
    for i in range(5):
        log = DeliveryLog(
            id=f"log-{i}",
            webhook_id=list(manager.endpoints.keys())[i % 3],
            event_id=f"event-{i}",
            status=WebhookStatus.SUCCESS,
            status_code=200,
            delivery_time_ms=100 + i * 10,
        )
        manager.delivery_logs.append(log)

    print("Exporting webhook data...\n")

    # Export webhooks
    webhooks_file = "/tmp/webhooks_export.json"
    manager.export_webhooks_json(webhooks_file)
    print(f"✓ Webhooks exported to: {webhooks_file}")

    # Export logs
    logs_file = "/tmp/webhook_logs_export.json"
    manager.export_logs_json(logs_file)
    print(f"✓ Delivery logs exported to: {logs_file}")

    # Read and display
    print(f"\n--- Webhooks Export Preview ---")
    with open(webhooks_file, 'r') as f:
        data = json.load(f)
        print(f"Total webhooks: {data['total_webhooks']}")
        for webhook in data['webhooks']:
            print(f"  - {webhook['url']}")

    print(f"\n--- Logs Export Preview ---")
    with open(logs_file, 'r') as f:
        data = json.load(f)
        print(f"Total logs: {data['total_logs']}")
        for log in data['logs'][:3]:  # Show first 3
            print(f"  - Event {log['event_id']}: {log['status']}")

    return manager


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("  WEBHOOK MANAGEMENT SYSTEM - INTEGRATION EXAMPLES")
    print("="*60)

    try:
        # Example 1
        manager, webhook_id = example_basic_webhook_registration()

        # Example 2
        manager, webhooks = example_multiple_webhooks_with_filters()

        # Example 3
        manager, webhook_id = example_retry_configuration()

        # Example 4
        manager = example_webhook_management()

        # Example 5
        manager = example_statistics_monitoring()

        # Example 6
        manager = example_signature_verification()

        # Example 7
        manager = example_data_export()

        print_section("All Examples Completed Successfully!")
        print("✓ Basic webhook registration")
        print("✓ Multiple webhooks with custom filters")
        print("✓ Retry configuration with exponential backoff")
        print("✓ Webhook management (enable/disable)")
        print("✓ Statistics and monitoring")
        print("✓ Signature verification for security")
        print("✓ Data export to JSON")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
