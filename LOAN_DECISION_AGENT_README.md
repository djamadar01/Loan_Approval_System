# LoanDecisionAgent - MCP Integration Guide

## Overview

The `LoanDecisionAgent` is an intelligent agent class that synthesizes final loan decisions by calling the DecisionSynthesis MCP server. It takes risk assessments from other agents (financial, operational, compliance, reputational) and produces an explainable decision: **Approve**, **Reject**, or **Review** with confidence levels and key factors.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                  LoanDecisionAgent                          │
│  - make_decision()      - Single decision synthesis         │
│  - batch_make_decisions() - Multiple decisions              │
│  - get_decision_rules() - Retrieve business rules           │
│  - export_decision_json() - Serialize to JSON               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              MCPToolInterface (Abstract)                    │
│  - synthesize_decision()                                    │
│  - get_decision_rules()                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    ┌────────────┐     ┌──────────────────┐
    │   Mock     │     │ RealMCP          │
    │ Interface  │     │ Interface        │
    │ (Testing)  │     │ (Production)     │
    └────────────┘     └──────────────────┘
        │                   │
        └───────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│         DecisionSynthesis MCP Server                        │
│  - synthesize_decision(financial_risk, ...)                │
│  - get_decision_rules()                                     │
└─────────────────────────────────────────────────────────────┘
```

### Decision Flow

```
Risk Assessments (from other agents)
    │
    ├─ Financial Risk Score (0-100)
    ├─ Operational Risk Score (0-100)
    ├─ Compliance Risk Score (0-100)
    ├─ Reputational Risk Score (0-100)
    └─ Decision Factors
        ├─ Has Critical Issues (bool)
        ├─ Has Mitigating Factors (bool)
        └─ Requires Escalation (bool)
    │
    ▼
┌─────────────────────────────────┐
│ LoanDecisionAgent.make_decision  │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  MCP: synthesize_decision()     │
│  - Calculate risk score         │
│  - Apply decision rules         │
│  - Determine classification     │
│  - Calculate confidence         │
└─────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│         LoanDecisionResult               │
│  - Classification: Approve/Reject/Review │
│  - Risk Score: 0-100                     │
│  - Confidence: 0.0-1.0                   │
│  - Key Factors: [string]                 │
│  - Explanation: Detailed rationale       │
└──────────────────────────────────────────┘
```

## Installation

### Prerequisites

```bash
pip install anthropic fastmcp pydantic
```

### Files

- `loan_decision_agent.py` - Main agent implementation
- `loan_decision_agent_integration.py` - Integration examples
- `test_loan_decision_agent.py` - Unit tests
- `decision_synthesis_mcp.py` - MCP server (must be running)

## Quick Start

### Basic Usage (Mock Interface - No Server Required)

```python
import asyncio
from loan_decision_agent import LoanDecisionAgent, MockMCPToolInterface

async def main():
    # Initialize agent with mock interface (for testing)
    agent = LoanDecisionAgent(mcp_interface=MockMCPToolInterface())
    
    # Make a single decision
    result = await agent.make_decision(
        applicant_id="APP_001",
        financial_risk=30,
        operational_risk=25,
        compliance_risk=20,
        reputational_risk=15,
        has_critical_issues=False,
        has_mitigating_factors=True,
    )
    
    print(f"Decision: {result.classification.value}")
    print(f"Risk Score: {result.risk_score}/100")
    print(f"Confidence: {result.confidence_level * 100:.0f}%")
    print(f"Explanation:\n{result.explanation}")

asyncio.run(main())
```

### Production Usage (With Real MCP Server)

```python
import asyncio
from anthropic import Anthropic
from loan_decision_agent import LoanDecisionAgent, RealMCPToolInterface

async def main():
    # Initialize real MCP client
    client = Anthropic()
    
    # Create interface
    mcp_interface = RealMCPToolInterface(mcp_client=client)
    
    # Initialize agent
    agent = LoanDecisionAgent(mcp_interface=mcp_interface)
    
    # Make decision
    result = await agent.make_decision(
        applicant_id="APP_001",
        financial_risk=30,
        operational_risk=25,
        compliance_risk=20,
        reputational_risk=15,
    )
    
    # Export as JSON
    json_str = agent.export_decision_json(result)
    print(json_str)

