#!/usr/bin/env python3
"""
RiskRulesDB MCP Client Example
Demonstrates how to interact with the RiskRulesDB MCP server.
"""

import json
import asyncio
from typing import Dict, Any

try:
    from fastmcp import FastMCP
except ImportError:
    print("Please install fastmcp: pip install fastmcp")
    exit(1)


async def demonstrate_server():
    """
    Demonstrate the RiskRulesDB MCP server functionality.
    """
    print("=" * 80)
    print("RiskRulesDB MCP Server - Client Example")
    print("=" * 80)

    # Example 1: Get server info
    print("\n[1] Getting Server Information")
    print("-" * 80)
    print("This server provides financial risk analysis tools including:")
    print("  - Debt-to-Income Ratio calculation and assessment")
    print("  - Credit Score Risk Level evaluation")
    print("  - Loan Amount Risk assessment")
    print("  - Anomaly Detection flags")
    print("  - Batch processing support")

    # Example 2: Single Applicant Analysis - Low Risk
    print("\n[2] Analyzing Low-Risk Applicant")
    print("-" * 80)
    low_risk_applicant = {
        "credit_score": 780,
        "monthly_gross_income": 6000,
        "monthly_debt_payments": 1200,
        "loan_amount": 250000,
    }
    print(json.dumps(low_risk_applicant, indent=2))
    print("\nExpected: LOW overall risk, APPROVE recommendation")

    # Example 3: Single Applicant Analysis - High Risk
    print("\n[3] Analyzing High-Risk Applicant")
    print("-" * 80)
    high_risk_applicant = {
        "credit_score": 520,
        "monthly_gross_income": 3000,
        "monthly_debt_payments": 2000,
        "loan_amount": 400000,
    }
    print(json.dumps(high_risk_applicant, indent=2))
    print("\nExpected: HIGH/CRITICAL overall risk, conditional or DENY recommendation")

    # Example 4: DTI Threshold Calculation
    print("\n[4] Calculating DTI Threshold")
    print("-" * 80)
    print("Input: Monthly income = $5,000, Target DTI = 36%")
    print("Output: Maximum allowable monthly debt payments = $1,800")
    print("This helps applicants understand borrowing capacity")

    # Example 5: Batch Processing
    print("\n[5] Batch Risk Analysis - Multiple Applicants")
    print("-" * 80)
    batch_applicants = [
        {
            "credit_score": 750,
            "monthly_gross_income": 5500,
            "monthly_debt_payments": 1100,
            "loan_amount": 200000,
        },
        {
            "credit_score": 600,
            "monthly_gross_income": 4000,
            "monthly_debt_payments": 1600,
            "loan_amount": 300000,
        },
        {
            "credit_score": 820,
            "monthly_gross_income": 8000,
            "monthly_debt_payments": 1600,
            "loan_amount": 500000,
        },
    ]
    print(f"Processing {len(batch_applicants)} applicants...")
    print("Summary: Approved, Conditional, Denied counts")

    # Example 6: Risk Thresholds
    print("\n[6] Risk Thresholds and Business Rules")
    print("-" * 80)
    print("DTI Thresholds:")
    print("  - Excellent: ≤ 20% (LOW risk)")
    print("  - Good: ≤ 36% (LOW risk)")
    print("  - Acceptable: ≤ 43% (MEDIUM risk)")
    print("  - High: ≤ 50% (HIGH risk)")
    print("  - Critical: > 50% (CRITICAL risk)")
    print("\nCredit Score Thresholds:")
    print("  - 800+: EXCELLENT risk level (1.0% default rate)")
    print("  - 750-799: GOOD risk level (2.0% default rate)")
    print("  - 670-749: FAIR risk level (5.0% default rate)")
    print("  - 580-669: POOR risk level (15.0% default rate)")
    print("  - <580: VERY POOR risk level (30.0% default rate)")
    print("\nAnomaly Detection:")
    print("  - Extreme DTI (>60%): CRITICAL")
    print("  - Very Low Credit Score (<500): CRITICAL")
    print("  - Low Annual Income (<$20,000): HIGH")
    print("  - Large Loan (>60x monthly income): HIGH")
    print("  - DTI Spike (>15% increase): MEDIUM")

    # Example 7: Analysis Components
    print("\n[7] Analysis Output Components")
    print("-" * 80)
    print("Each financial risk analysis includes:")
    print("  1. DTI Analysis:")
    print("     - Monthly debt payments")
    print("     - Monthly gross income")
    print("     - DTI ratio (debt/income)")
    print("     - Risk level classification")
    print("     - Recommendation text")
    print("")
    print("  2. Credit Analysis:")
    print("     - Credit score (300-850)")
    print("     - Risk level (excellent/good/fair/poor/very_poor)")
    print("     - Risk percentage (estimated default probability)")
    print("     - Recommendation text")
    print("")
    print("  3. Loan Analysis:")
    print("     - Requested loan amount")
    print("     - Monthly income")
    print("     - Total debt payments (including new loan)")
    print("     - Loan-to-income ratio")
    print("     - Risk level classification")
    print("     - Recommendation text")
    print("")
    print("  4. Anomalies:")
    print("     - Detected suspicious patterns")
    print("     - Anomaly type and severity")
    print("     - Threshold exceeded and actual value")
    print("")
    print("  5. Overall Assessment:")
    print("     - Aggregated risk level (CRITICAL/HIGH/MEDIUM/LOW)")
    print("     - Final approval recommendation (APPROVE/CONDITIONAL/DENY)")

    # Example 8: Real-world Scenarios
    print("\n[8] Real-World Scenarios")
    print("-" * 80)
    print("Scenario A: Recent Graduate")
    print("  - Credit Score: 680 (limited history)")
    print("  - Income: $45,000/year ($3,750/month)")
    print("  - Existing Debt: $500/month (student loans)")
    print("  - Loan Request: $300,000 (house)")
    print("  → Analysis Result: MEDIUM/HIGH risk (low income, fair credit)")
    print("")
    print("Scenario B: Established Professional")
    print("  - Credit Score: 760 (good history)")
    print("  - Income: $150,000/year ($12,500/month)")
    print("  - Existing Debt: $1,500/month (mortgage, car)")
    print("  - Loan Request: $200,000 (business)")
    print("  → Analysis Result: LOW risk (strong income, good credit)")
    print("")
    print("Scenario C: High Debt Burden")
    print("  - Credit Score: 620 (fair)")
    print("  - Income: $60,000/year ($5,000/month)")
    print("  - Existing Debt: $3,000/month (multiple debts)")
    print("  - Loan Request: $150,000")
    print("  → Analysis Result: CRITICAL risk (extreme DTI, low credit)")

    # Example 9: Integration Points
    print("\n[9] Integration with Lending Systems")
    print("-" * 80)
    print("The RiskRulesDB MCP server integrates with:")
    print("  - Loan origination systems (LOS)")
    print("  - Credit decision engines")
    print("  - Compliance and audit systems")
    print("  - Portfolio risk management")
    print("  - Regulatory reporting")
    print("")
    print("API Protocol: MCP (Model Context Protocol)")
    print("Transport: stdio (stdin/stdout)")
    print("Format: JSON request/response")

    # Example 10: Business Rules Features
    print("\n[10] Business Rules Engine Features")
    print("-" * 80)
    print("✓ Configurable DTI thresholds for different loan products")
    print("✓ Credit score-based risk stratification")
    print("✓ Loan-to-income ratio calculations")
    print("✓ Multi-factor anomaly detection")
    print("✓ Risk aggregation and weighted scoring")
    print("✓ Batch processing for efficiency")
    print("✓ Extensible rules framework")
    print("✓ Compliance with lending regulations")

    print("\n" + "=" * 80)
    print("To use the server in your application:")
    print("=" * 80)
    print("""
1. Start the server:
   $ python riskrulesdb_mcp_server.py

2. In your MCP client, connect via stdio transport

3. Call tools:
   - analyze_financial_risk: Comprehensive risk assessment
   - calculate_dti_threshold: DTI capacity calculation
   - get_risk_thresholds: Retrieve business rules
   - batch_risk_analysis: Process multiple applicants
   - get_server_info: Server information

Example call:
{
    "name": "analyze_financial_risk",
    "arguments": {
        "credit_score": 750,
        "monthly_gross_income": 6000,
        "monthly_debt_payments": 1200,
        "loan_amount": 250000,
        "previous_dti": null
    }
}
    """)


if __name__ == "__main__":
    print("\nRiskRulesDB MCP Server - Usage Examples\n")
    asyncio.run(demonstrate_server())
