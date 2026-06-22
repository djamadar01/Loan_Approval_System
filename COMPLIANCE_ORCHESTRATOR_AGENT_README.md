# ComplianceOrchestratorAgent

## Overview

The **ComplianceOrchestratorAgent** is a sophisticated agent that orchestrates compliance decisions, integrates with the NotificationSystem MCP server, and maintains comprehensive audit trails. It automates the process of evaluating compliance for applicants, generating unique Case IDs, dispatching notifications, and maintaining an immutable audit trail of all decisions and actions.

## Features

### Core Capabilities

1. **Compliance Decision Processing**
   - Evaluates compliance based on configurable criteria
   - Generates decisions with confidence scores
   - Supports multiple compliance statuses (COMPLIANT, NON_COMPLIANT, PARTIAL_COMPLIANCE)
   - Automatically classifies decision types (APPROVAL, REJECTION, ESCALATION, REVIEW_REQUIRED)

2. **Case ID Generation**
   - Generates unique, trackable Case IDs
   - Format: `NOTIF-YYYYMMDD-XXXXXX` (date-based with random component)
   - Persistent storage of Case ID metadata
   - Registration and tracking of all cases

3. **Notification Management**
   - Sends tailored notifications based on decision type
   - Adaptive notification dispatch (decision, escalation, review notifications)
   - Configurable priorities (normal, high, critical)
   - Notification status tracking and response logging

4. **Audit Trail Maintenance**
   - Immutable audit logging of all actions
   - JSONL-based audit trail storage
   - Comprehensive action tracking (decision_processing_initiated, compliance_evaluation_completed, etc.)
   - Actor tracking (agent ID) for all actions
   - Success/failure result recording

5. **Summary Generation**
   - Comprehensive decision summaries
   - Structured output with all relevant metadata
   - JSON export capabilities
   - Human-readable summary generation

6. **Query and Retrieval**
   - Retrieve decision summaries by Case ID
   - List all decisions processed
   - Get comprehensive case status
   - Generate agent statistics

## Data Models

### ComplianceStatus (Enum)
```python
COMPLIANT = "compliant"              # Fully compliant
NON_COMPLIANT = "non_compliant"      # Major violations
PARTIAL_COMPLIANCE = "partial_compliance"  # Minor issues, needs review
UNKNOWN = "unknown"                  # Insufficient data
```

### DecisionType (Enum)
```python
APPROVAL = "approval"                # Application approved
REJECTION = "rejection"              # Application rejected
ESCALATION = "escalation"            # Requires escalation
REVIEW_REQUIRED = "review_required"  # Manual review needed
PENDING = "pending"                  # Decision pending
```

### DecisionSummary (Data Class)
Complete summary of a compliance decision including:
- `case_id`: Unique Case ID
- `timestamp`: ISO 8601 timestamp
- `subject`: Decision subject
- `applicant_id`: Applicant identifier
- `compliance_status`: ComplianceStatus enum value
- `decision`: ComplianceDecision object
- `notifications_sent`: List of notification responses
- `audit_entries`: List of audit trail entries
- `message_id`: Unique message ID
- `summary_text`: Human-readable summary

### ComplianceDecision (Data Class)
```python
@dataclass
class ComplianceDecision:
    decision_type: DecisionType          # Type of decision
    rationale: str                       # Explanation
    confidence_score: float              # 0-100
    rule_violations: List[str]           # Violations identified
    risk_factors: List[str]              # Risk factors
    metadata: Dict[str, Any]             # Additional metadata
```

## Installation

### Prerequisites
```bash
pip install fastmcp pydantic httpx
```

### Import
```python
from compliance_orchestrator_agent import (
    ComplianceOrchestratorAgent,
    DecisionType,
    ComplianceStatus,
    DecisionSummary,
    create_agent
)
```

## Usage

### Basic Usage

#### 1. Create an Agent
```python
from compliance_orchestrator_agent import create_agent

# Create with auto-generated ID
agent = create_agent()

# Or with custom ID
agent = create_agent("CUSTOM-COMPLIANCE-AGENT")
```

#### 2. Process a Compliance Decision
```python
# Prepare compliance data
compliance_data = {
    "compliance_score": 85,
    "rule_violations": [],
    "risk_factors": []
}

# Process decision
summary = agent.process_compliance_decision(
    applicant_id="APP-001",
    applicant_email="applicant@example.com",
    subject="Compliance Review - Application APP-001",
    compliance_data=compliance_data,
    decision_criteria={}  # Optional
)

# Access results
print(f"Case ID: {summary.case_id}")
print(f"Status: {summary.compliance_status.value}")
print(f"Decision: {summary.decision.decision_type.value}")
print(f"Confidence: {summary.decision.confidence_score}%")
```

#### 3. Retrieve Decision Information
```python
# Get decision summary by Case ID
decision = agent.get_decision_summary(case_id)
print(decision.to_json())

# Get comprehensive case status
case_status = agent.get_case_status(case_id)
print(f"Audit entries: {case_status['audit_entries_count']}")

# List all decisions
all_decisions = agent.list_all_decisions()
for case_id, summary in all_decisions.items():
    print(f"{case_id}: {summary.compliance_status.value}")
```