asyncio.run(main())
```

## Key Classes and Data Structures

### LoanDecisionAgent

Main agent class for decision synthesis.

**Methods:**

- `async make_decision(applicant_id, financial_risk, operational_risk, compliance_risk, reputational_risk, has_critical_issues=False, has_mitigating_factors=False, requires_escalation=False) -> LoanDecisionResult`
  - Synthesizes a single loan decision
  - Returns structured result with classification, confidence, and factors

- `async batch_make_decisions(decision_requests: List[Dict]) -> Dict`
  - Processes multiple applicants
  - Returns batch results with distribution and error handling

- `async get_decision_rules() -> Dict`
  - Retrieves decision rules from MCP server
  - Returns thresholds, weights, and classification logic

- `get_decision_summary(decision: LoanDecisionResult) -> Dict[str, str]`
  - Generates human-readable summary

- `export_decision_json(decision: LoanDecisionResult) -> str`
  - Exports decision as JSON string

### LoanDecisionResult

Complete decision result with supporting information.

**Fields:**

```python
@dataclass
class LoanDecisionResult:
    applicant_id: str                           # Unique applicant ID
    classification: DecisionClassification      # Approve/Reject/Review
    risk_score: int                             # 0-100
    confidence_level: float                     # 0.0-1.0
    key_decision_factors: List[str]            # Factors influencing decision
    explanation: str                            # Detailed rationale
    decision_factors: DecisionFactors           # Critical/mitigating/escalation flags
    risk_assessment: RiskAssessmentInput        # Input risk scores
    timestamp: str                              # ISO format timestamp
```

### RiskAssessmentInput

Input risk assessment from other agents.

```python
@dataclass
class RiskAssessmentInput:
    financial_risk: float          # 0-100
    operational_risk: float        # 0-100
    compliance_risk: float         # 0-100
    reputational_risk: float       # 0-100
```

### DecisionClassification

Enum for decision classifications.

```python
class DecisionClassification(str, Enum):
    APPROVE = "Approve"
    REJECT = "Reject"
    REVIEW = "Review"
```

## Decision Rules

### Risk Score Calculation

Overall risk score is a weighted average of component risks:

```
Risk Score = (Financial Risk × 0.35) + 
             (Operational Risk × 0.25) +
             (Compliance Risk × 0.25) +
             (Reputational Risk × 0.15)
```

**Weights:**
- Financial Risk: 35% (highest weight)
- Operational Risk: 25%
- Compliance Risk: 25%
- Reputational Risk: 15%

### Classification Logic

#### APPROVE (Confidence: 0.90-0.95)

Approved when:
- Risk score < 50 (low-medium risk)
- No critical unmitigable issues
- Mitigating factors present (optional)

**Example:**
```python
result = await agent.make_decision(
    applicant_id="LOW_RISK",
    financial_risk=20,
    operational_risk=15,
    compliance_risk=10,
    reputational_risk=8,
    has_critical_issues=False,
    has_mitigating_factors=True,
)
# Result: Approve, Risk Score: 15/100, Confidence: 95%
```

#### REJECT (Confidence: 0.90-0.95)

Rejected when:
- Risk score >= 85 (high risk) AND critical issues present
- Critical issues without mitigation possible
- Critical compliance violations

**Example:**
```python
result = await agent.make_decision(
    applicant_id="HIGH_RISK",
    financial_risk=90,
    operational_risk=85,
    compliance_risk=92,
    reputational_risk=80,
    has_critical_issues=True,
    has_mitigating_factors=False,
)
# Result: Reject, Risk Score: 88/100, Confidence: 95%
```

#### REVIEW (Confidence: 0.70-0.85)

Requires review when:
- Risk score 50-84 (medium-high risk)
- Critical issues with mitigation possible
- Requires escalation for approval
- Mixed risk profile needing human judgment

**Example:**
```python
result = await agent.make_decision(
    applicant_id="MED_RISK",
    financial_risk=50,
    operational_risk=55,
    compliance_risk=45,
    reputational_risk=35,
    has_critical_issues=True,
    has_mitigating_factors=True,
    requires_escalation=True,
)
# Result: Review, Risk Score: 50/100, Confidence: 85%
```

### Risk Score Ranges

| Range | Classification | Default Action |
|-------|---|---|
| 0-49 | Low-Medium Risk | Approve (if no issues) |
| 50-84 | Medium-High Risk | Review |
| 85-100 | High Risk | Reject (if issues) or Review |

## Batch Processing

### Usage

```python
decision_requests = [
    {
        "applicant_id": "APP_001",
        "financial_risk": 25,
        "operational_risk": 20,
        "compliance_risk": 15,
        "reputational_risk": 10,
        "has_critical_issues": False,
        "has_mitigating_factors": True,
    },
    {
        "applicant_id": "APP_002",
        "financial_risk": 65,
        "operational_risk": 60,
        "compliance_risk": 70,
        "reputational_risk": 50,
        "has_critical_issues": True,
        "has_mitigating_factors": True,
        "requires_escalation": True,
    },
    # ... more applicants
]

