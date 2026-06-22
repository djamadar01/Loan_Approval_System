# Loan Application API v2 - Complete Implementation

## Overview

This document describes the advanced API v2 implementation with 5 enterprise-grade endpoints:

1. **GET /api/v2/decisions/analytics** - Aggregated decision statistics and analytics
2. **POST /api/v2/applications/batch** - Batch submission and processing
3. **GET /api/v2/applications/{id}/explainability** - Detailed decision breakdown
4. **POST /api/v2/applications/{id}/what-if** - Scenario analysis
5. **WebSocket /ws/live-updates** - Real-time notifications

---

## 1. Analytics Endpoint: GET /api/v2/decisions/analytics

### Purpose
Provides comprehensive aggregated statistics across all loan decisions including approval rates, risk distributions, processing metrics, and time-series trends.

### Request
```http
GET /api/v2/decisions/analytics?period=last_7_days&group_by=location
```

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| period | string | last_7_days | Time period: `last_24_hours`, `last_7_days`, `last_30_days`, `all_time` |
| group_by | string | null | Optional grouping: `location`, `employment_status`, `credit_tier` |

### Response
```json
{
  "period": "last_7_days",
  "metrics": {
    "total_applications": 1547,
    "approved_count": 892,
    "rejected_count": 324,
    "manual_review_count": 198,
    "conditional_count": 133,
    "approval_rate": 0.5768,
    "average_risk_score": 42.7,
    "average_processing_time_ms": 1245.8,
    "median_loan_amount": 32500.0,
    "total_loan_volume": 50325000.0
  },
  "decision_distribution": {
    "approved": 892,
    "rejected": 324,
    "manual_review": 198,
    "conditional_approval": 133
  },
  "risk_distribution": {
    "low": 456,
    "medium": 789,
    "high": 245,
    "very_high": 57
  },
  "top_rejection_reasons": [
    {
      "reason": "Low credit score",
      "count": 89,
      "percentage": 27.5
    },
    {
      "reason": "High debt-to-income ratio",
      "count": 76,
      "percentage": 23.5
    }
  ],
  "processing_time_percentiles": {
    "p50": 890.0,
    "p75": 1450.0,
    "p90": 2100.0,
    "p95": 2850.0,
    "p99": 4200.0
  },
  "time_series_data": {
    "daily_approvals": [
      {
        "date": "2024-06-19T00:00:00",
        "count": 120
      }
    ],
    "hourly_processing_time": [
      {
        "hour": 0,
        "avg_time_ms": 1050.5
      }
    ]
  },
  "generated_at": "2024-06-20T10:30:45.123Z"
}
```

### Example Usage (Python)
```python
import asyncio
from api_v2_client import LoanApplicationAPIv2Client

async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Get analytics for last 7 days
        analytics = await client.get_analytics(period="last_7_days")
        
        # Extract key metrics
        approval_rate = analytics["metrics"]["approval_rate"]
        avg_risk = analytics["metrics"]["average_risk_score"]
        
        print(f"Approval Rate: {approval_rate:.1%}")
        print(f"Average Risk Score: {avg_risk:.1f}")
        
        # Analyze top rejection reasons
        for reason in analytics["top_rejection_reasons"]:
            print(f"- {reason['reason']}: {reason['percentage']:.1f}%")

asyncio.run(main())
```

### Use Cases
- Dashboard KPI monitoring
- Regulatory reporting
- Performance benchmarking
- Trend analysis
- Anomaly detection

---

## 2. Batch Processing Endpoint: POST /api/v2/applications/batch

### Purpose
Submit multiple loan applications for asynchronous batch processing with progress tracking and completion notifications.

### Request
```http
POST /api/v2/applications/batch
Content-Type: application/json
```

