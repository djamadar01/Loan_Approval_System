"""
ApplicantProfileAgent: Agent class that calls ApplicantDB MCP server tools.

This agent handles applicant profile data retrieval with comprehensive error handling,
data validation, and structured output generation including Income Stability Score,
Employment Risk, and Credit History Summary.
"""

import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Import the ApplicantDB tools
from mcp_servers.applicant_db import (
    get_applicant_profile,
    list_all_applicants,
    get_applicants_by_risk_level,
    get_applications_requiring_action
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
class IncomeStabilityAssessment:
    """Assessment of applicant's income stability."""
    score: int  # 0-100
    trend: str  # "increasing", "stable", "decreasing"
    volatility: str  # "low", "moderate", "high"
    average_monthly: float
    risk_indicator: str  # Derived: "healthy", "caution", "critical"

    def validate(self) -> None:
        """Validate income stability assessment."""
        if not (0 <= self.score <= 100):
            raise ValidationError(f"Income stability score must be 0-100, got {self.score}")
        if self.trend not in ["increasing", "stable", "decreasing"]:
            raise ValidationError(f"Invalid trend: {self.trend}")
        if self.volatility not in ["low", "moderate", "high"]:
            raise ValidationError(f"Invalid volatility: {self.volatility}")
        if self.average_monthly < 0:
            raise ValidationError(f"Average monthly income must be non-negative, got {self.average_monthly}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EmploymentRiskAssessment:
    """Assessment of applicant's employment risk."""
    risk_level: str  # "low", "medium", "high"
    rationale: str  # Explanation of risk level

    def validate(self) -> None:
        """Validate employment risk assessment."""
        if self.risk_level not in ["low", "medium", "high"]:
            raise ValidationError(f"Invalid risk level: {self.risk_level}")
        if not self.rationale or not isinstance(self.rationale, str):
            raise ValidationError("Rationale must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CreditHistorySummary:
    """Summary of applicant's credit history."""
    credit_score: int  # 300-850
    accounts_on_time: int
    accounts_late: int
    total_debt: float
    debt_to_income_ratio: float
    delinquencies: int
    credit_rating: str  # Derived: "excellent", "good", "fair", "poor"

    def validate(self) -> None:
        """Validate credit history summary."""
        if not (300 <= self.credit_score <= 850):
            raise ValidationError(f"Credit score must be 300-850, got {self.credit_score}")
        if self.accounts_on_time < 0 or self.accounts_late < 0:
            raise ValidationError("Account counts must be non-negative")
        if self.total_debt < 0:
            raise ValidationError(f"Total debt must be non-negative, got {self.total_debt}")
        if self.debt_to_income_ratio < 0:
            raise ValidationError(f"DTI ratio must be non-negative, got {self.debt_to_income_ratio}")
        if self.delinquencies < 0:
            raise ValidationError(f"Delinquencies must be non-negative, got {self.delinquencies}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ApplicantProfileSummary:
    """Structured output of applicant profile analysis."""
    applicant_id: str
    name: str
    email: str
    phone: str
    income_stability: IncomeStabilityAssessment
    employment_risk: EmploymentRiskAssessment
    credit_history: CreditHistorySummary
    application_status: str
    application_date: str
    completion_percentage: int
    missing_fields: List[str]
    overall_risk_score: float  # 0-100, derived aggregate
    recommendation: str  # Overall recommendation

    def validate(self) -> None:
        """Validate all components of profile summary."""
        if not self.applicant_id or not isinstance(self.applicant_id, str):
            raise ValidationError("Applicant ID must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Name must be a non-empty string")
        if not (0 <= self.completion_percentage <= 100):
            raise ValidationError(f"Completion percentage must be 0-100, got {self.completion_percentage}")
        if not (0 <= self.overall_risk_score <= 100):
            raise ValidationError(f"Overall risk score must be 0-100, got {self.overall_risk_score}")

        self.income_stability.validate()
        self.employment_risk.validate()
        self.credit_history.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "applicant_id": self.applicant_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "income_stability": self.income_stability.to_dict(),
            "employment_risk": self.employment_risk.to_dict(),
            "credit_history": self.credit_history.to_dict(),
            "application_status": self.application_status,
            "application_date": self.application_date,
            "completion_percentage": self.completion_percentage,
            "missing_fields": self.missing_fields,
            "overall_risk_score": self.overall_risk_score,
            "recommendation": self.recommendation
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


# ============================================================================
# Risk Calculation and Analysis Functions
# ============================================================================


def calculate_credit_rating(score: int) -> str:
    """Calculate credit rating from FICO score."""
    if score >= 750:
        return "excellent"
    elif score >= 700:
        return "good"
    elif score >= 650:
        return "fair"
    else:
        return "poor"


def calculate_income_risk_indicator(score: int, trend: str, volatility: str) -> str:
    """Calculate income risk indicator based on score, trend, and volatility."""
    if score >= 80 and trend in ["increasing", "stable"] and volatility in ["low"]:
        return "healthy"
    elif score >= 50 and volatility != "high":
        return "caution"
    else:
        return "critical"


def calculate_overall_risk_score(
    income_score: int,
    credit_score: int,
    dti_ratio: float,
    delinquencies: int,
    risk_level: str
) -> float:
    """Calculate aggregate risk score from multiple factors."""
    # Normalize factors to 0-100 scale
    income_component = income_score * 0.25  # Weight: 25%

    # Credit component: excellent=100, good=80, fair=60, poor=30
    credit_rating = calculate_credit_rating(credit_score)
    credit_component = {
        "excellent": 90,
        "good": 75,
        "fair": 55,
        "poor": 25
    }[credit_rating] * 0.25  # Weight: 25%

    # DTI component: safe < 43%, moderate 43-50%, risky > 50%
    if dti_ratio < 43:
        dti_component = 80 * 0.25
    elif dti_ratio < 50:
        dti_component = 50 * 0.25
    else:
        dti_component = 20 * 0.25

    # Delinquency component: 0=100, 1-2=70, 3+=30
    if delinquencies == 0:
        delinquency_component = 100 * 0.25
    elif delinquencies <= 2:
        delinquency_component = 70 * 0.25
    else:
        delinquency_component = 30 * 0.25

    # Risk level multiplier
    risk_multiplier = {"low": 1.0, "medium": 0.7, "high": 0.4}[risk_level]

    total_score = (income_component + credit_component + dti_component + delinquency_component) * risk_multiplier
    return min(max(total_score, 0), 100)  # Clamp to 0-100


def generate_employment_risk_rationale(
    income_score: int,
    trend: str,
    dti_ratio: float,
    delinquencies: int,
    risk_level: str
) -> str:
    """Generate rationale for employment risk assessment."""
    factors = []

    if income_score >= 80:
        factors.append("Strong income stability (score >= 80)")
    elif income_score >= 60:
        factors.append("Moderate income stability (score 60-79)")
    else:
        factors.append("Low income stability (score < 60)")

    if trend == "increasing":
        factors.append("Income trend is improving")
    elif trend == "decreasing":
        factors.append("Income trend is declining")

    if dti_ratio < 43:
        factors.append(f"Healthy DTI ratio ({dti_ratio:.1f}%)")
    elif dti_ratio < 50:
        factors.append(f"Moderate DTI ratio ({dti_ratio:.1f}%)")
    else:
        factors.append(f"High DTI ratio ({dti_ratio:.1f}%)")

    if delinquencies == 0:
        factors.append("No recent delinquencies")
    else:
        factors.append(f"{delinquencies} recent delinquencies")

    return "; ".join(factors)


def generate_overall_recommendation(
    overall_risk_score: float,
    completion_percentage: int,
    missing_fields: List[str],
    credit_score: int,
    dti_ratio: float
) -> str:
    """Generate overall recommendation based on profile analysis."""
    if completion_percentage < 60:
        return "REQUEST ADDITIONAL INFORMATION - Application is incomplete (< 60% complete). Cannot proceed without missing documents."

    if missing_fields:
        return f"CONDITIONAL APPROVAL - Pending receipt of: {', '.join(missing_fields)}. Re-evaluate upon completion."

    if credit_score < 600:
        return "REVIEW REQUIRED - Credit score is below acceptable threshold. Recommend senior review and additional verification."

    if dti_ratio > 50:
        return "REVIEW REQUIRED - Debt-to-income ratio exceeds safe limits. May require co-signer or collateral."

    if overall_risk_score >= 75:
        return "APPROVE - Strong profile with low to moderate risk indicators."

    if overall_risk_score >= 50:
        return "CONDITIONAL APPROVAL - Acceptable risk profile pending final verification steps."

    return "DENY - Risk profile indicates significant concerns. Recommend decline or extensive review."


# ============================================================================
# ApplicantProfileAgent Class
# ============================================================================


class ApplicantProfileAgent:
    """
    Agent for fetching and analyzing applicant profiles from ApplicantDB MCP server.

    This agent provides:
    - Applicant profile data retrieval
    - Comprehensive error handling and validation
    - Structured output with Income Stability Score, Employment Risk, and Credit History
    - Risk assessment and scoring
    - Recommendation generation
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the ApplicantProfileAgent.

        Args:
            verbose: Enable logging of operations
        """
        self.verbose = verbose
        self.logger = logger if verbose else None

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.logger:
            self.logger.info(message)

    def fetch_applicant_profile(self, applicant_id: str) -> ApplicantProfileSummary:
        """
        Fetch and analyze a complete applicant profile.

        Args:
            applicant_id: Unique applicant identifier (e.g., "APP001")

        Returns:
            ApplicantProfileSummary with structured analysis

        Raises:
            AgentError: If profile fetch or validation fails
        """
        self._log(f"Fetching profile for applicant {applicant_id}")

        try:
            # Fetch raw profile from MCP server
            raw_profile = get_applicant_profile(applicant_id)
            self._log(f"Successfully retrieved profile for {applicant_id}")

            # Extract and validate data components
            self._validate_raw_profile(raw_profile)

            # Build structured assessments
            income_stability = self._build_income_stability_assessment(
                raw_profile["income_stability"],
                raw_profile["employment_risk"]
            )

            employment_risk = self._build_employment_risk_assessment(
                raw_profile,
                income_stability
            )

            credit_history = self._build_credit_history_summary(
                raw_profile["credit_history"]
            )

            # Calculate aggregate metrics
            overall_risk_score = calculate_overall_risk_score(
                income_stability.score,
                credit_history.credit_score,
                credit_history.debt_to_income_ratio,
                credit_history.delinquencies,
                raw_profile["employment_risk"]
            )

            recommendation = generate_overall_recommendation(
                overall_risk_score,
                raw_profile["completeness"]["completion_percentage"],
                raw_profile["completeness"]["missing_fields"],
                credit_history.credit_score,
                credit_history.debt_to_income_ratio
            )

            # Build final profile summary
            profile_summary = ApplicantProfileSummary(
                applicant_id=raw_profile["applicant_id"],
                name=raw_profile["name"],
                email=raw_profile["email"],
                phone=raw_profile["phone"],
                income_stability=income_stability,
                employment_risk=employment_risk,
                credit_history=credit_history,
                application_status=raw_profile["status"],
                application_date=raw_profile["application_date"],
                completion_percentage=raw_profile["completeness"]["completion_percentage"],
                missing_fields=raw_profile["completeness"]["missing_fields"],
                overall_risk_score=overall_risk_score,
                recommendation=recommendation
            )

            # Validate complete profile
            profile_summary.validate()
            self._log(f"Profile analysis completed for {applicant_id}")

            return profile_summary

        except ValidationError as e:
            raise AgentError(f"Data validation error for {applicant_id}: {str(e)}")
        except ValueError as e:
            raise AgentError(f"Profile fetch error for {applicant_id}: {str(e)}")
        except Exception as e:
            raise AgentError(f"Unexpected error processing {applicant_id}: {str(e)}")

    def fetch_all_applicants(self) -> List[Dict[str, Any]]:
        """
        Fetch all applicants with summary information.

        Returns:
            List of applicant summaries

        Raises:
            AgentError: If fetch operation fails
        """
        self._log("Fetching all applicants")

        try:
            result = list_all_applicants()
            self._log(f"Successfully retrieved {result['total_count']} applicants")
            return result["applicants"]
        except Exception as e:
            raise AgentError(f"Error fetching all applicants: {str(e)}")

    def fetch_applicants_by_risk(self, risk_level: str) -> List[Dict[str, Any]]:
        """
        Fetch applicants filtered by risk level.

        Args:
            risk_level: Risk level filter ("low", "medium", or "high")

        Returns:
            List of applicants matching the risk level

        Raises:
            AgentError: If fetch operation or validation fails
        """
        self._log(f"Fetching applicants with risk level: {risk_level}")

        try:
            if risk_level not in ["low", "medium", "high"]:
                raise AgentError(f"Invalid risk level: {risk_level}. Must be 'low', 'medium', or 'high'.")

            result = get_applicants_by_risk_level(risk_level)
            self._log(f"Retrieved {result['count']} applicants with {risk_level} risk level")
            return result["applicants"]
        except ValueError as e:
            raise AgentError(f"Risk level fetch error: {str(e)}")
        except Exception as e:
            raise AgentError(f"Unexpected error fetching by risk level: {str(e)}")

    def fetch_applications_requiring_action(self) -> Dict[str, Any]:
        """
        Fetch applications with incomplete documentation or pending verification.

        Returns:
            Applications requiring action with details on missing documents

        Raises:
            AgentError: If fetch operation fails
        """
        self._log("Fetching applications requiring action")

        try:
            result = get_applications_requiring_action()
            self._log(f"Found {result['incomplete_count']} applications requiring action")
            return result
        except Exception as e:
            raise AgentError(f"Error fetching applications requiring action: {str(e)}")

    def analyze_risk_portfolio(self) -> Dict[str, Any]:
        """
        Analyze the complete portfolio of applicants by risk level.

        Returns:
            Portfolio analysis with breakdown by risk level

        Raises:
            AgentError: If analysis fails
        """
        self._log("Analyzing risk portfolio")

        try:
            portfolio = {}
            for risk_level in ["low", "medium", "high"]:
                result = get_applicants_by_risk_level(risk_level)
                portfolio[risk_level] = {
                    "count": result["count"],
                    "applicants": result["applicants"]
                }

            total = sum(p["count"] for p in portfolio.values())
            portfolio["total"] = total
            portfolio["distribution"] = {
                risk: round((portfolio[risk]["count"] / total * 100) if total > 0 else 0, 1)
                for risk in ["low", "medium", "high"]
            }

            self._log("Portfolio analysis completed")
            return portfolio
        except Exception as e:
            raise AgentError(f"Error analyzing risk portfolio: {str(e)}")

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _validate_raw_profile(self, profile: Dict[str, Any]) -> None:
        """
        Validate raw profile data from MCP server.

        Args:
            profile: Raw profile dictionary

        Raises:
            ValidationError: If validation fails
        """
        required_keys = [
            "applicant_id", "name", "email", "phone",
            "income_stability", "employment_risk", "credit_history",
            "completeness", "application_date", "status"
        ]

        for key in required_keys:
            if key not in profile:
                raise ValidationError(f"Missing required field: {key}")

        if not isinstance(profile.get("income_stability"), dict):
            raise ValidationError("income_stability must be a dictionary")
        if not isinstance(profile.get("credit_history"), dict):
            raise ValidationError("credit_history must be a dictionary")
        if not isinstance(profile.get("completeness"), dict):
            raise ValidationError("completeness must be a dictionary")

    def _build_income_stability_assessment(
        self,
        income_data: Dict[str, Any],
        risk_level: str
    ) -> IncomeStabilityAssessment:
        """Build income stability assessment from raw data."""
        score = income_data.get("score", 0)
        trend = income_data.get("trend", "unknown")
        volatility = income_data.get("volatility", "unknown")
        average_monthly = income_data.get("average_monthly", 0)

        risk_indicator = calculate_income_risk_indicator(score, trend, volatility)

        assessment = IncomeStabilityAssessment(
            score=score,
            trend=trend,
            volatility=volatility,
            average_monthly=average_monthly,
            risk_indicator=risk_indicator
        )
        assessment.validate()
        return assessment

    def _build_employment_risk_assessment(
        self,
        profile: Dict[str, Any],
        income_stability: IncomeStabilityAssessment
    ) -> EmploymentRiskAssessment:
        """Build employment risk assessment from profile data."""
        risk_level = profile["employment_risk"]
        dti_ratio = profile["credit_history"]["debt_to_income_ratio"]
        delinquencies = profile["credit_history"]["delinquencies"]

        rationale = generate_employment_risk_rationale(
            income_stability.score,
            income_stability.trend,
            dti_ratio,
            delinquencies,
            risk_level
        )

        assessment = EmploymentRiskAssessment(
            risk_level=risk_level,
            rationale=rationale
        )
        assessment.validate()
        return assessment

    def _build_credit_history_summary(
        self,
        credit_data: Dict[str, Any]
    ) -> CreditHistorySummary:
        """Build credit history summary from raw data."""
        credit_score = credit_data.get("credit_score", 300)
        credit_rating = calculate_credit_rating(credit_score)

        summary = CreditHistorySummary(
            credit_score=credit_score,
            accounts_on_time=credit_data.get("accounts_on_time", 0),
            accounts_late=credit_data.get("accounts_late", 0),
            total_debt=credit_data.get("total_debt", 0),
            debt_to_income_ratio=credit_data.get("debt_to_income_ratio", 0),
            delinquencies=credit_data.get("delinquencies", 0),
            credit_rating=credit_rating
        )
        summary.validate()
        return summary


# ============================================================================
# Example Usage and Testing
# ============================================================================


def main():
    """Demonstrate ApplicantProfileAgent usage."""
    print("\n" + "=" * 80)
    print("  ApplicantProfileAgent - Demonstration")
    print("=" * 80 + "\n")

    # Initialize agent
    agent = ApplicantProfileAgent(verbose=True)

    # Example 1: Fetch and analyze single applicant profile
    print("\n[Example 1: Fetch and Analyze Single Applicant Profile]")
    print("-" * 80)

    try:
        profile = agent.fetch_applicant_profile("APP001")
        print("\nFetched Profile Summary:")
        print(profile.to_json())
    except AgentError as e:
        print(f"Error: {e}")

    # Example 2: Fetch all applicants
    print("\n\n[Example 2: List All Applicants]")
    print("-" * 80)

    try:
        applicants = agent.fetch_all_applicants()
        print(f"\nFound {len(applicants)} applicants:")
        for app in applicants:
            print(f"  - {app['applicant_id']}: {app['name']} ({app['status']})")
    except AgentError as e:
        print(f"Error: {e}")

    # Example 3: Filter by risk level
    print("\n\n[Example 3: Filter Applicants by Risk Level]")
    print("-" * 80)

    try:
        for risk_level in ["low", "medium", "high"]:
            applicants = agent.fetch_applicants_by_risk(risk_level)
            print(f"\n{risk_level.upper()} Risk Applicants ({len(applicants)} total):")
            for app in applicants:
                print(f"  - {app['applicant_id']}: {app['name']} "
                      f"(Income: {app['income_stability_score']}, Credit: {app['credit_score']})")
    except AgentError as e:
        print(f"Error: {e}")

    # Example 4: Applications requiring action
    print("\n\n[Example 4: Applications Requiring Action]")
    print("-" * 80)

    try:
        result = agent.fetch_applications_requiring_action()
        print(f"\nIncomplete Applications: {result['incomplete_count']}")
        print(f"Missing Documentation: {result['missing_docs_count']}\n")
        for app in result["applications"]:
            print(f"  {app['applicant_id']}: {app['name']}")
            print(f"    Completion: {app['completion_percentage']}%")
            print(f"    Missing: {', '.join(app['missing_fields']) if app['missing_fields'] else 'None'}")
            print(f"    Required Actions: {', '.join(app['required_actions']) if app['required_actions'] else 'None'}\n")
    except AgentError as e:
        print(f"Error: {e}")

    # Example 5: Risk portfolio analysis
    print("\n[Example 5: Risk Portfolio Analysis]")
    print("-" * 80)

    try:
        portfolio = agent.analyze_risk_portfolio()
        print(f"\nTotal Applicants: {portfolio['total']}")
        print("\nDistribution by Risk Level:")
        for risk_level in ["low", "medium", "high"]:
            count = portfolio[risk_level]["count"]
            percentage = portfolio["distribution"][risk_level]
            print(f"  {risk_level.upper()}: {count} applicants ({percentage}%)")
    except AgentError as e:
        print(f"Error: {e}")

    # Example 6: Error handling - invalid applicant
    print("\n\n[Example 6: Error Handling - Invalid Applicant]")
    print("-" * 80)

    try:
        profile = agent.fetch_applicant_profile("INVALID")
    except AgentError as e:
        print(f"\nCaught AgentError (expected): {e}")

    # Example 7: Error handling - invalid risk level
    print("\n\n[Example 7: Error Handling - Invalid Risk Level]")
    print("-" * 80)

    try:
        applicants = agent.fetch_applicants_by_risk("invalid_risk")
    except AgentError as e:
        print(f"\nCaught AgentError (expected): {e}")

    print("\n" + "=" * 80)
    print("  Demonstration Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
