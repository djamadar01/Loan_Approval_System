"""ApplicantDB MCP server using FastMCP with mock database for applicant profiles."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json


# ============================================================================
# Pydantic Models for Type Safety
# ============================================================================


class EmploymentRisk(str, Enum):
    """Employment risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IncomeStabilityScore(BaseModel):
    """Income stability score with supporting metrics."""
    score: int = Field(ge=0, le=100, description="Income stability score from 0-100")
    trend: str = Field(description="Income trend: increasing, stable, or decreasing")
    volatility: str = Field(description="Income volatility: low, moderate, or high")
    average_monthly: float = Field(description="Average monthly income in dollars")


class CreditHistorySummary(BaseModel):
    """Summary of credit history."""
    credit_score: int = Field(ge=300, le=850, description="Credit score")
    accounts_on_time: int = Field(description="Number of accounts with on-time payments")
    accounts_late: int = Field(description="Number of accounts with late payments")
    total_debt: float = Field(description="Total outstanding debt in dollars")
    debt_to_income_ratio: float = Field(description="Debt-to-income ratio percentage")
    delinquencies: int = Field(description="Number of delinquencies in last 7 years")


class ApplicationCompletenessFlags(BaseModel):
    """Flags indicating missing or incomplete application data."""
    income_documentation_required: bool = Field(description="Missing income documentation")
    employment_verification_required: bool = Field(description="Missing employment verification")
    identity_verification_required: bool = Field(description="Missing identity verification")
    credit_authorization_required: bool = Field(description="Missing credit authorization")
    missing_fields: list[str] = Field(description="List of missing required fields")
    completion_percentage: int = Field(ge=0, le=100, description="Overall completion percentage")


class ApplicantProfile(BaseModel):
    """Complete applicant profile with all assessment data."""
    applicant_id: str = Field(description="Unique applicant identifier")
    name: str = Field(description="Applicant full name")
    email: str = Field(description="Applicant email address")
    phone: str = Field(description="Applicant phone number")
    income_stability: IncomeStabilityScore = Field(description="Income stability assessment")
    employment_risk: EmploymentRisk = Field(description="Employment risk level")
    credit_history: CreditHistorySummary = Field(description="Credit history summary")
    completeness: ApplicationCompletenessFlags = Field(description="Application completeness status")
    application_date: str = Field(description="Date application was submitted")
    status: str = Field(description="Current application status: submitted, under_review, approved, denied")


# ============================================================================
# Mock Database
# ============================================================================


