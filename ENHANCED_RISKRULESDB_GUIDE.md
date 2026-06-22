# Enhanced RiskRulesDB MCP Server - Complete Implementation Guide

## Overview

The Enhanced RiskRulesDB MCP Server is a production-grade financial risk analysis engine with 5 advanced features designed for enterprise lending and compliance needs.

**Version**: 2.0.0  
**Status**: Production Ready  
**Framework**: FastMCP (Model Context Protocol)

---

## Features Overview

### 1. Configurable Risk Thresholds API

Dynamic threshold management without code changes.

**Tools:**
- `configure_risk_threshold()` - Update existing thresholds
- `add_custom_risk_threshold()` - Create new metric thresholds
- `get_all_risk_thresholds()` - Retrieve all configured thresholds

**Use Cases:**
- Adapt to regulatory requirement changes
- A/B test different risk policies
- Support multiple loan products with different standards
- Emergency threshold adjustments during market volatility

**Example:**
```python
# Update DTI threshold for new regulatory requirement
configure_risk_threshold(
    metric="debt_to_income_ratio",
    low_threshold=0.0,
    moderate_threshold=0.40,      # Changed from 0.36
    high_threshold=0.55,           # Changed from 0.50
    critical_threshold=0.80        # Changed from 0.75
)

# Add custom macro indicator
add_custom_risk_threshold(
    metric="unemployment_rate",
    name="Unemployment Risk",
    low_threshold=0.02,
    moderate_threshold=0.05,
    high_threshold=0.08,
    critical_threshold=0.12,
    unit="percentage",
    description="Local unemployment impact on default risk"
)
```

---

### 2. Historical Risk Trending

Time-series risk analysis with trend detection and cohort statistics.

**Tools:**
- `record_risk_assessment()` - Store assessment in history
- `get_risk_history()` - Retrieve historical data
- `calculate_risk_trend()` - Analyze trend direction
- `get_cohort_statistics()` - Compare cohorts

**Use Cases:**
- Early warning system for deteriorating profiles
- Portfolio risk composition analysis
- Validate policy change effectiveness
- Benchmark against industry cohorts
- Identify seasonal or economic patterns

**Example:**
```python
# Record assessment
record_risk_assessment(
    entity_id="applicant_12345",
    risk_score=0.42,
    risk_level="moderate",
    dti_ratio=0.38,
    credit_score=690,
    loan_amount=150000,
    monthly_income=5000,
    anomaly_count=1,
    notes="Minor spending spike detected"
)

# Analyze trends
trend = calculate_risk_trend(
    entity_id="applicant_12345",
    period_days=30
)
# Returns: {
#   "trend_direction": "deteriorating",
#   "risk_score_trend": {
#     "initial": 0.35,
#     "final": 0.42,
#     "change": 0.07
#   }
# }

# Cohort analysis
cohort_stats = get_cohort_statistics(
    risk_level="critical",
    period_days=30
)
# Returns: Statistics on all critical-risk entities
```

---

### 3. Anomaly Detection with ML (Simulated)

Ensemble machine learning approach for pattern recognition.

**Methods:**
- **Z-score Analysis**: Statistical deviation detection
- **Isolation Forest (Simulated)**: Multivariate anomaly detection
- **Spending Pattern Analysis**: Spike and variance detection
- **Velocity Detection**: High-volume transaction detection

**Anomaly Types:**
- `SPENDING_SPIKE` - Unusual spending increase
- `UNUSUAL_PATTERN` - Deviation from historical behavior
- `HIGH_VELOCITY` - Rapid/excessive transactions
- `ACCOUNT_AGE` - New account behavior
- `GEOGRAPHIC_ANOMALY` - Unusual location activity
- `INCOME_VARIANCE` - Income level changes

**Tools:**
- `detect_financial_anomalies()` - Run ML detection

**Example:**
```python
result = detect_financial_anomalies(
    entity_id="applicant_12345",
    dti_ratio=0.68,
    credit_score=485,
    loan_amount=500000,
    monthly_income=4500,
    spending_pattern=[2000, 2100, 2150, 5800]  # Spike!
)
# Returns: {
#   "anomalies": [
#     {
#       "type": "spending_spike",
#       "severity": "high",
#       "message": "Recent spending spike: 2.7x average",
#       "score": 0.6
#     }
#   ],
#   "overall_risk_score": 0.72,
#   "ml_model": "ensemble_iso_forest_zscore",
#   "confidence": 0.92,
#   "recommendations": [...]
# }
```

