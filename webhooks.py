"""
Webhook Management System

This module provides a complete webhook management system including:
- Endpoint registration and deregistration
- Multiple event types (application_submitted, decision_made, status_changed)
- Retry logic with exponential backoff
- Event filtering by type and custom conditions
- Comprehensive delivery logging
"""

import json
import logging
import hashlib
import hmac
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict, field
from threading import Thread
import requests
from abc import ABC, abstractmethod


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Supported event types for webhooks."""
    APPLICATION_SUBMITTED = "application_submitted"
    DECISION_MADE = "decision_made"
    STATUS_CHANGED = "status_changed"


class WebhookStatus(str, Enum):
    """Status of webhook delivery attempts."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RETRYING = "retrying"


@dataclass
class EventFilter:
    """Filter criteria for webhook events."""
    event_types: Optional[List[EventType]] = None
    custom_filter: Optional[Callable[[Dict[str, Any]], bool]] = None

    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if event matches the filter criteria."""
        if self.event_types and event.get("type") not in self.event_types:
            return False

        if self.custom_filter and not self.custom_filter(event):
            return False

        return True


@dataclass
class WebhookEndpoint:
    """Represents a registered webhook endpoint."""
    id: str
    url: str
    event_types: List[EventType]
    secret: str
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    custom_filter: Optional[Callable[[Dict[str, Any]], bool]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    retry_max_attempts: int = 5
    retry_initial_delay: float = 1.0  # seconds
    retry_backoff_factor: float = 2.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (excluding non-serializable fields)."""
        data = asdict(self)
        data['event_types'] = [et.value for et in self.event_types]
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data.pop('custom_filter', None)  # Remove callable
        return data


@dataclass
class WebhookEvent:
    """Represents a webhook event to be delivered."""
    id: str
    type: EventType
    timestamp: datetime
    payload: Dict[str, Any]
    endpoint_id: str
    attempt: int = 0
    next_retry: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'payload': self.payload,
            'endpoint_id': self.endpoint_id,
            'attempt': self.attempt,
            'next_retry': self.next_retry.isoformat() if self.next_retry else None,
        }


@dataclass
class DeliveryLog:
    """Log entry for a webhook delivery attempt."""
    id: str
    webhook_id: str
    event_id: str
    status: WebhookStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempt_number: int = 1
    next_retry_at: Optional[datetime] = None
    delivery_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'event_id': self.event_id,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'status_code': self.status_code,
            'response_body': self.response_body,
            'error_message': self.error_message,
            'attempt_number': self.attempt_number,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'delivery_time_ms': self.delivery_time_ms,
        }