#### Request Body
```json
{
  "applications": [
    {
      "applicant_id": "APP-001",
      "profile": {
        "name": "John Doe",
        "age": 35,
        "employment_status": "full_time",
        "employment_years": 5,
        "education_level": "bachelor",
        "annual_income": 75000,
        "monthly_expenses": 2500,
        "savings": 15000,
        "existing_loans": 1
      },
      "credit_score": 720,
      "loan_amount": 25000,
      "tenure": 60,
      "liabilities": 10000,
      "location": "New York, NY"
    }
  ],
  "priority": "normal",
  "notify_on_completion": true
}
```

### Response (202 Accepted)
```json
{
  "batch_id": "BATCH-20240620-A1B2C3D4",
  "total_applications": 1,
  "status": "queued",
  "created_at": "2024-06-20T10:35:22.123Z",
  "estimated_completion": "2024-06-20T10:36:15.789Z"
}
```

### Batch Status Endpoint
```http
GET /api/v2/batches/{batch_id}/status
```

#### Status Response
```json
{
  "batch_id": "BATCH-20240620-A1B2C3D4",
  "status": "completed",
  "total_applications": 100,
  "processed": 100,
  "created_at": "2024-06-20T10:35:22.123Z",
  "started_at": "2024-06-20T10:35:25.456Z",
  "completed_at": "2024-06-20T10:38:45.789Z"
}
```

### Example Usage (Python)
```python
async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Create applications
        applications = [
            {
                "applicant_id": f"APP-{i:04d}",
                "profile": {...},
                "credit_score": 700 + i,
                "loan_amount": 25000,
                "tenure": 60,
                "liabilities": 10000,
                "location": "New York, NY"
            }
            for i in range(100)
        ]
        
        # Submit batch
        result = await client.submit_batch(
            applications,
            priority="high",
            notify_on_completion=True
        )
        
        print(f"Batch ID: {result.batch_id}")
        print(f"Estimated Completion: {result.estimated_completion}")
        
        # Poll for completion
        while True:
            status = await client.get_batch_status(result.batch_id)
            if status["status"] == "completed":
                print(f"Processed: {status['processed']}/{status['total_applications']}")
                break
            await asyncio.sleep(5)
```

### Features
- **Asynchronous Processing**: Non-blocking submission and processing
- **Priority Scheduling**: normal, high, low priority levels
- **Progress Tracking**: Real-time processing status
- **Error Handling**: Per-application error tracking
- **Notifications**: WebSocket notifications on completion

---

## 3. Explainability Endpoint: GET /api/v2/applications/{id}/explainability

### Purpose
Provides detailed, interpretable breakdown of loan decisions with factor analysis, alternative paths, regulatory compliance, and confidence intervals.

### Request
```http
GET /api/v2/applications/APP-001/explainability?include_alternatives=true&confidence_level=0.95
```

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| include_alternatives | boolean | true | Include alternative decision paths |
| confidence_level | float | 0.95 | Confidence level for uncertainty intervals (0.5-0.99) |

### Response
```json
{
  "case_id": "CASE-20240620-APP-001",
  "classification": "approved",
  "risk_score": 42.7,
  "decision_breakdown": {
    "primary_factors": {
      "credit_score": 720,
      "debt_to_income": 0.28,
      "employment_stability": 0.85,
      "savings_ratio": 0.32
    },
    "threshold_analysis": {
      "credit_score_threshold": 650,
      "credit_score_status": "passed",
      "dti_threshold": 0.43,
      "dti_status": "passed"
    },
    "scoring_methodology": "gradient_boosting_model_v2.1",
    "model_version": "2.1.0",
    "model_accuracy": 0.912
  },
  "key_factors": [
    {
      "factor_name": "Credit Score",
      "impact": "positive",
      "value": 720,
      "weight": 0.35,
      "explanation": "Excellent credit history with no delinquencies"
    },
    {
      "factor_name": "Debt-to-Income Ratio",
      "impact": "positive",
      "value": 0.28,
      "weight": 0.25,
      "explanation": "Conservative debt level relative to income"
    }
  ],
  "factor_contributions": {
    "Credit Score": 0.35,
    "Debt-to-Income Ratio": 0.25,
    "Employment Stability": 0.20,
    "Savings and Reserves": 0.15
  },
  "alternative_paths": [
    {
      "scenario": "If credit score was 650",
      "predicted_classification": "conditional_approval",
      "predicted_risk_score": 58.5,
      "change_in_decision": "From approved to conditional"
    }
  ],
  "regulatory_flags": [
    "ECOA_compliant",
    "FCRA_compliant",
    "Fair_lending_check_passed",
    "Income_verified"
  ],
  "confidence_intervals": {
    "risk_score_interval": {
      "lower_bound": 38.2,
      "upper_bound": 47.8,
      "confidence_level": 0.95
    },
    "approval_probability": {
      "point_estimate": 0.92,
      "interval": [0.87, 0.96],
      "confidence_level": 0.95
    },
    "expected_default_rate": {
      "point_estimate": 0.032,
      "interval": [0.018, 0.048],
      "confidence_level": 0.95
    }
  },
  "generated_at": "2024-06-20T10:40:22.345Z"
}
```

