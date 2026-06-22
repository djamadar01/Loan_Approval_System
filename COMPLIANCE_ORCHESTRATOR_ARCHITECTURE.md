# ComplianceOrchestratorAgent - Architecture & Implementation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  ComplianceOrchestratorAgent                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Main Orchestration Methods                   │   │
│  │  - process_compliance_decision()                         │   │
│  │  - get_decision_summary()                                │   │
│  │  - get_case_status()                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│        ┌─────────────────┼─────────────────┐                     │
│        │                 │                 │                     │
│        ▼                 ▼                 ▼                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Compliance  │  │ Notification │  │ Audit Trail  │          │
│  │  Evaluation  │  │  Management  │  │  Management  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│        │                 │                 │                     │
│        └─────────────────┼─────────────────┘                     │
│                          │                                        │
└──────────────────────────┼────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
   │  Case ID    │  │ Notification│  │   Audit      │
   │  Manager    │  │  Service    │  │   Trail      │
   │  (FastMCP)  │  │  (FastMCP)  │  │   Manager    │
   │             │  │             │  │   (FastMCP)  │
   └─────────────┘  └─────────────┘  └──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
    ┌─────────────────────────────────────────────────┐
    │         NotificationSystem MCP Server           │
    │                                                  │
    │  - send_notification()                          │
    │  - get_notification_status()                    │
    │  - get_audit_trail()                            │
    │  - list_all_notifications()                     │
    │  - get_system_info()                            │
    └─────────────────────────────────────────────────┘
        │
        ▼
    ┌──────────────────────────────┐
    │      Persistent Storage      │
    │                              │
    │  - audit_logs/               │
    │    ├── audit_trail.log       │
    │    ├── notifications.jsonl   │
    │    └── case_ids.json         │
    └──────────────────────────────┘
```

## Component Details

### 1. ComplianceOrchestratorAgent

The main orchestration class responsible for:

- **Initialization**: Sets up agent ID, notification service, and managers
- **Decision Processing**: Orchestrates the full compliance decision workflow
- **Evaluation**: Evaluates compliance based on provided data
- **Notification Dispatch**: Sends appropriate notifications
- **Audit Logging**: Records all actions to audit trail
- **Query/Retrieval**: Provides access to decisions and audit data

```python
class ComplianceOrchestratorAgent:
    def __init__(self, agent_id: str, notification_service: Optional[NotificationService])
    def process_compliance_decision(...) -> DecisionSummary
    def get_decision_summary(case_id: str) -> Optional[DecisionSummary]
    def get_case_status(case_id: str) -> Optional[Dict[str, Any]]
    def list_all_decisions() -> Dict[str, DecisionSummary]
    def get_audit_trail(case_id: str) -> List[Dict[str, Any]]
    def get_agent_statistics() -> Dict[str, Any]
```

### 2. Compliance Evaluation Module

Evaluates compliance based on:

- **Compliance Score**: Overall numeric assessment (0-100)
- **Rule Violations**: List of identified violations
- **Risk Factors**: List of identified risks

```python
def _evaluate_compliance(
    case_id: str,
    applicant_id: str,
    compliance_data: Dict[str, Any],
    decision_criteria: Optional[Dict[str, Any]]
) -> tuple[ComplianceStatus, ComplianceDecision]
```

#### Evaluation Algorithm

```
Input: compliance_score, rule_violations, risk_factors

if compliance_score >= 80 AND len(violations) == 0:
    COMPLIANT -> APPROVAL (confidence 95%)
    
elif 60 <= compliance_score < 80 AND len(violations) <= 2:
    PARTIAL_COMPLIANCE -> REVIEW_REQUIRED (confidence 75%)
    
elif len(violations) > 0 OR compliance_score < 40:
    NON_COMPLIANT -> ESCALATION (confidence 90%)
    
else:
    UNKNOWN -> PENDING (confidence 50%)
