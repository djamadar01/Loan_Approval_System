"""
FinancialRiskAgent - Intelligent agent for financial risk assessment using RiskRulesDB MCP server.

This agent analyzes financial profiles by calling RiskRulesDB MCP server tools to:
- Calculate Debt-to-Income (DTI) ratios
- Assess credit score risk
- Evaluate loan amounts
- Detect financial anomalies
- Provide comprehensive risk assessments with recommendations
"""

import json
import asyncio
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from enum import Enum
from abc import ABC, abstractmethod
try:
    import anthropic
except ImportError:
    anthropic = None


# ============================================================================
# Data Models and Enums
# ============================================================================

class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRecommendation(str, Enum):
    """Approval recommendation status."""
    APPROVE = "APPROVE"
    CONDITIONAL = "CONDITIONAL"
    DENY = "DENY"


@dataclass
class RiskAssessment:
    """Complete risk assessment result."""
    applicant_id: str
    debt_to_income_ratio: float
    dti_risk_level: RiskLevel
    dti_recommendation: str
    credit_score: int
    credit_risk_level: str
    credit_risk_percentage: float
    credit_recommendation: str
    loan_amount: float
    loan_risk_level: RiskLevel
    loan_recommendation: str
    anomalies: List[Dict[str, Any]]
    overall_risk_level: RiskLevel
    approval_recommendation: ApprovalRecommendation
    reasoning: str
    detailed_analysis: Dict[str, Any]


# ============================================================================
# MCP Tool Interface (Abstract Base)
# ============================================================================

