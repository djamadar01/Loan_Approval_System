# API v2 - Quick Start Guide

## Installation

### 1. Install Dependencies
```bash
pip install -r api_v2_requirements.txt
```

### 2. Start the API Server
```bash
# Option 1: Direct Python
python api_v2.py

# Option 2: Uvicorn
uvicorn api_v2:app --host 0.0.0.0 --port 8001 --reload

# Option 3: Docker
docker build -t loan-api-v2 .
docker run -p 8001:8001 loan-api-v2
```

### 3. Access API Documentation
- **Interactive Docs**: http://localhost:8001/api/v2/docs
- **ReDoc**: http://localhost:8001/api/v2/redoc

---

## Quick Examples

### Example 1: Get Analytics

**Using Python Client:**
```python
import asyncio
from api_v2_client import LoanApplicationAPIv2Client

async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        analytics = await client.get_analytics(period="last_7_days")
        
        print(f"Total Applications: {analytics['metrics']['total_applications']}")
        print(f"Approval Rate: {analytics['metrics']['approval_rate']:.1%}")
        print(f"Avg Risk Score: {analytics['metrics']['average_risk_score']:.1f}")

asyncio.run(main())
```

**Using cURL:**
```bash
curl http://localhost:8001/api/v2/decisions/analytics?period=last_7_days
```

**Using JavaScript/Fetch:**
```javascript
const response = await fetch(
  'http://localhost:8001/api/v2/decisions/analytics?period=last_7_days'
);
const data = await response.json();
console.log(`Approval Rate: ${(data.metrics.approval_rate * 100).toFixed(1)}%`);
```

---

### Example 2: Submit Batch Applications

**Using Python Client:**
```python
import asyncio
from api_v2_client import LoanApplicationAPIv2Client, create_sample_applications

async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Create sample applications
        applications = await create_sample_applications(5)
        
        # Submit batch
        result = await client.submit_batch(
            applications,
            priority="normal",
            notify_on_completion=True
        )
        
        print(f"Batch ID: {result.batch_id}")
        print(f"Status: {result.status}")
        print(f"Estimated Completion: {result.estimated_completion}")
        
        # Check status
        while True:
            status = await client.get_batch_status(result.batch_id)
            processed = status.get('processed', 0)
            total = status['total_applications']
            
            print(f"Progress: {processed}/{total}")
            
            if status['status'] == 'completed':
                print("Batch processing completed!")
                break
            
            await asyncio.sleep(2)

asyncio.run(main())
```

**Using cURL:**
```bash
curl -X POST http://localhost:8001/api/v2/applications/batch \
  -H "Content-Type: application/json" \
  -d '{
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
    "priority": "normal"
  }'
```

---

### Example 3: Get Explainability

**Using Python Client:**
```python
import asyncio
from api_v2_client import LoanApplicationAPIv2Client

async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        explanation = await client.get_explainability("APP-001")
        
        print(f"Decision: {explanation['classification']}")
        print(f"Risk Score: {explanation['risk_score']:.1f}")
        
        print("\nKey Factors:")
        for factor in explanation['key_factors']:
            print(f"  {factor['factor_name']} ({factor['impact']})")
            print(f"    Weight: {factor['weight']:.0%}")
            print(f"    {factor['explanation']}")
        
        print("\nRegulatory Compliance:")
        for flag in explanation['regulatory_flags']:
            print(f"  ✓ {flag}")

asyncio.run(main())
```

**Using cURL:**
```bash
curl "http://localhost:8001/api/v2/applications/APP-001/explainability?include_alternatives=true&confidence_level=0.95"
```

---

### Example 4: What-If Analysis

**Using Python Client:**
```python
import asyncio
from api_v2_client import LoanApplicationAPIv2Client, Scenario

async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Define scenarios
        scenarios = [
            Scenario(
                scenario_name="Higher Income",
                changes={"annual_income": 100000},
                description="If annual income was $100,000"
            ),
            Scenario(
                scenario_name="Lower Credit Score",
                changes={"credit_score": 650},
                description="If credit score was 650"
            ),
            Scenario(
                scenario_name="Higher Debt",
                changes={"liabilities": 25000},
                description="If liabilities were $25,000"
            )
        ]
        
        # Run what-if analysis
        results = await client.what_if_analysis("APP-001", scenarios)
        
        # Display original decision
        print("Original Decision:")
        orig = results['original_decision']
        print(f"  Classification: {orig['classification']}")
        print(f"  Risk Score: {orig['risk_score']:.1f}")
        print(f"  Approval Probability: {orig['approval_probability']:.0%}")
        
        # Show scenario impacts
        print("\nScenario Analysis:")
        for scenario in results['scenarios']:
            print(f"\n  {scenario['scenario_name']}:")
            print(f"    New Classification: {scenario['predicted_classification']}")
            print(f"    New Risk Score: {scenario['predicted_risk_score']:.1f}")
            print(f"    Impact: {scenario['decision_impact']}")
        
        # Display insights
        print("\nKey Insights:")
        for insight in results['insights']:
            print(f"  • {insight}")

asyncio.run(main())
```