MOCK_APPLICANTS_DATABASE = {
    "APP001": {
        "name": "Alice Johnson",
        "email": "alice.johnson@email.com",
        "phone": "555-0101",
        "income_stability": {
            "score": 85,
            "trend": "increasing",
            "volatility": "low",
            "average_monthly": 5250.00
        },
        "employment_risk": "low",
        "credit_history": {
            "credit_score": 750,
            "accounts_on_time": 8,
            "accounts_late": 0,
            "total_debt": 15000.00,
            "debt_to_income_ratio": 28.6,
            "delinquencies": 0
        },
        "completeness": {
            "income_documentation_required": False,
            "employment_verification_required": False,
            "identity_verification_required": False,
            "credit_authorization_required": False,
            "missing_fields": [],
            "completion_percentage": 100
        },
        "application_date": "2026-06-01",
        "status": "approved"
    },
    "APP002": {
        "name": "Bob Smith",
        "email": "bob.smith@email.com",
        "phone": "555-0102",
        "income_stability": {
            "score": 62,
            "trend": "stable",
            "volatility": "moderate",
            "average_monthly": 3800.00
        },
        "employment_risk": "medium",
        "credit_history": {
            "credit_score": 680,
            "accounts_on_time": 5,
            "accounts_late": 1,
            "total_debt": 28000.00,
            "debt_to_income_ratio": 73.7,
            "delinquencies": 1
        },
        "completeness": {
            "income_documentation_required": False,
            "employment_verification_required": True,
            "identity_verification_required": False,
            "credit_authorization_required": False,
            "missing_fields": ["employment_verification_letter"],
            "completion_percentage": 85
        },
        "application_date": "2026-06-05",
        "status": "under_review"
    },
    "APP003": {
        "name": "Carol Davis",
        "email": "carol.davis@email.com",
        "phone": "555-0103",
        "income_stability": {
            "score": 45,
            "trend": "decreasing",
            "volatility": "high",
            "average_monthly": 2900.00
        },
        "employment_risk": "high",
        "credit_history": {
            "credit_score": 580,
            "accounts_on_time": 2,
            "accounts_late": 4,
            "total_debt": 42000.00,
            "debt_to_income_ratio": 144.8,
            "delinquencies": 3
        },
        "completeness": {
            "income_documentation_required": True,
            "employment_verification_required": True,
            "identity_verification_required": False,
            "credit_authorization_required": True,
            "missing_fields": ["recent_pay_stubs", "employment_verification_letter", "credit_authorization_form"],
            "completion_percentage": 60
        },
        "application_date": "2026-06-08",
        "status": "submitted"
    },
    "APP004": {
        "name": "David Martinez",
        "email": "david.martinez@email.com",
        "phone": "555-0104",
        "income_stability": {
            "score": 92,
            "trend": "increasing",
            "volatility": "low",
            "average_monthly": 8100.00
        },
        "employment_risk": "low",
        "credit_history": {
            "credit_score": 800,
            "accounts_on_time": 12,
            "accounts_late": 0,
            "total_debt": 5000.00,
            "debt_to_income_ratio": 6.2,
            "delinquencies": 0
        },
        "completeness": {
            "income_documentation_required": False,
            "employment_verification_required": False,
            "identity_verification_required": False,
            "credit_authorization_required": False,
            "missing_fields": [],
            "completion_percentage": 100
        },
        "application_date": "2026-06-02",
        "status": "approved"
    },
    "APP005": {
        "name": "Emily Wilson",
        "email": "emily.wilson@email.com",
        "phone": "555-0105",
        "income_stability": {
            "score": 71,
            "trend": "stable",
            "volatility": "low",
            "average_monthly": 4500.00
        },
        "employment_risk": "low",
        "credit_history": {
            "credit_score": 720,
            "accounts_on_time": 9,
            "accounts_late": 0,
            "total_debt": 18000.00,
            "debt_to_income_ratio": 40.0,
            "delinquencies": 0
        },
        "completeness": {
            "income_documentation_required": False,
            "employment_verification_required": False,
            "identity_verification_required": True,
            "credit_authorization_required": False,
            "missing_fields": ["government_id_copy"],
            "completion_percentage": 92
        },
        "application_date": "2026-06-10",
        "status": "under_review"
    }
}


# ============================================================================
# Tool Implementation Functions
# ============================================================================


def get_applicant_profile(applicant_id: str) -> dict:
    """
    Retrieve complete applicant profile with assessment data.

    Provides Income Stability Score (0-100), Employment Risk Level,
    Credit History Summary, and Application Completeness Flags.

    Args:
        applicant_id: The unique identifier of the applicant (e.g., "APP001")

    Returns:
        Complete applicant profile as a structured dictionary containing:
        - applicant_id: Unique identifier
        - name: Applicant full name
        - email: Email address
        - phone: Phone number
        - income_stability: IncomeStabilityScore object with score (0-100), trend, volatility, average_monthly
        - employment_risk: Employment risk level (low/medium/high)
        - credit_history: CreditHistorySummary with credit_score, accounts_on_time, accounts_late, total_debt, debt_to_income_ratio, delinquencies
        - completeness: ApplicationCompletenessFlags with status of missing documents and completion_percentage
        - application_date: Date application was submitted
        - status: Current application status

    Raises:
        ValueError: If applicant_id is not found in the database
    """
    if applicant_id not in MOCK_APPLICANTS_DATABASE:
        raise ValueError(f"Applicant with ID '{applicant_id}' not found in database. Available IDs: {list(MOCK_APPLICANTS_DATABASE.keys())}")

    applicant_data = MOCK_APPLICANTS_DATABASE[applicant_id]

    try:
        profile = ApplicantProfile(
            applicant_id=applicant_id,
            name=applicant_data["name"],
            email=applicant_data["email"],
            phone=applicant_data["phone"],
            income_stability=IncomeStabilityScore(**applicant_data["income_stability"]),
            employment_risk=EmploymentRisk(applicant_data["employment_risk"]),
            credit_history=CreditHistorySummary(**applicant_data["credit_history"]),
            completeness=ApplicationCompletenessFlags(**applicant_data["completeness"]),
            application_date=applicant_data["application_date"],
            status=applicant_data["status"]
        )
        return json.loads(profile.model_dump_json())
    except Exception as e:
        raise ValueError(f"Error validating applicant data for {applicant_id}: {str(e)}")


