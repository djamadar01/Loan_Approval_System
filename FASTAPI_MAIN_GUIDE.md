# FastAPI Main Application Guide

## Overview

The `main.py` file implements a comprehensive FastAPI application for the Loan Decision System with the following features:

### Core Features

1. **Health Monitoring Endpoint** (`/health`)
   - Real-time system status checking
   - Orchestrator readiness verification
   - Database connectivity status

2. **Loan Application Submission** (`POST /api/v1/applications`)
   - Complete request validation using Pydantic models
   - Multi-section validation (personal, employment, financial, loan details)
   - Debt-to-income ratio calculation and validation
   - Application ID generation

3. **Application Status Retrieval** (`GET /api/v1/applications/{app_id}`)
   - Current processing status
   - Applicant information
   - Submission and update timestamps

4. **Decision Management** (`GET /api/v1/decisions`)
   - Advanced filtering (by decision type, risk score range)
   - Pagination support
   - Sorting capabilities (by decision date, risk score, loan amount)
   - Total count and metadata

5. **Error Handling & Middleware**
   - Custom error handling middleware
   - Comprehensive exception handlers
   - Validation error responses
   - Request tracking support

6. **CORS Configuration**
   - Multiple origin support
   - Credential support
   - Configurable method and header allowances

7. **Startup Event**
   - LangGraph orchestrator initialization
   - Database connection setup
   - Graceful shutdown handling

## Installation

### Prerequisites
- Python 3.9+
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.104.0 | Web framework |
| uvicorn | >=0.24.0 | ASGI server |
| pydantic | >=2.0.0 | Data validation |
| langgraph | >=0.0.20 | Orchestrator |
| langchain | >=0.1.0 | LLM integration |
| python-dotenv | >=1.0.0 | Environment management |

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Frontend Configuration
FRONTEND_URL=http://localhost:3000

# Anthropic API
ANTHROPIC_API_KEY=your_api_key_here

# Database Configuration (if applicable)
DATABASE_URL=your_database_url
```

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-19T10:30:00.000000",
  "version": "1.0.0",
  "orchestrator_ready": true,
  "database_connected": true
}
```

**Status Codes:**
- `200 OK` - System is healthy

---

### 2. Submit Loan Application

**Endpoint:** `POST /api/v1/applications`

**Request Body:**
```json
{
  "personal_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "date_of_birth": "1990-01-15"
  },
  "employment_info": {
    "employer_name": "Tech Corp",
    "job_title": "Software Engineer",
    "employment_status": "employed",
    "years_employed": 5.5,
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
  "additional_notes": "No additional information"
}
```

**Response:**
```json
{
  "application_id": "APP-20240619-000001",
  "status": "received",
  "message": "Application APP-20240619-000001 has been received and queued for processing",
  "submission_timestamp": "2024-06-19T10:30:00.000000",
  "estimated_processing_time_hours": 24
}
```

**Status Codes:**
- `202 Accepted` - Application received and queued
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Validation Rules:**

| Field | Rules |
|-------|-------|
| first_name, last_name | 1-100 characters |
| email | Valid email format |
| phone | Valid phone number (9-15 digits) |
| date_of_birth | YYYY-MM-DD format |
| credit_score | 300-850 range |
| loan_amount | 0-1,000,000 range |
| loan_term_months | 6-360 months |
| debt_to_income_ratio | Maximum 50% |

---

### 3. Get Application Status

**Endpoint:** `GET /api/v1/applications/{app_id}`

**Path Parameters:**
- `app_id` (required): Application ID (e.g., "APP-20240619-000001")

**Response:**
```json
{
  "application_id": "APP-20240619-000001",
  "status": "pending",
  "applicant_name": "John Doe",
  "loan_amount": 250000,
  "submission_date": "2024-06-19T10:30:00.000000",
  "last_updated": "2024-06-19T10:35:00.000000",
  "current_stage": "queued",
  "notes": null
}
```

**Status Codes:**
- `200 OK` - Application found
- `404 Not Found` - Application not found
- `500 Internal Server Error` - Server error

---

### 4. Get Decisions with Filtering and Pagination

**Endpoint:** `GET /api/v1/decisions`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number (1-indexed) |
| page_size | integer | 10 | Results per page (1-100) |
| decision_filter | string | null | Filter: approved, rejected, conditional, manual_review, all |
| min_risk_score | float | null | Minimum risk score (0-100) |
| max_risk_score | float | null | Maximum risk score (0-100) |
| sort_by | string | decision_date | Sort field: decision_date, risk_score, loan_amount |
| sort_order | string | desc | Sort order: asc, desc |