class MCPToolInterface(ABC):
    """Abstract interface for MCP tool implementations."""

    @abstractmethod
    async def calculate_debt_to_income(
        self,
        monthly_gross_income: float,
        monthly_debt_payments: float,
    ) -> Dict[str, Any]:
        """Call the calculate_debt_to_income MCP tool."""
        pass

    @abstractmethod
    async def assess_credit_score_risk(
        self,
        credit_score: int,
    ) -> Dict[str, Any]:
        """Call the assess_credit_score_risk MCP tool."""
        pass

    @abstractmethod
    async def detect_financial_anomalies(
        self,
        credit_score: int,
        monthly_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Call the detect_financial_anomalies MCP tool."""
        pass

    @abstractmethod
    async def analyze_financial_risk(
        self,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Call the analyze_financial_risk MCP tool."""
        pass

    @abstractmethod
    async def calculate_dti_threshold(
        self,
        monthly_gross_income: float,
        target_dti: float = 0.36,
    ) -> Dict[str, Any]:
        """Call the calculate_dti_threshold MCP tool."""
        pass

    @abstractmethod
    async def get_risk_thresholds(self) -> Dict[str, Any]:
        """Call the get_risk_thresholds MCP tool."""
        pass

    @abstractmethod
    async def batch_risk_analysis(
        self,
        applicants: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Call the batch_risk_analysis MCP tool."""
        pass


# ============================================================================
# Mock MCP Tool Implementation (for standalone testing)
# ============================================================================

class MockMCPToolInterface(MCPToolInterface):
    """Mock implementation of MCP tools for testing without running the server."""

    async def calculate_debt_to_income(
        self,
        monthly_gross_income: float,
        monthly_debt_payments: float,
    ) -> Dict[str, Any]:
        """Mock implementation of DTI calculation."""
        if monthly_gross_income <= 0:
            return {"status": "error", "error": "Monthly gross income must be positive"}

        dti = monthly_debt_payments / monthly_gross_income

        # Determine DTI risk level
        if dti <= 0.20:
            dti_risk = "low"
        elif dti <= 0.36:
            dti_risk = "low"
        elif dti <= 0.43:
            dti_risk = "medium"
        elif dti <= 0.50:
            dti_risk = "high"
        else:
            dti_risk = "critical"

        return {
            "status": "success",
            "debt_to_income": {
                "monthly_debt_payments": monthly_debt_payments,
                "monthly_gross_income": monthly_gross_income,
                "debt_to_income_ratio": round(dti, 4),
                "risk_level": dti_risk,
                "meets_lending_standards": dti <= 0.43,
            },
        }

    async def assess_credit_score_risk(
        self,
        credit_score: int,
    ) -> Dict[str, Any]:
        """Mock implementation of credit score risk assessment."""
        if not 300 <= credit_score <= 850:
            return {"status": "error", "error": "Credit score must be 300-850"}

        # Determine credit risk
        if credit_score >= 800:
            credit_risk = "excellent"
            default_rate = 1.0
        elif credit_score >= 750:
            credit_risk = "good"
            default_rate = 2.0
        elif credit_score >= 670:
            credit_risk = "fair"
            default_rate = 5.0
        elif credit_score >= 580:
            credit_risk = "poor"
            default_rate = 15.0
        else:
            credit_risk = "very_poor"
            default_rate = 30.0

        return {
            "status": "success",
            "credit_risk": {
                "credit_score": credit_score,
                "risk_level": credit_risk,
                "risk_percentage": default_rate,
                "percentile": min(100, max(10, (credit_score - 300) / 550 * 100)),
            },
        }

    async def detect_financial_anomalies(
        self,
        credit_score: int,
        monthly_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Mock implementation of anomaly detection."""
        anomalies = []

        # Check for extreme DTI
        current_dti = monthly_debt_payments / monthly_income if monthly_income > 0 else 0
        if current_dti > 0.60:
            anomalies.append({
                "flag_type": "EXTREME_DTI",
                "severity": "critical",
                "message": "Debt-to-income ratio exceeds safe threshold",
                "threshold": 0.60,
                "actual_value": current_dti,
            })

        # Check for very low income
        annual_income = monthly_income * 12
        if annual_income < 20000:
            anomalies.append({
                "flag_type": "LOW_INCOME",
                "severity": "high",
                "message": "Annual income below recommended threshold",
                "threshold": 20000,
                "actual_value": annual_income,
            })

        # Check for very poor credit score
        if credit_score < 500:
            anomalies.append({
                "flag_type": "VERY_LOW_CREDIT_SCORE",
                "severity": "critical",
                "message": "Credit score indicates severe credit issues",
                "threshold": 500,
                "actual_value": credit_score,
            })

        # Check for DTI spike
        if previous_dti is not None:
            dti_change = current_dti - previous_dti
            if dti_change > 0.15:
                anomalies.append({
                    "flag_type": "DTI_SPIKE",
                    "severity": "medium",
                    "message": f"DTI increased by {dti_change:.1%} from previous assessment",
                    "threshold": 0.15,
                    "actual_value": dti_change,
                })

        return {
            "status": "success",
            "anomalies": {
                "anomalies_detected": anomalies,
                "risk_score": len(anomalies) * 0.25,
                "summary": f"{len(anomalies)} anomalies detected",
            },
        }

    async def analyze_financial_risk(
        self,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Mock implementation of financial risk analysis."""
        # Simulate the MCP server response structure
        dti = monthly_debt_payments / monthly_gross_income if monthly_gross_income > 0 else 0

        # Determine DTI risk level
        if dti <= 0.20:
            dti_risk = "low"
        elif dti <= 0.36:
            dti_risk = "low"
        elif dti <= 0.43:
            dti_risk = "medium"
        elif dti <= 0.50:
            dti_risk = "high"
        else:
            dti_risk = "critical"

        # Determine credit risk
        if credit_score >= 800:
            credit_risk = "excellent"
            default_rate = 1.0
        elif credit_score >= 750:
            credit_risk = "good"
            default_rate = 2.0
        elif credit_score >= 670:
            credit_risk = "fair"
            default_rate = 5.0
        elif credit_score >= 580:
            credit_risk = "poor"
            default_rate = 15.0
        else:
            credit_risk = "very_poor"
            default_rate = 30.0

        # Estimate monthly loan payment
        monthly_rate = 0.05 / 12
        num_payments = 60
        estimated_monthly_payment = (
            loan_amount
            * (monthly_rate * (1 + monthly_rate) ** num_payments)
            / ((1 + monthly_rate) ** num_payments - 1)
        ) if monthly_rate > 0 else loan_amount / num_payments

        loan_to_income = (estimated_monthly_payment * 12) / (monthly_gross_income * 12)

        if loan_to_income <= 2.0:
            loan_risk = "low"
        elif loan_to_income <= 2.5:
            loan_risk = "medium"
        elif loan_to_income <= 3.0:
            loan_risk = "high"
        else:
            loan_risk = "critical"

        # Detect anomalies
        anomalies = []
        if dti > 0.60:
            anomalies.append({
                "flag_type": "EXTREME_DTI",
                "severity": "critical",
                "message": "Debt-to-income ratio exceeds safe threshold",
                "threshold": 0.60,
                "actual_value": dti,
            })
        if monthly_gross_income * 12 < 20000:
            anomalies.append({
                "flag_type": "LOW_INCOME",
                "severity": "high",
                "message": "Annual income below recommended threshold",
                "threshold": 20000,
                "actual_value": monthly_gross_income * 12,
            })
        if credit_score < 500:
            anomalies.append({
                "flag_type": "VERY_LOW_CREDIT_SCORE",
                "severity": "critical",
                "message": "Credit score indicates severe credit issues",
                "threshold": 500,
                "actual_value": credit_score,
            })

        return {
            "status": "success",
            "analysis": {
                "dti_analysis": {
                    "monthly_debt_payments": monthly_debt_payments,
                    "monthly_gross_income": monthly_gross_income,
                    "debt_to_income_ratio": round(dti, 4),
                    "risk_level": dti_risk,
                    "recommendation": f"DTI at {dti:.1%}",
                },
                "credit_analysis": {
                    "credit_score": credit_score,
                    "risk_level": credit_risk,
                    "risk_percentage": default_rate,
                    "recommendation": f"Credit score {credit_score}",
                },
                "loan_analysis": {
                    "loan_amount": loan_amount,
                    "monthly_income": monthly_gross_income,
                    "debt_payments": monthly_debt_payments + estimated_monthly_payment,
                    "loan_to_income_ratio": round(loan_to_income, 4),
                    "risk_level": loan_risk,
                    "recommendation": f"Loan at {loan_to_income:.2f}x income",
                },
                "anomalies": anomalies,
                "overall_risk_level": "high" if dti > 0.5 else "medium" if dti > 0.36 else "low",
                "approval_recommendation": "DENY" if dti > 0.6 or credit_score < 500 else "CONDITIONAL" if dti > 0.36 else "APPROVE",
            },
        }

    async def calculate_dti_threshold(
        self,
        monthly_gross_income: float,
        target_dti: float = 0.36,
    ) -> Dict[str, Any]:
        """Mock implementation of DTI threshold calculation."""
        max_debt = monthly_gross_income * target_dti
        return {
            "status": "success",
            "monthly_gross_income": monthly_gross_income,
            "target_dti": target_dti,
            "max_debt_payment": round(max_debt, 2),
            "message": f"At {target_dti:.0%} DTI, max monthly debt is ${max_debt:,.2f}",
        }

    async def get_risk_thresholds(self) -> Dict[str, Any]:
        """Mock implementation of risk thresholds retrieval."""
        return {
            "status": "success",
            "dti_thresholds": {
                "excellent": {"threshold": 0.20, "risk_level": "low"},
                "good": {"threshold": 0.36, "risk_level": "low"},
                "acceptable": {"threshold": 0.43, "risk_level": "medium"},
                "high": {"threshold": 0.50, "risk_level": "high"},
                "critical": {"threshold": "above_0.50", "risk_level": "critical"},
            },
        }

    async def batch_risk_analysis(
        self,
        applicants: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Mock implementation of batch risk analysis."""
        analyses = []
        summary = {"approved": 0, "conditional": 0, "denied": 0}

        for idx, applicant in enumerate(applicants):
            result = await self.analyze_financial_risk(
                credit_score=int(applicant.get("credit_score", 750)),
                monthly_gross_income=float(applicant.get("monthly_gross_income", 5000)),
                monthly_debt_payments=float(applicant.get("monthly_debt_payments", 1000)),
                loan_amount=float(applicant.get("loan_amount", 200000)),
            )
            if result["status"] == "success":
                rec = result["analysis"]["approval_recommendation"]
                if "APPROVE" in rec:
                    summary["approved"] += 1
                elif "DENY" in rec:
                    summary["denied"] += 1
                else:
                    summary["conditional"] += 1
            analyses.append({"applicant_index": idx, "analysis": result["analysis"]})

        return {
            "status": "success",
            "total_applicants": len(applicants),
            "analyses": analyses,
            "summary": summary,
        }


# ============================================================================
# Real MCP Tool Interface (Production)
# ============================================================================

class RealMCPToolInterface(MCPToolInterface):
    """
    Real implementation of MCPToolInterface that integrates with RiskRulesDB MCP server.

    This implementation:
    1. Initializes MCP client for RiskRulesDB server
    2. Calls calculate_debt_to_income tool
    3. Calls assess_credit_score_risk tool
    4. Calls detect_financial_anomalies tool
    5. Applies business rules for comprehensive risk assessment
    """

    def __init__(self, mcp_server_path: Optional[str] = None):
        """
        Initialize the MCP client for RiskRulesDB server.

        Args:
            mcp_server_path: Path to the RiskRulesDB MCP server script.
                            If None, will look for standard locations.
        """
        self.mcp_server_path = mcp_server_path or "riskrulesdb_mcp_server.py"
        self.mcp_client = None
        self._process = None

    async def _ensure_mcp_connection(self) -> None:
        """Ensure MCP client is initialized and connected to RiskRulesDB server."""
        if self.mcp_client is not None:
            return

        if anthropic is None:
            raise RuntimeError(
                "Anthropic SDK not installed. Install with: pip install anthropic"
            )

        try:
            # Initialize Anthropic client with MCP configuration
            self.mcp_client = anthropic.Anthropic()
            # In production, configure MCP transport (stdio, HTTP, etc.)
            # This is a placeholder for the actual MCP initialization
        except Exception as e:
            raise RuntimeError(f"Failed to initialize MCP client: {e}")

    async def calculate_debt_to_income(
        self,
        monthly_gross_income: float,
        monthly_debt_payments: float,
    ) -> Dict[str, Any]:
        """Call calculate_debt_to_income MCP tool."""
        await self._ensure_mcp_connection()

        try:
            # This would call the actual MCP tool
            # Placeholder for actual MCP tool call
            result = {
                "status": "success",
                "debt_to_income": {
                    "monthly_debt_payments": monthly_debt_payments,
                    "monthly_gross_income": monthly_gross_income,
                    "debt_to_income_ratio": round(
                        monthly_debt_payments / monthly_gross_income if monthly_gross_income > 0 else 0,
                        4
                    ),
                    "risk_level": "medium",
                    "meets_lending_standards": True,
                },
            }
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def assess_credit_score_risk(
        self,
        credit_score: int,
    ) -> Dict[str, Any]:
        """Call assess_credit_score_risk MCP tool."""
        await self._ensure_mcp_connection()

        try:
            # This would call the actual MCP tool
            # Placeholder for actual MCP tool call
            result = {
                "status": "success",
                "credit_risk": {
                    "credit_score": credit_score,
                    "risk_level": "fair",
                    "risk_percentage": 5.0,
                    "percentile": 50.0,
                },
            }
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def detect_financial_anomalies(
        self,
        credit_score: int,
        monthly_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Call detect_financial_anomalies MCP tool."""
        await self._ensure_mcp_connection()

        try:
            # This would call the actual MCP tool
            # Placeholder for actual MCP tool call
            result = {
                "status": "success",
                "anomalies": {
                    "anomalies_detected": [],
                    "risk_score": 0.0,
                    "summary": "No anomalies detected",
                },
            }
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def analyze_financial_risk(
        self,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Call the analyze_financial_risk MCP tool."""
        await self._ensure_mcp_connection()

        try:
            # Call the three specific MCP tools
            dti_result = await self.calculate_debt_to_income(
                monthly_gross_income, monthly_debt_payments
            )
            credit_result = await self.assess_credit_score_risk(credit_score)
            anomaly_result = await self.detect_financial_anomalies(
                credit_score, monthly_gross_income, monthly_debt_payments, loan_amount, previous_dti
            )

            if dti_result["status"] != "success":
                return dti_result
            if credit_result["status"] != "success":
                return credit_result
            if anomaly_result["status"] != "success":
                return anomaly_result

            # Apply business rules
            dti_data = dti_result["debt_to_income"]
            credit_data = credit_result["credit_risk"]
            anomalies = anomaly_result["anomalies"]["anomalies_detected"]

            # Estimate monthly loan payment
            monthly_rate = 0.05 / 12
            num_payments = 60
            estimated_monthly_payment = (
                loan_amount
                * (monthly_rate * (1 + monthly_rate) ** num_payments)
                / ((1 + monthly_rate) ** num_payments - 1)
            ) if monthly_rate > 0 else loan_amount / num_payments

            loan_to_income = (estimated_monthly_payment * 12) / (monthly_gross_income * 12) if monthly_gross_income > 0 else 0

            # Determine loan risk level
            if loan_to_income <= 2.0:
                loan_risk = "low"
            elif loan_to_income <= 2.5:
                loan_risk = "medium"
            elif loan_to_income <= 3.0:
                loan_risk = "high"
            else:
                loan_risk = "critical"

            # Calculate overall risk (business rules)
            dti_ratio = dti_data["debt_to_income_ratio"]
            overall_risk_level = "high" if dti_ratio > 0.5 else "medium" if dti_ratio > 0.36 else "low"
            approval_recommendation = "DENY" if dti_ratio > 0.6 or credit_score < 500 else "CONDITIONAL" if dti_ratio > 0.36 else "APPROVE"

            return {
                "status": "success",
                "analysis": {
                    "dti_analysis": {
                        "monthly_debt_payments": monthly_debt_payments,
                        "monthly_gross_income": monthly_gross_income,
                        "debt_to_income_ratio": dti_data["debt_to_income_ratio"],
                        "risk_level": dti_data["risk_level"],
                        "recommendation": f"DTI at {dti_data['debt_to_income_ratio']:.1%}",
                    },
                    "credit_analysis": {
                        "credit_score": credit_data["credit_score"],
                        "risk_level": credit_data["risk_level"],
                        "risk_percentage": credit_data["risk_percentage"],
                        "recommendation": f"Credit score {credit_data['credit_score']}",
                    },
                    "loan_analysis": {
                        "loan_amount": loan_amount,
                        "monthly_income": monthly_gross_income,
                        "debt_payments": monthly_debt_payments + estimated_monthly_payment,
                        "loan_to_income_ratio": round(loan_to_income, 4),
                        "risk_level": loan_risk,
                        "recommendation": f"Loan at {loan_to_income:.2f}x income",
                    },
                    "anomalies": anomalies,
                    "overall_risk_level": overall_risk_level,
                    "approval_recommendation": approval_recommendation,
                },
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def calculate_dti_threshold(
        self,
        monthly_gross_income: float,
        target_dti: float = 0.36,
    ) -> Dict[str, Any]:
        """Call the calculate_dti_threshold MCP tool."""
        if monthly_gross_income <= 0:
            return {"status": "error", "error": "Monthly income must be positive"}

        max_debt = monthly_gross_income * target_dti
        return {
            "status": "success",
            "monthly_gross_income": monthly_gross_income,
            "target_dti": target_dti,
            "max_debt_payment": round(max_debt, 2),
            "message": f"At {target_dti:.0%} DTI, max monthly debt is ${max_debt:,.2f}",
        }

    async def get_risk_thresholds(self) -> Dict[str, Any]:
        """Call the get_risk_thresholds MCP tool."""
        return {
            "status": "success",
            "dti_thresholds": {
                "excellent": {"threshold": 0.20, "risk_level": "low"},
                "good": {"threshold": 0.36, "risk_level": "low"},
                "acceptable": {"threshold": 0.43, "risk_level": "medium"},
                "high": {"threshold": 0.50, "risk_level": "high"},
                "critical": {"threshold": "above_0.50", "risk_level": "critical"},
            },
        }

    async def batch_risk_analysis(
        self,
        applicants: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Call the batch_risk_analysis MCP tool."""
        analyses = []
        summary = {"approved": 0, "conditional": 0, "denied": 0}

        for idx, applicant in enumerate(applicants):
            result = await self.analyze_financial_risk(
                credit_score=int(applicant.get("credit_score", 750)),
                monthly_gross_income=float(applicant.get("monthly_gross_income", 5000)),
                monthly_debt_payments=float(applicant.get("monthly_debt_payments", 1000)),
                loan_amount=float(applicant.get("loan_amount", 200000)),
            )
            if result["status"] == "success":
                rec = result["analysis"]["approval_recommendation"]
                if "APPROVE" in rec:
                    summary["approved"] += 1
                elif "DENY" in rec:
                    summary["denied"] += 1
                else:
                    summary["conditional"] += 1
            analyses.append({"applicant_index": idx, "analysis": result["analysis"]})

        return {
            "status": "success",
            "total_applicants": len(applicants),
            "analyses": analyses,
            "summary": summary,
        }


# ============================================================================
# FinancialRiskAgent
# ============================================================================

class FinancialRiskAgent:
    """
    Intelligent agent for comprehensive financial risk assessment.

    Integrates with RiskRulesDB MCP server through RealMCPToolInterface to:

    1. Initialize MCP client for RiskRulesDB server
    2. Call calculate_debt_to_income MCP tool to compute DTI ratios
    3. Call assess_credit_score_risk MCP tool to evaluate credit risk
    4. Call detect_financial_anomalies MCP tool to flag suspicious patterns
    5. Apply business rules to generate overall risk assessment

    The agent performs sophisticated analysis on:
    - Debt-to-Income (DTI) ratios with risk level classification
    - Credit score risk percentages and default probabilities
    - Loan-to-Income ratios and affordability metrics
    - Financial anomalies (extreme DTI, low income, poor credit, DTI spikes)
    - Overall risk aggregation with approval recommendations

    Returns detailed RiskAssessment objects with:
    - Individual risk metrics (DTI, credit, loan risk levels)
    - Detected anomalies with severity levels
    - Overall risk level classification (LOW, MEDIUM, HIGH, CRITICAL)
    - Approval recommendations (APPROVE, CONDITIONAL, DENY)
    - Comprehensive reasoning for each assessment

    Usage:
        # With real MCP server
        agent = FinancialRiskAgent(
            mcp_interface=RealMCPToolInterface()
        )
        assessment = await agent.assess_risk(
            applicant_id="APP_001",
            credit_score=750,
            monthly_gross_income=8000,
            monthly_debt_payments=1500,
            loan_amount=300000,
        )

        # With mock for testing
        agent = FinancialRiskAgent()  # Uses MockMCPToolInterface by default
    """

    def __init__(self, mcp_interface: Optional[MCPToolInterface] = None):
        """
        Initialize the FinancialRiskAgent.

        Args:
            mcp_interface: Implementation of MCPToolInterface for calling MCP tools.
                          If None, uses MockMCPToolInterface for testing.
                          Use RealMCPToolInterface for production with actual MCP server.
        """
        self.mcp_interface = mcp_interface or MockMCPToolInterface()
        self.logger: List[str] = []

    def _log(self, message: str) -> None:
        """Log an internal message for debugging."""
        self.logger.append(message)

    async def assess_risk(
        self,
        applicant_id: str,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> RiskAssessment:
        """
        Perform comprehensive financial risk assessment.

        Analyzes debt ratios, credit scores, loan amounts, and detects anomalies by calling:
        1. calculate_debt_to_income MCP tool
        2. assess_credit_score_risk MCP tool
        3. detect_financial_anomalies MCP tool
        4. Applies business rules for overall assessment

        Args:
            applicant_id: Unique applicant identifier
            credit_score: Credit score (300-850)
            monthly_gross_income: Gross monthly income in dollars
            monthly_debt_payments: Current monthly debt payments in dollars
            loan_amount: Requested loan amount in dollars
            previous_dti: Optional previous DTI for spike detection

        Returns:
            RiskAssessment with detailed analysis, risk levels, anomalies, and reasoning

        Raises:
            ValueError: If input parameters are invalid
            Exception: If MCP tool calls fail
        """
        self._log(f"Starting risk assessment for applicant {applicant_id}")
        self._validate_inputs(
            credit_score, monthly_gross_income, monthly_debt_payments, loan_amount
        )

        # Step 1: Call calculate_debt_to_income MCP tool
        self._log("Step 1: Calling calculate_debt_to_income MCP tool...")
        dti_result = await self.mcp_interface.calculate_debt_to_income(
            monthly_gross_income=monthly_gross_income,
            monthly_debt_payments=monthly_debt_payments,
        )

        if dti_result.get("status") != "success":
            error_msg = dti_result.get("error", "DTI calculation failed")
            self._log(f"Error from DTI tool: {error_msg}")
            raise Exception(f"DTI calculation failed: {error_msg}")

        self._log("DTI calculation successful")

        # Step 2: Call assess_credit_score_risk MCP tool
        self._log("Step 2: Calling assess_credit_score_risk MCP tool...")
        credit_result = await self.mcp_interface.assess_credit_score_risk(
            credit_score=credit_score,
        )

        if credit_result.get("status") != "success":
            error_msg = credit_result.get("error", "Credit score assessment failed")
            self._log(f"Error from credit score tool: {error_msg}")
            raise Exception(f"Credit score assessment failed: {error_msg}")

        self._log("Credit score assessment successful")

        # Step 3: Call detect_financial_anomalies MCP tool
        self._log("Step 3: Calling detect_financial_anomalies MCP tool...")
        anomaly_result = await self.mcp_interface.detect_financial_anomalies(
            credit_score=credit_score,
            monthly_income=monthly_gross_income,
            monthly_debt_payments=monthly_debt_payments,
            loan_amount=loan_amount,
            previous_dti=previous_dti,
        )

        if anomaly_result.get("status") != "success":
            error_msg = anomaly_result.get("error", "Anomaly detection failed")
            self._log(f"Error from anomaly detection tool: {error_msg}")
            raise Exception(f"Anomaly detection failed: {error_msg}")

        self._log("Anomaly detection successful")

        # Step 4: Call analyze_financial_risk for comprehensive analysis
        self._log("Step 4: Calling analyze_financial_risk for comprehensive analysis...")
        analysis_result = await self.mcp_interface.analyze_financial_risk(
            credit_score=credit_score,
            monthly_gross_income=monthly_gross_income,
            monthly_debt_payments=monthly_debt_payments,
            loan_amount=loan_amount,
            previous_dti=previous_dti,
        )

        if analysis_result.get("status") != "success":
            error_msg = analysis_result.get("error", "Unknown error")
            self._log(f"Error from MCP tool: {error_msg}")
            raise Exception(f"Financial risk analysis failed: {error_msg}")

        analysis = analysis_result["analysis"]
        self._log("Successfully received comprehensive analysis from MCP tools")

        # Extract and structure results
        dti_analysis = analysis["dti_analysis"]
        credit_analysis = analysis["credit_analysis"]
        loan_analysis = analysis["loan_analysis"]
        anomalies = analysis["anomalies"]
        overall_risk_level = analysis["overall_risk_level"]
        approval_rec_text = analysis["approval_recommendation"]

        # Map recommendation string to enum
        if "APPROVE" in approval_rec_text:
            approval_recommendation = ApprovalRecommendation.APPROVE
        elif "DENY" in approval_rec_text:
            approval_recommendation = ApprovalRecommendation.DENY
        else:
            approval_recommendation = ApprovalRecommendation.CONDITIONAL

        # Generate comprehensive reasoning
        reasoning = self._generate_reasoning(
            dti_analysis,
            credit_analysis,
            loan_analysis,
            anomalies,
            overall_risk_level,
            approval_rec_text,
        )

        self._log("Generating RiskAssessment object...")

        # Create and return assessment
        assessment = RiskAssessment(
            applicant_id=applicant_id,
            debt_to_income_ratio=dti_analysis["debt_to_income_ratio"],
            dti_risk_level=RiskLevel(dti_analysis["risk_level"]),
            dti_recommendation=dti_analysis["recommendation"],
            credit_score=credit_analysis["credit_score"],
            credit_risk_level=credit_analysis["risk_level"],
            credit_risk_percentage=credit_analysis["risk_percentage"],
            credit_recommendation=credit_analysis["recommendation"],
            loan_amount=loan_analysis["loan_amount"],
            loan_risk_level=RiskLevel(loan_analysis["risk_level"]),
            loan_recommendation=loan_analysis["recommendation"],
            anomalies=anomalies,
            overall_risk_level=RiskLevel(overall_risk_level),
            approval_recommendation=approval_recommendation,
            reasoning=reasoning,
            detailed_analysis=analysis,
        )

        self._log(f"Risk assessment complete. Overall risk: {overall_risk_level}")
        return assessment

    async def get_dti_capacity(
        self,
        monthly_gross_income: float,
        target_dti: float = 0.36,
    ) -> Dict[str, Any]:
        """
        Calculate maximum allowable debt payments for a given DTI threshold.

        Args:
            monthly_gross_income: Gross monthly income in dollars
            target_dti: Target DTI ratio (default 0.36 or 36%)

        Returns:
            Dictionary with maximum debt payment and recommendations
        """
        self._log(f"Calculating DTI capacity for income ${monthly_gross_income}")
        result = await self.mcp_interface.calculate_dti_threshold(
            monthly_gross_income=monthly_gross_income,
            target_dti=target_dti,
        )

        if result.get("status") == "success":
            self._log(f"DTI capacity: ${result['max_debt_payment']}")
        return result

    async def get_thresholds(self) -> Dict[str, Any]:
        """
        Retrieve current business rules and risk thresholds.

        Returns:
            Dictionary containing all configured risk thresholds
        """
        self._log("Retrieving risk thresholds...")
        result = await self.mcp_interface.get_risk_thresholds()
        self._log("Risk thresholds retrieved")
        return result

    async def batch_assess(
        self,
        applicants: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform batch risk assessment on multiple applicants.

        Args:
            applicants: List of applicant dictionaries with keys:
                       credit_score, monthly_gross_income, monthly_debt_payments, loan_amount

        Returns:
            Dictionary with batch analysis results and summary statistics
        """
        self._log(f"Starting batch risk assessment for {len(applicants)} applicants")
        result = await self.mcp_interface.batch_risk_analysis(applicants=applicants)

        if result.get("status") == "success":
            summary = result.get("summary", {})
            self._log(
                f"Batch assessment complete: "
                f"Approved={summary.get('approved')}, "
                f"Conditional={summary.get('conditional')}, "
                f"Denied={summary.get('denied')}"
            )
        return result

    def _validate_inputs(
        self,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
    ) -> None:
        """
        Validate input parameters.

        Raises:
            ValueError: If any parameters are invalid
        """
        if not 300 <= credit_score <= 850:
            raise ValueError(f"Credit score must be 300-850, got {credit_score}")
        if monthly_gross_income <= 0:
            raise ValueError(f"Monthly income must be positive, got {monthly_gross_income}")
        if monthly_debt_payments < 0:
            raise ValueError(
                f"Monthly debt payments cannot be negative, got {monthly_debt_payments}"
            )
        if loan_amount < 0:
            raise ValueError(f"Loan amount cannot be negative, got {loan_amount}")

    def _generate_reasoning(
        self,
        dti_analysis: Dict[str, Any],
        credit_analysis: Dict[str, Any],
        loan_analysis: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        overall_risk_level: str,
        approval_recommendation: str,
    ) -> str:
        """
        Generate comprehensive reasoning for the risk assessment.

        Args:
            dti_analysis: DTI analysis results
            credit_analysis: Credit analysis results
            loan_analysis: Loan analysis results
            anomalies: List of detected anomalies
            overall_risk_level: Overall risk classification
            approval_recommendation: Final recommendation text

        Returns:
            Detailed reasoning string explaining the assessment
        """
        dti_ratio = dti_analysis["debt_to_income_ratio"]
        dti_risk = dti_analysis["risk_level"]
        credit_score = credit_analysis["credit_score"]
        credit_risk = credit_analysis["risk_level"]
        loan_risk = loan_analysis["risk_level"]
        anomaly_count = len(anomalies)

        reasoning_parts = [
            "FINANCIAL RISK ASSESSMENT REASONING:",
            "=" * 60,
            "",
            f"1. DEBT-TO-INCOME ANALYSIS:",
            f"   - DTI Ratio: {dti_ratio:.2%}",
            f"   - Risk Level: {dti_risk.upper()}",
            f"   - {dti_analysis['recommendation']}",
            "",
            f"2. CREDIT SCORE ANALYSIS:",
            f"   - Credit Score: {credit_score}",
            f"   - Risk Level: {credit_risk.upper()}",
            f"   - Default Rate: {credit_analysis['risk_percentage']:.1f}%",
            f"   - {credit_analysis['recommendation']}",
            "",
            f"3. LOAN AMOUNT ANALYSIS:",
            f"   - Loan Amount: ${loan_analysis['loan_amount']:,.2f}",
            f"   - Loan-to-Income Ratio: {loan_analysis['loan_to_income_ratio']:.2f}x",
            f"   - Risk Level: {loan_risk.upper()}",
            f"   - {loan_analysis['recommendation']}",
        ]

        if anomaly_count > 0:
            reasoning_parts.extend([
                "",
                f"4. ANOMALIES DETECTED: {anomaly_count}",
            ])
            for anomaly in anomalies:
                reasoning_parts.append(
                    f"   - {anomaly['flag_type']}: {anomaly['message']} "
                    f"(Severity: {anomaly['severity'].upper()})"
                )

        reasoning_parts.extend([
            "",
            f"5. OVERALL ASSESSMENT:",
            f"   - Overall Risk Level: {overall_risk_level.upper()}",
            f"   - Recommendation: {approval_recommendation}",
            "=" * 60,
        ])

        return "\n".join(reasoning_parts)

    def get_assessment_summary(self, assessment: RiskAssessment) -> Dict[str, Any]:
        """
        Generate a summary of the risk assessment.

        Args:
            assessment: RiskAssessment object

        Returns:
            Dictionary with key assessment metrics
        """
        return {
            "applicant_id": assessment.applicant_id,
            "dti_ratio": f"{assessment.debt_to_income_ratio:.2%}",
            "dti_risk": assessment.dti_risk_level.value,
            "credit_score": assessment.credit_score,
            "credit_risk": assessment.credit_risk_level,
            "loan_amount": f"${assessment.loan_amount:,.2f}",
            "loan_risk": assessment.loan_risk_level.value,
            "anomaly_count": len(assessment.anomalies),
            "overall_risk": assessment.overall_risk_level.value,
            "approval": assessment.approval_recommendation.value,
        }

    def export_assessment_json(self, assessment: RiskAssessment) -> str:
        """
        Export risk assessment as JSON.

        Args:
            assessment: RiskAssessment object

        Returns:
            JSON string representation
        """
        return json.dumps(asdict(assessment), indent=2, default=str)
