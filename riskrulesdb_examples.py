#!/usr/bin/env python3
"""
Production RiskRulesDB MCP Server - Practical Usage Examples
Demonstrates all major features and tool capabilities
"""

import json
import sys
sys.path.insert(0, '/home/ubuntu/Desktop/demo')

from riskrulesdb_production import RiskRulesDBServer


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_result(data):
    """Pretty print JSON result"""
    print(json.dumps(data, indent=2, default=str))


# ============================================================================
# Example 1: Basic DTI Calculation
# ============================================================================

def example_dti_calculations():
    """Demonstrate different DTI calculation methods"""
    print_section("Example 1: DTI Calculation Methods")

    server = RiskRulesDBServer("riskrulesdb_config.json")

    print("Applicant Profile:")
    print("  Monthly Gross Income: $5,000")
    print("  Existing Monthly Debt: $1,500")
    print("  Proposed Loan Payment: $500")

    # Standard method (existing debt only)
    print("\n--- Standard Method (Existing debt only) ---")
    result = server.calculate_debt_to_income(
        total_monthly_debt=1500,
        gross_monthly_income=5000,
        calculation_method="standard"
    )
    print_result(result)

    # Inclusive method (add proposed payment)
    print("\n--- Inclusive Method (Existing + Proposed) ---")
    result = server.calculate_debt_to_income(
        total_monthly_debt=1500,
        gross_monthly_income=5000,
        proposed_new_payment=500,
        calculation_method="inclusive"
    )
    print_result(result)

    # Conservative method (with income uncertainty)
    print("\n--- Conservative Method (Income * 0.8) ---")
    result = server.calculate_debt_to_income(
        total_monthly_debt=1500,
        gross_monthly_income=5000,
        proposed_new_payment=500,
        calculation_method="conservative"
    )
    print_result(result)


# ============================================================================
# Example 2: Credit Score Risk Assessment
# ============================================================================

def example_credit_score_assessment():
    """Demonstrate credit score risk assessment"""
    print_section("Example 2: Credit Score Risk Assessment")

    server = RiskRulesDBServer("riskrulesdb_config.json")

    test_cases = [
        {
            "credit_score": 800,
            "label": "Excellent Credit (800)",
            "industry": "mortgage"
        },
        {
            "credit_score": 700,
            "label": "Good Credit (700)",
            "industry": "personal_loans",
            "inquiries": 2,
            "late_payments": 0
        },
        {
            "credit_score": 650,
            "label": "Fair Credit (650)",
            "industry": "auto_loan",
            "inquiries": 5,
            "late_payments": 1
        },
        {
            "credit_score": 550,
            "label": "Poor Credit (550)",
            "industry": "credit_card",
            "inquiries": 8,
            "late_payments": 3
        },
        {
            "credit_score": 400,
            "label": "Very Poor Credit (400)",
            "industry": "personal_loans"
        }
    ]

    for test in test_cases:
        print(f"\n--- {test['label']} ---")
        result = server.assess_credit_score_risk(
            credit_score=test["credit_score"],
            industry_type=test.get("industry", "personal_loans"),
            inquiries_last_6_months=test.get("inquiries", 0),
            late_payments_last_24_months=test.get("late_payments", 0)
        )
        print_result(result)


# ============================================================================
# Example 3: Anomaly Detection
# ============================================================================

