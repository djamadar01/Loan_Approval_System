# DecisionSynthesis MCP Server - Quick Start Guide

## Overview

DecisionSynthesis is an MCP server that synthesizes intelligent decisions based on risk scores using configurable decision logic rules. Perfect for loan approvals, vendor evaluations, transaction risk assessment, and compliance decisions.

## Files Included

```
decision_synthesis_mcp.py                    # Main MCP server
test_decision_synthesis.py                   # Test suite and scenarios
decision_synthesis_integration_example.py    # Real-world integration examples
decision_synthesis_mcp_config.json           # MCP configuration
DECISION_SYNTHESIS_README.md                 # Full documentation
DECISION_SYNTHESIS_QUICKSTART.md             # This file
```

## Installation

### Prerequisites
- Python 3.8+
- FastMCP library

```bash
pip install fastmcp pydantic
```

## Quick Start

### 1. Run Test Suite

View all test scenarios and verify the server logic:

```bash
python test_decision_synthesis.py
```

**Output:** Shows 8 test scenarios with different risk profiles and their decisions.

### 2. Run Integration Examples

See real-world usage with loan and vendor applications:

```bash
python decision_synthesis_integration_example.py
```

**Output:** Demonstrates loan and vendor decision workflows, generates JSON decision reports.

### 3. Start the MCP Server

Launch the server for use with Claude or other MCP clients:

```bash
python decision_synthesis_mcp.py
```

The server will start listening for MCP requests.

## Basic Usage

### Direct Python Usage

```python
from decision_synthesis_mcp import synthesize_decision

# Synthesize a decision
result = synthesize_decision(
    financial_risk=45,
    operational_risk=50,
    compliance_risk=55,
    reputational_risk=40,
    has_critical_issues=False,
    has_mitigating_factors=True,
    requires_escalation=False
)

# Access results
print(f"Decision: {result.classification}")  # "Review", "Approve", or "Reject"
print(f"Risk Score: {result.risk_score}")    # 0-100
print(f"Confidence: {result.confidence_level}")  # 0.0-1.0
print(f"Factors: {result.key_decision_factors}")
print(f"Explanation: {result.explanation}")
```

### Via MCP Configuration

Add to your Claude settings or MCP client config:

```json
{
  "mcpServers": {
    "decision-synthesis": {
      "command": "python",
      "args": ["/full/path/to/decision_synthesis_mcp.py"]
    }
  }
}
```

Then use in Claude:
- Ask Claude to use the "synthesize_decision" tool
- Claude will call the MCP server with your parameters
- Get back structured decision results

## Decision Classification Quick Reference

### APPROVE
- **Risk Score:** < 50
- **Critical Issues:** No
- **Confidence:** 90-95%
- **Use Cases:** Low-risk loans, established vendors, routine approvals

**Example:** Credit score 750, debt-to-income 35%, all certifications in place

### REVIEW
- **Risk Score:** 50-84
- **Reason:** Medium-high risk or requires escalation
- **Confidence:** 70-85%
- **Use Cases:** Moderate-risk applications needing expert evaluation

**Example:** New vendor with some certifications, mixed risk profile, requires escalation

### REJECT
- **Risk Score:** ≥ 85 OR critical unmitigable issues
- **Confidence:** 90-95%
- **Use Cases:** High-risk applications, unmitigable compliance issues

**Example:** Credit score 300, unemployment, debt-to-income 85%

## Risk Factor Inputs (0-100 scale)

| Factor | Description | Example Use |
|--------|-------------|-------------|
| **financial_risk** | Credit history, payment capacity, collateral | Loan applicants, investment decisions |
| **operational_risk** | Business stability, operations consistency | Vendor assessment, business continuity |
| **compliance_risk** | Regulatory adherence, certifications, audit history | Financial institutions, regulated industries |
| **reputational_risk** | Public perception, references, track record | Brand partnerships, high-profile deals |

## Common Scenarios

### Scenario 1: Auto-Approve (Low Risk)
```python
result = synthesize_decision(
    financial_risk=10,
    operational_risk=15,
    compliance_risk=5,
    reputational_risk=8,
    has_critical_issues=False,
    has_mitigating_factors=False,
    requires_escalation=False
)
# Result: APPROVE, Risk Score 9, Confidence 95%
```

### Scenario 2: Auto-Reject (Critical Issues)
```python
result = synthesize_decision(
    financial_risk=90,
    operational_risk=85,
    compliance_risk=95,
    reputational_risk=80,
    has_critical_issues=True,
    has_mitigating_factors=False,
    requires_escalation=False
)
# Result: REJECT, Risk Score 88, Confidence 95%
```

