# Enhanced DecisionSynthesis MCP - API Reference

## Quick Start

### Installation

```bash
pip install fastmcp pydantic
```

### Starting the Server

```bash
python -m decision_synthesis_enhanced
```

### Server Endpoint

```
http://localhost:8000/tools
```

---

## API Endpoints

### 1. synthesize_decision()

Original decision synthesis functionality.

**Endpoint:** `POST /call/synthesize_decision`

**Request:**
```json
{
  "financial_risk": 30,
  "operational_risk": 25,
  "compliance_risk": 20,
  "reputational_risk": 15,
  "has_critical_issues": false,
  "has_mitigating_factors": true,
  "requires_escalation": false
}
```

**Response:**
```json
{
  "classification": "Approve",
  "risk_score": 25,
  "confidence_level": 0.95,
  "key_decision_factors": [
    "Risk score 25 within acceptable range",
    "No critical issues identified"
  ],
  "explanation": "Decision: Approve\nOverall Risk Score: 25/100\n..."
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `422 Validation Error` - Parameter out of range

**Error Examples:**
```json
{
  "error": "financial_risk must be between 0 and 100"
}
```

---

### 2. explain_decision()

Provides detailed explainability report for decision reasoning.

**Endpoint:** `POST /call/explain_decision`

**Request:**
```json
{
  "financial_risk": 45,
  "operational_risk": 40,
  "compliance_risk": 50,
  "reputational_risk": 35,
  "has_critical_issues": false,
  "has_mitigating_factors": true,
  "requires_escalation": false
}
```

**Response:**
```json
{
  "decision": "Review",
  "primary_reasons": [
    {
      "reason": "Risk profile in medium-high range",
      "score": 43,
      "threshold": 50,
      "impact": 0.4
    }
  ],
  "contributing_factors": [
    {
      "factor": "Financial Risk",
      "value": 45,
      "weight": 0.35
    },
    {
      "factor": "Operational Risk",
      "value": 40,
      "weight": 0.25
    },
    {
      "factor": "Compliance Risk",
      "value": 50,
      "weight": 0.25
    },
    {
      "factor": "Reputational Risk",
      "value": 35,
      "weight": 0.15
    }
  ],
  "decision_path": [
    "[1] Calculate overall risk score: 43/100",
    "[2] Evaluate critical factors: has_critical_issues=false",
    "[3] Check escalation: requires_escalation=false",
    "[4] Risk score 50-84: Trigger medium-high risk path",
    "[5] Final classification: Review"
  ],
  "rule_chain": [
    {
      "rule": "High Risk Check (>= 85)",
      "condition": false,
      "result": "Not triggered"
    },
    {
      "rule": "Critical Issues Check",
      "condition": false,
      "result": "Not triggered"
    },
    {
      "rule": "Medium-High Risk Check (50-84)",
      "condition": true,
      "result": "Triggers review for escalation or critical issues"
    }
  ],
  "impact_breakdown": {
    "financial_impact": 15.75,
    "operational_impact": 10.0,
    "compliance_impact": 12.5,
    "reputational_impact": 5.25
  }
}
```

**Response Fields:**
- `decision`: Classification (Approve, Reject, Review)
- `primary_reasons`: Top reasons for decision
- `contributing_factors`: All risk factors with weights
- `decision_path`: Step-by-step logic progression
- `rule_chain`: Rules evaluated and results
- `impact_breakdown`: Contribution of each risk category

---

### 3. whatif_analysis()

Performs scenario-based what-if analysis.

**Endpoint:** `POST /call/whatif_analysis`

**Request with Default Scenarios:**
```json
{
  "financial_risk": 75,
  "operational_risk": 70,
  "compliance_risk": 80,
  "reputational_risk": 65,
  "has_critical_issues": true,
  "has_mitigating_factors": false,
  "requires_escalation": true
}
```

**Request with Custom Scenarios:**
```json
{
  "financial_risk": 75,
  "operational_risk": 70,
  "compliance_risk": 80,
  "reputational_risk": 65,
  "has_critical_issues": true,
  "has_mitigating_factors": false,
  "requires_escalation": true,
  "scenarios": [
    {
      "name": "Add Mitigation",
      "description": "What if strong mitigating factors were added?",
      "has_mitigating_factors": true
    },
    {
      "name": "Reduce Compliance Risk",
      "description": "What if compliance improved to 50?",
      "compliance_risk": 50
    }
  ]
}
```

**Response:**
```json
[
  {
    "scenario_name": "Reduce Financial Risk",
    "description": "What if financial risk was reduced by 50%?",
    "original_decision": "Review",
    "modified_decision": "Approve",
    "original_risk_score": 73,
    "modified_risk_score": 66,
    "changes": {
      "financial_risk": {
        "from": 75,
        "to": 37.5
      }
    },
    "decision_changed": true,
    "impact_analysis": {
      "risk_score_delta": -7,
      "risk_delta_percentage": -9.59,
      "decision_changed": true,
      "original_decision": "Review",
      "new_decision": "Approve"
    }
  }
]
```

**Response Array:** Returns list of WhatIfScenario objects, one per scenario

---

### 4. calculate_confidence_intervals()

Calculates statistical confidence bounds for risk estimates.

**Endpoint:** `POST /call/calculate_confidence_intervals`

**Request:**
```json
{
  "financial_risk": 50,
  "operational_risk": 45,
  "compliance_risk": 55,
  "reputational_risk": 40,
  "sample_size": 150
}
```

**Response:**
```json
{
  "financial_risk": {
    "point_estimate": 50.0,
    "lower_bound": 45.8,
    "upper_bound": 54.2,
    "margin_of_error": 4.2,
    "confidence_level": 0.95,
    "interpretation": "We can be 95% confident that the true value lies between 45.8 and 54.2. The point estimate of 50.0 is our best estimate based on available data."
  },
  "operational_risk": {
    "point_estimate": 45.0,
    "lower_bound": 40.8,
    "upper_bound": 49.2,
    "margin_of_error": 4.2,
    "confidence_level": 0.95,
    "interpretation": "We can be 95% confident that the true value lies between 40.8 and 49.2. The point estimate of 45.0 is our best estimate based on available data."
  },
  "compliance_risk": {
    "point_estimate": 55.0,
    "lower_bound": 50.8,
    "upper_bound": 59.2,
    "margin_of_error": 4.2,
    "confidence_level": 0.95,
    "interpretation": "We can be 95% confident that the true value lies between 50.8 and 59.2. The point estimate of 55.0 is our best estimate based on available data."
  },
  "reputational_risk": {
    "point_estimate": 40.0,
    "lower_bound": 35.8,
    "upper_bound": 44.2,
    "margin_of_error": 4.2,
    "confidence_level": 0.95,
    "interpretation": "We can be 95% confident that the true value lies between 35.8 and 44.2. The point estimate of 40.0 is our best estimate based on available data."
  },
  "overall_risk_score": {
    "point_estimate": 47.5,
    "lower_bound": 43.3,
    "upper_bound": 51.7,
    "margin_of_error": 4.2,
    "confidence_level": 0.95,
    "interpretation": "We can be 95% confident that the true value lies between 43.3 and 51.7. The point estimate of 47.5 is our best estimate based on available data."
  }
}
```

**Parameters:**
- `sample_size`: 10-10000 (default: 100)
- `confidence_level`: Always 0.95 (95%)

**Key Fields:**
- `point_estimate`: Best estimate of the true value
- `lower_bound`: Lower confidence bound (95%)
- `upper_bound`: Upper confidence bound (95%)
- `margin_of_error`: ±MOE around estimate
- `interpretation`: Human-readable explanation

---

### 5. calculate_decision_probabilities()

Calculates probability scores for each decision classification.

**Endpoint:** `POST /call/calculate_decision_probabilities`

**Request:**
```json
{
  "financial_risk": 35,
  "operational_risk": 30,
  "compliance_risk": 25,
  "reputational_risk": 20,
  "has_critical_issues": false,
  "has_mitigating_factors": true,
  "requires_escalation": false
}
```

**Response:**
```json
{
  "approve_probability": 0.8934,
  "reject_probability": 0.0187,
  "review_probability": 0.0879,
  "most_likely_decision": "APPROVE",
  "decision_entropy": 0.3214,
  "probability_explanation": "Based on low risk profile (score: 29/100), the model assigns probabilities: Approve 89.3%, Reject 1.9%, Review 8.8%. Factors: critical_issues=false, mitigating_factors=true, escalation_required=false. Decision entropy: 0.32/1.0 (higher = more uncertain)."
}
```

**Response Fields:**
- `approve_probability`: 0.0-1.0 (probability of approval)
- `reject_probability`: 0.0-1.0 (probability of rejection)
- `review_probability`: 0.0-1.0 (probability of review)
- `most_likely_decision`: Most probable classification
- `decision_entropy`: Uncertainty measure (0.0-1.0)
- `probability_explanation`: Detailed explanation

**Entropy Interpretation:**
- `0.0-0.3`: Low uncertainty (confident decision)
- `0.3-0.7`: Moderate uncertainty (careful review)
- `0.7-1.0`: High uncertainty (needs detailed analysis)

---

### 6. detect_decision_biases()

Detects potential biases in decision logic.

**Endpoint:** `POST /call/detect_decision_biases`

**Request:**
```json
{
  "financial_risk": 5,
  "operational_risk": 85,
  "compliance_risk": 10,
  "reputational_risk": 8,
  "has_critical_issues": false,
  "has_mitigating_factors": true,
  "requires_escalation": false
}
```

**Response:**
```json
{
  "overall_bias_score": 0.1847,
  "detected_biases": [
    {
      "type": "RISK_SKEW",
      "severity": "high",
      "description": "Risk factors have disproportionate distribution",
      "details": "Standard deviation of 35.2 indicates high variance in risk distribution",
      "impact": "A few risk factors dominate the overall risk score",
      "score": 0.1453
    },
    {
      "type": "FACTOR_DOMINANCE",
      "severity": "high",
      "description": "operational risk dominates decision",
      "details": "operational contributes 52.3% of impact",
      "impact": "Decision may not adequately consider balanced risk profile",
      "score": 0.1847
    }
  ],
  "risk_distribution_analysis": {
    "mean_risk": 27.0,
    "std_deviation": 35.2,
    "min_risk": 5,
    "max_risk": 85,
    "range": 80
  },
  "threshold_fairness_analysis": {
    "high_risk_threshold": 85,
    "medium_risk_threshold": 50,
    "critical_issues_penalty": "Strong rejection signal",
    "mitigation_factor_benefit": "Can convert rejection to review"
  },
  "factor_dominance_analysis": {
    "dominant_factor": "operational",
    "dominant_factor_impact_percentage": 52.3,
    "all_factor_impacts": {
      "financial": 1.75,
      "operational": 21.25,
      "compliance": 2.5,
      "reputational": 1.2
    }
  },
  "recommendations": [
    "Review risk distribution: Consider investigating why certain risk factors are significantly higher than others",
    "Review weighting of operational: Consider if 52.3% contribution is intentional",
    "Review decision rules: Ensure rules are applied consistently across similar cases"
  ]
}
```

**Detected Bias Types:**
- `RISK_SKEW`: Unbalanced risk factor distribution
- `THRESHOLD_BIAS`: Unfair threshold application
- `FACTOR_DOMINANCE`: Single factor over-dominance
- `CONSISTENCY_BIAS`: Inconsistent rule application
- `ESCALATION_BIAS`: Biased escalation criteria

---

### 7. get_decision_rules()

Retrieves complete decision rule set.

**Endpoint:** `GET /call/get_decision_rules`

**Request:** No parameters

**Response:**
```json
{
  "risk_score_calculation": {
    "description": "Overall risk score is calculated as weighted average of component risks",
    "weights": {
      "financial_risk": 0.35,
      "operational_risk": 0.25,
      "compliance_risk": 0.25,
      "reputational_risk": 0.15
    },
    "range": "0-100"
  },
  "classification_rules": {
    "REJECT": {
      "conditions": [
        "Risk score >= 85 (high risk)",
        "Has critical unmitigable issues",
        "Critical compliance violations"
      ],
      "confidence_range": "0.9-0.95"
    },
    "REVIEW": {
      "conditions": [
        "Risk score 50-84 (medium-high risk)",
        "Has critical issues with mitigation possible",
        "Requires escalation",
        "Mixed risk profile"
      ],
      "confidence_range": "0.7-0.85"
    },
    "APPROVE": {
      "conditions": [
        "Risk score < 50 (low-medium risk)",
        "No critical unmitigable issues",
        "Mitigating factors present"
      ],
      "confidence_range": "0.9-0.95"
    }
  },
  "thresholds": {
    "low_risk": "0-49",
    "medium_high_risk": "50-84",
    "high_risk": "85-100"
  },
  "new_features": {
    "explain_decision": "Get detailed explainability report for a decision",
    "whatif_analysis": "Perform what-if scenario analysis",
    "calculate_confidence_intervals": "Calculate statistical confidence bounds",
    "calculate_decision_probabilities": "Get probability scores for each outcome",
    "detect_decision_biases": "Identify potential biases in decision logic"
  }
}
```

---

## Common Request/Response Patterns

### Success Response Format

```json
{
  "success": true,
  "data": { /* feature-specific data */ },
  "timestamp": "2024-06-19T10:30:00Z",
  "processing_time_ms": 2.5
}
```

### Error Response Format

```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "financial_risk must be between 0 and 100",
  "details": {
    "field": "financial_risk",
    "value": 150,
    "constraint": "0-100"
  },
  "timestamp": "2024-06-19T10:30:00Z"
}
```

### Parameter Validation

All risk parameters must be:
- **Type:** float or int
- **Range:** 0-100 (inclusive)
- **Required:** Yes

Boolean parameters:
- **Type:** boolean
- **Required:** No
- **Default:** false

---

## Rate Limiting & Performance

### Limits

- **Rate Limit:** 1000 requests/minute per API key
- **Timeout:** 30 seconds per request
- **Max Concurrent:** 100 simultaneous requests
- **Batch Size:** Max 50 decisions per batch call

### Performance Targets

| Operation | Time (ms) | P95 | P99 |
|-----------|-----------|-----|-----|
| synthesize_decision() | 0.8 | 1.2 | 1.8 |
| explain_decision() | 1.5 | 2.1 | 3.0 |
| whatif_analysis() (4 scenarios) | 3.2 | 4.5 | 6.0 |
| calculate_confidence_intervals() | 0.7 | 1.0 | 1.5 |
| calculate_decision_probabilities() | 0.9 | 1.3 | 2.0 |
| detect_decision_biases() | 2.1 | 3.0 | 4.2 |

---

## Authentication

### API Key

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"financial_risk": 30}' \
     http://localhost:8000/call/synthesize_decision
```

