#!/usr/bin/env python3
"""
RiskRulesDB MCP Server - Financial Risk Analysis Engine
Uses FastMCP framework with business rules engine for comprehensive risk assessment
"""

import json
from typing import Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
server = FastMCP("RiskRulesDB")


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class RiskLevel(Enum):
    """Risk classification levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CreditScoreRisk(Enum):
    """Credit score risk categories"""
    EXCELLENT = "EXCELLENT"  # 750+
    GOOD = "GOOD"  # 670-749
    FAIR = "FAIR"  # 580-669
    POOR = "POOR"  # <580


@dataclass
class DebtToIncomeMetrics:
    """Debt-to-Income ratio metrics"""
    total_monthly_debt: float
    monthly_income: float
    ratio: float
    risk_level: RiskLevel
    recommendation: str


@dataclass
class CreditScoreAnalysis:
    """Credit score risk analysis"""
    credit_score: int
    risk_category: CreditScoreRisk
    risk_level: RiskLevel
    factors: list[str]


@dataclass
class LoanRiskAssessment:
    """Loan amount risk assessment"""
    loan_amount: float
    borrower_income: float
    ltv_ratio: float  # Loan-to-Value (approximated as loan to income)
    risk_level: RiskLevel
    max_recommended_loan: float
    factors: list[str]


@dataclass
class AnomalyFlags:
    """Anomaly detection flags"""
    flags: list[str]
    anomaly_score: float
    has_anomalies: bool


@dataclass
class FinancialRiskProfile:
    """Complete financial risk profile"""
    timestamp: str
    debt_to_income: DebtToIncomeMetrics
    credit_risk: CreditScoreAnalysis
    loan_risk: LoanRiskAssessment
    anomalies: AnomalyFlags
    overall_risk_level: RiskLevel
    overall_recommendation: str


# ============================================================================
# BUSINESS RULES ENGINE
# ============================================================================

class RiskRulesEngine:
    """Business rules engine for financial risk assessment"""

    # Configuration constants
    DTI_RULES = {
        "acceptable_max": 0.43,  # 43% is standard maximum
        "acceptable_target": 0.35,  # Target for healthy finances
        "warning_threshold": 0.50,  # Warning if exceeds 50%
        "critical_threshold": 0.60,  # Critical if exceeds 60%
    }

    CREDIT_SCORE_RULES = {
        "excellent_min": 750,
        "good_min": 670,
        "fair_min": 580,
        "poor_max": 579,
    }

    LOAN_AMOUNT_RULES = {
        "conservative_ratio": 2.5,  # Loan should be max 2.5x annual income
        "moderate_ratio": 3.0,  # Loan should be max 3x annual income
        "aggressive_ratio": 3.5,  # Loan should be max 3.5x annual income
        "annual_income_multiplier": 12,
    }

    ANOMALY_DETECTION_RULES = {
        "high_dti_threshold": 0.50,
        "low_credit_threshold": 600,
        "high_loan_to_income": 4.0,
        "debt_to_income_variance": 0.15,  # 15% variance flag
    }

    @staticmethod
    def calculate_dti_ratio(
        total_monthly_debt: float, monthly_income: float
    ) -> DebtToIncomeMetrics:
        """
        Calculate Debt-to-Income (DTI) ratio and assess risk

        Args:
            total_monthly_debt: Total monthly debt payments
            monthly_income: Monthly gross income

        Returns:
            DebtToIncomeMetrics with risk assessment
        """
        if monthly_income <= 0:
            raise ValueError("Monthly income must be positive")

        ratio = total_monthly_debt / monthly_income

        # Determine risk level based on DTI rules
        if ratio <= RiskRulesEngine.DTI_RULES["acceptable_max"]:
            risk_level = RiskLevel.LOW
            recommendation = "DTI within acceptable range. Good financial health."
        elif ratio <= RiskRulesEngine.DTI_RULES["warning_threshold"]:
            risk_level = RiskLevel.MEDIUM
            recommendation = "DTI elevated. Consider reducing debt or increasing income."
        elif ratio <= RiskRulesEngine.DTI_RULES["critical_threshold"]:
            risk_level = RiskLevel.HIGH
            recommendation = "DTI high. Significant debt burden. Recommend debt reduction."
        else:
            risk_level = RiskLevel.CRITICAL
            recommendation = "DTI critical. Immediate action required to reduce debt."

        return DebtToIncomeMetrics(
            total_monthly_debt=total_monthly_debt,
            monthly_income=monthly_income,
            ratio=round(ratio, 4),
            risk_level=risk_level,
            recommendation=recommendation,
        )

    @staticmethod
    def assess_credit_score_risk(credit_score: int) -> CreditScoreAnalysis:
        """
        Assess credit score and determine risk level

        Args:
            credit_score: Credit score (typically 300-850)

        Returns:
            CreditScoreAnalysis with risk assessment
        """
        if not (300 <= credit_score <= 850):
            raise ValueError("Credit score must be between 300 and 850")

        factors = []

        # Determine risk category and level
        if credit_score >= RiskRulesEngine.CREDIT_SCORE_RULES["excellent_min"]:
            category = CreditScoreRisk.EXCELLENT
            risk_level = RiskLevel.LOW
            factors = ["Strong credit history", "Excellent payment history"]
        elif credit_score >= RiskRulesEngine.CREDIT_SCORE_RULES["good_min"]:
            category = CreditScoreRisk.GOOD
            risk_level = RiskLevel.LOW
            factors = ["Good payment history", "Reasonable credit utilization"]
        elif credit_score >= RiskRulesEngine.CREDIT_SCORE_RULES["fair_min"]:
            category = CreditScoreRisk.FAIR
            risk_level = RiskLevel.MEDIUM
            factors = [
                "Some negative items in history",
                "Higher credit utilization",
                "Previous payment issues",
            ]
        else:
            category = CreditScoreRisk.POOR
            risk_level = RiskLevel.HIGH
            factors = [
                "Significant negative history",
                "Multiple late payments",
                "High credit utilization",
                "Previous default/bankruptcy",
            ]

        return CreditScoreAnalysis(
            credit_score=credit_score,
            risk_category=category.value,
            risk_level=risk_level,
            factors=factors,
        )

    @staticmethod
    def assess_loan_amount_risk(
        loan_amount: float, borrower_annual_income: float
    ) -> LoanRiskAssessment:
        """
        Assess loan amount risk based on borrower income

        Args:
            loan_amount: Requested loan amount
            borrower_annual_income: Borrower's annual income

        Returns:
            LoanRiskAssessment with risk metrics
        """
        if loan_amount < 0 or borrower_annual_income <= 0:
            raise ValueError("Loan amount must be non-negative, income must be positive")

        # Calculate loan-to-value ratio (approximated as loan to annual income)
        ltv_ratio = loan_amount / borrower_annual_income

        factors = []

        # Determine risk level
        if ltv_ratio <= RiskRulesEngine.LOAN_AMOUNT_RULES["conservative_ratio"]:
            risk_level = RiskLevel.LOW
            max_recommended = (
                borrower_annual_income
                * RiskRulesEngine.LOAN_AMOUNT_RULES["conservative_ratio"]
            )
            factors.append(
                f"Loan amount conservative relative to income (ratio: {ltv_ratio:.2f})"
            )
        elif ltv_ratio <= RiskRulesEngine.LOAN_AMOUNT_RULES["moderate_ratio"]:
            risk_level = RiskLevel.MEDIUM
            max_recommended = (
                borrower_annual_income
                * RiskRulesEngine.LOAN_AMOUNT_RULES["moderate_ratio"]
            )
            factors.append(f"Loan amount moderate (ratio: {ltv_ratio:.2f})")
            factors.append("Monitor debt service capacity")
        elif ltv_ratio <= RiskRulesEngine.LOAN_AMOUNT_RULES["aggressive_ratio"]:
            risk_level = RiskLevel.HIGH
            max_recommended = (
                borrower_annual_income
                * RiskRulesEngine.LOAN_AMOUNT_RULES["aggressive_ratio"]
            )
            factors.append(f"Loan amount aggressive (ratio: {ltv_ratio:.2f})")
            factors.append("High debt service burden expected")
        else:
            risk_level = RiskLevel.CRITICAL
            max_recommended = (
                borrower_annual_income
                * RiskRulesEngine.LOAN_AMOUNT_RULES["aggressive_ratio"]
            )
            factors.append(f"Loan amount excessive (ratio: {ltv_ratio:.2f})")
            factors.append("Recommend loan reduction or income verification")

        return LoanRiskAssessment(
            loan_amount=loan_amount,
            borrower_income=borrower_annual_income,
            ltv_ratio=round(ltv_ratio, 2),
            risk_level=risk_level,
            max_recommended_loan=round(max_recommended, 2),
            factors=factors,
        )

    @staticmethod
    def detect_anomalies(
        dti_ratio: float,
        credit_score: int,
        loan_to_income: float,
        monthly_debt: float,
        monthly_income: float,
    ) -> AnomalyFlags:
        """
        Detect financial anomalies and red flags

        Args:
            dti_ratio: Debt-to-income ratio
            credit_score: Credit score
            loan_to_income: Loan-to-income ratio
            monthly_debt: Monthly debt payments
            monthly_income: Monthly income

        Returns:
            AnomalyFlags with detected anomalies
        """
        flags = []
        anomaly_count = 0

        # Check DTI anomaly
        if dti_ratio > RiskRulesEngine.ANOMALY_DETECTION_RULES["high_dti_threshold"]:
            flags.append("High DTI ratio detected")
            anomaly_count += 1

        # Check credit score anomaly
        if (
            credit_score
            < RiskRulesEngine.ANOMALY_DETECTION_RULES["low_credit_threshold"]
        ):
            flags.append("Low credit score detected")
            anomaly_count += 1

        # Check loan-to-income anomaly
        if (
            loan_to_income
            > RiskRulesEngine.ANOMALY_DETECTION_RULES["high_loan_to_income"]
        ):
            flags.append("Excessive loan-to-income ratio")
            anomaly_count += 1

        # Check for sudden changes (variance detection)
        if monthly_income > 0:
            debt_variance = monthly_debt / monthly_income
            if (
                debt_variance
                > RiskRulesEngine.ANOMALY_DETECTION_RULES["debt_to_income_variance"]
            ):
                flags.append("Unusual debt-to-income variance")
                anomaly_count += 1

        # Calculate anomaly score (0-1, where 1 is maximum anomalies)
        max_possible_flags = 4
        anomaly_score = min(anomaly_count / max_possible_flags, 1.0)

        return AnomalyFlags(
            flags=flags,
            anomaly_score=round(anomaly_score, 3),
            has_anomalies=anomaly_score > 0.25,
        )


# ============================================================================
# MCP TOOLS
# ============================================================================


@server.call_tool()
def analyze_financial_risk(
    borrower_name: str,
    monthly_income: float,
    total_monthly_debt: float,
    credit_score: int,
    loan_amount: float,
    annual_income: float,
) -> dict[str, Any]:
    """
    Comprehensive financial risk analysis tool

    Calculates:
    - Debt-to-Income Ratio with risk assessment
    - Credit Score Risk Level classification
    - Loan Amount Risk assessment
    - Anomaly Detection flags

    Args:
        borrower_name: Name of the borrower
        monthly_income: Monthly gross income
        total_monthly_debt: Total monthly debt obligations
        credit_score: Credit score (300-850)
        loan_amount: Requested loan amount
        annual_income: Annual gross income

    Returns:
        Comprehensive financial risk profile with all metrics
    """
    try:
        logger.info(f"Analyzing financial risk for: {borrower_name}")

        # Calculate DTI
        dti_metrics = RiskRulesEngine.calculate_dti_ratio(
            total_monthly_debt, monthly_income
        )

        # Assess credit score
        credit_analysis = RiskRulesEngine.assess_credit_score_risk(credit_score)

        # Assess loan amount
        loan_assessment = RiskRulesEngine.assess_loan_amount_risk(
            loan_amount, annual_income
        )

        # Detect anomalies
        loan_to_income = loan_amount / annual_income if annual_income > 0 else 0
        anomalies = RiskRulesEngine.detect_anomalies(
            dti_ratio=dti_metrics.ratio,
            credit_score=credit_score,
            loan_to_income=loan_to_income,
            monthly_debt=total_monthly_debt,
            monthly_income=monthly_income,
        )

        # Determine overall risk level
        risk_levels = [
            dti_metrics.risk_level,
            credit_analysis.risk_level,
            loan_assessment.risk_level,
        ]
        risk_level_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        overall_risk_level = max(risk_levels, key=lambda x: risk_level_order.index(x))

        # Generate recommendation
        if anomalies.has_anomalies:
            overall_recommendation = (
                f"CAUTION: Multiple anomalies detected. Review required before approval. "
                f"Overall risk level: {overall_risk_level.value}"
            )
        elif overall_risk_level == RiskLevel.CRITICAL:
            overall_recommendation = "REJECT: Critical risk factors present. Do not approve without major changes."
        elif overall_risk_level == RiskLevel.HIGH:
            overall_recommendation = "CONDITIONAL: High risk. Approve only with additional conditions or co-signer."
        elif overall_risk_level == RiskLevel.MEDIUM:
            overall_recommendation = "APPROVE WITH CONDITIONS: Moderate risk. Standard terms may apply with monitoring."
        else:
            overall_recommendation = "APPROVE: Low risk profile. Standard terms recommended."

        # Build profile
        profile = FinancialRiskProfile(
            timestamp=datetime.now().isoformat(),
            debt_to_income=dti_metrics,
            credit_risk=credit_analysis,
            loan_risk=loan_assessment,
            anomalies=anomalies,
            overall_risk_level=overall_risk_level,
            overall_recommendation=overall_recommendation,
        )

        # Convert to dictionary
        result = {
            "borrower_name": borrower_name,
            "analysis_timestamp": profile.timestamp,
            "debt_to_income": {
                "total_monthly_debt": profile.debt_to_income.total_monthly_debt,
                "monthly_income": profile.debt_to_income.monthly_income,
                "ratio": profile.debt_to_income.ratio,
                "risk_level": profile.debt_to_income.risk_level.value,
                "recommendation": profile.debt_to_income.recommendation,
            },
            "credit_risk": {
                "credit_score": profile.credit_risk.credit_score,
                "risk_category": profile.credit_risk.risk_category,
                "risk_level": profile.credit_risk.risk_level.value,
                "factors": profile.credit_risk.factors,
            },
            "loan_risk": {
                "loan_amount": profile.loan_risk.loan_amount,
                "borrower_income": profile.loan_risk.borrower_income,
                "ltv_ratio": profile.loan_risk.ltv_ratio,
                "risk_level": profile.loan_risk.risk_level.value,
                "max_recommended_loan": profile.loan_risk.max_recommended_loan,
                "factors": profile.loan_risk.factors,
            },
            "anomaly_detection": {
                "flags": profile.anomalies.flags,
                "anomaly_score": profile.anomalies.anomaly_score,
                "has_anomalies": profile.anomalies.has_anomalies,
            },
            "overall_risk_level": profile.overall_risk_level.value,
            "overall_recommendation": profile.overall_recommendation,
        }

        logger.info(f"Risk analysis complete for {borrower_name}: {overall_risk_level.value}")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {"error": f"Validation error: {str(e)}", "status": "failed"}
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}", "status": "failed"}


@server.call_tool()
def get_risk_rules_configuration() -> dict[str, Any]:
    """
    Retrieve the current business rules configuration

    Returns:
        Dictionary containing all risk rules thresholds and parameters
    """
    return {
        "dti_rules": {
            "acceptable_max": RiskRulesEngine.DTI_RULES["acceptable_max"],
            "acceptable_target": RiskRulesEngine.DTI_RULES["acceptable_target"],
            "warning_threshold": RiskRulesEngine.DTI_RULES["warning_threshold"],
            "critical_threshold": RiskRulesEngine.DTI_RULES["critical_threshold"],
        },
        "credit_score_rules": {
            "excellent_min": RiskRulesEngine.CREDIT_SCORE_RULES["excellent_min"],
            "good_min": RiskRulesEngine.CREDIT_SCORE_RULES["good_min"],
            "fair_min": RiskRulesEngine.CREDIT_SCORE_RULES["fair_min"],
            "poor_max": RiskRulesEngine.CREDIT_SCORE_RULES["poor_max"],
        },
        "loan_amount_rules": {
            "conservative_ratio": RiskRulesEngine.LOAN_AMOUNT_RULES["conservative_ratio"],
            "moderate_ratio": RiskRulesEngine.LOAN_AMOUNT_RULES["moderate_ratio"],
            "aggressive_ratio": RiskRulesEngine.LOAN_AMOUNT_RULES["aggressive_ratio"],
        },
        "anomaly_detection_rules": {
            "high_dti_threshold": RiskRulesEngine.ANOMALY_DETECTION_RULES[
                "high_dti_threshold"
            ],
            "low_credit_threshold": RiskRulesEngine.ANOMALY_DETECTION_RULES[
                "low_credit_threshold"
            ],
            "high_loan_to_income": RiskRulesEngine.ANOMALY_DETECTION_RULES[
                "high_loan_to_income"
            ],
            "debt_to_income_variance": RiskRulesEngine.ANOMALY_DETECTION_RULES[
                "debt_to_income_variance"
            ],
        },
    }


@server.call_tool()
def batch_analyze_financial_risk(borrowers: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze financial risk for multiple borrowers in batch

    Args:
        borrowers: List of borrower dictionaries with required fields:
                   - borrower_name
                   - monthly_income
                   - total_monthly_debt
                   - credit_score
                   - loan_amount
                   - annual_income

    Returns:
        Dictionary with analysis results for all borrowers
    """
    try:
        results = {
            "batch_timestamp": datetime.now().isoformat(),
            "total_borrowers": len(borrowers),
            "analyses": [],
            "summary": {
                "low_risk_count": 0,
                "medium_risk_count": 0,
                "high_risk_count": 0,
                "critical_risk_count": 0,
            },
        }

        for borrower in borrowers:
            analysis = analyze_financial_risk(
                borrower_name=borrower.get("borrower_name", "Unknown"),
                monthly_income=borrower.get("monthly_income", 0),
                total_monthly_debt=borrower.get("total_monthly_debt", 0),
                credit_score=borrower.get("credit_score", 300),
                loan_amount=borrower.get("loan_amount", 0),
                annual_income=borrower.get("annual_income", 0),
            )

            if "error" not in analysis:
                results["analyses"].append(analysis)
                risk_level = analysis.get("overall_risk_level", "UNKNOWN")
                results["summary"][f"{risk_level.lower()}_risk_count"] += 1

        return results

    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}")
        return {"error": f"Batch analysis failed: {str(e)}", "status": "failed"}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    logger.info("Starting RiskRulesDB MCP Server")
    logger.info("Available tools:")
    logger.info("  - analyze_financial_risk: Comprehensive single borrower analysis")
    logger.info("  - get_risk_rules_configuration: View current business rules")
    logger.info("  - batch_analyze_financial_risk: Analyze multiple borrowers")

    # Run the server
    server.run(sys.argv[1] if len(sys.argv) > 1 else None)
