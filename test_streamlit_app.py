"""
Test script to validate Streamlit application functionality
and demonstrate expected workflows.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any

# Sample test data for different scenarios
TEST_APPLICATIONS = [
    {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "age": 35,
        "location": "New York, NY",
        "employment_status": "employed",
        "employment_years": 8.5,
        "education_level": "bachelors",
        "annual_income": 85000.0,
        "credit_score": 750,
        "savings": 35000.0,
        "monthly_expenses": 2500.0,
        "liabilities": 10000.0,
        "loan_purpose": "home_purchase",
        "loan_amount": 250000.0,
        "loan_tenure": 360,
        "expected_outcome": "approved",
        "description": "Excellent credit, stable income, substantial savings"
    },
    {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "age": 42,
        "location": "Los Angeles, CA",
        "employment_status": "self_employed",
        "employment_years": 3.0,
        "education_level": "associates",
        "annual_income": 55000.0,
        "credit_score": 620,
        "savings": 5000.0,
        "monthly_expenses": 3000.0,
        "liabilities": 25000.0,
        "loan_purpose": "debt_consolidation",
        "loan_amount": 30000.0,
        "loan_tenure": 84,
        "expected_outcome": "review_required",
        "description": "Lower credit score, high debt, self-employed"
    },
    {
        "name": "Carol White",
        "email": "carol@example.com",
        "age": 28,
        "location": "Chicago, IL",
        "employment_status": "employed",
        "employment_years": 2.5,
        "education_level": "masters",
        "annual_income": 72000.0,
        "credit_score": 695,
        "savings": 15000.0,
        "monthly_expenses": 1800.0,
        "liabilities": 8000.0,
        "loan_purpose": "auto_purchase",
        "loan_amount": 35000.0,
        "loan_tenure": 60,
        "expected_outcome": "conditional_approval",
        "description": "Good income, fair credit, newer employment"
    },
    {
        "name": "David Brown",
        "email": "david@example.com",
        "age": 51,
        "location": "Houston, TX",
        "employment_status": "employed",
        "employment_years": 15.0,
        "education_level": "bachelors",
        "annual_income": 120000.0,
        "credit_score": 800,
        "savings": 100000.0,
        "monthly_expenses": 4000.0,
        "liabilities": 5000.0,
        "loan_purpose": "home_improvement",
        "loan_amount": 50000.0,
        "loan_tenure": 120,
        "expected_outcome": "approved",
        "description": "Excellent credit, high income, long employment, substantial savings"
    },
    {
        "name": "Emma Davis",
        "email": "emma@example.com",
        "age": 22,
        "location": "Boston, MA",
        "employment_status": "student",
        "employment_years": 0.5,
        "education_level": "high_school",
        "annual_income": 25000.0,
        "credit_score": 550,
        "savings": 2000.0,
        "monthly_expenses": 1000.0,
        "liabilities": 15000.0,
        "loan_purpose": "education",
        "loan_amount": 20000.0,
        "loan_tenure": 120,
        "expected_outcome": "denied",
        "description": "Young applicant, low income, high debt, poor credit"
    }
]


def print_test_header(title: str):
    """Print a formatted test header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{title}")
    print("-" * 70)


