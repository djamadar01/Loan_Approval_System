"""
Unit tests for FastAPI Main Application

Tests for:
- Pydantic model validation
- API endpoints
- Error handling
- CORS configuration
- Startup/shutdown events
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from main import app, app_state, LoanApplicationRequest, PersonalInfo, EmploymentInfo, FinancialInfo, LoanDetails

# Create test client
client = TestClient(app)


# ============================================================================
# FIXTURE SETUP
# ============================================================================

@pytest.fixture
def valid_application():
    """Create a valid loan application."""
    return {
        "personal_info": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+14155552671",
            "date_of_birth": "1990-05-15"
        },
        "employment_info": {
            "employer_name": "Tech Corp",
            "job_title": "Engineer",
            "employment_status": "employed",
            "years_employed": 5.0,
            "monthly_income": 8000
        },
        "financial_info": {
            "annual_income": 96000,
            "monthly_expenses": 3000,
            "credit_score": 750,
            "existing_loans_count": 1,
            "savings_amount": 50000
        },
        "loan_details": {
            "loan_amount": 250000,
            "loan_term_months": 360,
            "loan_purpose": "home",
            "collateral_type": "property",
            "collateral_value": 300000
        },
        "additional_notes": "Good applicant"
    }


@pytest.fixture
def high_dti_application():
    """Create application with high debt-to-income ratio."""
    return {
        "personal_info": {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "+14155552672",
            "date_of_birth": "1995-08-20"
        },
        "employment_info": {
            "employer_name": "Retail Store",
            "job_title": "Sales",
            "employment_status": "employed",
            "years_employed": 2.0,
            "monthly_income": 3000
        },
        "financial_info": {
            "annual_income": 36000,
            "monthly_expenses": 2500,
            "credit_score": 650,
            "existing_loans_count": 3,
            "savings_amount": 5000
        },
        "loan_details": {
            "loan_amount": 50000,
            "loan_term_months": 60,
            "loan_purpose": "auto",
            "collateral_type": "vehicle",
            "collateral_value": 55000
        }
    }


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_health_check_endpoint():
    """Test health check endpoint returns proper response."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "version" in data
    assert "orchestrator_ready" in data
    assert "database_connected" in data


def test_health_check_response_format():
    """Test health check response format."""
    response = client.get("/health")
    data = response.json()

    # Check timestamp is ISO format
    assert datetime.fromisoformat(data["timestamp"])

    # Check version format
    assert isinstance(data["version"], str)
    assert data["version"] == "1.0.0"

    # Check boolean fields
    assert isinstance(data["orchestrator_ready"], bool)
    assert isinstance(data["database_connected"], bool)


# ============================================================================
# LOAN APPLICATION SUBMISSION TESTS
# ============================================================================

def test_submit_valid_application(valid_application):
    """Test submitting a valid loan application."""
    response = client.post("/api/v1/applications", json=valid_application)

    assert response.status_code == 202
    data = response.json()
    assert "application_id" in data
    assert data["status"] == "received"
    assert "submission_timestamp" in data
    assert data["estimated_processing_time_hours"] == 24
    assert "APP-" in data["application_id"]


def test_submit_application_with_high_dti(high_dti_application):
    """Test submitting application with high debt-to-income ratio."""
    response = client.post("/api/v1/applications", json=high_dti_application)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_submit_application_missing_fields(valid_application):
    """Test submitting application with missing required fields."""
    del valid_application["personal_info"]["first_name"]

    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_submit_application_invalid_email(valid_application):
    """Test submitting application with invalid email."""
    valid_application["personal_info"]["email"] = "invalid-email"

    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_submit_application_invalid_phone(valid_application):
    """Test submitting application with invalid phone number."""
    valid_application["personal_info"]["phone"] = "123"

    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_submit_application_invalid_date_format(valid_application):
    """Test submitting application with invalid date format."""
    valid_application["personal_info"]["date_of_birth"] = "15-05-1990"

    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_submit_application_invalid_credit_score(valid_application):
    """Test submitting application with invalid credit score."""
    # Too high
    valid_application["financial_info"]["credit_score"] = 900
    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422

    # Too low
    valid_application["financial_info"]["credit_score"] = 200
    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_submit_application_invalid_loan_amount(valid_application):
    """Test submitting application with invalid loan amount."""
    valid_application["loan_details"]["loan_amount"] = 0

    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_submit_application_invalid_employment_status(valid_application):
    """Test submitting application with invalid employment status."""
    valid_application["employment_info"]["employment_status"] = "unknown"

    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_submit_application_invalid_loan_purpose(valid_application):
    """Test submitting application with invalid loan purpose."""
    valid_application["loan_details"]["loan_purpose"] = "vacation"

    response = client.post("/api/v1/applications", json=valid_application)
    assert response.status_code == 422


