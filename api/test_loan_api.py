"""
Test suite for the Loan Application API.

Tests cover:
- Request validation
- Response formatting
- Error handling
- End-to-end workflow
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi.testclient import TestClient
from pydantic import ValidationError

# Import the FastAPI app
from loan_application_api import (
    app,
    LoanApplicationRequest,
    LoanDecisionResponse,
    initialize_orchestrator
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def setup_app():
    """Setup the app with orchestrator."""
    await initialize_orchestrator()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_application_request() -> Dict[str, Any]:
    """Create a valid application request."""
    return {
        "applicant_id": "TEST-APP-001",
        "profile": {
            "name": "John Smith",
            "age": 35,
            "employment_status": "full_time",
            "employment_years": 8,
            "education_level": "bachelor",
            "annual_income": 75000,
            "monthly_expenses": 2500,
            "savings": 15000,
            "existing_loans": 1
        },
        "credit_score": 720,
        "loan_amount": 25000,
        "tenure": 60,
        "liabilities": 10000,
        "location": "New York, NY",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def excellent_application_request() -> Dict[str, Any]:
    """Create an excellent application request (likely approved)."""
    return {
        "applicant_id": "TEST-EXCELLENT-001",
        "profile": {
            "name": "Sarah Johnson",
            "age": 40,
            "employment_status": "full_time",
            "employment_years": 15,
            "education_level": "graduate",
            "annual_income": 120000,
            "monthly_expenses": 2000,
            "savings": 50000,
            "existing_loans": 0
        },
        "credit_score": 800,
        "loan_amount": 20000,
        "tenure": 60,
        "liabilities": 5000,
        "location": "San Francisco, CA",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def poor_application_request() -> Dict[str, Any]:
    """Create a poor application request (likely rejected)."""
    return {
        "applicant_id": "TEST-POOR-001",
        "profile": {
            "name": "Bob Wilson",
            "age": 28,
            "employment_status": "unemployed",
            "employment_years": 0,
            "education_level": "high_school",
            "annual_income": 0,
            "monthly_expenses": 3000,
            "savings": 500,
            "existing_loans": 5
        },
        "credit_score": 450,
        "loan_amount": 50000,
        "tenure": 84,
        "liabilities": 45000,
        "location": "Detroit, MI",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# TESTS: REQUEST VALIDATION
# ============================================================================

class TestRequestValidation:
    """Test request validation."""

    def test_valid_request_structure(self, valid_application_request):
        """Test that valid request passes validation."""
        request = LoanApplicationRequest(**valid_application_request)
        assert request.applicant_id == "TEST-APP-001"
        assert request.credit_score == 720
        assert request.loan_amount == 25000

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            LoanApplicationRequest(
                applicant_id="TEST-001",
                profile={},
                credit_score=720
            )

    def test_invalid_credit_score(self, valid_application_request):
        """Test credit score bounds validation."""
        valid_application_request["credit_score"] = 300  # Min valid
        request = LoanApplicationRequest(**valid_application_request)
        assert request.credit_score == 300

        valid_application_request["credit_score"] = 850  # Max valid
        request = LoanApplicationRequest(**valid_application_request)
        assert request.credit_score == 850

        with pytest.raises(ValidationError):
            valid_application_request["credit_score"] = 299
            LoanApplicationRequest(**valid_application_request)

        with pytest.raises(ValidationError):
            valid_application_request["credit_score"] = 851
            LoanApplicationRequest(**valid_application_request)

    def test_invalid_loan_amount(self, valid_application_request):
        """Test loan amount validation."""
        with pytest.raises(ValidationError):
            valid_application_request["loan_amount"] = 0
            LoanApplicationRequest(**valid_application_request)

        with pytest.raises(ValidationError):
            valid_application_request["loan_amount"] = -1000
            LoanApplicationRequest(**valid_application_request)

    def test_invalid_tenure(self, valid_application_request):
        """Test tenure validation."""
        with pytest.raises(ValidationError):
            valid_application_request["tenure"] = 0
            LoanApplicationRequest(**valid_application_request)

        with pytest.raises(ValidationError):
            valid_application_request["tenure"] = 481  # Max is 480
            LoanApplicationRequest(**valid_application_request)

    def test_profile_missing_required_fields(self, valid_application_request):
        """Test profile missing required fields."""
        valid_application_request["profile"].pop("annual_income")
        with pytest.raises(ValidationError):
            LoanApplicationRequest(**valid_application_request)

    def test_invalid_age(self, valid_application_request):
        """Test age validation in profile."""
        with pytest.raises(ValidationError):
            valid_application_request["profile"]["age"] = 17
            LoanApplicationRequest(**valid_application_request)

        with pytest.raises(ValidationError):
            valid_application_request["profile"]["age"] = 121
            LoanApplicationRequest(**valid_application_request)

    def test_invalid_employment_years(self, valid_application_request):
        """Test employment years validation."""
        with pytest.raises(ValidationError):
            valid_application_request["profile"]["employment_years"] = -1
            LoanApplicationRequest(**valid_application_request)

    def test_negative_income(self, valid_application_request):
        """Test income validation."""
        with pytest.raises(ValidationError):
            valid_application_request["profile"]["annual_income"] = -1000
            LoanApplicationRequest(**valid_application_request)

    def test_invalid_applicant_id(self, valid_application_request):
        """Test applicant ID format validation."""
        with pytest.raises(ValidationError):
            valid_application_request["applicant_id"] = ""
            LoanApplicationRequest(**valid_application_request)

    def test_invalid_timestamp_format(self, valid_application_request):
        """Test timestamp format validation."""
        with pytest.raises(ValidationError):
            valid_application_request["timestamp"] = "not-a-timestamp"
            LoanApplicationRequest(**valid_application_request)


# ============================================================================
# TESTS: ENDPOINTS
# ============================================================================

class TestEndpoints:
    """Test API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_submit_application_valid(
        self,
        client,
        valid_application_request,
        setup_app
    ):
        """Test submitting a valid application."""
        response = client.post(
            "/submit-application",
            json=valid_application_request
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "case_id" in data
        assert "classification" in data
        assert "risk_score" in data
        assert "confidence" in data
        assert "factors" in data
        assert "explanation" in data
        assert "processed_at" in data
        assert "processing_time_ms" in data

        # Verify case ID format
        assert data["case_id"].startswith("CASE-")

        # Verify classification is valid
        assert data["classification"] in [
            "approved",
            "rejected",
            "manual_review",
            "conditional_approval"
        ]

        # Verify scores are in valid ranges
        assert 0 <= data["risk_score"] <= 100
        assert 0 <= data["confidence"] <= 1

        # Verify factors exist
        assert len(data["factors"]) > 0
        for factor in data["factors"]:
            assert "factor_name" in factor
            assert "impact" in factor
            assert "value" in factor
            assert "weight" in factor
            assert "explanation" in factor

    @pytest.mark.asyncio
    async def test_submit_application_invalid(
        self,
        client,
        valid_application_request,
        setup_app
    ):
        """Test submitting invalid application."""
        valid_application_request["credit_score"] = 300  # Below valid range
        response = client.post(
            "/submit-application",
            json=valid_application_request
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_application_excellent_profile(
        self,
        client,
        excellent_application_request,
        setup_app
    ):
        """Test submitting excellent application."""
        response = client.post(
            "/submit-application",
            json=excellent_application_request
        )

        assert response.status_code == 200
        data = response.json()

        # Excellent profile should have lower risk score
        assert data["risk_score"] < 50
        assert data["confidence"] > 0.75

    @pytest.mark.asyncio
    async def test_submit_application_poor_profile(
        self,
        client,
        poor_application_request,
        setup_app
    ):
        """Test submitting poor application."""
        response = client.post(
            "/submit-application",
            json=poor_application_request
        )

        assert response.status_code == 200
        data = response.json()

        # Poor profile should have higher risk score
        assert data["risk_score"] > 50


# ============================================================================
# TESTS: RESPONSE VALIDATION
# ============================================================================

class TestResponseValidation:
    """Test response validation and format."""

    @pytest.mark.asyncio
    async def test_response_model_validation(
        self,
        client,
        valid_application_request,
        setup_app
    ):
        """Test response can be validated by pydantic model."""
        response = client.post(
            "/submit-application",
            json=valid_application_request
        )

        assert response.status_code == 200
        data = response.json()

        # This should not raise ValidationError
        decision = LoanDecisionResponse(**data)
        assert isinstance(decision, LoanDecisionResponse)

    @pytest.mark.asyncio
    async def test_response_has_all_required_fields(
        self,
        client,
        valid_application_request,
        setup_app
    ):
        """Test response has all required fields."""
        response = client.post(
            "/submit-application",
            json=valid_application_request
        )

        assert response.status_code == 200
        data = response.json()

        required_fields = {
            "case_id",
            "classification",
            "risk_score",
            "confidence",
            "factors",
            "explanation",
            "processed_at",
            "processing_time_ms"
        }

        assert required_fields.issubset(set(data.keys()))

    @pytest.mark.asyncio
    async def test_decision_factors_structure(
        self,
        client,
        valid_application_request,
        setup_app
    ):
        """Test decision factors have correct structure."""
        response = client.post(
            "/submit-application",
            json=valid_application_request
        )

        assert response.status_code == 200
        data = response.json()

        for factor in data["factors"]:
            assert "factor_name" in factor
            assert "impact" in factor
            assert factor["impact"] in ["positive", "neutral", "negative"]
            assert "value" in factor
            assert "weight" in factor
            assert 0 <= factor["weight"] <= 1
            assert "explanation" in factor


# ============================================================================
# TESTS: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling."""

    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        response = client.post(
            "/submit-application",
            content="invalid"
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_invalid_json(self, client, setup_app):
        """Test handling of invalid JSON."""
        response = client.post(
            "/submit-application",
            content="{invalid json}",
            headers={"content-type": "application/json"}
        )
        assert response.status_code in [400, 422]


# ============================================================================
# TESTS: INTEGRATION
# ============================================================================

class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_multiple_applications(
        self,
        client,
        valid_application_request,
        excellent_application_request,
        poor_application_request,
        setup_app
    ):
        """Test processing multiple applications."""
        test_cases = [
            valid_application_request,
            excellent_application_request,
            poor_application_request
        ]

        responses = []
        for test_case in test_cases:
            response = client.post(
                "/submit-application",
                json=test_case
            )
            assert response.status_code == 200
            responses.append(response.json())

        # Verify all have different case IDs
        case_ids = {r["case_id"] for r in responses}
        assert len(case_ids) == 3

        # Verify decision logic makes sense
        excellent = responses[1]
        poor = responses[2]

        # Excellent should have lower risk than poor
        assert excellent["risk_score"] < poor["risk_score"]


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