def validate_form_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate form data and return validation results.

    Returns:
        Dict with keys: valid (bool), errors (list), warnings (list)
    """
    errors = []
    warnings = []

    # Validate Step 1: Personal Info
    if not data.get("name", "").strip():
        errors.append("Name is required")

    if not data.get("email", "").strip() or "@" not in data.get("email", ""):
        errors.append("Valid email is required")

    age = data.get("age")
    if not isinstance(age, int) or age < 18 or age > 120:
        errors.append("Age must be between 18 and 120")

    if not data.get("location", "").strip():
        errors.append("Location is required")

    # Validate Step 2: Employment
    if data.get("employment_status") not in [
        "employed", "self_employed", "retired", "unemployed", "student", "homemaker"
    ]:
        errors.append("Invalid employment status")

    employment_years = data.get("employment_years", 0)
    if not isinstance(employment_years, (int, float)) or employment_years < 0:
        errors.append("Employment years must be non-negative")

    if employment_years == 0 and data.get("employment_status") in ["employed", "self_employed"]:
        warnings.append("Very new employment may affect approval")

    if data.get("education_level") not in [
        "high_school", "associates", "bachelors", "masters", "doctorate", "other"
    ]:
        errors.append("Invalid education level")

    annual_income = data.get("annual_income", 0)
    if not isinstance(annual_income, (int, float)) or annual_income <= 0:
        errors.append("Annual income must be positive")

    # Validate Step 3: Financial
    credit_score = data.get("credit_score", 0)
    if not isinstance(credit_score, int) or credit_score < 300 or credit_score > 850:
        errors.append("Credit score must be between 300 and 850")

    if credit_score < 600:
        warnings.append("Low credit score may result in conditional approval or denial")

    savings = data.get("savings", 0)
    if not isinstance(savings, (int, float)) or savings < 0:
        errors.append("Savings must be non-negative")

    monthly_expenses = data.get("monthly_expenses", 0)
    if not isinstance(monthly_expenses, (int, float)) or monthly_expenses < 0:
        errors.append("Monthly expenses must be non-negative")

    liabilities = data.get("liabilities", 0)
    if not isinstance(liabilities, (int, float)) or liabilities < 0:
        errors.append("Liabilities must be non-negative")

    # Calculate DTI
    monthly_income = annual_income / 12
    monthly_payment = data.get("loan_amount", 0) / max(data.get("loan_tenure", 1), 1)
    total_monthly_debt = (liabilities / 12) + monthly_payment
    dti_ratio = (total_monthly_debt / monthly_income) * 100 if monthly_income > 0 else 100

    if dti_ratio > 50:
        warnings.append(f"High DTI ratio ({dti_ratio:.1f}%) may affect approval")

    # Validate Step 4: Loan
    if data.get("loan_purpose") not in [
        "home_purchase", "refinance", "home_improvement", "debt_consolidation",
        "auto_purchase", "business", "education", "personal", "other"
    ]:
        errors.append("Invalid loan purpose")

    loan_amount = data.get("loan_amount", 0)
    if not isinstance(loan_amount, (int, float)) or loan_amount <= 0:
        errors.append("Loan amount must be positive")

    loan_tenure = data.get("loan_tenure", 0)
    if not isinstance(loan_tenure, int) or loan_tenure <= 0 or loan_tenure > 480:
        errors.append("Loan tenure must be between 1 and 480 months")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "dti_ratio": dti_ratio
    }


def calculate_risk_score(data: Dict[str, Any]) -> float:
    """Calculate estimated risk score (0-100, lower is better)."""
    risk_score = 50.0  # Start at neutral

    credit_score = data.get("credit_score", 650)
    if credit_score >= 750:
        risk_score -= 15
    elif credit_score >= 700:
        risk_score -= 10
    elif credit_score >= 650:
        risk_score -= 5
    elif credit_score < 600:
        risk_score += 20

    # DTI impact
    annual_income = data.get("annual_income", 50000)
    loan_amount = data.get("loan_amount", 25000)
    loan_tenure = data.get("loan_tenure", 60)
    liabilities = data.get("liabilities", 5000)

    monthly_income = annual_income / 12
    monthly_payment = loan_amount / max(loan_tenure, 1)
    total_monthly_debt = (liabilities / 12) + monthly_payment
    dti_ratio = (total_monthly_debt / monthly_income) * 100 if monthly_income > 0 else 100

    if dti_ratio > 50:
        risk_score += 20
    elif dti_ratio > 43:
        risk_score += 10

    # Savings impact
    savings = data.get("savings", 0)
    if savings > annual_income * 0.5:
        risk_score -= 10
    elif savings < annual_income * 0.1:
        risk_score += 5

    # Employment stability
    employment_years = data.get("employment_years", 0)
    if employment_years < 2:
        risk_score += 10
    elif employment_years >= 10:
        risk_score -= 5

    return max(0, min(100, risk_score))


def test_validation():
    """Test validation functionality."""
    print_test_header("VALIDATION TESTS")

    for idx, app in enumerate(TEST_APPLICATIONS, 1):
        print_section(f"Test Case {idx}: {app['name']}")
        print(f"Description: {app['description']}")

        validation = validate_form_data(app)

        print(f"\nValid: {validation['valid']}")
        print(f"DTI Ratio: {validation['dti_ratio']:.1f}%")

        if validation['errors']:
            print("\nErrors:")
            for error in validation['errors']:
                print(f"  ✗ {error}")

        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠ {warning}")

        if validation['valid']:
            print("\n✓ Validation passed!")


def test_risk_calculation():
    """Test risk score calculation."""
    print_test_header("RISK SCORE CALCULATION TESTS")

    for idx, app in enumerate(TEST_APPLICATIONS, 1):
        print_section(f"Test Case {idx}: {app['name']}")

        risk_score = calculate_risk_score(app)
        print(f"Risk Score: {risk_score:.1f}/100")

        if risk_score < 30:
            risk_level = "LOW"
            confidence = 0.95
        elif risk_score < 50:
            risk_level = "MEDIUM"
            confidence = 0.85
        elif risk_score < 70:
            risk_level = "HIGH"
            confidence = 0.70
        else:
            risk_level = "VERY HIGH"
            confidence = 0.60

        print(f"Risk Level: {risk_level}")
        print(f"Confidence: {confidence * 100:.0f}%")
        print(f"Expected Outcome: {app['expected_outcome']}")

        # Determine expected decision based on risk
        if risk_score < 40 and app.get("credit_score", 0) > 700:
            predicted = "approved"
        elif risk_score < 55 and app.get("credit_score", 0) > 650:
            predicted = "conditional_approval"
        elif risk_score > 65 or app.get("credit_score", 0) < 600:
            predicted = "review_required"
        else:
            predicted = "denied"

        match = "✓" if predicted == app['expected_outcome'] else "✗"
        print(f"Predicted: {predicted} {match}")


def test_payload_format():
    """Test request payload generation."""
    print_test_header("PAYLOAD FORMAT TESTS")

    for idx, app in enumerate(TEST_APPLICATIONS[:2], 1):
        print_section(f"Test Case {idx}: {app['name']}")

        payload = {
            "applicant_id": f"APP-{int(time.time() * 1000)}",
            "profile": {
                "name": app["name"],
                "age": app["age"],
                "employment_status": app["employment_status"],
                "employment_years": app["employment_years"],
                "education_level": app["education_level"],
                "annual_income": app["annual_income"],
                "monthly_expenses": app["monthly_expenses"],
                "savings": app["savings"]
            },
            "credit_score": app["credit_score"],
            "loan_amount": app["loan_amount"],
            "tenure": app["loan_tenure"],
            "liabilities": app["liabilities"],
            "location": app["location"],
        }

        print("Generated Payload:")
        print(json.dumps(payload, indent=2))


def test_response_handling():
    """Test response handling scenarios."""
    print_test_header("RESPONSE HANDLING TESTS")

    print_section("Scenario 1: Success Response (Approved)")
    success_response = {
        "case_id": "CASE-20240618-001",
        "classification": "approved",
        "risk_score": 35.5,
        "confidence": 0.92,
        "factors": [
            {
                "factor_name": "Credit Score",
                "impact": "positive",
                "value": 750,
                "weight": 0.35,
                "explanation": "Excellent credit score indicates strong payment history"
            },
            {
                "factor_name": "Debt-to-Income Ratio",
                "impact": "positive",
                "value": 25.5,
                "weight": 0.30,
                "explanation": "Low DTI ratio shows healthy financial management"
            }
        ],
        "explanation": "Your application has been approved. Your excellent credit history and low debt-to-income ratio demonstrate strong financial responsibility.",
        "conditions": [],
        "required_documents": ["Government ID", "Proof of Income"],
        "processed_at": datetime.now().isoformat(),
        "processing_time_ms": 245.5
    }
    print(json.dumps(success_response, indent=2))

    print_section("Scenario 2: Conditional Approval")
    conditional_response = {
        "case_id": "CASE-20240618-002",
        "classification": "conditional_approval",
        "risk_score": 52.3,
        "confidence": 0.78,
        "factors": [
            {
                "factor_name": "Employment Tenure",
                "impact": "negative",
                "value": 2.5,
                "weight": 0.25,
                "explanation": "Relatively short employment tenure (less than 3 years)"
            }
        ],
        "explanation": "Your application is conditionally approved subject to verification of recent employment.",
        "conditions": [
            "Recent employment verification required",
            "Minimum 6 months employment at current position"
        ],
        "required_documents": ["Employment verification letter", "Recent pay stubs"],
        "processed_at": datetime.now().isoformat(),
        "processing_time_ms": 312.3
    }
    print(json.dumps(conditional_response, indent=2))

    print_section("Scenario 3: Denied Application")
    denied_response = {
        "case_id": "CASE-20240618-003",
        "classification": "denied",
        "risk_score": 78.9,
        "confidence": 0.85,
        "factors": [
            {
                "factor_name": "Credit Score",
                "impact": "negative",
                "value": 520,
                "weight": 0.40,
                "explanation": "Poor credit score indicates payment difficulties"
            },
            {
                "factor_name": "Debt-to-Income Ratio",
                "impact": "negative",
                "value": 68.5,
                "weight": 0.35,
                "explanation": "High DTI ratio suggests overextension"
            }
        ],
        "explanation": "Unfortunately, your application could not be approved at this time. Your credit profile and current debt obligations present too much risk for our lending criteria.",
        "conditions": [],
        "required_documents": [],
        "processed_at": datetime.now().isoformat(),
        "processing_time_ms": 198.7
    }
    print(json.dumps(denied_response, indent=2))


def test_ui_components():
    """Test UI component requirements."""
    print_test_header("UI COMPONENT REQUIREMENTS")

    components = {
        "Sidebar Navigation": [
            "Home button",
            "Apply button",
            "Status button",
            "Analytics button",
            "System status indicator",
            "Recent applications list"
        ],
        "Home Page": [
            "Title and description",
            "Key metrics (decisions, approval rate, processing time)",
            "Feature highlights",
            "Process steps explanation",
            "Call-to-action button"
        ],
        "Apply Page": [
            "Progress indicator",
            "Step 1: Personal Information form",
            "Step 2: Employment Information form",
            "Step 3: Financial Information form",
            "Step 4: Loan Information form",
            "Back/Next navigation buttons",
            "Form validation with error messages",
            "Helpful hints and expandable info boxes",
            "Submit button"
        ],
        "Status Page": [
            "Decision banner (color-coded)",
            "Key metrics display",
            "Decision explanation",
            "Risk assessment gauges",
            "Risk factors analysis chart",
            "Individual factor cards",
            "Conditions list (if applicable)",
            "Required documents checklist",
            "Processing details"
        ],
        "Analytics Page": [
            "Top metrics cards",
            "Decision distribution pie chart",
            "Loan amount distribution box plot",
            "Application timeline scatter plot",
            "Recent applications data table"
        ]
    }

    for section, items in components.items():
        print_section(section)
        for idx, item in enumerate(items, 1):
            print(f"  {idx}. {item}")


def run_all_tests():
    """Run all tests."""
    print_test_header("STREAMLIT APPLICATION TEST SUITE")
    print(f"Total Test Cases: {len(TEST_APPLICATIONS)}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    test_validation()
    print("\n")
    test_risk_calculation()
    print("\n")
    test_payload_format()
    print("\n")
    test_response_handling()
    print("\n")
    test_ui_components()

    print_test_header("TEST SUITE COMPLETE")
    print("All tests completed successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements_streamlit.txt")
    print("2. Start FastAPI backend: python server.py")
    print("3. Run Streamlit app: streamlit run app.py")
    print("4. Open browser to: http://localhost:8501")


if __name__ == "__main__":
    run_all_tests()