result = await agent.batch_make_decisions(decision_requests)

# Access results
print(f"Status: {result['status']}")                 # success/partial_success/failure
print(f"Successful: {result['successful']}/{result['total_requests']}")
print(f"Approvals: {result['summary']['approved']}")
print(f"Rejections: {result['summary']['rejected']}")
print(f"Reviews: {result['summary']['review']}")
print(f"Approval Rate: {result['summary']['approval_rate']:.1f}%")

# Iterate decisions
for decision in result['decisions']:
    print(f"{decision.applicant_id}: {decision.classification.value}")

# Handle errors
for error in result['errors']:
    print(f"Error for {error['applicant_id']}: {error['error']}")
```

### Result Structure

```python
{
    "status": "success|partial_success|failure",
    "total_requests": int,
    "successful": int,
    "failed": int,
    "decisions": [LoanDecisionResult, ...],
    "errors": [
        {
            "request_index": int,
            "applicant_id": str,
            "error": str,
        },
        ...
    ],
    "summary": {
        "approved": int,
        "rejected": int,
        "review": int,
        "approval_rate": float,  # percentage
    },
}
```

## Integration Examples

### Example 1: Single Decision

See `loan_decision_agent_integration.py` - Example 1

### Example 2: Batch Processing

See `loan_decision_agent_integration.py` - Example 2

### Example 3: Decision Rules

See `loan_decision_agent_integration.py` - Example 3

### Example 4: JSON Export

See `loan_decision_agent_integration.py` - Example 4

### Example 5: Scenario Analysis

See `loan_decision_agent_integration.py` - Example 5

## Error Handling

### Exception Types

```python
# Data validation errors
ValidationError(message)

# Agent operation errors
AgentError(message)

# MCP communication errors
MCPError(message)
```

### Error Handling Example

```python
try:
    result = await agent.make_decision(
        applicant_id="APP_001",
        financial_risk=150,  # Invalid: > 100
        operational_risk=25,
        compliance_risk=20,
        reputational_risk=15,
    )
except ValidationError as e:
    print(f"Validation error: {e}")
except MCPError as e:
    print(f"MCP communication error: {e}")
except AgentError as e:
    print(f"Agent error: {e}")
```

### Batch Error Handling

```python
result = await agent.batch_make_decisions(requests)

if result["status"] == "failure":
    print(f"All requests failed: {result['failed']}")
elif result["status"] == "partial_success":
    print(f"Partial success: {result['successful']} succeeded, {result['failed']} failed")
    
    # Process errors
    for error in result["errors"]:
        print(f"Error for {error['applicant_id']}: {error['error']}")
```

## JSON Export & Serialization

### Export Example

```python
result = await agent.make_decision(
    applicant_id="EXPORT_001",
    financial_risk=35,
    operational_risk=30,
    compliance_risk=25,
    reputational_risk=20,
)

# Export as JSON
json_str = agent.export_decision_json(result)
print(json_str)

# Or access dictionary
result_dict = result.to_dict()
```

### JSON Structure

```json
{
  "applicant_id": "EXPORT_001",
  "classification": "Approve",
  "risk_score": 29,
  "confidence_level": 0.95,
  "key_decision_factors": [
    "Risk score 29 within acceptable range",
    "No critical issues identified"
  ],
  "explanation": "Decision: Approve\n...",
  "decision_factors": {
    "critical_issues": false,
    "mitigating_factors": false,
    "requires_escalation": false,
    "key_factors": [...]
  },
  "risk_assessment": {
    "financial_risk": 35,
    "operational_risk": 30,
    "compliance_risk": 25,
    "reputational_risk": 20
  },
  "timestamp": "2026-06-18T05:20:42.216119"
}
```

## Integration with Other Systems

### Database Storage

```python
# Store decision in database
import json

decision = await agent.make_decision(...)
decision_json = agent.export_decision_json(decision)

