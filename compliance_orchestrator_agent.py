"""
ComplianceOrchestratorAgent: Agent class that calls NotificationSystem MCP server tools.

This agent handles compliance orchestration with comprehensive decision logging,
notification dispatch, audit trail maintenance, and structured output generation
including Case ID generation and decision summaries.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timezone
import uuid

# Import the NotificationSystem tools
from notification_system_mcp import (
    NotificationService,
    CaseIDManager,
    AuditTrailManager,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================


class DecisionType(Enum):
    """Types of compliance decisions."""
    APPROVAL = "approval"
    REJECTION = "rejection"
    ESCALATION = "escalation"
    REVIEW_REQUIRED = "review_required"
    PENDING = "pending"


class ComplianceStatus(Enum):
    """Status of compliance evaluation."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL_COMPLIANCE = "partial_compliance"
    UNKNOWN = "unknown"


class NotificationType(Enum):
    """Types of notifications to send."""
    DECISION = "decision"
    ALERT = "alert"
    REVIEW = "review"
    ESCALATION = "escalation"
    AUDIT = "audit"


# ============================================================================
# Data Validation and Error Handling
# ============================================================================


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class AgentError(Exception):
    """Custom exception for agent operation errors."""
    pass


# ============================================================================
# Data Classes for Structured Output
# ============================================================================