class WebhookManager:
    """
    Manages webhook registration, delivery, and logging.

    Features:
    - Register and deregister webhook endpoints
    - Trigger events with filtering
    - Retry failed deliveries with exponential backoff
    - Comprehensive delivery logging
    - Event signature generation for security
    """

    def __init__(self, max_delivery_threads: int = 5):
        """
        Initialize the webhook manager.

        Args:
            max_delivery_threads: Maximum number of concurrent delivery threads
        """
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.pending_events: List[WebhookEvent] = []
        self.delivery_logs: List[DeliveryLog] = []
        self.max_delivery_threads = max_delivery_threads
        self.active_threads = 0
        self._lock = False  # Simple thread-safety flag

    def register_webhook(
        self,
        url: str,
        event_types: List[EventType],
        secret: Optional[str] = None,
        custom_filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_max_attempts: int = 5,
        retry_initial_delay: float = 1.0,
        retry_backoff_factor: float = 2.0,
    ) -> str:
        """
        Register a new webhook endpoint.

        Args:
            url: The URL to deliver webhook events to
            event_types: List of event types to subscribe to
            secret: Secret key for HMAC signature (auto-generated if not provided)
            custom_filter: Optional custom filter function for events
            headers: Optional custom headers to include in webhook requests
            retry_max_attempts: Maximum number of retry attempts
            retry_initial_delay: Initial delay for retry in seconds
            retry_backoff_factor: Backoff factor for exponential retry

        Returns:
            Webhook endpoint ID

        Raises:
            ValueError: If URL is invalid or event types are empty
        """
        if not url:
            raise ValueError("URL cannot be empty")
        if not event_types:
            raise ValueError("At least one event type must be specified")
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        endpoint_id = str(uuid.uuid4())
        secret = secret or self._generate_secret()

        endpoint = WebhookEndpoint(
            id=endpoint_id,
            url=url,
            event_types=event_types,
            secret=secret,
            active=True,
            custom_filter=custom_filter,
            headers=headers or {},
            retry_max_attempts=retry_max_attempts,
            retry_initial_delay=retry_initial_delay,
            retry_backoff_factor=retry_backoff_factor,
        )

        self.endpoints[endpoint_id] = endpoint
        logger.info(
            f"Webhook registered: {endpoint_id} -> {url} "
            f"for events: {[et.value for et in event_types]}"
        )
        return endpoint_id

    def deregister_webhook(self, webhook_id: str) -> bool:
        """
        Deregister a webhook endpoint.

        Args:
            webhook_id: ID of the webhook to deregister

        Returns:
            True if deregistered, False if not found
        """
        if webhook_id in self.endpoints:
            endpoint = self.endpoints.pop(webhook_id)
            logger.info(f"Webhook deregistered: {webhook_id} -> {endpoint.url}")
            return True
        return False

    def get_webhook(self, webhook_id: str) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint by ID."""
        return self.endpoints.get(webhook_id)

    def list_webhooks(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all registered webhooks.

        Args:
            active_only: If True, only return active webhooks

        Returns:
            List of webhook endpoint dictionaries
        """
        webhooks = []
        for endpoint in self.endpoints.values():
            if active_only and not endpoint.active:
                continue
            webhooks.append(endpoint.to_dict())
        return webhooks

    def update_webhook_status(self, webhook_id: str, active: bool) -> bool:
        """
        Enable or disable a webhook endpoint.

        Args:
            webhook_id: ID of the webhook to update
            active: New active status

        Returns:
            True if updated, False if not found
        """
        if webhook_id not in self.endpoints:
            return False

        endpoint = self.endpoints[webhook_id]
        endpoint.active = active
        endpoint.updated_at = datetime.utcnow()
        logger.info(f"Webhook {webhook_id} status updated to: {active}")
        return True

    def trigger_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        endpoint_filter: Optional[Callable[[WebhookEndpoint], bool]] = None,
    ) -> List[str]:
        """
        Trigger a webhook event to matching endpoints.

        Args:
            event_type: Type of event to trigger
            payload: Event payload data
            endpoint_filter: Optional custom filter for selecting endpoints

        Returns:
            List of event IDs created
        """
        event_ids = []
        event = {
            "type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
        }

        for endpoint_id, endpoint in self.endpoints.items():
            # Skip inactive endpoints
            if not endpoint.active:
                continue

            # Check if endpoint subscribes to this event type
            if event_type not in endpoint.event_types:
                continue

            # Apply custom endpoint filter
            if endpoint_filter and not endpoint_filter(endpoint):
                continue

            # Apply custom event filter
            if endpoint.custom_filter and not endpoint.custom_filter(event):
                continue

            # Create webhook event
            webhook_event = WebhookEvent(
                id=str(uuid.uuid4()),
                type=event_type,
                timestamp=datetime.utcnow(),
                payload=payload,
                endpoint_id=endpoint_id,
            )

            self.pending_events.append(webhook_event)
            event_ids.append(webhook_event.id)
            logger.info(
                f"Event triggered: {event_type.value} -> {endpoint_id} "
                f"(event_id: {webhook_event.id})"
            )

        return event_ids

    def deliver_pending_events(self, async_mode: bool = False) -> Dict[str, Any]:
        """
        Attempt to deliver all pending events.

        Args:
            async_mode: If True, run deliveries in background threads

        Returns:
            Dictionary with delivery statistics
        """
        if not self.pending_events:
            return {"total": 0, "successful": 0, "failed": 0}

        if async_mode:
            thread = Thread(target=self._deliver_events_batch)
            thread.daemon = True
            thread.start()
            return {"message": "Delivery started in background"}

        return self._deliver_events_batch()

    def _deliver_events_batch(self) -> Dict[str, Any]:
        """Internal method to deliver a batch of events."""
        total = len(self.pending_events)
        successful = 0
        failed = 0

        while self.pending_events:
            event = self.pending_events.pop(0)
            endpoint = self.endpoints.get(event.endpoint_id)

            if not endpoint:
                logger.warning(f"Endpoint {event.endpoint_id} not found for event {event.id}")
                failed += 1
                continue

            success = self._deliver_event(event, endpoint)
            if success:
                successful += 1
            else:
                failed += 1

        logger.info(
            f"Batch delivery complete - Total: {total}, "
            f"Successful: {successful}, Failed: {failed}"
        )
        return {"total": total, "successful": successful, "failed": failed}

    def _deliver_event(
        self,
        event: WebhookEvent,
        endpoint: WebhookEndpoint,
    ) -> bool:
        """
        Deliver a single event to an endpoint with retry logic.

        Args:
            event: The webhook event to deliver
            endpoint: The target webhook endpoint

        Returns:
            True if delivery succeeded, False otherwise
        """
        event.attempt += 1
        start_time = time.time()

        try:
            payload = {
                "event_id": event.id,
                "event_type": event.type.value,
                "timestamp": event.timestamp.isoformat(),
                "data": event.payload,
            }

            # Generate signature
            signature = self._generate_signature(payload, endpoint.secret)

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-ID": endpoint.id,
                "X-Event-Type": event.type.value,
                **endpoint.headers,
            }

            # Send request
            response = requests.post(
                endpoint.url,
                json=payload,
                headers=headers,
                timeout=10,
            )

            delivery_time = (time.time() - start_time) * 1000

            # Log delivery
            log_entry = DeliveryLog(
                id=str(uuid.uuid4()),
                webhook_id=endpoint.id,
                event_id=event.id,
                status=WebhookStatus.SUCCESS if response.status_code < 300 else WebhookStatus.FAILED,
                status_code=response.status_code,
                response_body=response.text[:500],  # Limit response body
                attempt_number=event.attempt,
                delivery_time_ms=delivery_time,
            )

            if response.status_code < 300:
                self.delivery_logs.append(log_entry)
                logger.info(
                    f"Event {event.id} delivered successfully to {endpoint.url} "
                    f"(status: {response.status_code}, time: {delivery_time:.2f}ms)"
                )
                return True
            else:
                # Schedule retry
                self._schedule_retry(event, endpoint, log_entry)
                return False

        except requests.Timeout:
            delivery_time = (time.time() - start_time) * 1000
            log_entry = DeliveryLog(
                id=str(uuid.uuid4()),
                webhook_id=endpoint.id,
                event_id=event.id,
                status=WebhookStatus.RETRYING,
                error_message="Request timeout",
                attempt_number=event.attempt,
                delivery_time_ms=delivery_time,
            )
            self._schedule_retry(event, endpoint, log_entry)
            logger.warning(f"Event {event.id} delivery timed out to {endpoint.url}")
            return False

        except requests.RequestException as e:
            delivery_time = (time.time() - start_time) * 1000
            log_entry = DeliveryLog(
                id=str(uuid.uuid4()),
                webhook_id=endpoint.id,
                event_id=event.id,
                status=WebhookStatus.RETRYING,
                error_message=str(e),
                attempt_number=event.attempt,
                delivery_time_ms=delivery_time,
            )
            self._schedule_retry(event, endpoint, log_entry)
            logger.error(f"Event {event.id} delivery failed to {endpoint.url}: {str(e)}")
            return False

    def _schedule_retry(
        self,
        event: WebhookEvent,
        endpoint: WebhookEndpoint,
        log_entry: DeliveryLog,
    ) -> None:
        """
        Schedule a retry for a failed event delivery using exponential backoff.

        Args:
            event: The webhook event
            endpoint: The target endpoint
            log_entry: The delivery log entry
        """
        if event.attempt >= endpoint.retry_max_attempts:
            log_entry.status = WebhookStatus.FAILED
            self.delivery_logs.append(log_entry)
            logger.error(
                f"Event {event.id} failed after {event.attempt} attempts to {endpoint.url}"
            )
            return

        # Calculate backoff delay
        delay = endpoint.retry_initial_delay * (
            endpoint.retry_backoff_factor ** (event.attempt - 1)
        )
        next_retry = datetime.utcnow() + timedelta(seconds=delay)
        event.next_retry = next_retry
        log_entry.next_retry_at = next_retry

        self.pending_events.append(event)
        self.delivery_logs.append(log_entry)

        logger.info(
            f"Event {event.id} scheduled for retry at {next_retry.isoformat()} "
            f"(attempt {event.attempt}/{endpoint.retry_max_attempts}, delay: {delay:.2f}s)"
        )

    def get_delivery_logs(
        self,
        webhook_id: Optional[str] = None,
        event_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve delivery logs with optional filtering.

        Args:
            webhook_id: Filter by webhook ID
            event_id: Filter by event ID
            status: Filter by delivery status
            limit: Maximum number of logs to return

        Returns:
            List of delivery log dictionaries
        """
        logs = []
        for log in reversed(self.delivery_logs):  # Most recent first
            if webhook_id and log.webhook_id != webhook_id:
                continue
            if event_id and log.event_id != event_id:
                continue
            if status and log.status != status:
                continue

            logs.append(log.to_dict())
            if len(logs) >= limit:
                break

        return logs

    def get_webhook_statistics(self, webhook_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for webhook(s).

        Args:
            webhook_id: If specified, get stats for specific webhook; otherwise get global stats

        Returns:
            Dictionary with webhook statistics
        """
        if webhook_id:
            webhooks = [webhook_id]
        else:
            webhooks = list(self.endpoints.keys())

        stats = {
            "total_webhooks": len(self.endpoints),
            "active_webhooks": sum(1 for e in self.endpoints.values() if e.active),
            "webhooks": {},
        }

        for wid in webhooks:
            logs = [l for l in self.delivery_logs if l.webhook_id == wid]
            stats["webhooks"][wid] = {
                "total_events": len(logs),
                "successful": sum(1 for l in logs if l.status == WebhookStatus.SUCCESS),
                "failed": sum(1 for l in logs if l.status == WebhookStatus.FAILED),
                "retrying": sum(1 for l in logs if l.status == WebhookStatus.RETRYING),
                "avg_delivery_time_ms": (
                    sum(l.delivery_time_ms for l in logs) / len(logs)
                    if logs else 0
                ),
            }

        return stats

    def clear_delivery_logs(self, older_than_days: int = 30) -> int:
        """
        Clear old delivery logs.

        Args:
            older_than_days: Delete logs older than this many days

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        initial_count = len(self.delivery_logs)

        self.delivery_logs = [
            log for log in self.delivery_logs
            if log.timestamp > cutoff_date
        ]

        deleted = initial_count - len(self.delivery_logs)
        logger.info(f"Cleared {deleted} delivery logs older than {older_than_days} days")
        return deleted

    def _generate_secret(self, length: int = 32) -> str:
        """Generate a random secret key for webhook signing."""
        import secrets
        return secrets.token_urlsafe(length)

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.

        Args:
            payload: The webhook payload
            secret: The webhook secret

        Returns:
            Hex-encoded signature string
        """
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def verify_signature(self, payload: Dict[str, Any], signature: str, secret: str) -> bool:
        """
        Verify a webhook signature.

        Args:
            payload: The webhook payload
            signature: The provided signature
            secret: The webhook secret

        Returns:
            True if signature is valid
        """
        expected_signature = self._generate_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)

    def export_logs_json(self, filepath: str) -> None:
        """
        Export all delivery logs to a JSON file.

        Args:
            filepath: Path to write the JSON file
        """
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_logs": len(self.delivery_logs),
            "logs": [log.to_dict() for log in self.delivery_logs],
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self.delivery_logs)} logs to {filepath}")

    def export_webhooks_json(self, filepath: str) -> None:
        """
        Export all webhook endpoints to a JSON file.

        Args:
            filepath: Path to write the JSON file
        """
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_webhooks": len(self.endpoints),
            "webhooks": [endpoint.to_dict() for endpoint in self.endpoints.values()],
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self.endpoints)} webhooks to {filepath}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize webhook manager
    webhook_manager = WebhookManager()

    # Example 1: Register webhooks
    print("=== Registering Webhooks ===")
    webhook_1 = webhook_manager.register_webhook(
        url="https://example.com/webhook",
        event_types=[
            EventType.APPLICATION_SUBMITTED,
            EventType.DECISION_MADE,
        ],
        headers={"Authorization": "Bearer token123"},
    )
    print(f"Registered webhook 1: {webhook_1}")

    webhook_2 = webhook_manager.register_webhook(
        url="https://service.com/events",
        event_types=[EventType.STATUS_CHANGED],
        custom_filter=lambda event: event["payload"].get("priority") == "high",
    )
    print(f"Registered webhook 2: {webhook_2}")

    # Example 2: List webhooks
    print("\n=== Listing Webhooks ===")
    webhooks = webhook_manager.list_webhooks()
    print(json.dumps(webhooks, indent=2, default=str))

    # Example 3: Trigger events
    print("\n=== Triggering Events ===")
    event_ids = webhook_manager.trigger_event(
        event_type=EventType.APPLICATION_SUBMITTED,
        payload={
            "application_id": "APP-001",
            "user_email": "user@example.com",
            "priority": "high",
        }
    )
    print(f"Triggered events: {event_ids}")

    # Example 4: Simulate delivery (would require actual endpoints to be running)
    print("\n=== Webhook Statistics ===")
    stats = webhook_manager.get_webhook_statistics()
    print(json.dumps(stats, indent=2, default=str))

    # Example 5: Get delivery logs
    print("\n=== Delivery Logs ===")
    logs = webhook_manager.get_delivery_logs(limit=5)
    print(f"Total delivery logs: {len(webhook_manager.delivery_logs)}")
    if logs:
        print(json.dumps(logs, indent=2, default=str))

    # Example 6: Deregister webhook
    print("\n=== Deregistering Webhook ===")
    deregistered = webhook_manager.deregister_webhook(webhook_1)
    print(f"Webhook 1 deregistered: {deregistered}")

    # Example 7: Export data
    print("\n=== Exporting Data ===")
    webhook_manager.export_webhooks_json("/tmp/webhooks.json")
    webhook_manager.export_logs_json("/tmp/logs.json")
    print("Data exported successfully")
