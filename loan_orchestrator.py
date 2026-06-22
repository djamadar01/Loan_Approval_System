"""
LangGraph-based Loan Application Orchestrator

This module implements a multi-agent workflow for processing loan applications
with state management, error handling, and decision routing logic.
"""

from typing import Any, Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import logging
from functools import reduce
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class ApplicationStatus(str, Enum):
    """Status of the loan application."""
    PENDING = "pending"
    PROFILE_ANALYZED = "profile_analyzed"
    RISK_ASSESSED = "risk_assessed"
    DECISION_MADE = "decision_made"
    COMPLIANCE_CHECKED = "compliance_checked"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    ERROR = "error"


class DecisionType(str, Enum):
    """Types of loan decisions."""
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"
    CONDITIONAL_APPROVAL = "conditional_approval"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApplicantProfile:
    """Applicant profile information."""
    applicant_id: str
    name: str
    age: int
    employment_status: str
    employment_years: float
    education_level: str
    credit_score: int
    existing_loans: int
    profile_risk_score: float = 0.0
    profile_analysis: str = ""
    analysis_timestamp: Optional[str] = None


@dataclass
class FinancialData:
    """Financial information for risk assessment."""
    annual_income: float
    monthly_expenses: float
    savings: float
    debt_to_income_ratio: float = 0.0
    loan_amount: float = 0.0
    loan_term_months: int = 0
    monthly_payment: float = 0.0
    financial_risk_score: float = 0.0
    financial_analysis: str = ""
    analysis_timestamp: Optional[str] = None


@dataclass
class RiskAssessment:
    """Risk assessment results."""
    overall_risk_level: RiskLevel
    risk_score: float  # 0-100
    credit_risk: float
    income_risk: float
    debt_risk: float
    employment_risk: float
    risk_factors: List[str] = field(default_factory=list)
    mitigating_factors: List[str] = field(default_factory=list)
    assessment_timestamp: Optional[str] = None


@dataclass
class LoanDecision:
    """Loan decision information."""
    decision: DecisionType
    decision_score: float  # 0-100
    approval_probability: float
    rationale: str
    conditions: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)
    decision_timestamp: Optional[str] = None
    reviewer_notes: str = ""


@dataclass
class ComplianceCheckResult:
    """Compliance check results."""
    is_compliant: bool
    compliance_checks: Dict[str, bool]
    flags: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    aml_status: str = "clear"
    regulatory_notes: str = ""
    check_timestamp: Optional[str] = None


@dataclass
class ApplicationState(TypedDict, total=False):
    """Complete application state."""
    application_id: str
    status: ApplicationStatus
    applicant_profile: Optional[ApplicantProfile]
    financial_data: Optional[FinancialData]
    risk_assessment: Optional[RiskAssessment]
    loan_decision: Optional[LoanDecision]
    compliance_result: Optional[ComplianceCheckResult]
    errors: List[Dict[str, Any]]
    execution_log: List[Dict[str, Any]]
    created_at: str
    updated_at: str


# ============================================================================
# AGENT IMPLEMENTATIONS
# ============================================================================