**Example Request:**
```
GET /api/v1/decisions?page=1&page_size=20&decision_filter=approved&min_risk_score=30&max_risk_score=70&sort_by=risk_score&sort_order=asc
```

**Response:**
```json
{
  "decisions": [
    {
      "application_id": "APP-20240619-000001",
      "applicant_name": "John Doe",
      "loan_amount": 250000,
      "decision": "approved",
      "risk_score": 45.5,
      "decision_date": "2024-06-19T11:00:00.000000",
      "decision_reason": "Good credit history and stable employment",
      "approved_amount": 250000,
      "conditions": null
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

**Status Codes:**
- `200 OK` - Decisions retrieved successfully
- `500 Internal Server Error` - Server error

---

## Pydantic Models

### PersonalInfo
- `first_name` (string, 1-100 chars, required)
- `last_name` (string, 1-100 chars, required)
- `email` (EmailStr, required)
- `phone` (string, regex validated, required)
- `date_of_birth` (string, YYYY-MM-DD format, required)

### EmploymentInfo
- `employer_name` (string, 1-200 chars, required)
- `job_title` (string, 1-100 chars, required)
- `employment_status` (enum: employed, self-employed, unemployed, retired, required)
- `years_employed` (float, 0-70, required)
- `monthly_income` (float, > 0, required)

### FinancialInfo
- `annual_income` (float, > 0, required)
- `monthly_expenses` (float, >= 0, required)
- `credit_score` (integer, 300-850, required)
- `existing_loans_count` (integer, >= 0, required)
- `savings_amount` (float, >= 0, required)

### LoanDetails
- `loan_amount` (float, 0-1,000,000, required)
- `loan_term_months` (integer, 6-360, required)
- `loan_purpose` (enum: home, auto, personal, business, education, required)
- `collateral_type` (enum: property, vehicle, cash, none, optional)
- `collateral_value` (float, >= 0, default: 0)

### LoanApplicationRequest
- `personal_info` (PersonalInfo object, required)
- `employment_info` (EmploymentInfo object, required)
- `financial_info` (FinancialInfo object, required)
- `loan_details` (LoanDetails object, required)
- `additional_notes` (string, max 1000 chars, optional)

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "timestamp": "2024-06-19T10:30:00.000000",
  "request_id": "req-12345"
}
```

### Common Error Scenarios

| Status | Error | Cause |
|--------|-------|-------|
| 422 | Validation error | Invalid request body |
| 404 | Not Found | Application ID doesn't exist |
| 500 | Internal server error | Server processing error |

### Example Error Response

```json
{
  "error": "Validation error",
  "detail": "Debt-to-income ratio 52.50% exceeds maximum allowed (50%)",
  "timestamp": "2024-06-19T10:30:00.000000",
  "request_id": "req-abc123"
}
```

---

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) with the following settings:

**Allowed Origins:**
- http://localhost
- http://localhost:3000
- http://localhost:8000
- http://127.0.0.1
- http://127.0.0.1:3000
- http://127.0.0.1:8000
- Custom origin from `FRONTEND_URL` environment variable

**Allowed Methods:** All HTTP methods

**Allowed Headers:** All headers

**Exposed Headers:**
- X-Total-Count
- X-Page
- X-Page-Size

**Max Age:** 600 seconds

---

## Middleware & Startup Events

### Error Handling Middleware

Custom middleware that:
- Catches unhandled exceptions
- Logs errors with full traceback
- Returns consistent error responses
- Supports request tracking via X-Request-ID header

### Startup Events

The application initializes two critical components on startup:

1. **LangGraph Orchestrator**
   - Imports `create_orchestrator()` from `loan_orchestrator` module
   - Falls back to mock orchestrator if module unavailable
   - Tracks orchestrator readiness status

2. **Database Connection**
   - Initializes database connection pool
   - Sets `db_connected` flag
   - Logs connection status

### Shutdown Events

Clean shutdown process:
- Closes database connections
- Clears orchestrator reference
- Logs shutdown completion

---

## Running the Application

### Development Mode

```bash
# Set debug mode in .env
DEBUG=true

# Run with auto-reload
python main.py
```

### Production Mode

