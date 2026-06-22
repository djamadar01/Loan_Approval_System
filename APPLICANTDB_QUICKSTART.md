# ApplicantDB MCP Server - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r applicantdb_requirements.txt
```

### 2. Start the Server
```bash
python applicantdb_mcp_server.py
```

Expected output:
```
INFO - applicantdb_mcp_server - Database initialized at ~/.mcp_applicantdb/applicantdb.sqlite
INFO - applicantdb_mcp_server - Employer database initialized at ~/.mcp_applicantdb/employers.sqlite
```

### 3. Run the Demo
In another terminal:
```bash
python applicantdb_client_example.py
```

Output shows complete workflow with employers, applicants, credit history, and employment verification.

### 4. Run Tests
```bash
python applicantdb_test.py
```

All 19 tests should pass.

## Usage Examples

### Python Client

```python
from applicantdb_mcp_server import ApplicantDB, EmployerDB

# Initialize
app_db = ApplicantDB()
emp_db = EmployerDB()

# Register employer
emp_db.add_employer({
    'id': 'EMP_001',
    'name': 'Tech Corp',
    'industry': 'Technology'
})

# Register applicant
app_db.create_applicant({
    'id': 'APP_001',
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'john@example.com',
    'annual_income': 95000
})

# Add credit information
app_db.add_credit_update('APP_001', {
    'credit_score': 750,
    'total_debt': 20000
})

# Verify employment
emp_db.verify_employment('APP_001', 'EMP_001', {
    'job_title': 'Senior Engineer',
    'salary': 95000
})

# Get complete profile
profile = app_db.get_applicant('APP_001')
credit_history = app_db.get_credit_history('APP_001')
employment = emp_db.get_employment_records('APP_001')
```

### High-Level Client

```python
from applicantdb_client_example import ApplicantDBClient

client = ApplicantDBClient()

# Register applicant
result = client.register_applicant(
    applicant_id='APP_001',
    first_name='John',
    last_name='Doe',
    email='john@example.com',
    phone='555-0101',
    annual_income=95000
)

# Update credit
result = client.update_credit_profile(
    applicant_id='APP_001',
    credit_score=750,
    total_debt=20000
)

# Verify employment
result = client.verify_applicant_employment(
    applicant_id='APP_001',
    employer_id='EMP_001',
    job_title='Engineer',
    salary=95000
)

# Get profile
profile = client.get_complete_profile('APP_001')
print(profile)
```

## Key Features

### 1. Applicant Management
- Create applicants with personal info
- Store contact details, SSN, DOB
- Track employment and income

### 2. Credit History
- Track credit scores (300-850)
- Store debt and credit limits
- Maintain payment history
- Timestamped updates

### 3. Employment Verification
- Register employers
- Verify applicant employment
- Store job titles and salaries
- Track employment dates

### 4. Performance
- LRU caching (128 profiles)
- Indexed database queries
- Automatic cache invalidation
- Fast profile retrieval

### 5. Data Integrity
- Foreign key constraints
- Unique email and SSN
- Type validation
- Transaction atomicity

## Database Schema

```
APPLICANTS TABLE
├─ id (PK)
├─ first_name, last_name
├─ email (UNIQUE)
├─ phone
├─ ssn (UNIQUE)
├─ date_of_birth
├─ address, city, state, zip_code
├─ employment_status
├─ employer_id (FK)
├─ annual_income
└─ created_at, updated_at

CREDIT_HISTORY TABLE
├─ id (PK)
├─ applicant_id (FK)
├─ credit_score (300-850)
├─ total_debt
├─ available_credit
├─ payment_history (JSON)
├─ last_updated
└─ updated_by

EMPLOYERS TABLE
├─ id (PK)
├─ name
├─ industry
├─ headquarters_state
├─ employee_count
├─ verified
└─ created_at

EMPLOYEE_RECORDS TABLE
├─ id (PK)
├─ employer_id (FK)
├─ applicant_id
├─ employee_id
├─ start_date
├─ current_status
├─ job_title
├─ salary
└─ verified_at
```

## Error Handling

Common errors and solutions:

### ValidationError: "Invalid email format"
```python
# ✗ Wrong
create_applicant({'email': 'invalid-email'})

# ✓ Correct
create_applicant({'email': 'user@example.com'})
```

### ValidationError: "Invalid credit score"
```python
# ✗ Wrong (score > 850)
add_credit_update(app_id, {'credit_score': 900})

# ✓ Correct (300-850)
add_credit_update(app_id, {'credit_score': 750})
```

### DatabaseError: "Duplicate applicant ID"
```python
# ✗ Wrong (ID already exists)
create_applicant({'id': 'APP_001', ...})  # After already creating APP_001

# ✓ Correct (use unique ID)
create_applicant({'id': 'APP_002', ...})
```

### ValidationError: "Applicant not found"
```python
# ✗ Wrong (applicant doesn't exist)
add_credit_update('NONEXISTENT', {...})

