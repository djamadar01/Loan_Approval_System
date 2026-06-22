"""
DecisionSynthesis MCP Server using FastMCP

Provides tools for synthesizing decisions based on risk scores and applying decision logic rules.
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum
import json


# Models and Enums
class ClassificationEnum(str, Enum):
    """Classification enum for decisions"""
    APPROVE = "Approve"
    REJECT = "Reject"
    REVIEW = "Review"


class SynthesisResult(BaseModel):
    """Result model for decision synthesis"""
    classification: ClassificationEnum = Field(
        description="Decision classification: Approve, Reject, or Review"
    )
    risk_score: int = Field(
        description="Overall risk score from 0-100",
        ge=0,
        le=100
    )
    confidence_level: float = Field(
        description="Confidence level of the decision (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    key_decision_factors: List[str] = Field(
        description="List of key factors that influenced the decision"
    )
    explanation: str = Field(
        description="Detailed explanation of the decision rationale"
    )


class DecisionRuleSet:
    """Encapsulates decision logic rules"""

    @staticmethod
    def calculate_risk_score(
        financial_risk: float = 0,
        operational_risk: float = 0,
        compliance_risk: float = 0,
        reputational_risk: float = 0,
    ) -> int:
        """
        Calculate overall risk score from component risk factors.

        Args:
            financial_risk: Financial risk factor (0-100)
            operational_risk: Operational risk factor (0-100)
            compliance_risk: Compliance risk factor (0-100)
            reputational_risk: Reputational risk factor (0-100)

        Returns:
            Overall risk score (0-100)
        """
        # Weighted average: give more weight to compliance and financial risks
        weights = {
            'financial': 0.35,
            'operational': 0.25,
            'compliance': 0.25,
            'reputational': 0.15
        }

        overall_score = (
            financial_risk * weights['financial'] +
            operational_risk * weights['operational'] +
            compliance_risk * weights['compliance'] +
            reputational_risk * weights['reputational']
        )

        return min(100, max(0, int(round(overall_score))))

    @staticmethod
    def classify_decision(
        risk_score: int,
        has_critical_issues: bool = False,
        has_mitigating_factors: bool = False,
        requires_escalation: bool = False,
    ) -> tuple[ClassificationEnum, float, List[str]]:
        """
        Apply decision logic rules to classify a decision.

        Decision Rules:
        1. REJECT if:
           - Risk score >= 85 (high risk)
           - Has critical compliance issues
           - Critical issues cannot be mitigated

        2. REVIEW if:
           - Risk score 50-84 (medium-high risk)
           - Has critical issues but they can be mitigated
           - Requires escalation for approval
           - Has mixed risk profile requiring human judgment

        3. APPROVE if:
           - Risk score < 50 (low-medium risk)
           - No critical unmitigable issues
           - Mitigating factors present

        Args:
            risk_score: Overall risk score (0-100)
            has_critical_issues: Whether critical issues exist
            has_mitigating_factors: Whether mitigating factors exist
            requires_escalation: Whether decision requires escalation

        Returns:
            Tuple of (classification, confidence_level, factors)
        """
        factors = []
        confidence = 1.0

        # Rule 1: Critical rejection factors
        if risk_score >= 85:
            factors.append(f"Risk score {risk_score} exceeds high-risk threshold (85)")
            if has_critical_issues:
                factors.append("Critical unmitigable issues detected")
                confidence = 0.95
                return ClassificationEnum.REJECT, confidence, factors

        # Rule 2: Hard reject for unmitigable critical issues
        if has_critical_issues and not has_mitigating_factors:
            factors.append("Critical issues present without mitigation")
            confidence = 0.9
            return ClassificationEnum.REJECT, confidence, factors

        # Rule 3: Review required for medium-high risk
        if risk_score >= 50:
            factors.append(f"Risk score {risk_score} in medium-high range (50-84)")
            if requires_escalation:
                factors.append("Escalation required")
                confidence = 0.85
                return ClassificationEnum.REVIEW, confidence, factors

            if has_critical_issues:
                factors.append("Critical issues require review")
                confidence = 0.8
                return ClassificationEnum.REVIEW, confidence, factors

        # Rule 4: Approve for low risk with no critical issues
        if risk_score < 50:
            factors.append(f"Risk score {risk_score} within acceptable range")
            if not has_critical_issues:
                factors.append("No critical issues identified")
                confidence = 0.95
                return ClassificationEnum.APPROVE, confidence, factors

        # Rule 5: Default to Review if mitigating factors present
        if has_mitigating_factors:
            factors.append("Mitigating factors present, recommend review")
            confidence = 0.75
            return ClassificationEnum.REVIEW, confidence, factors

        # Default fallback
        factors.append("Default review classification applied")
        confidence = 0.7
        return ClassificationEnum.REVIEW, confidence, factors


# Initialize FastMCP server
mcp = FastMCP("DecisionSynthesis")


@mcp.tool()
def synthesize_decision(
    financial_risk: float = Field(
        default=0,
        description="Financial risk score (0-100)",
        ge=0,
        le=100
    ),
    operational_risk: float = Field(
        default=0,
        description="Operational risk score (0-100)",
        ge=0,
        le=100
    ),
    compliance_risk: float = Field(
        default=0,
        description="Compliance risk score (0-100)",
        ge=0,
        le=100
    ),
    reputational_risk: float = Field(
        default=0,
        description="Reputational risk score (0-100)",
        ge=0,
        le=100
    ),
    has_critical_issues: bool = Field(
        default=False,
        description="Whether critical issues have been identified"
    ),
    has_mitigating_factors: bool = Field(
        default=False,
        description="Whether mitigating factors are present"
    ),
    requires_escalation: bool = Field(
        default=False,
        description="Whether the decision requires escalation"
    ),
) -> SynthesisResult:
    """
    Synthesize a decision based on risk scores and decision logic rules.

    This tool evaluates multiple risk factors (financial, operational, compliance,
    reputational) and applies decision logic to produce a classification with
    supporting factors and confidence levels.

    Returns:
        SynthesisResult containing classification, risk score, confidence level,
        key decision factors, and explanation.
    """

    # Calculate overall risk score
    risk_score = DecisionRuleSet.calculate_risk_score(
        financial_risk=financial_risk,
        operational_risk=operational_risk,
        compliance_risk=compliance_risk,
        reputational_risk=reputational_risk,
    )

    # Classify decision
    classification, confidence, factors = DecisionRuleSet.classify_decision(
        risk_score=risk_score,
        has_critical_issues=has_critical_issues,
        has_mitigating_factors=has_mitigating_factors,
        requires_escalation=requires_escalation,
    )

    # Build explanation
    explanation_parts = [
        f"Decision: {classification.value}",
        f"Overall Risk Score: {risk_score}/100",
        f"Risk Breakdown:",
        f"  - Financial Risk: {financial_risk}/100",
        f"  - Operational Risk: {operational_risk}/100",
        f"  - Compliance Risk: {compliance_risk}/100",
        f"  - Reputational Risk: {reputational_risk}/100",
    ]

    if has_critical_issues:
        explanation_parts.append("Status: Critical issues identified")

    if has_mitigating_factors:
        explanation_parts.append("Status: Mitigating factors present")

    if requires_escalation:
        explanation_parts.append("Status: Escalation required")

    explanation_parts.append("Decision Factors:")
    for factor in factors:
        explanation_parts.append(f"  - {factor}")

    explanation = "\n".join(explanation_parts)

    return SynthesisResult(
        classification=classification,
        risk_score=risk_score,
        confidence_level=confidence,
        key_decision_factors=factors,
        explanation=explanation,
    )


@mcp.tool()
def get_decision_rules() -> dict:
    """
    Retrieve the complete decision rule set and logic.

    Returns:
        Dictionary containing all decision rules, thresholds, and logic.
    """
    rules = {
        "risk_score_calculation": {
            "description": "Overall risk score is calculated as weighted average of component risks",
            "weights": {
                "financial_risk": 0.35,
                "operational_risk": 0.25,
                "compliance_risk": 0.25,
                "reputational_risk": 0.15,
            },
            "range": "0-100"
        },
        "classification_rules": {
            "REJECT": {
                "conditions": [
                    "Risk score >= 85 (high risk)",
                    "Has critical unmitigable issues",
                    "Critical compliance violations"
                ],
                "confidence_range": "0.9-0.95"
            },
            "REVIEW": {
                "conditions": [
                    "Risk score 50-84 (medium-high risk)",
                    "Has critical issues with mitigation possible",
                    "Requires escalation",
                    "Mixed risk profile"
                ],
                "confidence_range": "0.7-0.85"
            },
            "APPROVE": {
                "conditions": [
                    "Risk score < 50 (low-medium risk)",
                    "No critical unmitigable issues",
                    "Mitigating factors present"
                ],
                "confidence_range": "0.9-0.95"
            }
        },
        "thresholds": {
            "low_risk": "0-49",
            "medium_high_risk": "50-84",
            "high_risk": "85-100"
        }
    }

    return rules


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