```bash
# Set debug mode in .env
DEBUG=false

# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

```bash
# Build image
docker build -t loan-decision-api .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  loan-decision-api
```

---

## Testing the API

### Using cURL

**Health Check:**
```bash
curl -X GET http://localhost:8000/health
```

**Submit Application:**
```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d @application.json
```

**Get Status:**
```bash
curl -X GET http://localhost:8000/api/v1/applications/APP-20240619-000001
```

**Get Decisions:**
```bash
curl -X GET "http://localhost:8000/api/v1/decisions?page=1&page_size=10&decision_filter=approved"
```

### Using Python Requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Submit application
payload = {...}  # See API documentation
response = requests.post(
    "http://localhost:8000/api/v1/applications",
    json=payload
)
app_id = response.json()["application_id"]

# Get status
response = requests.get(
    f"http://localhost:8000/api/v1/applications/{app_id}"
)
print(response.json())

# Get decisions
response = requests.get(
    "http://localhost:8000/api/v1/decisions",
    params={
        "page": 1,
        "page_size": 10,
        "decision_filter": "approved"
    }
)
print(response.json())
```

---

## Interactive API Documentation

Once the application is running, access the interactive API documentation at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide:
- Live endpoint exploration
- Interactive request/response examples
- Schema validation
- Try-it-out functionality

---

## Monitoring & Logging

### Log Levels

The application uses the following log levels:

- `INFO` - Normal operations (startup, requests)
- `WARNING` - Potential issues (orchestrator not available)
- `ERROR` - Error conditions (failed validations, server errors)

### Log Format

```
2024-06-19 10:30:00,000 - main - INFO - Processing loan application from John Doe
```

### Key Log Points

- Application startup/shutdown
- Orchestrator initialization
- Database connection
- Application submission
- Status retrieval
- Decision filtering
- Exception handling

---

## Performance Considerations

### Application State Storage

Currently uses in-memory storage for:
- Applications (keyed by application_id)
- Decisions (list-based)

**For Production:**
- Replace with persistent database (PostgreSQL, MongoDB)
- Implement caching layer (Redis)
- Add database connection pooling

### Pagination

Default page size: 10
Maximum page size: 100

Adjust in query parameters as needed for optimal performance.

### CORS Configuration

Max age for preflight requests: 600 seconds

Adjust based on your frontend needs.

---

## Integration with LangGraph Orchestrator

The application initializes the LangGraph orchestrator at startup. To integrate with your custom orchestrator:

1. **Create orchestrator module** (`loan_orchestrator.py`):
   ```python
   def create_orchestrator():
       # Initialize your orchestrator
       return orchestrator_instance
   ```

2. **Enable orchestrator processing** in `submit_loan_application`:
   ```python
   if app_state.orchestrator:
       await app_state.orchestrator.process_application(app_id)
   ```

3. **Implement status updates** in orchestrator to update application status

---

## Security Considerations

1. **Email Validation:** Pydantic validates email format
2. **Phone Validation:** Regex pattern ensures valid phone numbers
3. **CORS:** Restricts cross-origin requests
4. **Error Messages:** Don't expose sensitive internals
5. **Input Limits:** Max string lengths and numeric ranges
6. **Request Validation:** All requests validated before processing

---

## Troubleshooting

### Issue: "Module not found" error for loan_orchestrator

**Solution:** Ensure `loan_orchestrator.py` is in the same directory or Python path. The app falls back to mock orchestrator if unavailable.

### Issue: CORS errors in frontend

**Solution:** Check `FRONTEND_URL` environment variable or add origin to `allow_origins` list in CORSMiddleware configuration.

### Issue: Database connection fails

**Solution:** Check database credentials in `.env` and verify database service is running. Application continues with `db_connected = False`.

### Issue: High response times

**Solution:**
- Check orchestrator processing time
- Increase page sizes for large datasets
- Monitor database query performance
- Consider implementing caching

---

## API Versioning

Current API version: **v1**

The API uses URL-based versioning:
- `/api/v1/applications` - Version 1 endpoints
- Future versions: `/api/v2/applications`

---

## Future Enhancements

1. **Database Persistence:**
   - Replace in-memory storage with PostgreSQL/MongoDB
   - Implement proper transaction management

2. **Authentication:**
   - Add JWT token-based authentication
   - Implement role-based access control (RBAC)

3. **Async Processing:**
   - Background task queue (Celery, RQ)
   - Webhook notifications for decision updates

4. **Advanced Analytics:**
   - Decision statistics and reporting
   - Risk score distribution analysis
   - Application processing metrics

5. **Caching:**
   - Redis caching for frequently accessed decisions
   - ETag support for GET requests

6. **Rate Limiting:**
   - Per-endpoint rate limits
   - Per-client rate limiting

7. **WebSocket Support:**
   - Real-time application status updates
   - Live decision notifications

---

## Support & Contact

For issues, questions, or feature requests:
- Check logs for detailed error information
- Review API documentation at `/docs`
- Verify environment configuration in `.env`
- Check LangGraph orchestrator module availability