@dataclass
class ComplianceDecision:
    """Represents a compliance decision."""
    decision_type: DecisionType
    rationale: str
    confidence_score: float  # 0-100
    rule_violations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate compliance decision."""
        if not isinstance(self.decision_type, DecisionType):
            raise ValidationError(f"Invalid decision type: {self.decision_type}")
        if not self.rationale or not isinstance(self.rationale, str):
            raise ValidationError("Rationale must be a non-empty string")
        if not (0 <= self.confidence_score <= 100):
            raise ValidationError(f"Confidence score must be 0-100, got {self.confidence_score}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["decision_type"] = self.decision_type.value
        return data


@dataclass
class AuditTrailEntry:
    """Represents an audit trail entry."""
    timestamp: str
    action: str
    actor: str
    case_id: str
    details: Dict[str, Any]
    result: str

    def validate(self) -> None:
        """Validate audit trail entry."""
        if not self.timestamp or not isinstance(self.timestamp, str):
            raise ValidationError("Timestamp must be a non-empty string")
        if not self.action or not isinstance(self.action, str):
            raise ValidationError("Action must be a non-empty string")
        if self.result not in ["success", "failure", "pending"]:
            raise ValidationError(f"Invalid result: {self.result}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DecisionSummary:
    """Structured summary of compliance decision."""
    case_id: str
    timestamp: str
    subject: str
    applicant_id: str
    compliance_status: ComplianceStatus
    decision: ComplianceDecision
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)
    audit_entries: List[AuditTrailEntry] = field(default_factory=list)
    message_id: Optional[str] = None
    summary_text: Optional[str] = None

    def validate(self) -> None:
        """Validate decision summary."""
        if not self.case_id or not isinstance(self.case_id, str):
            raise ValidationError("Case ID must be a non-empty string")
        if not self.applicant_id or not isinstance(self.applicant_id, str):
            raise ValidationError("Applicant ID must be a non-empty string")
        if not isinstance(self.compliance_status, ComplianceStatus):
            raise ValidationError(f"Invalid compliance status: {self.compliance_status}")

        self.decision.validate()
        for entry in self.audit_entries:
            entry.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "case_id": self.case_id,
            "timestamp": self.timestamp,
            "subject": self.subject,
            "applicant_id": self.applicant_id,
            "compliance_status": self.compliance_status.value,
            "decision": self.decision.to_dict(),
            "notifications_sent": self.notifications_sent,
            "audit_entries": [entry.to_dict() for entry in self.audit_entries],
            "message_id": self.message_id,
            "summary_text": self.summary_text
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


# ============================================================================
# ComplianceOrchestratorAgent
# ============================================================================


class ComplianceOrchestratorAgent:
    """Agent for orchestrating compliance decisions and notifications."""

    def __init__(
        self,
        agent_id: str = "COMPLIANCE-AGENT-001",
        notification_service: Optional[NotificationService] = None
    ):
        """Initialize the ComplianceOrchestratorAgent.

        Args:
            agent_id: Unique identifier for this agent
            notification_service: NotificationService instance (creates if None)
        """
        self.agent_id = agent_id
        self.notification_service = notification_service or NotificationService()
        self.case_id_manager = self.notification_service.case_id_manager
        self.audit_trail_manager = self.notification_service.audit_trail_manager
        self.decision_history: Dict[str, DecisionSummary] = {}

        logger.info(f"ComplianceOrchestratorAgent initialized: {self.agent_id}")

    # ========================================================================
    # Main Orchestration Methods
    # ========================================================================

    def process_compliance_decision(
        self,
        applicant_id: str,
        applicant_email: str,
        subject: str,
        compliance_data: Dict[str, Any],
        decision_criteria: Optional[Dict[str, Any]] = None
    ) -> DecisionSummary:
        """Process a compliance decision and coordinate notifications.

        Args:
            applicant_id: ID of the applicant
            applicant_email: Email of the applicant
            subject: Subject of the decision
            compliance_data: Compliance data for evaluation
            decision_criteria: Criteria for decision making

        Returns:
            DecisionSummary with case ID and decision details
        """
        try:
            # Generate Case ID
            case_id = self.case_id_manager.generate_case_id()
            timestamp = datetime.now(timezone.utc).isoformat()

            logger.info(
                f"Processing compliance decision - Case ID: {case_id}, "
                f"Applicant: {applicant_id}"
            )

            # Log decision initiation
            self._log_action(
                case_id=case_id,
                action="decision_processing_initiated",
                details={
                    "applicant_id": applicant_id,
                    "subject": subject,
                },
                result="pending"
            )

            # Evaluate compliance
            compliance_status, decision = self._evaluate_compliance(
                case_id=case_id,
                applicant_id=applicant_id,
                compliance_data=compliance_data,
                decision_criteria=decision_criteria
            )

            # Create decision summary
            summary = DecisionSummary(
                case_id=case_id,
                timestamp=timestamp,
                subject=subject,
                applicant_id=applicant_id,
                compliance_status=compliance_status,
                decision=decision
            )

            # Register case ID
            self.case_id_manager.register_case_id(
                case_id=case_id,
                recipient=applicant_email,
                subject=subject,
                notification_type="compliance_decision"
            )

            # Send notifications
            notifications = self._send_notifications(
                case_id=case_id,
                applicant_email=applicant_email,
                decision=decision,
                summary=summary
            )
            summary.notifications_sent = notifications

            # Generate summary text
            summary_text = self._generate_decision_summary(
                case_id=case_id,
                applicant_id=applicant_id,
                compliance_status=compliance_status,
                decision=decision,
                timestamp=timestamp
            )
            summary.summary_text = summary_text
            summary.message_id = self._generate_message_id()

            # Log decision completion
            self._log_action(
                case_id=case_id,
                action="decision_processing_completed",
                details={
                    "compliance_status": compliance_status.value,
                    "decision_type": decision.decision_type.value,
                    "notifications_count": len(notifications)
                },
                result="success"
            )

            # Store in history
            self.decision_history[case_id] = summary

            # Validate summary
            summary.validate()

            logger.info(
                f"Compliance decision processed successfully - Case ID: {case_id}, "
                f"Status: {compliance_status.value}"
            )

            return summary

        except Exception as e:
            logger.error(f"Error processing compliance decision: {str(e)}")
            raise AgentError(f"Failed to process compliance decision: {str(e)}")

    # ========================================================================
    # Compliance Evaluation
    # ========================================================================

    def _evaluate_compliance(
        self,
        case_id: str,
        applicant_id: str,
        compliance_data: Dict[str, Any],
        decision_criteria: Optional[Dict[str, Any]] = None
    ) -> tuple[ComplianceStatus, ComplianceDecision]:
        """Evaluate compliance based on provided data.

        Args:
            case_id: Case ID for this evaluation
            applicant_id: Applicant ID
            compliance_data: Data to evaluate
            decision_criteria: Optional criteria for evaluation

        Returns:
            Tuple of (ComplianceStatus, ComplianceDecision)
        """
        criteria = decision_criteria or {}

        # Extract compliance factors
        violations = compliance_data.get("rule_violations", [])
        risk_factors = compliance_data.get("risk_factors", [])
        compliance_score = compliance_data.get("compliance_score", 0)

        # Determine compliance status
        if not violations and compliance_score >= 80:
            compliance_status = ComplianceStatus.COMPLIANT
            decision_type = DecisionType.APPROVAL
            confidence = 95.0
        elif len(violations) <= 2 and compliance_score >= 60:
            compliance_status = ComplianceStatus.PARTIAL_COMPLIANCE
            decision_type = DecisionType.REVIEW_REQUIRED
            confidence = 75.0
        elif violations or compliance_score < 40:
            compliance_status = ComplianceStatus.NON_COMPLIANT
            decision_type = DecisionType.ESCALATION
            confidence = 90.0
        else:
            compliance_status = ComplianceStatus.UNKNOWN
            decision_type = DecisionType.PENDING
            confidence = 50.0

        # Generate rationale
        rationale = self._generate_compliance_rationale(
            compliance_score=compliance_score,
            violations=violations,
            risk_factors=risk_factors,
            criteria=criteria
        )

        # Create decision
        decision = ComplianceDecision(
            decision_type=decision_type,
            rationale=rationale,
            confidence_score=confidence,
            rule_violations=violations,
            risk_factors=risk_factors,
            metadata=compliance_data
        )

        # Log evaluation
        self._log_action(
            case_id=case_id,
            action="compliance_evaluation_completed",
            details={
                "compliance_score": compliance_score,
                "violations_count": len(violations),
                "risk_factors_count": len(risk_factors),
                "decision_type": decision_type.value,
                "confidence": confidence
            },
            result="success"
        )

        return compliance_status, decision

    def _generate_compliance_rationale(
        self,
        compliance_score: float,
        violations: List[str],
        risk_factors: List[str],
        criteria: Dict[str, Any]
    ) -> str:
        """Generate rationale for compliance decision.

        Args:
            compliance_score: Overall compliance score
            violations: List of rule violations
            risk_factors: List of risk factors
            criteria: Decision criteria

        Returns:
            Rationale text
        """
        factors = [f"Compliance Score: {compliance_score:.1f}/100"]

        if violations:
            factors.append(f"Violations: {len(violations)} identified ({', '.join(violations)})")
        else:
            factors.append("No violations detected")

        if risk_factors:
            factors.append(f"Risk Factors: {', '.join(risk_factors)}")
        else:
            factors.append("No significant risk factors")

        return "; ".join(factors)

    # ========================================================================
    # Notification Methods
    # ========================================================================

    def _send_notifications(
        self,
        case_id: str,
        applicant_email: str,
        decision: ComplianceDecision,
        summary: DecisionSummary
    ) -> List[Dict[str, Any]]:
        """Send notifications based on decision.

        Args:
            case_id: Case ID
            applicant_email: Recipient email
            decision: The compliance decision
            summary: Decision summary

        Returns:
            List of notification details
        """
        notifications = []

        try:
            # Send primary decision notification
            primary_notification = self._send_decision_notification(
                case_id=case_id,
                applicant_email=applicant_email,
                decision=decision,
                summary=summary
            )
            notifications.append(primary_notification)

            # Send supplementary alerts based on decision type
            if decision.decision_type == DecisionType.ESCALATION:
                escalation_notification = self._send_escalation_notification(
                    case_id=case_id,
                    applicant_email=applicant_email,
                    decision=decision
                )
                notifications.append(escalation_notification)

            elif decision.decision_type == DecisionType.REVIEW_REQUIRED:
                review_notification = self._send_review_notification(
                    case_id=case_id,
                    applicant_email=applicant_email,
                    decision=decision
                )
                notifications.append(review_notification)

            # Log notification dispatch
            self._log_action(
                case_id=case_id,
                action="notifications_dispatched",
                details={
                    "notification_count": len(notifications),
                    "recipient": applicant_email
                },
                result="success"
            )

        except Exception as e:
            logger.error(f"Error sending notifications for case {case_id}: {str(e)}")
            self._log_action(
                case_id=case_id,
                action="notifications_dispatch_failed",
                details={"error": str(e)},
                result="failure"
            )

        return notifications

    def _send_decision_notification(
        self,
        case_id: str,
        applicant_email: str,
        decision: ComplianceDecision,
        summary: DecisionSummary
    ) -> Dict[str, Any]:
        """Send primary decision notification.

        Args:
            case_id: Case ID
            applicant_email: Recipient email
            decision: Compliance decision
            summary: Decision summary

        Returns:
            Notification response
        """
        subject = f"Compliance Decision - Case {case_id}"

        priority_map = {
            DecisionType.APPROVAL: "normal",
            DecisionType.REJECTION: "high",
            DecisionType.ESCALATION: "critical",
            DecisionType.REVIEW_REQUIRED: "high",
            DecisionType.PENDING: "normal"
        }
        priority = priority_map.get(decision.decision_type, "normal")

        message = f"""
