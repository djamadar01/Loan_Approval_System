"""
ApplicantProfileAgent integration with Anthropic Claude API.

This module demonstrates how to use ApplicantProfileAgent with Claude API
for intelligent applicant analysis and decision-making.
"""

import json
from typing import Optional
from applicant_profile_agent import (
    ApplicantProfileAgent,
    AgentError,
    ApplicantProfileSummary
)


class ClaudeApplicantAnalyzer:
    """
    Integration layer between ApplicantProfileAgent and Claude API.

    This class demonstrates how to use the agent with Claude for intelligent
    applicant analysis, decision generation, and reasoning.
    """

    def __init__(self, verbose: bool = False):
        """Initialize the analyzer with an agent instance."""
        self.agent = ApplicantProfileAgent(verbose=verbose)
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[ClaudeAnalyzer] {message}")

    def create_mcp_tool_definitions(self) -> list:
        """
        Create MCP tool definitions for Claude API integration.

        These definitions describe the ApplicantProfileAgent methods
        that Claude can call.

        Returns:
            List of tool definitions for Claude's system prompt
        """
        return [
            {
                "name": "fetch_applicant_profile",
                "description": "Fetch complete applicant profile with Income Stability Score (0-100), Employment Risk level, Credit History Summary, and overall risk scoring",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "applicant_id": {
                            "type": "string",
                            "description": "The unique identifier of the applicant (e.g., 'APP001')"
                        }
                    },
                    "required": ["applicant_id"]
                }
            },
            {
                "name": "fetch_applicants_by_risk",
                "description": "Get applicants filtered by employment risk level for portfolio analysis",
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
                "name": "fetch_applications_requiring_action",
                "description": "Get applications with incomplete documentation or pending verification",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "analyze_risk_portfolio",
                "description": "Analyze complete portfolio of applicants with risk distribution",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def execute_agent_tool(self, tool_name: str, tool_input: dict) -> dict:
        """
        Execute an agent method based on tool name.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result as dictionary

        Raises:
            AgentError: If tool execution fails
        """
        self._log(f"Executing tool: {tool_name}")

        try:
            if tool_name == "fetch_applicant_profile":
                profile = self.agent.fetch_applicant_profile(tool_input["applicant_id"])
                return self._profile_to_dict(profile)

            elif tool_name == "fetch_applicants_by_risk":
                applicants = self.agent.fetch_applicants_by_risk(tool_input["risk_level"])
                return {
                    "risk_level": tool_input["risk_level"],
                    "count": len(applicants),
                    "applicants": applicants
                }

            elif tool_name == "fetch_applications_requiring_action":
                return self.agent.fetch_applications_requiring_action()

            elif tool_name == "analyze_risk_portfolio":
                return self.agent.analyze_risk_portfolio()

            else:
                raise AgentError(f"Unknown tool: {tool_name}")

        except AgentError as e:
            return {"error": str(e), "status": "failed"}

    def _profile_to_dict(self, profile: ApplicantProfileSummary) -> dict:
        """Convert profile to dictionary for JSON serialization."""
        return profile.to_dict()

    def generate_system_prompt(self) -> str:
        """
        Generate system prompt for Claude with agent tool definitions.

        Returns:
            System prompt string for Claude API
        """
        tools = self.create_mcp_tool_definitions()
        tools_json = json.dumps(tools, indent=2)

        return f"""You are an AI assistant specialized in applicant screening, risk assessment, and loan decision-making.

You have access to the ApplicantProfileAgent through the following tools:

{tools_json}

Your responsibilities:
1. Analyze individual applicant profiles and provide detailed risk assessments
2. Identify applicants requiring immediate action or additional documentation
3. Segment applicants by risk level and provide portfolio insights
4. Generate loan decision recommendations based on multi-factor analysis
5. Explain your reasoning with specific reference to income stability, credit history, and employment risk
6. Flag critical risk factors and suggest mitigation strategies

When analyzing applicants:
- Consider Income Stability Score (0-100): Higher is better
- Evaluate Employment Risk Level: low/medium/high
- Review Credit History: Score, DTI ratio, delinquencies
- Calculate Overall Risk Score: Combines all factors
- Provide Clear Recommendation: APPROVE, CONDITIONAL APPROVAL, REVIEW, or DENY

Always provide:
- Specific risk factors and their impact
- Supporting evidence from the applicant's profile
- Clear rationale for your recommendations
- Alternative scenarios where applicable

Format your response with clear sections for analysis and recommendations."""

    def demonstrate_single_applicant_analysis(self) -> None:
        """Demonstrate analysis of a single applicant."""
        print("\n" + "=" * 80)
        print("  Single Applicant Analysis Demo")
        print("=" * 80)

        applicant_id = "APP001"
        print(f"\nFetching profile for {applicant_id}...")

        tool_call = {
            "name": "fetch_applicant_profile",
            "arguments": {"applicant_id": applicant_id}
        }

        print(f"Tool call: {json.dumps(tool_call, indent=2)}")

        result = self.execute_agent_tool(tool_call["name"], tool_call["arguments"])

        print(f"\nProfile Retrieved:")
        print(json.dumps(result, indent=2, default=str))

        print("\n[Claude Analysis Would Follow]")
        print(f"""
Based on the profile for {result['name']}:

INCOME STABILITY:
- Score: {result['income_stability']['score']}/100 ({result['income_stability']['risk_indicator']})
- Trend: {result['income_stability']['trend'].title()}
- Volatility: {result['income_stability']['volatility'].title()}
- Monthly Income: ${result['income_stability']['average_monthly']:,.2f}

EMPLOYMENT RISK: {result['employment_risk']['risk_level'].upper()}
- {result['employment_risk']['rationale']}

CREDIT HISTORY:
- Credit Score: {result['credit_history']['credit_score']} ({result['credit_history']['credit_rating'].title()})
- Accounts On-Time: {result['credit_history']['accounts_on_time']}
- Accounts Late: {result['credit_history']['accounts_late']}
- DTI Ratio: {result['credit_history']['debt_to_income_ratio']}%
- Delinquencies: {result['credit_history']['delinquencies']}

ASSESSMENT:
- Overall Risk Score: {result['overall_risk_score']:.1f}/100
- Recommendation: {result['recommendation']}
- Missing Documents: {len(result['missing_fields'])} ({', '.join(result['missing_fields']) if result['missing_fields'] else 'None'})
""")

    def demonstrate_portfolio_analysis(self) -> None:
        """Demonstrate portfolio risk analysis."""
        print("\n" + "=" * 80)
        print("  Portfolio Risk Analysis Demo")
        print("=" * 80)

        print("\nAnalyzing complete portfolio...")

        tool_call = {"name": "analyze_risk_portfolio", "arguments": {}}
        result = self.execute_agent_tool(tool_call["name"], tool_call["arguments"])

        print(f"\nPortfolio Summary:")
        print(f"Total Applicants: {result['total']}")
        print(f"\nRisk Distribution:")

        for risk_level in ["low", "medium", "high"]:
            count = result[risk_level]["count"]
            percentage = result["distribution"][risk_level]
            print(f"  {risk_level.upper()}: {count} applicants ({percentage}%)")

        print("\n[Claude Analysis Would Follow]")
        print(f"""
PORTFOLIO COMPOSITION:
The current portfolio consists of {result['total']} applicants distributed across risk segments:

- LOW RISK: {result['low']['count']} applicants ({result['distribution']['low']}%)
  Recommendation: Strong segment with predictable outcomes

- MEDIUM RISK: {result['medium']['count']} applicants ({result['distribution']['medium']}%)
  Recommendation: Acceptable with conditional terms

- HIGH RISK: {result['high']['count']} applicants ({result['distribution']['high']}%)
  Recommendation: Requires enhanced due diligence

PORTFOLIO HEALTH: {"Excellent" if result['low']['count'] >= result['total'] * 0.5 else "Good" if result['low']['count'] >= result['total'] * 0.3 else "Fair"}
- Strong low-risk representation: {result['distribution']['low']}%
- Manageable medium-risk portion: {result['distribution']['medium']}%
- Limited high-risk exposure: {result['distribution']['high']}%
""")

    def demonstrate_workflow_optimization(self) -> None:
        """Demonstrate workflow optimization analysis."""
        print("\n" + "=" * 80)
        print("  Workflow Optimization Demo")
        print("=" * 80)

        print("\nIdentifying applications requiring action...")

        tool_call = {"name": "fetch_applications_requiring_action", "arguments": {}}
        result = self.execute_agent_tool(tool_call["name"], tool_call["arguments"])

        print(f"\nPending Actions Summary:")
        print(f"Total Incomplete Applications: {result['incomplete_count']}")
        print(f"Missing Documentation Count: {result['missing_docs_count']}")
        print(f"\nApplications Requiring Action:")

        for app in result["applications"]:
            print(f"\n  {app['applicant_id']}: {app['name']}")
            print(f"    Completion: {app['completion_percentage']}%")
            print(f"    Missing: {', '.join(app['missing_fields'])}")
            print(f"    Actions: {', '.join(app['required_actions'])}")

        print("\n[Claude Analysis Would Follow]")
        print(f"""
WORKFLOW BOTTLENECK ANALYSIS:

Total Pending: {result['incomplete_count']} applications
Documentation Missing: {result['missing_docs_count']} applications

ACTION ITEMS BY PRIORITY:

CRITICAL (< 60% Complete):
""")
        for app in result["applications"]:
            if app["completion_percentage"] < 60:
                print(f"  - {app['name']}: {len(app['missing_fields'])} documents needed")

        print(f"""
HIGH (60-80% Complete):
""")
        for app in result["applications"]:
            if 60 <= app["completion_percentage"] < 80:
                print(f"  - {app['name']}: {len(app['missing_fields'])} documents needed")

        print(f"""
MEDIUM (80-95% Complete):
""")
        for app in result["applications"]:
            if 80 <= app["completion_percentage"] < 95:
                print(f"  - {app['name']}: {len(app['missing_fields'])} documents needed")

        print(f"""
RECOMMENDATIONS:
1. Prioritize CRITICAL items for senior review
2. Send automated follow-ups for HIGH items (48-hour window)
3. Batch document requests to reduce applicant communication overhead
4. Set SLA target: Complete reviews within 5 business days
5. Monitor trend: Current completion rate {100 - (result['missing_docs_count']/result['incomplete_count']*100):.1f}% (target: 95%+)
""")

    def demonstrate_risk_segmentation(self) -> None:
        """Demonstrate risk-based segmentation and analysis."""
        print("\n" + "=" * 80)
        print("  Risk Segmentation Demo")
        print("=" * 80)

        all_results = {}
        for risk_level in ["low", "medium", "high"]:
            print(f"\nFetching {risk_level}-risk applicants...")
            tool_call = {
                "name": "fetch_applicants_by_risk",
                "arguments": {"risk_level": risk_level}
            }
            result = self.execute_agent_tool(tool_call["name"], tool_call["arguments"])
            all_results[risk_level] = result

            print(f"  Found: {result['count']} applicants")
            for app in result.get("applicants", []):
                print(f"    - {app['name']}: Income {app['income_stability_score']}, Credit {app['credit_score']}")

        print("\n[Claude Analysis Would Follow]")
        print("""
RISK SEGMENT ANALYSIS:

LOW RISK SEGMENT:
- Characteristics: Stable income, strong credit, healthy DTI
- Recommendation: Standard approval with standard terms
- Action: Process quickly for high customer satisfaction

MEDIUM RISK SEGMENT:
- Characteristics: Moderate income variability, fair credit, elevated DTI
- Recommendation: Conditional approval with enhanced verification
- Action: Require additional documentation and co-signer options

HIGH RISK SEGMENT:
- Characteristics: Declining income, poor credit, very high DTI
- Recommendation: Require senior review and extensive due diligence
- Action: Consider secured loans, higher interest rates, or decline

STRATEGIC INSIGHTS:
- Portfolio composition is within acceptable risk parameters
- Low-risk segment provides stable revenue base
- Medium and high-risk segments require active monitoring
- Diversification strategy is effective
""")


def main():
    """Run all demonstration scenarios."""
    analyzer = ClaudeApplicantAnalyzer(verbose=True)

    print("\n" + "=" * 80)
    print("  ApplicantProfileAgent + Claude API Integration Demo")
    print("=" * 80)

    # Show system prompt
    print("\n[System Prompt for Claude]")
    print("-" * 80)
    print(analyzer.generate_system_prompt()[:500] + "...")

    # Run demonstrations
    analyzer.demonstrate_single_applicant_analysis()
    analyzer.demonstrate_portfolio_analysis()
    analyzer.demonstrate_workflow_optimization()
    analyzer.demonstrate_risk_segmentation()

    print("\n" + "=" * 80)
    print("  Integration Demo Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