#### 4. Access Audit Trail
```python
# Get audit trail for a specific case
audit_trail = agent.get_audit_trail(case_id)
for entry in audit_trail:
    print(f"{entry['timestamp']}: {entry['action']} ({entry['result']})")

# Get all audit entries
all_entries = agent.get_all_audit_entries()
```

#### 5. Get Agent Statistics
```python
stats = agent.get_agent_statistics()
print(f"Total decisions: {stats['total_decisions']}")
print(f"Total audit entries: {stats['total_audit_entries']}")
print(f"Decision distribution: {stats['decision_types_distribution']}")
print(f"Compliance distribution: {stats['compliance_status_distribution']}")
```

### Advanced Usage

#### Scenario 1: Fully Compliant Application
```python
compliance_data = {
    "compliance_score": 95,
    "rule_violations": [],
    "risk_factors": []
}

summary = agent.process_compliance_decision(
    applicant_id="APP-COMPLIANT",
    applicant_email="compliant@example.com",
    subject="Compliance Check",
    compliance_data=compliance_data
)

# Result:
# - Status: COMPLIANT
# - Decision: APPROVAL
# - Confidence: 95.0%
# - Notifications: 1 (decision notification)
```

#### Scenario 2: Non-Compliant Application (Escalation)
```python
compliance_data = {
    "compliance_score": 25,
    "rule_violations": ["Missing tax documentation", "Identity verification failed"],
    "risk_factors": ["High-risk jurisdiction", "Suspicious activity patterns"]
}

summary = agent.process_compliance_decision(
    applicant_id="APP-ESCALATE",
    applicant_email="escalate@example.com",
    subject="Compliance Check",
    compliance_data=compliance_data
)

# Result:
# - Status: NON_COMPLIANT
# - Decision: ESCALATION
# - Confidence: 90.0%
# - Notifications: 2 (decision + escalation notifications)
# - Audit: Escalation action logged
```

#### Scenario 3: Partial Compliance (Review Required)
```python
compliance_data = {
    "compliance_score": 70,
    "rule_violations": ["Income verification pending"],
    "risk_factors": ["Recent employment change"]
}

summary = agent.process_compliance_decision(
    applicant_id="APP-REVIEW",
    applicant_email="review@example.com",
    subject="Compliance Check",
    compliance_data=compliance_data
)

# Result:
# - Status: PARTIAL_COMPLIANCE
# - Decision: REVIEW_REQUIRED
# - Confidence: 75.0%
# - Notifications: 2 (decision + review notifications)
```

## Audit Trail

The agent maintains a comprehensive audit trail in `audit_logs/notifications.jsonl`. Each entry includes:

```json
{
  "timestamp": "2026-06-18T10:49:28.532003+00:00",
  "case_id": "NOTIF-20260618-D93D05",
  "action": "decision_processing_initiated",
  "actor": "COMP-AGENT-3AE8B9",
  "details": {
    "applicant_id": "APP-001",
    "subject": "Compliance Review"
  },
  "result": "pending"
}
```

### Tracked Actions
- `decision_processing_initiated`: Decision processing started
- `compliance_evaluation_completed`: Compliance evaluation finished
- `notifications_dispatched`: All notifications sent
- `decision_processing_completed`: Decision processing finished
- `notification_initiated`: Individual notification started
- `notification_sent`: Individual notification sent successfully
- `notifications_dispatch_failed`: Notification dispatch error

## File Structure

```
audit_logs/
  ├── audit_trail.log           # Comprehensive audit log file
  ├── notifications.jsonl       # JSONL audit entries
  └── case_ids.json            # Case ID registry
```

## Integration with NotificationSystem

The agent uses the NotificationSystem MCP server tools:

### send_notification
Sends notifications with:
- Dynamic subject based on decision type
- Priority levels (normal, high, critical)
- Detailed message content
- Metadata including case ID and confidence score

### get_notification_status
Retrieves notification status and history for tracking

### get_audit_trail
Retrieves audit trail entries for compliance verification

## Decision Logic

### Compliance Evaluation Algorithm

```
if compliance_score >= 80 AND no violations:
    Status: COMPLIANT
    Decision: APPROVAL
    Confidence: 95%

elif compliance_score >= 60 AND violations <= 2:
    Status: PARTIAL_COMPLIANCE
    Decision: REVIEW_REQUIRED
    Confidence: 75%

elif violations OR compliance_score < 40:
    Status: NON_COMPLIANT
    Decision: ESCALATION
    Confidence: 90%

else:
    Status: UNKNOWN
    Decision: PENDING
    Confidence: 50%
```

## API Reference

### ComplianceOrchestratorAgent Methods