### Example Usage (Python)
```python
async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Get detailed explanation
        explanation = await client.get_explainability(
            "APP-001",
            include_alternatives=True,
            confidence_level=0.95
        )
        
        # Print decision summary
        print(f"Decision: {explanation['classification']}")
        print(f"Risk Score: {explanation['risk_score']:.1f}")
        
        # Show key factors with contributions
        print("\nFactor Analysis:")
        for factor in explanation["key_factors"]:
            weight = factor["weight"] * 100
            print(f"- {factor['factor_name']}: {weight:.1f}%")
            print(f"  Impact: {factor['impact']}")
            print(f"  {factor['explanation']}")
        
        # Show alternative scenarios
        print("\nAlternative Scenarios:")
        for alt in explanation["alternative_paths"]:
            print(f"- {alt['scenario']}")
            print(f"  Result: {alt['predicted_classification']} (Risk: {alt['predicted_risk_score']:.1f})")
        
        # Compliance check
        print(f"\nRegulatory Compliance: {'✓' if 'ECOA_compliant' in explanation['regulatory_flags'] else '✗'}")
```

### Features
- **Factor Decomposition**: Weight and contribution of each factor
- **Threshold Analysis**: Show which thresholds were passed/failed
- **Alternative Scenarios**: What-if the applicant had different characteristics
- **Regulatory Compliance**: Fair lending and ECOA compliance flags
- **Uncertainty Quantification**: Confidence intervals for predictions
- **Model Transparency**: Show which model version and accuracy

---

## 4. What-If Analysis Endpoint: POST /api/v2/applications/{id}/what-if

### Purpose
Analyze how loan decisions would change under different scenarios, enabling sensitivity analysis and decision threshold exploration.

### Request
```http
POST /api/v2/applications/APP-001/what-if
Content-Type: application/json
```

#### Request Body
```json
{
  "scenarios": [
    {
      "scenario_name": "Higher Income",
      "changes": {
        "annual_income": 100000
      },
      "description": "What if annual income was $100,000?"
    },
    {
      "scenario_name": "Lower Credit Score",
      "changes": {
        "credit_score": 650
      },
      "description": "What if credit score dropped to 650?"
    },
    {
      "scenario_name": "Combined Improvement",
      "changes": {
        "credit_score": 780,
        "annual_income": 95000,
        "liabilities": 5000,
        "savings": 50000
      },
      "description": "What if all metrics improved?"
    }
  ],
  "base_application_id": "APP-001"
}
```

