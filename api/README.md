# Loan Application API

A production-ready FastAPI-based REST service for processing loan applications using LangGraph orchestration with multi-agent analysis.

## Quick Start

### 1. Start the API Server

```bash
cd /home/ubuntu/Desktop/demo/api
python -m uvicorn loan_application_api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 2. Access Documentation

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **OpenAPI Schema:** http://localhost:8000/api/openapi.json

### 3. Submit Your First Application

#### Using cURL

```bash
curl -X POST "http://localhost:8000/submit-application" \
  -H "Content-Type: application/json" \
  -d '{
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
    "location": "New York, NY"
  }'
```

#### Using Python Client

```python
from api.loan_api_client import submit_loan_application_sync

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
print(f"Case ID: {decision.case_id}")
```

## Features

### Core Capabilities
- **Multi-Agent Processing:** Profile analysis, financial risk assessment, decision making, compliance checking
- **Comprehensive Validation:** Input validation with detailed error messages
- **Risk Assessment:** 0-100 risk scoring with confidence metrics
- **Decision Explanation:** Detailed factors and rationale for decisions
- **Audit Trail:** Unique case IDs and comprehensive logging

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check and orchestrator status |
| `/submit-application` | POST | Process loan application |
| `/test-application` | POST | Test endpoint with sample data |

### Response Features
- **Case ID:** Unique identifier for tracking: `CASE-YYYYMMDD-XXXXXXXX`
- **Classification:** approved, rejected, manual_review, conditional_approval
- **Risk Score:** 0-100 scale
- **Confidence:** 0-1 decision confidence metric
- **Decision Factors:** Detailed breakdown of decision drivers
- **Processing Metadata:** Timestamp and processing duration

## Installation

### Prerequisites
- Python 3.8+
- FastAPI
- Pydantic
- LangGraph
- Anthropic SDK

### Setup

```bash
# Clone repository (if applicable)
cd /home/ubuntu/Desktop/demo

# Install dependencies
pip install fastapi uvicorn pydantic httpx anthropic langgraph

# Verify installation
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
```

## Usage

### Request Format

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

### Response Format

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
    }
  ],
  "explanation": "Your loan application has been APPROVED...",
  "conditions": [],
  "required_documents": ["Photo ID", "Proof of Income"],
  "processed_at": "2024-06-18T10:30:45.123456",
  "processing_time_ms": 1234.5
}
```

## Validation Rules

### Credit Score
- **Range:** 300-850
- **Impact:** Primary risk factor

### Loan Amount
- **Range:** > 0
- **Impact:** Affects debt calculations

### Tenure (Months)
- **Range:** 1-480 months
- **Impact:** Repayment period risk

### Age
- **Range:** 18-120 years
- **Optimal:** 30-50 years

### Employment Status
- **Valid:** full_time, part_time, self_employed, unemployed
- **Optimal:** full_time

### Income & Expenses
- **Annual Income:** Must be > 0
- **Monthly Expenses:** Must be ≥ 0
- **Savings:** Must be ≥ 0

## Client Libraries

### Synchronous Client

```python
from api.loan_api_client import SyncLoanApplicationClient

client = SyncLoanApplicationClient()
decision = client.submit_application(
    applicant_id="APP-001",
    profile={...},
    credit_score=720,
    loan_amount=25000,
    tenure=60,
    liabilities=10000,
    location="New York, NY"
)
client.close()
```

### Asynchronous Client

```python
import asyncio
from api.loan_api_client import LoanApplicationClient

async def main():
    async with LoanApplicationClient() as client:
        decision = await client.submit_application(
            applicant_id="APP-001",
            profile={...},
            credit_score=720,
            loan_amount=25000,
            tenure=60,
            liabilities=10000,
            location="New York, NY"
        )

asyncio.run(main())
```

### Batch Processing

```python
results = await client.submit_batch_applications([
    {
        "applicant_id": "APP-001",
        "profile": {...},
        ...
    },
    {
        "applicant_id": "APP-002",
        "profile": {...},
        ...
    }
])
```

## Error Handling

