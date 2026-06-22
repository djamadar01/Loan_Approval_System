"""
Test and demonstration client for the DecisionSynthesis MCP server.

This script demonstrates various decision synthesis scenarios.
"""

import json
import asyncio
from typing import Any
import subprocess
import sys


class DecisionSynthesisClient:
    """Client for testing DecisionSynthesis MCP server"""

    def __init__(self):
        self.scenarios = []

    def add_scenario(self, name: str, description: str, params: dict):
        """Add a test scenario"""
        self.scenario = {
            "name": name,
            "description": description,
            "params": params
        }
        self.scenarios.append(self.scenario)
        return self

    def build_scenarios(self):
        """Build comprehensive test scenarios"""

        # Scenario 1: Low risk application
        self.add_scenario(
            "Low Risk Application",
            "Application with low risk across all categories",
            {
                "financial_risk": 10,
                "operational_risk": 15,
                "compliance_risk": 5,
                "reputational_risk": 8,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
                "requires_escalation": False,
            }
        )

        # Scenario 2: Medium-high risk with mitigation
        self.add_scenario(
            "Medium-High Risk with Mitigation",
            "Application with moderate risk but mitigating factors present",
            {
                "financial_risk": 60,
                "operational_risk": 55,
                "compliance_risk": 50,
                "reputational_risk": 45,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
                "requires_escalation": False,
            }
        )

        # Scenario 3: High risk requiring review
        self.add_scenario(
            "High Risk Application",
            "Application with high risk scores requiring expert review",
            {
                "financial_risk": 75,
                "operational_risk": 70,
                "compliance_risk": 80,
                "reputational_risk": 65,
                "has_critical_issues": True,
                "has_mitigating_factors": False,
                "requires_escalation": True,
            }
        )

        # Scenario 4: Critical issues without mitigation
        self.add_scenario(
            "Critical Issues - No Mitigation",
            "Application with critical unmitigable issues - should reject",
            {
                "financial_risk": 90,
                "operational_risk": 85,
                "compliance_risk": 95,
                "reputational_risk": 80,
                "has_critical_issues": True,
                "has_mitigating_factors": False,
                "requires_escalation": False,
            }
        )

        # Scenario 5: Mixed risk profile
        self.add_scenario(
            "Mixed Risk Profile",
            "Application with varied risk levels requiring careful evaluation",
            {
                "financial_risk": 30,
                "operational_risk": 70,
                "compliance_risk": 45,
                "reputational_risk": 25,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
                "requires_escalation": True,
            }
        )

        # Scenario 6: Critical issues with strong mitigation
        self.add_scenario(
            "Critical Issues with Strong Mitigation",
            "Critical issues present but strong mitigating factors exist",
            {
                "financial_risk": 65,
                "operational_risk": 60,
                "compliance_risk": 70,
                "reputational_risk": 55,
                "has_critical_issues": True,
                "has_mitigating_factors": True,
                "requires_escalation": False,
            }
        )

        # Scenario 7: Very low risk across board
        self.add_scenario(
            "Very Low Risk",
            "Minimal risk across all categories - should auto-approve",
            {
                "financial_risk": 5,
                "operational_risk": 5,
                "compliance_risk": 8,
                "reputational_risk": 3,
                "has_critical_issues": False,
                "has_mitigating_factors": False,
                "requires_escalation": False,
            }
        )

        # Scenario 8: High compliance risk
        self.add_scenario(
            "High Compliance Risk",
            "Application with elevated compliance risk despite other low factors",
            {
                "financial_risk": 20,
                "operational_risk": 25,
                "compliance_risk": 85,
                "reputational_risk": 30,
                "has_critical_issues": True,
                "has_mitigating_factors": False,
                "requires_escalation": True,
            }
        )

        return self

    def print_scenarios(self):
        """Print all scenarios in a formatted manner"""
        print("\n" + "=" * 80)
        print("DecisionSynthesis MCP Server - Test Scenarios")
        print("=" * 80 + "\n")

        for i, scenario in enumerate(self.scenarios, 1):
            print(f"Scenario {i}: {scenario['name']}")
            print(f"Description: {scenario['description']}")
            print(f"Parameters:")
            for key, value in scenario["params"].items():
                print(f"  {key}: {value}")
            print()

    def export_scenarios_json(self, filename: str = "decision_scenarios.json"):
        """Export all scenarios to JSON file"""
        with open(filename, "w") as f:
            json.dump(
                {
                    "scenarios": self.scenarios,
                    "total_scenarios": len(self.scenarios)
                },
                f,
                indent=2
            )
        print(f"Scenarios exported to {filename}")

    def run_scenario_demo(self):
        """Run a demonstration of the scenarios"""
        print("\n" + "=" * 80)
        print("Decision Synthesis Logic Demo")
        print("=" * 80 + "\n")

        from decision_synthesis_mcp import DecisionRuleSet

        for scenario in self.scenarios:
            params = scenario["params"]
            print(f"\n>>> {scenario['name']}")
            print(f"    {scenario['description']}")

            # Calculate risk score
            risk_score = DecisionRuleSet.calculate_risk_score(
                financial_risk=params["financial_risk"],
                operational_risk=params["operational_risk"],
                compliance_risk=params["compliance_risk"],
                reputational_risk=params["reputational_risk"],
            )

            # Classify decision
            classification, confidence, factors = DecisionRuleSet.classify_decision(
                risk_score=risk_score,
                has_critical_issues=params["has_critical_issues"],
                has_mitigating_factors=params["has_mitigating_factors"],
                requires_escalation=params["requires_escalation"],
            )

            print(f"\n    Result:")
            print(f"    ├─ Classification: {classification.value}")
            print(f"    ├─ Risk Score: {risk_score}/100")
            print(f"    ├─ Confidence: {confidence:.2f}")
            print(f"    └─ Decision Factors:")
            for factor in factors:
                print(f"       - {factor}")