# ✓ Correct (create first)
create_applicant({'id': 'APP_001', ...})
add_credit_update('APP_001', {...})
```

## Database Maintenance

### Backup
```bash
cp ~/.mcp_applicantdb/applicantdb.sqlite ~/.backup/applicantdb.sqlite.bak
cp ~/.mcp_applicantdb/employers.sqlite ~/.backup/employers.sqlite.bak
```

### Optimize
```bash
sqlite3 ~/.mcp_applicantdb/applicantdb.sqlite "VACUUM;"
sqlite3 ~/.mcp_applicantdb/employers.sqlite "VACUUM;"
```

### Analyze (performance tuning)
```bash
sqlite3 ~/.mcp_applicantdb/applicantdb.sqlite "ANALYZE;"
```

### Check Integrity
```bash
sqlite3 ~/.mcp_applicantdb/applicantdb.sqlite "PRAGMA integrity_check;"
```

## Performance Tips

1. **Use Caching**: Profile requests cache results automatically
2. **Batch Operations**: Process multiple records efficiently
3. **Index Queries**: Email/SSN lookups use indexes
4. **Periodic Maintenance**: VACUUM and ANALYZE monthly
5. **Archive Old Data**: Move historical records to archive DB

## Configuration

### Change Cache Size
Edit `applicantdb_mcp_server.py`:
```python
CACHE_SIZE = 256  # Default is 128
```

### Change Database Location
Edit `applicantdb_mcp_server.py`:
```python
DB_PATH = Path('/custom/path/applicantdb.sqlite')
EMPLOYMENT_DB_PATH = Path('/custom/path/employers.sqlite')
```

### Enable Debug Logging
Edit `applicantdb_mcp_server.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Common Workflows

### Complete Applicant Onboarding
```python
client = ApplicantDBClient()

# 1. Create applicant
client.register_applicant(
    applicant_id='APP_NEW_001',
    first_name='Jane',
    last_name='Smith',
    email='jane@example.com',
    phone='555-1234',
    annual_income=80000
)

# 2. Add credit information
client.update_credit_profile(
    applicant_id='APP_NEW_001',
    credit_score=720,
    total_debt=15000
)

# 3. Verify current employment
client.verify_applicant_employment(
    applicant_id='APP_NEW_001',
    employer_id='EMP_CURRENT',
    job_title='Analyst',
    salary=80000
)

# 4. Get complete profile
profile = client.get_complete_profile('APP_NEW_001')
```

### Batch Import
```python
applicants_data = [
    {'id': 'APP_100', 'first_name': 'Alice', ...},
    {'id': 'APP_101', 'first_name': 'Bob', ...},
    {'id': 'APP_102', 'first_name': 'Charlie', ...},
]

for app_data in applicants_data:
    try:
        client.register_applicant(**app_data)
    except Exception as e:
        print(f"Error: {e}")
```

### Credit Profile Update
```python
# Update credit for existing applicant
client.update_credit_profile(
    applicant_id='APP_001',
    credit_score=760,
    total_debt=18000,
    available_credit=45000
)

# Retrieve history
profile = client.get_complete_profile('APP_001')
print(f"Credit Score: {profile['profile']['credit_history'][0]['credit_score']}")
```

## Testing

### Run All Tests
```bash
python applicantdb_test.py
```

### Run Specific Test
```python
import unittest
from applicantdb_test import TestApplicantDB

suite = unittest.TestLoader().loadTestsFromTestCase(TestApplicantDB)
unittest.TextTestRunner(verbosity=2).run(suite)
```

### Manual Testing
```python
from applicantdb_mcp_server import ApplicantDB

# Test database operations
db = ApplicantDB()

# Create
app_id = db.create_applicant({
    'id': 'TEST_001',
    'first_name': 'Test',
    'last_name': 'User',
    'email': 'test@example.com'
})
print(f"Created: {app_id}")

# Read
app = db.get_applicant('TEST_001')
print(f"Retrieved: {app}")

# Update
db.add_credit_update('TEST_001', {'credit_score': 750})
print("Credit updated")

# Verify
history = db.get_credit_history('TEST_001')
print(f"Credit history: {history}")
```

## Troubleshooting

### Server won't start
1. Check port 8000 is available
2. Verify Python version >= 3.8
3. Check dependencies installed: `pip list`

### Database locked
1. No other processes accessing DB
2. Restart server
3. Check file permissions

### Tests failing
1. Run in isolation: `python applicantdb_test.py`
2. Check temp directory has space
3. Clear old test databases in /tmp

### Slow queries
1. Run ANALYZE on database
2. Check cache hit rate
3. Consider archiving old records

## Next Steps

1. **Read API Documentation**: See APPLICANTDB_API.md
2. **Review Schema**: See APPLICANTDB_SETUP.md
3. **Explore Examples**: Check applicantdb_client_example.py
4. **Run Tests**: Execute applicantdb_test.py
5. **Deploy**: Follow production deployment guidelines

## Support

- Check logs: `tail -f ~/.mcp_applicantdb/logs`
- Run stats: `client.get_database_stats()`
- Test connection: Run applicantdb_test.py
- Review schema: Check applicantdb_mcp_server.py

## What's Next?

- Implement REST API wrapper
- Add web dashboard
- Create CLI tools
- Set up continuous backup
- Add advanced reporting
- Implement API authentication