def example_anomaly_detection():
    """Demonstrate financial anomaly detection"""
    print_section("Example 3: Financial Anomaly Detection")

    server = RiskRulesDBServer("riskrulesdb_config.json")

    # Case 1: New Account with High Spending
    print("\n--- Case 1: New Account with Unusual Spending ---")
    result = server.detect_financial_anomalies(
        transaction_history=[
            {"date": "2024-01-01", "amount": 100, "category": "groceries"},
            {"date": "2024-01-02", "amount": 95, "category": "groceries"},
            {"date": "2024-01-03", "amount": 5000, "category": "jewelry"}
        ],
        account_age_days=15,
        baseline_monthly_spending=300,
        geographic_locations=["New York"]
    )
    print_result(result)

    # Case 2: Geographic Anomaly
    print("\n--- Case 2: Geographic Anomaly (Multiple Locations) ---")
    result = server.detect_financial_anomalies(
        transaction_history=[
            {"date": "2024-01-01", "amount": 100, "category": "groceries"},
            {"date": "2024-01-02", "amount": 150, "category": "gas"}
        ],
        account_age_days=365,
        baseline_monthly_spending=200,
        geographic_locations=["New York", "Los Angeles", "Miami", "Chicago", "Houston"]
    )
    print_result(result)

    # Case 3: Normal Activity (No Anomalies)
    print("\n--- Case 3: Normal Activity (No Anomalies) ---")
    result = server.detect_financial_anomalies(
        transaction_history=[
            {"date": "2024-01-01", "amount": 150, "category": "groceries"},
            {"date": "2024-01-02", "amount": 140, "category": "groceries"},
            {"date": "2024-01-03", "amount": 160, "category": "groceries"}
        ],
        account_age_days=365,
        baseline_monthly_spending=150,
        geographic_locations=["New York"]
    )
    print_result(result)


# ============================================================================
# Example 4: Business Rules and Compliance
# ============================================================================

def example_business_rules():
    """Demonstrate regulatory compliance checking"""
    print_section("Example 4: Business Rules and Compliance")

    server = RiskRulesDBServer("riskrulesdb_config.json")

    # Case 1: Compliant Applicant
    print("\n--- Case 1: Compliant Applicant ---")
    result = server.apply_business_rules(
        applicant_data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "credit_score": 720,
            "annual_income": 75000,
            "debt_to_income": 0.35,
            "credit_report_used": True,
            "account_age_days": 365,
            "applications_7_days": 1
        },
        loan_details={
            "requested_amount": 25000,
            "loan_type": "personal_loan"
        },
        rules_to_apply=["all"]
    )
    print_result(result)

    # Case 2: Applicant with ECOA Violation
    print("\n--- Case 2: ECOA Violation (Prohibited Criteria) ---")
    result = server.apply_business_rules(
        applicant_data={
            "name": "John Smith",
            "age": 68,  # Protected characteristic
            "race": "Caucasian",  # Protected characteristic
            "credit_score": 720,
            "annual_income": 75000,
            "debt_to_income": 0.35
        },
        loan_details={},
        rules_to_apply=["ecoa"]
    )
    print_result(result)

    # Case 3: Applicant with Lending Limit Violations
    print("\n--- Case 3: Lending Limits Violations ---")
    result = server.apply_business_rules(
        applicant_data={
            "credit_score": 480,  # Below minimum
            "annual_income": 10000,  # Below minimum
            "debt_to_income": 0.80  # Exceeds maximum
        },
        loan_details={"requested_amount": 50000},
        rules_to_apply=["lending_limits"]
    )
    print_result(result)

    # Case 4: Fraud Detection - Synthetic Identity
    print("\n--- Case 4: Fraud Detection (Synthetic Identity) ---")
    result = server.apply_business_rules(
        applicant_data={
            "account_age_days": 10,  # Very new
            "applications_7_days": 1,
            "annual_income": 50000
        },
        loan_details={"requested_amount": 75000},  # High for new account
        rules_to_apply=["fraud_detection"]
    )
    print_result(result)

    # Case 5: Fraud Detection - High Velocity
    print("\n--- Case 5: Fraud Detection (High Application Velocity) ---")
    result = server.apply_business_rules(
        applicant_data={
            "account_age_days": 365,
            "applications_7_days": 7,  # Multiple applications
            "annual_income": 50000
        },
        loan_details={"requested_amount": 25000},
        rules_to_apply=["fraud_detection"]
    )
    print_result(result)