### Response
```json
{
  "original_decision": {
    "case_id": "CASE-20240620-APP-001",
    "classification": "approved",
    "risk_score": 42.7,
    "confidence": 0.92,
    "loan_amount": 25000,
    "approval_probability": 0.92
  },
  "scenarios": [
    {
      "scenario_name": "Higher Income",
      "description": "What if annual income was $100,000?",
      "changes_applied": {
        "annual_income": 100000
      },
      "predicted_classification": "approved",
      "predicted_risk_score": 38.5,
      "predicted_confidence": 0.85,
      "decision_impact": "no_change",
      "approval_probability": 0.92,
      "key_changes": [
        "annual_income: 100000"
      ]
    },
    {
      "scenario_name": "Lower Credit Score",
      "description": "What if credit score dropped to 650?",
      "changes_applied": {
        "credit_score": 650
      },
      "predicted_classification": "conditional_approval",
      "predicted_risk_score": 58.5,
      "predicted_confidence": 0.85,
      "decision_impact": "decline",
      "approval_probability": 0.45,
      "key_changes": [
        "credit_score: 650"
      ]
    }
  ],
  "comparison_matrix": {
    "original": {...},
    "scenarios": [...],
    "sensitivity_ranking": [
      ["Lower Credit Score", 15.8],
      ["Combined Improvement", 4.2],
      ["Higher Income", 4.2]
    ]
  },
  "insights": [
    "Most sensitive factor: Lower Credit Score (risk score change: 15.8)",
    "1 scenario(s) result in rejection",
    "Consider improving credit score for better loan terms"
  ],
  "generated_at": "2024-06-20T10:45:33.567Z"
}
```

### Example Usage (Python)
```python
async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Define scenarios
        scenarios = [
            Scenario(
                scenario_name="Job Promotion (+$20k)",
                changes={"annual_income": 95000},
                description="After getting promoted"
            ),
            Scenario(
                scenario_name="Pay Off Credit Cards",
                changes={"liabilities": 5000},
                description="After paying down debt"
            ),
            Scenario(
                scenario_name="Build Savings",
                changes={"savings": 50000},
                description="After 2 years of saving"
            )
        ]
        
        # Run analysis
        results = await client.what_if_analysis("APP-001", scenarios)
        
        # Compare scenarios
        print(f"Original: {results['original_decision']['classification']} "
              f"(Risk: {results['original_decision']['risk_score']:.1f})")
        
        for scenario in results["scenarios"]:
            impact = "↑" if scenario["decision_impact"] == "improvement" else (
                "↓" if scenario["decision_impact"] == "decline" else "→"
            )
            print(f"\n{impact} {scenario['scenario_name']}")
            print(f"  Result: {scenario['predicted_classification']}")
            print(f"  Risk: {scenario['predicted_risk_score']:.1f}")
        
        # Show insights
        print("\nKey Insights:")
        for insight in results["insights"]:
            print(f"• {insight}")
```

### Features
- **Multi-Scenario Analysis**: Compare up to 10 scenarios simultaneously
- **Simultaneous Changes**: Modify multiple parameters at once
- **Sensitivity Ranking**: Identify most impactful factors
- **Decision Thresholds**: Show proximity to decision boundaries
- **Actionable Insights**: AI-generated recommendations
- **Comparison Matrix**: Side-by-side decision comparisons

---

## 5. WebSocket Endpoint: /ws/live-updates

### Purpose
Provide real-time, bidirectional communication for live notifications, batch progress updates, and system status.

### Connection
```javascript
const ws = new WebSocket("ws://localhost:8001/ws/live-updates");
```

### Protocol

#### Client-to-Server Messages

**Subscribe to Topic:**
```json
{
  "action": "subscribe",
  "topic": "batch_processing"
}
```

**Unsubscribe from Topic:**
```json
{
  "action": "unsubscribe",
  "topic": "batch_processing"
}
```

**Keep-Alive Ping:**
```json
{
  "action": "ping"
}
```

#### Server-to-Client Messages

**Subscription Confirmation:**
```json
{
  "type": "status",
  "message": "Subscribed to topic: batch_processing",
  "topic": "batch_processing",
  "timestamp": "2024-06-20T10:50:00.123Z"
}
```

**Batch Progress Update:**
```json
{
  "type": "batch_progress",
  "batch_id": "BATCH-20240620-ABC123",
  "processed": 45,
  "total": 100,
  "percentage": 45.0,
  "timestamp": "2024-06-20T10:50:15.456Z"
}
```

