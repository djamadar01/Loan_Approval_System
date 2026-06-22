# FinancialRiskAgent - Updated Implementation

## Overview

The **FinancialRiskAgent** has been updated to provide comprehensive financial risk assessment by integrating with the RiskRulesDB MCP server through a structured, multi-step process.

## Key Features

### 1. MCP Client Initialization
The agent now includes a `RealMCPToolInterface` class that:
- Initializes the Anthropic SDK client for MCP communication
- Configures connection to the RiskRulesDB MCP server
- Handles authentication and transport protocols (stdio, HTTP, etc.)
- Provides error handling and connection management

### 2. Three Specific MCP Tool Calls

#### Tool 1: `calculate_debt_to_income`
**Purpose**: Calculate Debt-to-Income ratio with risk classification

**Parameters**:
- `monthly_gross_income` (float): Gross monthly income in dollars
- `monthly_debt_payments` (float): Current monthly debt payments in dollars

**Returns**:
```json
{
  "status": "success",
  "debt_to_income": {
    "monthly_debt_payments": float,
    "monthly_gross_income": float,
    "debt_to_income_ratio": float (0-1),
    "risk_level": string ("low", "medium", "high", "critical"),
    "meets_lending_standards": boolean
  }
}
```

**Risk Thresholds**:
- ≤ 0.20: Excellent (Low Risk)
- ≤ 0.36: Good (Low Risk)
- ≤ 0.43: Acceptable (Medium Risk)
- ≤ 0.50: High (High Risk)
- > 0.50: Critical (Critical Risk)

---

#### Tool 2: `assess_credit_score_risk`
**Purpose**: Evaluate credit risk based on credit score

**Parameters**:
- `credit_score` (int): Credit score value (300-850)

**Returns**:
```json
{
  "status": "success",
  "credit_risk": {
    "credit_score": int,
    "risk_level": string ("excellent", "good", "fair", "poor", "very_poor"),
    "risk_percentage": float (default probability %),
    "percentile": float (0-100)
  }
}
```

**Risk Categories**:
- 800+: Excellent (1.0% default rate)
- 750-799: Good (2.0% default rate)
- 670-749: Fair (5.0% default rate)
- 580-669: Poor (15.0% default rate)
- <580: Very Poor (30.0% default rate)

---

#### Tool 3: `detect_financial_anomalies`
**Purpose**: Identify suspicious patterns and red flags in financial profile

**Parameters**:
- `credit_score` (int): Credit score (300-850)
- `monthly_income` (float): Monthly income in dollars
- `monthly_debt_payments` (float): Monthly debt payments in dollars
- `loan_amount` (float): Requested loan amount in dollars
- `previous_dti` (Optional[float]): Previous DTI for spike detection

**Returns**:
```json
{
  "status": "success",
  "anomalies": {
    "anomalies_detected": [
      {
        "flag_type": string,
        "severity": string ("low", "medium", "high", "critical"),
        "message": string,
        "threshold": float,
        "actual_value": float
      }
    ],
    "risk_score": float,
    "summary": string
  }
}
```

**Anomaly Types**:
- `EXTREME_DTI`: DTI > 0.60
- `LOW_INCOME`: Annual income < $20,000
- `VERY_LOW_CREDIT_SCORE`: Credit score < 500
- `DTI_SPIKE`: DTI increased > 15% from previous period
- `LARGE_LOAN_AMOUNT`: Loan > 60x monthly income

---

### 3. Business Rules Application

The agent applies comprehensive business rules after calling the MCP tools:

```python
# DTI-based decision
if dti > 0.60:
    overall_risk = "CRITICAL"
    
# Credit-based decision
if credit_score < 500:
    overall_risk = "CRITICAL"

# Anomaly count consideration
# Each anomaly adds 0.25 to risk score

# Overall approval logic
if dti > 0.6 or credit_score < 500 or anomalies > threshold:
    recommendation = "DENY"
elif dti > 0.36:
    recommendation = "CONDITIONAL"
else:
    recommendation = "APPROVE"
```

### 4. Risk Level Classification

The agent produces four-tier risk classifications:

| Risk Level | Characteristics | Action |
|------------|-----------------|--------|
| **LOW** | DTI ≤ 0.36, Good+ credit, No anomalies | APPROVE |
| **MEDIUM** | DTI 0.36-0.43, Fair credit, Few anomalies | REVIEW |
| **HIGH** | DTI 0.43-0.50, Poor credit, Multiple anomalies | CONDITIONAL |
| **CRITICAL** | DTI > 0.50, Very Poor credit, Critical anomalies | DENY |

---

## Implementation Details

### RealMCPToolInterface Class

Extends `MCPToolInterface` with production-ready MCP integration:

```python
class RealMCPToolInterface(MCPToolInterface):
    def __init__(self, mcp_server_path: Optional[str] = None):
        """Initialize MCP client for RiskRulesDB server."""
        
    async def calculate_debt_to_income(
        self, 
        monthly_gross_income: float,
        monthly_debt_payments: float
    ) -> Dict[str, Any]:
        """Call calculate_debt_to_income MCP tool"""
        
    async def assess_credit_score_risk(
        self,
        credit_score: int
    ) -> Dict[str, Any]:
        """Call assess_credit_score_risk MCP tool"""
        
    async def detect_financial_anomalies(
        self,
        credit_score: int,
        monthly_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None
    ) -> Dict[str, Any]:
        """Call detect_financial_anomalies MCP tool"""
```

### Enhanced assess_risk() Method

The `assess_risk()` method now executes a 4-step process:

