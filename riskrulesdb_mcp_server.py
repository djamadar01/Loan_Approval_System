#!/usr/bin/env python3
"""
Production RiskRulesDB MCP Server
Comprehensive financial risk assessment and regulatory compliance engine
Features: configurable thresholds, multiple calculation methods, statistical anomaly detection, regulatory compliance
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, asdict, field
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import statistics
from enum import Enum

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP package not installed. Install with: pip install fastmcp")
    sys.exit(1)


# ============================================================================
# Configuration and Constants
# ============================================================================

@dataclass
class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyType(Enum):
    """Types of detected anomalies"""
    SPENDING_SPIKE = "spending_spike"
    UNUSUAL_PATTERN = "unusual_pattern"
    HIGH_VELOCITY = "high_velocity"
    ACCOUNT_AGE = "account_age"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    INCOME_VARIANCE = "income_variance"


@dataclass
class DebtToIncomeResult:
    """Result of debt-to-income calculation"""
    ratio: float
    risk_level: str
    total_monthly_debt: float
    gross_monthly_income: float
    calculation_method: str
    meets_lending_standards: bool
    industry_comparison: Dict[str, Any]


@dataclass
class CreditScoreRiskResult:
    """Result of credit score risk assessment"""
    credit_score: int
    risk_level: str
    category: str
    percentile: float
    industry_benchmarks: Dict[str, Any]
    risk_factors: List[str]
    recommendation: str


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection"""
    anomalies_detected: List[Dict[str, Any]]
    risk_score: float
    summary: str
    recommended_actions: List[str]


@dataclass
class BusinessRuleResult:
    """Result of business rule application"""
    rules_applied: List[str]
    overall_compliance: bool
    violations: List[str]
    regulatory_status: Dict[str, Any]
    recommendation: str
    debt_to_income_ratio: float
    risk_level: RiskLevel
    recommendation: str


@dataclass
class CreditScoreAnalysis:
    """Credit score risk assessment."""
    credit_score: int
    risk_level: CreditScoreRiskLevel
    risk_percentage: float
    recommendation: str


@dataclass
class LoanAmountAnalysis:
    """Loan amount risk assessment."""
    loan_amount: float
    monthly_income: float
    debt_payments: float
    loan_to_income_ratio: float
    risk_level: RiskLevel
    recommendation: str


@dataclass
class FinancialRiskAnalysis:
    """Complete financial risk analysis result."""
    dti_analysis: DebtToIncomeAnalysis
    credit_analysis: CreditScoreAnalysis
    loan_analysis: LoanAmountAnalysis
    anomalies: List[AnomalyFlag]
    overall_risk_level: RiskLevel
    approval_recommendation: str


# ============================================================================
# Business Rules Engine
# ============================================================================