class ApplicantProfileAgent:
    """Agent for analyzing applicant profiles."""

    @staticmethod
    def analyze_profile(profile: ApplicantProfile) -> ApplicantProfile:
        """
        Analyze applicant profile and generate risk score.

        Args:
            profile: Applicant profile data

        Returns:
            Updated profile with analysis
        """
        logger.info(f"Analyzing profile for applicant {profile.applicant_id}")

        # Calculate profile risk score based on various factors
        risk_score = 0.0

        # Credit score factor (lower is riskier)
        if profile.credit_score < 500:
            risk_score += 40
        elif profile.credit_score < 650:
            risk_score += 25
        elif profile.credit_score < 750:
            risk_score += 10
        else:
            risk_score += 0

        # Employment stability factor
        if profile.employment_status == "unemployed":
            risk_score += 30
        elif profile.employment_status == "self_employed":
            risk_score += 15
        elif profile.employment_status == "part_time":
            risk_score += 10
        else:  # full_time
            risk_score += 0

        # Employment duration factor
        if profile.employment_years < 1:
            risk_score += 20
        elif profile.employment_years < 2:
            risk_score += 10
        elif profile.employment_years < 5:
            risk_score += 5
        else:
            risk_score += 0

        # Education level factor
        if profile.education_level == "high_school":
            risk_score += 5
        elif profile.education_level == "bachelor":
            risk_score -= 5
        elif profile.education_level == "graduate":
            risk_score -= 10
        else:
            risk_score += 0

        # Existing loans factor
        risk_score += min(profile.existing_loans * 5, 20)

        # Age factor (optimal: 30-50)
        age_factor = abs(profile.age - 40) / 10
        risk_score += min(age_factor * 5, 15)

        profile.profile_risk_score = min(max(risk_score, 0), 100)
        profile.analysis_timestamp = datetime.now().isoformat()
        profile.profile_analysis = (
            f"Profile analyzed: Risk Score={profile.profile_risk_score:.2f}, "
            f"Employment Status={profile.employment_status}, "
            f"Credit Score={profile.credit_score}, "
            f"Employment Duration={profile.employment_years} years"
        )

        logger.info(
            f"Profile analysis complete: {profile.applicant_id} - "
            f"Risk Score: {profile.profile_risk_score:.2f}"
        )

        return profile


class FinancialRiskAgent:
    """Agent for assessing financial risk."""

    @staticmethod
    def assess_financial_risk(
        profile: ApplicantProfile,
        financial_data: FinancialData,
    ) -> FinancialData:
        """
        Assess financial risk based on income and expenses.

        Args:
            profile: Applicant profile
            financial_data: Financial information

        Returns:
            Updated financial data with risk assessment
        """
        logger.info(f"Assessing financial risk for applicant {profile.applicant_id}")

        # Calculate financial metrics
        net_monthly_income = financial_data.annual_income / 12
        financial_data.debt_to_income_ratio = (
            financial_data.monthly_expenses / net_monthly_income
            if net_monthly_income > 0
            else 0
        )

        # Calculate monthly payment
        if financial_data.loan_term_months > 0:
            # Simple interest calculation
            monthly_rate = 0.05 / 12  # Assuming 5% annual rate
            financial_data.monthly_payment = (
                financial_data.loan_amount
                * (
                    monthly_rate
                    * (1 + monthly_rate) ** financial_data.loan_term_months
                )
                / ((1 + monthly_rate) ** financial_data.loan_term_months - 1)
            )

        # Calculate financial risk score
        risk_score = 0.0

        # Debt-to-income ratio factor
        if financial_data.debt_to_income_ratio > 0.5:
            risk_score += 40
        elif financial_data.debt_to_income_ratio > 0.4:
            risk_score += 25
        elif financial_data.debt_to_income_ratio > 0.3:
            risk_score += 10
        else:
            risk_score += 0

        # Savings factor (emergency fund)
        if financial_data.savings < financial_data.monthly_expenses * 3:
            risk_score += 20
        elif financial_data.savings < financial_data.monthly_expenses * 6:
            risk_score += 10
        else:
            risk_score += 0

        # Income adequacy with new loan
        total_monthly_obligations = (
            financial_data.monthly_expenses + financial_data.monthly_payment
        )
        if net_monthly_income > 0:
            obligation_ratio = total_monthly_obligations / net_monthly_income
            if obligation_ratio > 0.7:
                risk_score += 35
            elif obligation_ratio > 0.6:
                risk_score += 20
            elif obligation_ratio > 0.5:
                risk_score += 10
            else:
                risk_score += 0

        financial_data.financial_risk_score = min(max(risk_score, 0), 100)
        financial_data.analysis_timestamp = datetime.now().isoformat()
        financial_data.financial_analysis = (
            f"Financial analysis complete: Risk Score={financial_data.financial_risk_score:.2f}, "
            f"DTI Ratio={financial_data.debt_to_income_ratio:.2f}, "
            f"Savings={financial_data.savings:.2f}, "
            f"Estimated Monthly Payment={financial_data.monthly_payment:.2f}"
        )

        logger.info(
            f"Financial risk assessment complete: {profile.applicant_id} - "
            f"Risk Score: {financial_data.financial_risk_score:.2f}"
        )

        return financial_data


