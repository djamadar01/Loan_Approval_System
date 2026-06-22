# ApplicantDB MCP Server - Setup and Configuration Guide

## Overview

ApplicantDB is a production-ready Model Context Protocol (MCP) server for managing applicant profiles, credit history, and employment verification. It features:

- **SQLite Database**: Persistent storage for applicants and employment records
- **Employer Database**: Separate database for employer information and employee records
- **Caching**: LRU caching for frequently accessed profiles
- **Comprehensive Validation**: Input validation and error handling
- **Employment Verification**: Employer database lookup system
- **Credit Tracking**: Historical credit information management
- **Full-text Search Ready**: Indexed fields for efficient queries

## Installation

### 1. Install Dependencies

```bash
pip install -r applicantdb_requirements.txt
```

### 2. Database Initialization

The database is automatically initialized on first run. Databases are created in:
- Applicant DB: `~/.mcp_applicantdb/applicantdb.sqlite`
- Employer DB: `~/.mcp_applicantdb/employers.sqlite`

### 3. Server Startup

```bash
python applicantdb_mcp_server.py
```

The server will:
1. Create databases if they don't exist
2. Initialize schema with all required tables
3. Start listening on `127.0.0.1:8000`

## Database Schema

### Applicants Table
```sql
CREATE TABLE applicants (
    id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    ssn TEXT UNIQUE,
    date_of_birth TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    employment_status TEXT,
    employer_id TEXT,
    annual_income REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### Credit History Table
```sql
CREATE TABLE credit_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id TEXT NOT NULL,
    credit_score INTEGER,
    total_debt REAL,
    available_credit REAL,
    payment_history TEXT,
    last_updated TEXT NOT NULL,
    updated_by TEXT,
    FOREIGN KEY (applicant_id) REFERENCES applicants(id)
)
```

### Employers Table
```sql
CREATE TABLE employers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    headquarters_state TEXT,
    employee_count INTEGER,
    verified BOOLEAN DEFAULT 1,
    created_at TEXT NOT NULL
)
```

### Employee Records Table
```sql
CREATE TABLE employee_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employer_id TEXT NOT NULL,
    applicant_id TEXT NOT NULL,
    employee_id TEXT,
    start_date TEXT,
    current_status TEXT,
    job_title TEXT,
    salary REAL,
    verified_at TEXT NOT NULL,
    FOREIGN KEY (employer_id) REFERENCES employers(id)
)
```

## MCP Tools

### 1. create_applicant()
Create a new applicant record in the database.

**Parameters:**
- `applicant_id` (required): Unique identifier
- `first_name` (required): First name
- `last_name` (required): Last name
- `email` (required): Email address (must be valid)
- `phone` (optional): Phone number
- `ssn` (optional): Social security number
- `date_of_birth` (optional): ISO format date
- `address` (optional): Street address
- `city` (optional): City
- `state` (optional): State code
- `zip_code` (optional): ZIP code
- `employment_status` (optional): Employment status
- `employer_id` (optional): Current employer ID
- `annual_income` (optional): Annual income

**Returns:**
```json
{
    "success": true,
    "applicant_id": "APP_001",
    "message": "Applicant created successfully"
}
```

**Validation:**
- Required fields must be provided
- Email must contain "@"
- Each email and SSN must be unique

### 2. get_applicant_profile()
Retrieve complete applicant profile with caching.

**Parameters:**
- `applicant_id` (required): The applicant ID to retrieve

**Returns:**
```json
{
    "success": true,
    "data": {
        "applicant": {
            "id": "APP_001",
            "first_name": "Alice",
            "email": "alice@example.com",
            ...
        },
        "credit_history": [
            {
                "credit_score": 785,
                "total_debt": 25000.00,
                ...
            }
        ],
        "employment_records": [
            {
                "employer_name": "ACME Corp",
                "job_title": "Engineer",
                ...
            }
        ]
    }
}
```

**Caching:**
- Profiles are cached with 128-item LRU cache
- Cache is automatically invalidated on updates
- Dramatically improves performance for repeated queries

### 3. update_applicant_credit_history()
Add credit history record for an applicant.

**Parameters:**
- `applicant_id` (required): Applicant ID
- `credit_score` (optional): Credit score (300-850)
- `total_debt` (optional): Total outstanding debt
- `available_credit` (optional): Available credit limit
- `payment_history` (optional): List of payment records
- `updated_by` (optional): User/system that made update

**Returns:**
```json
{
    "success": true,
    "record_id": 1,
    "applicant_id": "APP_001",
    "updated_at": "2024-01-15T10:30:00",
    "updated_by": "system"
}
```

**Validation:**
- Credit score must be between 300 and 850
- Applicant must exist in database
- Automatically tracks update timestamp

### 4. verify_employment()
Verify employment with employer database lookup.

**Parameters:**
- `applicant_id` (required): Applicant ID
- `employer_id` (required): Employer ID (must exist)
- `employee_id` (optional): Employee ID in employer system
- `job_title` (optional): Job title
- `salary` (optional): Annual salary
- `start_date` (optional): Employment start date (ISO format)
- `current_status` (optional): Employment status (default: "active")

**Returns:**
```json
{
    "success": true,
    "verification": {
        "verification_id": 1,
        "applicant_id": "APP_001",
        "employer_id": "EMP_ACME",
        "employer_name": "ACME Corporation",
        "verified_at": "2024-01-15T10:30:00",
        "status": "verified"
    }
}
```

**Validation:**
- Employer must exist in database
- Creates permanent employment verification record
- Tracks verification timestamp

### 5. add_employer()
Add a new employer to the employer database.

**Parameters:**
- `employer_id` (required): Unique employer identifier
- `name` (required): Company name
- `industry` (optional): Industry type
- `headquarters_state` (optional): Headquarters state
- `employee_count` (optional): Number of employees
- `verified` (optional): Whether employer is verified

**Returns:**
```json
{
    "success": true,
    "employer_id": "EMP_ACME",
    "message": "Employer added successfully"
}
```

### 6. get_database_stats()
Get database statistics and metadata.

**Returns:**
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

## Error Handling

The server provides comprehensive error handling:

### ValidationError
- Missing required fields
- Invalid email format
- Credit score out of range (300-850)
- Duplicate unique values (email, SSN, applicant ID)

Example response:
```json
{
    "success": false,
    "error": "Invalid credit score: 900. Must be between 300 and 850.",
    "applicant_id": "APP_001"
}
```

### DatabaseError
- Connection failures
- Integrity constraint violations
- Query execution errors

Example response:
```json
{
    "success": false,
    "error": "Duplicate applicant ID or email: ...",
    "applicant_id": "APP_001"
}
```

## Running Tests

### Unit Tests
```bash
python applicantdb_test.py
```

Test coverage includes:
- Database initialization
- CRUD operations
- Input validation
- Credit history operations
- Employment verification
- Caching behavior
- Data isolation
- Complete workflows

### Example Client
```bash
python applicantdb_client_example.py
```

Demonstrates:
- Registering employers and applicants
- Updating credit profiles
- Verifying employment
- Retrieving complete profiles
- Database statistics

## Production Deployment

### 1. Database Backup

Regular backups are recommended:
```bash
cp ~/.mcp_applicantdb/applicantdb.sqlite ~/.mcp_applicantdb/applicantdb.sqlite.backup
cp ~/.mcp_applicantdb/employers.sqlite ~/.mcp_applicantdb/employers.sqlite.backup
```

### 2. Performance Optimization

The server includes performance optimizations:
- Indexed columns for fast lookups
- LRU caching for profile requests
- Connection pooling
- Foreign key constraints enabled

### 3. Logging Configuration

Logging is configured at INFO level. To change:
```python
logging.basicConfig(level=logging.DEBUG)  # or WARNING, ERROR
```

### 4. Security Considerations

- Validate all input before storing
- Use parameterized queries (prevents SQL injection)
- Implement row-level access control in production
- Consider encrypting SSN fields
- Regular security audits

## Data Integrity

The server maintains data integrity through:

1. **Foreign Key Constraints**: Enforced between applicants and credit history
2. **Unique Constraints**: Email and SSN must be unique per applicant
3. **Type Validation**: Credit scores, salary values, etc.
4. **Transaction Atomicity**: All-or-nothing database operations

## Performance Notes

- Applicant profile requests are cached (128 items)
- Indexed lookups on email, SSN, applicant_id
- Credit history ordered by most recent first
- Employment records joined with employer data

### Cache Invalidation
Cache is automatically cleared when:
- New applicant created
- Credit history updated
- Employment verified

## Troubleshooting

### Database Locked
If database is locked, ensure:
1. No other processes accessing the database
2. Previous operations completed successfully
3. Restart the server

### Connection Failures
Check:
1. Database file permissions
2. Disk space available
3. Database corruption (rebuild if necessary)

### Performance Issues
- Check database file size
- Run `VACUUM` on SQLite database
- Consider archiving old records

## API Integration Example

```python
from applicantdb_mcp_server import ApplicantDB, EmployerDB

# Initialize
app_db = ApplicantDB()
emp_db = EmployerDB()

# Create applicant
app_db.create_applicant({
    'id': 'APP_001',
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'john@example.com'
})

# Get profile
profile = app_db.get_applicant('APP_001')

# Add credit update
app_db.add_credit_update('APP_001', {
    'credit_score': 750,
    'total_debt': 20000
})
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Database Optimization** (Monthly):
   ```bash
   sqlite3 ~/.mcp_applicantdb/applicantdb.sqlite "VACUUM;"
   ```

2. **Index Analysis** (Quarterly):
   ```bash
   sqlite3 ~/.mcp_applicantdb/applicantdb.sqlite "ANALYZE;"
   ```

3. **Data Backup** (Weekly):
   Automated backup scripts recommended

## Version History

- **v1.0.0** - Initial release
  - Core applicant management
  - Credit history tracking
  - Employment verification
  - FastMCP integration
  - Comprehensive testing

## License

Production-ready implementation. See LICENSE file for details.
