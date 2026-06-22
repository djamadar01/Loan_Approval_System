#!/usr/bin/env python3
"""
Example client for the NotificationSystem MCP Server.
Demonstrates all four core tools in production workflows.
"""

import asyncio
import json
from anthropic import Anthropic

# Initialize client
client = Anthropic()


async def run_notification_workflow():
    """
    Demonstrate a complete notification system workflow:
    1. Create case record
    2. Log compliance action
    3. Send decision notification
    4. Generate summary report
    """

    # System prompt that instructs Claude to use the MCP tools
    system_prompt = """You are a compliance notification system operator. Your role is to:
1. Create case records for customer complaints and incidents
2. Log compliance actions for audit trails
3. Send notifications about decisions and resolutions
4. Generate summary reports for regulatory compliance

Use the available tools to complete these tasks. Always ensure case IDs exist before
referencing them in notifications or compliance logs."""

    # Example workflow messages
    messages = [
        {
            "role": "user",
            "content": """Please execute the following workflow:
1. Create a case record: complaint from customer John Doe about data handling, HIGH priority
2. Log a GDPR compliance review action with actor "compliance_officer_01"
3. Send a decision notification confirming data protection review completion
4. Generate a daily summary report for the last 7 days

Make sure to extract the case ID from step 1 and use it in subsequent steps."""
        }
    ]

    # Define tools for the MCP server
    tools = [
        {
            "type": "function",
            "function": {
                "name": "create_case_record",
                "description": "Create a new case record with unique Case ID generation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "case_type": {"type": "string", "description": "COMPLAINT, INCIDENT, or REQUEST"},
                        "subject": {"type": "string", "description": "Case subject"},
                        "description": {"type": "string", "description": "Detailed description"},
                        "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                        "assigned_to": {"type": "string", "description": "Assigned person/team"}
                    },
                    "required": ["case_type", "subject"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_decision_notification",
                "description": "Send a decision notification",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string", "description": "Case ID"},
                        "recipient_email": {"type": "string", "description": "Recipient email"},
                        "notification_type": {"type": "string", "enum": ["DECISION", "UPDATE", "RESOLUTION", "ESCALATION"]},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body"}
                    },
                    "required": ["case_id", "recipient_email", "notification_type", "subject", "body"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "log_compliance_action",
                "description": "Log a compliance action",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string", "description": "Case ID"},
                        "action_type": {"type": "string", "description": "REVIEW, APPROVAL, REJECTION, etc"},
                        "regulation": {"type": "string", "description": "GDPR, CCPA, SOC2, etc"},
                        "actor": {"type": "string", "description": "Person/system performing action"},
                        "description": {"type": "string", "description": "Action details"},
                        "evidence_hash": {"type": "string", "description": "Optional hash"},
                        "tags": {"type": "string", "description": "Tags"}
                    },
                    "required": ["case_id", "action_type", "regulation", "actor", "description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_summary_report",
                "description": "Generate a summary report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"]},
                        "days_back": {"type": "integer", "description": "Days to include"}
                    }
                }
            }
        }
    ]

    print("=" * 80)
    print("NOTIFICATION SYSTEM - CLIENT WORKFLOW EXAMPLE")
    print("=" * 80)
    print("\nInitiating workflow with Claude using MCP tools...\n")

    # Note: This is a demonstration showing how the client would call the tools.
    # In a production environment, this would be connected to an actual MCP server via stdio.
    print("Example tool calls that would be made:")
    print(json.dumps({
        "step_1": {
            "tool": "create_case_record",
            "params": {
                "case_type": "COMPLAINT",
                "subject": "Customer data handling concern",
                "description": "Customer John Doe reported concerns about personal data handling",
                "priority": "HIGH",
                "assigned_to": "legal_team_01"
            }
        },
        "step_2": {
            "tool": "log_compliance_action",
            "params": {
                "case_id": "[extracted from step 1]",
                "action_type": "REVIEW",
                "regulation": "GDPR",
                "actor": "compliance_officer_01",
                "description": "Conducted comprehensive data protection review per GDPR Article 5"
            }
        },
        "step_3": {
            "tool": "send_decision_notification",
            "params": {
                "case_id": "[extracted from step 1]",
                "recipient_email": "john.doe@example.com",
                "notification_type": "DECISION",
                "subject": "Your Data Protection Review - Decision",
                "body": "We have completed our review and confirmed compliance with all data protection requirements."
            }
        },
        "step_4": {
            "tool": "generate_summary_report",
            "params": {
                "report_type": "DAILY",
                "days_back": 7
            }
        }
    }, indent=2))

    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print("""
This client demonstrates:
✓ Creating a case record with unique ID generation
✓ Logging compliance actions with regulatory tracking
✓ Sending decision notifications
✓ Generating audit reports

To run with the actual MCP server:
1. Start the server: python notification_system_server.py
2. Configure client with MCP over stdio connection
3. Call the tools as shown above
""")


