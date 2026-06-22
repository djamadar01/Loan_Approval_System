#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced NotificationSystem

Tests:
1. Multi-channel notification delivery
2. Notification preferences
3. Escalation rules and triggering
4. Communication history tracking
5. Compliance report generation and verification
"""

import unittest
import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from notification_system_enhanced import (
    EnhancedNotificationDB,
    NotificationChannel,
    EscalationLevel,
    ComplianceFramework
)


class TestEnhancedNotificationDB(unittest.TestCase):
    """Test cases for Enhanced Notification Database."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db = EnhancedNotificationDB(self.db_path)

    def tearDown(self):
        """Clean up test database."""
        self.temp_dir.cleanup()

    def test_register_recipient(self):
        """Test recipient registration."""
        result = self.db.register_recipient(
            recipient_id="test_user_001",
            name="Test User",
            email="test@example.com",
            phone="+1-555-0001"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["recipient_id"], "test_user_001")

    def test_register_multiple_recipients(self):
        """Test registering multiple recipients."""
        recipients = [
            ("user_001", "Alice", "alice@example.com", "+1-555-0001"),
            ("user_002", "Bob", "bob@example.com", "+1-555-0002"),
            ("user_003", "Charlie", "charlie@example.com", "+1-555-0003")
        ]

        for recipient_id, name, email, phone in recipients:
            result = self.db.register_recipient(
                recipient_id=recipient_id,
                name=name,
                email=email,
                phone=phone
            )
            self.assertTrue(result["success"])

    def test_set_notification_preference_email_channel(self):
        """Test setting email notification preference."""
        # Register recipient first
        self.db.register_recipient("user_001", "Test User", "test@example.com")

        result = self.db.set_notification_preference(
            recipient_id="user_001",
            preferred_channels=["email"],
            max_notifications_per_day=50,
            escalation_enabled=True
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["preferred_channels"], ["email"])

    def test_set_notification_preference_multi_channel(self):
        """Test setting multi-channel notification preference."""
        self.db.register_recipient("user_002", "Test User", "test@example.com")

        result = self.db.set_notification_preference(
            recipient_id="user_002",
            preferred_channels=["email", "sms", "push"],
            timezone="US/Eastern",
            language="en"
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(result["preferred_channels"]), 3)

    def test_set_notification_preference_with_dnd(self):
        """Test setting do-not-disturb preferences."""
        self.db.register_recipient("user_003", "Test User", "test@example.com")

        result = self.db.set_notification_preference(
            recipient_id="user_003",
            preferred_channels=["email", "sms"],
            do_not_disturb_start="18:00",
            do_not_disturb_end="08:00"
        )

        self.assertTrue(result["success"])

    def test_get_notification_preference(self):
        """Test retrieving notification preferences."""
        self.db.register_recipient("user_004", "Test User", "test@example.com")
        self.db.set_notification_preference(
            recipient_id="user_004",
            preferred_channels=["email", "push"]
        )

        result = self.db.get_notification_preference("user_004")
        self.assertTrue(result["success"])
        self.assertEqual(result["preferences"]["recipient_id"], "user_004")
        self.assertIn("email", result["preferences"]["preferred_channels"])

    def test_get_non_existent_preference(self):
        """Test retrieving non-existent preferences."""
        result = self.db.get_notification_preference("non_existent_user")
        self.assertFalse(result["success"])

    def test_send_notification_email_channel(self):
        """Test sending notification via email."""
        self.db.register_recipient("user_005", "Test User", "user5@example.com")
        self.db.set_notification_preference(
            recipient_id="user_005",
            preferred_channels=["email"]
        )

        result = self.db.send_notification(
            recipient_id="user_005",
            channel="email",
            subject="Test Email",
            body="This is a test email notification",
            priority="normal"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "email")
        self.assertIn(result["status"], ["sent", "pending"])

    def test_send_notification_sms_channel(self):
        """Test sending notification via SMS."""
        self.db.register_recipient("user_006", "Test User", phone="+1-555-0006")
        self.db.set_notification_preference(
            recipient_id="user_006",
            preferred_channels=["sms"]
        )

        result = self.db.send_notification(
            recipient_id="user_006",
            channel="sms",
            subject="Test SMS",
            body="SMS notification test",
            priority="high"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "sms")

    def test_send_notification_push_channel(self):
        """Test sending notification via push."""
        self.db.register_recipient("user_007", "Test User")
        self.db.set_notification_preference(
            recipient_id="user_007",
            preferred_channels=["push"]
        )

        result = self.db.send_notification(
            recipient_id="user_007",
            channel="push",
            subject="Test Push",
            body="Push notification test",
            priority="normal"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "push")

    def test_send_notification_wrong_channel(self):
        """Test sending notification with channel not in preferences."""
        self.db.register_recipient("user_008", "Test User")
        self.db.set_notification_preference(
            recipient_id="user_008",
            preferred_channels=["email"]
        )

        result = self.db.send_notification(
            recipient_id="user_008",
            channel="sms",  # Not preferred
            subject="Test",
            body="This should fail",
            priority="normal"
        )

        self.assertFalse(result["success"])

    def test_add_escalation_rule_high_priority(self):
        """Test adding high priority escalation rule."""
        result = self.db.add_escalation_rule(
            priority_threshold="high",
            max_attempts=2,
            time_between_attempts=300,
            escalation_level="level_2",
            escalation_channel="sms",
            escalation_recipient="admin@example.com"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["escalation_level"], "level_2")

    def test_add_escalation_rule_critical_priority(self):
        """Test adding critical priority escalation rule."""
        result = self.db.add_escalation_rule(
            priority_threshold="critical",
            max_attempts=1,
            time_between_attempts=60,
            escalation_level="critical",
            escalation_channel="sms",
            escalation_recipient="emergency@example.com"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["priority_threshold"], "critical")

    def test_add_multiple_escalation_rules(self):
        """Test adding multiple escalation rules."""
        rules = [
            ("low", "level_1", "email"),
            ("normal", "level_1", "email"),
            ("high", "level_2", "sms"),
            ("critical", "critical", "sms")
        ]

        for priority, level, channel in rules:
            result = self.db.add_escalation_rule(
                priority_threshold=priority,
                escalation_level=level,
                escalation_channel=channel
            )
            self.assertTrue(result["success"])

    def test_check_and_escalate(self):
        """Test escalation checking."""
        # Create setup for escalation
        self.db.register_recipient("user_009", "Test User", "user9@example.com")
        self.db.set_notification_preference(
            recipient_id="user_009",
            preferred_channels=["email"],
            escalation_enabled=True
        )

        self.db.add_escalation_rule(
            priority_threshold="high",
            escalation_level="level_2",
            escalation_channel="sms"
        )

        # Send high priority notification
        notif_result = self.db.send_notification(
            recipient_id="user_009",
            channel="email",
            subject="High Priority",
            body="This needs escalation",
            priority="high"
        )

        # Check escalation
        result = self.db.check_and_escalate(notif_result["notification_id"])
        self.assertTrue(result["success"])

    def test_get_communication_history(self):
        """Test retrieving communication history."""
        self.db.register_recipient("user_010", "Test User", "user10@example.com")
        self.db.set_notification_preference(
            recipient_id="user_010",
            preferred_channels=["email", "sms", "push"]
        )

        # Send multiple notifications
        for i in range(3):
            self.db.send_notification(
                recipient_id="user_010",
                channel="email",
                subject=f"Test {i}",
                body=f"Test body {i}",
                priority="normal"
            )

        # Get history
        result = self.db.get_communication_history(
            recipient_id="user_010",
            days_back=30
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["recipient_id"], "user_010")
        self.assertGreater(result["total_entries"], 0)

    def test_generate_compliance_report_gdpr(self):
        """Test GDPR compliance report generation."""
        result = self.db.generate_compliance_report(
            framework="gdpr",
            period_days=30,
            signed_by="compliance@example.com"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["framework"], "gdpr")
        self.assertIsNotNone(result["digital_signature"])
        self.assertEqual(result["signed_by"], "compliance@example.com")

    def test_generate_compliance_report_ccpa(self):
        """Test CCPA compliance report generation."""
        result = self.db.generate_compliance_report(
            framework="ccpa",
            period_days=30,
            signed_by="compliance@example.com"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["framework"], "ccpa")

    def test_generate_compliance_report_multiple_frameworks(self):
        """Test generating reports for multiple frameworks."""
        frameworks = ["gdpr", "ccpa", "hipaa", "soc2", "iso27001"]

        for framework in frameworks:
            result = self.db.generate_compliance_report(
                framework=framework,
                period_days=30,
                signed_by="compliance@example.com"
            )
            self.assertTrue(result["success"])
            self.assertEqual(result["framework"], framework)

    def test_get_compliance_report(self):
        """Test retrieving compliance report."""
        # Generate report first
        gen_result = self.db.generate_compliance_report(
            framework="gdpr",
            period_days=30,
            signed_by="compliance@example.com"
        )

        report_id = gen_result["report_id"]

        # Retrieve report
        result = self.db.get_compliance_report(report_id)
        self.assertTrue(result["success"])
        self.assertEqual(result["report"]["report_id"], report_id)
        self.assertTrue(result["report"]["signature_valid"])

    def test_get_non_existent_compliance_report(self):
        """Test retrieving non-existent compliance report."""
        result = self.db.get_compliance_report("NON_EXISTENT_REPORT_ID")
        self.assertFalse(result["success"])

    def test_list_compliance_reports(self):
        """Test listing compliance reports."""
        # Generate multiple reports
        for framework in ["gdpr", "ccpa"]:
            self.db.generate_compliance_report(
                framework=framework,
                period_days=30,
                signed_by="compliance@example.com"
            )

        # List all reports
        result = self.db.list_compliance_reports()
        self.assertTrue(result["success"])
        self.assertGreater(result["total_reports"], 0)

    def test_list_compliance_reports_by_framework(self):
        """Test listing compliance reports filtered by framework."""
        # Generate GDPR report
        self.db.generate_compliance_report(
            framework="gdpr",
            period_days=30,
            signed_by="compliance@example.com"
        )

        # List GDPR reports
        result = self.db.list_compliance_reports(framework="gdpr")
        self.assertTrue(result["success"])

        # Verify all reports are GDPR
        for report in result["reports"]:
            self.assertEqual(report["framework"], "gdpr")

    def test_compliance_report_signature_integrity(self):
        """Test compliance report signature integrity."""
        # Generate report
        gen_result = self.db.generate_compliance_report(
            framework="soc2",
            period_days=30,
            signed_by="auditor@example.com"
        )

        original_signature = gen_result["digital_signature"]

        # Retrieve report
        get_result = self.db.get_compliance_report(gen_result["report_id"])

        # Verify signature matches
        self.assertEqual(
            get_result["report"]["digital_signature"],
            original_signature
        )

    def test_notification_with_complex_data(self):
        """Test notification with complex data scenarios."""
        self.db.register_recipient("user_011", "Test User", "user11@example.com")
        self.db.set_notification_preference(
            recipient_id="user_011",
            preferred_channels=["email", "sms"],
            max_notifications_per_day=100,
            escalation_enabled=True,
            timezone="US/Pacific",
            language="en"
        )

        # Send notification with long body
        long_body = "Test notification with complex content. " * 50
        result = self.db.send_notification(
            recipient_id="user_011",
            channel="email",
            subject="Complex Notification Test",
            body=long_body,
            priority="critical"
        )

        self.assertTrue(result["success"])

    def test_database_persistence(self):
        """Test that data persists in database."""
        # First connection: register recipient
        self.db.register_recipient("user_012", "Persist Test", "persist@example.com")
        self.db.set_notification_preference(
            recipient_id="user_012",
            preferred_channels=["email"]
        )

        # Create new connection to same database
        db2 = EnhancedNotificationDB(self.db_path)
        result = db2.get_notification_preference("user_012")

        self.assertTrue(result["success"])
        self.assertEqual(result["preferences"]["recipient_id"], "user_012")

    def test_error_handling_invalid_recipient(self):
        """Test error handling with invalid recipient."""
        result = self.db.send_notification(
            recipient_id="non_existent_user",
            channel="email",
            subject="Test",
            body="Test",
            priority="normal"
        )

        self.assertFalse(result["success"])

    def test_escalation_with_time_threshold(self):
        """Test escalation rules with time thresholds."""
        result = self.db.add_escalation_rule(
            priority_threshold="high",
            max_attempts=3,
            time_between_attempts=600,  # 10 minutes
            escalation_level="level_2",
            escalation_channel="email"
        )

        self.assertTrue(result["success"])

    def test_communication_history_time_filtering(self):
        """Test communication history with time filtering."""
        self.db.register_recipient("user_013", "Time Test", "time@example.com")
        self.db.set_notification_preference(
            recipient_id="user_013",
            preferred_channels=["email"]
        )

        # Send notification
        self.db.send_notification(
            recipient_id="user_013",
            channel="email",
            subject="Test",
            body="Test",
            priority="normal"
        )

        # Get history for last 7 days
        result = self.db.get_communication_history(
            recipient_id="user_013",
            days_back=7
        )

        self.assertTrue(result["success"])
        self.assertGreater(result["total_entries"], 0)