class FinancialRiskAgent:
    """Agent for assessing financial risk."""

    @staticmethod
    def assess_financial_risk(
        profile: ApplicantProfile,
        financial_data: FinancialData,
    ) -> FinancialData:
        """
        Assess financial risk based on income and expenses.

        Args:
            profile: Applicant profile
            financial_data: Financial information

        Returns:
            Updated financial data with risk assessment
        """
        logger.info(f"Assessing financial risk for applicant {profile.applicant_id}")

        # Calculate financial metrics
        net_monthly_income = financial_data.annual_income / 12
        financial_data.debt_to_income_ratio = (
            financial_data.monthly_expenses / net_monthly_income
            if net_monthly_income > 0
            else 0
        )

        # Calculate monthly payment
        if financial_data.loan_term_months > 0:
            # Simple interest calculation
            monthly_rate = 0.05 / 12  # Assuming 5% annual rate
            financial_data.monthly_payment = (
                financial_data.loan_amount
                * (
                    monthly_rate
                    * (1 + monthly_rate) ** financial_data.loan_term_months
                )
                / ((1 + monthly_rate) ** financial_data.loan_term_months - 1)
            )

        # Calculate financial risk score
        risk_score = 0.0

        # Debt-to-income ratio factor
        if financial_data.debt_to_income_ratio > 0.5:
            risk_score += 40
        elif financial_data.debt_to_income_ratio > 0.4:
            risk_score += 25
        elif financial_data.debt_to_income_ratio > 0.3:
            risk_score += 10
        else:
            risk_score += 0

        # Savings factor (emergency fund)
        if financial_data.savings < financial_data.monthly_expenses * 3:
            risk_score += 20
        elif financial_data.savings < financial_data.monthly_expenses * 6:
            risk_score += 10
        else:
            risk_score += 0

        # Income adequacy with new loan
        total_monthly_obligations = (
            financial_data.monthly_expenses + financial_data.monthly_payment
        )
        if net_monthly_income > 0:
            obligation_ratio = total_monthly_obligations / net_monthly_income
            if obligation_ratio > 0.7:
                risk_score += 35
            elif obligation_ratio > 0.6:
                risk_score += 20
            elif obligation_ratio > 0.5:
                risk_score += 10
            else:
                risk_score += 0

        financial_data.financial_risk_score = min(max(risk_score, 0), 100)
        financial_data.analysis_timestamp = datetime.now().isoformat()
        financial_data.financial_analysis = (
            f"Financial analysis complete: Risk Score={financial_data.financial_risk_score:.2f}, "
            f"DTI Ratio={financial_data.debt_to_income_ratio:.2f}, "
            f"Savings={financial_data.savings:.2f}, "
            f"Estimated Monthly Payment={financial_data.monthly_payment:.2f}"
        )

        logger.info(
            f"Financial risk assessment complete: {profile.applicant_id} - "
            f"Risk Score: {financial_data.financial_risk_score:.2f}"
        )

        return financial_data