def demonstrate_query_patterns():
    """Show example query patterns for common scenarios."""

    scenarios = {
        "Scenario 1: Data Privacy Complaint": {
            "description": "A customer files a GDPR complaint",
            "tools_used": ["create_case_record", "log_compliance_action", "send_decision_notification"],
            "flow": [
                "Create HIGH priority COMPLAINT case",
                "Log GDPR compliance review action",
                "Send DECISION notification to customer"
            ]
        },
        "Scenario 2: Security Incident Response": {
            "description": "Security team responds to a data breach incident",
            "tools_used": ["create_case_record", "log_compliance_action", "send_decision_notification"],
            "flow": [
                "Create CRITICAL priority INCIDENT case",
                "Log SOC2 compliance action for incident response",
                "Send UPDATE notification to stakeholders"
            ]
        },
        "Scenario 3: Audit & Compliance Reporting": {
            "description": "Monthly compliance report generation",
            "tools_used": ["generate_summary_report"],
            "flow": [
                "Generate MONTHLY report for 30 days",
                "Review cases by status and priority",
                "Export compliance statistics"
            ]
        },
        "Scenario 4: Case Escalation": {
            "description": "Escalate a case to senior management",
            "tools_used": ["log_compliance_action", "send_decision_notification"],
            "flow": [
                "Log escalation compliance action",
                "Send ESCALATION notification to manager",
                "Update case priority to CRITICAL"
            ]
        }
    }

    print("\n" + "=" * 80)
    print("PRODUCTION USE CASE SCENARIOS")
    print("=" * 80)

    for scenario_name, details in scenarios.items():
        print(f"\n{scenario_name}: {details['description']}")
        print(f"  Tools: {', '.join(details['tools_used'])}")
        print(f"  Workflow:")
        for step in details['flow']:
            print(f"    → {step}")


def show_database_schema():
    """Display the database schema."""

    schema = """
DATABASE SCHEMA
===============

tables:
  - cases: Core case records with unique ID tracking
  - notifications: Decision notification logs
  - compliance_actions: Regulatory audit trail
  - summary_reports: Generated compliance reports

CASES TABLE:
  case_id (PK)          - Format: CASE-YYYYMMDD-RANDOM-CHECKSUM
  created_at            - ISO 8601 timestamp
  updated_at            - ISO 8601 timestamp
  case_type             - COMPLAINT, INCIDENT, REQUEST
  status                - OPEN, IN_PROGRESS, RESOLVED, CLOSED
  subject               - Case subject
  description           - Detailed description
  priority              - LOW, MEDIUM, HIGH, CRITICAL
  assigned_to           - Assigned person/team
  case_hash (UNIQUE)    - Deduplication hash

NOTIFICATIONS TABLE:
  notification_id (PK)  - Format: NOTIF-XXXXXXXXXX
  case_id (FK)          - Reference to cases table
  created_at            - ISO 8601 timestamp
  recipient_email       - Email recipient
  notification_type     - DECISION, UPDATE, RESOLUTION, ESCALATION
  status                - SENT, PENDING, FAILED
  subject               - Email subject
  body                  - Email body
  delivery_timestamp    - When sent
  retry_count           - Number of retry attempts

COMPLIANCE_ACTIONS TABLE:
  action_id (PK)        - Format: COMP-XXXXXXXXXX
  case_id (FK)          - Reference to cases table
  created_at            - ISO 8601 timestamp
  action_type           - REVIEW, APPROVAL, REJECTION, ESCALATION
  regulation            - GDPR, CCPA, SOC2, HIPAA, etc
  actor                 - Person/system performing action
  description           - Action details
  evidence_hash         - Hash of supporting evidence
  status                - RECORDED, VERIFIED, APPROVED
  tags                  - Comma-separated tags

SUMMARY_REPORTS TABLE:
  report_id (PK)        - Format: REPORT-XXXXXXXXXX
  created_at            - ISO 8601 timestamp
  report_type           - DAILY, WEEKLY, MONTHLY, QUARTERLY
  total_cases           - Count of cases in period
  cases_by_status       - JSON breakdown by status
  compliance_actions    - Count of logged actions
  notifications_sent    - Count of notifications sent
  high_priority_cases   - Count of HIGH/CRITICAL cases
  report_data           - Full JSON report

INDEXES:
  idx_case_status               - Fast status queries
  idx_case_created              - Fast date range queries
  idx_notification_case         - Fast case lookups
  idx_compliance_case           - Fast compliance lookups
  idx_compliance_regulation     - Fast regulation lookups
"""
    print(schema)


if __name__ == "__main__":
    # Run demonstrations
    asyncio.run(run_notification_workflow())
    demonstrate_query_patterns()
    show_database_schema()