def test_application_stored_in_state(valid_application):
    """Test that submitted application is stored in app state."""
    initial_count = len(app_state.applications_store)

    response = client.post("/api/v1/applications", json=valid_application)
    app_id = response.json()["application_id"]

    assert len(app_state.applications_store) == initial_count + 1
    assert app_id in app_state.applications_store


# ============================================================================
# APPLICATION STATUS TESTS
# ============================================================================

def test_get_application_status(valid_application):
    """Test retrieving application status."""
    # Submit application
    submit_response = client.post("/api/v1/applications", json=valid_application)
    app_id = submit_response.json()["application_id"]

    # Get status
    status_response = client.get(f"/api/v1/applications/{app_id}")

    assert status_response.status_code == 200
    data = status_response.json()
    assert data["application_id"] == app_id
    assert "status" in data
    assert "applicant_name" in data
    assert "loan_amount" in data
    assert "submission_date" in data


def test_get_application_status_not_found():
    """Test retrieving non-existent application."""
    response = client.get("/api/v1/applications/APP-99999999-999999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data or "error" in data


def test_get_application_status_returns_correct_data(valid_application):
    """Test that status response contains correct application data."""
    submit_response = client.post("/api/v1/applications", json=valid_application)
    app_id = submit_response.json()["application_id"]

    status_response = client.get(f"/api/v1/applications/{app_id}")
    data = status_response.json()

    assert data["applicant_name"] == f"{valid_application['personal_info']['first_name']} {valid_application['personal_info']['last_name']}"
    assert data["loan_amount"] == valid_application["loan_details"]["loan_amount"]


# ============================================================================
# DECISIONS ENDPOINT TESTS
# ============================================================================

def test_get_decisions_default_pagination():
    """Test getting decisions with default pagination."""
    response = client.get("/api/v1/decisions")

    assert response.status_code == 200
    data = response.json()
    assert "decisions" in data
    assert "total_count" in data
    assert "page" in data
    assert data["page"] == 1
    assert "page_size" in data
    assert "has_more" in data


def test_get_decisions_with_pagination():
    """Test getting decisions with custom pagination."""
    response = client.get("/api/v1/decisions?page=1&page_size=5")

    assert response.status_code == 200
    data = response.json()
    assert data["page_size"] == 5
    assert len(data["decisions"]) <= 5


def test_get_decisions_invalid_page_size():
    """Test getting decisions with invalid page size."""
    # Page size too large
    response = client.get("/api/v1/decisions?page_size=1000")
    assert response.status_code == 422

    # Page size zero
    response = client.get("/api/v1/decisions?page_size=0")
    assert response.status_code == 422


def test_get_decisions_with_filter():
    """Test getting decisions with decision filter."""
    response = client.get("/api/v1/decisions?decision_filter=approved")

    assert response.status_code == 200
    data = response.json()
    # All decisions should be approved
    for decision in data["decisions"]:
        assert decision["decision"] == "approved"


def test_get_decisions_invalid_filter():
    """Test getting decisions with invalid filter."""
    response = client.get("/api/v1/decisions?decision_filter=unknown")
    assert response.status_code == 422


def test_get_decisions_with_risk_score_range():
    """Test filtering decisions by risk score."""
    response = client.get("/api/v1/decisions?min_risk_score=30&max_risk_score=70")

    assert response.status_code == 200
    data = response.json()
    for decision in data["decisions"]:
        assert 30 <= decision["risk_score"] <= 70


def test_get_decisions_with_sorting():
    """Test sorting decisions."""
    # Sort by decision date descending
    response = client.get("/api/v1/decisions?sort_by=decision_date&sort_order=desc")
    assert response.status_code == 200

    # Sort by risk score ascending
    response = client.get("/api/v1/decisions?sort_by=risk_score&sort_order=asc")
    assert response.status_code == 200

    # Sort by loan amount descending
    response = client.get("/api/v1/decisions?sort_by=loan_amount&sort_order=desc")
    assert response.status_code == 200


def test_get_decisions_invalid_sort():
    """Test invalid sort parameters."""
    response = client.get("/api/v1/decisions?sort_by=invalid")
    assert response.status_code == 422


# ============================================================================
# CORS TESTS
# ============================================================================

def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options(
        "/api/v1/applications",
        headers={"Origin": "http://localhost:3000"}
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_allowed_origins():
    """Test CORS allows expected origins."""
    origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    for origin in origins:
        response = client.options(
            "/api/v1/applications",
            headers={"Origin": origin}
        )
        # Should not return 403 Forbidden
        assert response.status_code != 403


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_error_response_format():
    """Test error responses follow expected format."""
    response = client.get("/api/v1/applications/invalid-id")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data or "error" in data


def test_validation_error_response():
    """Test validation error response."""
    invalid_data = {
        "personal_info": {
            "first_name": "",  # Empty string not allowed
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+14155552671",
            "date_of_birth": "1990-05-15"
        }
    }

    response = client.post("/api/v1/applications", json=invalid_data)
    assert response.status_code == 422


# ============================================================================
# PYDANTIC MODEL TESTS
# ============================================================================

def test_personal_info_validation():
    """Test PersonalInfo Pydantic model validation."""
    # Valid
    personal_info = PersonalInfo(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+14155552671",
        date_of_birth="1990-05-15"
    )
    assert personal_info.first_name == "John"

    # Invalid email
    with pytest.raises(ValueError):
        PersonalInfo(
            first_name="John",
            last_name="Doe",
            email="invalid-email",
            phone="+14155552671",
            date_of_birth="1990-05-15"
        )

    # Invalid date format
    with pytest.raises(ValueError):
        PersonalInfo(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+14155552671",
            date_of_birth="15-05-1990"
        )


def test_employment_info_validation():
    """Test EmploymentInfo Pydantic model validation."""
    # Valid
    emp_info = EmploymentInfo(
        employer_name="Tech Corp",
        job_title="Engineer",
        employment_status="employed",
        years_employed=5.0,
        monthly_income=8000
    )
    assert emp_info.employment_status == "employed"

    # Invalid status
    with pytest.raises(ValueError):
        EmploymentInfo(
            employer_name="Tech Corp",
            job_title="Engineer",
            employment_status="invalid",
            years_employed=5.0,
            monthly_income=8000
        )


def test_financial_info_validation():
    """Test FinancialInfo Pydantic model validation."""
    # Valid
    fin_info = FinancialInfo(
        annual_income=96000,
        monthly_expenses=3000,
        credit_score=750,
        existing_loans_count=1,
        savings_amount=50000
    )
    assert fin_info.credit_score == 750

    # Invalid credit score (too high)
    with pytest.raises(ValueError):
        FinancialInfo(
            annual_income=96000,
            monthly_expenses=3000,
            credit_score=900,
            existing_loans_count=1,
            savings_amount=50000
        )


def test_loan_details_validation():
    """Test LoanDetails Pydantic model validation."""
    # Valid
    loan_details = LoanDetails(
        loan_amount=250000,
        loan_term_months=360,
        loan_purpose="home",
        collateral_type="property",
        collateral_value=300000
    )
    assert loan_details.loan_purpose == "home"

    # Invalid purpose
    with pytest.raises(ValueError):
        LoanDetails(
            loan_amount=250000,
            loan_term_months=360,
            loan_purpose="vacation",
            collateral_type="property",
            collateral_value=300000
        )


# ============================================================================
# ROOT AND API INFO ENDPOINTS
# ============================================================================

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "documentation" in data


def test_api_info_endpoint():
    """Test API info endpoint."""
    response = client.get("/api/v1")

    assert response.status_code == 200
    data = response.json()
    assert "api_version" in data
    assert data["api_version"] == "v1"
    assert "endpoints" in data


# ============================================================================
# APPLICATION ID GENERATION TESTS
# ============================================================================

def test_application_id_uniqueness(valid_application):
    """Test that generated application IDs are unique."""
    id_set = set()

    for _ in range(5):
        response = client.post("/api/v1/applications", json=valid_application)
        app_id = response.json()["application_id"]
        assert app_id not in id_set
        id_set.add(app_id)


def test_application_id_format(valid_application):
    """Test that application ID follows expected format."""
    response = client.post("/api/v1/applications", json=valid_application)
    app_id = response.json()["application_id"]

    # Format: APP-YYYYMMDD-XXXXXX
    parts = app_id.split("-")
    assert len(parts) == 3
    assert parts[0] == "APP"
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 6  # 6 digit counter


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow(valid_application):
    """Test complete workflow: submit, check status, retrieve decisions."""
    # Submit application
    submit_response = client.post("/api/v1/applications", json=valid_application)
    assert submit_response.status_code == 202
    app_id = submit_response.json()["application_id"]

    # Check status
    status_response = client.get(f"/api/v1/applications/{app_id}")
    assert status_response.status_code == 200
    assert status_response.json()["application_id"] == app_id

    # Get decisions (should exist, even if empty initially)
    decisions_response = client.get("/api/v1/decisions")
    assert decisions_response.status_code == 200
    assert "decisions" in decisions_response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
