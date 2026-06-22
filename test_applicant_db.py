"""Test script for ApplicantDB MCP server."""

import sys
import json
from mcp_servers.applicant_db import (
    create_applicant_db_server,
    MOCK_APPLICANTS_DATABASE,
    ApplicantProfile,
    IncomeStabilityScore,
    EmploymentRisk,
    CreditHistorySummary,
    ApplicationCompletenessFlags
)


def test_pydantic_models():
    """Test that Pydantic models validate correctly."""
    print("Testing Pydantic Models...")

    # Test IncomeStabilityScore
    income = IncomeStabilityScore(
        score=85,
        trend="increasing",
        volatility="low",
        average_monthly=5250.00
    )
    assert income.score == 85
    assert income.trend == "increasing"
    print("✓ IncomeStabilityScore model works")

    # Test EmploymentRisk enum
    risk = EmploymentRisk.LOW
    assert risk.value == "low"
    print("✓ EmploymentRisk enum works")

    # Test CreditHistorySummary
    credit = CreditHistorySummary(
        credit_score=750,
        accounts_on_time=8,
        accounts_late=0,
        total_debt=15000.00,
        debt_to_income_ratio=28.6,
        delinquencies=0
    )
    assert credit.credit_score == 750
    print("✓ CreditHistorySummary model works")

    # Test ApplicationCompletenessFlags
    completeness = ApplicationCompletenessFlags(
        income_documentation_required=False,
        employment_verification_required=False,
        identity_verification_required=False,
        credit_authorization_required=False,
        missing_fields=[],
        completion_percentage=100
    )
    assert completeness.completion_percentage == 100
    print("✓ ApplicationCompletenessFlags model works")

    # Test full ApplicantProfile
    app_data = MOCK_APPLICANTS_DATABASE["APP001"]
    profile = ApplicantProfile(
        applicant_id="APP001",
        name=app_data["name"],
        email=app_data["email"],
        phone=app_data["phone"],
        income_stability=IncomeStabilityScore(**app_data["income_stability"]),
        employment_risk=EmploymentRisk(app_data["employment_risk"]),
        credit_history=CreditHistorySummary(**app_data["credit_history"]),
        completeness=ApplicationCompletenessFlags(**app_data["completeness"]),
        application_date=app_data["application_date"],
        status=app_data["status"]
    )
    assert profile.applicant_id == "APP001"
    assert profile.income_stability.score == 85
    print("✓ ApplicantProfile model works")

    print()


def test_mock_database():
    """Test that mock database has valid data."""
    print("Testing Mock Database...")

    assert len(MOCK_APPLICANTS_DATABASE) == 5
    print(f"✓ Database contains {len(MOCK_APPLICANTS_DATABASE)} applicants")

    # Verify all applicants have required fields
    required_fields = [
        "name", "email", "phone", "income_stability", "employment_risk",
        "credit_history", "completeness", "application_date", "status"
    ]

    for app_id, app_data in MOCK_APPLICANTS_DATABASE.items():
        for field in required_fields:
            assert field in app_data, f"Missing field '{field}' in {app_id}"
    print("✓ All applicants have required fields")

    # Check application IDs
    expected_ids = ["APP001", "APP002", "APP003", "APP004", "APP005"]
    actual_ids = list(MOCK_APPLICANTS_DATABASE.keys())
    assert set(actual_ids) == set(expected_ids)
    print(f"✓ Database contains expected applicant IDs: {actual_ids}")

    # Verify income stability scores are valid (0-100)
    for app_id, app_data in MOCK_APPLICANTS_DATABASE.items():
        score = app_data["income_stability"]["score"]
        assert 0 <= score <= 100, f"Invalid score {score} for {app_id}"
    print("✓ All income stability scores are in valid range (0-100)")

    # Verify employment risk levels
    for app_id, app_data in MOCK_APPLICANTS_DATABASE.items():
        risk = app_data["employment_risk"]
        assert risk in ["low", "medium", "high"], f"Invalid risk level {risk} for {app_id}"
    print("✓ All employment risk levels are valid")

    # Verify credit scores are in valid range
    for app_id, app_data in MOCK_APPLICANTS_DATABASE.items():
        score = app_data["credit_history"]["credit_score"]
        assert 300 <= score <= 850, f"Invalid credit score {score} for {app_id}"
    print("✓ All credit scores are in valid range (300-850)")

    print()


def test_server_tools():
    """Test that server tools work correctly."""
    print("Testing Server Tools...")

    # Import and create server - the decorator returns the original function
    # so we can test the tool functions directly
    from mcp_servers.applicant_db import (
        get_applicant_profile, list_all_applicants,
        get_applicants_by_risk_level, get_applications_requiring_action
    )

    # Test get_applicant_profile
    print("\nTesting get_applicant_profile...")
    result = get_applicant_profile("APP001")
    assert isinstance(result, dict)
    assert result["applicant_id"] == "APP001"
    assert result["name"] == "Alice Johnson"
    assert "income_stability" in result
    assert result["income_stability"]["score"] == 85
    assert "employment_risk" in result
    assert result["employment_risk"] == "low"
    assert "credit_history" in result
    assert "completeness" in result
    print("✓ get_applicant_profile returns complete profile")

    # Test get_applicant_profile - error case
    try:
        get_applicant_profile("INVALID_ID")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)
        print("✓ get_applicant_profile raises ValueError for invalid ID")

    # Test list_all_applicants
    print("\nTesting list_all_applicants...")
    result = list_all_applicants()
    assert isinstance(result, dict)
    assert result["total_count"] == 5
    assert len(result["applicants"]) == 5
    assert all("applicant_id" in app for app in result["applicants"])
    print("✓ list_all_applicants returns all applicants")

    # Test get_applicants_by_risk_level
    print("\nTesting get_applicants_by_risk_level...")
    result = get_applicants_by_risk_level("low")
    assert isinstance(result, dict)
    assert result["risk_level"] == "low"
    assert result["count"] > 0
    assert len(result["applicants"]) == result["count"]
    assert all(app["employment_risk"] == "low" for app in result["applicants"])
    print("✓ get_applicants_by_risk_level filters correctly")

    # Test get_applicants_by_risk_level - error case
    try:
        get_applicants_by_risk_level("invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid risk level" in str(e)
        print("✓ get_applicants_by_risk_level raises ValueError for invalid risk level")

    # Test get_applications_requiring_action
    print("\nTesting get_applications_requiring_action...")
    result = get_applications_requiring_action()
    assert isinstance(result, dict)
    assert "incomplete_count" in result
    assert "missing_docs_count" in result
    assert "applications" in result
    assert isinstance(result["applications"], list)
    print("✓ get_applications_requiring_action returns pending applications")

    print()


def main():
    """Run all tests."""
    print("=" * 70)
    print("ApplicantDB MCP Server - Test Suite")
    print("=" * 70)
    print()

    try:
        test_pydantic_models()
        test_mock_database()
        test_server_tools()

        print("=" * 70)
        print("All Tests Passed! ✓")
        print("=" * 70)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test Failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