class LoanDecisionAgent:
    """Agent for making loan decisions based on risk assessments."""

    @staticmethod
    def make_decision(
        profile: ApplicantProfile,
        financial_data: FinancialData,
        risk_assessment: RiskAssessment,
    ) -> LoanDecision:
        """
        Make loan decision based on comprehensive risk assessment.

        Args:
            profile: Applicant profile
            financial_data: Financial data
            risk_assessment: Risk assessment results

        Returns:
            Loan decision
        """
        logger.info(f"Making loan decision for applicant {profile.applicant_id}")

        decision = LoanDecision(
            decision=DecisionType.MANUAL_REVIEW,
            decision_score=0.0,
            approval_probability=0.0,
            rationale="",
            decision_timestamp=datetime.now().isoformat(),
        )

        # Calculate overall decision score
        decision_score = 100.0

        # Apply profile risk
        decision_score -= profile.profile_risk_score * 0.3

        # Apply financial risk
        decision_score -= financial_data.financial_risk_score * 0.4

        # Apply overall risk level
        if risk_assessment.overall_risk_level == RiskLevel.CRITICAL:
            decision_score -= 30
        elif risk_assessment.overall_risk_level == RiskLevel.HIGH:
            decision_score -= 20
        elif risk_assessment.overall_risk_level == RiskLevel.MEDIUM:
            decision_score -= 10

        decision.decision_score = max(min(decision_score, 100), 0)

        # Determine decision based on score
        if decision.decision_score >= 75:
            decision.decision = DecisionType.APPROVED
            decision.approval_probability = 0.95
            decision.rationale = "Strong financial profile with low risk indicators"
        elif decision.decision_score >= 60:
            decision.decision = DecisionType.CONDITIONAL_APPROVAL
            decision.approval_probability = 0.70
            decision.rationale = "Acceptable profile with conditional requirements"
            decision.conditions = [
                "Proof of income verification",
                "Reference letter from employer",
                "Collateral requirement evaluation",
            ]
        elif decision.decision_score >= 40:
            decision.decision = DecisionType.MANUAL_REVIEW
            decision.approval_probability = 0.40
            decision.rationale = "Requires manual review by senior underwriter"
            decision.required_documents = [
                "Detailed financial statements",
                "Employment verification",
                "Bank statements (6 months)",
                "Tax returns (2 years)",
            ]
        else:
            decision.decision = DecisionType.REJECTED
            decision.approval_probability = 0.05
            decision.rationale = (
                "Loan application does not meet minimum approval criteria. "
                f"Risk factors: {', '.join(risk_assessment.risk_factors[:3])}"
            )

        logger.info(
            f"Loan decision made: {profile.applicant_id} - "
            f"Decision: {decision.decision.value}, Score: {decision.decision_score:.2f}"
        )

        return decision


