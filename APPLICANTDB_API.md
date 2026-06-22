# ApplicantDB MCP Server - API Reference

## Overview

ApplicantDB is a Model Context Protocol (MCP) server providing REST endpoints for managing applicant profiles, credit history, and employment verification. All endpoints follow JSON-RPC conventions via HTTP.

## Base URL

```
http://127.0.0.1:8000/
```

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
    "success": false,
    "error": "Error message describing the issue",
    "applicant_id": "APP_001"
}
```

### Error Types

| Error | HTTP Code | Description |
|-------|-----------|-------------|
| ValidationError | 400 | Invalid input data (missing fields, invalid format) |
| DatabaseError | 500 | Database operation failed |
| Not Found | 404 | Resource not found |
| Internal Error | 500 | Unexpected server error |

## Tools (Endpoints)

### 1. create_applicant

Create a new applicant record in the database.

**Endpoint:** `/tools/create_applicant`

**Method:** POST

**Request:**
```json
{
    "applicant_id": "APP_001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "555-0101",
    "ssn": "123-45-6789",
    "date_of_birth": "1990-05-15",
    "address": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94102",
    "employment_status": "employed",
    "employer_id": "EMP_001",
    "annual_income": 95000.00
}
```

**Response (Success):**
```json
{
    "success": true,
    "applicant_id": "APP_001",
    "message": "Applicant created successfully"
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Invalid email format: invalid-email"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| applicant_id | string | Yes | Unique identifier for applicant |
| first_name | string | Yes | First name |
| last_name | string | Yes | Last name |
| email | string | Yes | Email address (must contain @) |
| phone | string | No | Phone number |
| ssn | string | No | Social security number (unique) |
| date_of_birth | string (ISO) | No | Birth date YYYY-MM-DD |
| address | string | No | Street address |
| city | string | No | City |
| state | string | No | State code |
| zip_code | string | No | ZIP/Postal code |
| employment_status | string | No | Status: employed, unemployed, unknown |
| employer_id | string | No | Current employer ID |
| annual_income | number | No | Annual income in dollars |

**Validation Rules:**
- applicant_id must be unique
- email must be unique and contain "@"
- ssn must be unique (if provided)
- email format: must contain "@"

---

### 2. get_applicant_profile

Retrieve complete applicant profile with all related data (cached).

**Endpoint:** `/tools/get_applicant_profile`

**Method:** POST

**Request:**
```json
{
    "applicant_id": "APP_001"
}
```

**Response (Success):**
```json
{
    "success": true,
    "data": {
        "applicant": {
            "id": "APP_001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "555-0101",
            "ssn": "123-45-6789",
            "date_of_birth": "1990-05-15",
            "address": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94102",
            "employment_status": "employed",
            "employer_id": "EMP_001",
            "annual_income": 95000.00,
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00"
        },
        "credit_history": [
            {
                "id": 1,
                "applicant_id": "APP_001",
                "credit_score": 785,
                "total_debt": 25000.00,
                "available_credit": 50000.00,
                "payment_history": "[\"on_time\", \"on_time\"]",
                "last_updated": "2024-01-15T10:30:00",
                "updated_by": "system"
            }
        ],
        "employment_records": [
            {
                "id": 1,
                "employer_id": "EMP_001",
                "applicant_id": "APP_001",
                "employee_id": "EMP-123456",
                "start_date": "2020-01-15",
                "current_status": "active",
                "job_title": "Senior Engineer",
                "salary": 95000.00,
                "verified_at": "2024-01-15T10:30:00",
                "employer_name": "Tech Corp"
            }
        ]
    }
}
```

**Response (Not Found):**
```json
{
    "success": false,
    "error": "Applicant not found",
    "applicant_id": "APP_999"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| applicant_id | string | Yes | Applicant ID to retrieve |

**Performance Notes:**
- Results cached with LRU (128 items)
- Cache automatically invalidated on updates
- First request loads from DB, subsequent requests from cache

---

### 3. update_applicant_credit_history

Add a new credit history record for an applicant.

**Endpoint:** `/tools/update_applicant_credit_history`

**Method:** POST

**Request:**
```json
{
    "applicant_id": "APP_001",
    "credit_score": 785,
    "total_debt": 25000.00,
    "available_credit": 50000.00,
    "payment_history": ["on_time", "on_time", "late_30_days"],
    "updated_by": "system"
}
```

**Response (Success):**
```json
{
    "success": true,
    "record_id": 1,
    "applicant_id": "APP_001",
    "updated_at": "2024-01-15T10:35:00",
    "updated_by": "system"
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Invalid credit score: 900. Must be between 300 and 850.",
    "applicant_id": "APP_001"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| applicant_id | string | Yes | Applicant ID |
| credit_score | integer | No | Credit score 300-850 |
| total_debt | number | No | Total outstanding debt |
| available_credit | number | No | Available credit limit |
| payment_history | array | No | List of payment statuses |
| updated_by | string | No | User/system that made update (default: "system") |

**Validation Rules:**
- credit_score must be 300-850 (if provided)
- applicant must exist in database
- Timestamp automatically set to current UTC time

**Payment History Examples:**
```
"on_time"
"late_15_days"
"late_30_days"
"payment_deferred"
"charge_off"
```

---

### 4. verify_employment

Verify applicant employment with employer database lookup.

**Endpoint:** `/tools/verify_employment`

**Method:** POST

**Request:**
```json
{
    "applicant_id": "APP_001",
    "employer_id": "EMP_001",
    "employee_id": "EMP-123456",
    "job_title": "Senior Engineer",
    "salary": 95000.00,
    "start_date": "2020-01-15",
    "current_status": "active"
}
```

**Response (Success):**
```json
{
    "success": true,
    "verification": {
        "verification_id": 1,
        "applicant_id": "APP_001",
        "employer_id": "EMP_001",
        "employer_name": "Tech Corp",
        "verified_at": "2024-01-15T10:40:00",
        "status": "verified"
    }
}
```

**Response (Error - Employer Not Found):**
```json
{
    "success": false,
    "error": "Employer not found: EMP_999",
    "applicant_id": "APP_001",
    "employer_id": "EMP_999"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| applicant_id | string | Yes | Applicant ID |
| employer_id | string | Yes | Employer ID (must exist) |
| employee_id | string | No | Employee ID in employer system |
| job_title | string | No | Job title |
| salary | number | No | Annual salary |
| start_date | string (ISO) | No | Employment start date YYYY-MM-DD |
| current_status | string | No | Status: active, inactive (default: active) |

**Validation Rules:**
- employer_id must reference existing employer
- Creates permanent employment verification record
- Timestamp automatically set to current UTC time

---

### 5. add_employer

Add a new employer to the employer database.

**Endpoint:** `/tools/add_employer`

**Method:** POST

**Request:**
```json
{
    "employer_id": "EMP_001",
    "name": "Tech Corp Inc",
    "industry": "Technology",
    "headquarters_state": "CA",
    "employee_count": 5000,
    "verified": true
}
```

**Response (Success):**
```json
{
    "success": true,
    "employer_id": "EMP_001",
    "message": "Employer added successfully"
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Employer must have 'id' and 'name'"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| employer_id | string | Yes | Unique identifier |
| name | string | Yes | Company name |
| industry | string | No | Industry type |
| headquarters_state | string | No | State code |
| employee_count | integer | No | Number of employees |
| verified | boolean | No | Whether verified (default: true) |

**Validation Rules:**
- employer_id must be unique
- name is required
- Duplicate IDs are ignored (INSERT OR IGNORE)

---

### 6. get_database_stats

Get database statistics and metadata.

**Endpoint:** `/tools/get_database_stats`

**Method:** POST

**Request:**
```json
{}
```

**Response (Success):**
```json
{
    "success": true,
    "applicant_count": 3,
    "active_applicants": 2,
    "credit_history_records": 5,
    "employer_count": 2,
    "employment_records": 4,
    "applicant_db_path": "/home/user/.mcp_applicantdb/applicantdb.sqlite",
    "employer_db_path": "/home/user/.mcp_applicantdb/employers.sqlite",
    "cache_size": 128
}
```

**Parameters:** None

**Returns:**
- applicant_count: Total applicants in system
- active_applicants: Number with "active" employment status
- credit_history_records: Total credit update records
- employer_count: Number of registered employers
- employment_records: Total employment verifications
- applicant_db_path: Full path to applicant database
- employer_db_path: Full path to employer database
- cache_size: Maximum cached profiles (LRU)

---

## Request/Response Formats

### Standard Request Format

All requests use JSON in the request body:

```json
{
    "method": "tool_name",
    "params": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

### Standard Response Format

```json
{
    "success": true/false,
    "data": { ... },
    "error": "error message (if applicable)"
}
```

## Data Types and Formats

### Date/Time Format
- ISO 8601: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`
- Timestamps stored in UTC
- Example: `2024-01-15T10:30:00`

### Numeric Types
- credit_score: Integer 300-850
- salary/income: Floating point (currency)
- employee_count: Integer >= 0

### String Types
- email: Must contain "@"
- ssn: Format not enforced (but unique)
- phone: Format not enforced
- state: 2-letter code (CA, NY, etc.)
- zip_code: Flexible format

## Rate Limiting

No built-in rate limiting. Consider implementing:
- Per-IP rate limits
- Per-user rate limits
- Request queuing for high volume

## Pagination

Not implemented. For large datasets:
- Use database queries with LIMIT/OFFSET
- Or implement cursor-based pagination

## Caching

### Profile Caching

- LRU cache: 128 profiles
- Cache key: applicant_id
- Invalidated on:
  - New applicant created
  - Credit history updated
  - Employment verified

### Database Indexing

Indexed columns:
- applicants.email
- applicants.ssn
- credit_history.applicant_id
- credit_history.last_updated
- employee_records.applicant_id
- employee_records.employer_id

## Security Considerations

### Input Validation
- All inputs validated before storage
- SQL injection prevented via parameterized queries
- Type checking on numeric fields

### Data Protection
- SSN stored in plaintext (consider encryption for production)
- Foreign key constraints enforce referential integrity
- Row-level access control recommended for production

### Recommendations
1. Use HTTPS in production
2. Implement authentication/authorization
3. Add request signing
4. Encrypt SSN, DOB fields
5. Audit logging of sensitive operations
6. Regular security assessments

## Examples

### Complete Workflow Example

```bash
# 1. Add an employer
curl -X POST http://127.0.0.1:8000/tools/add_employer \
  -H "Content-Type: application/json" \
  -d '{
    "employer_id": "EMP_ACME",
    "name": "ACME Corporation",
    "industry": "Technology",
    "headquarters_state": "CA"
  }'

# 2. Create an applicant
curl -X POST http://127.0.0.1:8000/tools/create_applicant \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP_001",
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice@example.com",
    "annual_income": 95000,
    "employer_id": "EMP_ACME"
  }'

# 3. Update credit profile
curl -X POST http://127.0.0.1:8000/tools/update_applicant_credit_history \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP_001",
    "credit_score": 785,
    "total_debt": 25000,
    "available_credit": 50000
  }'

# 4. Verify employment
curl -X POST http://127.0.0.1:8000/tools/verify_employment \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP_001",
    "employer_id": "EMP_ACME",
    "job_title": "Senior Engineer",
    "salary": 95000,
    "start_date": "2020-01-15"
  }'

# 5. Get complete profile
curl -X POST http://127.0.0.1:8000/tools/get_applicant_profile \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP_001"
  }'

# 6. Get statistics
curl -X POST http://127.0.0.1:8000/tools/get_database_stats \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Python Client Example

```python
from applicantdb_mcp_server import ApplicantDB, EmployerDB

# Initialize
app_db = ApplicantDB()
emp_db = EmployerDB()

# Create applicant
app_db.create_applicant({
    'id': 'APP_001',
    'first_name': 'Alice',
    'last_name': 'Johnson',
    'email': 'alice@example.com'
})

# Get profile
profile = app_db.get_applicant('APP_001')

# Add credit update
app_db.add_credit_update('APP_001', {
    'credit_score': 785,
    'total_debt': 25000
})
```

## FAQ

**Q: Are SSNs encrypted?**
A: Not by default. Consider implementing encryption for production.

**Q: What's the maximum profile cache size?**
A: 128 profiles with LRU eviction.

**Q: Can I modify historical records?**
A: No, all records are append-only for audit trail.

**Q: How do I backup the database?**
A: Copy the .sqlite files to a backup location.

**Q: What happens if the server crashes?**
A: Data is persistent on disk. Restart the server to resume operations.

## Support

For issues or questions:
1. Check database logs in ~/.mcp_applicantdb/
2. Review error messages and validation rules
3. Verify data integrity with get_database_stats()
4. Check database file permissions and disk space
