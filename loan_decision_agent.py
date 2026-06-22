"""
LoanDecisionAgent: Agent class that calls DecisionSynthesis MCP server tools.

This agent takes risk assessments from other agents (financial, operational, compliance,
reputational) and synthesizes a final loan decision: Approve/Reject/Review with confidence
level and explainable factors.
"""

import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums for Decision Classification
# ============================================================================


class DecisionClassification(str, Enum):
    """Classification enum for loan decisions"""
    APPROVE = "Approve"
    REJECT = "Reject"
    REVIEW = "Review"


# ============================================================================
# Exception Classes
# ============================================================================


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class AgentError(Exception):
    """Custom exception for agent operation errors."""
    pass


class MCPError(Exception):
    """Custom exception for MCP server communication errors."""
    pass


# ============================================================================
# Data Classes for Structured Output
# ============================================================================


@dataclass
class RiskAssessmentInput:
    """Input risk assessment from another agent."""
    financial_risk: float  # 0-100
    operational_risk: float  # 0-100
    compliance_risk: float  # 0-100
    reputational_risk: float  # 0-100

    def validate(self) -> None:
        """Validate risk assessment input."""
        risks = {
            "financial_risk": self.financial_risk,
            "operational_risk": self.operational_risk,
            "compliance_risk": self.compliance_risk,
            "reputational_risk": self.reputational_risk,
        }

        for risk_name, risk_value in risks.items():
            if not isinstance(risk_value, (int, float)):
                raise ValidationError(f"{risk_name} must be numeric, got {type(risk_value)}")
            if not (0 <= risk_value <= 100):
                raise ValidationError(f"{risk_name} must be 0-100, got {risk_value}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DecisionFactors:
    """Structured representation of decision factors."""
    critical_issues: bool
    mitigating_factors: bool
    requires_escalation: bool
    key_factors: List[str]

    def validate(self) -> None:
        """Validate decision factors."""
        if not isinstance(self.critical_issues, bool):
            raise ValidationError("critical_issues must be boolean")
        if not isinstance(self.mitigating_factors, bool):
            raise ValidationError("mitigating_factors must be boolean")
        if not isinstance(self.requires_escalation, bool):
            raise ValidationError("requires_escalation must be boolean")
        if not isinstance(self.key_factors, list):
            raise ValidationError("key_factors must be a list")
        if not all(isinstance(f, str) for f in self.key_factors):
            raise ValidationError("All key_factors must be strings")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LoanDecisionResult:
    """Complete loan decision result with all supporting information."""
    applicant_id: str
    classification: DecisionClassification
    risk_score: int  # 0-100
    confidence_level: float  # 0.0-1.0
    key_decision_factors: List[str]
    explanation: str
    decision_factors: DecisionFactors
    risk_assessment: RiskAssessmentInput
    timestamp: str

    def validate(self) -> None:
        """Validate decision result."""
        if not self.applicant_id or not isinstance(self.applicant_id, str):
            raise ValidationError("applicant_id must be a non-empty string")
        if not isinstance(self.classification, DecisionClassification):
            raise ValidationError("classification must be a DecisionClassification enum")
        if not (0 <= self.risk_score <= 100):
            raise ValidationError(f"risk_score must be 0-100, got {self.risk_score}")
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValidationError(f"confidence_level must be 0.0-1.0, got {self.confidence_level}")
        if not isinstance(self.key_decision_factors, list):
            raise ValidationError("key_decision_factors must be a list")
        if not isinstance(self.explanation, str) or not self.explanation:
            raise ValidationError("explanation must be a non-empty string")

        self.decision_factors.validate()
        self.risk_assessment.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "applicant_id": self.applicant_id,
            "classification": self.classification.value,
            "risk_score": self.risk_score,
            "confidence_level": self.confidence_level,
            "key_decision_factors": self.key_decision_factors,
            "explanation": self.explanation,
            "decision_factors": self.decision_factors.to_dict(),
            "risk_assessment": self.risk_assessment.to_dict(),
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


# ============================================================================
# MCP Tool Interface
# ============================================================================


class MCPToolInterface:
    """
    Abstract interface for MCP tool calls.

    Subclasses implement actual MCP communication with the DecisionSynthesis server.
    """

    async def synthesize_decision(
        self,
        financial_risk: float,
        operational_risk: float,
        compliance_risk: float,
        reputational_risk: float,
        has_critical_issues: bool,
        has_mitigating_factors: bool,
        requires_escalation: bool,
    ) -> Dict[str, Any]:
        """Call the synthesize_decision MCP tool."""
        raise NotImplementedError("Subclasses must implement synthesize_decision")

    async def get_decision_rules(self) -> Dict[str, Any]:
        """Call the get_decision_rules MCP tool."""
        raise NotImplementedError("Subclasses must implement get_decision_rules")


# ============================================================================
# Mock MCP Tool Interface (for testing)
# ============================================================================


class MockMCPToolInterface(MCPToolInterface):
    """
    Mock implementation of MCPToolInterface for testing without MCP server.
    """

    async def synthesize_decision(
        self,
        financial_risk: float,
        operational_risk: float,
        compliance_risk: float,
        reputational_risk: float,
        has_critical_issues: bool,
        has_mitigating_factors: bool,
        requires_escalation: bool,
    ) -> Dict[str, Any]:
        """Mock implementation of synthesize_decision."""
        # Calculate weighted risk score
        weights = {
            "financial": 0.35,
            "operational": 0.25,
            "compliance": 0.25,
            "reputational": 0.15,
        }

        risk_score = int(
            round(
                financial_risk * weights["financial"]
                + operational_risk * weights["operational"]
                + compliance_risk * weights["compliance"]
                + reputational_risk * weights["reputational"]
            )
        )

        # Determine classification
        if risk_score >= 85 and has_critical_issues:
            classification = "Reject"
            confidence = 0.95
        elif has_critical_issues and not has_mitigating_factors:
            classification = "Reject"
            confidence = 0.9
        elif risk_score >= 50 and requires_escalation:
            classification = "Review"
            confidence = 0.85
        elif risk_score >= 50 and has_critical_issues:
            classification = "Review"
            confidence = 0.8
        elif risk_score < 50 and not has_critical_issues:
            classification = "Approve"
            confidence = 0.95
        elif has_mitigating_factors:
            classification = "Review"
            confidence = 0.75
        else:
            classification = "Review"
            confidence = 0.7

        # Build factors list
        factors = []
        if risk_score >= 85:
            factors.append(f"Risk score {risk_score} exceeds high-risk threshold (85)")
        if has_critical_issues:
            factors.append("Critical issues identified")
        if has_mitigating_factors:
            factors.append("Mitigating factors present")
        if requires_escalation:
            factors.append("Escalation required")

        # Build explanation
        explanation_parts = [
            f"Decision: {classification}",
            f"Overall Risk Score: {risk_score}/100",
            f"Risk Breakdown:",
            f"  - Financial Risk: {financial_risk}/100",
            f"  - Operational Risk: {operational_risk}/100",
            f"  - Compliance Risk: {compliance_risk}/100",
            f"  - Reputational Risk: {reputational_risk}/100",
            "Decision Factors:",
        ]
        for factor in factors:
            explanation_parts.append(f"  - {factor}")

        explanation = "\n".join(explanation_parts)

        return {
            "classification": classification,
            "risk_score": risk_score,
            "confidence_level": confidence,
            "key_decision_factors": factors,
            "explanation": explanation,
        }

    async def get_decision_rules(self) -> Dict[str, Any]:
        """Mock implementation of get_decision_rules."""
        return {
            "risk_score_calculation": {
                "description": "Overall risk score is calculated as weighted average of component risks",
                "weights": {
                    "financial_risk": 0.35,
                    "operational_risk": 0.25,
                    "compliance_risk": 0.25,
                    "reputational_risk": 0.15,
                },
                "range": "0-100",
            },
            "classification_rules": {
                "REJECT": {
                    "conditions": [
                        "Risk score >= 85 (high risk)",
                        "Has critical unmitigable issues",
                        "Critical compliance violations",
                    ],
                    "confidence_range": "0.9-0.95",
                },
                "REVIEW": {
                    "conditions": [
                        "Risk score 50-84 (medium-high risk)",
                        "Has critical issues with mitigation possible",
                        "Requires escalation",
                        "Mixed risk profile",
                    ],
                    "confidence_range": "0.7-0.85",
                },
                "APPROVE": {
                    "conditions": [
                        "Risk score < 50 (low-medium risk)",
                        "No critical unmitigable issues",
                        "Mitigating factors present",
                    ],
                    "confidence_range": "0.9-0.95",
                },
            },
            "thresholds": {
                "low_risk": "0-49",
                "medium_high_risk": "50-84",
                "high_risk": "85-100",
            },
        }


# ============================================================================
# Real MCP Tool Interface Implementation
# ============================================================================


class RealMCPToolInterface(MCPToolInterface):
    """
    Real implementation of MCPToolInterface that calls DecisionSynthesis MCP server.

    This requires the DecisionSynthesis MCP server to be running and accessible
    via the MCP protocol (typically stdio transport).
    """

    def __init__(self, mcp_client: Any = None):
        """
        Initialize with MCP client.

        Args:
            mcp_client: Initialized MCP client that has access to DecisionSynthesis tools
        """
        self.mcp_client = mcp_client

    async def synthesize_decision(
        self,
        financial_risk: float,
        operational_risk: float,
        compliance_risk: float,
        reputational_risk: float,
        has_critical_issues: bool,
        has_mitigating_factors: bool,
        requires_escalation: bool,
    ) -> Dict[str, Any]:
        """Call the synthesize_decision MCP tool."""
        if not self.mcp_client:
            raise MCPError("MCP client not initialized")

        result = await self.mcp_client.call_tool(
            "synthesize_decision",
            {
                "financial_risk": financial_risk,
                "operational_risk": operational_risk,
                "compliance_risk": compliance_risk,
                "reputational_risk": reputational_risk,
                "has_critical_issues": has_critical_issues,
                "has_mitigating_factors": has_mitigating_factors,
                "requires_escalation": requires_escalation,
            },
        )
        return result

    async def get_decision_rules(self) -> Dict[str, Any]:
        """Call the get_decision_rules MCP tool."""
        if not self.mcp_client:
            raise MCPError("MCP client not initialized")

        result = await self.mcp_client.call_tool("get_decision_rules", {})
        return result


# ============================================================================
# LoanDecisionAgent Class
# ============================================================================


class LoanDecisionAgent:
    """
    Agent for synthesizing loan decisions based on risk assessments from other agents.

    This agent:
    - Accepts risk assessments (financial, operational, compliance, reputational)
    - Calls DecisionSynthesis MCP server tools
    - Synthesizes final decision: Approve/Reject/Review
    - Provides confidence levels and explainable factors
    - Supports batch decision making
    """

    def __init__(
        self,
        mcp_interface: Optional[MCPToolInterface] = None,
        verbose: bool = True,
    ):
        """
        Initialize the LoanDecisionAgent.

        Args:
            mcp_interface: MCPToolInterface implementation for server communication
            verbose: Enable logging of operations
        """
        self.mcp_interface = mcp_interface or MockMCPToolInterface()
        self.verbose = verbose
        self.logger = logger if verbose else None
        self.decision_rules = None

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.logger:
            self.logger.info(message)

    async def make_decision(
        self,
        applicant_id: str,
        financial_risk: float,
        operational_risk: float,
        compliance_risk: float,
        reputational_risk: float,
        has_critical_issues: bool = False,
        has_mitigating_factors: bool = False,
        requires_escalation: bool = False,
    ) -> LoanDecisionResult:
        """
        Synthesize a loan decision based on risk assessments.

        Args:
            applicant_id: Unique applicant identifier
            financial_risk: Financial risk score (0-100)
            operational_risk: Operational risk score (0-100)
            compliance_risk: Compliance risk score (0-100)
            reputational_risk: Reputational risk score (0-100)
            has_critical_issues: Whether critical issues have been identified
            has_mitigating_factors: Whether mitigating factors are present
            requires_escalation: Whether decision requires escalation

        Returns:
            LoanDecisionResult with decision, confidence, and factors

        Raises:
            AgentError: If decision synthesis fails
            ValidationError: If input validation fails
        """
        self._log(f"Starting decision synthesis for applicant {applicant_id}")

        try:
            # Validate input
            risk_assessment = RiskAssessmentInput(
                financial_risk=financial_risk,
                operational_risk=operational_risk,
                compliance_risk=compliance_risk,
                reputational_risk=reputational_risk,
            )
            risk_assessment.validate()

            self._log(f"Risk assessment validated for {applicant_id}")

            # Call MCP tool to synthesize decision
            mcp_result = await self.mcp_interface.synthesize_decision(
                financial_risk=financial_risk,
                operational_risk=operational_risk,
                compliance_risk=compliance_risk,
                reputational_risk=reputational_risk,
                has_critical_issues=has_critical_issues,
                has_mitigating_factors=has_mitigating_factors,
                requires_escalation=requires_escalation,
            )

            self._log(f"MCP synthesize_decision succeeded for {applicant_id}")

            # Parse MCP result
            classification_str = mcp_result.get("classification", "Review")
            try:
                classification = DecisionClassification(classification_str)
            except ValueError:
                raise AgentError(f"Invalid classification from MCP: {classification_str}")

            # Build decision factors
            decision_factors = DecisionFactors(
                critical_issues=has_critical_issues,
                mitigating_factors=has_mitigating_factors,
                requires_escalation=requires_escalation,
                key_factors=mcp_result.get("key_decision_factors", []),
            )
            decision_factors.validate()

            # Build decision result
            import datetime

            decision_result = LoanDecisionResult(
                applicant_id=applicant_id,
                classification=classification,
                risk_score=mcp_result.get("risk_score", 50),
                confidence_level=mcp_result.get("confidence_level", 0.7),
                key_decision_factors=mcp_result.get("key_decision_factors", []),
                explanation=mcp_result.get(
                    "explanation", "Decision synthesis completed"
                ),
                decision_factors=decision_factors,
                risk_assessment=risk_assessment,
                timestamp=datetime.datetime.utcnow().isoformat(),
            )

            # Validate result
            decision_result.validate()
            self._log(f"Decision synthesis completed for {applicant_id}: {classification.value}")

            return decision_result

        except ValidationError as e:
            raise AgentError(f"Validation error for {applicant_id}: {str(e)}")
        except MCPError as e:
            raise AgentError(f"MCP communication error for {applicant_id}: {str(e)}")
        except Exception as e:
            raise AgentError(f"Unexpected error processing {applicant_id}: {str(e)}")

    async def batch_make_decisions(
        self,
        decision_requests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesize decisions for multiple applicants in batch.

        Args:
            decision_requests: List of decision request dictionaries, each containing:
                - applicant_id: str
                - financial_risk: float
                - operational_risk: float
                - compliance_risk: float
                - reputational_risk: float
                - has_critical_issues: bool (optional)
                - has_mitigating_factors: bool (optional)
                - requires_escalation: bool (optional)

        Returns:
            Dictionary with batch results including:
                - status: success/partial_success/failure
                - total_requests: int
                - successful: int
                - failed: int
                - decisions: List[LoanDecisionResult]
                - errors: List[Dict] with request and error info

        Raises:
            AgentError: If batch processing encounters critical errors
        """
        self._log(f"Starting batch decision synthesis for {len(decision_requests)} applicants")

        decisions = []
        errors = []
        successful_count = 0
        failed_count = 0

        for idx, request in enumerate(decision_requests):
            applicant_id = request.get("applicant_id", f"UNKNOWN_{idx}")

            try:
                # Extract parameters with defaults
                result = await self.make_decision(
                    applicant_id=applicant_id,
                    financial_risk=request.get("financial_risk", 0),
                    operational_risk=request.get("operational_risk", 0),
                    compliance_risk=request.get("compliance_risk", 0),
                    reputational_risk=request.get("reputational_risk", 0),
                    has_critical_issues=request.get("has_critical_issues", False),
                    has_mitigating_factors=request.get("has_mitigating_factors", False),
                    requires_escalation=request.get("requires_escalation", False),
                )

                decisions.append(result)
                successful_count += 1

            except AgentError as e:
                failed_count += 1
                errors.append(
                    {
                        "request_index": idx,
                        "applicant_id": applicant_id,
                        "error": str(e),
                    }
                )
                self._log(f"Error processing {applicant_id}: {str(e)}")

        # Determine overall status
        if failed_count == 0:
            status = "success"
        elif successful_count > 0:
            status = "partial_success"
        else:
            status = "failure"

        # Calculate decision distribution
        approval_count = sum(
            1 for d in decisions if d.classification == DecisionClassification.APPROVE
        )
        rejection_count = sum(
            1 for d in decisions if d.classification == DecisionClassification.REJECT
        )
        review_count = sum(
            1 for d in decisions if d.classification == DecisionClassification.REVIEW
        )

        batch_result = {
            "status": status,
            "total_requests": len(decision_requests),
            "successful": successful_count,
            "failed": failed_count,
            "decisions": decisions,
            "errors": errors,
            "summary": {
                "approved": approval_count,
                "rejected": rejection_count,
                "review": review_count,
                "approval_rate": (
                    approval_count / successful_count * 100
                    if successful_count > 0
                    else 0
                ),
            },
        }

        self._log(f"Batch synthesis completed: {successful_count} success, {failed_count} failed")

        return batch_result

    async def get_decision_rules(self) -> Dict[str, Any]:
        """
        Retrieve the decision rules from the MCP server.

        Returns:
            Dictionary containing all decision rules, thresholds, and logic

        Raises:
            AgentError: If rule retrieval fails
        """
        self._log("Retrieving decision rules from MCP server")

        try:
            rules = await self.mcp_interface.get_decision_rules()
            self._log("Successfully retrieved decision rules")
            self.decision_rules = rules
            return rules
        except MCPError as e:
            raise AgentError(f"Error retrieving decision rules: {str(e)}")
        except Exception as e:
            raise AgentError(f"Unexpected error retrieving decision rules: {str(e)}")

    def get_decision_summary(self, decision: LoanDecisionResult) -> Dict[str, str]:
        """
        Get a human-readable summary of a decision.

        Args:
            decision: LoanDecisionResult to summarize

        Returns:
            Dictionary with summary fields
        """
        return {
            "Applicant ID": decision.applicant_id,
            "Decision": decision.classification.value,
            "Risk Score": f"{decision.risk_score}/100",
            "Confidence": f"{decision.confidence_level * 100:.0f}%",
            "Timestamp": decision.timestamp,
        }

    def export_decision_json(self, decision: LoanDecisionResult) -> str:
        """
        Export decision as JSON string.

        Args:
            decision: LoanDecisionResult to export

        Returns:
            JSON string representation
        """
        return decision.to_json()


# ============================================================================
# Example Usage and Testing
# ============================================================================


async def example_single_decision() -> None:
    """Example: Make a single loan decision."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: SINGLE LOAN DECISION")
    print("=" * 80)

    agent = LoanDecisionAgent(verbose=True)

    print("\nScenario: Low-risk applicant with strong profile")
    print("  - Financial Risk: 25")
    print("  - Operational Risk: 20")
    print("  - Compliance Risk: 15")
    print("  - Reputational Risk: 10")

    try:
        result = await agent.make_decision(
            applicant_id="APP_STRONG_001",
            financial_risk=25,
            operational_risk=20,
            compliance_risk=15,
            reputational_risk=10,
            has_critical_issues=False,
            has_mitigating_factors=True,
            requires_escalation=False,
        )

        print("\n" + "-" * 80)
        print("DECISION RESULT:")
        print("-" * 80)

        summary = agent.get_decision_summary(result)
        for key, value in summary.items():
            print(f"  {key:20}: {value}")

        print("\nKEY FACTORS:")
        for factor in result.key_decision_factors:
            print(f"  - {factor}")

        print("\nEXPLANATION:")
        print(result.explanation)

    except AgentError as e:
        print(f"\nError: {e}")


async def example_batch_decisions() -> None:
    """Example: Make decisions for multiple applicants."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: BATCH LOAN DECISIONS")
    print("=" * 80)

    agent = LoanDecisionAgent(verbose=True)

    applicants = [
        {
            "applicant_id": "APP_LOW_RISK_001",
            "financial_risk": 25,
            "operational_risk": 20,
            "compliance_risk": 15,
            "reputational_risk": 10,
            "has_critical_issues": False,
            "has_mitigating_factors": True,
        },
        {
            "applicant_id": "APP_MED_RISK_001",
            "financial_risk": 50,
            "operational_risk": 55,
            "compliance_risk": 45,
            "reputational_risk": 35,
            "has_critical_issues": True,
            "has_mitigating_factors": True,
            "requires_escalation": True,
        },
        {
            "applicant_id": "APP_HIGH_RISK_001",
            "financial_risk": 85,
            "operational_risk": 90,
            "compliance_risk": 88,
            "reputational_risk": 75,
            "has_critical_issues": True,
            "has_mitigating_factors": False,
        },
    ]

    print(f"\nProcessing {len(applicants)} loan applications...\n")

    try:
        result = await agent.batch_make_decisions(applicants)

        print("-" * 80)
        print("BATCH SUMMARY:")
        print("-" * 80)
        print(f"  Total Requests:  {result['total_requests']}")
        print(f"  Successful:      {result['successful']}")
        print(f"  Failed:          {result['failed']}")
        print(f"  Status:          {result['status']}")

        summary = result["summary"]
        print("\nDECISION DISTRIBUTION:")
        print(f"  Approved: {summary['approved']}")
        print(f"  Rejected: {summary['rejected']}")
        print(f"  Review:   {summary['review']}")
        print(f"  Approval Rate: {summary['approval_rate']:.1f}%")

        print("\nINDIVIDUAL DECISIONS:")
        for decision in result["decisions"]:
            risk_score = decision.risk_score
            classification = decision.classification.value
            confidence = decision.confidence_level * 100
            print(
                f"  [{decision.applicant_id}] "
                f"Risk: {risk_score:3}/100 | "
                f"Decision: {classification:8} | "
                f"Confidence: {confidence:5.0f}%"
            )

        if result["errors"]:
            print("\nERRORS:")
            for error in result["errors"]:
                print(
                    f"  [{error['applicant_id']}] {error['error']}"
                )

    except AgentError as e:
        print(f"\nError: {e}")


async def example_decision_rules() -> None:
    """Example: Retrieve decision rules."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: DECISION RULES AND THRESHOLDS")
    print("=" * 80)

    agent = LoanDecisionAgent(verbose=True)

    try:
        rules = await agent.get_decision_rules()

        print("\n" + "-" * 80)
        print("RISK SCORE CALCULATION:")
        print("-" * 80)
        calc_rules = rules["risk_score_calculation"]
        print(f"  Description: {calc_rules['description']}")
        print(f"  Range: {calc_rules['range']}")
        print("  Weights:")
        for risk_type, weight in calc_rules["weights"].items():
            print(f"    - {risk_type}: {weight * 100:.0f}%")

        print("\n" + "-" * 80)
        print("CLASSIFICATION RULES:")
        print("-" * 80)
        for classification, rules_data in rules["classification_rules"].items():
            print(f"\n  {classification}:")
            print(f"    Confidence Range: {rules_data['confidence_range']}")
            print("    Conditions:")
            for condition in rules_data["conditions"]:
                print(f"      - {condition}")

        print("\n" + "-" * 80)
        print("RISK THRESHOLDS:")
        print("-" * 80)
        for threshold_name, threshold_range in rules["thresholds"].items():
            print(f"  {threshold_name}: {threshold_range}")

    except AgentError as e:
        print(f"\nError: {e}")


async def main():
    """Main entry point for examples."""
    print("\n" + "=" * 80)
    print("LOAN DECISION AGENT - EXAMPLES")
    print("=" * 80)

    try:
        await example_single_decision()
        await example_batch_decisions()
        await example_decision_rules()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError in examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