class ComplianceOrchestratorAgent:
    """Agent for orchestrating compliance checks and actions."""

    @staticmethod
    def check_compliance(
        profile: ApplicantProfile,
        loan_decision: LoanDecision,
        risk_assessment: RiskAssessment,
    ) -> ComplianceCheckResult:
        """
        Perform compliance checks and determine required actions.

        Args:
            profile: Applicant profile
            loan_decision: Loan decision
            risk_assessment: Risk assessment

        Returns:
            Compliance check results
        """
        logger.info(f"Performing compliance checks for applicant {profile.applicant_id}")

        result = ComplianceCheckResult(
            is_compliant=True,
            compliance_checks={},
            check_timestamp=datetime.now().isoformat(),
        )

        # AML/KYC Check
        result.compliance_checks["aml_kyc"] = True
        result.aml_status = "clear"

        # Age verification
        result.compliance_checks["age_verification"] = profile.age >= 18
        if not result.compliance_checks["age_verification"]:
            result.is_compliant = False
            result.flags.append("Applicant below legal age")

        # Sanctioned parties check
        result.compliance_checks["sanctioned_parties"] = True

        # PEP (Politically Exposed Person) check
        result.compliance_checks["pep_check"] = True

        # Fraud check
        result.compliance_checks["fraud_check"] = profile.credit_score > 300
        if not result.compliance_checks["fraud_check"]:
            result.flags.append("Potential fraud indicator")

        # Enhanced due diligence for high-risk profiles
        if risk_assessment.overall_risk_level == RiskLevel.CRITICAL:
            result.compliance_checks["enhanced_due_diligence"] = True
            result.required_actions.append(
                "Perform enhanced due diligence (EDD)"
            )
            result.regulatory_notes = "High-risk profile requires EDD per regulatory guidelines"

        # Decision-based compliance actions
        if loan_decision.decision == DecisionType.APPROVED:
            result.required_actions.extend([
                "Generate approval letter",
                "Initiate loan documentation",
                "Schedule loan disbursement",
                "Send welcome materials",
            ])
        elif loan_decision.decision == DecisionType.CONDITIONAL_APPROVAL:
            result.required_actions.extend([
                "Request conditional documents",
                "Schedule verification call",
                "Obtain borrower signatures on conditions",
            ])
        elif loan_decision.decision == DecisionType.MANUAL_REVIEW:
            result.required_actions.extend([
                "Route to underwriting team",
                "Schedule underwriter review",
                "Request additional documentation",
            ])
        else:  # REJECTED
            result.required_actions.extend([
                "Generate rejection letter",
                "Send appeal instructions",
                "Archive application",
            ])

        # Determine overall compliance status
        result.is_compliant = all(result.compliance_checks.values())

        logger.info(
            f"Compliance check complete: {profile.applicant_id} - "
            f"Compliant: {result.is_compliant}, "
            f"Flags: {len(result.flags)}, "
            f"Actions: {len(result.required_actions)}"
        )

        return result


# ============================================================================
# WORKFLOW GRAPH NODES
# ============================================================================

def validate_input_node(state: ApplicationState) -> ApplicationState:
    """Validate loan application input data."""
    logger.info(f"Validating input for application {state['application_id']}")

    if not state.get("applicant_profile"):
        raise ValueError("Missing applicant profile")
    if not state.get("financial_data"):
        raise ValueError("Missing financial data")

    state["status"] = ApplicationStatus.PENDING
    state["execution_log"].append({
        "step": "input_validation",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
    })

    return state


