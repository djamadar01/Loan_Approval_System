#!/usr/bin/env python3
"""
Example client demonstrating RiskRulesDB MCP Server usage
Shows how to interact with the financial risk analysis tools
"""

import json
import subprocess
import sys
from typing import Any


def run_mcp_tool(tool_name: str, **kwargs) -> dict[str, Any]:
    """
    Run MCP tool via subprocess and parse results
    (In production, use Anthropic SDK's tool_use feature)
    """
    command = [
        sys.executable,
        "risk_rules_db_server.py",
        json.dumps({"tool": tool_name, "input": kwargs}),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"error": "Tool execution timeout"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": str(e)}


def format_risk_report(analysis: dict[str, Any]) -> str:
    """Format analysis results into readable report"""
    report = []
    report.append("\n" + "=" * 80)
    report.append(f"FINANCIAL RISK ANALYSIS REPORT")
    report.append("=" * 80)

    if "error" in analysis:
        report.append(f"ERROR: {analysis['error']}")
        return "\n".join(report)

    # Header
    report.append(f"\nBorrower: {analysis.get('borrower_name', 'N/A')}")
    report.append(f"Analysis Date: {analysis.get('analysis_timestamp', 'N/A')}")

    # Overall Assessment
    report.append("\n" + "-" * 80)
    report.append("OVERALL RISK ASSESSMENT")
    report.append("-" * 80)
    report.append(f"Risk Level: {analysis.get('overall_risk_level', 'N/A')}")
    report.append(f"Recommendation: {analysis.get('overall_recommendation', 'N/A')}")

    # DTI Analysis
    report.append("\n" + "-" * 80)
    report.append("DEBT-TO-INCOME (DTI) ANALYSIS")
    report.append("-" * 80)
    dti = analysis.get("debt_to_income", {})
    report.append(f"Monthly Income: ${dti.get('monthly_income', 0):,.2f}")
    report.append(f"Total Monthly Debt: ${dti.get('total_monthly_debt', 0):,.2f}")
    report.append(f"DTI Ratio: {dti.get('ratio', 0):.2%}")
    report.append(f"Risk Level: {dti.get('risk_level', 'N/A')}")
    report.append(f"Insight: {dti.get('recommendation', 'N/A')}")

    # Credit Risk Analysis
    report.append("\n" + "-" * 80)
    report.append("CREDIT RISK ANALYSIS")
    report.append("-" * 80)
    credit = analysis.get("credit_risk", {})
    report.append(f"Credit Score: {credit.get('credit_score', 0)}")
    report.append(f"Risk Category: {credit.get('risk_category', 'N/A')}")
    report.append(f"Risk Level: {credit.get('risk_level', 'N/A')}")
    report.append("Contributing Factors:")
    for factor in credit.get("factors", []):
        report.append(f"  • {factor}")

    # Loan Risk Analysis
    report.append("\n" + "-" * 80)
    report.append("LOAN AMOUNT RISK ANALYSIS")
    report.append("-" * 80)
    loan = analysis.get("loan_risk", {})
    report.append(f"Requested Loan Amount: ${loan.get('loan_amount', 0):,.2f}")
    report.append(f"Annual Income: ${loan.get('borrower_income', 0):,.2f}")
    report.append(f"Loan-to-Income Ratio: {loan.get('ltv_ratio', 0):.2f}x")
    report.append(f"Max Recommended Loan: ${loan.get('max_recommended_loan', 0):,.2f}")
    report.append(f"Risk Level: {loan.get('risk_level', 'N/A')}")
    report.append("Risk Factors:")
    for factor in loan.get("factors", []):
        report.append(f"  • {factor}")

    # Anomaly Detection
    report.append("\n" + "-" * 80)
    report.append("ANOMALY DETECTION")
    report.append("-" * 80)
    anomalies = analysis.get("anomaly_detection", {})
    report.append(f"Anomaly Score: {anomalies.get('anomaly_score', 0):.1%}")
    report.append(f"Has Anomalies: {'Yes' if anomalies.get('has_anomalies') else 'No'}")
    if anomalies.get("flags"):
        report.append("Detected Anomalies:")
        for flag in anomalies.get("flags", []):
            report.append(f"  ⚠ {flag}")
    else:
        report.append("No significant anomalies detected")

    report.append("\n" + "=" * 80)
    return "\n".join(report)


def example_single_analysis():
    """Example: Analyze a single borrower"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Single Borrower Analysis")
    print("=" * 80)

    borrower_data = {
        "borrower_name": "John Smith",
        "monthly_income": 8000,
        "total_monthly_debt": 2400,  # DTI = 30%
        "credit_score": 720,
        "loan_amount": 250000,
        "annual_income": 96000,
    }

    print("\nInput Data:")
    print(json.dumps(borrower_data, indent=2))

    # Note: This is a conceptual example. In production, use Anthropic SDK
    print(
        "\nNote: In production, call this via Anthropic SDK's tool_use feature"
    )
    print("Tool would be called: analyze_financial_risk")


def example_batch_analysis():
    """Example: Analyze multiple borrowers"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Batch Analysis of Multiple Borrowers")
    print("=" * 80)

    borrowers = [
        {
            "borrower_name": "Alice Johnson",
            "monthly_income": 6000,
            "total_monthly_debt": 1800,  # DTI = 30%
            "credit_score": 750,
            "loan_amount": 200000,
            "annual_income": 72000,
        },
        {
            "borrower_name": "Bob Williams",
            "monthly_income": 5000,
            "total_monthly_debt": 2500,  # DTI = 50%
            "credit_score": 620,
            "loan_amount": 350000,
            "annual_income": 60000,
        },
        {
            "borrower_name": "Carol Davis",
            "monthly_income": 9000,
            "total_monthly_debt": 1500,  # DTI = 16.67%
            "credit_score": 800,
            "loan_amount": 150000,
            "annual_income": 108000,
        },
    ]

    print("\nBatch Input (3 borrowers):")
    for i, b in enumerate(borrowers, 1):
        print(f"\n  Borrower {i}: {b['borrower_name']}")
        print(f"    Monthly Income: ${b['monthly_income']:,.0f}")
        print(f"    Monthly Debt: ${b['total_monthly_debt']:,.0f}")
        print(f"    Credit Score: {b['credit_score']}")
        print(f"    Loan Amount: ${b['loan_amount']:,.0f}")


