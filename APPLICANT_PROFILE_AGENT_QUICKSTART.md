# ApplicantProfileAgent - Quick Start Guide

Get up and running with ApplicantProfileAgent in 5 minutes.

## Installation

1. Ensure you have the required dependencies:
```bash
pip install pydantic mcp fastmcp anthropic
```

2. Files included:
- `applicant_profile_agent.py` - Main agent implementation
- `test_applicant_profile_agent.py` - Comprehensive test suite
- `mcp_servers/applicant_db.py` - ApplicantDB MCP server

## Basic Usage

### 1. Initialize the Agent

```python
from applicant_profile_agent import ApplicantProfileAgent

# Create agent instance
agent = ApplicantProfileAgent(verbose=True)
```

### 2. Fetch a Single Applicant Profile

```python
# Fetch profile by applicant ID
profile = agent.fetch_applicant_profile("APP001")

# Access profile data
print(f"Name: {profile.name}")
print(f"Email: {profile.email}")
print(f"Risk Level: {profile.employment_risk.risk_level}")
print(f"Credit Score: {profile.credit_history.credit_score}")
print(f"Overall Risk Score: {profile.overall_risk_score}")
print(f"Recommendation: {profile.recommendation}")
```

### 3. Get All Applicants

```python
# List all applicants
applicants = agent.fetch_all_applicants()

for app in applicants:
    print(f"{app['applicant_id']}: {app['name']} ({app['status']})")
```

### 4. Filter by Risk Level

```python
# Get low-risk applicants
low_risk = agent.fetch_applicants_by_risk("low")
print(f"Low-risk applicants: {len(low_risk)}")

for app in low_risk:
    print(f"  {app['name']}: Income {app['income_stability_score']}, Credit {app['credit_score']}")
```

### 5. Find Applications Requiring Action

```python
# Get incomplete applications
pending = agent.fetch_applications_requiring_action()

print(f"Incomplete applications: {pending['incomplete_count']}")
for app in pending["applications"]:
    print(f"  {app['name']}: {app['completion_percentage']}% complete")
    print(f"  Missing: {', '.join(app['missing_fields'])}")
```

### 6. Analyze Portfolio Risk Distribution

```python
# Analyze entire portfolio
portfolio = agent.analyze_risk_portfolio()

print(f"Total Applicants: {portfolio['total']}")
print(f"\nRisk Distribution:")
for risk_level in ["low", "medium", "high"]:
    pct = portfolio["distribution"][risk_level]
    count = portfolio[risk_level]["count"]
    print(f"  {risk_level.upper()}: {count} applicants ({pct}%)")
```

## Common Scenarios

### Scenario 1: Loan Decision on Specific Applicant

```python
agent = ApplicantProfileAgent()

# Get applicant profile
profile = agent.fetch_applicant_profile("APP003")

# Make decision based on recommendation
if "APPROVE" in profile.recommendation:
    print(f"Decision: APPROVE {profile.name}")
    print(f"Risk Score: {profile.overall_risk_score:.1f}/100")
elif "CONDITIONAL" in profile.recommendation:
    print(f"Decision: REVIEW {profile.name}")
    print(f"Pending: {', '.join(profile.missing_fields)}")
else:
    print(f"Decision: DENY {profile.name}")
    print(f"Reason: {profile.recommendation}")
```

### Scenario 2: Portfolio Risk Assessment

```python
agent = ApplicantProfileAgent()

# Analyze each risk segment
for risk_level in ["low", "medium", "high"]:
    applicants = agent.fetch_applicants_by_risk(risk_level)
    
    if applicants:
        avg_credit = sum(a["credit_score"] for a in applicants) / len(applicants)
        print(f"\n{risk_level.upper()} RISK ({len(applicants)} applicants)")
        print(f"  Avg Credit Score: {avg_credit:.0f}")
```

### Scenario 3: Workflow Management

```python
agent = ApplicantProfileAgent()

# Identify high-priority work items
pending = agent.fetch_applications_requiring_action()

print("HIGH PRIORITY (< 70% complete):")
for app in pending["applications"]:
    if app["completion_percentage"] < 70:
        print(f"  {app['name']}: {len(app['missing_fields'])} documents needed")

print("\nMEDIUM PRIORITY (70-90% complete):")
for app in pending["applications"]:
    if 70 <= app["completion_percentage"] < 90:
        print(f"  {app['name']}: {len(app['missing_fields'])} documents needed")
```

## Data Models Reference

