# Loan Application API Guide

## Overview

The Loan Application API is a FastAPI-based REST service that processes loan applications using a LangGraph-based orchestrator. It provides:

- **Multi-agent loan decision processing** with profile, financial, risk, and compliance analysis
- **Comprehensive validation** of applicant and financial data
- **Structured error handling** with detailed error responses
- **Detailed decision explanations** with risk factors and recommendations
- **Async/sync client libraries** for easy integration
- **Comprehensive logging** for audit and debugging
- **Production-ready** with health checks and metrics

## Architecture

```
Client Request
      ↓
FastAPI Endpoint (/submit-application)
      ↓
Input Validation (Pydantic)
      ↓
LangGraph Orchestrator
      ├─ ApplicantProfileAgent (profiles analysis)
      ├─ FinancialRiskAgent (financial assessment)
      ├─ LoanDecisionAgent (decision making)
      └─ ComplianceOrchestratorAgent (compliance checks)
      ↓
Response Formatting
      ↓
LoanDecisionResponse (JSON)
```

## Installation

### Prerequisites

- Python 3.8+
- FastAPI
- Pydantic
- LangGraph
- Anthropic SDK (for LLM integration)

### Setup

```bash
# Install dependencies
pip install fastapi uvicorn pydantic httpx

# Navigate to API directory
cd /home/ubuntu/Desktop/demo/api

# Start the API server
python -m uvicorn loan_application_api:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check API server health and readiness.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-18T10:30:45.123456",
  "orchestrator_ready": true,
  "version": "1.0.0"
}
```

### 2. Submit Application

**Endpoint:** `POST /submit-application`

**Description:** Submit a loan application for processing.

#### Request Body

```json
{
  "applicant_id": "APP-001",
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
  "timestamp": "2024-06-18T10:30:45.123456"
}
```

#### Request Field Definitions

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `applicant_id` | string | Unique applicant identifier | 1-255 chars, alphanumeric + `_-` |
| `profile` | object | Applicant profile data | See profile fields below |
| `credit_score` | integer | Applicant credit score | 300-850 |
| `loan_amount` | float | Requested loan amount | > 0 |
| `tenure` | integer | Loan duration in months | 1-480 |
| `liabilities` | float | Total existing liabilities | ≥ 0 |
| `location` | string | Applicant location | 1+ chars, non-empty |
| `timestamp` | string | ISO 8601 timestamp | ISO format |

#### Profile Object Fields

| Field | Type | Description | Valid Values |
|-------|------|-------------|--------------|
| `name` | string | Applicant name | Any non-empty string |
| `age` | integer | Age in years | 18-120 |
| `employment_status` | string | Current employment status | `full_time`, `part_time`, `self_employed`, `unemployed` |
| `employment_years` | float | Years of employment | ≥ 0 |
| `education_level` | string | Education level | `high_school`, `bachelor`, `graduate` |
| `annual_income` | float | Annual income | > 0 |
| `monthly_expenses` | float | Monthly expenses | ≥ 0 |
| `savings` | float | Total savings | ≥ 0 |
| `existing_loans` | integer | Number of existing loans | ≥ 0 |

#### Response Body

```json
{
  "case_id": "CASE-20240618-ABC123D",
  "classification": "approved",
  "risk_score": 35.5,
  "confidence": 0.92,
  "factors": [
    {
      "factor_name": "Credit Score",
      "impact": "positive",
      "value": 750.0,
      "weight": 0.35,
      "explanation": "Excellent credit score indicates strong payment history"
    },
    {
      "factor_name": "Employment Status",
      "impact": "positive",
      "value": 1.0,
      "weight": 0.20,
      "explanation": "Stable full-time employment"
    },
    {
      "factor_name": "Debt-to-Income Ratio",
      "impact": "neutral",
      "value": 0.40,
      "weight": 0.15,
      "explanation": "Moderate debt-to-income ratio within acceptable range"
    }
  ],
  "explanation": "Your loan application has been APPROVED. You meet the lending criteria...",
  "conditions": [],
  "required_documents": ["Photo ID", "Proof of Income"],
  "processed_at": "2024-06-18T10:30:45.123456",
  "processing_time_ms": 1234.5
}
```

#### Response Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `case_id` | string | Unique case identifier for tracking (format: `CASE-YYYYMMDD-XXXXXXXX`) |
| `classification` | string | Decision classification: `approved`, `rejected`, `manual_review`, `conditional_approval` |
| `risk_score` | float | Overall risk score (0-100) |
| `confidence` | float | Decision confidence (0-1) |
| `factors` | array | List of DecisionFactor objects |
| `explanation` | string | Comprehensive decision rationale |
| `conditions` | array | Conditions for approval (if applicable) |
| `required_documents` | array | Required documents for processing |
| `processed_at` | string | ISO 8601 timestamp of processing |
| `processing_time_ms` | float | Processing duration in milliseconds |

