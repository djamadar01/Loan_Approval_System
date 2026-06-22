# ApplicantDB MCP Server

A production-ready Model Context Protocol (MCP) server built with FastMCP that provides comprehensive tools for querying applicant profiles and assessment data. The server uses Pydantic models for type safety and includes a mock database with sample applicant data.

## Features

- **Type Safety**: All data models validated with Pydantic v2
- **FastMCP Integration**: Built using the modern MCP FastMCP framework
- **Mock Database**: Pre-populated with 5 realistic applicant records
- **Error Handling**: Comprehensive validation and user-friendly error messages
- **Four Core Tools**:
  1. `get_applicant_profile` - Retrieve complete profile with all assessment data
  2. `list_all_applicants` - View all applications with summary information
  3. `get_applicants_by_risk_level` - Filter applicants by employment risk
  4. `get_applications_requiring_action` - Find incomplete applications

## Architecture

### Pydantic Models

All data is validated using type-safe Pydantic models:

#### `IncomeStabilityScore`
- `score` (0-100): Income stability numeric score
- `trend`: Income trend (increasing, stable, decreasing)
- `volatility`: Income volatility level (low, moderate, high)
- `average_monthly`: Average monthly income in dollars

#### `EmploymentRisk` (Enum)
- `low`
- `medium`
- `high`

#### `CreditHistorySummary`
- `credit_score` (300-850): Numeric credit score
- `accounts_on_time`: Number of accounts with on-time payments
- `accounts_late`: Number of accounts with late payments
- `total_debt`: Total outstanding debt in dollars
- `debt_to_income_ratio`: DTI ratio as percentage
- `delinquencies`: Number of delinquencies in last 7 years

#### `ApplicationCompletenessFlags`
- `income_documentation_required`: Boolean flag
- `employment_verification_required`: Boolean flag
- `identity_verification_required`: Boolean flag
- `credit_authorization_required`: Boolean flag
- `missing_fields`: List of specific missing documents
- `completion_percentage` (0-100): Overall completion percentage

#### `ApplicantProfile`
Complete profile combining all assessment data:
- `applicant_id`: Unique identifier (e.g., "APP001")
- `name`: Applicant full name
- `email`: Email address
- `phone`: Phone number
- `income_stability`: IncomeStabilityScore object
- `employment_risk`: EmploymentRisk enum value
- `credit_history`: CreditHistorySummary object
- `completeness`: ApplicationCompletenessFlags object
- `application_date`: Application submission date
- `status`: Current status (submitted, under_review, approved, denied)

### Mock Database

The server includes a realistic mock database with 5 applicants:

| ID | Name | Risk Level | Income Score | Credit | Status |
|----|------|-----------|--------------|--------|--------|
| APP001 | Alice Johnson | Low | 85 | 750 | Approved |
| APP002 | Bob Smith | Medium | 62 | 680 | Under Review |
| APP003 | Carol Davis | High | 45 | 580 | Submitted |
| APP004 | David Martinez | Low | 92 | 800 | Approved |
| APP005 | Emily Wilson | Low | 71 | 720 | Under Review |

## Tool Specifications

### 1. get_applicant_profile

Retrieve a complete applicant profile with all assessment data.

**Parameters:**
- `applicant_id` (string, required): Unique applicant identifier (e.g., "APP001")

**Returns:**
Complete ApplicantProfile with Income Stability Score (0-100), Employment Risk level, Credit History Summary, and Application Completeness Flags.

**Example Response:**
```json
{
  "applicant_id": "APP001",
  "name": "Alice Johnson",
  "email": "alice.johnson@email.com",
  "phone": "555-0101",
  "income_stability": {
    "score": 85,
    "trend": "increasing",
    "volatility": "low",
    "average_monthly": 5250.00
  },
  "employment_risk": "low",
  "credit_history": {
    "credit_score": 750,
    "accounts_on_time": 8,
    "accounts_late": 0,
    "total_debt": 15000.00,
    "debt_to_income_ratio": 28.6,
    "delinquencies": 0
  },
  "completeness": {
    "income_documentation_required": false,
    "employment_verification_required": false,
    "identity_verification_required": false,
    "credit_authorization_required": false,
    "missing_fields": [],
    "completion_percentage": 100
  },
  "application_date": "2026-06-01",
  "status": "approved"
}
```

**Errors:**
- Raises `ValueError` if applicant_id not found in database

---

### 2. list_all_applicants

List all applicants in the database with basic summary information.

**Parameters:** None

**Returns:**
Dictionary containing:
- `total_count`: Total number of applicants
- `applicants`: Array of applicant summaries (id, name, email, status, date)

**Example Response:**
```json
{
  "total_count": 5,
  "applicants": [
    {
      "applicant_id": "APP001",
      "name": "Alice Johnson",
      "email": "alice.johnson@email.com",
      "status": "approved",
      "application_date": "2026-06-01"
    },
    {
      "applicant_id": "APP002",
      "name": "Bob Smith",
      "email": "bob.smith@email.com",
      "status": "under_review",
      "application_date": "2026-06-05"
    }
  ]
}
```

---

### 3. get_applicants_by_risk_level

Filter applicants by employment risk level.

**Parameters:**
- `risk_level` (string, required): One of "low", "medium", or "high"

**Returns:**
Dictionary containing:
- `risk_level`: The requested risk level
- `count`: Number of applicants at this risk level
- `applicants`: Array of matching applicant summaries with scores

**Example Response:**
```json
{
  "risk_level": "low",
  "count": 3,
  "applicants": [
    {
      "applicant_id": "APP001",
      "name": "Alice Johnson",
      "employment_risk": "low",
      "income_stability_score": 85,
      "credit_score": 750,
      "status": "approved"
    }
  ]
}
```

