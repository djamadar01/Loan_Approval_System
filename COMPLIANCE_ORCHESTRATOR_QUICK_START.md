# ComplianceOrchestratorAgent - Quick Start Guide

## 5-Minute Setup

### 1. Import and Create Agent
```python
from compliance_orchestrator_agent import create_agent

agent = create_agent()
```

### 2. Process a Decision
```python
summary = agent.process_compliance_decision(
    applicant_id="APP-001",
    applicant_email="user@example.com",
    subject="Compliance Review",
    compliance_data={
        "compliance_score": 85,
        "rule_violations": [],
        "risk_factors": []
    }
)

print(f"Case ID: {summary.case_id}")
print(f"Status: {summary.compliance_status.value}")
print(f"Decision: {summary.decision.decision_type.value}")
```

### 3. Retrieve Results
```python
# Get decision by Case ID
decision = agent.get_decision_summary(summary.case_id)

# Get all audit entries for this case
audit_trail = agent.get_audit_trail(summary.case_id)

# Get agent statistics
stats = agent.get_agent_statistics()
print(f"Total decisions processed: {stats['total_decisions']}")
```

## Common Scenarios

### Scenario 1: Approve Compliant Application
```python
summary = agent.process_compliance_decision(
    applicant_id="APP-GOOD",
    applicant_email="good@example.com",
    subject="Compliance Review",
    compliance_data={
        "compliance_score": 95,
        "rule_violations": [],
        "risk_factors": []
    }
)
# Result: COMPLIANT -> APPROVAL (95% confidence)
```

### Scenario 2: Escalate Non-Compliant Application
```python
summary = agent.process_compliance_decision(
    applicant_id="APP-BAD",
    applicant_email="bad@example.com",
    subject="Compliance Review",
    compliance_data={
        "compliance_score": 20,
        "rule_violations": ["Fraud detected", "KYC failed"],
        "risk_factors": ["High-risk entity"]
    }
)
# Result: NON_COMPLIANT -> ESCALATION (90% confidence)
# Two notifications sent: decision + escalation
```

### Scenario 3: Request Review for Partial Compliance
```python
summary = agent.process_compliance_decision(
    applicant_id="APP-MAYBE",
    applicant_email="maybe@example.com",
    subject="Compliance Review",
    compliance_data={
        "compliance_score": 65,
        "rule_violations": ["Doc pending"],
        "risk_factors": []
    }
)
# Result: PARTIAL_COMPLIANCE -> REVIEW_REQUIRED (75% confidence)
# Two notifications sent: decision + review
```

## Decision Outcomes

| Compliance Score | Violations | Status | Decision | Confidence | Actions |
|---|---|---|---|---|---|
| >= 80 | None | COMPLIANT | APPROVAL | 95% | 1 notification |
| 60-79 | <= 2 | PARTIAL | REVIEW | 75% | 2 notifications |
| < 60 | Any | NON_COMPLIANT | ESCALATION | 90% | 2 notifications |

## Audit Trail Example

```python
audit_trail = agent.get_audit_trail(case_id)

for entry in audit_trail:
    print(f"{entry['timestamp']}")
    print(f"  Action: {entry['action']}")
    print(f"  Result: {entry['result']}")
    print(f"  Actor: {entry['actor']}")
```

Output:
```
2026-06-18T10:49:28.532003+00:00
  Action: decision_processing_initiated
  Result: pending
  Actor: COMP-AGENT-3AE8B9

2026-06-18T10:49:28.532003+00:00
  Action: compliance_evaluation_completed
  Result: success
  Actor: COMP-AGENT-3AE8B9

...
```

## Access Notification Details

```python
summary = agent.process_compliance_decision(...)

for notification in summary.notifications_sent:
    print(f"Type: {notification['type']}")
    print(f"Recipient: {notification['recipient']}")
    print(f"Timestamp: {notification['timestamp']}")
    print(f"Response: {notification['response']}")
```

## Export to JSON

```python
summary = agent.process_compliance_decision(...)

# Export full decision summary as JSON
json_output = summary.to_json()
print(json_output)

# Or convert to dictionary
decision_dict = summary.to_dict()
```

## Key Properties

### DecisionSummary
- `case_id`: Unique identifier (NOTIF-YYYYMMDD-XXXXXX)
- `timestamp`: ISO 8601 timestamp
- `compliance_status`: COMPLIANT / NON_COMPLIANT / PARTIAL_COMPLIANCE
- `decision.decision_type`: APPROVAL / ESCALATION / REVIEW_REQUIRED
- `decision.confidence_score`: 0-100
- `notifications_sent`: List of notifications
- `audit_entries`: List of audit trail entries
- `message_id`: Unique message identifier
- `summary_text`: Human-readable summary

### ComplianceDecision
- `decision_type`: DecisionType enum
- `rationale`: Explanation of decision
- `confidence_score`: 0-100 score
- `rule_violations`: List of violations
- `risk_factors`: List of risk factors
- `metadata`: Additional data