```

### 3. Notification Management Module

Sends three types of notifications:

#### a. Decision Notification (Always Sent)
- Primary notification with decision details
- Includes compliance status and confidence score
- Priority: normal, high, or critical (based on decision type)

#### b. Escalation Notification (For Non-Compliant Cases)
- Critical priority notification
- Indicates need for escalation
- Lists specific violations

#### c. Review Notification (For Partial Compliance Cases)
- High priority notification
- Indicates manual review required
- Lists items requiring review

```python
def _send_notifications(...) -> List[Dict[str, Any]]
    ├── _send_decision_notification(...)
    ├── _send_escalation_notification(...) [if ESCALATION]
    └── _send_review_notification(...) [if REVIEW_REQUIRED]
```

### 4. Audit Trail Management Module

Records every action with:
- **Timestamp**: ISO 8601 timestamp
- **Case ID**: Associated case ID
- **Action**: What was performed
- **Actor**: Agent ID performing action
- **Details**: Detailed context
- **Result**: success, failure, or pending

```python
def _log_action(
    case_id: str,
    action: str,
    details: Dict[str, Any],
    result: str = "success"
) -> None
```

#### Tracked Actions

| Action | Trigger | Details |
|--------|---------|---------|
| decision_processing_initiated | Start of decision | Applicant ID, subject |
| compliance_evaluation_completed | After evaluation | Score, violations, risk factors |
| notifications_dispatched | After sending notifications | Notification count |
| decision_processing_completed | End of decision | Compliance status, decision type |
| notification_initiated | Start of notification | Message ID |
| notification_sent | Notification sent | Recipient, response |

### 5. Case ID Management (FastMCP Integration)

Generates and tracks unique Case IDs:

**Format**: `NOTIF-YYYYMMDD-XXXXXX`
- Date component: 8 digits (YYYYMMDD)
- Random component: 6 hex characters

```python
def generate_case_id() -> str:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    random_component = uuid.uuid4().hex[:6].upper()
    return f"NOTIF-{date_str}-{random_component}"
```

**Storage**: Case ID registry in `audit_logs/case_ids.json`

```json
{
  "NOTIF-20260618-D93D05": {
    "timestamp": "2026-06-18T10:49:28.532003+00:00",
    "recipient": "applicant@example.com",
    "subject": "Compliance Review",
    "notification_type": "compliance_decision"
  }
}
```

## Data Flow

### Decision Processing Flow

```
1. Input: applicant_id, email, subject, compliance_data
   │
   ├─> Generate unique Case ID (NOTIF-20260618-XXXXXX)
   ├─> Log: decision_processing_initiated (PENDING)
   │
   ├─> Evaluate Compliance
   │   ├─> Analyze compliance_score
   │   ├─> Check rule_violations
   │   ├─> Assess risk_factors
   │   └─> Determine: ComplianceStatus + DecisionType
   │
   ├─> Log: compliance_evaluation_completed (SUCCESS)
   ├─> Register Case ID in manager
   │
   ├─> Send Notifications
   │   ├─> Primary decision notification
   │   ├─> [Optional] Escalation notification
   │   └─> [Optional] Review notification
   │
   ├─> Log: notifications_dispatched (SUCCESS)
   ├─> Generate summary_text and message_id
   ├─> Log: decision_processing_completed (SUCCESS)
   │
   └─> Output: DecisionSummary
       ├─> case_id
       ├─> compliance_status
       ├─> decision (type, rationale, confidence)
       ├─> notifications_sent
       ├─> audit_entries
       └─> summary_text
