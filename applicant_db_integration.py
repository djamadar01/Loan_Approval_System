"""
Integration example: Using ApplicantDB MCP server with Claude API.

This demonstrates how to integrate the ApplicantDB MCP server tools
with the Anthropic Claude API for intelligent applicant analysis.
"""

import json
from mcp_servers.applicant_db import (
    get_applicant_profile,
    list_all_applicants,
    get_applicants_by_risk_level,
    get_applications_requiring_action
)


def create_tool_definitions():
    """Create MCP tool definitions for Claude API."""
    return [
        {
            "name": "get_applicant_profile",
            "description": "Retrieve a complete applicant profile with Income Stability Score (0-100), Employment Risk level, Credit History Summary, and Application Completeness Flags",
            "input_schema": {
                "type": "object",
                "properties": {
                    "applicant_id": {
                        "type": "string",
                        "description": "The unique identifier of the applicant (e.g., 'APP001', 'APP002')"
                    }
                },
                "required": ["applicant_id"]
            }
        },
        {
            "name": "list_all_applicants",
            "description": "List all applicants in the database with their ID, name, email, application status, and application date",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_applicants_by_risk_level",
            "description": "Filter applicants by employment risk level (low, medium, or high). Returns applicants with their risk level, income stability score, and credit score",
            "input_schema": {
                "type": "object",
                "properties": {
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Employment risk level to filter by"
                    }
                },
                "required": ["risk_level"]
            }
        },
        {
            "name": "get_applications_requiring_action",
            "description": "Get all applications with incomplete documentation or documents pending verification. Shows missing fields and required actions",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        }
    ]


def execute_tool(tool_name: str, tool_input: dict):
    """Execute a tool and return the result."""
    if tool_name == "get_applicant_profile":
        return get_applicant_profile(tool_input["applicant_id"])
    elif tool_name == "list_all_applicants":
        return list_all_applicants()
    elif tool_name == "get_applicants_by_risk_level":
        return get_applicants_by_risk_level(tool_input["risk_level"])
    elif tool_name == "get_applications_requiring_action":
        return get_applications_requiring_action()
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def format_tool_result(result):
    """Format tool result as JSON for Claude."""
    return json.dumps(result, indent=2, default=str)


