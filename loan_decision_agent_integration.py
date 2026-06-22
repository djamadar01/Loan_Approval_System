"""
Integration example: LoanDecisionAgent with DecisionSynthesis MCP Server

This demonstrates how to integrate the LoanDecisionAgent with the actual
DecisionSynthesis MCP server using the Anthropic SDK and MCP protocol.
"""

import asyncio
import json
from typing import Any, Dict, Optional, List
from loan_decision_agent import (
    LoanDecisionAgent,
    MCPToolInterface,
    RealMCPToolInterface,
    MockMCPToolInterface,
)


# ============================================================================
# Integration Examples
# ============================================================================


async def example_single_decision(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Make a single loan decision.

    This shows the complete workflow of assessing risk and synthesizing
    a final loan decision.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: SINGLE LOAN DECISION")
    print("=" * 80)

    agent = LoanDecisionAgent(mcp_interface=mcp_interface, verbose=True)

    print("\nScenario 1: Strong applicant with low risk")
    print("  - Financial Risk: 25/100")
    print("  - Operational Risk: 20/100")
    print("  - Compliance Risk: 15/100")
    print("  - Reputational Risk: 10/100")
    print("  - Critical Issues: No")
    print("  - Mitigating Factors: Yes")

    try:
        decision = await agent.make_decision(
            applicant_id="APP_STRONG_001",
            financial_risk=25,
            operational_risk=20,
            compliance_risk=15,
            reputational_risk=10,
            has_critical_issues=False,
            has_mitigating_factors=True,
            requires_escalation=False,
        )

        print("\n" + "-" * 80)
        print("DECISION RESULT:")
        print("-" * 80)

        summary = agent.get_decision_summary(decision)
        for key, value in summary.items():
            print(f"  {key:20}: {value}")

        print("\nKEY DECISION FACTORS:")
        for i, factor in enumerate(decision.key_decision_factors, 1):
            print(f"  {i}. {factor}")

        print("\nDETAILED EXPLANATION:")
        print(decision.explanation)

    except Exception as e:
        print(f"\nError: {e}")

    # Scenario 2: High-risk applicant
    print("\n" + "=" * 80)
    print("\nScenario 2: High-risk applicant requiring rejection")
    print("  - Financial Risk: 85/100")
    print("  - Operational Risk: 90/100")
    print("  - Compliance Risk: 88/100")
    print("  - Reputational Risk: 75/100")
    print("  - Critical Issues: Yes")
    print("  - Mitigating Factors: No")

    try:
        decision = await agent.make_decision(
            applicant_id="APP_HIGH_RISK_001",
            financial_risk=85,
            operational_risk=90,
            compliance_risk=88,
            reputational_risk=75,
            has_critical_issues=True,
            has_mitigating_factors=False,
            requires_escalation=False,
        )

        print("\n" + "-" * 80)
        print("DECISION RESULT:")
        print("-" * 80)

        summary = agent.get_decision_summary(decision)
        for key, value in summary.items():
            print(f"  {key:20}: {value}")

        print("\nKEY DECISION FACTORS:")
        for i, factor in enumerate(decision.key_decision_factors, 1):
            print(f"  {i}. {factor}")

        print("\nDETAILED EXPLANATION:")
        print(decision.explanation)

    except Exception as e:
        print(f"\nError: {e}")

    # Scenario 3: Medium-risk applicant requiring review
    print("\n" + "=" * 80)
    print("\nScenario 3: Medium-risk applicant requiring review")
    print("  - Financial Risk: 50/100")
    print("  - Operational Risk: 55/100")
    print("  - Compliance Risk: 45/100")
    print("  - Reputational Risk: 35/100")
    print("  - Critical Issues: Yes")
    print("  - Mitigating Factors: Yes")
    print("  - Requires Escalation: Yes")

    try:
        decision = await agent.make_decision(
            applicant_id="APP_MEDIUM_RISK_001",
            financial_risk=50,
            operational_risk=55,
            compliance_risk=45,
            reputational_risk=35,
            has_critical_issues=True,
            has_mitigating_factors=True,
            requires_escalation=True,
        )

        print("\n" + "-" * 80)
        print("DECISION RESULT:")
        print("-" * 80)

        summary = agent.get_decision_summary(decision)
        for key, value in summary.items():
            print(f"  {key:20}: {value}")

        print("\nKEY DECISION FACTORS:")
        for i, factor in enumerate(decision.key_decision_factors, 1):
            print(f"  {i}. {factor}")

        print("\nDETAILED EXPLANATION:")
        print(decision.explanation)

    except Exception as e:
        print(f"\nError: {e}")


async def example_batch_decisions(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Make decisions for multiple applicants in batch.

    This demonstrates processing multiple applicants efficiently and
    generating summary statistics.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: BATCH LOAN DECISIONS")
    print("=" * 80)

    agent = LoanDecisionAgent(mcp_interface=mcp_interface, verbose=True)

    # Create diverse applicant scenarios
    decision_requests = [
        {
            "applicant_id": "BATCH_APP_001",
            "financial_risk": 20,
            "operational_risk": 15,
            "compliance_risk": 10,
            "reputational_risk": 8,
            "has_critical_issues": False,
            "has_mitigating_factors": True,
        },
        {
            "applicant_id": "BATCH_APP_002",
            "financial_risk": 65,
            "operational_risk": 60,
            "compliance_risk": 70,
            "reputational_risk": 50,
            "has_critical_issues": True,
            "has_mitigating_factors": True,
            "requires_escalation": True,
        },
        {
            "applicant_id": "BATCH_APP_003",
            "financial_risk": 90,
            "operational_risk": 85,
            "compliance_risk": 92,
            "reputational_risk": 80,
            "has_critical_issues": True,
            "has_mitigating_factors": False,
        },
        {
            "applicant_id": "BATCH_APP_004",
            "financial_risk": 35,
            "operational_risk": 30,
            "compliance_risk": 25,
            "reputational_risk": 20,
            "has_critical_issues": False,
            "has_mitigating_factors": False,
        },
        {
            "applicant_id": "BATCH_APP_005",
            "financial_risk": 55,
            "operational_risk": 50,
            "compliance_risk": 60,
            "reputational_risk": 45,
            "has_critical_issues": False,
            "has_mitigating_factors": True,
            "requires_escalation": False,
        },
    ]

    print(f"\nProcessing {len(decision_requests)} loan applications...")

    try:
        result = await agent.batch_make_decisions(decision_requests)

        print("\n" + "-" * 80)
        print("BATCH PROCESSING SUMMARY:")
        print("-" * 80)

        print(f"  Total Requests:     {result['total_requests']}")
        print(f"  Successful:         {result['successful']}")
        print(f"  Failed:             {result['failed']}")
        print(f"  Overall Status:     {result['status'].upper()}")

        summary = result["summary"]
        print("\n  Decision Distribution:")
        print(f"    - Approved:  {summary['approved']} ({summary['approved']/result['successful']*100:.0f}%)")
        print(f"    - Rejected:  {summary['rejected']} ({summary['rejected']/result['successful']*100:.0f}%)")
        print(f"    - Review:    {summary['review']} ({summary['review']/result['successful']*100:.0f}%)")
        print(f"    - Approval Rate: {summary['approval_rate']:.1f}%")

        print("\n" + "-" * 80)
        print("INDIVIDUAL DECISIONS:")
        print("-" * 80)

        for decision in result["decisions"]:
            applicant_id = decision.applicant_id
            classification = decision.classification.value
            risk_score = decision.risk_score
            confidence = decision.confidence_level * 100

            status_icon = {
                "Approve": "✓",
                "Reject": "✗",
                "Review": "?",
            }.get(classification, " ")

            print(
                f"  [{status_icon}] {applicant_id:15} | "
                f"Risk: {risk_score:3}/100 | "
                f"Decision: {classification:8} | "
                f"Confidence: {confidence:5.1f}%"
            )

        if result["errors"]:
            print("\n" + "-" * 80)
            print("ERRORS:")
            print("-" * 80)
            for error in result["errors"]:
                print(f"  [{error['applicant_id']}] {error['error']}")

    except Exception as e:
        print(f"\nError: {e}")


async def example_decision_rules(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Retrieve and display decision rules.

    This shows the configured decision rules and risk thresholds
    used by the DecisionSynthesis engine.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: DECISION RULES AND THRESHOLDS")
    print("=" * 80)

    agent = LoanDecisionAgent(mcp_interface=mcp_interface, verbose=True)

    print("\nRetrieving decision rules from DecisionSynthesis server...")

    try:
        rules = await agent.get_decision_rules()

        print("\n" + "-" * 80)
        print("RISK SCORE CALCULATION:")
        print("-" * 80)

        calc_rules = rules["risk_score_calculation"]
        print(f"  Description: {calc_rules['description']}")
        print(f"  Formula: Weighted average of component risks")
        print(f"  Score Range: {calc_rules['range']}")

        print("\n  Risk Component Weights:")
        weights = calc_rules["weights"]
        for risk_type in [
            "financial_risk",
            "operational_risk",
            "compliance_risk",
            "reputational_risk",
        ]:
            weight = weights[risk_type]
            print(f"    - {risk_type:20}: {weight:5.0%}")

        print("\n" + "-" * 80)
        print("CLASSIFICATION RULES:")
        print("-" * 80)

        class_rules = rules["classification_rules"]
        for classification in ["REJECT", "REVIEW", "APPROVE"]:
            print(f"\n  {classification}:")
            rule = class_rules[classification]
            print(f"    Confidence Range: {rule['confidence_range']}")
            print("    Decision Conditions:")
            for condition in rule["conditions"]:
                print(f"      • {condition}")

        print("\n" + "-" * 80)
        print("RISK THRESHOLDS:")
        print("-" * 80)

        thresholds = rules["thresholds"]
        for threshold_name, threshold_range in thresholds.items():
            print(f"  {threshold_name:20}: {threshold_range}")

        print("\n" + "-" * 80)
        print("DECISION LOGIC SUMMARY:")
        print("-" * 80)
        print("""
  1. REJECT (High Confidence 0.9-0.95):
     - Applied when risk score >= 85 AND critical issues present
     - Applied when critical issues exist without mitigation
     - Applied when compliance violations are detected

  2. REVIEW (Medium Confidence 0.7-0.85):
     - Applied for medium-high risk (50-84) requiring escalation
     - Applied when critical issues exist but can be mitigated
     - Applied for mixed risk profiles requiring human judgment

  3. APPROVE (High Confidence 0.9-0.95):
     - Applied when risk score < 50 with no critical issues
     - Applied when mitigating factors are present
     - Applied for low to medium-low risk profiles
        """)

    except Exception as e:
        print(f"\nError: {e}")


async def example_json_export(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Export decision results as JSON.

    Demonstrates how to export decisions for integration with
    other systems, reporting, or archival.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: JSON EXPORT AND INTEGRATION")
    print("=" * 80)

    agent = LoanDecisionAgent(mcp_interface=mcp_interface, verbose=True)

    print("\nMaking a decision and exporting as JSON...")

    try:
        decision = await agent.make_decision(
            applicant_id="EXPORT_DEMO_001",
            financial_risk=35,
            operational_risk=30,
            compliance_risk=25,
            reputational_risk=20,
            has_critical_issues=False,
            has_mitigating_factors=True,
            requires_escalation=False,
        )

        print("\n" + "-" * 80)
        print("EXPORTED DECISION (JSON):")
        print("-" * 80)

        json_str = agent.export_decision_json(decision)
        print(json_str)

        print("\n" + "-" * 80)
        print("INTEGRATION PATTERNS:")
        print("-" * 80)
        print("""
1. Database Storage:
   - Store JSON in loan_decisions table
   - Index by applicant_id and timestamp
   - Query by decision classification and risk_score range
   - Track decision history for audit trail

2. API Response:
   - Serve decision as REST API endpoint
   - Include in loan application status responses
   - Provide to downstream notification/workflow systems
   - Support real-time decision queries

3. Report Generation:
   - Use explanation field for audit trail documentation
   - Create portfolio reports from batch decisions
   - Track decision distribution and approval rates
   - Analyze decision patterns over time

4. Workflow Integration:
   - Route APPROVE decisions to funding process
   - Route REJECT decisions to decline communication
   - Route REVIEW decisions to underwriter queue
   - Trigger automated notifications based on classification

5. Machine Learning:
   - Use decision as feature input for models
   - Track actual vs. predicted outcomes
   - Measure decision model performance
   - Retrain decision rules periodically based on outcomes

6. Compliance & Audit:
   - Export decisions for regulatory reporting
   - Generate audit trail with confidence levels
   - Track key factors for compliance documentation
   - Support fair lending analysis
        """)

    except Exception as e:
        print(f"\nError: {e}")


async def example_scenario_analysis(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Analyze how different risk profiles affect decisions.

    This demonstrates using the agent to understand decision patterns
    across different risk scenarios.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: RISK SCENARIO ANALYSIS")
    print("=" * 80)

    agent = LoanDecisionAgent(mcp_interface=mcp_interface, verbose=True)

    print("\nAnalyzing decision patterns across risk profiles...\n")

    # Create scenarios that systematically vary risk levels
    scenarios = []

    for overall_risk in [20, 40, 60, 80]:
        for critical in [False, True]:
            for mitigating in [False, True]:
                scenarios.append(
                    {
                        "applicant_id": f"SCENARIO_{overall_risk}_C{critical}_M{mitigating}",
                        "financial_risk": overall_risk,
                        "operational_risk": overall_risk,
                        "compliance_risk": overall_risk,
                        "reputational_risk": overall_risk,
                        "has_critical_issues": critical,
                        "has_mitigating_factors": mitigating,
                    }
                )

    try:
        result = await agent.batch_make_decisions(scenarios)

        print("-" * 80)
        print("SCENARIO ANALYSIS RESULTS:")
        print("-" * 80)

        # Organize results by risk level
        by_risk_level = {}
        for decision in result["decisions"]:
            risk_level = decision.risk_score // 20 * 20  # Group by 20s
            if risk_level not in by_risk_level:
                by_risk_level[risk_level] = []
            by_risk_level[risk_level].append(decision)

        for risk_level in sorted(by_risk_level.keys()):
            decisions_at_level = by_risk_level[risk_level]
            approve_count = sum(
                1 for d in decisions_at_level if d.classification.value == "Approve"
            )
            reject_count = sum(
                1 for d in decisions_at_level if d.classification.value == "Reject"
            )
            review_count = sum(
                1 for d in decisions_at_level if d.classification.value == "Review"
            )

            total = len(decisions_at_level)
            risk_range = f"{risk_level}-{risk_level + 19}"

            print(f"\n  Risk Score Range {risk_range}:")
            print(
                f"    Approve: {approve_count:2d} ({approve_count/total*100:5.1f}%) | "
                f"Reject: {reject_count:2d} ({reject_count/total*100:5.1f}%) | "
                f"Review: {review_count:2d} ({review_count/total*100:5.1f}%)"
            )

        print("\n" + "-" * 80)
        print("KEY INSIGHTS:")
        print("-" * 80)
        print(f"  Total Scenarios Analyzed: {result['total_requests']}")
        print(f"  Total Approvals: {result['summary']['approved']}")
        print(f"  Total Rejections: {result['summary']['rejected']}")
        print(f"  Total Reviews: {result['summary']['review']}")
        print(f"  Overall Approval Rate: {result['summary']['approval_rate']:.1f}%")

    except Exception as e:
        print(f"\nError: {e}")


async def main():
    """
    Main entry point showing how to use LoanDecisionAgent with MCP.

    In production, you would:
    1. Initialize the MCP client connected to DecisionSynthesis server
    2. Create RealMCPToolInterface with the MCP client
    3. Pass it to LoanDecisionAgent
    4. Use the agent to synthesize decisions
    """

    print("\n" + "=" * 80)
    print("LOAN DECISION AGENT - MCP INTEGRATION EXAMPLES")
    print("=" * 80)

    # For production use with real MCP server:
    # from anthropic import Anthropic
    # client = Anthropic()
    # mcp_interface = RealMCPToolInterface(mcp_client=client)

    # For demo purposes, use mock interface
    mcp_interface = MockMCPToolInterface()

    print("""
SETUP:
------
To use this with a real DecisionSynthesis MCP server:

1. Start the server:
   $ python decision_synthesis_mcp.py

2. Initialize MCP client in your application:
   from anthropic import Anthropic
   client = Anthropic()

3. Create interface:
   mcp_interface = RealMCPToolInterface(mcp_client=client)

4. Create agent:
   agent = LoanDecisionAgent(mcp_interface=mcp_interface)

Running with MockMCPToolInterface for demonstration...
    """)

    try:
        # Run all examples
        await example_single_decision(mcp_interface)
        await example_batch_decisions(mcp_interface)
        await example_decision_rules(mcp_interface)
        await example_json_export(mcp_interface)
        await example_scenario_analysis(mcp_interface)

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError in examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