def list_all_applicants() -> dict:
    """
    List all applicants in the database with basic information.

    Returns:
        Dictionary containing:
        - total_count: Total number of applicants
        - applicants: List of applicants with id, name, email, status, and application_date
    """
    applicants = []
    for app_id, app_data in MOCK_APPLICANTS_DATABASE.items():
        applicants.append({
            "applicant_id": app_id,
            "name": app_data["name"],
            "email": app_data["email"],
            "status": app_data["status"],
            "application_date": app_data["application_date"]
        })

    return {
        "total_count": len(applicants),
        "applicants": applicants
    }


def get_applicants_by_risk_level(risk_level: str) -> dict:
    """
    Filter applicants by employment risk level.

    Args:
        risk_level: Employment risk level to filter by ("low", "medium", or "high")

    Returns:
        Dictionary containing:
        - risk_level: The requested risk level
        - count: Number of applicants at this risk level
        - applicants: List of matching applicants with basic info and scores
    """
    valid_levels = ["low", "medium", "high"]
    if risk_level not in valid_levels:
        raise ValueError(f"Invalid risk level '{risk_level}'. Must be one of: {valid_levels}")

    matching = []
    for app_id, app_data in MOCK_APPLICANTS_DATABASE.items():
        if app_data["employment_risk"] == risk_level:
            matching.append({
                "applicant_id": app_id,
                "name": app_data["name"],
                "employment_risk": app_data["employment_risk"],
                "income_stability_score": app_data["income_stability"]["score"],
                "credit_score": app_data["credit_history"]["credit_score"],
                "status": app_data["status"]
            })

    return {
        "risk_level": risk_level,
        "count": len(matching),
        "applicants": matching
    }


def get_applications_requiring_action() -> dict:
    """
    Get all applications with incomplete documentation or requiring verification.

    Returns:
        Dictionary containing:
        - incomplete_count: Number of incomplete applications
        - missing_docs_count: Number needing document submission
        - applications: List of applications requiring action
    """
    applications = []
    incomplete_count = 0
    missing_docs_count = 0

    for app_id, app_data in MOCK_APPLICANTS_DATABASE.items():
        completeness = app_data["completeness"]
        if completeness["completion_percentage"] < 100 or any([
            completeness["income_documentation_required"],
            completeness["employment_verification_required"],
            completeness["identity_verification_required"],
            completeness["credit_authorization_required"]
        ]):
            incomplete_count += 1
            if completeness["missing_fields"]:
                missing_docs_count += 1

            applications.append({
                "applicant_id": app_id,
                "name": app_data["name"],
                "completion_percentage": completeness["completion_percentage"],
                "missing_fields": completeness["missing_fields"],
                "required_actions": [
                    action.replace("_required", "").replace("_", " ")
                    for action in [k for k in completeness.keys() if k.endswith("_required") and completeness[k]]
                ],
                "status": app_data["status"]
            })

    return {
        "incomplete_count": incomplete_count,
        "missing_docs_count": missing_docs_count,
        "applications": applications
    }


# ============================================================================
# FastMCP Server Factory
# ============================================================================


def create_applicant_db_server():
    """Factory function to create and configure the ApplicantDB MCP server."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("applicant_db")

    @server.tool()
    def get_applicant_profile_tool(applicant_id: str) -> dict:
        """
        Retrieve complete applicant profile with assessment data.

        Provides Income Stability Score (0-100), Employment Risk Level,
        Credit History Summary, and Application Completeness Flags.
        """
        return get_applicant_profile(applicant_id)

    @server.tool()
    def list_all_applicants_tool() -> dict:
        """List all applicants in the database with basic information."""
        return list_all_applicants()

    @server.tool()
    def get_applicants_by_risk_level_tool(risk_level: str) -> dict:
        """Filter applicants by employment risk level."""
        return get_applicants_by_risk_level(risk_level)

    @server.tool()
    def get_applications_requiring_action_tool() -> dict:
        """Get all applications with incomplete documentation or requiring verification."""
        return get_applications_requiring_action()

    return server


if __name__ == "__main__":
    import asyncio

    server = create_applicant_db_server()

    async def main():
        """Run the MCP server."""
        async with server:
            print("ApplicantDB MCP Server started. Listening for requests...")
            await asyncio.Event().wait()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down ApplicantDB MCP Server...")
