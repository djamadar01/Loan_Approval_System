"""
Comprehensive test suite for ComplianceOrchestratorAgent.

Demonstrates all capabilities including:
- Case ID generation
- Decision logging
- Notification dispatch
- Audit trail maintenance
- Summary generation
- Query and retrieval
"""

import json
import pytest
from typing import Dict, Any
from compliance_orchestrator_agent import (
    ComplianceOrchestratorAgent,
    DecisionType,
    ComplianceStatus,
    DecisionSummary,
    create_agent,
)


class TestComplianceOrchestratorAgent:
    """Test suite for ComplianceOrchestratorAgent."""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing."""
        return create_agent("TEST-AGENT-001")

    def test_agent_creation(self):
        """Test agent creation."""
        agent = create_agent()
        assert agent is not None
        assert agent.agent_id is not None
        assert "COMP-AGENT-" in agent.agent_id

    def test_agent_custom_id(self):
        """Test agent creation with custom ID."""
        agent = create_agent("CUSTOM-AGENT-123")
        assert agent.agent_id == "CUSTOM-AGENT-123"

    def test_process_compliant_decision(self, agent):
        """Test processing a compliant application."""
        compliance_data = {
            "compliance_score": 95,
            "rule_violations": [],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-COMPLIANT-001",
            applicant_email="compliant@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        assert summary is not None
        assert summary.compliance_status == ComplianceStatus.COMPLIANT
        assert summary.decision.decision_type == DecisionType.APPROVAL
        assert summary.decision.confidence_score == 95.0
        assert len(summary.decision.rule_violations) == 0
        assert summary.case_id is not None
        assert "NOTIF-" in summary.case_id

    def test_process_non_compliant_decision(self, agent):
        """Test processing a non-compliant application."""
        compliance_data = {
            "compliance_score": 20,
            "rule_violations": ["Tax fraud detected", "Identity mismatch"],
            "risk_factors": ["High-risk jurisdiction", "Suspicious patterns"]
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-NON-COMPLIANT-001",
            applicant_email="noncompliant@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        assert summary is not None
        assert summary.compliance_status == ComplianceStatus.NON_COMPLIANT
        assert summary.decision.decision_type == DecisionType.ESCALATION
        assert summary.decision.confidence_score == 90.0
        assert len(summary.decision.rule_violations) == 2
        assert len(summary.decision.risk_factors) == 2

    def test_process_partial_compliance_decision(self, agent):
        """Test processing a partial compliance application."""
        compliance_data = {
            "compliance_score": 65,
            "rule_violations": ["Income verification pending"],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-PARTIAL-001",
            applicant_email="partial@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        assert summary is not None
        assert summary.compliance_status == ComplianceStatus.PARTIAL_COMPLIANCE
        assert summary.decision.decision_type == DecisionType.REVIEW_REQUIRED
        assert summary.decision.confidence_score == 75.0
        assert len(summary.decision.rule_violations) == 1

    def test_case_id_generation(self, agent):
        """Test Case ID generation."""
        compliance_data = {
            "compliance_score": 85,
            "rule_violations": [],
            "risk_factors": []
        }

        summary1 = agent.process_compliance_decision(
            applicant_id="APP-001",
            applicant_email="app1@example.com",
            subject="Check 1",
            compliance_data=compliance_data
        )

        summary2 = agent.process_compliance_decision(
            applicant_id="APP-002",
            applicant_email="app2@example.com",
            subject="Check 2",
            compliance_data=compliance_data
        )

        # Case IDs should be unique
        assert summary1.case_id != summary2.case_id
        # Both should follow the format NOTIF-YYYYMMDD-XXXXXX
        assert summary1.case_id.startswith("NOTIF-")
        assert summary2.case_id.startswith("NOTIF-")

    def test_notifications_sent(self, agent):
        """Test that notifications are sent."""
        compliance_data = {
            "compliance_score": 50,
            "rule_violations": ["Minor issue"],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-NOTIF-001",
            applicant_email="notif@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        assert len(summary.notifications_sent) > 0
        # Should have at least one notification (decision notification)
        assert any(n["type"] == "decision" for n in summary.notifications_sent)

    def test_escalation_notifications(self, agent):
        """Test that escalation notifications are sent for non-compliant cases."""
        compliance_data = {
            "compliance_score": 10,
            "rule_violations": ["Major violation"],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-ESCALATE-001",
            applicant_email="escalate@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        # Should have both decision and escalation notifications
        notification_types = [n["type"] for n in summary.notifications_sent]
        assert "decision" in notification_types
        assert "escalation" in notification_types

    def test_review_notifications(self, agent):
        """Test that review notifications are sent for partial compliance."""
        compliance_data = {
            "compliance_score": 70,
            "rule_violations": ["Review needed"],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-REVIEW-001",
            applicant_email="review@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        # Should have both decision and review notifications
        notification_types = [n["type"] for n in summary.notifications_sent]
        assert "decision" in notification_types
        assert "review" in notification_types

    def test_audit_trail_logged(self, agent):
        """Test that audit trail is properly logged."""
        compliance_data = {
            "compliance_score": 80,
            "rule_violations": [],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-AUDIT-001",
            applicant_email="audit@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        audit_trail = agent.get_audit_trail(summary.case_id)
        assert len(audit_trail) > 0
        # Should have at least these actions
        actions = [entry["action"] for entry in audit_trail]
        assert "decision_processing_initiated" in actions
        assert "compliance_evaluation_completed" in actions
        assert "notifications_dispatched" in actions
        assert "decision_processing_completed" in actions

    def test_decision_summary_generation(self, agent):
        """Test decision summary generation."""
        compliance_data = {
            "compliance_score": 88,
            "rule_violations": [],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-SUMMARY-001",
            applicant_email="summary@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        assert summary.summary_text is not None
        assert summary.case_id in summary.summary_text
        assert summary.applicant_id in summary.summary_text
        assert "COMPLIANCE DECISION SUMMARY" in summary.summary_text

    def test_message_id_generation(self, agent):
        """Test message ID generation."""
        compliance_data = {
            "compliance_score": 85,
            "rule_violations": [],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-MSG-001",
            applicant_email="msg@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        assert summary.message_id is not None
        assert summary.message_id.startswith("MSG-COMP-")

    def test_get_decision_summary(self, agent):
        """Test retrieving decision summary."""
        compliance_data = {
            "compliance_score": 80,
            "rule_violations": [],
            "risk_factors": []
        }

        summary1 = agent.process_compliance_decision(
            applicant_id="APP-GET-001",
            applicant_email="get@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        case_id = summary1.case_id
        retrieved_summary = agent.get_decision_summary(case_id)

        assert retrieved_summary is not None
        assert retrieved_summary.case_id == case_id
        assert retrieved_summary.applicant_id == "APP-GET-001"

    def test_list_all_decisions(self, agent):
        """Test listing all decisions."""
        compliance_data = {
            "compliance_score": 80,
            "rule_violations": [],
            "risk_factors": []
        }

        # Process multiple decisions
        for i in range(3):
            agent.process_compliance_decision(
                applicant_id=f"APP-LIST-{i:03d}",
                applicant_email=f"app{i}@example.com",
                subject="Compliance Check",
                compliance_data=compliance_data
            )

        decisions = agent.list_all_decisions()
        assert len(decisions) >= 3

    def test_get_case_status(self, agent):
        """Test getting case status."""
        compliance_data = {
            "compliance_score": 75,
            "rule_violations": [],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-STATUS-001",
            applicant_email="status@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        case_status = agent.get_case_status(summary.case_id)
        assert case_status is not None
        assert case_status["case_id"] == summary.case_id
        assert "case_info" in case_status
        assert "audit_trail" in case_status
        assert "decision" in case_status

    def test_get_agent_statistics(self, agent):
        """Test getting agent statistics."""
        compliance_data = {
            "compliance_score": 80,
            "rule_violations": [],
            "risk_factors": []
        }

        # Process multiple decisions
        for i in range(2):
            agent.process_compliance_decision(
                applicant_id=f"APP-STATS-{i}",
                applicant_email=f"stats{i}@example.com",
                subject="Compliance Check",
                compliance_data=compliance_data
            )

        stats = agent.get_agent_statistics()
        assert stats["agent_id"] == agent.agent_id
        assert stats["total_decisions"] >= 2
        assert stats["total_audit_entries"] > 0
        assert "decision_types_distribution" in stats
        assert "compliance_status_distribution" in stats

    def test_decision_summary_validation(self, agent):
        """Test decision summary validation."""
        compliance_data = {
            "compliance_score": 80,
            "rule_violations": [],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-VALID-001",
            applicant_email="valid@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        # Should not raise an exception
        summary.validate()

    def test_decision_summary_json_export(self, agent):
        """Test exporting decision summary to JSON."""
        compliance_data = {
            "compliance_score": 85,
            "rule_violations": [],
            "risk_factors": []
        }

        summary = agent.process_compliance_decision(
            applicant_id="APP-JSON-001",
            applicant_email="json@example.com",
            subject="Compliance Check",
            compliance_data=compliance_data
        )

        json_str = summary.to_json()
        assert json_str is not None
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["case_id"] == summary.case_id
        assert parsed["applicant_id"] == "APP-JSON-001"

    def test_confidence_scores(self, agent):
        """Test confidence score calculation."""
        # Test compliant case
        compliant_data = {
            "compliance_score": 95,
            "rule_violations": [],
            "risk_factors": []
        }
        compliant_summary = agent.process_compliance_decision(
            applicant_id="APP-CONF-COMP",
            applicant_email="conf@example.com",
            subject="Check",
            compliance_data=compliant_data
        )
        assert compliant_summary.decision.confidence_score == 95.0

        # Test non-compliant case
        noncompliant_data = {
            "compliance_score": 15,
            "rule_violations": ["Issue"],
            "risk_factors": []
        }
        noncompliant_summary = agent.process_compliance_decision(
            applicant_id="APP-CONF-NON",
            applicant_email="conf@example.com",
            subject="Check",
            compliance_data=noncompliant_data
        )
        assert noncompliant_summary.decision.confidence_score == 90.0

        # Test partial compliance case
        partial_data = {
            "compliance_score": 65,
            "rule_violations": ["Issue"],
            "risk_factors": []
        }
        partial_summary = agent.process_compliance_decision(
            applicant_id="APP-CONF-PART",
            applicant_email="conf@example.com",
            subject="Check",
            compliance_data=partial_data
        )
        assert partial_summary.decision.confidence_score == 75.0


# ============================================================================
# Integration Tests
# ============================================================================

def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    agent = create_agent("E2E-TEST-AGENT")

    # Step 1: Process first decision
    data1 = {
        "compliance_score": 90,
        "rule_violations": [],
        "risk_factors": []
    }
    summary1 = agent.process_compliance_decision(
        applicant_id="APP-E2E-001",
        applicant_email="e2e1@example.com",
        subject="Initial Review",
        compliance_data=data1
    )

    case_id_1 = summary1.case_id
    assert case_id_1 is not None

    # Step 2: Retrieve case status
    case_status = agent.get_case_status(case_id_1)
    assert case_status is not None
    assert len(case_status["audit_trail"]) > 0

    # Step 3: Process second decision
    data2 = {
        "compliance_score": 30,
        "rule_violations": ["Issue 1", "Issue 2"],
        "risk_factors": ["Risk 1"]
    }
    summary2 = agent.process_compliance_decision(
        applicant_id="APP-E2E-002",
        applicant_email="e2e2@example.com",
        subject="Escalation Review",
        compliance_data=data2
    )

    case_id_2 = summary2.case_id
    assert case_id_2 != case_id_1

    # Step 4: Get agent statistics
    stats = agent.get_agent_statistics()
    assert stats["total_decisions"] == 2

    # Step 5: Export both summaries
    all_decisions = agent.list_all_decisions()
    assert len(all_decisions) == 2

    for cid, summary in all_decisions.items():
        json_export = summary.to_json()
        assert json_export is not None
        parsed = json.loads(json_export)
        assert "case_id" in parsed
        assert "decision" in parsed


# ============================================================================
# Manual Test Runner
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ComplianceOrchestratorAgent Test Suite")
    print("=" * 80)

    # Run tests with pytest if available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("\nPytest not available. Running manual tests...\n")

        # Manual test execution
        test_obj = TestComplianceOrchestratorAgent()
        agent = create_agent("MANUAL-TEST")

        tests = [
            ("Agent Creation", test_obj.test_agent_creation),
            ("Custom Agent ID", lambda: test_obj.test_agent_custom_id()),
            ("Compliant Decision", lambda: test_obj.test_process_compliant_decision(agent)),
            ("Non-Compliant Decision", lambda: test_obj.test_process_non_compliant_decision(agent)),
            ("Partial Compliance Decision", lambda: test_obj.test_process_partial_compliance_decision(agent)),
            ("Case ID Generation", lambda: test_obj.test_case_id_generation(agent)),
            ("Notifications Sent", lambda: test_obj.test_notifications_sent(agent)),
            ("Audit Trail Logged", lambda: test_obj.test_audit_trail_logged(agent)),
            ("Decision Summary Generation", lambda: test_obj.test_decision_summary_generation(agent)),
            ("Agent Statistics", lambda: test_obj.test_get_agent_statistics(agent)),
            ("End-to-End Workflow", test_end_to_end_workflow),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                test_func()
                print(f"✓ {test_name}")
                passed += 1
            except Exception as e:
                print(f"✗ {test_name}: {str(e)}")
                failed += 1

        print(f"\n{passed} passed, {failed} failed")
        print("=" * 80)