Compliance Decision Notification

Case ID: {case_id}
Status: {summary.compliance_status.value}
Decision Type: {decision.decision_type.value}
Confidence Score: {decision.confidence_score:.1f}%

Rationale:
{decision.rationale}

Rule Violations: {len(decision.rule_violations)}
Risk Factors: {len(decision.risk_factors)}

This notification has been automatically generated by the Compliance Orchestrator Agent.
For questions or appeals, please contact the compliance team with your Case ID.
"""

        metadata = {
            "case_id": case_id,
            "decision_type": decision.decision_type.value,
            "compliance_status": summary.compliance_status.value,
            "confidence_score": decision.confidence_score,
            "violations_count": len(decision.rule_violations),
            "risk_factors_count": len(decision.risk_factors)
        }

        response = self.notification_service.send_notification(
            recipient=applicant_email,
            subject=subject,
            message=message,
            notification_type="decision",
            priority=priority,
            metadata=metadata
        )

        logger.info(f"Decision notification sent for case {case_id}")

        return {
            "type": "decision",
            "case_id": case_id,
            "recipient": applicant_email,
            "response": response.model_dump(mode="json"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _send_escalation_notification(
        self,
        case_id: str,
        applicant_email: str,
        decision: ComplianceDecision
    ) -> Dict[str, Any]:
        """Send escalation notification for non-compliant cases.

        Args:
            case_id: Case ID
            applicant_email: Recipient email
            decision: Compliance decision

        Returns:
            Notification response
        """
        subject = f"Compliance Escalation Required - Case {case_id}"

        message = f"""
