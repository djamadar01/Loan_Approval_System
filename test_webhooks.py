"""
Comprehensive tests for the webhook management system.

Demonstrates all features including:
- Endpoint registration and deregistration
- Event triggering with filtering
- Retry logic with exponential backoff
- Delivery logging and statistics
"""

import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from webhooks import (
    WebhookManager,
    EventType,
    WebhookStatus,
    WebhookEndpoint,
    WebhookEvent,
    DeliveryLog,
    EventFilter,
)


class TestWebhookRegistration(unittest.TestCase):
    """Test webhook registration and deregistration."""

    def setUp(self):
        self.manager = WebhookManager()

    def test_register_webhook_success(self):
        """Test successful webhook registration."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )

        self.assertIsNotNone(webhook_id)
        self.assertIn(webhook_id, self.manager.endpoints)

    def test_register_webhook_multiple_event_types(self):
        """Test registering webhook with multiple event types."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[
                EventType.APPLICATION_SUBMITTED,
                EventType.DECISION_MADE,
                EventType.STATUS_CHANGED,
            ],
        )

        endpoint = self.manager.get_webhook(webhook_id)
        self.assertEqual(len(endpoint.event_types), 3)

    def test_register_webhook_with_custom_secret(self):
        """Test registering webhook with custom secret."""
        secret = "my-custom-secret"
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
            secret=secret,
        )

        endpoint = self.manager.get_webhook(webhook_id)
        self.assertEqual(endpoint.secret, secret)

    def test_register_webhook_with_custom_headers(self):
        """Test registering webhook with custom headers."""
        headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
            headers=headers,
        )

        endpoint = self.manager.get_webhook(webhook_id)
        self.assertEqual(endpoint.headers, headers)

    def test_register_webhook_invalid_url(self):
        """Test registering webhook with invalid URL."""
        with self.assertRaises(ValueError):
            self.manager.register_webhook(
                url="not-a-valid-url",
                event_types=[EventType.APPLICATION_SUBMITTED],
            )

    def test_register_webhook_empty_event_types(self):
        """Test registering webhook with no event types."""
        with self.assertRaises(ValueError):
            self.manager.register_webhook(
                url="https://example.com/webhook",
                event_types=[],
            )

    def test_deregister_webhook_success(self):
        """Test successful webhook deregistration."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )

        deregistered = self.manager.deregister_webhook(webhook_id)
        self.assertTrue(deregistered)
        self.assertNotIn(webhook_id, self.manager.endpoints)

    def test_deregister_webhook_not_found(self):
        """Test deregistering non-existent webhook."""
        deregistered = self.manager.deregister_webhook("non-existent-id")
        self.assertFalse(deregistered)


class TestEventTriggering(unittest.TestCase):
    """Test event triggering and filtering."""

    def setUp(self):
        self.manager = WebhookManager()

    def test_trigger_event_single_subscriber(self):
        """Test triggering event with single subscriber."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )

        event_ids = self.manager.trigger_event(
            event_type=EventType.APPLICATION_SUBMITTED,
            payload={"application_id": "APP-001"},
        )

        self.assertEqual(len(event_ids), 1)
        self.assertEqual(len(self.manager.pending_events), 1)

    def test_trigger_event_multiple_subscribers(self):
        """Test triggering event with multiple subscribers."""
        webhook_1 = self.manager.register_webhook(
            url="https://example.com/webhook1",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )
        webhook_2 = self.manager.register_webhook(
            url="https://example.com/webhook2",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )

        event_ids = self.manager.trigger_event(
            event_type=EventType.APPLICATION_SUBMITTED,
            payload={"application_id": "APP-001"},
        )

        self.assertEqual(len(event_ids), 2)

    def test_trigger_event_no_matching_subscribers(self):
        """Test triggering event with no matching subscribers."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.DECISION_MADE],
        )

        event_ids = self.manager.trigger_event(
            event_type=EventType.APPLICATION_SUBMITTED,
            payload={"application_id": "APP-001"},
        )

        self.assertEqual(len(event_ids), 0)

    def test_trigger_event_with_custom_filter(self):
        """Test triggering event with custom event filter."""
        def high_priority_filter(event):
            return event["payload"].get("priority") == "high"

        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
            custom_filter=high_priority_filter,
        )

        # Should trigger (high priority)
        event_ids_1 = self.manager.trigger_event(
            event_type=EventType.APPLICATION_SUBMITTED,
            payload={"application_id": "APP-001", "priority": "high"},
        )
        self.assertEqual(len(event_ids_1), 1)

        # Should not trigger (low priority)
        event_ids_2 = self.manager.trigger_event(
            event_type=EventType.APPLICATION_SUBMITTED,
            payload={"application_id": "APP-002", "priority": "low"},
        )
        self.assertEqual(len(event_ids_2), 0)

    def test_trigger_event_inactive_webhook(self):
        """Test that inactive webhooks don't receive events."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )

        self.manager.update_webhook_status(webhook_id, active=False)

        event_ids = self.manager.trigger_event(
            event_type=EventType.APPLICATION_SUBMITTED,
            payload={"application_id": "APP-001"},
        )

        self.assertEqual(len(event_ids), 0)