**Application Submitted Notification:**
```json
{
  "type": "application_submitted",
  "batch_id": "BATCH-20240620-ABC123",
  "total_applications": 100,
  "timestamp": "2024-06-20T10:50:00.123Z"
}
```

**Application Processed Notification:**
```json
{
  "type": "application_processed",
  "case_id": "CASE-20240620-ABC123",
  "applicant_id": "APP-001",
  "classification": "approved",
  "risk_score": 42.7,
  "timestamp": "2024-06-20T10:50:22.789Z"
}
```

**Error Notification:**
```json
{
  "type": "error",
  "message": "Failed to process application",
  "error_code": "PROCESSING_ERROR",
  "timestamp": "2024-06-20T10:51:00.111Z"
}
```

**Keep-Alive Pong:**
```json
{
  "type": "pong",
  "timestamp": "2024-06-20T10:52:00.222Z"
}
```

### Example Usage (Python)
```python
async def handle_message(message):
    """Handle incoming WebSocket messages."""
    msg_type = message.get("type")
    
    if msg_type == "batch_progress":
        pct = message["percentage"]
        print(f"Batch progress: {pct:.1f}%")
    
    elif msg_type == "application_processed":
        case_id = message["case_id"]
        classification = message["classification"]
        print(f"Application {case_id}: {classification}")
    
    elif msg_type == "error":
        print(f"Error: {message['message']}")

async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Subscribe to multiple topics and receive updates
        await client.websocket_live_updates(
            handle_message,
            topics=["batch_processing", "applications"]
        )

asyncio.run(main())
```

### Example Usage (JavaScript)
```javascript
const ws = new WebSocket("ws://localhost:8001/ws/live-updates");

ws.onopen = () => {
    console.log("Connected");
    
    // Subscribe to batch processing updates
    ws.send(JSON.stringify({
        action: "subscribe",
        topic: "batch_processing"
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === "batch_progress") {
        const progressBar = document.getElementById("progress");
        progressBar.style.width = data.percentage + "%";
        progressBar.textContent = data.percentage.toFixed(1) + "%";
    }
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
};

ws.onclose = () => {
    console.log("Disconnected");
};
```

### Topics

| Topic | Description |
|-------|-------------|
| batch_processing | Batch submission and progress updates |
| applications | Individual application processing events |
| analytics | Analytics updates and recalculations |
| system | System status and maintenance messages |

### Features
- **Bidirectional Communication**: Client and server can both initiate messages
- **Topic-Based Routing**: Subscribe to specific notification types
- **Low Latency**: Real-time updates with minimal delay
- **Automatic Reconnection**: Built-in reconnection logic
- **Keep-Alive**: Ping/pong for connection health
- **Multiple Subscribers**: One connection can subscribe to multiple topics

---

## Error Handling

All endpoints follow consistent error response format:

### Error Response Format
```json
{
  "error_code": "VALIDATION_ERROR",
  "error_message": "Input validation failed",
  "details": {
    "validation_errors": [
      {
        "field": "credit_score",
        "type": "value_error.number.not_ge",
        "message": "ensure this value is greater than or equal to 300"
      }
    ]
  },
  "case_id": "CASE-20240620-ABC123",
  "timestamp": "2024-06-20T10:55:00.123Z"
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| VALIDATION_ERROR | 422 | Input validation failed |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict |
| RATE_LIMITED | 429 | Rate limit exceeded |
| INTERNAL_SERVER_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Service unavailable |

---

## Rate Limiting

API implements rate limiting to ensure fair usage:

- **Analytics**: 100 requests/minute
- **Batch Processing**: 10 requests/minute
- **Explainability**: 50 requests/minute
- **What-If**: 30 requests/minute
- **WebSocket**: 1 connection/IP

---

## Authentication

Optional API key authentication:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8001/api/v2/decisions/analytics
```

