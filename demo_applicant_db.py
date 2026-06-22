"""Demonstration script for ApplicantDB MCP server."""

import json
from mcp_servers.applicant_db import (
    get_applicant_profile,
    list_all_applicants,
    get_applicants_by_risk_level,
    get_applications_requiring_action,
    MOCK_APPLICANTS_DATABASE
)


def print_separator(title: str = ""):
    """Print a formatted separator."""
    if title:
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}\n")
    else:
        print(f"\n{'-' * 70}\n")


def demo_get_applicant_profile():
    """Demonstrate get_applicant_profile tool."""
    print_separator("get_applicant_profile - Retrieve Complete Profile")

    app_id = "APP001"
    print(f"Retrieving profile for: {app_id}\n")

    profile = get_applicant_profile(app_id)

    print(f"Name: {profile['name']}")
    print(f"Email: {profile['email']}")
    print(f"Phone: {profile['phone']}")
    print(f"Status: {profile['status']}")
    print(f"Application Date: {profile['application_date']}\n")

    print("Income Stability:")
    print(f"  - Score (0-100): {profile['income_stability']['score']}")
    print(f"  - Trend: {profile['income_stability']['trend']}")
    print(f"  - Volatility: {profile['income_stability']['volatility']}")
    print(f"  - Average Monthly Income: ${profile['income_stability']['average_monthly']:,.2f}\n")

    print(f"Employment Risk: {profile['employment_risk'].upper()}\n")

    print("Credit History:")
    credit = profile['credit_history']
    print(f"  - Credit Score: {credit['credit_score']}")
    print(f"  - Accounts On Time: {credit['accounts_on_time']}")
    print(f"  - Accounts Late: {credit['accounts_late']}")
    print(f"  - Total Debt: ${credit['total_debt']:,.2f}")
    print(f"  - Debt-to-Income Ratio: {credit['debt_to_income_ratio']:.1f}%")
    print(f"  - Delinquencies: {credit['delinquencies']}\n")

    print("Application Completeness:")
    comp = profile['completeness']
    print(f"  - Completion: {comp['completion_percentage']}%")
    print(f"  - Income Documentation Required: {comp['income_documentation_required']}")
    print(f"  - Employment Verification Required: {comp['employment_verification_required']}")
    print(f"  - Identity Verification Required: {comp['identity_verification_required']}")
    print(f"  - Credit Authorization Required: {comp['credit_authorization_required']}")
    if comp['missing_fields']:
        print(f"  - Missing Fields: {', '.join(comp['missing_fields'])}")
    else:
        print(f"  - Missing Fields: None")


def demo_list_all_applicants():
    """Demonstrate list_all_applicants tool."""
    print_separator("list_all_applicants - View All Applications")

    result = list_all_applicants()
    print(f"Total Applicants: {result['total_count']}\n")
    print(f"{'ID':<8} {'Name':<20} {'Email':<30} {'Status':<15} {'App Date'}")
    print("-" * 85)

    for app in result['applicants']:
        print(
            f"{app['applicant_id']:<8} "
            f"{app['name']:<20} "
            f"{app['email']:<30} "
            f"{app['status']:<15} "
            f"{app['application_date']}"
        )


def demo_get_applicants_by_risk_level():
    """Demonstrate get_applicants_by_risk_level tool."""
    print_separator("get_applicants_by_risk_level - Filter by Risk")

    for risk_level in ["low", "medium", "high"]:
        result = get_applicants_by_risk_level(risk_level)
        print(f"\nEmployment Risk: {risk_level.upper()}")
        print(f"Count: {result['count']}\n")

        for app in result['applicants']:
            print(
                f"  - {app['applicant_id']}: {app['name']} "
                f"(Income Score: {app['income_stability_score']}, "
                f"Credit: {app['credit_score']}, "
                f"Status: {app['status']})"
            )


def demo_get_applications_requiring_action():
    """Demonstrate get_applications_requiring_action tool."""
    print_separator("get_applications_requiring_action - Pending Work")

    result = get_applications_requiring_action()
    print(f"Incomplete Applications: {result['incomplete_count']}")
    print(f"Missing Documentation: {result['missing_docs_count']}\n")

    if result['applications']:
        print("Applications Requiring Action:\n")
        for app in result['applications']:
            print(f"ID: {app['applicant_id']}")
            print(f"  Name: {app['name']}")
            print(f"  Completion: {app['completion_percentage']}%")
            print(f"  Status: {app['status']}")

            if app['missing_fields']:
                print(f"  Missing Documents:")
                for field in app['missing_fields']:
                    print(f"    - {field}")

            if app['required_actions']:
                print(f"  Required Actions:")
                for action in app['required_actions']:
                    print(f"    - {action}")

            print()
    else:
        print("No applications requiring action.")


def demo_error_handling():
    """Demonstrate error handling."""
    print_separator("Error Handling - Invalid Requests")

    print("Attempting to retrieve non-existent applicant (APP999):")
    try:
        get_applicant_profile("APP999")
    except ValueError as e:
        print(f"  Error: {e}\n")

    print("Attempting to filter by invalid risk level (invalid):")
    try:
        get_applicants_by_risk_level("invalid")
    except ValueError as e:
        print(f"  Error: {e}\n")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  ApplicantDB MCP Server - Demonstration".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    demo_get_applicant_profile()
    demo_list_all_applicants()
    demo_get_applicants_by_risk_level()
    demo_get_applications_requiring_action()
    demo_error_handling()

    print_separator()
    print("Demonstration Complete!")
    print()


if __name__ == "__main__":
    main()