def demonstrate_claude_integration():
    """Demonstrate how Claude would interact with ApplicantDB tools."""

    print("\n" + "=" * 70)
    print("  ApplicantDB + Claude API Integration Example")
    print("=" * 70 + "\n")

    # Example 1: Analysis of a specific applicant
    print("Example 1: Claude analyzes a specific applicant")
    print("-" * 70)

    tool_call = {
        "name": "get_applicant_profile",
        "arguments": {"applicant_id": "APP003"}
    }

    print(f"\nClaude's tool call: {json.dumps(tool_call, indent=2)}")

    result = execute_tool(tool_call["name"], tool_call["arguments"])

    print(f"\nTool response:\n{format_tool_result(result)}")

    # Simulate Claude's analysis
    print("\n[Claude's Analysis]")
    print("""
Carol Davis (APP003) presents a HIGH-RISK applicant profile:

Risk Factors:
- Income Stability Score: 45/100 (Below average - decreasing trend)
- Volatility: High (Income fluctuates significantly)
- Credit Score: 580 (Poor - significantly below recommended 650)
- Debt-to-Income Ratio: 144.8% (CRITICAL - exceeds 100%, indicates potential inability to repay)
- Recent Delinquencies: 3 in past 7 years
- Accounts Late: 4 active accounts with late payments

Application Status:
- Completion: 60% (Incomplete)
- Missing Critical Documents: Pay stubs, employment verification, credit authorization

Recommendation:
APPROVE WITH CONDITIONS or REQUEST ADDITIONAL INFORMATION:
1. Require recent pay stubs (last 3 months) to verify employment and income stability
2. Obtain employment verification letter for income confirmation
3. Review reasons for recent delinquencies
4. Require co-signer or secured collateral given high DTI ratio
5. Request credit authorization form for further investigation
""")

    # Example 2: Risk segmentation
    print("\n" + "=" * 70)
    print("Example 2: Claude performs risk segmentation")
    print("-" * 70)

    print("\nClaude's tool calls:")
    for risk_level in ["low", "medium", "high"]:
        tool_call = {
            "name": "get_applicants_by_risk_level",
            "arguments": {"risk_level": risk_level}
        }
        print(f"\n  - Fetching {risk_level.upper()} risk applicants")

    print("\n[Processing all risk levels...]")

    all_results = {}
    for risk_level in ["low", "medium", "high"]:
        result = get_applicants_by_risk_level(risk_level)
        all_results[risk_level] = result

    print("\n[Claude's Analysis]")
    print("""
Risk Portfolio Analysis:

LOW RISK (3 applicants):
- Alice Johnson (APP001): Score 85, Credit 750 - APPROVED
- David Martinez (APP004): Score 92, Credit 800 - APPROVED
- Emily Wilson (APP005): Score 71, Credit 720 - UNDER_REVIEW

Assessment: Strong portfolio. All have stable income, good credit, and low DTI.

MEDIUM RISK (1 applicant):
- Bob Smith (APP002): Score 62, Credit 680 - UNDER_REVIEW

Assessment: Acceptable profile. Some debt concerns (73.7% DTI) but improving trend.
Recommendation: Approve pending employment verification.

HIGH RISK (1 applicant):
- Carol Davis (APP003): Score 45, Credit 580 - SUBMITTED

Assessment: Critical concerns. Declining income, poor credit, high DTI.
Recommendation: Requires senior review and extensive documentation.

Portfolio Summary:
- Approval Rate (Low Risk): 100%
- Conditional Approval Rate (Medium Risk): 80%
- Declining Rate (High Risk): Expected for this segment
""")

    # Example 3: Workflow optimization
    print("\n" + "=" * 70)
    print("Example 3: Claude identifies workflow bottlenecks")
    print("-" * 70)

    print("\nClaude's tool call:")
    tool_call = {"name": "get_applications_requiring_action"}
    print(f"  {json.dumps(tool_call, indent=4)}")

    result = execute_tool(tool_call["name"], {})

    print(f"\nTool response:\n{format_tool_result(result)}")

    print("\n[Claude's Analysis]")
    print(f"""
Application Processing Bottleneck Report:

Total Pending Actions: {result['incomplete_count']} applications
Missing Documentation: {result['missing_docs_count']} applications

Action Items by Priority:

CRITICAL (APP003 - Carol Davis):
- Status: SUBMITTED (Awaiting initial review)
- Missing: 3 critical documents
  * Recent pay stubs (income verification)
  * Employment verification letter
  * Credit authorization form
- Impact: Cannot proceed without these documents
- Action: Send automated document request email

HIGH (APP002 - Bob Smith):
- Status: UNDER_REVIEW (Review in progress)
- Missing: 1 document
  * Employment verification letter
- Impact: Delays final decision
- Action: Follow up with applicant - expected 2-3 business days

MEDIUM (APP005 - Emily Wilson):
- Status: UNDER_REVIEW (Review in progress)
- Missing: 1 document
  * Government ID copy
- Impact: Final verification step
- Action: Request via automated system

Recommendations:
1. Implement automated reminders for missing documents (48-hour follow-up)
2. Batch document requests to reduce communication overhead
3. Prioritize CRITICAL items for senior reviewer
4. Set SLA targets: Complete reviews within 5 business days
5. Monitor completion rate trends (currently 60-92%, target 95%+)
""")

    # Example 4: Tool definitions for system prompt
    print("\n" + "=" * 70)
    print("Example 4: Tool definitions for Claude system prompt")
    print("-" * 70)

    tools = create_tool_definitions()
    print(f"\nAvailable tools for Claude ({len(tools)} total):\n")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   {tool['description']}\n")

    print("System Prompt Addition:")
    print("""
    You are an AI assistant specialized in applicant screening and risk assessment.
    You have access to the ApplicantDB MCP server with the following tools:

    [Tool definitions above would be included here]

    Your responsibilities:
    1. Answer questions about individual applicant profiles
    2. Identify applicants requiring immediate action
    3. Segment applicants by risk level
    4. Provide loan decision recommendations
    5. Flag potential fraud indicators
    6. Optimize application processing workflows

    Always provide reasoning for recommendations and highlight critical risk factors.
    """)

    print("\n" + "=" * 70)
    print("Integration Example Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demonstrate_claude_integration()
