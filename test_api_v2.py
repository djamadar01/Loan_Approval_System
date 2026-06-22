"""
Comprehensive test suite for API v2 endpoints.

Tests all 5 advanced endpoints:
1. GET /api/v2/decisions/analytics
2. POST /api/v2/applications/batch
3. GET /api/v2/applications/{id}/explainability
4. POST /api/v2/applications/{id}/what-if
5. WebSocket /ws/live-updates
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import AsyncGenerator
from httpx import AsyncClient
import websockets

import sys
sys.path.insert(0, '/home/ubuntu/Desktop/demo')

from api_v2 import (
    app,
    ApplicationStore,
    ConnectionManager,
    BatchApplicationRequest,
    ApplicationData,
    WhatIfRequest,
    WhatIfScenario
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
def app_store():
    """Return application store instance."""
    from api_v2 import app_store
    return app_store


# ============================================================================
# TESTS: Endpoint 1 - Analytics
# ============================================================================

@pytest.mark.asyncio
async def test_analytics_last_24_hours(client):
    """Test analytics for last 24 hours."""
    response = await client.get(
        "/api/v2/decisions/analytics",
        params={"period": "last_24_hours"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["period"] == "last_24_hours"
    assert "metrics" in data
    assert "decision_distribution" in data
    assert "risk_distribution" in data
    assert "generated_at" in data

    metrics = data["metrics"]
    assert metrics["total_applications"] > 0
    assert metrics["approved_count"] >= 0
    assert metrics["rejected_count"] >= 0
    assert 0 <= metrics["approval_rate"] <= 1
    assert 0 <= metrics["average_risk_score"] <= 100


@pytest.mark.asyncio
async def test_analytics_last_7_days(client):
    """Test analytics for last 7 days with time series."""
    response = await client.get(
        "/api/v2/decisions/analytics",
        params={"period": "last_7_days"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["period"] == "last_7_days"
    assert data["time_series_data"] is not None
    assert "daily_approvals" in data["time_series_data"]


@pytest.mark.asyncio
async def test_analytics_all_time(client):
    """Test all-time analytics."""
    response = await client.get(
        "/api/v2/decisions/analytics",
        params={"period": "all_time"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["period"] == "all_time"
    assert "processing_time_percentiles" in data
    assert "p50" in data["processing_time_percentiles"]


@pytest.mark.asyncio
async def test_analytics_risk_distribution(client):
    """Test risk distribution in analytics."""
    response = await client.get("/api/v2/decisions/analytics")
    assert response.status_code == 200

    data = response.json()
    risk_dist = data["risk_distribution"]
    assert "low" in risk_dist
    assert "medium" in risk_dist
    assert "high" in risk_dist
    assert "very_high" in risk_dist


# ============================================================================
# TESTS: Endpoint 2 - Batch Processing
# ============================================================================

@pytest.mark.asyncio
async def test_batch_submit_single_application(client):
    """Test submitting a batch with single application."""
    batch_request = {
        "applications": [
            {
                "applicant_id": "APP-001",
                "profile": {
                    "name": "John Doe",
                    "age": 35,
                    "employment_status": "full_time",
                    "employment_years": 5,
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
                "location": "New York, NY"
            }
        ],
        "priority": "normal",
        "notify_on_completion": True
    }

    response = await client.post(
        "/api/v2/applications/batch",
        json=batch_request
    )
    assert response.status_code == 202

    data = response.json()
    assert "batch_id" in data
    assert data["total_applications"] == 1
    assert data["status"] == "queued"
    assert "created_at" in data
    assert "estimated_completion" in data


@pytest.mark.asyncio
async def test_batch_submit_multiple_applications(client):
    """Test submitting batch with multiple applications."""
    batch_request = {
        "applications": [
            {
                "applicant_id": f"APP-{i:03d}",
                "profile": {
                    "name": f"Applicant {i}",
                    "age": 30 + i,
                    "employment_status": "full_time",
                    "employment_years": 3 + i,
                    "education_level": "bachelor",
                    "annual_income": 60000 + (i * 5000),
                    "monthly_expenses": 2000 + (i * 100),
                    "savings": 10000 + (i * 2000),
                    "existing_loans": 1
                },
                "credit_score": 650 + (i * 10),
                "loan_amount": 20000 + (i * 5000),
                "tenure": 60,
                "liabilities": 8000 + (i * 1000),
                "location": "New York, NY"
            }
            for i in range(5)
        ],
        "priority": "high"
    }

    response = await client.post(
        "/api/v2/applications/batch",
        json=batch_request
    )
    assert response.status_code == 202

    data = response.json()
    assert data["total_applications"] == 5
    batch_id = data["batch_id"]

    # Wait a bit and check batch status
    await asyncio.sleep(0.5)
    status_response = await client.get(f"/api/v2/batches/{batch_id}/status")
    assert status_response.status_code == 200


@pytest.mark.asyncio
async def test_batch_submit_invalid_credit_score(client):
    """Test batch submission with invalid credit score."""
    batch_request = {
        "applications": [
            {
                "applicant_id": "APP-INVALID",
                "profile": {
                    "name": "Invalid",
                    "age": 35,
                    "employment_status": "full_time",
                    "employment_years": 5,
                    "education_level": "bachelor",
                    "annual_income": 75000,
                    "monthly_expenses": 2500,
                    "savings": 15000,
                    "existing_loans": 1
                },
                "credit_score": 900,  # Invalid: > 850
                "loan_amount": 25000,
                "tenure": 60,
                "liabilities": 10000,
                "location": "New York, NY"
            }
        ]
    }

    response = await client.post(
        "/api/v2/applications/batch",
        json=batch_request
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_batch_submit_empty_applications(client):
    """Test batch submission with empty applications list."""
    batch_request = {
        "applications": [],
        "priority": "normal"
    }

    response = await client.post(
        "/api/v2/applications/batch",
        json=batch_request
    )
    # Should validate and potentially fail or accept with empty
    assert response.status_code in [400, 422]


# ============================================================================
# TESTS: Endpoint 3 - Explainability
# ============================================================================

@pytest.mark.asyncio
async def test_explainability_basic(client):
    """Test getting explainability for an application."""
    response = await client.get(
        "/api/v2/applications/TEST-APP-001/explainability"
    )
    assert response.status_code == 200

    data = response.json()
    assert "case_id" in data
    assert "classification" in data
    assert "risk_score" in data
    assert "decision_breakdown" in data
    assert "key_factors" in data
    assert "factor_contributions" in data
    assert "regulatory_flags" in data
    assert "confidence_intervals" in data
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_explainability_with_alternatives(client):
    """Test explainability with alternative scenarios."""
    response = await client.get(
        "/api/v2/applications/TEST-APP-002/explainability",
        params={"include_alternatives": True}
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["alternative_paths"]) > 0

    for alt_path in data["alternative_paths"]:
        assert "scenario" in alt_path
        assert "predicted_classification" in alt_path
        assert "predicted_risk_score" in alt_path


@pytest.mark.asyncio
async def test_explainability_confidence_intervals(client):
    """Test confidence intervals in explainability."""
    response = await client.get(
        "/api/v2/applications/TEST-APP-003/explainability",
        params={"confidence_level": 0.95}
    )
    assert response.status_code == 200

    data = response.json()
    ci = data["confidence_intervals"]

    assert "risk_score_interval" in ci
    assert "lower_bound" in ci["risk_score_interval"]
    assert "upper_bound" in ci["risk_score_interval"]

    assert "approval_probability" in ci
    assert "point_estimate" in ci["approval_probability"]
    assert "interval" in ci["approval_probability"]


@pytest.mark.asyncio
async def test_explainability_key_factors(client):
    """Test key factors in explainability."""
    response = await client.get(
        "/api/v2/applications/TEST-APP-004/explainability"
    )
    assert response.status_code == 200

    data = response.json()
    factors = data["key_factors"]

    assert len(factors) > 0
    for factor in factors:
        assert "factor_name" in factor
        assert "impact" in factor
        assert "value" in factor
        assert "weight" in factor
        assert "explanation" in factor
        assert 0 <= factor["weight"] <= 1


# ============================================================================
# TESTS: Endpoint 4 - What-If Analysis
# ============================================================================

@pytest.mark.asyncio
async def test_what_if_single_scenario(client):
    """Test what-if analysis with single scenario."""
    what_if_request = {
        "scenarios": [
            {
                "scenario_name": "Lower Credit Score",
                "changes": {"credit_score": 650},
                "description": "Analysis if credit score was 650"
            }
        ],
        "base_application_id": "TEST-APP-005"
    }

    response = await client.post(
        "/api/v2/applications/TEST-APP-005/what-if",
        json=what_if_request
    )
    assert response.status_code == 200

    data = response.json()
    assert "original_decision" in data
    assert len(data["scenarios"]) == 1
    assert "comparison_matrix" in data
    assert "insights" in data

    scenario = data["scenarios"][0]
    assert scenario["scenario_name"] == "Lower Credit Score"
    assert "predicted_classification" in scenario
    assert "predicted_risk_score" in scenario


@pytest.mark.asyncio
async def test_what_if_multiple_scenarios(client):
    """Test what-if analysis with multiple scenarios."""
    what_if_request = {
        "scenarios": [
            {
                "scenario_name": "Higher Income",
                "changes": {"annual_income": 100000}
            },
            {
                "scenario_name": "Lower Debt",
                "changes": {"liabilities": 5000}
            },
            {
                "scenario_name": "Higher Savings",
                "changes": {"savings": 50000}
            }
        ],
        "base_application_id": "TEST-APP-006"
    }

    response = await client.post(
        "/api/v2/applications/TEST-APP-006/what-if",
        json=what_if_request
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["scenarios"]) == 3
    assert len(data["insights"]) > 0


@pytest.mark.asyncio
async def test_what_if_complex_changes(client):
    """Test what-if with simultaneous changes."""
    what_if_request = {
        "scenarios": [
            {
                "scenario_name": "Improved Financial Profile",
                "changes": {
                    "credit_score": 780,
                    "annual_income": 95000,
                    "liabilities": 8000,
                    "savings": 40000
                }
            }
        ],
        "base_application_id": "TEST-APP-007"
    }

    response = await client.post(
        "/api/v2/applications/TEST-APP-007/what-if",
        json=what_if_request
    )
    assert response.status_code == 200

    data = response.json()
    scenario = data["scenarios"][0]
    assert len(scenario["changes_applied"]) == 4


@pytest.mark.asyncio
async def test_what_if_too_many_scenarios(client):
    """Test what-if with too many scenarios."""
    what_if_request = {
        "scenarios": [
            {
                "scenario_name": f"Scenario {i}",
                "changes": {"credit_score": 650 + i}
            }
            for i in range(15)  # Too many
        ],
        "base_application_id": "TEST-APP-008"
    }

    response = await client.post(
        "/api/v2/applications/TEST-APP-008/what-if",
        json=what_if_request
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_what_if_no_scenarios(client):
    """Test what-if with no scenarios."""
    what_if_request = {
        "scenarios": [],
        "base_application_id": "TEST-APP-009"
    }

    response = await client.post(
        "/api/v2/applications/TEST-APP-009/what-if",
        json=what_if_request
    )
    assert response.status_code == 400


# ============================================================================
# TESTS: Endpoint 5 - WebSocket Live Updates
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection and welcome message."""
    uri = "ws://localhost:8001/ws/live-updates"
    try:
        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            data = json.loads(message)
            assert data["type"] == "status"
            assert "connected" in data["message"].lower()
    except (ConnectionRefusedError, asyncio.TimeoutError):
        pytest.skip("WebSocket server not running")