#### Decision Factor Object

| Field | Type | Description |
|-------|------|-------------|
| `factor_name` | string | Name of the factor |
| `impact` | string | Impact level: `positive`, `neutral`, `negative` |
| `value` | float | Numeric value of the factor |
| `weight` | float | Weight in final decision (0-1) |
| `explanation` | string | Detailed explanation |

#### Response Status Codes

| Code | Description |
|------|-------------|
| 200 | Application processed successfully |
| 400 | Bad request (invalid input) |
| 422 | Validation error (unprocessable entity) |
| 500 | Server error during processing |
| 503 | Orchestrator not initialized |

#### Error Response

```json
{
  "error_code": "VALIDATION_ERROR",
  "error_message": "Input validation failed",
  "details": {
    "validation_errors": [
      {
        "field": "credit_score",
        "type": "less_than",
        "message": "ensure this value is greater than or equal to 300"
      }
    ]
  },
  "case_id": null,
  "timestamp": "2024-06-18T10:30:45.123456"
}
```

## Client Libraries

### Python Async Client

```python
import asyncio
from api.loan_api_client import LoanApplicationClient

async def main():
    async with LoanApplicationClient(base_url="http://localhost:8000") as client:
        # Check health
        health = await client.health_check()
        print(f"API Status: {health['status']}")

        # Submit application
        decision = await client.submit_application(
            applicant_id="APP-001",
            profile={
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
            credit_score=720,
            loan_amount=25000,
            tenure=60,
            liabilities=10000,
            location="New York, NY"
        )

        print(f"Case ID: {decision.case_id}")
        print(f"Decision: {decision.classification}")
        print(f"Risk Score: {decision.risk_score}")
        print(f"Confidence: {decision.confidence}")

asyncio.run(main())
```

### Python Sync Client

```python
from api.loan_api_client import submit_loan_application_sync

# Submit application synchronously
decision = submit_loan_application_sync(
    applicant_id="APP-001",
    profile={
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
    credit_score=720,
    loan_amount=25000,
    tenure=60,
    liabilities=10000,
    location="New York, NY"
)

print(f"Decision: {decision.classification}")
print(f"Risk Score: {decision.risk_score}")
```

### Batch Processing

```python
import asyncio
from api.loan_api_client import LoanApplicationClient

async def batch_process():
    async with LoanApplicationClient() as client:
        applications = [
            {
                "applicant_id": "APP-001",
                "profile": {...},
                "credit_score": 720,
                ...
            },
            {
                "applicant_id": "APP-002",
                "profile": {...},
                "credit_score": 680,
                ...
            }
        ]

        results = await client.submit_batch_applications(applications)
        print(f"Processed: {results['processed']}")
        print(f"Errors: {results['errors']}")

asyncio.run(batch_process())
```

## Validation Rules

### Credit Score Validation
- **Range:** 300-850
- **Type:** Integer
- **Impact:** Lower scores increase risk

### Loan Amount Validation
- **Range:** > 0
- **Type:** Float
- **Impact:** Higher amounts increase risk

### Tenure Validation
- **Range:** 1-480 months
- **Type:** Integer
- **Impact:** Longer terms increase risk

### Age Validation
- **Range:** 18-120 years
- **Type:** Integer
- **Impact:** Optimal range is 30-50

### Employment Years Validation
- **Range:** ≥ 0
- **Type:** Float
- **Impact:** More experience decreases risk

### Income Validation
- **Rule:** Annual income must be positive
- **Type:** Float
- **Impact:** Higher income decreases risk

### Employment Status Validation
- **Valid Values:** full_time, part_time, self_employed, unemployed
- **Impact:** Full-time employment is lowest risk

## Error Handling

### Common Errors

#### 1. Validation Error (422)
```json
{
  "error_code": "VALIDATION_ERROR",
  "error_message": "Input validation failed",
  "details": {
    "validation_errors": [
      {
        "field": "profile.age",
        "type": "less_than",
        "message": "ensure this value is greater than or equal to 18"
      }
    ]
  },
  "timestamp": "2024-06-18T10:30:45.123456"
}
```

#### 2. Orchestrator Not Ready (503)
```json
{
  "error_code": "SERVICE_UNAVAILABLE",
  "error_message": "Orchestrator not initialized",
  "case_id": null,
  "timestamp": "2024-06-18T10:30:45.123456"
}
```