class TestRetryLogic(unittest.TestCase):
    """Test retry logic with exponential backoff."""

    def setUp(self):
        self.manager = WebhookManager()

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
            retry_initial_delay=1.0,
            retry_backoff_factor=2.0,
        )

        endpoint = self.manager.get_webhook(webhook_id)

        # Verify backoff factors
        delay_1 = endpoint.retry_initial_delay * (endpoint.retry_backoff_factor ** 0)
        delay_2 = endpoint.retry_initial_delay * (endpoint.retry_backoff_factor ** 1)
        delay_3 = endpoint.retry_initial_delay * (endpoint.retry_backoff_factor ** 2)

        self.assertEqual(delay_1, 1.0)
        self.assertEqual(delay_2, 2.0)
        self.assertEqual(delay_3, 4.0)

    def test_retry_scheduling(self):
        """Test that failed events are scheduled for retry."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
            retry_max_attempts=3,
            retry_initial_delay=1.0,
        )

        endpoint = self.manager.get_webhook(webhook_id)
        event = WebhookEvent(
            id="event-1",
            type=EventType.APPLICATION_SUBMITTED,
            timestamp=datetime.utcnow(),
            payload={"application_id": "APP-001"},
            endpoint_id=webhook_id,
            attempt=0,
        )

        log_entry = DeliveryLog(
            id="log-1",
            webhook_id=webhook_id,
            event_id=event.id,
            status=WebhookStatus.FAILED,
        )

        self.manager._schedule_retry(event, endpoint, log_entry)

        self.assertEqual(len(self.manager.pending_events), 1)
        self.assertIsNotNone(event.next_retry)

    def test_retry_max_attempts(self):
        """Test that retries stop after max attempts."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
            retry_max_attempts=2,
        )

        endpoint = self.manager.get_webhook(webhook_id)
        event = WebhookEvent(
            id="event-1",
            type=EventType.APPLICATION_SUBMITTED,
            timestamp=datetime.utcnow(),
            payload={"application_id": "APP-001"},
            endpoint_id=webhook_id,
            attempt=2,  # Already at max attempts
        )

        log_entry = DeliveryLog(
            id="log-1",
            webhook_id=webhook_id,
            event_id=event.id,
            status=WebhookStatus.FAILED,
        )

        self.manager._schedule_retry(event, endpoint, log_entry)

        # Should not add to pending events
        self.assertEqual(len(self.manager.pending_events), 0)
        # Log status should be FAILED
        self.assertEqual(log_entry.status, WebhookStatus.FAILED)


class TestSignatureGeneration(unittest.TestCase):
    """Test webhook signature generation and verification."""

    def setUp(self):
        self.manager = WebhookManager()

    def test_signature_generation(self):
        """Test HMAC-SHA256 signature generation."""
        secret = "test-secret"
        payload = {"event_id": "1", "type": "test"}

        signature = self.manager._generate_signature(payload, secret)

        self.assertIsNotNone(signature)
        self.assertEqual(len(signature), 64)  # SHA256 hex is 64 chars

    def test_signature_verification_valid(self):
        """Test valid signature verification."""
        secret = "test-secret"
        payload = {"event_id": "1", "type": "test"}

        signature = self.manager._generate_signature(payload, secret)
        is_valid = self.manager.verify_signature(payload, signature, secret)

        self.assertTrue(is_valid)

    def test_signature_verification_invalid(self):
        """Test invalid signature verification."""
        secret = "test-secret"
        payload = {"event_id": "1", "type": "test"}

        is_valid = self.manager.verify_signature(payload, "wrong-signature", secret)

        self.assertFalse(is_valid)