class RiskRulesEngine:
    """Business rules engine for financial risk assessment."""

    # Configuration constants
    DTI_EXCELLENT = 0.20  # 20%
    DTI_GOOD = 0.36  # 36%
    DTI_ACCEPTABLE = 0.43  # 43%
    DTI_HIGH = 0.50  # 50%

    CREDIT_SCORE_THRESHOLDS = {
        800: (CreditScoreRiskLevel.EXCELLENT, 1.0),
        750: (CreditScoreRiskLevel.GOOD, 2.0),
        670: (CreditScoreRiskLevel.FAIR, 5.0),
        580: (CreditScoreRiskLevel.POOR, 15.0),
        0: (CreditScoreRiskLevel.VERY_POOR, 30.0),
    }

    LOAN_TO_INCOME_THRESHOLDS = {
        2.0: (RiskLevel.LOW, 1.0),
        2.5: (RiskLevel.MEDIUM, 3.0),
        3.0: (RiskLevel.HIGH, 7.0),
        4.0: (RiskLevel.CRITICAL, 15.0),
    }

    ANOMALY_THRESHOLDS = {
        "dti_extreme": 0.60,
        "income_low": 20000,  # Annual
        "loan_large_jumps": 1.5,  # 150% increase
        "credit_score_very_low": 500,
        "dti_spike": 0.15,  # 15% month-over-month increase
    }

    @staticmethod
    def calculate_dti(monthly_debt_payments: float, monthly_gross_income: float) -> DebtToIncomeAnalysis:
        """Calculate Debt-to-Income ratio with risk assessment."""
        if monthly_gross_income <= 0:
            raise ValueError("Monthly gross income must be positive")

        dti_ratio = monthly_debt_payments / monthly_gross_income

        # Determine risk level and recommendation
        if dti_ratio <= RiskRulesEngine.DTI_EXCELLENT:
            risk_level = RiskLevel.LOW
            recommendation = "Excellent DTI ratio. Very favorable for loan approval."
        elif dti_ratio <= RiskRulesEngine.DTI_GOOD:
            risk_level = RiskLevel.LOW
            recommendation = "Good DTI ratio. Generally favorable for loan approval."
        elif dti_ratio <= RiskRulesEngine.DTI_ACCEPTABLE:
            risk_level = RiskLevel.MEDIUM
            recommendation = "Acceptable DTI ratio. May require additional review."
        elif dti_ratio <= RiskRulesEngine.DTI_HIGH:
            risk_level = RiskLevel.HIGH
            recommendation = "High DTI ratio. Loan approval unlikely without debt reduction."
        else:
            risk_level = RiskLevel.CRITICAL
            recommendation = "Critical DTI ratio. Substantial debt reduction required."

        return DebtToIncomeAnalysis(
            monthly_debt_payments=monthly_debt_payments,
            monthly_gross_income=monthly_gross_income,
            debt_to_income_ratio=round(dti_ratio, 4),
            risk_level=risk_level,
            recommendation=recommendation,
        )

    @staticmethod
    def calculate_credit_risk(credit_score: int) -> CreditScoreAnalysis:
        """Assess credit risk based on credit score."""
        if not 300 <= credit_score <= 850:
            raise ValueError("Credit score must be between 300 and 850")

        # Find appropriate risk level
        risk_level = CreditScoreRiskLevel.VERY_POOR
        risk_percentage = 30.0

        for threshold_score in sorted(
            RiskRulesEngine.CREDIT_SCORE_THRESHOLDS.keys(), reverse=True
        ):
            if credit_score >= threshold_score:
                risk_level, risk_percentage = (
                    RiskRulesEngine.CREDIT_SCORE_THRESHOLDS[threshold_score]
                )
                break

        # Generate recommendation
        recommendation_map = {
            CreditScoreRiskLevel.EXCELLENT: "Excellent credit profile. Highest approval likelihood.",
            CreditScoreRiskLevel.GOOD: "Good credit profile. Strong approval likelihood.",
            CreditScoreRiskLevel.FAIR: "Fair credit profile. Approval possible with conditions.",
            CreditScoreRiskLevel.POOR: "Poor credit profile. Higher interest rates expected.",
            CreditScoreRiskLevel.VERY_POOR: "Very poor credit profile. Significant approval challenges.",
        }

        return CreditScoreAnalysis(
            credit_score=credit_score,
            risk_level=risk_level,
            risk_percentage=risk_percentage,
            recommendation=recommendation_map[risk_level],
        )

    @staticmethod
    def calculate_loan_risk(
        loan_amount: float, monthly_income: float, existing_debt_payments: float
    ) -> LoanAmountAnalysis:
        """Assess loan amount risk."""
        if monthly_income <= 0:
            raise ValueError("Monthly income must be positive")
        if loan_amount < 0:
            raise ValueError("Loan amount cannot be negative")

        # Estimate monthly loan payment (assuming 60-month term and 5% interest)
        monthly_rate = 0.05 / 12
        num_payments = 60
        if monthly_rate == 0:
            estimated_monthly_payment = loan_amount / num_payments
        else:
            estimated_monthly_payment = (
                loan_amount
                * (monthly_rate * (1 + monthly_rate) ** num_payments)
                / ((1 + monthly_rate) ** num_payments - 1)
            )

        total_debt_payments = existing_debt_payments + estimated_monthly_payment
        loan_to_income_ratio = (estimated_monthly_payment * 12) / (monthly_income * 12)

        # Determine risk level
        risk_level = RiskLevel.LOW
        risk_percentage = 1.0

        for threshold_lti in sorted(
            RiskRulesEngine.LOAN_TO_INCOME_THRESHOLDS.keys()
        ):
            if loan_to_income_ratio <= threshold_lti:
                risk_level, risk_percentage = (
                    RiskRulesEngine.LOAN_TO_INCOME_THRESHOLDS[threshold_lti]
                )
                break

        # Generate recommendation
        recommendation_map = {
            RiskLevel.LOW: "Loan amount is well-suited to income. Strong approval likelihood.",
            RiskLevel.MEDIUM: "Loan amount is reasonable relative to income.",
            RiskLevel.HIGH: "Loan amount may be high relative to income.",
            RiskLevel.CRITICAL: "Loan amount poses critical risk to borrower.",
        }

        return LoanAmountAnalysis(
            loan_amount=loan_amount,
            monthly_income=monthly_income,
            debt_payments=total_debt_payments,
            loan_to_income_ratio=round(loan_to_income_ratio, 4),
            risk_level=risk_level,
            recommendation=recommendation_map[risk_level],
        )

    @staticmethod
    def detect_anomalies(
        credit_score: int,
        monthly_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> List[AnomalyFlag]:
        """Detect anomalies and suspicious patterns."""
        anomalies: List[AnomalyFlag] = []
        thresholds = RiskRulesEngine.ANOMALY_THRESHOLDS

        # Check for extreme DTI
        current_dti = monthly_debt_payments / monthly_income if monthly_income > 0 else 0
        if current_dti > thresholds["dti_extreme"]:
            anomalies.append(
                AnomalyFlag(
                    flag_type="EXTREME_DTI",
                    severity=RiskLevel.CRITICAL,
                    message=f"Debt-to-income ratio exceeds safe threshold of {thresholds['dti_extreme']}",
                    threshold=thresholds["dti_extreme"],
                    actual_value=current_dti,
                )
            )

        # Check for very low income
        annual_income = monthly_income * 12
        if annual_income < thresholds["income_low"]:
            anomalies.append(
                AnomalyFlag(
                    flag_type="LOW_INCOME",
                    severity=RiskLevel.HIGH,
                    message=f"Annual income below recommended threshold of ${thresholds['income_low']:,.0f}",
                    threshold=thresholds["income_low"],
                    actual_value=annual_income,
                )
            )

        # Check for very poor credit score
        if credit_score < thresholds["credit_score_very_low"]:
            anomalies.append(
                AnomalyFlag(
                    flag_type="VERY_LOW_CREDIT_SCORE",
                    severity=RiskLevel.CRITICAL,
                    message=f"Credit score below {thresholds['credit_score_very_low']} indicates severe credit issues",
                    threshold=thresholds["credit_score_very_low"],
                    actual_value=credit_score,
                )
            )

        # Check for extremely large loan amount
        if monthly_income > 0:
            loan_to_monthly_income = loan_amount / monthly_income
            if loan_to_monthly_income > 60:  # More than 60 months of income
                anomalies.append(
                    AnomalyFlag(
                        flag_type="LARGE_LOAN_AMOUNT",
                        severity=RiskLevel.HIGH,
                        message=f"Loan amount is {loan_to_monthly_income:.1f}x monthly income",
                        threshold=60.0,
                        actual_value=loan_to_monthly_income,
                    )
                )

        # Check for DTI spike (if previous DTI available)
        if previous_dti is not None:
            dti_change = current_dti - previous_dti
            if dti_change > thresholds["dti_spike"]:
                anomalies.append(
                    AnomalyFlag(
                        flag_type="DTI_SPIKE",
                        severity=RiskLevel.MEDIUM,
                        message=f"DTI increased by {dti_change:.1%} from previous assessment",
                        threshold=thresholds["dti_spike"],
                        actual_value=dti_change,
                    )
                )

        return anomalies

    @staticmethod
    def calculate_overall_risk(
        dti_risk: RiskLevel,
        credit_risk: CreditScoreRiskLevel,
        loan_risk: RiskLevel,
        anomaly_count: int,
    ) -> tuple[RiskLevel, str]:
        """
        Aggregate individual risk assessments into overall risk level.

        Risk levels are weighted: CRITICAL > HIGH > MEDIUM > LOW
        """
        # Convert credit risk to comparable scale
        credit_risk_map = {
            CreditScoreRiskLevel.EXCELLENT: RiskLevel.LOW,
            CreditScoreRiskLevel.GOOD: RiskLevel.LOW,
            CreditScoreRiskLevel.FAIR: RiskLevel.MEDIUM,
            CreditScoreRiskLevel.POOR: RiskLevel.HIGH,
            CreditScoreRiskLevel.VERY_POOR: RiskLevel.CRITICAL,
        }

        credit_risk_level = credit_risk_map[credit_risk]

        # Risk level hierarchy
        risk_hierarchy = {RiskLevel.CRITICAL: 4, RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}

        # Calculate weighted risk
        total_risk = (
            risk_hierarchy[dti_risk]
            + risk_hierarchy[credit_risk_level]
            + risk_hierarchy[loan_risk]
        )
        average_risk = total_risk / 3

        # Anomalies increase overall risk
        if anomaly_count > 0:
            average_risk += min(anomaly_count * 0.5, 1.5)

        # Determine overall risk level
        if average_risk >= 3.5:
            overall_risk = RiskLevel.CRITICAL
            recommendation = "DENY: Critical risk factors present. Substantial remediation required."
        elif average_risk >= 2.5:
            overall_risk = RiskLevel.HIGH
            recommendation = "CONDITIONAL: High-risk profile. Additional review/conditions required."
        elif average_risk >= 1.5:
            overall_risk = RiskLevel.MEDIUM
            recommendation = "REVIEW: Moderate risk. Standard underwriting procedures apply."
        else:
            overall_risk = RiskLevel.LOW
            recommendation = "APPROVE: Low-risk profile. Standard approval recommended."

        return overall_risk, recommendation


# ============================================================================
# FastMCP Server Setup
# ============================================================================

# Create FastMCP server instance
mcp = FastMCP("RiskRulesDB")


@mcp.tool()
def analyze_financial_risk(
    credit_score: int,
    monthly_gross_income: float,
    monthly_debt_payments: float,
    loan_amount: float,
    previous_dti: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Comprehensive financial risk analysis tool using business rules engine.

    Calculates:
    - Debt-to-Income (DTI) Ratio with risk assessment
    - Credit Score Risk Level
    - Loan Amount Risk
    - Anomaly Detection flags

    Args:
        credit_score: Credit score (300-850)
        monthly_gross_income: Gross monthly income in dollars
        monthly_debt_payments: Current monthly debt payments in dollars
        loan_amount: Requested loan amount in dollars
        previous_dti: Optional previous DTI for spike detection

    Returns:
        Complete financial risk analysis with recommendations
    """
    try:
        # Input validation
        if credit_score < 300 or credit_score > 850:
            raise ValueError(f"Credit score must be 300-850, got {credit_score}")
        if monthly_gross_income <= 0:
            raise ValueError(f"Monthly income must be positive, got {monthly_gross_income}")
        if monthly_debt_payments < 0:
            raise ValueError(f"Monthly debt payments cannot be negative, got {monthly_debt_payments}")
        if loan_amount < 0:
            raise ValueError(f"Loan amount cannot be negative, got {loan_amount}")

        # Execute risk analysis using business rules engine
        dti_analysis = RiskRulesEngine.calculate_dti(
            monthly_debt_payments, monthly_gross_income
        )
        credit_analysis = RiskRulesEngine.calculate_credit_risk(credit_score)
        loan_analysis = RiskRulesEngine.calculate_loan_risk(
            loan_amount, monthly_gross_income, monthly_debt_payments
        )
        anomalies = RiskRulesEngine.detect_anomalies(
            credit_score,
            monthly_gross_income,
            monthly_debt_payments,
            loan_amount,
            previous_dti,
        )

        # Calculate overall risk
        overall_risk, approval_recommendation = RiskRulesEngine.calculate_overall_risk(
            dti_analysis.risk_level,
            credit_analysis.risk_level,
            loan_analysis.risk_level,
            len(anomalies),
        )

        # Build comprehensive response
        analysis = FinancialRiskAnalysis(
            dti_analysis=dti_analysis,
            credit_analysis=credit_analysis,
            loan_analysis=loan_analysis,
            anomalies=anomalies,
            overall_risk_level=overall_risk,
            approval_recommendation=approval_recommendation,
        )

        # Serialize to dictionary with nested structures
        return {
            "status": "success",
            "analysis": {
                "dti_analysis": asdict(dti_analysis),
                "credit_analysis": {
                    "credit_score": credit_analysis.credit_score,
                    "risk_level": credit_analysis.risk_level.value,
                    "risk_percentage": credit_analysis.risk_percentage,
                    "recommendation": credit_analysis.recommendation,
                },
                "loan_analysis": {
                    "loan_amount": loan_analysis.loan_amount,
                    "monthly_income": loan_analysis.monthly_income,
                    "debt_payments": loan_analysis.debt_payments,
                    "loan_to_income_ratio": loan_analysis.loan_to_income_ratio,
                    "risk_level": loan_analysis.risk_level.value,
                    "recommendation": loan_analysis.recommendation,
                },
                "anomalies": [
                    {
                        "flag_type": anomaly.flag_type,
                        "severity": anomaly.severity.value,
                        "message": anomaly.message,
                        "threshold": anomaly.threshold,
                        "actual_value": anomaly.actual_value,
                    }
                    for anomaly in anomalies
                ],
                "overall_risk_level": overall_risk.value,
                "approval_recommendation": approval_recommendation,
            },
        }

    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error during analysis: {str(e)}",
        }


@mcp.tool()
def calculate_dti_threshold(monthly_gross_income: float, target_dti: float = 0.36) -> Dict[str, Any]:
    """
    Calculate maximum allowable debt payments for a given DTI threshold.

    Args:
        monthly_gross_income: Gross monthly income in dollars
        target_dti: Target DTI ratio (default 0.36 or 36%)

    Returns:
        Maximum debt payment amount and recommendations
    """
    if monthly_gross_income <= 0:
        return {"status": "error", "error": "Monthly income must be positive"}
    if not 0 < target_dti < 1:
        return {"status": "error", "error": "Target DTI must be between 0 and 1"}

    max_debt_payment = monthly_gross_income * target_dti

    return {
        "status": "success",
        "monthly_gross_income": monthly_gross_income,
        "target_dti": target_dti,
        "max_debt_payment": round(max_debt_payment, 2),
        "message": f"At {target_dti:.0%} DTI, maximum monthly debt payment is ${max_debt_payment:,.2f}",
    }


@mcp.tool()
def get_risk_thresholds() -> Dict[str, Any]:
    """
    Retrieve the current business rules and thresholds used by the risk engine.

    Returns:
        Dictionary of all configured risk thresholds and decision rules
    """
    return {
        "status": "success",
        "dti_thresholds": {
            "excellent": {"threshold": RiskRulesEngine.DTI_EXCELLENT, "risk_level": "low"},
            "good": {"threshold": RiskRulesEngine.DTI_GOOD, "risk_level": "low"},
            "acceptable": {"threshold": RiskRulesEngine.DTI_ACCEPTABLE, "risk_level": "medium"},
            "high": {"threshold": RiskRulesEngine.DTI_HIGH, "risk_level": "high"},
            "critical": {"threshold": "above_high", "risk_level": "critical"},
        },
        "credit_score_thresholds": [
            {"score": "800+", "risk_level": "excellent", "default_rate": "1.0%"},
            {"score": "750-799", "risk_level": "good", "default_rate": "2.0%"},
            {"score": "670-749", "risk_level": "fair", "default_rate": "5.0%"},
            {"score": "580-669", "risk_level": "poor", "default_rate": "15.0%"},
            {"score": "<580", "risk_level": "very_poor", "default_rate": "30.0%"},
        ],
        "loan_to_income_ratio_thresholds": {
            "low_risk": {"ratio": "≤2.0", "default_rate": "1.0%"},
            "medium_risk": {"ratio": "2.0-2.5", "default_rate": "3.0%"},
            "high_risk": {"ratio": "2.5-3.0", "default_rate": "7.0%"},
            "critical_risk": {"ratio": ">3.0", "default_rate": "15.0%"},
        },
        "anomaly_detection_triggers": {
            "extreme_dti": {"threshold": RiskRulesEngine.ANOMALY_THRESHOLDS["dti_extreme"], "severity": "critical"},
            "low_income": {
                "threshold": f"${RiskRulesEngine.ANOMALY_THRESHOLDS['income_low']:,} annual",
                "severity": "high",
            },
            "very_low_credit_score": {
                "threshold": RiskRulesEngine.ANOMALY_THRESHOLDS["credit_score_very_low"],
                "severity": "critical",
            },
            "large_loan_amount": {"threshold": "60x monthly income", "severity": "high"},
            "dti_spike": {"threshold": f"{RiskRulesEngine.ANOMALY_THRESHOLDS['dti_spike']:.0%} increase", "severity": "medium"},
        },
    }


@mcp.tool()
def batch_risk_analysis(applicants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform batch risk analysis on multiple applicants.

    Args:
        applicants: List of applicant data dictionaries with keys:
                   credit_score, monthly_gross_income, monthly_debt_payments, loan_amount

    Returns:
        Dictionary with analysis results for each applicant
    """
    if not isinstance(applicants, list):
        return {"status": "error", "error": "Applicants must be a list"}
    if len(applicants) == 0:
        return {"status": "error", "error": "Applicants list cannot be empty"}
    if len(applicants) > 100:
        return {"status": "error", "error": "Maximum 100 applicants per batch"}

    results = {
        "status": "success",
        "total_applicants": len(applicants),
        "analyses": [],
        "summary": {"approved": 0, "conditional": 0, "denied": 0},
    }

    for idx, applicant in enumerate(applicants):
        try:
            analysis_result = analyze_financial_risk(
                credit_score=int(applicant.get("credit_score", 0)),
                monthly_gross_income=float(applicant.get("monthly_gross_income", 0)),
                monthly_debt_payments=float(applicant.get("monthly_debt_payments", 0)),
                loan_amount=float(applicant.get("loan_amount", 0)),
                previous_dti=applicant.get("previous_dti"),
            )

            if analysis_result["status"] == "success":
                overall_risk = analysis_result["analysis"]["overall_risk_level"]
                recommendation = analysis_result["analysis"]["approval_recommendation"]

                # Update summary
                if "APPROVE" in recommendation:
                    results["summary"]["approved"] += 1
                elif "DENY" in recommendation:
                    results["summary"]["denied"] += 1
                else:
                    results["summary"]["conditional"] += 1

                results["analyses"].append(
                    {
                        "applicant_index": idx,
                        "analysis": analysis_result["analysis"],
                    }
                )
            else:
                results["analyses"].append(
                    {
                        "applicant_index": idx,
                        "error": analysis_result.get("error", "Unknown error"),
                    }
                )
        except Exception as e:
            results["analyses"].append(
                {
                    "applicant_index": idx,
                    "error": str(e),
                }
            )

    return results


# ============================================================================
# Server Metadata
# ============================================================================

@mcp.tool()
def get_server_info() -> Dict[str, Any]:
    """
    Get information about the RiskRulesDB MCP server.

    Returns:
        Server name, version, and description
    """
    return {
        "name": "RiskRulesDB",
        "version": "1.0.0",
        "description": "Financial risk analysis server with embedded business rules engine",
        "tools": [
            "analyze_financial_risk",
            "calculate_dti_threshold",
            "get_risk_thresholds",
            "batch_risk_analysis",
            "get_server_info",
        ],
        "features": [
            "Debt-to-Income ratio calculation",
            "Credit score risk assessment",
            "Loan amount risk evaluation",
            "Anomaly detection and flagging",
            "Batch processing support",
            "Configurable business rules",
        ],
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    """Run the RiskRulesDB MCP server."""
    import sys

    # Run the FastMCP server
    # FastMCP automatically handles stdio transport
    mcp.run()