# ============================================================================
# Example 5: Complete Risk Assessment
# ============================================================================

def example_complete_assessment():
    """Demonstrate complete risk assessment for applicant"""
    print_section("Example 5: Complete Risk Assessment")

    server = RiskRulesDBServer("riskrulesdb_config.json")

    applicants = [
        {
            "name": "Low-Risk Applicant",
            "data": {
                "total_monthly_debt": 1000,
                "gross_monthly_income": 5000,
                "proposed_new_payment": 300,
                "credit_score": 750,
                "industry_type": "personal_loans",
                "account_age_days": 1825,
                "transactions": [
                    {"date": "2024-01-01", "amount": 150},
                    {"date": "2024-01-02", "amount": 140},
                    {"date": "2024-01-03", "amount": 160}
                ],
                "annual_income": 60000,
                "debt_to_income": 0.20,
                "credit_report_used": True,
                "applications_7_days": 1,
                "requested_amount": 15000
            }
        },
        {
            "name": "Moderate-Risk Applicant",
            "data": {
                "total_monthly_debt": 1500,
                "gross_monthly_income": 4500,
                "proposed_new_payment": 400,
                "credit_score": 680,
                "industry_type": "personal_loans",
                "inquiries": 3,
                "late_payments": 1,
                "account_age_days": 365,
                "transactions": [
                    {"date": "2024-01-01", "amount": 200},
                    {"date": "2024-01-02", "amount": 150},
                    {"date": "2024-01-03", "amount": 2000}
                ],
                "annual_income": 54000,
                "debt_to_income": 0.40,
                "credit_report_used": True,
                "applications_7_days": 2,
                "requested_amount": 20000
            }
        },
        {
            "name": "High-Risk Applicant",
            "data": {
                "total_monthly_debt": 3000,
                "gross_monthly_income": 3500,
                "proposed_new_payment": 600,
                "credit_score": 550,
                "industry_type": "personal_loans",
                "inquiries": 8,
                "late_payments": 3,
                "account_age_days": 30,
                "transactions": [
                    {"date": "2024-01-01", "amount": 100},
                    {"date": "2024-01-02", "amount": 150},
                    {"date": "2024-01-03", "amount": 8000}
                ],
                "annual_income": 42000,
                "debt_to_income": 0.85,
                "credit_report_used": False,
                "applications_7_days": 5,
                "requested_amount": 50000
            }
        }
    ]

    for applicant_profile in applicants:
        print(f"\n{'='*70}")
        print(f"  {applicant_profile['name'].upper()}")
        print(f"{'='*70}\n")

        data = applicant_profile['data']

        # DTI Analysis
        print("1. DEBT-TO-INCOME ANALYSIS")
        print("-" * 40)
        dti_result = server.calculate_debt_to_income(
            total_monthly_debt=data["total_monthly_debt"],
            gross_monthly_income=data["gross_monthly_income"],
            proposed_new_payment=data.get("proposed_new_payment", 0),
            calculation_method="inclusive"
        )
        print(f"DTI Ratio: {dti_result['ratio']:.2%}")
        print(f"Risk Level: {dti_result['risk_level'].upper()}")
        print(f"Meets Lending Standards: {dti_result['meets_lending_standards']}")

        # Credit Analysis
        print("\n2. CREDIT SCORE ANALYSIS")
        print("-" * 40)
        credit_result = server.assess_credit_score_risk(
            credit_score=data["credit_score"],
            industry_type=data.get("industry_type", "personal_loans"),
            inquiries_last_6_months=data.get("inquiries", 0),
            late_payments_last_24_months=data.get("late_payments", 0)
        )
        print(f"Credit Score: {credit_result['credit_score']}")
        print(f"Category: {credit_result['category'].upper()}")
        print(f"Risk Level: {credit_result['risk_level'].upper()}")
        print(f"Recommendation: {credit_result['recommendation']}")

        # Anomaly Detection
        print("\n3. ANOMALY DETECTION")
        print("-" * 40)
        anomaly_result = server.detect_financial_anomalies(
            transaction_history=data.get("transactions", []),
            account_age_days=data.get("account_age_days", 0),
            baseline_monthly_spending=data.get("total_monthly_debt", 100)
        )
        print(f"Anomalies Detected: {len(anomaly_result['anomalies_detected'])}")
        print(f"Risk Score: {anomaly_result['risk_score']:.2f}")
        if anomaly_result['anomalies_detected']:
            for anomaly in anomaly_result['anomalies_detected']:
                print(f"  - {anomaly['type']}: {anomaly['description']}")

        # Compliance Check
        print("\n4. COMPLIANCE CHECK")
        print("-" * 40)
        compliance_result = server.apply_business_rules(
            applicant_data={
                "credit_score": data["credit_score"],
                "annual_income": data.get("annual_income", 0),
                "debt_to_income": data.get("debt_to_income", 0),
                "credit_report_used": data.get("credit_report_used", False),
                "account_age_days": data.get("account_age_days", 0),
                "applications_7_days": data.get("applications_7_days", 0)
            },
            loan_details={
                "requested_amount": data.get("requested_amount", 0)
            },
            rules_to_apply=["all"]
        )
        print(f"Overall Compliance: {'✓ PASS' if compliance_result['overall_compliance'] else '✗ FAIL'}")
        print(f"Rules Applied: {', '.join(compliance_result['rules_applied'])}")
        if compliance_result['violations']:
            print(f"Violations: {len(compliance_result['violations'])}")
            for violation in compliance_result['violations'][:3]:
                print(f"  - {violation}")

        # Final Recommendation
        print("\n5. FINAL RECOMMENDATION")
        print("-" * 40)
        overall_risk = "CRITICAL" if dti_result['risk_level'] == 'critical' or credit_result['risk_level'] == 'critical' else dti_result['risk_level'].upper()
        if compliance_result['overall_compliance']:
            if overall_risk == "LOW":
                recommendation = "APPROVE"
            elif overall_risk == "MODERATE":
                recommendation = "REVIEW & APPROVE"
            else:
                recommendation = "CONDITIONAL/REVIEW"
        else:
            recommendation = "DENY" if len(compliance_result['violations']) > 2 else "CONDITIONAL"

        print(f"Risk Level: {overall_risk}")
        print(f"Recommendation: {recommendation}")