def demonstrate_decision_rules():
    """Demonstrate the decision rules"""
    from decision_synthesis_mcp import DecisionRuleSet

    print("\n" + "=" * 80)
    print("Decision Rule Documentation")
    print("=" * 80)

    print("\n1. RISK SCORE CALCULATION")
    print("   The overall risk score is a weighted average of component risks:")
    print("   ├─ Financial Risk (35% weight)")
    print("   ├─ Operational Risk (25% weight)")
    print("   ├─ Compliance Risk (25% weight)")
    print("   └─ Reputational Risk (15% weight)")

    print("\n2. CLASSIFICATION RULES")
    print("   REJECT (Risk Score >= 85 or unmitigable critical issues):")
    print("   ├─ High-risk applications")
    print("   ├─ Critical issues without mitigation")
    print("   └─ Confidence: 0.90-0.95")

    print("\n   REVIEW (Risk Score 50-84 or requires escalation):")
    print("   ├─ Medium-high risk applications")
    print("   ├─ Critical issues with possible mitigation")
    print("   ├─ Applications requiring escalation")
    print("   └─ Confidence: 0.70-0.85")

    print("\n   APPROVE (Risk Score < 50 and no critical issues):")
    print("   ├─ Low to medium-risk applications")
    print("   ├─ No critical unmitigable issues")
    print("   ├─ May have mitigating factors")
    print("   └─ Confidence: 0.90-0.95")


def main():
    """Main demonstration function"""
    print("\n")
    print("DecisionSynthesis MCP Server")
    print("=" * 80)

    # Create client and build scenarios
    client = DecisionSynthesisClient()
    client.build_scenarios()

    # Print scenarios
    client.print_scenarios()

    # Run decision logic demo
    client.run_scenario_demo()

    # Demonstrate rules
    demonstrate_decision_rules()

    # Export scenarios
    client.export_scenarios_json()

    print("\n" + "=" * 80)
    print("Demo Complete")
    print("=" * 80)
    print("\nTo start the MCP server, run:")
    print("  python -m decision_synthesis_mcp")
    print("\nTo use with Claude or other MCP clients, configure:")
    print('  "command": "python /path/to/decision_synthesis_mcp.py"')
    print("\n")


if __name__ == "__main__":
    main()