#### 3. Server Error (500)
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "error_message": "An unexpected error occurred during processing",
  "case_id": "CASE-20240618-ABC123D",
  "timestamp": "2024-06-18T10:30:45.123456"
}
```

### Error Handling Best Practices

1. **Always check status code** before processing response
2. **Log error_code** for tracking and debugging
3. **Use case_id** for support and tracking
4. **Retry on 503** (service unavailable)
5. **Don't retry on 422** (validation error - fix input)
6. **Implement exponential backoff** for retries

## Logging

The API includes comprehensive logging:

```
2024-06-18 10:30:45,123 - loan_application_api - INFO - [REQ-001] POST /submit-application
2024-06-18 10:30:45,125 - loan_application_api - INFO - [CASE-20240618-ABC123D] Processing application for applicant: APP-001
2024-06-18 10:30:45,126 - loan_application_api - DEBUG - [CASE-20240618-ABC123D] Built applicant profile: APP-001
2024-06-18 10:30:46,234 - loan_application_api - INFO - [CASE-20240618-ABC123D] Invoking LangGraph orchestrator...
2024-06-18 10:30:47,456 - loan_application_api - INFO - [CASE-20240618-ABC123D] Orchestrator execution completed
2024-06-18 10:30:47,457 - loan_application_api - INFO - [CASE-20240618-ABC123D] Application processed successfully - Decision: approved, Risk: 35.5, Time: 1234.5ms
2024-06-18 10:30:47,458 - loan_application_api - INFO - [REQ-001] Status: 200 - 1333.5ms
```

## Decision Factors

### Credit Score Factor
- **Impact:** 0.25 weight
- **Positive:** 750+
- **Neutral:** 650-749
- **Negative:** 600-649 or below

### Employment Status Factor
- **Impact:** 0.20 weight
- **Positive:** Full-time
- **Neutral:** Self-employed, Part-time
- **Negative:** Unemployed

### Debt-to-Income Factor
- **Impact:** 0.15 weight
- **Positive:** ≤ 0.30
- **Neutral:** 0.30-0.50
- **Negative:** > 0.50

### Employment Duration Factor
- **Impact:** Varies
- **Positive:** 5+ years
- **Neutral:** 2-5 years
- **Negative:** < 2 years

## Example Workflows

### Workflow 1: Simple Approval Flow
```
1. Client submits application
2. API validates input
3. Orchestrator analyzes profile
4. Orchestrator assesses financial risk
5. Orchestrator makes decision
6. Orchestrator checks compliance
7. API formats response
8. Client receives decision
```

### Workflow 2: Batch Processing Flow
```
1. Client submits batch of 10 applications
2. API validates each application
3. For each application:
   - Invoke orchestrator
   - Collect decision
4. Return batch results
5. Log processing metrics
```

### Workflow 3: Integration Flow
```
1. External system calls API
2. API processes request
3. API returns case_id immediately
4. External system stores case_id
5. External system queries for updates using case_id
6. External system tracks decision
```

## Performance Considerations

### Processing Time
- **Average:** 1-2 seconds per application
- **Factors affecting time:** Profile complexity, orchestrator agents, LLM calls

### Concurrency
- API supports concurrent requests
- Each request gets unique case_id
- Orchestrator handles concurrent processing

### Scalability
- Deploy multiple API instances behind load balancer
- Share central orchestrator or deploy per-instance
- Use async/await for I/O efficiency

## Security Considerations

1. **Input Validation:** All inputs validated by Pydantic
2. **Error Handling:** Sensitive errors logged but not exposed to client
3. **Case ID:** Unique per request for audit trail
4. **Timestamp Logging:** All operations timestamped
5. **Rate Limiting:** Consider implementing based on use case

## Development

### Running Tests

```bash
cd /home/ubuntu/Desktop/demo/api
pytest test_loan_api.py -v
```

### Testing Endpoint

A test endpoint is available for development:

```bash
POST /test-application
```

Returns a sample decision without requiring a database.

### Interactive Documentation

Access Swagger UI and ReDoc:

```
Swagger UI: http://localhost:8000/api/docs
ReDoc: http://localhost:8000/api/redoc
OpenAPI Schema: http://localhost:8000/api/openapi.json
```

## Troubleshooting

### Issue: Orchestrator Not Initialized
**Solution:** Check startup logs, ensure all dependencies installed

### Issue: Validation Error
**Solution:** Review error_message field, check field constraints

### Issue: Timeout
**Solution:** Increase timeout parameter, check LLM availability

### Issue: Inconsistent Decisions
**Solution:** Check seed values in orchestrator, review risk factors

## API Evolution

The API follows semantic versioning:
- **Major:** Breaking changes
- **Minor:** New features (backward compatible)
- **Patch:** Bug fixes

Current version: **1.0.0**

## Support

For issues or questions:
1. Check logs for detailed error information
2. Review this guide for common issues
3. Check case_id in responses for tracking
4. Review implementation code for customization needs