## Statistics

```python
stats = agent.get_agent_statistics()

print(f"Agent ID: {stats['agent_id']}")
print(f"Total Decisions: {stats['total_decisions']}")
print(f"Total Audit Entries: {stats['total_audit_entries']}")
print(f"Decision Types: {stats['decision_types_distribution']}")
print(f"Compliance Status: {stats['compliance_status_distribution']}")
```

## Case Status Retrieval

```python
case_status = agent.get_case_status(case_id)

print(f"Case ID: {case_status['case_id']}")
print(f"Case Info: {case_status['case_info']}")
print(f"Audit Entries: {case_status['audit_entries_count']}")
print(f"Decision: {case_status['decision']}")
```

## List All Decisions

```python
all_decisions = agent.list_all_decisions()

for case_id, summary in all_decisions.items():
    print(f"{case_id}: {summary.applicant_id} - {summary.compliance_status.value}")
```

## Files Generated

- `audit_logs/audit_trail.log` - Comprehensive audit log
- `audit_logs/notifications.jsonl` - JSONL audit entries
- `audit_logs/case_ids.json` - Case ID registry

## Common Issues

### Issue: Case ID not found
```python
# Make sure you're using the correct case_id from the summary
decision = agent.get_decision_summary(summary.case_id)
```

### Issue: Notifications not sent
```python
# Check that applicant_email is provided
summary = agent.process_compliance_decision(
    applicant_id="APP-001",
    applicant_email="valid@email.com",  # Required
    subject="Review",
    compliance_data={...}
)
```

### Issue: Audit trail empty
```python
# Process a decision first
summary = agent.process_compliance_decision(...)
# Then retrieve audit trail
audit = agent.get_audit_trail(summary.case_id)
```

## Performance Tips

1. Cache decision summaries for frequently accessed cases
2. Batch query audit trails for multiple cases
3. Use agent statistics for reporting instead of iterating all decisions
4. Store Case IDs for quick retrieval

## Next Steps

1. Review `COMPLIANCE_ORCHESTRATOR_AGENT_README.md` for detailed documentation
2. Run `test_compliance_orchestrator_agent.py` to see all features
3. Check `audit_logs/` directory for generated artifacts
4. Integrate with your application using the agent's API

## Code Snippets

### Full Processing Flow
```python
from compliance_orchestrator_agent import create_agent

# Create agent
agent = create_agent("MY-AGENT")

# Process decision
summary = agent.process_compliance_decision(
    applicant_id="APP-001",
    applicant_email="user@example.com",
    subject="Compliance Review",
    compliance_data={
        "compliance_score": 85,
        "rule_violations": [],
        "risk_factors": []
    }
)

# Check result
print(f"Case ID: {summary.case_id}")
print(f"Status: {summary.compliance_status.value}")
print(f"Notifications: {len(summary.notifications_sent)}")

# Retrieve audit trail
audit = agent.get_audit_trail(summary.case_id)
print(f"Audit entries: {len(audit)}")

# Get statistics
stats = agent.get_agent_statistics()
print(f"Total decisions: {stats['total_decisions']}")

# Export
json_output = summary.to_json()
```

### Error Handling
```python
from compliance_orchestrator_agent import create_agent, AgentError

agent = create_agent()

try:
    summary = agent.process_compliance_decision(
        applicant_id="APP-001",
        applicant_email="user@example.com",
        subject="Review",
        compliance_data={...}
    )
except AgentError as e:
    print(f"Agent error: {e}")
```

## Integration Examples

### With Flask Web Service
```python
from flask import Flask, request, jsonify
from compliance_orchestrator_agent import create_agent

app = Flask(__name__)
agent = create_agent()

@app.route('/compliance/decide', methods=['POST'])
def decide():
    data = request.json
    summary = agent.process_compliance_decision(
        applicant_id=data['applicant_id'],
        applicant_email=data['email'],
        subject=data['subject'],
        compliance_data=data['compliance_data']
    )
    return jsonify(summary.to_dict())

@app.route('/compliance/status/<case_id>', methods=['GET'])
def get_status(case_id):
    case_status = agent.get_case_status(case_id)
    return jsonify(case_status)
```

### Batch Processing
```python
applicants = [
    ("APP-001", "user1@example.com", {...}),
    ("APP-002", "user2@example.com", {...}),
    ("APP-003", "user3@example.com", {...}),
]

agent = create_agent()
results = []

for applicant_id, email, compliance_data in applicants:
    summary = agent.process_compliance_decision(
        applicant_id=applicant_id,
        applicant_email=email,
        subject="Batch Review",
        compliance_data=compliance_data
    )
    results.append(summary)

print(f"Processed {len(results)} decisions")
```

## Resources

- Full Documentation: `COMPLIANCE_ORCHESTRATOR_AGENT_README.md`
- Test Suite: `test_compliance_orchestrator_agent.py`
- Implementation: `compliance_orchestrator_agent.py`
- Audit Logs: `audit_logs/`