class TestNotificationChannels(unittest.TestCase):
    """Test notification channel functionality."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db = EnhancedNotificationDB(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_email_channel_delivery(self):
        """Test email channel delivery."""
        self.db.register_recipient("email_user", "Email Test", "test@example.com")
        self.db.set_notification_preference(
            recipient_id="email_user",
            preferred_channels=["email"]
        )

        result = self.db.send_notification(
            recipient_id="email_user",
            channel="email",
            subject="Email Test",
            body="Testing email delivery"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "email")

    def test_sms_channel_delivery(self):
        """Test SMS channel delivery."""
        self.db.register_recipient("sms_user", "SMS Test", phone="+1-555-1234")
        self.db.set_notification_preference(
            recipient_id="sms_user",
            preferred_channels=["sms"]
        )

        result = self.db.send_notification(
            recipient_id="sms_user",
            channel="sms",
            subject="SMS Test",
            body="Testing SMS delivery"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "sms")

    def test_push_channel_delivery(self):
        """Test push notification delivery."""
        self.db.register_recipient("push_user", "Push Test")
        self.db.set_notification_preference(
            recipient_id="push_user",
            preferred_channels=["push"]
        )

        result = self.db.send_notification(
            recipient_id="push_user",
            channel="push",
            subject="Push Test",
            body="Testing push delivery"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "push")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