### OAuth 2.0

```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/call/get_decision_rules
```

---

## Webhooks

### Decision Events

Subscribe to decision events:

```json
POST /webhooks/subscribe
{
  "url": "https://your-api.com/webhooks/decision",
  "events": ["decision.made", "decision.reviewed", "bias.detected"],
  "batch": false
}
```

### Webhook Payload

```json
{
  "event": "decision.made",
  "timestamp": "2024-06-19T10:30:00Z",
  "decision_id": "DEC-2024-06-19-001",
  "result": {
    "classification": "Approve",
    "risk_score": 35,
    "confidence_level": 0.92
  }
}
```

---

## SDKs

### Python SDK

```python
from decision_synthesis_enhanced import DecisionSynthesisClient

client = DecisionSynthesisClient(api_key="your_key")

result = await client.explain_decision(
    financial_risk=30,
    operational_risk=25,
    compliance_risk=20,
    reputational_risk=15
)

print(result.decision)
print(result.primary_reasons)
```

### JavaScript/TypeScript SDK

```javascript
import { DecisionSynthesisClient } from 'decision-synthesis-sdk';

const client = new DecisionSynthesisClient({
  apiKey: 'your_key'
});

const result = await client.explainDecision({
  financialRisk: 30,
  operationalRisk: 25,
  complianceRisk: 20,
  reputationalRisk: 15
});
```

---

## Versioning

### API Version: v1

Current stable version: `1.0.0`

### Version Header

```bash
curl -H "API-Version: 1.0.0" \
     http://localhost:8000/call/synthesize_decision
```

### Deprecation Policy

- Features marked deprecated will be supported for 12 months
- Breaking changes only in major version updates
- Minor versions for feature additions
- Patch versions for bug fixes

---

## Changelog

### Version 1.0.0 (Current)

**New Features:**
- Decision explainability API
- What-if analysis tool
- Confidence interval calculation
- Decision probability scoring
- Bias detection checks

**Breaking Changes:** None (initial release)

**Deprecated:** None

---

## Support

### Documentation

- **API Guide:** This document
- **Feature Guide:** DECISION_SYNTHESIS_ENHANCED_GUIDE.md
- **Examples:** enhanced_decision_examples.py
- **Tests:** test_decision_synthesis_enhanced.py

### Getting Help

1. Check documentation and examples
2. Review test cases for usage patterns
3. Check error codes and messages
4. Contact support with error details

---

**Last Updated:** 2024-06-19  
**API Version:** 1.0.0  
**Status:** Stable
