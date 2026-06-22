# API Specification - Loan Decision System

**Version:** 1.0.0  
**Last Updated:** 2024-06-19  
**API Base URL:** `http://localhost:8000`

---

## Table of Contents

1. [Overview](#overview)
2. [OpenAPI/Swagger Specification](#openapi-swagger-specification)
3. [Authentication Flow](#authentication-flow)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
6. [Request/Response Models](#requestresponse-models)
7. [Error Codes & Meanings](#error-codes--meanings)
8. [Webhook Specification](#webhook-specification)
9. [Auto-Generation from FastAPI](#auto-generation-from-fastapi)

---

## Overview

The Loan Decision System API is a REST API built with FastAPI that provides comprehensive endpoints for:

- **Loan Application Submission**: Accept and validate loan applications
- **Application Status Tracking**: Monitor processing status of applications
- **Decision Management**: Retrieve and filter loan decisions
- **Health Monitoring**: System status and readiness checks
- **Webhook Events**: Real-time notifications for application lifecycle events

**Key Features:**
- Type-safe request/response validation using Pydantic
- Comprehensive error handling with detailed error codes
- Rate limiting to prevent abuse
- CORS support for multi-origin requests
- Structured logging for auditing
- JWT authentication (optional)
- Pagination support for large result sets
- Advanced filtering and sorting capabilities

---

## OpenAPI/Swagger Specification

### Interactive Documentation

FastAPI automatically generates interactive Swagger UI and ReDoc documentation:

- **Swagger UI**: `GET /docs` - Interactive API documentation with try-it-out functionality
- **ReDoc**: `GET/redoc` - Alternative API documentation
- **OpenAPI Schema**: `GET /openapi.json` - Machine-readable OpenAPI 3.0 specification

### Generate OpenAPI Schema

To programmatically generate the OpenAPI schema:

```python
from fastapi import FastAPI
from main import app

# Get the OpenAPI schema
schema = app.openapi()

# Export to JSON
import json
with open('openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)
```

### Auto-Generated OpenAPI Specification Structure

The API automatically generates OpenAPI 3.0 specification with:

```json
{
  "openapi": "3.0.2",
  "info": {
    "title": "Loan Decision System API",
    "description": "REST API for loan application processing and decision management",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "http://localhost:8000",
      "description": "Development server"
    },
    {
      "url": "https://api.example.com",
      "description": "Production server"
    }
  ],
  "paths": {
    "/health": {},
    "/api/v1/applications": {},
    "/api/v1/applications/{app_id}": {},
    "/api/v1/decisions": {},
    "/api/v1/webhooks/subscribe": {},
    "/api/v1/webhooks/unsubscribe": {}
  },
  "components": {
    "schemas": {},
    "securitySchemes": {
      "Bearer": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }
    }
  }
}
```

---

## Authentication Flow

### JWT Bearer Token Authentication

The API uses JWT (JSON Web Tokens) for stateless authentication.

#### 1. Token Request

**Endpoint:** `POST /api/v1/auth/token`

```http
POST /api/v1/auth/token HTTP/1.1
Host: api.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

**Request Parameters:**
- `grant_type`: `client_credentials` (OAuth2 Client Credentials flow)
- `client_id`: Your application's client ID
- `client_secret`: Your application's client secret

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response Fields:**
- `access_token`: JWT token for API requests (valid for 1 hour)
- `token_type`: Always "bearer"
- `expires_in`: Token expiration time in seconds
- `refresh_token`: Token for obtaining new access tokens

#### 2. Using the Token

Include the token in the Authorization header for all subsequent requests:

```http
GET /api/v1/applications/APP-20240619-000001 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 3. Token Refresh

**Endpoint:** `POST /api/v1/auth/refresh`

```http
POST /api/v1/auth/refresh HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 4. Token Validation

**Endpoint:** `POST /api/v1/auth/validate`

```http
POST /api/v1/auth/validate HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "valid": true,
  "client_id": "YOUR_CLIENT_ID",
  "expires_in": 2845,
  "scopes": ["read:applications", "write:applications"]
}
```

### Authentication Scopes

Available OAuth2 scopes:

| Scope | Description |
|-------|-------------|
| `read:applications` | Read application data |
| `write:applications` | Submit and update applications |
| `read:decisions` | View loan decisions |
| `write:decisions` | Modify decisions (admin only) |
| `read:webhooks` | Manage webhook subscriptions |
| `write:webhooks` | Create/delete webhooks |
| `admin` | Full administrative access |

### Public Endpoints (No Auth Required)

The following endpoints do not require authentication:

- `GET /health` - Health check
- `GET /` - Root endpoint
- `GET /docs` - Swagger documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema

---

## Rate Limiting

### Rate Limit Strategy

The API implements token bucket rate limiting on a per-client basis.

### Rate Limit Headers

All responses include rate limit information in HTTP headers:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1624108800
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Total requests allowed per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

### Rate Limits by Endpoint

| Endpoint | Limit | Window | Per |
|----------|-------|--------|-----|
| `GET /health` | 10000 | 1 hour | IP/Client |
| `POST /api/v1/applications` | 100 | 1 hour | Client |
| `GET /api/v1/applications/*` | 1000 | 1 hour | Client |
| `GET /api/v1/decisions` | 500 | 1 hour | Client |
| `POST /api/v1/webhooks/*` | 50 | 1 hour | Client |

### Rate Limit Exceeded Response

When rate limit is exceeded, the API returns HTTP 429 (Too Many Requests):

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1624112400
Content-Type: application/json

{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Limit reset at 2024-06-19T11:00:00Z",
  "timestamp": "2024-06-19T10:55:00Z",
  "request_id": "req_1234567890"
}
```

### Rate Limit Tiers

Premium customers can request higher rate limits:

| Tier | Requests/Hour | Cost |
|------|---------------|------|
| Free | 100 | $0 |
| Standard | 1,000 | $50 |
| Professional | 10,000 | $200 |
| Enterprise | Unlimited | Custom |

To upgrade: Contact support@example.com

---

## Endpoints

### 1. Health Check

#### Endpoint: `GET /health`

**Description:** Check API health status and readiness

**Authentication:** Not required

**Parameters:** None

**cURL Example:**

```bash
curl -X GET http://localhost:8000/health \
  -H "Content-Type: application/json"
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2024-06-19T10:55:00.000000Z",
  "version": "1.0.0",
  "orchestrator_ready": true,
  "database_connected": true
}
```

**Response Fields:**
- `status`: `healthy`, `degraded`, or `unhealthy`
- `timestamp`: ISO 8601 timestamp of check
- `version`: API version
- `orchestrator_ready`: LangGraph orchestrator status
- `database_connected`: Database connection status

---

### 2. Submit Loan Application

#### Endpoint: `POST /api/v1/applications`

**Description:** Submit a new loan application for processing

**Authentication:** Required (Bearer token with `write:applications` scope)

**Request Body:**

```json
{
  "personal_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "date_of_birth": "1990-01-15"
  },
  "employment_info": {
    "employer_name": "Acme Corporation",
    "job_title": "Software Engineer",
    "employment_status": "employed",
    "years_employed": 5.5,
    "monthly_income": 8000.00
  },
  "financial_info": {
    "annual_income": 96000.00,
    "monthly_expenses": 3000.00,
    "credit_score": 750,
    "existing_loans_count": 1,
    "savings_amount": 50000.00
  },
  "loan_details": {
    "loan_amount": 250000.00,
    "loan_term_months": 360,
    "loan_purpose": "home",
    "collateral_type": "property",
    "collateral_value": 300000.00
  },
  "additional_notes": "Urgent processing requested"
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @application_payload.json
```

**Response (202 Accepted):**

```json
{
  "application_id": "APP-20240619-000001",
  "status": "received",
  "message": "Application APP-20240619-000001 has been received and queued for processing",
  "submission_timestamp": "2024-06-19T10:55:00.000000Z",
  "estimated_processing_time_hours": 24
}
```

**Response Fields:**
- `application_id`: Unique identifier for the application (use for status checks)
- `status`: Current status ("received", "pending", "approved", "rejected", "under_review", "flagged")
- `message`: Human-readable message
- `submission_timestamp`: ISO 8601 timestamp of submission
- `estimated_processing_time_hours`: Estimated time to completion

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid request | Malformed JSON or invalid field values |
| 422 | Validation error | DTI ratio exceeds 50% or other validation rules |
| 401 | Unauthorized | Missing or invalid authentication token |
| 429 | Rate limit exceeded | Too many requests |
| 500 | Internal server error | Server-side processing error |

---

### 3. Get Application Status

#### Endpoint: `GET /api/v1/applications/{app_id}`

**Description:** Retrieve the current status of a loan application

**Authentication:** Required (Bearer token with `read:applications` scope)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `app_id` | string | Application ID returned from submission |

**Query Parameters:** None

**cURL Example:**

```bash
curl -X GET http://localhost:8000/api/v1/applications/APP-20240619-000001 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**

```json
{
  "application_id": "APP-20240619-000001",
  "status": "under_review",
  "applicant_name": "John Doe",
  "loan_amount": 250000.00,
  "submission_date": "2024-06-19T10:55:00.000000Z",
  "last_updated": "2024-06-19T11:30:00.000000Z",
  "current_stage": "risk_assessment",
  "notes": "Undergoing financial risk assessment"
}
```

**Response Fields:**
- `application_id`: Application identifier
- `status`: Current status
- `applicant_name`: Full name of applicant
- `loan_amount`: Requested loan amount in USD
- `submission_date`: Application submission timestamp
- `last_updated`: Most recent update timestamp
- `current_stage`: Current processing stage
- `notes`: Optional processing notes

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 404 | Not found | Application ID does not exist |
| 401 | Unauthorized | Missing or invalid token |
| 500 | Internal server error | Server-side error |

---

### 4. Get Loan Decisions

#### Endpoint: `GET /api/v1/decisions`

**Description:** Retrieve loan decisions with filtering, sorting, and pagination

**Authentication:** Required (Bearer token with `read:decisions` scope)

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `page_size` | integer | 10 | Results per page (1-100) |
| `decision_filter` | string | "all" | Filter: `approved`, `rejected`, `conditional`, `manual_review`, or `all` |
| `min_risk_score` | float | 0 | Minimum risk score (0-100) |
| `max_risk_score` | float | 100 | Maximum risk score (0-100) |
| `sort_by` | string | "decision_date" | Sort field: `decision_date`, `risk_score`, or `loan_amount` |
| `sort_order` | string | "desc" | Sort order: `asc` or `desc` |

**cURL Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/decisions?page=1&page_size=20&decision_filter=approved&min_risk_score=0&max_risk_score=30&sort_by=decision_date&sort_order=desc" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**

```json
{
  "decisions": [
    {
      "application_id": "APP-20240619-000001",
      "applicant_name": "John Doe",
      "loan_amount": 250000.00,
      "decision": "approved",
      "risk_score": 25.5,
      "decision_date": "2024-06-19T14:30:00.000000Z",
      "decision_reason": "Good credit score and stable employment",
      "approved_amount": 250000.00,
      "conditions": ["Property appraisal required", "Flood insurance required"]
    }
  ],
  "total_count": 145,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

**Response Fields:**
- `decisions`: Array of decision records
- `total_count`: Total number of decisions matching filters
- `page`: Current page number
- `page_size`: Results per page
- `has_more`: Whether more results available

**Decision Record Fields:**
- `application_id`: Application identifier
- `applicant_name`: Applicant name
- `loan_amount`: Requested loan amount
- `decision`: Decision type
- `risk_score`: Calculated risk score (0-100)
- `decision_date`: When decision was made
- `decision_reason`: Human-readable reason for decision
- `approved_amount`: Amount approved (if approved)
- `conditions`: List of conditions (if conditional approval)

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid parameters | Invalid page, page_size, or filter values |
| 401 | Unauthorized | Missing or invalid token |
| 500 | Internal server error | Server-side error |

---

### 5. Subscribe to Webhooks

#### Endpoint: `POST /api/v1/webhooks/subscribe`

**Description:** Subscribe to application status and decision events

**Authentication:** Required (Bearer token with `write:webhooks` scope)

**Request Body:**

```json
{
  "url": "https://your-domain.com/webhooks/application-events",
  "events": ["application.submitted", "application.approved", "application.rejected", "decision.made"],
  "secret": "your_webhook_secret_key",
  "active": true,
  "max_retries": 3,
  "timeout_seconds": 30
}
```

**Request Fields:**
- `url`: HTTPS URL to receive webhook events (required)
- `events`: Array of event types to subscribe to (required)
- `secret`: Secret key for HMAC signature verification (recommended)
- `active`: Whether webhook is active (default: true)
- `max_retries`: Maximum retry attempts on failure (default: 3)
- `timeout_seconds`: Request timeout in seconds (default: 30)

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/subscribe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://your-domain.com/webhooks/application-events",
    "events": ["application.submitted", "application.approved"],
    "secret": "your_webhook_secret_key"
  }'
```

**Response (201 Created):**

```json
{
  "webhook_id": "whk_1234567890abcdef",
  "url": "https://your-domain.com/webhooks/application-events",
  "events": ["application.submitted", "application.approved", "application.rejected", "decision.made"],
  "active": true,
  "created_at": "2024-06-19T10:55:00.000000Z",
  "last_triggered": null,
  "failure_count": 0
}
```

**Response Fields:**
- `webhook_id`: Unique webhook identifier
- `url`: Registered webhook URL
- `events`: Subscribed events
- `active`: Webhook active status
- `created_at`: Creation timestamp
- `last_triggered`: Last event delivery timestamp
- `failure_count`: Number of consecutive failures

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid URL | URL must be HTTPS and valid |
| 401 | Unauthorized | Missing or invalid token |
| 409 | Duplicate subscription | URL already subscribed to these events |
| 422 | Invalid events | Unknown event types requested |
| 500 | Internal server error | Server-side error |

---

### 6. Unsubscribe from Webhooks

#### Endpoint: `DELETE /api/v1/webhooks/subscribe/{webhook_id}`

**Description:** Unsubscribe from webhook events

**Authentication:** Required (Bearer token with `write:webhooks` scope)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `webhook_id` | string | Webhook identifier from subscription |

**cURL Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/webhooks/subscribe/whk_1234567890abcdef \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (204 No Content):**

No response body. Webhook successfully deleted.

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 404 | Not found | Webhook ID does not exist |
| 401 | Unauthorized | Missing or invalid token |
| 500 | Internal server error | Server-side error |

---

## Request/Response Models

### PersonalInfo Model

```json
{
  "type": "object",
  "properties": {
    "first_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "First name of applicant"
    },
    "last_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Last name of applicant"
    },
    "email": {
      "type": "string",
      "format": "email",
      "description": "Valid email address"
    },
    "phone": {
      "type": "string",
      "pattern": "^\\+?1?\\d{9,15}$",
      "description": "Phone number (9-15 digits)"
    },
    "date_of_birth": {
      "type": "string",
      "format": "date",
      "description": "Date in YYYY-MM-DD format"
    }
  },
  "required": ["first_name", "last_name", "email", "phone", "date_of_birth"]
}
```

### EmploymentInfo Model

```json
{
  "type": "object",
  "properties": {
    "employer_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "description": "Name of employer"
    },
    "job_title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Job title"
    },
    "employment_status": {
      "type": "string",
      "enum": ["employed", "self-employed", "unemployed", "retired"],
      "description": "Current employment status"
    },
    "years_employed": {
      "type": "number",
      "minimum": 0,
      "maximum": 70,
      "description": "Years at current employer"
    },
    "monthly_income": {
      "type": "number",
      "exclusiveMinimum": 0,
      "description": "Monthly gross income in USD"
    }
  },
  "required": ["employer_name", "job_title", "employment_status", "years_employed", "monthly_income"]
}
```

### FinancialInfo Model

```json
{
  "type": "object",
  "properties": {
    "annual_income": {
      "type": "number",
      "exclusiveMinimum": 0,
      "description": "Annual gross income in USD"
    },
    "monthly_expenses": {
      "type": "number",
      "minimum": 0,
      "description": "Monthly expenses in USD"
    },
    "credit_score": {
      "type": "integer",
      "minimum": 300,
      "maximum": 850,
      "description": "Credit score (300-850)"
    },
    "existing_loans_count": {
      "type": "integer",
      "minimum": 0,
      "description": "Number of existing loans"
    },
    "savings_amount": {
      "type": "number",
      "minimum": 0,
      "description": "Total savings in USD"
    }
  },
  "required": ["annual_income", "monthly_expenses", "credit_score", "existing_loans_count", "savings_amount"]
}
```

### LoanDetails Model

```json
{
  "type": "object",
  "properties": {
    "loan_amount": {
      "type": "number",
      "exclusiveMinimum": 0,
      "maximum": 1000000,
      "description": "Requested loan amount in USD (max $1M)"
    },
    "loan_term_months": {
      "type": "integer",
      "minimum": 6,
      "maximum": 360,
      "description": "Loan term in months (6-360)"
    },
    "loan_purpose": {
      "type": "string",
      "enum": ["home", "auto", "personal", "business", "education"],
      "description": "Primary purpose of the loan"
    },
    "collateral_type": {
      "type": "string",
      "enum": ["property", "vehicle", "cash", "none"],
      "nullable": true,
      "description": "Type of collateral offered"
    },
    "collateral_value": {
      "type": "number",
      "minimum": 0,
      "description": "Value of collateral in USD"
    }
  },
  "required": ["loan_amount", "loan_term_months", "loan_purpose"]
}
```

### ApplicationResponse Model

```json
{
  "type": "object",
  "properties": {
    "application_id": {
      "type": "string",
      "pattern": "^APP-\\d{8}-\\d{6}$",
      "description": "Unique application identifier"
    },
    "status": {
      "type": "string",
      "enum": ["received", "pending", "approved", "rejected", "under_review", "flagged"],
      "description": "Current application status"
    },
    "message": {
      "type": "string",
      "description": "Human-readable status message"
    },
    "submission_timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 submission timestamp"
    },
    "estimated_processing_time_hours": {
      "type": "integer",
      "description": "Estimated time to decision in hours"
    }
  },
  "required": ["application_id", "status", "message", "submission_timestamp", "estimated_processing_time_hours"]
}
```

### ErrorResponse Model

```json
{
  "type": "object",
  "properties": {
    "error": {
      "type": "string",
      "description": "Error type/title"
    },
    "detail": {
      "type": "string",
      "description": "Detailed error message"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 error timestamp"
    },
    "request_id": {
      "type": "string",
      "nullable": true,
      "description": "Unique request identifier for support"
    }
  },
  "required": ["error", "detail", "timestamp"]
}
```

---

## Error Codes & Meanings

### HTTP Status Codes

| Code | Meaning | Scenario |
|------|---------|----------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for asynchronous processing |
| 204 | No Content | Successful deletion/update with no response body |
| 400 | Bad Request | Malformed request or invalid parameters |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Authenticated but not authorized for this resource |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error (business logic violation) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side processing error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | API temporarily unavailable |

### Application-Specific Error Codes

| Error Code | HTTP Status | Meaning | Cause | Resolution |
|-----------|------------|---------|-------|-----------|
| `INVALID_EMAIL` | 400 | Email format invalid | Provided email doesn't match RFC 5322 | Provide valid email address |
| `INVALID_PHONE` | 400 | Phone format invalid | Phone must be 9-15 digits | Use format: +1-555-123-4567 |
| `INVALID_DATE_FORMAT` | 400 | Date format invalid | Date not in YYYY-MM-DD | Use ISO 8601 format |
| `CREDIT_SCORE_OUT_OF_RANGE` | 422 | Credit score invalid | Score not between 300-850 | Verify credit score |
| `DTI_RATIO_EXCEEDED` | 422 | Debt-to-income too high | DTI > 50% | Reduce debt or increase income |
| `NEGATIVE_AMOUNT` | 400 | Amount is negative | Loan amount must be positive | Provide positive amount |
| `LOAN_AMOUNT_EXCEEDS_LIMIT` | 422 | Loan exceeds maximum | Amount > $1,000,000 | Request lower amount |
| `INVALID_LOAN_TERM` | 400 | Loan term out of range | Term not 6-360 months | Use 6-360 month range |
| `INVALID_EMPLOYMENT_STATUS` | 400 | Unknown employment status | Status not in allowed list | Use: employed, self-employed, unemployed, retired |
| `APP_NOT_FOUND` | 404 | Application doesn't exist | Application ID not found | Verify application ID |
| `INVALID_TOKEN` | 401 | Token invalid or expired | Token malformed or expired | Obtain new token |
| `INSUFFICIENT_SCOPE` | 403 | Missing required scope | Token doesn't have required permissions | Request token with broader scopes |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit hit | Too many requests in time window | Wait for limit reset or upgrade tier |
| `DUPLICATE_WEBHOOK` | 409 | Webhook URL already registered | Webhook URL already exists | Use different URL or update existing |
| `INVALID_WEBHOOK_URL` | 400 | Webhook URL invalid | URL must be HTTPS and valid | Provide valid HTTPS URL |
| `INTERNAL_ERROR` | 500 | Server error | Unexpected server error | Retry request; contact support if persists |

### Error Response Examples

**Example 1: Validation Error (DTI Ratio)**

```json
{
  "error": "Validation error",
  "detail": "Debt-to-income ratio 0.65 exceeds maximum allowed (50%)",
  "timestamp": "2024-06-19T10:55:00.000000Z",
  "request_id": "req_20240619_1055_0001"
}
```

**Example 2: Authentication Error**

```json
{
  "error": "Unauthorized",
  "detail": "Invalid or expired authentication token",
  "timestamp": "2024-06-19T10:55:00.000000Z",
  "request_id": "req_20240619_1055_0002"
}
```

**Example 3: Rate Limit Error**

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Limit: 100/hour. Reset at 2024-06-19T11:55:00Z",
  "timestamp": "2024-06-19T10:55:00.000000Z",
  "request_id": "req_20240619_1055_0003"
}
```

---

## Webhook Specification

### Webhook Overview

Webhooks enable real-time notifications of application and decision events. The API will send HTTP POST requests to your registered webhook URL when events occur.

### Webhook Events

#### Event: `application.submitted`

**Description:** Triggered when a new loan application is submitted

**Payload:**

```json
{
  "event_id": "evt_1234567890abcdef",
  "event_type": "application.submitted",
  "timestamp": "2024-06-19T10:55:00.000000Z",
  "data": {
    "application_id": "APP-20240619-000001",
    "applicant_name": "John Doe",
    "email": "john@example.com",
    "loan_amount": 250000.00,
    "loan_purpose": "home",
    "submission_timestamp": "2024-06-19T10:55:00.000000Z"
  }
}
```

**Event Fields:**
- `event_id`: Unique event identifier for deduplication
- `event_type`: Always "application.submitted"
- `timestamp`: When event occurred (ISO 8601)
- `data`: Event-specific data

---

#### Event: `application.approved`

**Description:** Triggered when an application is approved

**Payload:**

```json
{
  "event_id": "evt_1234567890abcdef",
  "event_type": "application.approved",
  "timestamp": "2024-06-19T14:30:00.000000Z",
  "data": {
    "application_id": "APP-20240619-000001",
    "applicant_name": "John Doe",
    "email": "john@example.com",
    "loan_amount": 250000.00,
    "approved_amount": 250000.00,
    "interest_rate": 4.5,
    "conditions": ["Property appraisal required", "Flood insurance required"],
    "decision_timestamp": "2024-06-19T14:30:00.000000Z"
  }
}
```

---

#### Event: `application.rejected`

**Description:** Triggered when an application is rejected

**Payload:**

```json
{
  "event_id": "evt_1234567890abcdef",
  "event_type": "application.rejected",
  "timestamp": "2024-06-19T14:30:00.000000Z",
  "data": {
    "application_id": "APP-20240619-000001",
    "applicant_name": "John Doe",
    "email": "john@example.com",
    "loan_amount": 250000.00,
    "reason": "Credit score below acceptable threshold",
    "risk_score": 85.5,
    "decision_timestamp": "2024-06-19T14:30:00.000000Z",
    "appeal_instructions": "Contact support@example.com to appeal"
  }
}
```

---

#### Event: `decision.made`

**Description:** Triggered when a final decision is made

**Payload:**

```json
{
  "event_id": "evt_1234567890abcdef",
  "event_type": "decision.made",
  "timestamp": "2024-06-19T14:30:00.000000Z",
  "data": {
    "application_id": "APP-20240619-000001",
    "decision": "approved",
    "risk_score": 25.5,
    "decision_reason": "Good credit score and stable employment",
    "decision_timestamp": "2024-06-19T14:30:00.000000Z",
    "next_steps": "Documentation will be sent via email"
  }
}
```

---

### Webhook Delivery

#### Request Format

All webhook requests are HTTP POST with:

**Headers:**

```http
POST /webhooks/application-events HTTP/1.1
Host: your-domain.com
Content-Type: application/json
User-Agent: LoanDecisionSystem/1.0
X-Webhook-ID: whk_1234567890abcdef
X-Webhook-Signature: sha256=abcd1234...
X-Webhook-Delivery-ID: evt_dlv_1234567890abcdef
X-Webhook-Retry-Count: 0
```

| Header | Description |
|--------|-------------|
| `X-Webhook-ID` | Webhook subscription ID |
| `X-Webhook-Signature` | HMAC-SHA256 signature of body with secret |
| `X-Webhook-Delivery-ID` | Unique delivery attempt ID |
| `X-Webhook-Retry-Count` | Number of retry attempts (0 for first) |

#### Request Body

```json
{
  "event_id": "evt_1234567890abcdef",
  "event_type": "application.submitted",
  "timestamp": "2024-06-19T10:55:00.000000Z",
  "data": {}
}
```

---

### Webhook Security

#### HMAC Signature Verification

To verify webhook authenticity:

1. Extract `X-Webhook-Signature` header
2. Compute HMAC-SHA256 of request body using your webhook secret
3. Compare computed signature with header value

**Python Example:**

```python
import hmac
import hashlib

def verify_webhook(request_body: str, signature_header: str, secret: str) -> bool:
    """Verify webhook signature."""
    computed_signature = hmac.new(
        secret.encode(),
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = signature_header.replace("sha256=", "")
    return hmac.compare_digest(computed_signature, expected_signature)

# Usage
body = request.body
signature = request.headers.get("X-Webhook-Signature")
is_valid = verify_webhook(body, signature, "your_webhook_secret")
```

**Node.js Example:**

```javascript
const crypto = require('crypto');

function verifyWebhook(requestBody, signatureHeader, secret) {
  const computedSignature = crypto
    .createHmac('sha256', secret)
    .update(requestBody)
    .digest('hex');
  
  const expectedSignature = signatureHeader.replace('sha256=', '');
  return crypto.timingSafeEqual(
    Buffer.from(computedSignature),
    Buffer.from(expectedSignature)
  );
}
```

---

### Webhook Response

Your webhook endpoint must respond with:

**Success Response (200-299):**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "received": true
}
```

**Failure Response (400+):**

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Processing failed"
}
```

---

### Webhook Retry Policy

Failed webhook deliveries are automatically retried:

| Attempt | Delay | Total Time |
|---------|-------|-----------|
| 1 (initial) | - | 0 seconds |
| 2 (retry) | 5 minutes | 5 minutes |
| 3 (retry) | 30 minutes | 35 minutes |
| 4 (retry) | 2 hours | 2.5 hours |
| 5 (final retry) | 24 hours | 26.5 hours |

After 5 total attempts, the webhook is marked as failed and disabled. Check webhook status with:

```bash
curl -X GET http://localhost:8000/api/v1/webhooks/whk_1234567890abcdef \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Example Webhook Handler

**Flask Example:**

```python
from flask import Flask, request
import hmac
import hashlib
import json

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret"

@app.route('/webhooks/application-events', methods=['POST'])
def handle_webhook():
    """Handle webhook events from Loan Decision System."""
    
    # 1. Verify signature
    signature = request.headers.get('X-Webhook-Signature', '')
    body = request.get_data()
    
    computed_sig = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, computed_sig):
        return {'error': 'Invalid signature'}, 403
    
    # 2. Parse event
    event = request.get_json()
    event_type = event.get('event_type')
    event_id = event.get('event_id')
    data = event.get('data', {})
    
    # 3. Idempotency check (store event_id in database)
    if is_event_processed(event_id):
        return {'received': True}, 200
    
    # 4. Handle event
    if event_type == 'application.submitted':
        handle_application_submitted(data)
    elif event_type == 'application.approved':
        handle_application_approved(data)
    elif event_type == 'application.rejected':
        handle_application_rejected(data)
    elif event_type == 'decision.made':
        handle_decision_made(data)
    
    # 5. Mark as processed
    mark_event_processed(event_id)
    
    return {'received': True}, 200

def handle_application_submitted(data):
    """Process application.submitted event."""
    application_id = data.get('application_id')
    applicant_name = data.get('applicant_name')
    print(f"New application submitted: {application_id} - {applicant_name}")

def handle_application_approved(data):
    """Process application.approved event."""
    application_id = data.get('application_id')
    approved_amount = data.get('approved_amount')
    print(f"Application approved: {application_id} - ${approved_amount}")

def handle_application_rejected(data):
    """Process application.rejected event."""
    application_id = data.get('application_id')
    reason = data.get('reason')
    print(f"Application rejected: {application_id} - {reason}")

def handle_decision_made(data):
    """Process decision.made event."""
    application_id = data.get('application_id')
    decision = data.get('decision')
    print(f"Decision made: {application_id} - {decision}")
```

---

## Auto-Generation from FastAPI

### Automatic OpenAPI Generation

FastAPI automatically generates OpenAPI 3.0 specification from Python type hints and docstrings.

### Command: Generate OpenAPI JSON

**Using FastAPI CLI:**

```bash
fastapi run main.py --help
```

**Using Python script:**

```python
import json
from main import app

# Generate OpenAPI schema
schema = app.openapi()

# Export to file
with open('openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)

print("OpenAPI schema exported to openapi.json")
```

### Command: Validate with OpenAPI Standards

```bash
# Install openapi-spec-validator
pip install openapi-spec-validator

# Validate generated schema
openapi-spec-validator openapi.json
```

### Auto-Generate Clients from OpenAPI

**Python Client (OpenAPI Generator):**

```bash
# Install openapi-generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./generated_client
```

**TypeScript Client:**

```bash
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-fetch \
  -o ./generated_client_ts
```

**Documentation Generation:**

```bash
openapi-generator-cli generate \
  -i openapi.json \
  -g markdown \
  -o ./generated_docs
```

### FastAPI Integration with OpenAPI

**Key FastAPI decorators for OpenAPI generation:**

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Loan Decision System API",
    description="REST API for loan application processing",
    version="1.0.0",
    terms_of_service="https://example.com/terms",
    contact={
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

@app.get(
    "/api/v1/applications/{app_id}",
    response_model=ApplicationStatus,
    responses={
        200: {"description": "Application found"},
        404: {"description": "Application not found"},
        500: {"description": "Server error"},
    },
    tags=["Applications"],
    summary="Get application status",
    operation_id="getApplicationStatus"
)
async def get_application_status(
    app_id: str = Path(..., description="Application ID")
) -> ApplicationStatus:
    """
    Retrieve the current status of a loan application.
    
    Args:
        app_id: The application ID to retrieve
        
    Returns:
        ApplicationStatus object with current status
        
    Raises:
        HTTPException 404: Application not found
        HTTPException 500: Server error
    """
    pass
```

---

### Exposing OpenAPI Schema

**Interactive Swagger UI:**

```
GET /docs
```

**ReDoc Alternative:**

```
GET /redoc
```

**Raw OpenAPI JSON:**

```
GET /openapi.json
```

### OpenAPI Customization

**Custom OpenAPI schema function:**

```python
def custom_openapi():
    """Customize OpenAPI schema."""
    if not app.openapi_schema:
        app.openapi_schema = app.openapi()
        # Customize schema
        app.openapi_schema["servers"] = [
            {
                "url": "https://api.example.com",
                "description": "Production"
            },
            {
                "url": "https://staging-api.example.com",
                "description": "Staging"
            }
        ]
    return app.openapi_schema

app.openapi = custom_openapi
```

---

## Implementation Guidelines

### For API Consumers

1. **Obtain Authentication Token:** Use OAuth2 client credentials to get JWT token
2. **Set Headers:** Include Authorization header in all authenticated requests
3. **Handle Errors:** Check status codes and error response fields
4. **Respect Rate Limits:** Monitor X-RateLimit-* headers and implement backoff
5. **Verify Webhooks:** Always verify signature on incoming webhook events
6. **Implement Idempotency:** Use event_id to deduplicate webhook events

### For API Developers

1. **Use Type Hints:** Enable automatic OpenAPI generation
2. **Add Docstrings:** Enhance auto-generated documentation
3. **Define Models:** Use Pydantic for validation
4. **Handle Errors:** Implement comprehensive error responses
5. **Implement Security:** Use JWT, scopes, and rate limiting
6. **Test Thoroughly:** Use OpenAPI schema for integration testing

---

## Conclusion

This API specification provides a complete reference for integrating with the Loan Decision System. The API is designed for:

- **Security:** JWT authentication with scopes
- **Reliability:** Retry logic and webhooks for async events
- **Scalability:** Rate limiting and pagination
- **Usability:** Clear documentation and auto-generated schemas

For support: support@example.com