### Validation Error (422)
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
  }
}
```

### Service Unavailable (503)
```json
{
  "error_code": "SERVICE_UNAVAILABLE",
  "error_message": "Orchestrator not initialized"
}
```

### Server Error (500)
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "error_message": "An unexpected error occurred during processing",
  "case_id": "CASE-20240618-ABC123D"
}
```

## Testing

### Run Test Suite

```bash
cd /home/ubuntu/Desktop/demo/api
pytest test_loan_api.py -v
```

### Run Examples

```bash
python example_client_usage.py
```

### Interactive Testing

Use Swagger UI for interactive testing:
http://localhost:8000/api/docs

## Decision Factors

The API evaluates decisions based on multiple factors:

1. **Credit Score (35% weight)**
   - 750+: Positive
   - 650-749: Neutral
   - Below 650: Negative

2. **Employment Status (20% weight)**
   - Full-time: Positive
   - Part-time/Self-employed: Neutral
   - Unemployed: Negative

3. **Debt-to-Income Ratio (15% weight)**
   - ≤ 0.30: Positive
   - 0.30-0.50: Neutral
   - > 0.50: Negative

4. **Employment Duration (10% weight)**
   - 5+ years: Positive
   - 2-5 years: Neutral
   - < 2 years: Negative

5. **Risk Assessment Factors (20% weight)**
   - Based on comprehensive financial analysis

## Logging

The API provides comprehensive logging:

- **INFO:** Application processing events
- **DEBUG:** Internal state and calculations
- **ERROR:** Processing failures and exceptions
- **WARNING:** Validation issues

Access logs via standard Python logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance

### Processing Time
- **Average:** 1-2 seconds per application
- **Factors:** Profile complexity, orchestrator agents, LLM calls

### Concurrency
- Supports concurrent request processing
- Each request gets unique case_id
- Async/await for I/O efficiency

## Architecture

```
Client Request
    ↓
FastAPI Endpoint
    ↓
Pydantic Validation
    ↓
LangGraph Orchestrator
  ├─ Applicant Profile Agent
  ├─ Financial Risk Agent
  ├─ Loan Decision Agent
  └─ Compliance Orchestrator
    ↓
Response Formatting
    ↓
LoanDecisionResponse (JSON)
```

## Files

- **`loan_application_api.py`** - Main FastAPI application
- **`loan_api_client.py`** - Client library (sync and async)
- **`test_loan_api.py`** - Comprehensive test suite
- **`example_client_usage.py`** - Usage examples
- **`LOAN_API_GUIDE.md`** - Comprehensive API documentation
- **`README.md`** - This file

## Documentation

See **`LOAN_API_GUIDE.md`** for:
- Detailed API reference
- Field definitions and constraints
- Error handling patterns
- Integration examples
- Performance considerations
- Security considerations
- Troubleshooting guide

## Status Codes

| Code | Meaning | Retry? |
|------|---------|--------|
| 200 | Success | No |
| 400 | Bad Request | No |
| 422 | Validation Error | No |
| 500 | Server Error | Yes |
| 503 | Service Unavailable | Yes |

## Deployment

### Docker (Example)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/
COPY loan_orchestrator.py .
COPY loan_decision_agent.py .
# ... copy other required files

CMD ["python", "-m", "uvicorn", "api.loan_application_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. Use production ASGI server (Gunicorn + Uvicorn)
2. Implement rate limiting
3. Add authentication/authorization
4. Enable HTTPS/TLS
5. Configure logging aggregation
6. Set up monitoring and alerts

## Support & Documentation

- **Quick Start Guide:** See above
- **Full API Guide:** `LOAN_API_GUIDE.md`
- **Example Usage:** `example_client_usage.py`
- **Tests:** `test_loan_api.py`
- **Interactive Docs:** http://localhost:8000/api/docs

## Contributing

When modifying the API:

1. Run existing tests to verify no regressions
2. Add tests for new features
3. Update documentation
4. Follow PEP 8 style guidelines
5. Include comprehensive error handling
6. Add logging for debugging

## License

[Specify license as needed]

## Version

**Current Version:** 1.0.0

- Major updates may require schema changes
- Minor updates are backward compatible
- Patch updates are bug fixes only