```

## Integration with NotificationSystem MCP

### Tool Calls Made

1. **send_notification()** (via NotificationService)
   - Sends primary, escalation, and review notifications
   - Each call generates its own Case ID in the notification system
   - Returns notification response with case ID

2. **Case ID Manager** (via NotificationService)
   - Registers Case IDs with metadata
   - Retrieves case information
   - Lists all cases

3. **Audit Trail Manager** (via NotificationService)
   - Logs all actions to JSONL audit trail
   - Retrieves audit trail for specific case
   - Retrieves all audit entries

### Data Structures

#### ComplianceDecision
```python
@dataclass
class ComplianceDecision:
    decision_type: DecisionType          # APPROVAL/ESCALATION/REVIEW_REQUIRED
    rationale: str                       # Explanation
    confidence_score: float              # 0-100
    rule_violations: List[str]           # Identified violations
    risk_factors: List[str]              # Risk factors
    metadata: Dict[str, Any]             # Original compliance_data
```

#### DecisionSummary
```python
@dataclass
class DecisionSummary:
    case_id: str                         # Unique identifier
    timestamp: str                       # ISO 8601
    subject: str                         # Decision subject
    applicant_id: str                    # Applicant identifier
    compliance_status: ComplianceStatus  # Status enum
    decision: ComplianceDecision         # The decision
    notifications_sent: List[Dict]       # Notification responses
    audit_entries: List[AuditTrailEntry] # Audit trail
    message_id: Optional[str]            # Message ID
    summary_text: Optional[str]          # Human-readable summary
```

## Validation & Error Handling

### Validation Chain

```python
process_compliance_decision()
├─> Validate applicant_id (non-empty string)
├─> Validate applicant_email (non-empty string)
├─> Validate subject (non-empty string)
├─> Validate compliance_data (dict with required fields)
│
└─> After processing:
    └─> summary.validate()
        ├─> Validate case_id
        ├─> Validate applicant_id
        ├─> Validate compliance_status
        ├─> Validate decision (recursive)
        └─> Validate audit_entries (each entry)
```

### Exception Handling

```python
class ValidationError(Exception)
    """Data validation errors"""

class AgentError(Exception)
    """Agent operation errors"""
    
try:
    summary = agent.process_compliance_decision(...)
except ValidationError as e:
    # Handle validation error
    log.error(f"Validation error: {e}")
except AgentError as e:
    # Handle agent error
    log.error(f"Agent error: {e}")
```

## Performance Characteristics

| Operation | Time Complexity | Space Complexity | Notes |
|-----------|-----------------|------------------|-------|
| generate_case_id() | O(1) | O(1) | Constant time UUID generation |
| process_compliance_decision() | O(1) | O(n) | n = audit entries for case |
| get_decision_summary() | O(1) | O(1) | In-memory lookup |
| get_audit_trail() | O(m) | O(m) | m = audit entries in file |
| list_all_decisions() | O(d) | O(d) | d = total decisions |
| get_agent_statistics() | O(d+m) | O(1) | d = decisions, m = entries |

## Extensibility Points

### 1. Custom Decision Criteria
```python
decision_criteria = {
    "min_score": 70,
    "max_violations": 3,
    "critical_risk_factors": ["fraud", "sanctions"]
}

summary = agent.process_compliance_decision(
    ...,
    decision_criteria=decision_criteria
)
```

### 2. Custom Compliance Evaluation
Subclass and override `_evaluate_compliance()`:
```python
class CustomComplianceAgent(ComplianceOrchestratorAgent):
    def _evaluate_compliance(self, ...):
        # Custom logic
        return compliance_status, decision
```

### 3. Custom Notification Templates
Override `_send_*_notification()` methods:
```python
class CustomNotificationAgent(ComplianceOrchestratorAgent):
    def _send_decision_notification(self, ...):
        # Custom message format
        message = "Custom template..."
        ...
```

### 4. Custom Audit Logging
Override `_log_action()`:
```python
class CustomAuditAgent(ComplianceOrchestratorAgent):
    def _log_action(self, ...):
        # Custom logging logic
        super()._log_action(...)
        # Additional logging