@pytest.mark.asyncio
async def test_websocket_subscribe():
    """Test WebSocket subscription."""
    uri = "ws://localhost:8001/ws/live-updates"
    try:
        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            await asyncio.wait_for(websocket.recv(), timeout=2.0)

            # Subscribe to topic
            await websocket.send(json.dumps({
                "action": "subscribe",
                "topic": "batch_processing"
            }))

            # Receive subscription confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            data = json.loads(message)
            assert data["type"] == "status"
            assert "subscribed" in data["message"].lower()
    except (ConnectionRefusedError, asyncio.TimeoutError):
        pytest.skip("WebSocket server not running")


@pytest.mark.asyncio
async def test_websocket_ping_pong():
    """Test WebSocket ping-pong."""
    uri = "ws://localhost:8001/ws/live-updates"
    try:
        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            await asyncio.wait_for(websocket.recv(), timeout=2.0)

            # Send ping
            await websocket.send(json.dumps({
                "action": "ping"
            }))

            # Receive pong
            message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            data = json.loads(message)
            assert data["type"] == "pong"
    except (ConnectionRefusedError, asyncio.TimeoutError):
        pytest.skip("WebSocket server not running")


# ============================================================================
# TESTS: Health & Info Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/api/v2/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert "timestamp" in data
    assert "websocket_enabled" in data


@pytest.mark.asyncio
async def test_api_info(client):
    """Test API info endpoint."""
    response = await client.get("/api/v2/info")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data
    assert "features" in data
    assert len(data["features"]) >= 5


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_batch_and_analytics(client):
    """Test end-to-end: submit batch then check analytics."""
    # Submit batch
    batch_request = {
        "applications": [
            {
                "applicant_id": f"E2E-APP-{i:03d}",
                "profile": {
                    "name": f"E2E Applicant {i}",
                    "age": 30 + i,
                    "employment_status": "full_time",
                    "employment_years": 5,
                    "education_level": "bachelor",
                    "annual_income": 75000,
                    "monthly_expenses": 2500,
                    "savings": 15000,
                    "existing_loans": 1
                },
                "credit_score": 700 + i,
                "loan_amount": 25000,
                "tenure": 60,
                "liabilities": 10000,
                "location": "New York, NY"
            }
            for i in range(3)
        ]
    }

    batch_response = await client.post(
        "/api/v2/applications/batch",
        json=batch_request
    )
    assert batch_response.status_code == 202

    # Get analytics
    await asyncio.sleep(0.5)
    analytics_response = await client.get("/api/v2/decisions/analytics")
    assert analytics_response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