class TestDeliveryLogging(unittest.TestCase):
    """Test delivery logging and retrieval."""

    def setUp(self):
        self.manager = WebhookManager()

    def test_delivery_log_creation(self):
        """Test creating delivery log entries."""
        log = DeliveryLog(
            id="log-1",
            webhook_id="webhook-1",
            event_id="event-1",
            status=WebhookStatus.SUCCESS,
            status_code=200,
        )

        self.manager.delivery_logs.append(log)
        self.assertEqual(len(self.manager.delivery_logs), 1)

    def test_get_delivery_logs_by_webhook(self):
        """Test retrieving logs filtered by webhook ID."""
        for i in range(5):
            log = DeliveryLog(
                id=f"log-{i}",
                webhook_id="webhook-1",
                event_id=f"event-{i}",
                status=WebhookStatus.SUCCESS,
            )
            self.manager.delivery_logs.append(log)

        logs = self.manager.get_delivery_logs(webhook_id="webhook-1")
        self.assertEqual(len(logs), 5)

    def test_get_delivery_logs_by_status(self):
        """Test retrieving logs filtered by status."""
        for i in range(3):
            log = DeliveryLog(
                id=f"log-{i}",
                webhook_id="webhook-1",
                event_id=f"event-{i}",
                status=WebhookStatus.SUCCESS,
            )
            self.manager.delivery_logs.append(log)

        log = DeliveryLog(
            id="log-failed",
            webhook_id="webhook-1",
            event_id="event-failed",
            status=WebhookStatus.FAILED,
        )
        self.manager.delivery_logs.append(log)

        logs = self.manager.get_delivery_logs(status=WebhookStatus.SUCCESS)
        self.assertEqual(len(logs), 3)

    def test_clear_old_logs(self):
        """Test clearing old delivery logs."""
        # Add recent log
        recent_log = DeliveryLog(
            id="log-recent",
            webhook_id="webhook-1",
            event_id="event-1",
            status=WebhookStatus.SUCCESS,
            timestamp=datetime.utcnow(),
        )
        self.manager.delivery_logs.append(recent_log)

        # Add old log
        old_log = DeliveryLog(
            id="log-old",
            webhook_id="webhook-1",
            event_id="event-2",
            status=WebhookStatus.SUCCESS,
            timestamp=datetime.utcnow() - timedelta(days=40),
        )
        self.manager.delivery_logs.append(old_log)

        deleted = self.manager.clear_delivery_logs(older_than_days=30)

        self.assertEqual(deleted, 1)
        self.assertEqual(len(self.manager.delivery_logs), 1)


class TestStatistics(unittest.TestCase):
    """Test webhook statistics calculation."""

    def setUp(self):
        self.manager = WebhookManager()

    def test_webhook_statistics_global(self):
        """Test getting global webhook statistics."""
        webhook_1 = self.manager.register_webhook(
            url="https://example.com/webhook1",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )
        webhook_2 = self.manager.register_webhook(
            url="https://example.com/webhook2",
            event_types=[EventType.DECISION_MADE],
        )

        stats = self.manager.get_webhook_statistics()

        self.assertEqual(stats["total_webhooks"], 2)
        self.assertEqual(stats["active_webhooks"], 2)

    def test_webhook_statistics_specific(self):
        """Test getting statistics for specific webhook."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )

        # Add some logs
        for i in range(3):
            log = DeliveryLog(
                id=f"log-{i}",
                webhook_id=webhook_id,
                event_id=f"event-{i}",
                status=WebhookStatus.SUCCESS,
                delivery_time_ms=100.0 + i * 10,
            )
            self.manager.delivery_logs.append(log)

        stats = self.manager.get_webhook_statistics(webhook_id=webhook_id)

        self.assertEqual(stats["webhooks"][webhook_id]["total_events"], 3)
        self.assertEqual(stats["webhooks"][webhook_id]["successful"], 3)

    def test_webhook_statistics_average_delivery_time(self):
        """Test average delivery time calculation."""
        webhook_id = self.manager.register_webhook(
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
        )

        for delivery_time in [100.0, 200.0, 300.0]:
            log = DeliveryLog(
                id=f"log-{delivery_time}",
                webhook_id=webhook_id,
                event_id=f"event-{delivery_time}",
                status=WebhookStatus.SUCCESS,
                delivery_time_ms=delivery_time,
            )
            self.manager.delivery_logs.append(log)

        stats = self.manager.get_webhook_statistics(webhook_id=webhook_id)
        avg_time = stats["webhooks"][webhook_id]["avg_delivery_time_ms"]

        self.assertEqual(avg_time, 200.0)


class TestWebhookDataTypes(unittest.TestCase):
    """Test webhook data types and serialization."""

    def test_webhook_endpoint_to_dict(self):
        """Test WebhookEndpoint serialization."""
        endpoint = WebhookEndpoint(
            id="webhook-1",
            url="https://example.com/webhook",
            event_types=[EventType.APPLICATION_SUBMITTED],
            secret="secret-key",
        )

        data = endpoint.to_dict()

        self.assertEqual(data["id"], "webhook-1")
        self.assertEqual(data["url"], "https://example.com/webhook")
        self.assertEqual(data["event_types"], ["application_submitted"])

    def test_webhook_event_to_dict(self):
        """Test WebhookEvent serialization."""
        event = WebhookEvent(
            id="event-1",
            type=EventType.APPLICATION_SUBMITTED,
            timestamp=datetime.utcnow(),
            payload={"application_id": "APP-001"},
            endpoint_id="webhook-1",
        )

        data = event.to_dict()

        self.assertEqual(data["id"], "event-1")
        self.assertEqual(data["type"], "application_submitted")

    def test_delivery_log_to_dict(self):
        """Test DeliveryLog serialization."""
        log = DeliveryLog(
            id="log-1",
            webhook_id="webhook-1",
            event_id="event-1",
            status=WebhookStatus.SUCCESS,
            status_code=200,
        )

        data = log.to_dict()

        self.assertEqual(data["id"], "log-1")
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["status_code"], 200)


def run_tests():
    """Run all tests and print results."""
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