### Scenario 3: Requires Review (Medium Risk)
```python
result = synthesize_decision(
    financial_risk=60,
    operational_risk=55,
    compliance_risk=50,
    reputational_risk=45,
    has_critical_issues=False,
    has_mitigating_factors=True,
    requires_escalation=True
)
# Result: REVIEW, Risk Score 54, Confidence 75-85%
```

## Integration with Real Applications

### Loan Decision System

```python
from decision_synthesis_integration_example import LoanApplication, DecisionWorkflow

# Create loan application
app = LoanApplication(
    applicant_id="APP001",
    loan_amount=50000,
    applicant_credit_score=750,
    employment_status="employed",
    debt_to_income_ratio=0.35,
    collateral_value=60000
)

# Get decision
workflow = DecisionWorkflow()
result = workflow.evaluate_loan(app)
```

### Vendor Evaluation System

```python
from decision_synthesis_integration_example import VendorApplication, DecisionWorkflow

# Create vendor application
vendor = VendorApplication(
    vendor_id="VENDOR001",
    company_name="Acme Corp",
    years_established=10,
    financial_rating="AA",
    compliance_certifications=["ISO9001", "SOC2"],
    references=5,
    transaction_volume=1000000
)

# Get decision
workflow = DecisionWorkflow()
result = workflow.evaluate_vendor(vendor)
```

## Output Format

### JSON Response Example

```json
{
  "classification": "Review",
  "risk_score": 62,
  "confidence_level": 0.8,
  "key_decision_factors": [
    "Risk score 62 in medium-high range (50-84)",
    "Critical issues require review"
  ],
  "explanation": "Decision: Review\nOverall Risk Score: 62/100\nRisk Breakdown:\n  - Financial Risk: 60/100\n  - Operational Risk: 55/100\n  - Compliance Risk: 50/100\n  - Reputational Risk: 45/100\nStatus: Critical issues identified\nDecision Factors:\n  - Risk score 62 in medium-high range (50-84)\n  - Critical issues require review"
}
```

## Key Weights in Risk Calculation

The overall risk score uses weighted factors:

- **Financial Risk: 35%** - Highest impact on decision
- **Compliance Risk: 25%** - Regulatory importance
- **Operational Risk: 25%** - Business continuity
- **Reputational Risk: 15%** - Secondary factor

Example calculation:
```
Risk Score = (60 × 0.35) + (50 × 0.25) + (45 × 0.25) + (40 × 0.15)
           = 21 + 12.5 + 11.25 + 6
           = 50.75 → 51 (rounded)
```

## Troubleshooting

### Issue: Module not found
```bash
pip install fastmcp pydantic
```

### Issue: Risk scores out of range
Risk scores must be 0-100. FastMCP will validate:
```python
# ❌ Invalid
synthesize_decision(financial_risk=150)

# ✅ Valid
synthesize_decision(financial_risk=50)
```

### Issue: Server won't start
```bash
# Run with verbose output
python -u decision_synthesis_mcp.py

# Check Python version
python --version  # Should be 3.8+
```

## Advanced Usage

### Customizing Decision Rules

Edit `decision_synthesis_mcp.py` to modify classification logic:

```python
@staticmethod
def classify_decision(
    risk_score: int,
    has_critical_issues: bool = False,
    has_mitigating_factors: bool = False,
    requires_escalation: bool = False,
) -> tuple[ClassificationEnum, float, List[str]]:
    # Modify thresholds and logic here
    if risk_score >= 90:  # Changed from 85
        return ClassificationEnum.REJECT, 0.95, factors
    # ... rest of logic
```

### Adding New Risk Factors

Extend `calculate_risk_score()`:

```python
@staticmethod
def calculate_risk_score(
    financial_risk: float = 0,
    operational_risk: float = 0,
    compliance_risk: float = 0,
    reputational_risk: float = 0,
    security_risk: float = 0,  # New factor
) -> int:
    weights = {
        'financial': 0.30,
        'operational': 0.20,
        'compliance': 0.25,
        'reputational': 0.15,
        'security': 0.10,  # New weight
    }
    # Calculate with all factors
```

## Best Practices

1. **Calibrate Risk Scores:** Ensure your risk assessments use consistent 0-100 scaling
2. **Document Critical Issues:** Clearly identify what constitutes critical issues
3. **Track Mitigations:** Maintain audit trail of mitigating factors
4. **Review Confidence:** Use confidence scores to identify borderline cases
5. **Explain Decisions:** Always reference the explanation field for stakeholders

## Next Steps

1. Run `test_decision_synthesis.py` to understand the system
2. Explore `decision_synthesis_integration_example.py` for real-world patterns
3. Integrate with your decision-making workflow
4. Customize decision rules for your business logic
5. Monitor decision accuracy and adjust weights as needed

## Support

For detailed documentation, see: `DECISION_SYNTHESIS_README.md`

For questions about decision logic, review the classification rules in the README.

For implementation help, check `decision_synthesis_integration_example.py` for working examples.