---

## Performance Metrics

### Typical Response Times
- **Analytics**: 200-500ms
- **Batch Submission**: 100-200ms
- **Explainability**: 300-800ms
- **What-If Analysis**: 500-1500ms
- **WebSocket Connect**: <50ms

### Throughput
- **Analytics**: 100+ requests/second
- **Batch Applications**: 1000+ applications/minute
- **WebSocket Connections**: 1000+ concurrent connections

---

## Integration Examples

### Complete Loan Decision Workflow

```python
async def complete_loan_workflow():
    """Complete end-to-end loan decision workflow."""
    
    client = LoanApplicationAPIv2Client("http://localhost:8001")
    
    async with client:
        # 1. Submit batch of applications
        print("Step 1: Submitting batch...")
        applications = await create_sample_applications(10)
        batch = await client.submit_batch(applications)
        
        # 2. Monitor processing with WebSocket
        print("Step 2: Monitoring progress...")
        async def log_progress(msg):
            if msg["type"] == "batch_progress":
                print(f"  Progress: {msg['percentage']:.1f}%")
        
        # Start listening (in background)
        ws_task = asyncio.create_task(
            client.websocket_live_updates(
                log_progress,
                topics=[f"batch_{batch.batch_id}"]
            )
        )
        
        # Wait for batch to complete
        while True:
            status = await client.get_batch_status(batch.batch_id)
            if status["status"] == "completed":
                break
            await asyncio.sleep(2)
        
        # 3. Get analytics for the batch
        print("Step 3: Analyzing results...")
        analytics = await client.get_analytics(period="last_24_hours")
        print(f"  Approval Rate: {analytics['metrics']['approval_rate']:.1%}")
        
        # 4. Deep-dive into a decision
        print("Step 4: Getting detailed explanation...")
        explanation = await client.get_explainability("APP-001")
        print(f"  Decision: {explanation['classification']}")
        
        # 5. Run what-if analysis
        print("Step 5: Running what-if scenarios...")
        scenarios = [
            Scenario("Higher Income", {"annual_income": 100000}),
            Scenario("Better Credit", {"credit_score": 750})
        ]
        what_if = await client.what_if_analysis("APP-001", scenarios)
        
        print("\nWorkflow Complete!")
```

---

## Installation & Setup

### Requirements
```
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
httpx>=0.24.0
websockets>=11.0
```

### Start API Server
```bash
python api_v2.py
# or with uvicorn directly
uvicorn api_v2:app --host 0.0.0.0 --port 8001 --reload
```

### Access Documentation
- OpenAPI: http://localhost:8001/api/v2/docs
- ReDoc: http://localhost:8001/api/v2/redoc

---

## Testing

Run comprehensive test suite:
```bash
pytest test_api_v2.py -v
```

Test individual endpoints:
```bash
# Test analytics
pytest test_api_v2.py::test_analytics_last_7_days -v

# Test batch processing
pytest test_api_v2.py::test_batch_submit_multiple_applications -v

# Test WebSocket
pytest test_api_v2.py::test_websocket_connection -v
```

---

## Deployment

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY api_v2.py .
CMD ["uvicorn", "api_v2:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Build and Run:**
```bash
docker build -t loan-api-v2 .
docker run -p 8001:8001 loan-api-v2
```

### Kubernetes Deployment

See `k8s-deployment.yaml` for complete Kubernetes manifests.

---

## Support & Documentation

- **API Documentation**: http://localhost:8001/api/v2/docs
- **Client Library**: `api_v2_client.py`
- **Test Suite**: `test_api_v2.py`
- **Examples**: See examples in client library and this documentation

---

## Version History

### v2.0.0 (Current)
- Initial release with 5 advanced endpoints
- Analytics with time-series support
- Batch processing with WebSocket notifications
- Explainability with regulatory compliance
- What-if scenario analysis
- Real-time WebSocket updates

---

## License & Copyright

© 2024 Loan Application Processing System. All rights reserved.