#### process_compliance_decision()
```python
def process_compliance_decision(
    applicant_id: str,
    applicant_email: str,
    subject: str,
    compliance_data: Dict[str, Any],
    decision_criteria: Optional[Dict[str, Any]] = None
) -> DecisionSummary
```
Process a compliance decision and coordinate notifications.

**Parameters:**
- `applicant_id`: Unique applicant identifier
- `applicant_email`: Applicant email for notifications
- `subject`: Decision subject
- `compliance_data`: Compliance evaluation data
- `decision_criteria`: Optional decision criteria

**Returns:** DecisionSummary with case ID and decision details

---

#### get_decision_summary()
```python
def get_decision_summary(case_id: str) -> Optional[DecisionSummary]
```
Retrieve a decision summary by case ID.

---

#### get_case_status()
```python
def get_case_status(case_id: str) -> Optional[Dict[str, Any]]
```
Get comprehensive status for a case including audit trail.

---

#### get_audit_trail()
```python
def get_audit_trail(case_id: str) -> List[Dict[str, Any]]
```
Retrieve audit trail entries for a specific case.

---

#### get_all_audit_entries()
```python
def get_all_audit_entries() -> List[Dict[str, Any]]
```
Retrieve all audit entries across all cases.

---

#### list_all_decisions()
```python
def list_all_decisions() -> Dict[str, DecisionSummary]
```
List all decisions processed by the agent.

---

#### get_agent_statistics()
```python
def get_agent_statistics() -> Dict[str, Any]
```
Get statistics about agent operations.

## Testing

Run the test suite:

```bash
# Run with pytest (if installed)
pytest test_compliance_orchestrator_agent.py -v

# Or run manually
python test_compliance_orchestrator_agent.py
```

### Test Coverage
- Agent creation and initialization
- Compliant, non-compliant, and partial compliance decisions
- Case ID generation and uniqueness
- Notification dispatch (decision, escalation, review)
- Audit trail logging
- Decision summary generation and validation
- Message ID generation
- JSON export functionality
- Confidence score calculation
- Case status retrieval
- Agent statistics
- End-to-end workflow

## Example Output

### DecisionSummary JSON Export
```json
{
  "case_id": "NOTIF-20260618-D93D05",
  "timestamp": "2026-06-18T10:49:28.532003+00:00",
  "subject": "Compliance Review - Application APP-001",
  "applicant_id": "APP-001",
  "compliance_status": "compliant",
  "decision": {
    "decision_type": "approval",
    "rationale": "Compliance Score: 95.0/100; No violations detected; No significant risk factors",
    "confidence_score": 95.0,
    "rule_violations": [],
    "risk_factors": [],
    "metadata": {
      "compliance_score": 95,
      "rule_violations": [],
      "risk_factors": []
    }
  },
  "notifications_sent": [
    {
      "type": "decision",
      "case_id": "NOTIF-20260618-D93D05",
      "recipient": "applicant@example.com",
      "timestamp": "2026-06-18T10:49:28.532003+00:00"
    }
  ],
  "audit_entries": [...],
  "message_id": "MSG-COMP-20260618104928-A1B2C3",
  "summary_text": "COMPLIANCE DECISION SUMMARY\n..."
}
```

### Case Status Response
```json
{
  "case_id": "NOTIF-20260618-D93D05",
  "case_info": {
    "timestamp": "2026-06-18T10:49:28.532003+00:00",
    "recipient": "applicant@example.com",
    "subject": "Compliance Review - Application APP-001",
    "notification_type": "compliance_decision"
  },
  "audit_trail": [
    {
      "timestamp": "2026-06-18T10:49:28.532003+00:00",
      "case_id": "NOTIF-20260618-D93D05",
      "action": "decision_processing_initiated",
      "actor": "COMP-AGENT-3AE8B9",
      "details": {...},
      "result": "pending"
    },
    ...
  ],
  "audit_entries_count": 4,
  "decision": {...}
}
```

## Best Practices

1. **Case ID Preservation**: Always store and reference Case IDs for audit and compliance verification

2. **Notification Monitoring**: Track notification delivery status through the audit trail

3. **Audit Trail Review**: Regularly review audit trails for compliance monitoring

4. **Decision Criteria**: Clearly define decision criteria for consistent evaluations

5. **Error Handling**: Wrap agent calls in try-except blocks for production use

6. **Statistics Tracking**: Use agent statistics for compliance reporting

## Performance Considerations

- Case ID generation: O(1) operation
- Audit trail queries: O(n) where n = number of audit entries
- Decision history: In-memory storage (scales with decision count)
- Notification dispatch: Asynchronous (does not block agent)

## Future Enhancements

- Database backend for persistent storage
- Async/await support for non-blocking operations
- Batch decision processing
- Machine learning integration for confidence scoring
- Real-time notification webhook support
- Advanced query and filtering capabilities
- Role-based access control for audit trails
- Data export in multiple formats (CSV, XML)

## License

This implementation follows the same licensing as the broader project.

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review audit logs for action history
3. Verify Case IDs and decision summaries
4. Check agent statistics for operational insights
