# Enhanced ApplicantDB MCP Server - Quick Start Guide

## 5 Major Features at a Glance

### 1. ✉️ Webhook Support
Register endpoints to receive real-time notifications when applicant data changes.

```python
# Register webhook
webhook_id = register_webhook(
    url="https://myapp.com/webhooks/profile-updates",
    event_type="profile_updated"
)

# List webhooks
webhooks = list_webhooks(event_type="profile_updated")

# Unregister webhook
unregister_webhook(webhook_id)
```

**Event Types:**
- `profile_updated` - Profile created or modified
- `credit_updated` - Credit score or debt changed
- `employment_verified` - Employment verified
- `validation_failed` - Profile validation failed

---

### 2. 📦 Batch Operations
Retrieve multiple applicant profiles efficiently in a single call.

```python
# Get batch of 10 applicants
result = get_applicants_batch([
    "APP001", "APP002", "APP003",
    "APP004", "APP005", "APP006",
    "APP007", "APP008", "APP009", "APP010"
])

# Access results
for profile in result["profiles"]:
    app = profile["applicant"]
    print(f"{app['id']}: {app['first_name']} {app['last_name']}")
    print(f"  Validation Status: {app['validation_status']}")
    print(f"  Credit Score: {profile['credit_history'][0]['credit_score']}")

# Summary stats
print(f"Retrieved: {result['summary']['retrieved']}")
print(f"Not Found: {result['summary']['not_found']}")
```

**Limits:**
- Maximum 100 applicants per request
- More efficient than individual requests
- Fully cached and indexed

---

### 3. ✅ Advanced Validation Rules
9 comprehensive validation rules for profile data.

```python
# Validate a profile
result = validate_applicant_profile("APP001")

if result["validation_status"] == "valid":
    print(f"✓ Valid: {result['rules_passed']}/{result['rules_checked']} passed")
else:
    print(f"✗ Invalid:")
    for error in result["errors"]:
        print(f"  - {error}")
```

**Validation Rules:**
1. Email Format - Valid email syntax
2. Credit Score Range - 300-850 FICO range
3. Income Threshold - Minimum $20,000/year
4. Employment Status - Valid status values
5. Phone Format - At least 10 digits
6. SSN Format - Exactly 9 digits
7. Debt-to-Income Ratio - Maximum 43%
8. Address Completeness - Complete if provided
9. Age Requirement - Minimum 18 years old

---

### 4. 📜 Audit Trail
Complete historical tracking of all changes to applicant data.

```python
# Get audit history
history = get_applicant_audit_history("APP001", limit=50)

for event in history["history"]:
    print(f"Event: {event['event_type']}")
    print(f"  Action: {event['action']}")
    print(f"  User: {event['user_id']}")
    print(f"  Time: {event['timestamp']}")
    print(f"  Changes: {event['new_values']}")
```

**Event Types:**
- `profile_created` - New applicant created
- `profile_updated` - Profile information changed
- `credit_updated` - Credit data updated
- `employment_verified` - Employment verified
- `validation_failed` - Validation failed
- `data_enriched` - Data enriched from external source
- `webhook_triggered` - Webhook event sent

---

### 5. 🔄 Data Enrichment
Automatic enrichment with external service data (simulated).

```python
# Create applicant with automatic enrichment
result = create_applicant(
    applicant_id="APP001",
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    ssn="123-45-6789",
    annual_income=85000
)

# Access enrichment data
enrichment = result["enrichment_data"]

# Credit enrichment
print(f"Credit Score: {enrichment['credit_enrichment']['credit_score']}")
print(f"Total Debt: ${enrichment['credit_enrichment']['total_debt']}")

# Employment enrichment
print(f"Employment Verified: {enrichment['employment_enrichment']['employment_verified']}")

# Identity enrichment
print(f"Identity Verified: {enrichment['identity_enrichment']['identity_verified']}")
```

**Enrichment Services:**
1. Credit Bureau - Credit score, debt, available credit
2. Employment Service - Employment verification, confidence
3. Identity Service - Identity verification status

---

## Complete Workflow Example

```python
from applicantdb_mcp_server_enhanced import *

# 1. Create applicant with enrichment & validation
applicant = create_applicant(
    applicant_id="APP100",
    first_name="Jane",
    last_name="Smith",
    email="jane@example.com",
    phone="555-123-4567",
    ssn="987-65-4321",
    date_of_birth="1990-05-15",
    address="123 Main St",
    city="San Francisco",
    state="CA",
    zip_code="94105",
    employment_status="active",
    annual_income=95000
)

print(f"Created: {applicant['applicant_id']}")
print(f"Validation: {applicant['validation_status']}")
print(f"Errors: {applicant['validation_errors']}")

# 2. Validate profile with all rules
validation = validate_applicant_profile("APP100")
print(f"Validation passed: {validation['rules_passed']}/{validation['rules_checked']}")

# 3. Update credit history
credit = update_applicant_credit_history(
    applicant_id="APP100",
    credit_score=750,
    total_debt=20000,
    available_credit=25000
)
print(f"Credit updated: {credit['record_id']}")

# 4. Verify employment
employment = verify_employment(
    applicant_id="APP100",
    employer_id="EMP123",
    employee_id="EMP-98765",
    job_title="Senior Manager",
    salary=95000
)
print(f"Employment verified: {employment['verification']['status']}")

# 5. Register webhook for notifications
webhook = register_webhook(
    url="https://myapp.com/hooks/applicant-updates",
    event_type="profile_updated"
)
print(f"Webhook registered: {webhook['webhook_id']}")

# 6. Get complete profile with audit trail
profile = get_applicant_profile("APP100")
print(f"Profile: {profile['data']['applicant']['first_name']} {profile['data']['applicant']['last_name']}")

audit_history = get_applicant_audit_history("APP100")
print(f"Audit events: {audit_history['count']}")

# 7. Batch retrieve multiple profiles
batch = get_applicants_batch(["APP100", "APP101", "APP102"])
print(f"Batch retrieved: {batch['summary']['retrieved']} applicants")

# 8. Get database statistics
stats = get_database_stats()
print(f"Total applicants: {stats['applicant_stats']['total']}")
print(f"Webhooks registered: {stats['webhook_stats']['total_webhooks']}")
print(f"Audit events: {stats['audit_stats']['total_events']}")
```