# ============================================================================
# Example 6: Batch Processing
# ============================================================================

def example_configuration():
    """Show configuration details"""
    print_section("Example 6: Configuration Details")

    server = RiskRulesDBServer("riskrulesdb_config.json")

    print("Risk Thresholds:")
    print("-" * 40)
    print(json.dumps(server.config.get("risk_thresholds", {}), indent=2))

    print("\nIndustry Benchmarks:")
    print("-" * 40)
    print(json.dumps(server.config.get("industry_benchmarks", {}), indent=2))

    print("\nLending Limits:")
    print("-" * 40)
    limits = server.config.get("business_rules", {}).get("lending_limits", {})
    print(json.dumps(limits, indent=2))


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run all examples"""
    try:
        example_dti_calculations()
        example_credit_score_assessment()
        example_anomaly_detection()
        example_business_rules()
        example_complete_assessment()
        example_configuration()

        print_section("Examples Complete")
        print("All examples executed successfully!")
        print("\nKey Takeaways:")
        print("  ✓ DTI calculations support multiple methods")
        print("  ✓ Credit scores mapped to risk with industry benchmarks")
        print("  ✓ Statistical anomaly detection identifies suspicious activity")
        print("  ✓ Business rules enforce regulatory compliance")
        print("  ✓ Complete assessments aggregate all risk factors")
        print("  ✓ Configuration enables customization")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
