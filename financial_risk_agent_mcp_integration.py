"""
Integration example: FinancialRiskAgent with RiskRulesDB MCP Server

This demonstrates how to integrate the FinancialRiskAgent with the actual
RiskRulesDB MCP server using the Anthropic SDK and MCP protocol.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from financial_risk_agent import (
    FinancialRiskAgent,
    MCPToolInterface,
    RiskAssessment,
)


# ============================================================================
# Real MCP Tool Interface Implementation
# ============================================================================

class RealMCPToolInterface(MCPToolInterface):
    """
    Real implementation of MCPToolInterface that calls RiskRulesDB MCP server.

    This requires the RiskRulesDB MCP server to be running and accessible
    via the MCP protocol (typically stdio transport).
    """

    def __init__(self, mcp_client: Any = None):
        """
        Initialize with MCP client.

        Args:
            mcp_client: Initialized MCP client that has access to RiskRulesDB tools
        """
        self.mcp_client = mcp_client

    async def analyze_financial_risk(
        self,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        previous_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Call the analyze_financial_risk MCP tool."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        result = await self.mcp_client.call_tool(
            "analyze_financial_risk",
            {
                "credit_score": credit_score,
                "monthly_gross_income": monthly_gross_income,
                "monthly_debt_payments": monthly_debt_payments,
                "loan_amount": loan_amount,
                "previous_dti": previous_dti,
            },
        )
        return result

    async def calculate_dti_threshold(
        self,
        monthly_gross_income: float,
        target_dti: float = 0.36,
    ) -> Dict[str, Any]:
        """Call the calculate_dti_threshold MCP tool."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        result = await self.mcp_client.call_tool(
            "calculate_dti_threshold",
            {
                "monthly_gross_income": monthly_gross_income,
                "target_dti": target_dti,
            },
        )
        return result

    async def get_risk_thresholds(self) -> Dict[str, Any]:
        """Call the get_risk_thresholds MCP tool."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        result = await self.mcp_client.call_tool("get_risk_thresholds", {})
        return result

    async def batch_risk_analysis(
        self,
        applicants: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Call the batch_risk_analysis MCP tool."""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")

        result = await self.mcp_client.call_tool(
            "batch_risk_analysis",
            {"applicants": applicants},
        )
        return result


# ============================================================================
# Agent Integration Examples
# ============================================================================