Compliance Escalation Notice

Case ID: {case_id}
Decision Type: {decision.decision_type.value}
Priority Level: CRITICAL

The compliance evaluation has identified issues requiring escalation.
A compliance officer will contact you within 24 hours.

Identified Issues:
{json.dumps(decision.rule_violations, indent=2)}

Please have your Case ID ready for reference.
"""

        response = self.notification_service.send_notification(
            recipient=applicant_email,
            subject=subject,
            message=message,
            notification_type="escalation",
            priority="critical",
            metadata={
                "case_id": case_id,
                "violations": decision.rule_violations
            }
        )

        logger.info(f"Escalation notification sent for case {case_id}")

        return {
            "type": "escalation",
            "case_id": case_id,
            "recipient": applicant_email,
            "response": response.model_dump(mode="json"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _send_review_notification(
        self,
        case_id: str,
        applicant_email: str,
        decision: ComplianceDecision
    ) -> Dict[str, Any]:
        """Send review notification for partial compliance cases.

        Args:
            case_id: Case ID
            applicant_email: Recipient email
            decision: Compliance decision

        Returns:
            Notification response
        """
        subject = f"Compliance Review Required - Case {case_id}"

        message = f"""
Compliance Review Notice

Case ID: {case_id}
Status: REVIEW REQUIRED
Priority Level: HIGH

Your application requires additional review by our compliance team.
We will contact you within 48 hours with next steps.

Items Requiring Review:
{json.dumps(decision.rule_violations, indent=2)}