**ML Model Details:**
- **Type**: Ensemble (Isolation Forest + Z-score)
- **Approach**: Simulated, ready for real ML integration
- **Confidence Range**: 0.50 - 0.95
- **Training**: Historical data optional, statistical fallback available

---

### 4. Regulatory Rule Versioning

Version control for compliance rules with audit trail.

**Default Rules:**
- **ECOA** (v2.0) - Equal Credit Opportunity Act
- **FCRA** (v1.5) - Fair Credit Reporting Act
- **GLBA** (v1.0) - Gramm-Leach-Bliley Act

**Tools:**
- `get_active_regulatory_rules()` - View all active rules
- `create_regulatory_rule_version()` - Create new version
- `validate_compliance()` - Check against rules

**Use Cases:**
- Track regulatory rule evolution
- Maintain complete audit trail
- Support gradual rule rollout
- Archive outdated rules
- Validate decisions against versioned rules

**Example:**
```python
# Get all active rules
rules = get_active_regulatory_rules()
# Returns: All rules organized by type

# Create new rule version
create_regulatory_rule_version(
    rule_id="ECOA",
    name="Equal Credit Opportunity Act",
    description="Prohibits discrimination in credit decisions",
    rule_type="ECOA",
    version="3.0",
    content={
        "prohibited_criteria": ["age", "race", "color", "religion", "national_origin"],
        "new_requirement": "Algorithmic bias testing",
        "effective_date": "2025-01-01"
    }
)

# Validate compliance
compliance = validate_compliance(
    entity_data={
        "entity_id": "applicant_12345",
        "dti_ratio": 0.38,
        "credit_score": 690
    },
    rule_types=["ECOA", "FCRA"]
)
# Returns: {
#   "compliant": True,
#   "violations": []
# }
```

---

### 5. Custom Rule Engine Extensibility

Plugin-style rule framework for business logic.

**Rule Types:**
- **Threshold**: Simple condition-based rules
- **Complex**: Multi-condition logic with AND/OR
- **ML-based**: Machine learning rule basis (extensible)

**Tools:**
- `create_custom_threshold_rule()` - Create threshold rule
- `create_custom_complex_rule()` - Create complex rule
- `evaluate_custom_rules()` - Run rules against data
- `get_custom_rules()` - List all rules

**Use Cases:**
- Implement product-specific lending rules
- Enable rapid rule changes without deployment
- Support business team self-service rule creation
- A/B test rule variations
- Complex multi-criteria decision logic

**Example:**
```python
# Create threshold rule
create_custom_threshold_rule(
    rule_id="max_debt_to_income",
    name="Maximum DTI for Personal Loans",
    description="Rejects if DTI exceeds 43%",
    metric="dti_ratio",
    threshold=0.43,
    operator="<="
)

# Create complex rule
create_custom_complex_rule(
    rule_id="high_risk_profile",
    name="High Risk Profile",
    description="Flags profile if both conditions true",
    conditions=[
        {
            "metric": "dti_ratio",
            "operator": ">",
            "value": 0.50
        },
        {
            "metric": "credit_score",
            "operator": "<",
            "value": 600
        }
    ],
    logic="AND"
)

# Evaluate rules
results = evaluate_custom_rules(
    data={
        "dti_ratio": 0.55,
        "credit_score": 580,
        "loan_amount": 100000
    },
    rule_ids=["max_debt_to_income", "high_risk_profile"]
)
# Returns: Pass/fail results with compliance score
```

---

## Comprehensive Risk Analysis Tool

Single tool orchestrating all 5 features:

```python
result = comprehensive_risk_analysis(
    entity_id="applicant_98765",
    dti_ratio=0.42,
    credit_score=675,
    loan_amount=200000,
    monthly_income=5200,
    spending_pattern=[3200, 3400, 3600, 4800]
)
```

**Analysis Steps:**
1. Evaluate against configurable thresholds
2. Record in history and calculate trends
3. Run ML anomaly detection ensemble
4. Validate regulatory compliance
5. Evaluate custom business rules
6. Synthesize into final recommendation