**Using cURL:**
```bash
curl -X POST http://localhost:8001/api/v2/applications/APP-001/what-if \
  -H "Content-Type: application/json" \
  -d '{
    "scenarios": [
      {
        "scenario_name": "Higher Income",
        "changes": {"annual_income": 100000},
        "description": "If income increased"
      }
    ],
    "base_application_id": "APP-001"
  }'
```

---

### Example 5: WebSocket Live Updates

**Using Python Client:**
```python
import asyncio
from api_v2_client import LoanApplicationAPIv2Client

async def handle_message(message):
    """Handle incoming messages."""
    msg_type = message.get('type')
    
    if msg_type == 'batch_progress':
        pct = message.get('percentage', 0)
        print(f"Batch Progress: {pct:.1f}%")
    
    elif msg_type == 'application_processed':
        print(f"Application {message['case_id']}: {message['classification']}")
    
    elif msg_type == 'status':
        print(f"Status: {message['message']}")

async def main():
    client = LoanApplicationAPIv2Client()
    async with client:
        # Connect to WebSocket and listen for updates
        await client.websocket_live_updates(
            handle_message,
            topics=['batch_processing', 'applications']
        )

asyncio.run(main())
```

**Using JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/live-updates');

ws.onopen = () => {
    console.log('Connected to live updates');
    
    // Subscribe to batch processing updates
    ws.send(JSON.stringify({
        action: 'subscribe',
        topic: 'batch_processing'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'batch_progress':
            console.log(`Progress: ${data.percentage.toFixed(1)}%`);
            break;
        case 'application_processed':
            console.log(`Application processed: ${data.case_id}`);
            break;
        default:
            console.log('Message:', data);
    }
};

ws.onerror = (error) => console.error('WebSocket error:', error);
ws.onclose = () => console.log('Connection closed');
```

---

## Common Use Cases

### Use Case 1: Real-Time Dashboard

```python
import asyncio
from api_v2_client import LoanApplicationAPIv2Client

async def update_dashboard():
    """Update dashboard with real-time metrics."""
    client = LoanApplicationAPIv2Client()
    
    async with client:
        while True:
            analytics = await client.get_analytics()
            metrics = analytics['metrics']
            
            # Update dashboard
            print(f"\n{'='*50}")
            print(f"LOAN DECISION DASHBOARD")
            print(f"{'='*50}")
            print(f"Total Applications: {metrics['total_applications']}")
            print(f"Approved: {metrics['approved_count']} ({metrics['approval_rate']:.1%})")
            print(f"Rejected: {metrics['rejected_count']}")
            print(f"Manual Review: {metrics['manual_review_count']}")
            print(f"Avg Processing Time: {metrics['average_processing_time_ms']:.0f}ms")
            print(f"Avg Risk Score: {metrics['average_risk_score']:.1f}")
            
            # Refresh every 30 seconds
            await asyncio.sleep(30)

asyncio.run(update_dashboard())
```

### Use Case 2: Batch Processing with Progress Tracking

```python
async def process_bulk_applications(csv_file):
    """Process applications from CSV with progress tracking."""
    import csv
    
    client = LoanApplicationAPIv2Client()
    
    async with client:
        # Read CSV
        applications = []
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                applications.append({
                    "applicant_id": row['id'],
                    "profile": {
                        "name": row['name'],
                        "age": int(row['age']),
                        "employment_status": row['employment'],
                        "employment_years": int(row['years']),
                        "education_level": row['education'],
                        "annual_income": float(row['income']),
                        "monthly_expenses": float(row['expenses']),
                        "savings": float(row['savings']),
                        "existing_loans": int(row['loans'])
                    },
                    "credit_score": int(row['credit_score']),
                    "loan_amount": float(row['loan_amount']),
                    "tenure": int(row['tenure']),
                    "liabilities": float(row['liabilities']),
                    "location": row['location']
                })
        
        # Submit batch
        print(f"Submitting {len(applications)} applications...")
        result = await client.submit_batch(applications, priority="high")
        
        # Monitor progress
        while True:
            status = await client.get_batch_status(result.batch_id)
            processed = status.get('processed', 0)
            total = status['total_applications']
            
            pct = (processed / total) * 100 if total > 0 else 0
            print(f"Progress: [{int(pct/5)*'='}{' '*(20-int(pct/5))}] {pct:.0f}%")
            
            if status['status'] == 'completed':
                break
            
            await asyncio.sleep(5)
        
        print("Batch processing completed!")

asyncio.run(process_bulk_applications('applications.csv'))
```

### Use Case 3: Decision Explainability for Appeals

```python
async def generate_appeal_package(application_id):
    """Generate detailed explanation for customer appeal."""
    client = LoanApplicationAPIv2Client()
    
    async with client:
        # Get detailed explanation
        explanation = await client.get_explainability(application_id)
        
        # Get what-if scenarios for improvement
        from api_v2_client import Scenario
        scenarios = [
            Scenario("Improve Credit", {"credit_score": 700}),
            Scenario("Increase Income", {"annual_income": 90000}),
            Scenario("Lower Debt", {"liabilities": 5000})
        ]
        what_if = await client.what_if_analysis(application_id, scenarios)
        
        # Generate report
        report = f"""
LOAN DECISION APPEAL PACKAGE
Application ID: {application_id}

ORIGINAL DECISION
-----------------
Classification: {explanation['classification']}
Risk Score: {explanation['risk_score']:.1f}/100

KEY FACTORS
-----------
{chr(10).join(f"- {f['factor_name']}: {f['explanation']}" for f in explanation['key_factors'])}

HOW TO IMPROVE YOUR DECISION
-----------------------------
{chr(10).join(f"- {s['scenario_name']}: Would result in {s['predicted_classification']}" for s in what_if['scenarios'])}

COMPLIANCE STATUS
-----------------
{chr(10).join(f"✓ {flag}" for flag in explanation['regulatory_flags'])}
        """
        
        return report

# Usage
import asyncio
report = asyncio.run(generate_appeal_package("APP-001"))
print(report)
```

---

## Running Tests

```bash
# All tests
pytest test_api_v2.py -v

# Specific endpoint tests
pytest test_api_v2.py::test_analytics_last_7_days -v
pytest test_api_v2.py::test_batch_submit_multiple_applications -v
pytest test_api_v2.py::test_explainability_key_factors -v
pytest test_api_v2.py::test_what_if_multiple_scenarios -v

# With coverage
pytest test_api_v2.py --cov=api_v2 --cov-report=html
```

---

## Performance Tips

### 1. Batch Processing
- Group applications in batches of 10-100 for optimal performance
- Use `priority="high"` for time-critical batches
- Monitor batch status asynchronously without blocking

### 2. Analytics Queries
- Use shorter time periods (`last_24_hours`) for real-time dashboards
- Cache analytics results when possible
- Request only needed periods to reduce load

### 3. WebSocket Connections
- Subscribe only to relevant topics to reduce message volume
- Implement reconnection logic for stability
- Use connection pooling for multiple clients

### 4. Explainability Requests
- Set `include_alternatives=False` if not needed
- Cache results for frequently accessed applications
- Batch multiple explainability requests together

---

## Troubleshooting

### Issue: Connection Refused
```
Error: Connection refused on localhost:8001
```
**Solution:** Make sure API server is running
```bash
python api_v2.py
```

### Issue: WebSocket Connection Timeout
```
Error: WebSocket connection timeout
```
**Solution:** Check firewall settings and ensure WebSocket port is open

### Issue: Batch Processing Slow
```
Batch taking longer than expected
```
**Solution:** Check system resources and reduce batch size

### Issue: Invalid Application Data
```
Validation error: credit_score must be between 300 and 850
```
**Solution:** Validate input data before submission
```python
assert 300 <= app['credit_score'] <= 850
assert app['loan_amount'] > 0
```

---

## Next Steps

1. **Read Full Documentation**: See `API_V2_DOCUMENTATION.md` for complete API reference
2. **Explore Interactive Docs**: Visit http://localhost:8001/api/v2/docs
3. **Run Examples**: Execute `python api_v2_client.py` for full workflow
4. **Run Tests**: Execute `pytest test_api_v2.py -v`
5. **Integrate**: Use client library in your applications

---

## Support

For issues and questions:
1. Check this quickstart guide
2. Review full documentation
3. Examine test cases for usage patterns
4. Check API interactive documentation at `/api/v2/docs`

---

## Example Scripts

All example scripts are included in the repository:

- `api_v2.py` - Main API server
- `api_v2_client.py` - Python client library with examples
- `test_api_v2.py` - Comprehensive test suite

Run the client with examples:
```bash
python api_v2_client.py
```

This will demonstrate all 5 endpoints with realistic data.
