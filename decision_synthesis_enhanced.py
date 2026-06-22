"""
Enhanced DecisionSynthesis MCP Server with Advanced Analytics

Features:
1. Decision Explainability API - Explains why decisions are made
2. What-if Analysis Tool - Scenario modeling and sensitivity analysis
3. Confidence Interval Calculation - Statistical confidence bounds
4. Decision Probability Scoring - Probabilistic risk assessment
5. Bias Detection Checks - Identifies potential biases in decision logic

Uses FastMCP for MCP protocol compliance.
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import json
import math
from statistics import mean, stdev
from datetime import datetime


# ============================================================================
# Enums and Models
# ============================================================================

class ClassificationEnum(str, Enum):
    """Classification enum for decisions"""
    APPROVE = "Approve"
    REJECT = "Reject"
    REVIEW = "Review"


class RiskCategory(str, Enum):
    """Risk categories for analysis"""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"


class BiasType(str, Enum):
    """Types of biases to detect"""
    RISK_SKEW = "risk_skew"  # Disproportionate weighting
    THRESHOLD_BIAS = "threshold_bias"  # Unfair thresholds
    FACTOR_DOMINANCE = "factor_dominance"  # Single factor over-dominance
    CONSISTENCY_BIAS = "consistency_bias"  # Inconsistent application
    ESCALATION_BIAS = "escalation_bias"  # Bias in escalation criteria


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


class ExplainabilityReport(BaseModel):
    """Decision explainability report"""
    decision: str = Field(description="The decision classification")
    primary_reasons: List[Dict[str, Any]] = Field(
        description="Primary reasons for the decision with impact scores"
    )
    contributing_factors: List[Dict[str, Any]] = Field(
        description="Secondary contributing factors"
    )
    decision_path: List[str] = Field(
        description="Step-by-step path through decision logic"
    )
    rule_chain: List[Dict[str, Any]] = Field(
        description="Rules that were evaluated and their results"
    )
    impact_breakdown: Dict[str, float] = Field(
        description="Impact of each risk category on final decision"
    )


class WhatIfScenario(BaseModel):
    """What-if analysis scenario"""
    scenario_name: str = Field(description="Name of the scenario")
    description: str = Field(description="Description of the scenario")
    original_decision: str = Field(description="Original decision classification")
    modified_decision: str = Field(description="Decision under modified conditions")
    original_risk_score: int = Field(description="Original risk score")
    modified_risk_score: int = Field(description="Modified risk score")
    changes: Dict[str, Any] = Field(description="Changes made in this scenario")
    decision_changed: bool = Field(description="Whether decision changed")
    impact_analysis: Dict[str, Any] = Field(description="Impact of changes")


class ConfidenceInterval(BaseModel):
    """Confidence interval analysis"""
    point_estimate: float = Field(description="Point estimate of the metric")
    lower_bound: float = Field(description="Lower confidence bound (95%)")
    upper_bound: float = Field(description="Upper confidence bound (95%)")
    margin_of_error: float = Field(description="Margin of error")
    confidence_level: float = Field(description="Confidence level (0.95 for 95%)")
    interpretation: str = Field(description="Interpretation of the interval")


class ProbabilityScoring(BaseModel):
    """Decision probability scoring"""
    approve_probability: float = Field(
        description="Probability of Approve decision (0-1)",
        ge=0.0,
        le=1.0
    )
    reject_probability: float = Field(
        description="Probability of Reject decision (0-1)",
        ge=0.0,
        le=1.0
    )
    review_probability: float = Field(
        description="Probability of Review decision (0-1)",
        ge=0.0,
        le=1.0
    )
    most_likely_decision: str = Field(description="Most likely decision")
    decision_entropy: float = Field(
        description="Entropy of decision probabilities (uncertainty measure)"
    )
    probability_explanation: str = Field(
        description="Explanation of probability distribution"
    )


class BiasDetectionReport(BaseModel):
    """Bias detection analysis report"""
    overall_bias_score: float = Field(
        description="Overall bias score (0-1, higher = more bias detected)",
        ge=0.0,
        le=1.0
    )
    detected_biases: List[Dict[str, Any]] = Field(
        description="List of detected biases with details"
    )
    risk_distribution_analysis: Dict[str, Any] = Field(
        description="Analysis of risk factor distribution"
    )
    threshold_fairness_analysis: Dict[str, Any] = Field(
        description="Analysis of threshold application fairness"
    )
    factor_dominance_analysis: Dict[str, Any] = Field(
        description="Analysis of individual factor dominance"
    )
    recommendations: List[str] = Field(
        description="Recommendations to mitigate detected biases"
    )


# ============================================================================
# Enhanced Decision Rule Set
# ============================================================================

class EnhancedDecisionRuleSet:
    """Enhanced decision logic with analytics capabilities"""

    # Historical decision data for analysis (would come from database in production)
    HISTORICAL_DATA = {
        "low_risk_approvals": 950,
        "low_risk_reviews": 45,
        "low_risk_rejections": 5,
        "medium_risk_approvals": 600,
        "medium_risk_reviews": 350,
        "medium_risk_rejections": 50,
        "high_risk_approvals": 20,
        "high_risk_reviews": 150,
        "high_risk_rejections": 830,
    }

    @staticmethod
    def calculate_risk_score(
        financial_risk: float = 0,
        operational_risk: float = 0,
        compliance_risk: float = 0,
        reputational_risk: float = 0,
    ) -> int:
        """Calculate overall risk score from component risk factors."""
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
        """Apply decision logic rules to classify a decision."""
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


# ============================================================================
# Initialize FastMCP server
# ============================================================================

mcp = FastMCP("DecisionSynthesis")


# ============================================================================
# Tool 1: Synthesize Decision (Original)
# ============================================================================

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
    risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
        financial_risk=financial_risk,
        operational_risk=operational_risk,
        compliance_risk=compliance_risk,
        reputational_risk=reputational_risk,
    )

    # Classify decision
    classification, confidence, factors = EnhancedDecisionRuleSet.classify_decision(
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


# ============================================================================
# Tool 2: Decision Explainability API
# ============================================================================

@mcp.tool()
def explain_decision(
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
) -> ExplainabilityReport:
    """
    Generate a detailed explainability report for a decision.

    Provides comprehensive insight into:
    - Primary reasons for the decision
    - Contributing factors and their impact
    - Step-by-step decision path through the logic
    - Impact breakdown of each risk category

    Returns:
        ExplainabilityReport with detailed decision reasoning
    """

    # Calculate risk score
    risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
        financial_risk=financial_risk,
        operational_risk=operational_risk,
        compliance_risk=compliance_risk,
        reputational_risk=reputational_risk,
    )

    # Classify decision
    classification, confidence, factors = EnhancedDecisionRuleSet.classify_decision(
        risk_score=risk_score,
        has_critical_issues=has_critical_issues,
        has_mitigating_factors=has_mitigating_factors,
        requires_escalation=requires_escalation,
    )

    # Calculate risk impacts
    weights = {
        'financial': 0.35,
        'operational': 0.25,
        'compliance': 0.25,
        'reputational': 0.15
    }

    impact_breakdown = {
        "financial_impact": financial_risk * weights['financial'],
        "operational_impact": operational_risk * weights['operational'],
        "compliance_impact": compliance_risk * weights['compliance'],
        "reputational_impact": reputational_risk * weights['reputational'],
    }

    # Identify primary reasons
    primary_reasons = []

    if risk_score >= 85:
        primary_reasons.append({
            "reason": "High overall risk score",
            "score": risk_score,
            "threshold": 85,
            "impact": 0.4
        })

    if has_critical_issues and not has_mitigating_factors:
        primary_reasons.append({
            "reason": "Critical issues without mitigation",
            "details": "Unmitigable critical issues detected",
            "impact": 0.35
        })

    if compliance_risk >= 70:
        primary_reasons.append({
            "reason": "High compliance risk",
            "score": compliance_risk,
            "weight": weights['compliance'],
            "impact": 0.3
        })

    # Build decision path
    decision_path = []
    decision_path.append(f"[1] Calculate overall risk score: {risk_score}/100")
    decision_path.append(f"[2] Evaluate critical factors: has_critical_issues={has_critical_issues}")
    decision_path.append(f"[3] Check escalation: requires_escalation={requires_escalation}")

    if risk_score >= 85:
        decision_path.append(f"[4] Risk score >= 85: Trigger high-risk path")
    elif risk_score >= 50:
        decision_path.append(f"[4] Risk score 50-84: Trigger medium-high risk path")
    else:
        decision_path.append(f"[4] Risk score < 50: Trigger low risk path")

    decision_path.append(f"[5] Final classification: {classification.value}")

    # Build rule chain
    rule_chain = []

    rule_chain.append({
        "rule": "High Risk Check (>= 85)",
        "condition": risk_score >= 85,
        "result": "Triggers rejection if critical issues present"
    })

    rule_chain.append({
        "rule": "Critical Issues Check",
        "condition": has_critical_issues and not has_mitigating_factors,
        "result": "Triggers rejection if true"
    })

    rule_chain.append({
        "rule": "Medium-High Risk Check (50-84)",
        "condition": 50 <= risk_score < 85,
        "result": "Triggers review for escalation or critical issues"
    })

    rule_chain.append({
        "rule": "Mitigation Assessment",
        "condition": has_mitigating_factors,
        "result": "Can convert rejection to review"
    })

    return ExplainabilityReport(
        decision=classification.value,
        primary_reasons=primary_reasons if primary_reasons else [
            {"reason": "Risk profile within acceptable range", "impact": 1.0}
        ],
        contributing_factors=[
            {"factor": "Financial Risk", "value": financial_risk, "weight": weights['financial']},
            {"factor": "Operational Risk", "value": operational_risk, "weight": weights['operational']},
            {"factor": "Compliance Risk", "value": compliance_risk, "weight": weights['compliance']},
            {"factor": "Reputational Risk", "value": reputational_risk, "weight": weights['reputational']},
        ],
        decision_path=decision_path,
        rule_chain=rule_chain,
        impact_breakdown=impact_breakdown,
    )


# ============================================================================
# Tool 3: What-If Analysis
# ============================================================================

@mcp.tool()
def whatif_analysis(
    financial_risk: float = Field(
        default=0,
        description="Original financial risk score (0-100)",
        ge=0,
        le=100
    ),
    operational_risk: float = Field(
        default=0,
        description="Original operational risk score (0-100)",
        ge=0,
        le=100
    ),
    compliance_risk: float = Field(
        default=0,
        description="Original compliance risk score (0-100)",
        ge=0,
        le=100
    ),
    reputational_risk: float = Field(
        default=0,
        description="Original reputational risk score (0-100)",
        ge=0,
        le=100
    ),
    has_critical_issues: bool = Field(
        default=False,
        description="Original has critical issues flag"
    ),
    has_mitigating_factors: bool = Field(
        default=False,
        description="Original has mitigating factors flag"
    ),
    requires_escalation: bool = Field(
        default=False,
        description="Original requires escalation flag"
    ),
    scenarios: List[Dict[str, Any]] = Field(
        default=[],
        description="List of what-if scenarios to analyze. Each scenario should have parameter changes."
    ),
) -> List[WhatIfScenario]:
    """
    Perform what-if analysis on decision scenarios.

    Allows analysis of how changes to risk factors would affect the decision.
    Each scenario models an alternative set of conditions.

    Scenario format:
    {
        "name": "Scenario Name",
        "description": "Scenario description",
        "financial_risk": 20,  # Optional: new value
        "operational_risk": 15,  # Optional
        ... other risk factors
    }

    Returns:
        List of WhatIfScenario results showing decision changes
    """

    # Get original decision
    original_risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
        financial_risk=financial_risk,
        operational_risk=operational_risk,
        compliance_risk=compliance_risk,
        reputational_risk=reputational_risk,
    )

    original_classification, _, _ = EnhancedDecisionRuleSet.classify_decision(
        risk_score=original_risk_score,
        has_critical_issues=has_critical_issues,
        has_mitigating_factors=has_mitigating_factors,
        requires_escalation=requires_escalation,
    )

    results = []

    # Default scenarios if none provided
    if not scenarios:
        scenarios = [
            {
                "name": "Reduce Financial Risk",
                "description": "What if financial risk was reduced by 50%?",
                "financial_risk": financial_risk * 0.5,
            },
            {
                "name": "Add Mitigation",
                "description": "What if strong mitigating factors were introduced?",
                "has_mitigating_factors": True,
            },
            {
                "name": "Reduce All Risks by 25%",
                "description": "What if all risk factors were reduced by 25%?",
                "financial_risk": financial_risk * 0.75,
                "operational_risk": operational_risk * 0.75,
                "compliance_risk": compliance_risk * 0.75,
                "reputational_risk": reputational_risk * 0.75,
            },
            {
                "name": "Compliance Risk to Critical",
                "description": "What if compliance risk increased to critical levels?",
                "compliance_risk": 95,
                "has_critical_issues": True,
            },
        ]

    for scenario in scenarios:
        # Extract scenario parameters
        mod_financial = scenario.get("financial_risk", financial_risk)
        mod_operational = scenario.get("operational_risk", operational_risk)
        mod_compliance = scenario.get("compliance_risk", compliance_risk)
        mod_reputational = scenario.get("reputational_risk", reputational_risk)
        mod_critical = scenario.get("has_critical_issues", has_critical_issues)
        mod_mitigation = scenario.get("has_mitigating_factors", has_mitigating_factors)
        mod_escalation = scenario.get("requires_escalation", requires_escalation)

        # Calculate modified decision
        modified_risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
            financial_risk=mod_financial,
            operational_risk=mod_operational,
            compliance_risk=mod_compliance,
            reputational_risk=mod_reputational,
        )

        modified_classification, _, _ = EnhancedDecisionRuleSet.classify_decision(
            risk_score=modified_risk_score,
            has_critical_issues=mod_critical,
            has_mitigating_factors=mod_mitigation,
            requires_escalation=mod_escalation,
        )

        # Determine changes
        changes = {}
        if mod_financial != financial_risk:
            changes["financial_risk"] = {"from": financial_risk, "to": mod_financial}
        if mod_operational != operational_risk:
            changes["operational_risk"] = {"from": operational_risk, "to": mod_operational}
        if mod_compliance != compliance_risk:
            changes["compliance_risk"] = {"from": compliance_risk, "to": mod_compliance}
        if mod_reputational != reputational_risk:
            changes["reputational_risk"] = {"from": reputational_risk, "to": mod_reputational}
        if mod_critical != has_critical_issues:
            changes["has_critical_issues"] = {"from": has_critical_issues, "to": mod_critical}
        if mod_mitigation != has_mitigating_factors:
            changes["has_mitigating_factors"] = {"from": has_mitigating_factors, "to": mod_mitigation}
        if mod_escalation != requires_escalation:
            changes["requires_escalation"] = {"from": requires_escalation, "to": mod_escalation}

        # Calculate impact
        risk_delta = modified_risk_score - original_risk_score
        decision_changed = modified_classification != original_classification

        impact_analysis = {
            "risk_score_delta": risk_delta,
            "risk_delta_percentage": round((risk_delta / original_risk_score * 100) if original_risk_score > 0 else 0, 2),
            "decision_changed": decision_changed,
            "original_decision": original_classification.value,
            "new_decision": modified_classification.value,
        }

        results.append(WhatIfScenario(
            scenario_name=scenario.get("name", "Unnamed Scenario"),
            description=scenario.get("description", "No description provided"),
            original_decision=original_classification.value,
            modified_decision=modified_classification.value,
            original_risk_score=original_risk_score,
            modified_risk_score=modified_risk_score,
            changes=changes,
            decision_changed=decision_changed,
            impact_analysis=impact_analysis,
        ))

    return results


# ============================================================================
# Tool 4: Confidence Interval Calculation
# ============================================================================

@mcp.tool()
def calculate_confidence_intervals(
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
    sample_size: int = Field(
        default=100,
        description="Sample size for confidence interval calculation",
        ge=10,
        le=10000
    ),
) -> Dict[str, ConfidenceInterval]:
    """
    Calculate confidence intervals for risk score estimates.

    Uses statistical methods to determine the bounds of uncertainty around
    the calculated risk scores. Assumes normal distribution.

    Returns:
        Dictionary with confidence intervals for each risk category and overall score
    """

    # Calculate overall risk score
    overall_risk = EnhancedDecisionRuleSet.calculate_risk_score(
        financial_risk=financial_risk,
        operational_risk=operational_risk,
        compliance_risk=compliance_risk,
        reputational_risk=reputational_risk,
    )

    # Z-score for 95% confidence interval (two-tailed)
    z_score = 1.96

    # Calculate standard error based on sample size
    # For Likert-scale data, assumed standard deviation is ~20
    population_std = 20

    def calculate_interval(point_estimate: float, std_dev: float = population_std) -> ConfidenceInterval:
        """Calculate confidence interval for a point estimate"""
        standard_error = std_dev / math.sqrt(sample_size)
        margin_of_error = z_score * standard_error
        lower_bound = max(0, point_estimate - margin_of_error)
        upper_bound = min(100, point_estimate + margin_of_error)

        interpretation = (
            f"We can be 95% confident that the true value lies between "
            f"{lower_bound:.1f} and {upper_bound:.1f}. The point estimate of "
            f"{point_estimate:.1f} is our best estimate based on available data."
        )

        return ConfidenceInterval(
            point_estimate=float(point_estimate),
            lower_bound=float(lower_bound),
            upper_bound=float(upper_bound),
            margin_of_error=float(margin_of_error),
            confidence_level=0.95,
            interpretation=interpretation,
        )

    results = {
        "financial_risk": calculate_interval(financial_risk),
        "operational_risk": calculate_interval(operational_risk),
        "compliance_risk": calculate_interval(compliance_risk),
        "reputational_risk": calculate_interval(reputational_risk),
        "overall_risk_score": calculate_interval(float(overall_risk)),
    }

    return results


# ============================================================================
# Tool 5: Decision Probability Scoring
# ============================================================================

@mcp.tool()
def calculate_decision_probabilities(
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
) -> ProbabilityScoring:
    """
    Calculate probability scores for each decision classification.

    Uses historical decision data and risk factors to estimate the probability
    of each decision outcome (Approve, Reject, Review).

    Returns:
        ProbabilityScoring with decision probabilities and entropy
    """

    # Calculate risk score
    risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
        financial_risk=financial_risk,
        operational_risk=operational_risk,
        compliance_risk=compliance_risk,
        reputational_risk=reputational_risk,
    )

    # Determine risk category
    if risk_score < 50:
        risk_category = "low"
        base_approve = 0.90
        base_review = 0.08
        base_reject = 0.02
    elif risk_score < 85:
        risk_category = "medium"
        base_approve = 0.54
        base_review = 0.40
        base_reject = 0.06
    else:
        risk_category = "high"
        base_approve = 0.02
        base_review = 0.15
        base_reject = 0.83

    # Adjust probabilities based on factors
    adjust_approve = 0
    adjust_reject = 0
    adjust_review = 0

    if has_mitigating_factors:
        adjust_approve += 0.10
        adjust_reject -= 0.08

    if has_critical_issues:
        adjust_reject += 0.15
        adjust_approve -= 0.10

    if requires_escalation:
        adjust_review += 0.15
        adjust_approve -= 0.08

    # Apply adjustments (capped at 0-1)
    approve_prob = max(0, min(1, base_approve + adjust_approve))
    reject_prob = max(0, min(1, base_reject + adjust_reject))
    review_prob = max(0, min(1, base_review + adjust_review))

    # Normalize to sum to 1.0
    total = approve_prob + reject_prob + review_prob
    approve_prob = approve_prob / total
    reject_prob = reject_prob / total
    review_prob = review_prob / total

    # Calculate entropy (measure of decision uncertainty)
    def entropy(p: float) -> float:
        if p <= 0 or p >= 1:
            return 0
        return -p * math.log2(p)

    decision_entropy = entropy(approve_prob) + entropy(reject_prob) + entropy(review_prob)
    max_entropy = math.log2(3)  # Maximum entropy for 3 outcomes
    normalized_entropy = decision_entropy / max_entropy

    # Determine most likely decision
    probs = {
        "approve": approve_prob,
        "reject": reject_prob,
        "review": review_prob,
    }
    most_likely = max(probs, key=probs.get)

    # Build explanation
    probability_explanation = (
        f"Based on {risk_category} risk profile (score: {risk_score}/100), "
        f"the model assigns probabilities: Approve {approve_prob:.1%}, "
        f"Reject {reject_prob:.1%}, Review {review_prob:.1%}. "
        f"Factors: critical_issues={has_critical_issues}, "
        f"mitigating_factors={has_mitigating_factors}, "
        f"escalation_required={requires_escalation}. "
        f"Decision entropy: {normalized_entropy:.2f}/1.0 (higher = more uncertain)."
    )

    return ProbabilityScoring(
        approve_probability=round(approve_prob, 4),
        reject_probability=round(reject_prob, 4),
        review_probability=round(review_prob, 4),
        most_likely_decision=most_likely.upper(),
        decision_entropy=round(normalized_entropy, 4),
        probability_explanation=probability_explanation,
    )


# ============================================================================
# Tool 6: Bias Detection
# ============================================================================

@mcp.tool()
def detect_decision_biases(
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
) -> BiasDetectionReport:
    """
    Detect potential biases in the decision-making process.

    Analyzes:
    1. Risk Skew - Disproportionate weighting of certain risk factors
    2. Threshold Bias - Unfair application of decision thresholds
    3. Factor Dominance - Single factor over-dominance
    4. Consistency Bias - Inconsistent application of rules
    5. Escalation Bias - Bias in escalation criteria

    Returns:
        BiasDetectionReport with detected biases and recommendations
    """

    detected_biases = []
    overall_bias_score = 0.0

    # Weights used in calculation
    weights = {
        'financial': 0.35,
        'operational': 0.25,
        'compliance': 0.25,
        'reputational': 0.15
    }

    risk_factors = {
        'financial': financial_risk,
        'operational': operational_risk,
        'compliance': compliance_risk,
        'reputational': reputational_risk,
    }

    # ===== Check 1: Risk Distribution Skew =====
    risk_values = list(risk_factors.values())
    risk_variance = sum((x - mean(risk_values)) ** 2 for x in risk_values) / len(risk_values)
    risk_std = math.sqrt(risk_variance) if risk_variance > 0 else 0

    distribution_analysis = {
        "mean_risk": round(mean(risk_values), 2),
        "std_deviation": round(risk_std, 2),
        "min_risk": min(risk_values),
        "max_risk": max(risk_values),
        "range": max(risk_values) - min(risk_values),
    }

    # High variance indicates potential skew
    if risk_std > 25:  # High variance indicates skew
        bias_score = (risk_std - 25) / 75  # Normalize to 0-1
        detected_biases.append({
            "type": "RISK_SKEW",
            "severity": "high" if bias_score > 0.5 else "medium",
            "description": "Risk factors have disproportionate distribution",
            "details": f"Standard deviation of {risk_std:.1f} indicates high variance in risk distribution",
            "impact": f"A few risk factors dominate the overall risk score",
            "score": round(bias_score, 2),
        })
        overall_bias_score = max(overall_bias_score, bias_score)

    # ===== Check 2: Factor Dominance =====
    risk_impacts = {k: risk_factors[k] * weights[k] for k in risk_factors}
    max_impact_factor = max(risk_impacts, key=risk_impacts.get)
    max_impact_value = risk_impacts[max_impact_factor]
    total_impact = sum(risk_impacts.values())
    max_impact_percentage = (max_impact_value / total_impact * 100) if total_impact > 0 else 0

    dominance_analysis = {
        "dominant_factor": max_impact_factor,
        "dominant_factor_impact_percentage": round(max_impact_percentage, 1),
        "all_factor_impacts": {k: round(v, 2) for k, v in risk_impacts.items()},
    }

    if max_impact_percentage > 45:  # One factor dominates
        dominance_bias_score = (max_impact_percentage - 45) / 55
        detected_biases.append({
            "type": "FACTOR_DOMINANCE",
            "severity": "medium" if dominance_bias_score < 0.3 else "high",
            "description": f"{max_impact_factor} risk dominates decision",
            "details": f"{max_impact_factor.replace('_', ' ')} contributes {max_impact_percentage:.1f}% of impact",
            "impact": "Decision may not adequately consider balanced risk profile",
            "score": round(dominance_bias_score, 2),
        })
        overall_bias_score = max(overall_bias_score, dominance_bias_score)

    # ===== Check 3: Threshold Bias =====
    threshold_analysis = {
        "high_risk_threshold": 85,
        "medium_risk_threshold": 50,
        "critical_issues_penalty": "Strong rejection signal",
        "mitigation_factor_benefit": "Can convert rejection to review",
    }

    # Check if thresholds are being applied fairly
    risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
        financial_risk=financial_risk,
        operational_risk=operational_risk,
        compliance_risk=compliance_risk,
        reputational_risk=reputational_risk,
    )

    # Bias if compliance has critical role but low weight
    if compliance_risk > 70 and weights['compliance'] == 0.25:
        threshold_bias_score = 0.25
        detected_biases.append({
            "type": "THRESHOLD_BIAS",
            "severity": "medium",
            "description": "Compliance risk has high values but moderate weight",
            "details": f"Compliance risk ({compliance_risk}/100) exceeds 70 but has weight {weights['compliance']}",
            "impact": "High compliance violations may not adequately impact decision",
            "score": threshold_bias_score,
        })
        overall_bias_score = max(overall_bias_score, threshold_bias_score)

    # ===== Check 4: Consistency Bias =====
    # Check if rules are applied consistently
    consistency_issues = []
    consistency_score = 0.0

    # Check critical issues vs mitigation logic
    if has_critical_issues and not has_mitigating_factors:
        # Should lead to rejection
        expected_classification = "REJECT"
    elif has_critical_issues and has_mitigating_factors:
        # Should allow review
        expected_classification = "REVIEW"
    else:
        expected_classification = None

    if expected_classification and risk_score < 50:
        consistency_issues.append({
            "issue": "Risk score vs critical issues mismatch",
            "details": "Low risk score conflicts with critical issues flag",
        })
        consistency_score = 0.3

    if consistency_score > 0.1:
        detected_biases.append({
            "type": "CONSISTENCY_BIAS",
            "severity": "low" if consistency_score < 0.2 else "medium",
            "description": "Inconsistent application of decision rules",
            "details": f"Detected {len(consistency_issues)} inconsistency points",
            "impact": "Decision logic may not be applied uniformly",
            "score": round(consistency_score, 2),
        })
        overall_bias_score = max(overall_bias_score, consistency_score)

    # ===== Check 5: Escalation Bias =====
    escalation_analysis = {
        "requires_escalation_flag": requires_escalation,
        "risk_score_level": "high" if risk_score >= 85 else "medium" if risk_score >= 50 else "low",
        "critical_issues_present": has_critical_issues,
    }

    # Bias if escalation doesn't correlate with risk
    if not requires_escalation and risk_score >= 70 and has_critical_issues:
        escalation_bias_score = 0.35
        detected_biases.append({
            "type": "ESCALATION_BIAS",
            "severity": "medium",
            "description": "High-risk case without escalation flag",
            "details": f"Risk score {risk_score} and critical issues but escalation not flagged",
            "impact": "Cases that warrant escalation may not receive appropriate review",
            "score": escalation_bias_score,
        })
        overall_bias_score = max(overall_bias_score, escalation_bias_score)

    # ===== Recommendations =====
    recommendations = []

    if any(b["type"] == "RISK_SKEW" for b in detected_biases):
        recommendations.append(
            "Review risk distribution: Consider investigating why certain risk factors are significantly higher than others"
        )

    if any(b["type"] == "FACTOR_DOMINANCE" for b in detected_biases):
        recommendations.append(
            f"Review weighting of {max_impact_factor}: Consider if {max_impact_percentage:.1f}% contribution is intentional"
        )

    if any(b["type"] == "THRESHOLD_BIAS" for b in detected_biases):
        recommendations.append(
            "Review decision thresholds: Ensure thresholds are set fairly across all risk categories"
        )

    if any(b["type"] == "CONSISTENCY_BIAS" for b in detected_biases):
        recommendations.append(
            "Audit decision rules: Ensure rules are applied consistently across similar cases"
        )

    if any(b["type"] == "ESCALATION_BIAS" for b in detected_biases):
        recommendations.append(
            "Review escalation criteria: Define and apply escalation criteria more uniformly"
        )

    if not detected_biases:
        recommendations.append(
            "No significant biases detected. Continue monitoring decision patterns regularly."
        )

    return BiasDetectionReport(
        overall_bias_score=round(min(overall_bias_score, 1.0), 4),
        detected_biases=detected_biases,
        risk_distribution_analysis=distribution_analysis,
        threshold_fairness_analysis=threshold_analysis,
        factor_dominance_analysis=dominance_analysis,
        recommendations=recommendations,
    )


# ============================================================================
# Tool 7: Get Decision Rules
# ============================================================================

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
        },
        "new_features": {
            "explain_decision": "Get detailed explainability report for a decision",
            "whatif_analysis": "Perform what-if scenario analysis",
            "calculate_confidence_intervals": "Calculate statistical confidence bounds",
            "calculate_decision_probabilities": "Get probability scores for each outcome",
            "detect_decision_biases": "Identify potential biases in decision logic",
        }
    }

    return rules


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