### IncomeStabilityAssessment
```python
profile.income_stability.score          # 0-100
profile.income_stability.trend          # "increasing", "stable", "decreasing"
profile.income_stability.volatility     # "low", "moderate", "high"
profile.income_stability.average_monthly # Float (dollars)
profile.income_stability.risk_indicator # "healthy", "caution", "critical"
```

### EmploymentRiskAssessment
```python
profile.employment_risk.risk_level      # "low", "medium", "high"
profile.employment_risk.rationale       # String explanation
```

### CreditHistorySummary
```python
profile.credit_history.credit_score          # 300-850
profile.credit_history.accounts_on_time      # Integer
profile.credit_history.accounts_late         # Integer
profile.credit_history.total_debt            # Float (dollars)
profile.credit_history.debt_to_income_ratio  # Float (percentage)
profile.credit_history.delinquencies         # Integer
profile.credit_history.credit_rating         # "excellent", "good", "fair", "poor"
```

### ApplicantProfileSummary
```python
profile.applicant_id                    # String
profile.name                            # String
profile.email                           # String
profile.phone                           # String
profile.income_stability                # IncomeStabilityAssessment
profile.employment_risk                 # EmploymentRiskAssessment
profile.credit_history                  # CreditHistorySummary
profile.application_status              # String
profile.application_date                # String (YYYY-MM-DD)
profile.completion_percentage           # 0-100
profile.missing_fields                  # List of strings
profile.overall_risk_score              # 0-100 (float)
profile.recommendation                  # String (decision + rationale)
```

## Output Formats

### JSON Output
```python
profile = agent.fetch_applicant_profile("APP001")
json_str = profile.to_json()
print(json_str)  # Pretty-printed JSON
```

### Dictionary Output
```python
profile = agent.fetch_applicant_profile("APP001")
dict_data = profile.to_dict()
print(dict_data["income_stability"]["score"])  # Access nested data
```

## Error Handling

Always handle potential errors:

```python
from applicant_profile_agent import AgentError

try:
    profile = agent.fetch_applicant_profile("INVALID_ID")
except AgentError as e:
    print(f"Error: {e}")
    # Handle gracefully
```

## Testing

Run the demonstration:
```bash
python applicant_profile_agent.py
```

Run the test suite:
```bash
python test_applicant_profile_agent.py
```

## Sample Data

The agent comes with 5 mock applicants:

| ID | Name | Risk | Income | Credit | Status |
|----|------|------|--------|--------|--------|
| APP001 | Alice Johnson | Low | 85 | 750 | Approved |
| APP002 | Bob Smith | Medium | 62 | 680 | Under Review |
| APP003 | Carol Davis | High | 45 | 580 | Submitted |
| APP004 | David Martinez | Low | 92 | 800 | Approved |
| APP005 | Emily Wilson | Low | 71 | 720 | Under Review |

## Risk Score Interpretation

| Score | Interpretation | Action |
|-------|-----------------|--------|
| 80-100 | Excellent | APPROVE |
| 60-79 | Good | CONDITIONAL |
| 40-59 | Fair | REVIEW |
| 0-39 | Poor | DENY |

## Next Steps

1. **Read Full Documentation:** See `APPLICANT_PROFILE_AGENT_README.md`
2. **Review Test Suite:** See `test_applicant_profile_agent.py`
3. **Integrate with Claude API:** Use with Claude for intelligent analysis
4. **Customize Risk Rules:** Modify risk calculation formulas
5. **Extend Data Models:** Add custom assessment fields

## API Quick Reference

```python
# Fetch single profile
profile = agent.fetch_applicant_profile(applicant_id: str) -> ApplicantProfileSummary

# List all applicants
applicants = agent.fetch_all_applicants() -> List[Dict]

# Filter by risk level
applicants = agent.fetch_applicants_by_risk(risk_level: str) -> List[Dict]
# risk_level: "low", "medium", or "high"

# Get applications requiring action
pending = agent.fetch_applications_requiring_action() -> Dict

# Analyze portfolio
portfolio = agent.analyze_risk_portfolio() -> Dict
```

## Troubleshooting

**Q: AgentError - Applicant not found**
A: Use valid applicant ID from fetch_all_applicants()

**Q: AgentError - Invalid risk level**
A: Use "low", "medium", or "high" (lowercase)

**Q: ValidationError**
A: Check that MCP server is running and accessible

**Q: Empty results**
A: Check that mock database is populated and accessible

## Support

For issues or questions:
1. Check the comprehensive README: `APPLICANT_PROFILE_AGENT_README.md`
2. Review test cases: `test_applicant_profile_agent.py`
3. Run demonstration: `python applicant_profile_agent.py`
4. Check error messages for specific guidance
