#!/usr/bin/env python3
"""
Comprehensive Test Suite for NotificationSystem MCP Server.
Tests all four core tools and database functionality.
"""

import unittest
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from notification_system_server import AuditDatabase


class TestAuditDatabase(unittest.TestCase):
    """Test suite for AuditDatabase class."""

    def setUp(self):
        """Set up in-memory database for testing."""
        self.db = AuditDatabase(db_path=":memory:")

    def test_case_id_format(self):
        """Test that generated Case IDs have correct format."""
        case_id = self.db.create_case_id()
        parts = case_id.split("-")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "CASE")
        self.assertEqual(len(parts[1]), 8)
        self.assertEqual(len(parts[2]), 8)
        self.assertEqual(len(parts[3]), 4)

    def test_case_id_uniqueness(self):
        """Test that Case IDs are unique."""
        ids = set()
        for _ in range(100):
            case_id = self.db.create_case_id()
            self.assertNotIn(case_id, ids)
            ids.add(case_id)

    def test_create_case_record_success(self):
        """Test successful case record creation."""
        result = self.db.create_case_record(
            case_type="COMPLAINT",
            subject="Test complaint"
        )
        self.assertTrue(result["success"])
        self.assertIn("case_id", result)
        self.assertEqual(result["status"], "OPEN")

    def test_send_notification_success(self):
        """Test successful notification sending."""
        case = self.db.create_case_record(
            case_type="COMPLAINT",
            subject="Notification test"
        )
        case_id = case["case_id"]

        result = self.db.send_decision_notification(
            case_id=case_id,
            recipient_email="test@example.com",
            notification_type="DECISION",
            subject="Your case decision",
            body="We have made a decision on your case."
        )
        self.assertTrue(result["success"])
        self.assertIn("notification_id", result)

    def test_log_compliance_action_success(self):
        """Test successful compliance action logging."""
        case = self.db.create_case_record(
            case_type="COMPLAINT",
            subject="Compliance test"
        )
        case_id = case["case_id"]

        result = self.db.log_compliance_action(
            case_id=case_id,
            action_type="REVIEW",
            regulation="GDPR",
            actor="compliance_officer_01",
            description="Conducted data protection review"
        )
        self.assertTrue(result["success"])
        self.assertIn("COMP-", result["action_id"])

    def test_generate_summary_report_basic(self):
        """Test basic summary report generation."""
        result = self.db.generate_summary_report()
        self.assertTrue(result["success"])
        self.assertIn("report", result)

    def test_end_to_end_workflow(self):
        """Test complete workflow."""
        case_result = self.db.create_case_record(
            case_type="COMPLAINT",
            subject="E2E workflow test",
            priority="HIGH"
        )
        self.assertTrue(case_result["success"])
        case_id = case_result["case_id"]

        notif_result = self.db.send_decision_notification(
            case_id=case_id,
            recipient_email="customer@example.com",
            notification_type="UPDATE",
            subject="Your case status",
            body="We are reviewing your complaint."
        )
        self.assertTrue(notif_result["success"])

        comp_result = self.db.log_compliance_action(
            case_id=case_id,
            action_type="REVIEW",
            regulation="CCPA",
            actor="compliance_team",
            description="Privacy rights review completed"
        )
        self.assertTrue(comp_result["success"])

        report_result = self.db.generate_summary_report()
        self.assertTrue(report_result["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
