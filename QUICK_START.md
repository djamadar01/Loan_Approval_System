# FinancialRiskAgent - Quick Start Guide

## Installation

```bash
# Ensure Anthropic SDK is installed
pip install anthropic

# Verify installation
python -c "import anthropic; print('✓ Anthropic SDK installed')"
```

---

## Basic Usage (2 Minutes)

### Using Mock MCP (No Server Required)

```python
import asyncio
from financial_risk_agent import FinancialRiskAgent

async def main():
    # Create agent with default mock interface
    agent = FinancialRiskAgent()
    
    # Assess a single applicant
    assessment = await agent.assess_risk(
        applicant_id="APP_001",
        credit_score=750,
        monthly_gross_income=8000,
        monthly_debt_payments=1500,
        loan_amount=300000,
    )
    
    # Display results
    print(f"Applicant: {assessment.applicant_id}")
    print(f"DTI Ratio: {assessment.debt_to_income_ratio:.2%}")
    print(f"Overall Risk: {assessment.overall_risk_level.value}")
    print(f"Recommendation: {assessment.approval_recommendation.value}")

# Run the example
asyncio.run(main())
```

**Output**:
```
Applicant: APP_001
DTI Ratio: 18.75%
Overall Risk: low
Recommendation: APPROVE
```

---

## Using Real MCP Server

```python
import asyncio
from financial_risk_agent import FinancialRiskAgent, RealMCPToolInterface

async def main():
    # Create agent with real MCP interface
    mcp_interface = RealMCPToolInterface()
    agent = FinancialRiskAgent(mcp_interface=mcp_interface)
    
    # Same assessment as above
    assessment = await agent.assess_risk(
        applicant_id="APP_001",
        credit_score=750,
        monthly_gross_income=8000,
        monthly_debt_payments=1500,
        loan_amount=300000,
    )
    
    # Use results as before
    print(f"Assessment: {assessment.overall_risk_level.value}")

asyncio.run(main())
```

---

## Common Use Cases

### 1. Single Applicant Assessment

```python
# Simple assessment
assessment = await agent.assess_risk(
    applicant_id="John_Doe_001",
    credit_score=720,
    monthly_gross_income=6000,
    monthly_debt_payments=1200,
    loan_amount=200000,
)
```

### 2. Batch Processing

```python
# Process multiple applicants
applicants = [...]
result = await agent.batch_assess(applicants)
print(f"Approved: {result['summary']['approved']}")
```

### 3. DTI Capacity Planning

```python
result = await agent.get_dti_capacity(
    monthly_gross_income=6000,
    target_dti=0.36
)
print(f"Max monthly debt: ${result['max_debt_payment']}")
```

---

## Risk Levels

| Level | Meaning | Approval |
|-------|---------|----------|
| LOW | Safe profile | APPROVE ✓ |
| MEDIUM | Acceptable concerns | REVIEW ≈ |
| HIGH | Significant concerns | CONDITIONAL ? |
| CRITICAL | Serious red flags | DENY ✗ |

---

## Testing

```bash
python test_financial_risk_agent_updated.py
```

---

For complete documentation, see: `financial_risk_agent_updated.md`