---

## MCP Tools Reference

### Profile Management
- `create_applicant(...)` - Create new applicant
- `get_applicant_profile(applicant_id)` - Get single profile
- `get_applicants_batch(applicant_ids)` - Get multiple profiles
- `validate_applicant_profile(applicant_id)` - Validate profile

### Credit & Employment
- `update_applicant_credit_history(...)` - Update credit data
- `verify_employment(...)` - Verify employment
- `add_employer(...)` - Add employer to database

### Webhooks
- `register_webhook(url, event_type)` - Register webhook
- `unregister_webhook(webhook_id)` - Remove webhook
- `list_webhooks(event_type)` - List webhooks

### Audit & History
- `get_applicant_audit_history(applicant_id, limit)` - Get audit trail

### Information
- `get_database_stats()` - Database statistics

---

## Database Locations

```
~/.mcp_applicantdb_enhanced/
├── applicantdb.sqlite       # Applicant profiles & credit data
├── employers.sqlite         # Employer data
└── audit.sqlite            # Audit trail & webhooks
```

---

## Performance Tips

1. **Use Batch Operations** for multiple applicants
2. **Leverage Caching** - LRU cache stores 128 profiles
3. **Validate Early** - Check profiles before processing
4. **Monitor Webhooks** - Verify endpoints are reachable
5. **Archive Audit** - Archive old audit records after retention period

---

## Test Suite

Run comprehensive tests:

```bash
python test_applicantdb_enhanced.py
```

Tests cover:
- Webhook registration and dispatch
- Batch applicant retrieval
- All 9 validation rules
- Audit trail logging
- Data enrichment
- Integrated workflows

---

## Docker Quick Start

```dockerfile
FROM python:3.11
WORKDIR /app
COPY applicantdb_mcp_server_enhanced.py .
RUN pip install fastmcp
EXPOSE 8000
CMD ["python", "applicantdb_mcp_server_enhanced.py"]
```

Build and run:
```bash
docker build -t applicantdb-enhanced .
docker run -p 8000:8000 applicantdb-enhanced
```

---

## Common Use Cases

### Use Case 1: Loan Application Processing
```python
# Create applicant
app = create_applicant(...)

# Validate against requirements
validation = validate_applicant_profile(app['applicant_id'])

# Get enriched data
profile = get_applicant_profile(app['applicant_id'])

# Check credit score from enrichment
credit_data = profile['data']['applicant']['enrichment_data']['credit_enrichment']

# Verify employment
employment = verify_employment(
    applicant_id=app['applicant_id'],
    employer_id=profile['data']['applicant']['employer_id']
)

# Track all changes
audit = get_applicant_audit_history(app['applicant_id'])
```

### Use Case 2: Batch Data Import
```python
# Create multiple applicants
applicant_ids = []
for data in import_data:
    result = create_applicant(**data)
    applicant_ids.append(result['applicant_id'])

# Retrieve batch for processing
batch = get_applicants_batch(applicant_ids)

# Validate all profiles
for profile in batch['profiles']:
    validation = validate_applicant_profile(profile['applicant']['id'])
    print(f"{profile['applicant']['id']}: {validation['validation_status']}")
```

### Use Case 3: Real-time Notifications
```python
# Register webhook for CRM integration
webhook = register_webhook(
    url="https://crm.example.com/api/applicants/webhook",
    event_type="profile_updated"
)

# When profiles are created/updated, CRM receives notification
# Can also register for credit and employment updates
```

### Use Case 4: Compliance Reporting
```python
# Get audit trail for all events
audit_history = get_applicant_audit_history(applicant_id, limit=10000)

# Generate compliance report
by_event_type = {}
for event in audit_history['history']:
    event_type = event['event_type']
    by_event_type[event_type] = by_event_type.get(event_type, 0) + 1

print("Event Summary:")
for event_type, count in by_event_type.items():
    print(f"  {event_type}: {count}")
```

---

## Error Handling

```python
# All tools return {"success": bool, ...} structure
result = create_applicant(...)

if result["success"]:
    print(f"Created: {result['applicant_id']}")
else:
    print(f"Error: {result['error']}")

# Batch operations handle partial failures
batch_result = get_applicants_batch(applicant_ids)
if batch_result['summary']['not_found'] > 0:
    print(f"Warning: {batch_result['summary']['not_found']} not found")

# Validation includes detailed errors
validation = validate_applicant_profile(applicant_id)
if validation['validation_status'] == 'invalid':
    for error in validation['errors']:
        print(f"Validation error: {error}")
```

---

## Next Steps

1. ✅ Start with creating applicants
2. ✅ Validate profiles with comprehensive rules
3. ✅ Set up webhooks for real-time notifications
4. ✅ Monitor audit trail for compliance
5. ✅ Use batch operations for efficiency
6. ✅ Integrate enriched data into workflows

---

For detailed documentation, see: `ENHANCED_APPLICANTDB_FEATURES.md`