def example_anomaly_scenarios():
    """Example: Scenarios with anomalies"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Anomaly Detection Scenarios")
    print("=" * 80)

    scenarios = [
        {
            "name": "Low DTI & Excellent Credit (Approved Candidate)",
            "monthly_income": 10000,
            "total_monthly_debt": 1500,  # 15% DTI - Excellent
            "credit_score": 800,
            "loan_amount": 200000,
            "annual_income": 120000,
        },
        {
            "name": "High DTI & Low Credit Score (Red Flags)",
            "monthly_income": 4000,
            "total_monthly_debt": 2200,  # 55% DTI - Critical
            "credit_score": 550,
            "loan_amount": 400000,
            "annual_income": 48000,
        },
        {
            "name": "Moderate Metrics with Extreme Loan (Over-leveraged)",
            "monthly_income": 7000,
            "total_monthly_debt": 1400,  # 20% DTI - Good
            "credit_score": 680,
            "loan_amount": 500000,  # 7x annual income - Excessive
            "annual_income": 84000,
        },
        {
            "name": "Excellent Profile (Prime Candidate)",
            "monthly_income": 12000,
            "total_monthly_debt": 1200,  # 10% DTI - Excellent
            "credit_score": 820,
            "loan_amount": 180000,  # 1.5x annual income - Conservative
            "annual_income": 144000,
        },
    ]

    print("\nScenario Analysis:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n  Scenario {i}: {scenario['name']}")
        dti = scenario["total_monthly_debt"] / scenario["monthly_income"]
        lti = scenario["loan_amount"] / scenario["annual_income"]
        print(f"    DTI: {dti:.1%} | Credit: {scenario['credit_score']} | LTI: {lti:.2f}x")


def example_rules_configuration():
    """Example: Display business rules"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Business Rules Configuration")
    print("=" * 80)

    rules = {
        "DTI Rules": {
            "Acceptable Maximum": "43%",
            "Acceptable Target": "35%",
            "Warning Threshold": "50%",
            "Critical Threshold": "60%",
        },
        "Credit Score Rules": {
            "Excellent": "750+",
            "Good": "670-749",
            "Fair": "580-669",
            "Poor": "<580",
        },
        "Loan Amount Rules": {
            "Conservative": "≤ 2.5x annual income (LOW risk)",
            "Moderate": "≤ 3.0x annual income (MEDIUM risk)",
            "Aggressive": "≤ 3.5x annual income (HIGH risk)",
            "Excessive": "> 3.5x annual income (CRITICAL risk)",
        },
    }

    print("\nConfigured Business Rules:")
    for category, rules_dict in rules.items():
        print(f"\n  {category}:")
        for rule, value in rules_dict.items():
            print(f"    • {rule}: {value}")


def main():
    """Run all examples"""
    print("\n" + "#" * 80)
    print("# RiskRulesDB MCP Server - Example Usage Scenarios")
    print("#" * 80)

    example_single_analysis()
    example_batch_analysis()
    example_anomaly_scenarios()
    example_rules_configuration()

    print("\n" + "#" * 80)
    print("# INTEGRATION WITH ANTHROPIC SDK")
    print("#" * 80)
    print(
        """
The RiskRulesDB MCP server is designed to work with Anthropic's Claude API.

Integration example using Anthropic SDK:

```python
from anthropic import Anthropic

client = Anthropic()

# Configure MCP server
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2048,
    tools=[
        {
            "type": "computer_use",
            "name": "risk_rules_db",
            "description": "Financial Risk Analysis Engine",
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "Analyze financial risk for John Smith with monthly income $8000, "
                       "debt $2400, credit score 720, requesting $250k loan"
        }
    ]
)
```

Tools Available:
1. analyze_financial_risk - Single borrower comprehensive analysis
2. get_risk_rules_configuration - View current business rules
3. batch_analyze_financial_risk - Multiple borrower batch processing

Risk Levels: LOW, MEDIUM, HIGH, CRITICAL
    """
    )

    print("\n" + "#" * 80)
    print("# Server running on:")
    print("# python risk_rules_db_server.py")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    main()