```python
# Step 1: Calculate DTI
dti_result = await self.mcp_interface.calculate_debt_to_income(...)

# Step 2: Assess credit score
credit_result = await self.mcp_interface.assess_credit_score_risk(...)

# Step 3: Detect anomalies
anomaly_result = await self.mcp_interface.detect_financial_anomalies(...)

# Step 4: Comprehensive analysis (combines all results)
analysis_result = await self.mcp_interface.analyze_financial_risk(...)

# Apply business rules and generate RiskAssessment
```

---

## Usage Examples

### Example 1: Single Applicant Assessment

```python
import asyncio
from financial_risk_agent import FinancialRiskAgent, RealMCPToolInterface

async def main():
    # Initialize agent with real MCP interface
    mcp_interface = RealMCPToolInterface()
    agent = FinancialRiskAgent(mcp_interface=mcp_interface)
    
    # Perform assessment
    assessment = await agent.assess_risk(
        applicant_id="APP_PRO_001",
        credit_score=760,
        monthly_gross_income=8000,
        monthly_debt_payments=1500,
        loan_amount=300000,
    )
    
    # Use results
    print(f"DTI Risk Level: {assessment.dti_risk_level}")
    print(f"Credit Risk: {assessment.credit_risk_level}")
    print(f"Overall Risk: {assessment.overall_risk_level}")
    print(f"Recommendation: {assessment.approval_recommendation}")
    print(f"Reasoning:\n{assessment.reasoning}")

asyncio.run(main())
```

### Example 2: Batch Processing

```python
applicants = [
    {
        "credit_score": 800,
        "monthly_gross_income": 10000,
        "monthly_debt_payments": 1000,
        "loan_amount": 400000,
    },
    # ... more applicants
]

result = await agent.batch_assess(applicants)
print(f"Approved: {result['summary']['approved']}")
print(f"Conditional: {result['summary']['conditional']}")
print(f"Denied: {result['summary']['denied']}")
```

### Example 3: DTI Capacity Planning

```python
# Find maximum debt capacity
result = await agent.get_dti_capacity(
    monthly_gross_income=6000,
    target_dti=0.36  # 36% DTI threshold
)
print(f"Max monthly debt: ${result['max_debt_payment']}")
```

### Example 4: Business Rules Review

```python
# Retrieve configured thresholds
thresholds = await agent.get_thresholds()
print(thresholds['dti_thresholds'])
print(thresholds['credit_score_thresholds'])
print(thresholds['anomaly_detection_triggers'])
```

---

## Error Handling

The agent includes comprehensive error handling:

```python
try:
    assessment = await agent.assess_risk(...)
except ValueError as e:
    print(f"Input validation error: {e}")
except Exception as e:
    print(f"Risk assessment failed: {e}")
```

All MCP tool calls return status indicators:
- `"status": "success"` - Tool executed successfully
- `"status": "error"` - Tool failed with error message in `"error"` field

---

## Testing

### Mock Interface (for testing without MCP server)

```python
from financial_risk_agent import FinancialRiskAgent, MockMCPToolInterface

# Default - uses mock interface
agent = FinancialRiskAgent()

# Explicitly use mock
agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())
```

### Real Interface (with MCP server)

```python
from financial_risk_agent import FinancialRiskAgent, RealMCPToolInterface

# Requires RiskRulesDB MCP server running
agent = FinancialRiskAgent(mcp_interface=RealMCPToolInterface())
```

---

## Data Structures

### RiskAssessment Result

```python
@dataclass
class RiskAssessment:
    applicant_id: str
    debt_to_income_ratio: float
    dti_risk_level: RiskLevel  # LOW, MEDIUM, HIGH, CRITICAL
    dti_recommendation: str
    credit_score: int
    credit_risk_level: str
    credit_risk_percentage: float
    credit_recommendation: str
    loan_amount: float
    loan_risk_level: RiskLevel
    loan_recommendation: str
    anomalies: List[Dict[str, Any]]
    overall_risk_level: RiskLevel
    approval_recommendation: ApprovalRecommendation  # APPROVE, CONDITIONAL, DENY
    reasoning: str  # Detailed explanation
    detailed_analysis: Dict[str, Any]
```

---

## Integration with External Systems

The agent provides multiple integration points:

### 1. JSON Export
```python
json_str = agent.export_assessment_json(assessment)
# Store in database, send via API, etc.
```

### 2. Summary Generation
```python
summary = agent.get_assessment_summary(assessment)
# Use for dashboards, reports, etc.
```

### 3. Logging Access
```python
logs = agent.logger  # List of debug messages
# Useful for audit trails and debugging
```

---

## Configuration

### RiskRulesDB MCP Server Configuration

The RealMCPToolInterface can be configured with:

```python
# Custom server path
mcp_interface = RealMCPToolInterface(
    mcp_server_path="/custom/path/to/riskrulesdb_mcp_server.py"
)

# Custom Anthropic client
import anthropic
client = anthropic.Anthropic(api_key="your-key")
# Configure MCP transport in the client
```

---

## Performance Considerations

1. **Tool Call Optimization**: The agent batches related tool calls where possible
2. **Caching**: Consider caching threshold and configuration results
3. **Async Operations**: All tool calls are async for non-blocking I/O
4. **Batch Processing**: Use `batch_assess()` for multiple applicants to reduce overhead

---

## Future Enhancements

- [ ] MCP transaction caching for repeated assessments
- [ ] Configurable business rule updates via API
- [ ] Real-time threshold adjustments
- [ ] Predictive risk scoring with machine learning
- [ ] Enhanced anomaly detection algorithms
- [ ] Integration with external credit reporting services

---

## Support

For issues, questions, or enhancements, refer to:
- RiskRulesDB MCP Server documentation
- Anthropic SDK documentation
- MCP Protocol specification