```

## File Organization

```
demo/
├── compliance_orchestrator_agent.py
│   ├── ComplianceOrchestratorAgent (main class)
│   ├── DecisionType (enum)
│   ├── ComplianceStatus (enum)
│   ├── DecisionSummary (dataclass)
│   ├── ComplianceDecision (dataclass)
│   ├── AuditTrailEntry (dataclass)
│   └── Utility functions
│
├── test_compliance_orchestrator_agent.py
│   ├── TestComplianceOrchestratorAgent (test class)
│   ├── Integration tests
│   └── Manual test runner
│
├── COMPLIANCE_ORCHESTRATOR_AGENT_README.md
│   └── Full documentation
│
├── COMPLIANCE_ORCHESTRATOR_QUICK_START.md
│   └── Quick start guide
│
├── COMPLIANCE_ORCHESTRATOR_ARCHITECTURE.md
│   └── This file
│
└── audit_logs/
    ├── audit_trail.log         # Text log file
    ├── notifications.jsonl     # JSONL audit entries
    └── case_ids.json          # Case ID registry
```

## Security Considerations

1. **Audit Trail Immutability**
   - Append-only JSONL format
   - Timestamps recorded with UTC timezone
   - Actor identification for all actions

2. **Case ID Uniqueness**
   - Date-based prefix prevents collisions
   - Random hex component for uniqueness
   - Stored persistently

3. **Notification Security**
   - Metadata included with notifications
   - Case ID tracking for verification
   - Priority levels for sensitive decisions

4. **Error Handling**
   - Failures logged but don't halt processing
   - Exceptions caught and logged appropriately
   - Audit trail maintains record of failures

## Logging Strategy

### Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for data issues
- **ERROR**: Error conditions with stack traces

### Log Destinations

1. **audit_trail.log**: General audit information
2. **notifications.jsonl**: Structured audit entries
3. **Console output**: Real-time operational feedback

## Testing Strategy

```
Unit Tests (test_compliance_orchestrator_agent.py)
├── Agent Creation
│   ├── test_agent_creation()
│   └── test_agent_custom_id()
│
├── Decision Processing
│   ├── test_process_compliant_decision()
│   ├── test_process_non_compliant_decision()
│   └── test_process_partial_compliance_decision()
│
├── Case Management
│   ├── test_case_id_generation()
│   ├── test_get_decision_summary()
│   └── test_get_case_status()
│
├── Notification Management
│   ├── test_notifications_sent()
│   ├── test_escalation_notifications()
│   └── test_review_notifications()
│
├── Audit Trail
│   ├── test_audit_trail_logged()
│   └── test_get_agent_statistics()
│
├── Data Management
│   ├── test_decision_summary_json_export()
│   ├── test_confidence_scores()
│   └── test_decision_summary_validation()
│
└── Integration Tests
    └── test_end_to_end_workflow()
```

## Future Enhancements

1. **Database Backend**
   - Replace JSONL with relational database
   - Support for complex queries
   - Data archival and retention policies

2. **Async/Await Support**
   - Non-blocking notification dispatch
   - Concurrent decision processing
   - Improved scalability

3. **Machine Learning Integration**
   - Dynamic confidence scoring
   - Pattern-based rule violations
   - Anomaly detection

4. **Advanced Querying**
   - Date range queries
   - Status-based filtering
   - Compliance trend analysis

5. **Real-time Webhooks**
   - Event-driven notification dispatch
   - External system integration
   - Custom action triggers

6. **Role-Based Access Control**
   - Audit trail visibility controls
   - Decision approval workflows
   - Permission-based queries

## Deployment Considerations

### Development
- In-memory decision history
- Local file-based audit logs
- No authentication required

### Production
- Replace in-memory storage with database
- Implement rotation for audit logs
- Add authentication/authorization
- Enable structured logging to centralized system
- Implement metrics collection
- Add health check endpoints
- Set up alerting for critical failures

### Scalability
- Move audit logs to distributed storage
- Cache frequently accessed case IDs
- Implement batch processing for multiple decisions
- Add message queue for notification dispatch
- Monitor decision processing latency