Please keep your Case ID for reference.
"""

        response = self.notification_service.send_notification(
            recipient=applicant_email,
            subject=subject,
            message=message,
            notification_type="review",
            priority="high",
            metadata={
                "case_id": case_id,
                "violations": decision.rule_violations
            }
        )

        logger.info(f"Review notification sent for case {case_id}")

        return {
            "type": "review",
            "case_id": case_id,
            "recipient": applicant_email,
            "response": response.model_dump(mode="json"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ========================================================================
    # Audit Trail Methods
    # ========================================================================

    def _log_action(
        self,
        case_id: str,
        action: str,
        details: Dict[str, Any],
        result: str = "success"
    ) -> None:
        """Log an action to the audit trail.

        Args:
            case_id: Associated case ID
            action: Action performed
            details: Details about the action
            result: Result of action (success, failure, pending)
        """
        try:
            self.audit_trail_manager.log_action(
                case_id=case_id,
                action=action,
                details=details,
                actor=self.agent_id,
                result=result
            )
        except Exception as e:
            logger.error(f"Error logging action for case {case_id}: {str(e)}")

    def get_audit_trail(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieve audit trail for a case.

        Args:
            case_id: Case ID

        Returns:
            List of audit entries
        """
        try:
            return self.audit_trail_manager.get_audit_trail(case_id)
        except Exception as e:
            logger.error(f"Error retrieving audit trail for case {case_id}: {str(e)}")
            return []

    def get_all_audit_entries(self) -> List[Dict[str, Any]]:
        """Retrieve all audit entries.

        Returns:
            List of all audit entries
        """
        try:
            return self.audit_trail_manager.get_all_audit_entries()
        except Exception as e:
            logger.error(f"Error retrieving all audit entries: {str(e)}")
            return []

    # ========================================================================
    # Summary Generation Methods
    # ========================================================================

    def _generate_decision_summary(
        self,
        case_id: str,
        applicant_id: str,
        compliance_status: ComplianceStatus,
        decision: ComplianceDecision,
        timestamp: str
    ) -> str:
        """Generate a comprehensive decision summary.

        Args:
            case_id: Case ID
            applicant_id: Applicant ID
            compliance_status: Compliance status
            decision: Compliance decision
            timestamp: Timestamp of decision

        Returns:
            Summary text
        """
        summary = f"""
COMPLIANCE DECISION SUMMARY
==========================

Case ID: {case_id}
Applicant ID: {applicant_id}
Timestamp: {timestamp}
Compliance Status: {compliance_status.value}
Decision Type: {decision.decision_type.value}
Confidence Score: {decision.confidence_score:.1f}%

Decision Rationale:
{decision.rationale}

Rule Violations: {len(decision.rule_violations)}
"""
        if decision.rule_violations:
            summary += "\n  - " + "\n  - ".join(decision.rule_violations)

        summary += f"\n\nRisk Factors: {len(decision.risk_factors)}"
        if decision.risk_factors:
            summary += "\n  - " + "\n  - ".join(decision.risk_factors)

        summary += "\n\nAudit Trail: Available for review"
        summary += f"\n\nGenerated by: {self.agent_id}"

        return summary

    def _generate_message_id(self) -> str:
        """Generate a unique message ID.

        Returns:
            Message ID
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_component = str(uuid.uuid4().hex[:6]).upper()
        return f"MSG-COMP-{timestamp}-{random_component}"

    # ========================================================================
    # Query and Retrieval Methods
    # ========================================================================

    def get_decision_summary(self, case_id: str) -> Optional[DecisionSummary]:
        """Retrieve a decision summary by case ID.

        Args:
            case_id: Case ID

        Returns:
            DecisionSummary or None
        """
        return self.decision_history.get(case_id)

    def list_all_decisions(self) -> Dict[str, DecisionSummary]:
        """List all decisions processed by this agent.

        Returns:
            Dictionary of case IDs and decision summaries
        """
        return self.decision_history.copy()

    def get_case_status(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive status for a case.

        Args:
            case_id: Case ID

        Returns:
            Case status information
        """
        try:
            case_info = self.case_id_manager.get_case_info(case_id)
            audit_trail = self.get_audit_trail(case_id)
            decision = self.decision_history.get(case_id)

            if not case_info:
                return None

            return {
                "case_id": case_id,
                "case_info": case_info,
                "audit_trail": audit_trail,
                "audit_entries_count": len(audit_trail),
                "decision": decision.to_dict() if decision else None
            }
        except Exception as e:
            logger.error(f"Error getting case status for {case_id}: {str(e)}")
            return None

    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about this agent's operations.

        Returns:
            Agent statistics
        """
        all_decisions = self.list_all_decisions()
        all_audit_entries = self.get_all_audit_entries()

        decision_types = {}
        compliance_statuses = {}

        for summary in all_decisions.values():
            dt = summary.decision.decision_type.value
            decision_types[dt] = decision_types.get(dt, 0) + 1

            cs = summary.compliance_status.value
            compliance_statuses[cs] = compliance_statuses.get(cs, 0) + 1

        return {
            "agent_id": self.agent_id,
            "total_decisions": len(all_decisions),
            "total_audit_entries": len(all_audit_entries),
            "decision_types_distribution": decision_types,
            "compliance_status_distribution": compliance_statuses,
            "audit_log_path": str(self.audit_trail_manager.log_file),
            "case_id_log_path": str(self.case_id_manager.log_file)
        }


# ============================================================================
# Utility Functions
# ============================================================================


def create_agent(agent_id: Optional[str] = None) -> ComplianceOrchestratorAgent:
    """Factory function to create a ComplianceOrchestratorAgent.

    Args:
        agent_id: Optional agent ID

    Returns:
        ComplianceOrchestratorAgent instance
    """
    if not agent_id:
        random_component = str(uuid.uuid4().hex[:6]).upper()
        agent_id = f"COMP-AGENT-{random_component}"

    return ComplianceOrchestratorAgent(agent_id=agent_id)


# ============================================================================
# Main Entry Point for Testing
# ============================================================================

def main():
    """Main entry point for testing the agent."""
    import sys

    print("=" * 80)
    print("ComplianceOrchestratorAgent - Test Demo")
    print("=" * 80)

    # Create agent
    agent = create_agent()
    print(f"\nAgent created: {agent.agent_id}")

    # Example 1: Process compliant application
    print("\n[1] Processing compliant application...")
    compliance_data_1 = {
        "compliance_score": 95,
        "rule_violations": [],
        "risk_factors": []
    }

    decision_summary_1 = agent.process_compliance_decision(
        applicant_id="APP-001",
        applicant_email="applicant1@example.com",
        subject="Compliance Review - Application APP-001",
        compliance_data=compliance_data_1
    )

    print(f"\nDecision Summary:")
    print(f"  Case ID: {decision_summary_1.case_id}")
    print(f"  Status: {decision_summary_1.compliance_status.value}")
    print(f"  Decision: {decision_summary_1.decision.decision_type.value}")
    print(f"  Confidence: {decision_summary_1.decision.confidence_score:.1f}%")
    print(f"  Notifications Sent: {len(decision_summary_1.notifications_sent)}")

    # Example 2: Process non-compliant application
    print("\n[2] Processing non-compliant application...")
    compliance_data_2 = {
        "compliance_score": 25,
        "rule_violations": ["Missing tax documentation", "Income verification failed"],
        "risk_factors": ["Insufficient funds", "Employment gap"]
    }

    decision_summary_2 = agent.process_compliance_decision(
        applicant_id="APP-002",
        applicant_email="applicant2@example.com",
        subject="Compliance Review - Application APP-002",
        compliance_data=compliance_data_2
    )

    print(f"\nDecision Summary:")
    print(f"  Case ID: {decision_summary_2.case_id}")
    print(f"  Status: {decision_summary_2.compliance_status.value}")
    print(f"  Decision: {decision_summary_2.decision.decision_type.value}")
    print(f"  Confidence: {decision_summary_2.decision.confidence_score:.1f}%")
    print(f"  Violations: {len(decision_summary_2.decision.rule_violations)}")
    print(f"  Notifications Sent: {len(decision_summary_2.notifications_sent)}")

    # Example 3: Process partial compliance application
    print("\n[3] Processing partial compliance application...")
    compliance_data_3 = {
        "compliance_score": 65,
        "rule_violations": ["Income verification pending"],
        "risk_factors": ["Recent job change"]
    }

    decision_summary_3 = agent.process_compliance_decision(
        applicant_id="APP-003",
        applicant_email="applicant3@example.com",
        subject="Compliance Review - Application APP-003",
        compliance_data=compliance_data_3
    )

    print(f"\nDecision Summary:")
    print(f"  Case ID: {decision_summary_3.case_id}")
    print(f"  Status: {decision_summary_3.compliance_status.value}")
    print(f"  Decision: {decision_summary_3.decision.decision_type.value}")
    print(f"  Confidence: {decision_summary_3.decision.confidence_score:.1f}%")
    print(f"  Notifications Sent: {len(decision_summary_3.notifications_sent)}")

    # Example 4: Retrieve case status
    print(f"\n[4] Retrieving case status for {decision_summary_1.case_id}...")
    case_status = agent.get_case_status(decision_summary_1.case_id)
    if case_status:
        print(f"  Case Info: {json.dumps(case_status['case_info'], indent=2, default=str)}")
        print(f"  Audit Entries: {case_status['audit_entries_count']}")

    # Example 5: Get agent statistics
    print("\n[5] Agent Statistics:")
    stats = agent.get_agent_statistics()
    print(f"  Total Decisions: {stats['total_decisions']}")
    print(f"  Total Audit Entries: {stats['total_audit_entries']}")
    print(f"  Decision Types: {json.dumps(stats['decision_types_distribution'], indent=2)}")
    print(f"  Compliance Status Distribution: {json.dumps(stats['compliance_status_distribution'], indent=2)}")

    # Example 6: Export full decision summaries
    print("\n[6] Decision Summaries:")
    for case_id, summary in agent.list_all_decisions().items():
        print(f"\n  Case ID: {case_id}")
        print(f"  Full JSON:")
        print(f"  {summary.to_json()}")

    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