async def example_single_assessment(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Perform a single applicant risk assessment.

    This shows the complete workflow of assessing a single applicant
    and retrieving detailed risk metrics.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: SINGLE APPLICANT ASSESSMENT")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=mcp_interface)

    print("\nScenario: Loan application from established professional")
    print("  - Monthly Income: $8,000")
    print("  - Current Debt Payments: $1,500")
    print("  - Credit Score: 760")
    print("  - Loan Request: $300,000")

    try:
        assessment: RiskAssessment = await agent.assess_risk(
            applicant_id="APP_PRO_001",
            credit_score=760,
            monthly_gross_income=8000,
            monthly_debt_payments=1500,
            loan_amount=300000,
        )

        print("\n" + "-" * 80)
        print("ASSESSMENT RESULTS:")
        print("-" * 80)

        # Display key metrics
        summary = agent.get_assessment_summary(assessment)
        for key, value in summary.items():
            print(f"  {key:25}: {value}")

        # Display anomalies if any
        if assessment.anomalies:
            print("\nANOMALIES DETECTED:")
            for anomaly in assessment.anomalies:
                print(f"  - {anomaly['flag_type']} (Severity: {anomaly['severity']})")
                print(f"    Message: {anomaly['message']}")
                print(f"    Actual: {anomaly['actual_value']}, Threshold: {anomaly['threshold']}")
        else:
            print("\nNo anomalies detected.")

        # Display detailed reasoning
        print("\nDETAILED REASONING:")
        print(assessment.reasoning)

    except Exception as e:
        print(f"\nError during assessment: {e}")


async def example_batch_assessment(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Perform batch risk assessment on multiple applicants.

    This demonstrates processing multiple applicants efficiently and
    generating summary statistics.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: BATCH APPLICANT ASSESSMENT")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=mcp_interface)

    applicants = [
        {
            "applicant_id": "BATCH_APP_001",
            "credit_score": 800,
            "monthly_gross_income": 10000,
            "monthly_debt_payments": 1000,
            "loan_amount": 400000,
        },
        {
            "applicant_id": "BATCH_APP_002",
            "credit_score": 650,
            "monthly_gross_income": 4000,
            "monthly_debt_payments": 1600,
            "loan_amount": 150000,
        },
        {
            "applicant_id": "BATCH_APP_003",
            "credit_score": 720,
            "monthly_gross_income": 6500,
            "monthly_debt_payments": 1300,
            "loan_amount": 250000,
        },
    ]

    print(f"\nProcessing {len(applicants)} loan applications...")

    try:
        result = await agent.batch_assess(applicants)

        if result["status"] == "success":
            print("\n" + "-" * 80)
            print("BATCH ASSESSMENT SUMMARY:")
            print("-" * 80)

            summary = result["summary"]
            total = result["total_applicants"]

            print(f"  Total Applicants:    {total}")
            print(f"  Approved:            {summary['approved']} ({summary['approved']/total*100:.1f}%)")
            print(f"  Conditional Review:  {summary['conditional']} ({summary['conditional']/total*100:.1f}%)")
            print(f"  Denied:              {summary['denied']} ({summary['denied']/total*100:.1f}%)")

            print("\nINDIVIDUAL ASSESSMENTS:")
            for analysis in result["analyses"]:
                if "error" not in analysis:
                    idx = analysis["applicant_index"]
                    applicant = applicants[idx]
                    ana = analysis["analysis"]
                    risk_level = ana["overall_risk_level"]
                    recommendation = ana["approval_recommendation"]
                    dti = ana["dti_analysis"]["debt_to_income_ratio"]

                    print(
                        f"  [{idx}] {applicant['applicant_id']:20} "
                        f"| DTI: {dti:6.1%} | Risk: {risk_level:8} | {recommendation}"
                    )
        else:
            print(f"\nError in batch assessment: {result.get('error')}")

    except Exception as e:
        print(f"\nError during batch assessment: {e}")


async def example_dti_planning(mcp_interface: MCPToolInterface) -> None:
    """
    Example: DTI planning and capacity analysis.

    This shows how to use the agent to help applicants understand their
    borrowing capacity under different DTI scenarios.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: DTI CAPACITY PLANNING")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=mcp_interface)

    income = 6000
    scenarios = [
        {"name": "Excellent (≤20%)", "dti": 0.20},
        {"name": "Good (≤36%)", "dti": 0.36},
        {"name": "Acceptable (≤43%)", "dti": 0.43},
        {"name": "High (≤50%)", "dti": 0.50},
    ]

    print(f"\nMonthly Gross Income: ${income:,.2f}")
    print("\n" + "-" * 80)
    print("DTI Scenarios - Maximum Allowable Monthly Debt Payments:")
    print("-" * 80)

    for scenario in scenarios:
        try:
            result = await agent.get_dti_capacity(income, scenario["dti"])

            if result["status"] == "success":
                max_debt = result["max_debt_payment"]
                print(f"\n{scenario['name']:30}")
                print(f"  Maximum monthly debt: ${max_debt:>10,.2f}")
                print(f"  Maximum annual debt:  ${max_debt * 12:>10,.2f}")
                print(f"  Message: {result['message']}")

        except Exception as e:
            print(f"\nError calculating capacity for {scenario['name']}: {e}")


async def example_risk_thresholds(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Retrieve and display business rules and risk thresholds.

    This shows the configured risk thresholds and decision rules
    used by the RiskRulesDB engine.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: BUSINESS RULES AND RISK THRESHOLDS")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=mcp_interface)

    print("\nRetrieving configured business rules...")

    try:
        thresholds = await agent.get_thresholds()

        if thresholds["status"] == "success":
            print("\n" + "-" * 80)
            print("DTI THRESHOLDS:")
            print("-" * 80)
            for key, config in thresholds["dti_thresholds"].items():
                threshold = config["threshold"]
                risk = config["risk_level"]
                threshold_str = str(threshold) if isinstance(threshold, str) else f"{threshold:.0%}"
                print(f"  {key:15} → {threshold_str:>20} → Risk: {risk.upper()}")

            if "credit_score_thresholds" in thresholds:
                print("\n" + "-" * 80)
                print("CREDIT SCORE THRESHOLDS:")
                print("-" * 80)
                for threshold in thresholds["credit_score_thresholds"]:
                    score = threshold["score"]
                    risk = threshold["risk_level"]
                    default_rate = threshold["default_rate"]
                    print(f"  {score:>10} → Risk: {risk:12} → Default Rate: {default_rate:>6}")

        else:
            print(f"\nError retrieving thresholds: {thresholds.get('error')}")

    except Exception as e:
        print(f"\nError during threshold retrieval: {e}")


async def example_json_export(mcp_interface: MCPToolInterface) -> None:
    """
    Example: Export assessment results as JSON.

    Demonstrates how to export assessments for integration with
    other systems, reporting, or archival.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: JSON EXPORT AND INTEGRATION")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=mcp_interface)

    print("\nPerforming assessment for export...")

    try:
        assessment: RiskAssessment = await agent.assess_risk(
            applicant_id="EXPORT_DEMO",
            credit_score=750,
            monthly_gross_income=7000,
            monthly_debt_payments=1400,
            loan_amount=280000,
        )

        print("\n" + "-" * 80)
        print("EXPORTED ASSESSMENT (JSON):")
        print("-" * 80)

        # Export as JSON
        json_str = agent.export_assessment_json(assessment)
        json_obj = json.loads(json_str)

        # Display formatted JSON
        print(json.dumps(json_obj, indent=2))

        # Show usage for integration
        print("\n" + "-" * 80)
        print("INTEGRATION PATTERNS:")
        print("-" * 80)
        print("""
1. Database Storage:
   - Store JSON in assessment_results table
   - Index by applicant_id and overall_risk_level
   - Query by date range and risk level

2. API Response:
   - Serve assessment as REST API endpoint
   - Include in loan application status responses
   - Provide to downstream decision systems

3. Report Generation:
   - Use reasoning field for audit trail
   - Create custom reports from anomalies
   - Track approval recommendation trends

4. Machine Learning:
   - Use assessment as feature input for models
   - Track outcomes vs. predicted risk
   - Retrain business rules engine periodically
        """)

    except Exception as e:
        print(f"\nError during export: {e}")


async def main():
    """
    Main entry point showing how to use FinancialRiskAgent with MCP.

    In production, you would:
    1. Initialize the MCP client connected to RiskRulesDB server
    2. Create RealMCPToolInterface with the MCP client
    3. Pass it to FinancialRiskAgent
    4. Use the agent to assess applicants
    """

    print("\n" + "=" * 80)
    print("FINANCIAL RISK AGENT - MCP INTEGRATION EXAMPLES")
    print("=" * 80)

    # NOTE: For production use, initialize with actual MCP client:
    # from anthropic import Anthropic
    # client = Anthropic()
    # mcp_interface = RealMCPToolInterface(mcp_client=client)

    # For demo purposes, use mock interface
    from financial_risk_agent import MockMCPToolInterface

    mcp_interface = MockMCPToolInterface()

    print("""
SETUP:
------
To use this with a real RiskRulesDB MCP server:

1. Start the server:
   $ python riskrulesdb_mcp_server.py

2. Initialize MCP client in your application:
   from anthropic import Anthropic
   client = Anthropic()

3. Create interface:
   mcp_interface = RealMCPToolInterface(mcp_client=client)

4. Create agent:
   agent = FinancialRiskAgent(mcp_interface=mcp_interface)

Running with MockMCPToolInterface for demonstration...
    """)

    try:
        # Run all examples
        await example_single_assessment(mcp_interface)
        await example_batch_assessment(mcp_interface)
        await example_dti_planning(mcp_interface)
        await example_risk_thresholds(mcp_interface)
        await example_json_export(mcp_interface)

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        print(f"\nError in examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