**Output:**
```json
{
  "status": "success",
  "entity_id": "applicant_98765",
  "analyses": {
    "threshold_evaluation": {...},
    "anomaly_detection": {...},
    "historical_trend": {...},
    "regulatory_compliance": {...},
    "custom_rules": {...}
  },
  "final_assessment": {
    "overall_risk_score": 0.38,
    "overall_risk_level": "moderate",
    "final_recommendation": "APPROVE WITH MONITORING"
  }
}
```

---

## Real-World Integration Scenarios

### Scenario 1: Policy Change Rollout

Rolling out stricter lending standards:

```
1. Create new rule version
   → configure_risk_threshold() for new thresholds
   
2. A/B test on subset
   → evaluate_custom_rules() on test group
   
3. Monitor impact
   → get_cohort_statistics('high') for control group
   
4. Gradual rollout
   → Archive old rule versions, activate new ones
   
5. Audit trail
   → calculate_risk_trend() to measure impact
```

### Scenario 2: Portfolio Risk Monitoring

Early warning system for deteriorating portfolios:

```
1. Record all assessments
   → record_risk_assessment() after every decision
   
2. Daily cohort analysis
   → get_cohort_statistics('high') for critical portfolio
   
3. Trend detection
   → calculate_risk_trend() on high-risk segment
   
4. Alert on deterioration
   → If trend_direction = 'deteriorating', escalate
   
5. Manual review
   → Underwriter reviews full context
```

### Scenario 3: Fraud Detection

Detecting suspicious account activity:

```
1. Monitor velocity
   → detect_financial_anomalies() flags HIGH_VELOCITY
   
2. Pattern analysis
   → ML ensemble detects SPENDING_SPIKE or UNUSUAL_PATTERN
   
3. Rule triggers
   → Custom velocity rule fires (loan > 50x monthly income)
   
4. Complex logic
   → Multiple indicators combine for confidence
   
5. Investigation
   → Fraud team reviews with full context
```

### Scenario 4: Regulatory Audit

Ensuring ECOA/FCRA compliance:

```
1. Get active rules
   → get_active_regulatory_rules() shows v3.0 in effect
   
2. Validate sample
   → validate_compliance() checks decisions against rules
   
3. Historical audit
   → Review version history showing all changes
   
4. Document compliance
   → Store version used for each decision
   
5. Report findings
   → Demonstrate compliance with version history
```

---

## Architecture & Design

### Component Structure

```
RiskRulesDB-Enhanced/
├── ThresholdManager
│   ├── Default thresholds
│   ├── Custom threshold support
│   └── Threshold evaluation logic
│
├── RiskHistoryManager
│   ├── Time-series storage
│   ├── Entity history tracking
│   ├── Trend calculation
│   └── Cohort statistics
│
├── MLAnomalyDetector
│   ├── Z-score analysis
│   ├── Isolation Forest (simulated)
│   ├── Spending pattern analysis
│   ├── Velocity detection
│   └── Ensemble scoring
│
├── RegulatoryRuleManager
│   ├── Rule versioning
│   ├── Multiple regulation types
│   ├── Archive management
│   └── Compliance validation
│
└── CustomRuleEngine
    ├── Threshold rules
    ├── Complex rules
    ├── Rule registration
    └── Rule evaluation
```

### Data Models

**RiskThreshold**
- Metric, name, thresholds for each risk level
- Unit, description, timestamps

**RiskDataPoint**
- Timestamp, entity ID, risk metrics
- DTI, credit score, loan amount, anomaly count

**AnomalyDetectionResult**
- Detected anomalies with severity
- Overall risk score, confidence, recommendations

**RegulatoryRule**
- Rule ID, type, version, effective date
- Content, validation logic, archive status

**CustomRuleDefinition**
- Rule ID, type, parameters
- Priority, enabled status, timestamps

### Extensibility Points

1. **ML Models**: Replace simulated Isolation Forest with real model
2. **Rule Types**: Add new CustomRule subclasses
3. **Anomaly Types**: Extend AnomalyType enum
4. **Metrics**: Add custom thresholds and evaluators
5. **Regulations**: Add new regulatory rule types

---

## Deployment Guide

### Installation

```bash
# Install dependencies
pip install fastmcp

# Verify installation
python riskrulesdb_enhanced_server.py --test
```

### Running the Server

```bash
# Start server
python riskrulesdb_enhanced_server.py

# Server runs on stdio transport for MCP
# Listen for tool calls from MCP client
```

### MCP Client Integration