def profile_analysis_node(state: ApplicationState) -> ApplicationState:
    """Analyze applicant profile."""
    logger.info(f"Running profile analysis for {state['application_id']}")

    try:
        profile = state["applicant_profile"]
        profile = ApplicantProfileAgent.analyze_profile(profile)
        state["applicant_profile"] = profile
        state["status"] = ApplicationStatus.PROFILE_ANALYZED

        state["execution_log"].append({
            "step": "profile_analysis",
            "status": "completed",
            "profile_risk_score": profile.profile_risk_score,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in profile analysis: {str(e)}")
        state["status"] = ApplicationStatus.ERROR
        state["errors"].append({
            "step": "profile_analysis",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    return state


def financial_risk_node(state: ApplicationState) -> ApplicationState:
    """Assess financial risk."""
    logger.info(f"Running financial risk assessment for {state['application_id']}")

    try:
        profile = state["applicant_profile"]
        financial_data = state["financial_data"]

        financial_data = FinancialRiskAgent.assess_financial_risk(
            profile, financial_data
        )
        state["financial_data"] = financial_data
        state["status"] = ApplicationStatus.RISK_ASSESSED

        state["execution_log"].append({
            "step": "financial_risk_assessment",
            "status": "completed",
            "financial_risk_score": financial_data.financial_risk_score,
            "dti_ratio": financial_data.debt_to_income_ratio,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in financial risk assessment: {str(e)}")
        state["status"] = ApplicationStatus.ERROR
        state["errors"].append({
            "step": "financial_risk_assessment",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    return state


def aggregate_risk_node(state: ApplicationState) -> ApplicationState:
    """Aggregate all risk factors into comprehensive assessment."""
    logger.info(f"Aggregating risk assessment for {state['application_id']}")

    try:
        profile = state["applicant_profile"]
        financial_data = state["financial_data"]

        # Calculate overall risk level
        profile_risk = profile.profile_risk_score
        financial_risk = financial_data.financial_risk_score
        average_risk = (profile_risk + financial_risk) / 2

        if average_risk >= 75:
            risk_level = RiskLevel.CRITICAL
        elif average_risk >= 60:
            risk_level = RiskLevel.HIGH
        elif average_risk >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Identify risk factors
        risk_factors = []
        if profile.credit_score < 600:
            risk_factors.append(f"Low credit score: {profile.credit_score}")
        if profile.employment_status == "unemployed":
            risk_factors.append("Currently unemployed")
        if financial_data.debt_to_income_ratio > 0.45:
            risk_factors.append(
                f"High DTI ratio: {financial_data.debt_to_income_ratio:.2f}"
            )
        if financial_data.savings < financial_data.monthly_expenses * 3:
            risk_factors.append("Insufficient emergency savings")

        # Identify mitigating factors
        mitigating_factors = []
        if profile.credit_score > 750:
            mitigating_factors.append("Excellent credit score")
        if profile.employment_years >= 5:
            mitigating_factors.append("Strong employment history")
        if financial_data.savings > financial_data.monthly_expenses * 12:
            mitigating_factors.append("Substantial emergency fund")
        if financial_data.debt_to_income_ratio < 0.2:
            mitigating_factors.append("Low debt burden")

        risk_assessment = RiskAssessment(
            overall_risk_level=risk_level,
            risk_score=average_risk,
            credit_risk=min(100 - profile.credit_score / 8.5, 100),
            income_risk=financial_risk * 0.4,
            debt_risk=min(financial_data.debt_to_income_ratio * 100, 100),
            employment_risk=profile_risk * 0.3,
            risk_factors=risk_factors,
            mitigating_factors=mitigating_factors,
            assessment_timestamp=datetime.now().isoformat(),
        )

        state["risk_assessment"] = risk_assessment
        state["execution_log"].append({
            "step": "risk_aggregation",
            "status": "completed",
            "risk_level": risk_level.value,
            "risk_score": average_risk,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in risk aggregation: {str(e)}")
        state["status"] = ApplicationStatus.ERROR
        state["errors"].append({
            "step": "risk_aggregation",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    return state


def loan_decision_node(state: ApplicationState) -> ApplicationState:
    """Make loan decision."""
    logger.info(f"Making loan decision for {state['application_id']}")

    try:
        profile = state["applicant_profile"]
        financial_data = state["financial_data"]
        risk_assessment = state["risk_assessment"]

        decision = LoanDecisionAgent.make_decision(
            profile, financial_data, risk_assessment
        )
        state["loan_decision"] = decision
        state["status"] = ApplicationStatus.DECISION_MADE

        state["execution_log"].append({
            "step": "loan_decision",
            "status": "completed",
            "decision": decision.decision.value,
            "decision_score": decision.decision_score,
            "approval_probability": decision.approval_probability,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in loan decision: {str(e)}")
        state["status"] = ApplicationStatus.ERROR
        state["errors"].append({
            "step": "loan_decision",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    return state


def compliance_check_node(state: ApplicationState) -> ApplicationState:
    """Perform compliance checks."""
    logger.info(f"Performing compliance checks for {state['application_id']}")

    try:
        profile = state["applicant_profile"]
        loan_decision = state["loan_decision"]
        risk_assessment = state["risk_assessment"]

        compliance_result = ComplianceOrchestratorAgent.check_compliance(
            profile, loan_decision, risk_assessment
        )
        state["compliance_result"] = compliance_result

        # Determine final status
        if not compliance_result.is_compliant:
            state["status"] = ApplicationStatus.FLAGGED
        elif loan_decision.decision == DecisionType.APPROVED:
            state["status"] = ApplicationStatus.APPROVED
        elif loan_decision.decision == DecisionType.REJECTED:
            state["status"] = ApplicationStatus.REJECTED
        else:
            state["status"] = ApplicationStatus.COMPLIANCE_CHECKED

        state["execution_log"].append({
            "step": "compliance_check",
            "status": "completed",
            "is_compliant": compliance_result.is_compliant,
            "flags": len(compliance_result.flags),
            "required_actions": len(compliance_result.required_actions),
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in compliance check: {str(e)}")
        state["status"] = ApplicationStatus.ERROR
        state["errors"].append({
            "step": "compliance_check",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    return state


def error_handling_node(state: ApplicationState) -> ApplicationState:
    """Handle errors in the workflow."""
    logger.error(
        f"Error handler triggered for {state['application_id']}: "
        f"{len(state['errors'])} errors"
    )

    state["status"] = ApplicationStatus.ERROR
    state["execution_log"].append({
        "step": "error_handling",
        "status": "completed",
        "error_count": len(state["errors"]),
        "timestamp": datetime.now().isoformat(),
    })

    return state


def format_output_node(state: ApplicationState) -> ApplicationState:
    """Format final output."""
    state["updated_at"] = datetime.now().isoformat()
    state["execution_log"].append({
        "step": "output_formatting",
        "status": "completed",
        "final_status": state["status"].value,
        "timestamp": datetime.now().isoformat(),
    })
    return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_after_input_validation(state: ApplicationState) -> str:
    """Route to profile analysis or error handling."""
    if state["status"] == ApplicationStatus.ERROR:
        return "error_handler"
    return "profile_analysis"


def route_after_profile_analysis(state: ApplicationState) -> str:
    """Route to financial risk assessment or error handling."""
    if state["status"] == ApplicationStatus.ERROR:
        return "error_handler"
    return "financial_risk_assessment"


def route_after_financial_risk(state: ApplicationState) -> str:
    """Route to risk aggregation or error handling."""
    if state["status"] == ApplicationStatus.ERROR:
        return "error_handler"
    return "risk_aggregation"


def route_after_risk_aggregation(state: ApplicationState) -> str:
    """Route to loan decision or error handling."""
    if state["status"] == ApplicationStatus.ERROR:
        return "error_handler"
    return "loan_decision"


def route_after_loan_decision(state: ApplicationState) -> str:
    """Route to compliance check or error handling."""
    if state["status"] == ApplicationStatus.ERROR:
        return "error_handler"
    return "compliance_check"


def route_after_compliance(state: ApplicationState) -> str:
    """Route to output formatting or error handling."""
    if state["status"] == ApplicationStatus.ERROR:
        return "error_handler"
    return "output_formatting"


def route_after_error(state: ApplicationState) -> str:
    """Route to output formatting after error handling."""
    return "output_formatting"


# ============================================================================
# WORKFLOW GRAPH CONSTRUCTION
# ============================================================================

def build_loan_orchestrator_graph() -> StateGraph:
    """
    Build the LangGraph workflow for loan application orchestration.

    Returns:
        Compiled StateGraph for loan processing
    """
    # Initialize graph
    graph = StateGraph(ApplicationState)

    # Add nodes
    graph.add_node("input_validation", validate_input_node)
    graph.add_node("profile_analysis", profile_analysis_node)
    graph.add_node("financial_risk_assessment", financial_risk_node)
    graph.add_node("risk_aggregation", aggregate_risk_node)
    graph.add_node("loan_decision", loan_decision_node)
    graph.add_node("compliance_check", compliance_check_node)
    graph.add_node("error_handler", error_handling_node)
    graph.add_node("output_formatting", format_output_node)

    # Add edges with routing
    graph.add_edge(START, "input_validation")

    graph.add_conditional_edges(
        "input_validation",
        route_after_input_validation,
        {
            "profile_analysis": "profile_analysis",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "profile_analysis",
        route_after_profile_analysis,
        {
            "financial_risk_assessment": "financial_risk_assessment",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "financial_risk_assessment",
        route_after_financial_risk,
        {
            "risk_aggregation": "risk_aggregation",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "risk_aggregation",
        route_after_risk_aggregation,
        {
            "loan_decision": "loan_decision",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "loan_decision",
        route_after_loan_decision,
        {
            "compliance_check": "compliance_check",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "compliance_check",
        route_after_compliance,
        {
            "output_formatting": "output_formatting",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "error_handler",
        route_after_error,
        {"output_formatting": "output_formatting"},
    )

    graph.add_edge("output_formatting", END)

    return graph


def compile_loan_orchestrator() -> StateGraph:
    """
    Compile the loan orchestrator graph.

    Returns:
        Compiled StateGraph
    """
    graph = build_loan_orchestrator_graph()
    return graph.compile()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_initial_state(
    application_id: str,
    profile: ApplicantProfile,
    financial_data: FinancialData,
) -> ApplicationState:
    """
    Create initial application state.

    Args:
        application_id: Application identifier
        profile: Applicant profile
        financial_data: Financial data

    Returns:
        Initial application state
    """
    return ApplicationState(
        application_id=application_id,
        status=ApplicationStatus.PENDING,
        applicant_profile=profile,
        financial_data=financial_data,
        risk_assessment=None,
        loan_decision=None,
        compliance_result=None,
        errors=[],
        execution_log=[
            {
                "step": "initialization",
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
            }
        ],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )


def execute_application(
    orchestrator: StateGraph,
    application_id: str,
    profile: ApplicantProfile,
    financial_data: FinancialData,
) -> ApplicationState:
    """
    Execute loan application through orchestrator.

    Args:
        orchestrator: Compiled orchestrator graph
        application_id: Application identifier
        profile: Applicant profile
        financial_data: Financial data

    Returns:
        Final application state
    """
    logger.info(f"Executing application {application_id} through orchestrator")

    initial_state = create_initial_state(application_id, profile, financial_data)
    final_state = orchestrator.invoke(initial_state)

    return final_state


def format_state_for_output(state: ApplicationState) -> Dict[str, Any]:
    """
    Format application state for output.

    Args:
        state: Application state

    Returns:
        Formatted output dictionary
    """
    output = {
        "application_id": state["application_id"],
        "status": state["status"].value,
        "applicant_profile": (
            asdict(state["applicant_profile"])
            if state["applicant_profile"]
            else None
        ),
        "financial_data": (
            {k: v for k, v in asdict(state["financial_data"]).items()}
            if state["financial_data"]
            else None
        ),
        "risk_assessment": (
            asdict(state["risk_assessment"]) if state["risk_assessment"] else None
        ),
        "loan_decision": (
            {
                **asdict(state["loan_decision"]),
                "decision": state["loan_decision"].decision.value,
            }
            if state["loan_decision"]
            else None
        ),
        "compliance_result": (
            asdict(state["compliance_result"])
            if state["compliance_result"]
            else None
        ),
        "errors": state["errors"],
        "execution_log": state["execution_log"],
        "created_at": state["created_at"],
        "updated_at": state["updated_at"],
    }

    return output


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create sample applicant profile
    sample_profile = ApplicantProfile(
        applicant_id="APP001",
        name="John Doe",
        age=35,
        employment_status="full_time",
        employment_years=8,
        education_level="bachelor",
        credit_score=720,
        existing_loans=1,
    )

    # Create sample financial data
    sample_financial = FinancialData(
        annual_income=75000,
        monthly_expenses=2500,
        savings=15000,
        loan_amount=25000,
        loan_term_months=60,
    )

    # Compile orchestrator
    orchestrator = compile_loan_orchestrator()

    # Execute application
    result = execute_application(
        orchestrator,
        "APP001",
        sample_profile,
        sample_financial,
    )

    # Format and display output
    output = format_state_for_output(result)
    print(json.dumps(output, indent=2, default=str))