**Errors:**
- Raises `ValueError` if risk_level is not "low", "medium", or "high"

---

### 4. get_applications_requiring_action

Get all applications with incomplete documentation or documents pending verification.

**Parameters:** None

**Returns:**
Dictionary containing:
- `incomplete_count`: Total incomplete applications
- `missing_docs_count`: Applications with missing documents
- `applications`: Array of applications requiring action with missing fields and required actions

**Example Response:**
```json
{
  "incomplete_count": 3,
  "missing_docs_count": 3,
  "applications": [
    {
      "applicant_id": "APP002",
      "name": "Bob Smith",
      "completion_percentage": 85,
      "missing_fields": ["employment_verification_letter"],
      "required_actions": ["employment verification"],
      "status": "under_review"
    },
    {
      "applicant_id": "APP003",
      "name": "Carol Davis",
      "completion_percentage": 60,
      "missing_fields": [
        "recent_pay_stubs",
        "employment_verification_letter",
        "credit_authorization_form"
      ],
      "required_actions": [
        "income documentation",
        "employment verification",
        "credit authorization"
      ],
      "status": "submitted"
    }
  ]
}
```

## File Structure

```
mcp_servers/applicant_db.py          # Main MCP server implementation
test_applicant_db.py                 # Comprehensive test suite
demo_applicant_db.py                 # Interactive demonstration
```

## Running the Server

### As an MCP Server

```python
from mcp_servers.applicant_db import create_applicant_db_server
import asyncio

server = create_applicant_db_server()

async def main():
    async with server:
        print("ApplicantDB MCP Server started...")
        await asyncio.Event().wait()

asyncio.run(main())
```

### Running Tests

```bash
python test_applicant_db.py
```

Expected output:
```
======================================================================
ApplicantDB MCP Server - Test Suite
======================================================================

Testing Pydantic Models...
✓ IncomeStabilityScore model works
✓ EmploymentRisk enum works
✓ CreditHistorySummary model works
✓ ApplicationCompletenessFlags model works
✓ ApplicantProfile model works

Testing Mock Database...
✓ Database contains 5 applicants
✓ All applicants have required fields
[... more tests ...]

All Tests Passed! ✓
======================================================================
```

### Running Demo

```bash
python demo_applicant_db.py
```

This displays formatted demonstrations of all tools including:
- Full applicant profile retrieval
- Complete applicant listing
- Risk level filtering
- Pending applications requiring action
- Error handling examples

## Usage Examples

### Direct Function Import

```python
from mcp_servers.applicant_db import (
    get_applicant_profile,
    list_all_applicants,
    get_applicants_by_risk_level,
    get_applications_requiring_action
)

# Get a specific applicant
profile = get_applicant_profile("APP001")
print(f"Income Stability Score: {profile['income_stability']['score']}")
print(f"Employment Risk: {profile['employment_risk']}")

# List all applicants
all_apps = list_all_applicants()
print(f"Total applicants: {all_apps['total_count']}")

# Filter by risk
low_risk = get_applicants_by_risk_level("low")
print(f"Low risk applicants: {low_risk['count']}")

# Find incomplete applications
pending = get_applications_requiring_action()
print(f"Applications needing action: {pending['incomplete_count']}")
```

### Via MCP Server

When running as an MCP server, clients can call tools like:

```
{
  "method": "tools/call",
  "params": {
    "name": "get_applicant_profile",
    "arguments": {
      "applicant_id": "APP001"
    }
  }
}
```

## Dependencies

- `pydantic>=2.0.0` - Data validation and type safety
- `mcp>=1.0.0` - Model Context Protocol SDK
- `fastmcp>=0.1.0` - FastMCP framework

## Error Handling

The server provides comprehensive error messages:

```python
# Invalid applicant ID
try:
    get_applicant_profile("INVALID")
except ValueError as e:
    print(e)
    # Output: Applicant with ID 'INVALID' not found in database. Available IDs: [...]

# Invalid risk level
try:
    get_applicants_by_risk_level("invalid")
except ValueError as e:
    print(e)
    # Output: Invalid risk level 'invalid'. Must be one of: ['low', 'medium', 'high']
```

## Data Validation

All Pydantic models include field validation:

- **IncomeStabilityScore.score**: 0-100 integer
- **CreditHistorySummary.credit_score**: 300-850 integer
- **ApplicationCompletenessFlags.completion_percentage**: 0-100 integer
- **EmploymentRisk**: Enum restricted to low/medium/high

Invalid data raises `ValidationError` with detailed messages.

## Extensions

The server can be extended by:

1. **Adding new applicants** to `MOCK_APPLICANTS_DATABASE`
2. **Connecting to a real database** by modifying tool implementations
3. **Adding new assessment metrics** by extending Pydantic models
4. **Adding new tools** using the `@server.tool()` decorator

Example of extending with a new tool:

```python
@server.tool()
def get_applicants_above_credit_score(min_score: int) -> dict:
    """Filter applicants by minimum credit score."""
    # Implementation here
```

## Performance Considerations

- All operations use in-memory mock data (O(n) complexity)
- Pydantic validation adds minimal overhead
- MCP server supports concurrent requests
- For production, consider:
  - Database indexing on applicant_id
  - Caching frequently accessed profiles
  - Pagination for large result sets

## Testing

The test suite includes:
- Pydantic model validation tests
- Mock database integrity checks
- Tool functionality tests
- Error handling tests

All tests pass successfully, confirming type safety and correct behavior.

## License

MIT