**Claude Settings** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "riskrulesdb": {
      "command": "python",
      "args": [
        "/path/to/riskrulesdb_enhanced_server.py"
      ]
    }
  }
}
```

### Testing

```bash
# Run demonstration
python test_enhanced_riskrulesdb.py

# Output includes:
# - Feature demonstrations
# - Integration scenarios
# - Usage examples
# - Deployment instructions
```

---

## API Reference

### Tools Summary

| Feature | Tool | Purpose |
|---------|------|---------|
| Thresholds | `configure_risk_threshold` | Update threshold values |
| | `add_custom_risk_threshold` | Create new metrics |
| | `get_all_risk_thresholds` | View all thresholds |
| History | `record_risk_assessment` | Store in database |
| | `get_risk_history` | Retrieve history |
| | `calculate_risk_trend` | Analyze trends |
| | `get_cohort_statistics` | Compare cohorts |
| ML | `detect_financial_anomalies` | Run ML detection |
| Regulatory | `get_active_regulatory_rules` | View rules |
| | `create_regulatory_rule_version` | New rule version |
| | `validate_compliance` | Check compliance |
| Custom Rules | `create_custom_threshold_rule` | Threshold rule |
| | `create_custom_complex_rule` | Complex rule |
| | `evaluate_custom_rules` | Run rules |
| | `get_custom_rules` | List rules |
| Comprehensive | `comprehensive_risk_analysis` | All-in-one analysis |
| | `get_server_info` | Server details |

---

## Performance Considerations

**Scalability:**
- History manager: Configurable max points (default 1000)
- Anomaly detection: O(n) for historical data analysis
- Custom rules: O(m) where m = number of rules
- Threshold evaluation: O(1) lookup

**Optimization Strategies:**
- Cache threshold lookups
- Batch history queries
- Parallel cohort calculations
- Streaming anomaly detection

---

## Security & Compliance

**Built-in Protections:**
- ECOA compliance validation
- FCRA compliance checks
- Audit trail for all changes
- Version history for decisions
- No sensitive data storage

**Recommendations:**
- Run in isolated environment
- Implement authentication/authorization at client level
- Log all tool calls for audit trail
- Validate input parameters
- Encrypt history data at rest

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No history found | Check entity_id, ensure record_risk_assessment called |
| Threshold not updating | Verify metric name exists, use get_all_risk_thresholds |
| Anomaly score too high | Check spending_pattern data, verify inputs |
| Compliance validation fails | Review rule content, check for data mismatches |
| Custom rule doesn't fire | Verify rule registered, check operator syntax |

---

## Migration from v1.0

**Breaking Changes:** None

**New Features:**
- All 5 advanced features additive only
- Existing analyze_financial_risk tool still available
- Batch processing still supported

**Migration Path:**
1. Update to new server code
2. Keep existing tools working
3. Gradually migrate to new comprehensive tools
4. No data reprocessing needed

---

## Future Enhancements

**Roadmap:**
- Real ML model integration (scikit-learn, TensorFlow)
- GraphQL API alongside MCP
- Advanced visualization dashboard
- Real-time streaming alerts
- Integration with external data sources
- Multi-tenant support
- Caching layer (Redis)
- Advanced audit logging

---

## Support & Documentation

**Files:**
- `riskrulesdb_enhanced_server.py` - Main server implementation
- `test_enhanced_riskrulesdb.py` - Feature demonstrations
- `ENHANCED_RISKRULESDB_GUIDE.md` - This guide

**Tool Documentation:**
- Run `get_server_info()` for available tools
- Each tool includes comprehensive docstring
- See examples in test file for each feature

---

## License & Attribution

Enhanced RiskRulesDB v2.0.0  
Production-grade Financial Risk Analysis Engine  
Implements 5 advanced features for enterprise lending

---

## Quick Reference

### Most Common Use Cases

**1. Record Assessment**
```python
record_risk_assessment(entity_id, risk_score, risk_level, dti, credit, loan, income, anomalies)
```

**2. Detect Anomalies**
```python
detect_financial_anomalies(entity_id, dti, credit, loan, income, spending_pattern)
```

**3. Comprehensive Analysis**
```python
comprehensive_risk_analysis(entity_id, dti, credit, loan, income, spending_pattern)
```

**4. Check Trend**
```python
calculate_risk_trend(entity_id, period_days=30)
```

**5. Custom Rules**
```python
evaluate_custom_rules(data, rule_ids)
```

---

End of Guide