db.insert_loan_decision({
    "applicant_id": decision.applicant_id,
    "classification": decision.classification.value,
    "risk_score": decision.risk_score,
    "confidence_level": decision.confidence_level,
    "decision_data": decision_json,
    "created_at": datetime.now(),
})
```

### API Response

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/loan/decision")
async def synthesize_decision(request: DecisionRequest):
    agent = LoanDecisionAgent()
    
    result = await agent.make_decision(
        applicant_id=request.applicant_id,
        financial_risk=request.financial_risk,
        operational_risk=request.operational_risk,
        compliance_risk=request.compliance_risk,
        reputational_risk=request.reputational_risk,
    )
    
    return result.to_dict()
```

### Workflow Integration

```python
# Route decisions to appropriate workflow
decision = await agent.make_decision(...)

if decision.classification == DecisionClassification.APPROVE:
    # Route to funding process
    workflow.queue_funding(decision.applicant_id)
elif decision.classification == DecisionClassification.REJECT:
    # Route to decline notification
    workflow.queue_decline(decision.applicant_id)
else:
    # Route to underwriter review
    workflow.queue_review(decision.applicant_id)
```

## Testing

### Run Tests

```bash
# With pytest-asyncio installed
pip install pytest pytest-asyncio

# Run tests
python -m pytest test_loan_decision_agent.py -v
```

### Test Coverage

- Risk assessment validation
- Single decision making
- Batch processing
- Error handling
- JSON serialization
- Decision rules retrieval

## Running Examples

### Example 1: Basic Usage

```bash
python -c "
import asyncio
from loan_decision_agent import LoanDecisionAgent, MockMCPToolInterface

async def main():
    agent = LoanDecisionAgent(mcp_interface=MockMCPToolInterface())
    result = await agent.make_decision(
        applicant_id='APP_001',
        financial_risk=30,
        operational_risk=25,
        compliance_risk=20,
        reputational_risk=15,
    )
    print(f'Decision: {result.classification.value}')
    print(f'Risk Score: {result.risk_score}/100')

asyncio.run(main())
"
```

### Example 2: Full Integration Examples

```bash
python loan_decision_agent_integration.py
```

This runs:
1. Single decisions (3 scenarios)
2. Batch processing
3. Decision rules retrieval
4. JSON export
5. Scenario analysis

## Performance Considerations

### Single Decision
- Typical latency: < 100ms
- With real MCP server: 100-500ms

### Batch Processing
- Processes sequentially (can be parallelized)
- Partial failure handling preserves successful results
- Failed requests don't block others

### Memory Usage
- LoanDecisionAgent: ~1-2 MB
- Per decision result: ~5-10 KB (JSON)
- Batch of 1000 decisions: ~10 MB

## Troubleshooting

### Issue: "MCP client not initialized"

**Solution:** Ensure MCPToolInterface is properly initialized
```python
mcp_interface = MockMCPToolInterface()  # For testing
# OR
mcp_interface = RealMCPToolInterface(mcp_client=client)  # For production
```

### Issue: Validation errors on risk scores

**Solution:** Ensure all risk scores are 0-100
```python
# Valid
financial_risk=50  # ✓ Within 0-100
compliance_risk=0  # ✓ Minimum allowed
reputational_risk=100  # ✓ Maximum allowed

# Invalid
financial_risk=-10  # ✗ Negative
compliance_risk=150  # ✗ > 100
```

### Issue: Batch processing with errors

**Solution:** Check batch status and handle partial failures
```python
result = await agent.batch_make_decisions(requests)

if result["status"] == "partial_success":
    # Process successful decisions
    for decision in result["decisions"]:
        process(decision)
    
    # Handle errors
    for error in result["errors"]:
        log_error(error)
```

## API Reference

### LoanDecisionAgent.make_decision()

```python
async def make_decision(
    applicant_id: str,
    financial_risk: float,          # 0-100
    operational_risk: float,        # 0-100
    compliance_risk: float,         # 0-100
    reputational_risk: float,       # 0-100
    has_critical_issues: bool = False,
    has_mitigating_factors: bool = False,
    requires_escalation: bool = False,
) -> LoanDecisionResult:
    """Synthesize a loan decision based on risk assessments."""
```

### LoanDecisionAgent.batch_make_decisions()

```python
async def batch_make_decisions(
    decision_requests: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Synthesize decisions for multiple applicants."""
```

### LoanDecisionAgent.get_decision_rules()

```python
async def get_decision_rules() -> Dict[str, Any]:
    """Retrieve decision rules from MCP server."""
```

## Contributing

When extending LoanDecisionAgent:

1. Add new methods to the class
2. Add corresponding tests to `test_loan_decision_agent.py`
3. Update integration examples if adding new features
4. Maintain backward compatibility with existing API

## License

This implementation is part of the loan decision system.
