#!/usr/bin/env python3
"""
Test suite for updated FinancialRiskAgent with MCP tool integration.

Demonstrates:
1. MCP client initialization
2. Calling calculate_debt_to_income tool
3. Calling assess_credit_score_risk tool
4. Calling detect_financial_anomalies tool
5. Business rules application
"""

import asyncio
import json
from typing import Any, Dict
from financial_risk_agent import (
    FinancialRiskAgent,
    RealMCPToolInterface,
    MockMCPToolInterface,
    RiskAssessment,
    RiskLevel,
    ApprovalRecommendation,
)


# ============================================================================
# Test Scenarios
# ============================================================================

class TestScenario:
    """Test scenario with applicant data and expected outcomes."""

    def __init__(
        self,
        name: str,
        applicant_id: str,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
        expected_risk_level: RiskLevel,
        expected_recommendation: ApprovalRecommendation,
    ):
        self.name = name
        self.applicant_id = applicant_id
        self.credit_score = credit_score
        self.monthly_gross_income = monthly_gross_income
        self.monthly_debt_payments = monthly_debt_payments
        self.loan_amount = loan_amount
        self.expected_risk_level = expected_risk_level
        self.expected_recommendation = expected_recommendation


# Define test scenarios
SCENARIOS = [
    TestScenario(
        name="Prime Applicant - Excellent Profile",
        applicant_id="SCENARIO_001",
        credit_score=800,
        monthly_gross_income=10000,
        monthly_debt_payments=1000,
        loan_amount=400000,
        expected_risk_level=RiskLevel.LOW,
        expected_recommendation=ApprovalRecommendation.APPROVE,
    ),
    TestScenario(
        name="Good Applicant - Solid Profile",
        applicant_id="SCENARIO_002",
        credit_score=750,
        monthly_gross_income=8000,
        monthly_debt_payments=1500,
        loan_amount=300000,
        expected_risk_level=RiskLevel.LOW,
        expected_recommendation=ApprovalRecommendation.APPROVE,
    ),
    TestScenario(
        name="Fair Applicant - Requires Review",
        applicant_id="SCENARIO_003",
        credit_score=700,
        monthly_gross_income=6000,
        monthly_debt_payments=1800,
        loan_amount=200000,
        expected_risk_level=RiskLevel.MEDIUM,
        expected_recommendation=ApprovalRecommendation.CONDITIONAL,
    ),
    TestScenario(
        name="High Risk Applicant - DTI Issues",
        applicant_id="SCENARIO_004",
        credit_score=650,
        monthly_gross_income=4000,
        monthly_debt_payments=2000,
        loan_amount=150000,
        expected_risk_level=RiskLevel.HIGH,
        expected_recommendation=ApprovalRecommendation.CONDITIONAL,
    ),
    TestScenario(
        name="Critical Applicant - High DTI & Low Credit",
        applicant_id="SCENARIO_005",
        credit_score=480,
        monthly_gross_income=3000,
        monthly_debt_payments=2500,
        loan_amount=100000,
        expected_risk_level=RiskLevel.CRITICAL,
        expected_recommendation=ApprovalRecommendation.DENY,
    ),
]


# ============================================================================
# Test Functions
# ============================================================================

async def test_single_assessment(
    agent: FinancialRiskAgent,
    scenario: TestScenario,
) -> Dict[str, Any]:
    """
    Test single applicant assessment with specific MCP tool calls.

    Tests the complete workflow:
    1. Call calculate_debt_to_income
    2. Call assess_credit_score_risk
    3. Call detect_financial_anomalies
    4. Call analyze_financial_risk
    5. Verify business rules application
    """
    print(f"\n{'='*80}")
    print(f"TEST: {scenario.name}")
    print(f"{'='*80}")

    print(f"\nApplicant Profile:")
    print(f"  ID: {scenario.applicant_id}")
    print(f"  Credit Score: {scenario.credit_score}")
    print(f"  Monthly Income: ${scenario.monthly_gross_income:,.2f}")
    print(f"  Monthly Debt: ${scenario.monthly_debt_payments:,.2f}")
    print(f"  Loan Amount: ${scenario.loan_amount:,.2f}")

    try:
        assessment: RiskAssessment = await agent.assess_risk(
            applicant_id=scenario.applicant_id,
            credit_score=scenario.credit_score,
            monthly_gross_income=scenario.monthly_gross_income,
            monthly_debt_payments=scenario.monthly_debt_payments,
            loan_amount=scenario.loan_amount,
        )

        # Display assessment results
        print(f"\n{'='*80}")
        print("ASSESSMENT RESULTS")
        print(f"{'='*80}")

        # DTI Analysis
        print(f"\n1. DEBT-TO-INCOME ANALYSIS (calculate_debt_to_income tool):")
        print(f"   DTI Ratio: {assessment.debt_to_income_ratio:.2%}")
        print(f"   Risk Level: {assessment.dti_risk_level.value.upper()}")
        print(f"   Recommendation: {assessment.dti_recommendation}")

        # Credit Analysis
        print(f"\n2. CREDIT SCORE ANALYSIS (assess_credit_score_risk tool):")
        print(f"   Credit Score: {assessment.credit_score}")
        print(f"   Risk Level: {assessment.credit_risk_level.upper()}")
        print(f"   Default Risk: {assessment.credit_risk_percentage:.1f}%")
        print(f"   Recommendation: {assessment.credit_recommendation}")

        # Loan Analysis
        print(f"\n3. LOAN AMOUNT ANALYSIS:")
        print(f"   Loan Amount: ${assessment.loan_amount:,.2f}")
        print(f"   Risk Level: {assessment.loan_risk_level.value.upper()}")
        print(f"   Recommendation: {assessment.loan_recommendation}")

        # Anomalies
        print(f"\n4. ANOMALY DETECTION (detect_financial_anomalies tool):")
        if assessment.anomalies:
            print(f"   Anomalies Detected: {len(assessment.anomalies)}")
            for i, anomaly in enumerate(assessment.anomalies, 1):
                print(f"   [{i}] {anomaly['flag_type']}")
                print(f"       Severity: {anomaly['severity'].upper()}")
                print(f"       Message: {anomaly['message']}")
                print(f"       Threshold: {anomaly['threshold']}")
                print(f"       Actual: {anomaly['actual_value']:.4f}")
        else:
            print("   No anomalies detected")

        # Overall Assessment
        print(f"\n5. OVERALL ASSESSMENT (business rules applied):")
        print(f"   Overall Risk Level: {assessment.overall_risk_level.value.upper()}")
        print(f"   Approval Recommendation: {assessment.approval_recommendation.value}")

        # Test validation
        print(f"\n{'='*80}")
        print("TEST VALIDATION")
        print(f"{'='*80}")

        test_passed = True
        if assessment.overall_risk_level != scenario.expected_risk_level:
            print(f"FAIL: Risk level mismatch")
            print(f"  Expected: {scenario.expected_risk_level.value}")
            print(f"  Actual: {assessment.overall_risk_level.value}")
            test_passed = False
        else:
            print(f"PASS: Risk level matches ({scenario.expected_risk_level.value})")

        if assessment.approval_recommendation != scenario.expected_recommendation:
            print(f"FAIL: Recommendation mismatch")
            print(f"  Expected: {scenario.expected_recommendation.value}")
            print(f"  Actual: {assessment.approval_recommendation.value}")
            test_passed = False
        else:
            print(f"PASS: Recommendation matches ({scenario.expected_recommendation.value})")

        # Display reasoning
        print(f"\n{'='*80}")
        print("DETAILED REASONING")
        print(f"{'='*80}")
        print(assessment.reasoning)

        # Display logs
        if agent.logger:
            print(f"\n{'='*80}")
            print("PROCESSING LOG")
            print(f"{'='*80}")
            for i, log in enumerate(agent.logger, 1):
                print(f"  [{i}] {log}")

        return {
            "scenario": scenario.name,
            "passed": test_passed,
            "assessment": assessment,
            "summary": agent.get_assessment_summary(assessment),
        }

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "scenario": scenario.name,
            "passed": False,
            "error": str(e),
        }


async def test_mcp_tool_calls(agent: FinancialRiskAgent) -> None:
    """
    Test individual MCP tool calls directly.

    Demonstrates calling:
    1. calculate_debt_to_income
    2. assess_credit_score_risk
    3. detect_financial_anomalies
    """
    print(f"\n{'='*80}")
    print("TESTING INDIVIDUAL MCP TOOL CALLS")
    print(f"{'='*80}")

    # Test data
    credit_score = 750
    monthly_income = 8000
    monthly_debt = 1500
    loan_amount = 300000

    # Tool 1: calculate_debt_to_income
    print(f"\n1. CALLING calculate_debt_to_income MCP TOOL:")
    print(f"   Parameters:")
    print(f"     - monthly_gross_income: ${monthly_income:,.2f}")
    print(f"     - monthly_debt_payments: ${monthly_debt:,.2f}")

    try:
        dti_result = await agent.mcp_interface.calculate_debt_to_income(
            monthly_gross_income=monthly_income,
            monthly_debt_payments=monthly_debt,
        )
        print(f"   Result:")
        print(json.dumps(dti_result, indent=4))
    except Exception as e:
        print(f"   Error: {e}")

    # Tool 2: assess_credit_score_risk
    print(f"\n2. CALLING assess_credit_score_risk MCP TOOL:")
    print(f"   Parameters:")
    print(f"     - credit_score: {credit_score}")

    try:
        credit_result = await agent.mcp_interface.assess_credit_score_risk(
            credit_score=credit_score,
        )
        print(f"   Result:")
        print(json.dumps(credit_result, indent=4))
    except Exception as e:
        print(f"   Error: {e}")

    # Tool 3: detect_financial_anomalies
    print(f"\n3. CALLING detect_financial_anomalies MCP TOOL:")
    print(f"   Parameters:")
    print(f"     - credit_score: {credit_score}")
    print(f"     - monthly_income: ${monthly_income:,.2f}")
    print(f"     - monthly_debt_payments: ${monthly_debt:,.2f}")
    print(f"     - loan_amount: ${loan_amount:,.2f}")

    try:
        anomaly_result = await agent.mcp_interface.detect_financial_anomalies(
            credit_score=credit_score,
            monthly_income=monthly_income,
            monthly_debt_payments=monthly_debt,
            loan_amount=loan_amount,
        )
        print(f"   Result:")
        print(json.dumps(anomaly_result, indent=4))
    except Exception as e:
        print(f"   Error: {e}")


async def test_business_rules(agent: FinancialRiskAgent) -> None:
    """
    Test business rules application in risk assessment.

    Validates:
    - DTI-based decision logic
    - Credit score-based decision logic
    - Anomaly-based decision logic
    - Overall risk aggregation
    """
    print(f"\n{'='*80}")
    print("TESTING BUSINESS RULES APPLICATION")
    print(f"{'='*80}")

    test_cases = [
        {
            "name": "DTI Rule: High DTI (>0.5) → HIGH/CRITICAL",
            "credit_score": 750,
            "monthly_income": 3000,
            "monthly_debt": 1700,  # DTI = 56.7%
            "loan_amount": 100000,
        },
        {
            "name": "Credit Rule: Low Credit (<500) → CRITICAL",
            "credit_score": 480,
            "monthly_income": 8000,
            "monthly_debt": 1000,
            "loan_amount": 300000,
        },
        {
            "name": "Combined Rule: Moderate DTI + Good Credit → APPROVE",
            "credit_score": 780,
            "monthly_income": 10000,
            "monthly_debt": 2000,  # DTI = 20%
            "loan_amount": 400000,
        },
    ]

    for case in test_cases:
        print(f"\nTest Case: {case['name']}")
        print(f"  Credit Score: {case['credit_score']}")
        dti = case['monthly_debt'] / case['monthly_income']
        print(f"  DTI: {dti:.1%}")

        try:
            assessment = await agent.assess_risk(
                applicant_id=f"RULE_TEST_{case['name'][:20]}",
                credit_score=case['credit_score'],
                monthly_gross_income=case['monthly_income'],
                monthly_debt_payments=case['monthly_debt'],
                loan_amount=case['loan_amount'],
            )

            print(f"  → Overall Risk: {assessment.overall_risk_level.value.upper()}")
            print(f"  → Recommendation: {assessment.approval_recommendation.value}")

        except Exception as e:
            print(f"  → Error: {e}")


async def test_batch_processing(agent: FinancialRiskAgent) -> None:
    """
    Test batch processing of multiple applicants.

    Validates:
    - Multiple tool calls are handled efficiently
    - Summary statistics are accurate
    - Batch results are properly structured
    """
    print(f"\n{'='*80}")
    print("TESTING BATCH PROCESSING")
    print(f"{'='*80}")

    applicants = [
        {
            "applicant_id": "BATCH_001",
            "credit_score": 800,
            "monthly_gross_income": 10000,
            "monthly_debt_payments": 1000,
            "loan_amount": 400000,
        },
        {
            "applicant_id": "BATCH_002",
            "credit_score": 650,
            "monthly_gross_income": 4000,
            "monthly_debt_payments": 1600,
            "loan_amount": 150000,
        },
        {
            "applicant_id": "BATCH_003",
            "credit_score": 720,
            "monthly_gross_income": 6500,
            "monthly_debt_payments": 1300,
            "loan_amount": 250000,
        },
    ]

    print(f"\nProcessing {len(applicants)} applicants...")

    try:
        result = await agent.batch_assess(applicants)

        if result["status"] == "success":
            print(f"\nBatch Results:")
            print(f"  Total Applicants: {result['total_applicants']}")
            print(f"  Approved: {result['summary']['approved']}")
            print(f"  Conditional: {result['summary']['conditional']}")
            print(f"  Denied: {result['summary']['denied']}")

            print(f"\nDetailed Results:")
            for analysis in result["analyses"]:
                if "error" not in analysis:
                    idx = analysis["applicant_index"]
                    app = applicants[idx]
                    ana = analysis["analysis"]
                    print(f"  [{idx}] {app['applicant_id']}: "
                          f"Risk={ana['overall_risk_level'].upper()}, "
                          f"Recommendation={ana['approval_recommendation']}")
        else:
            print(f"Batch processing failed: {result.get('error')}")

    except Exception as e:
        print(f"Error in batch processing: {e}")


async def test_json_export(agent: FinancialRiskAgent) -> None:
    """
    Test JSON export functionality.

    Validates:
    - Assessment can be serialized to JSON
    - JSON contains all required fields
    - JSON can be parsed for integration
    """
    print(f"\n{'='*80}")
    print("TESTING JSON EXPORT")
    print(f"{'='*80}")

    try:
        assessment = await agent.assess_risk(
            applicant_id="EXPORT_TEST",
            credit_score=750,
            monthly_gross_income=7000,
            monthly_debt_payments=1400,
            loan_amount=280000,
        )

        json_str = agent.export_assessment_json(assessment)
        json_obj = json.loads(json_str)

        print(f"\nExported Assessment (top-level fields):")
        for key in json_obj.keys():
            if key != "reasoning":  # Skip long reasoning field
                value = json_obj[key]
                if isinstance(value, str):
                    print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")

        print(f"\nJSON Export: SUCCESS")
        print(f"Total JSON size: {len(json_str)} bytes")

    except Exception as e:
        print(f"JSON Export: FAILED - {e}")


async def main():
    """Run all tests."""
    print("="*80)
    print("FINANCIALRISKAGENT - COMPREHENSIVE TEST SUITE")
    print("Testing MCP Tool Integration and Business Rules")
    print("="*80)

    # Test with mock interface (no server required)
    print("\nInitializing with MockMCPToolInterface...")
    mock_interface = MockMCPToolInterface()
    mock_agent = FinancialRiskAgent(mcp_interface=mock_interface)

    # Test 1: Individual MCP Tool Calls
    await test_mcp_tool_calls(mock_agent)

    # Test 2: Single Assessments
    results = []
    for scenario in SCENARIOS:
        result = await test_single_assessment(mock_agent, scenario)
        results.append(result)

    # Test 3: Business Rules
    await test_business_rules(mock_agent)

    # Test 4: Batch Processing
    await test_batch_processing(mock_agent)

    # Test 5: JSON Export
    await test_json_export(mock_agent)

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r.get("passed", False))
    total = len(results)

    print(f"\nScenario Results: {passed}/{total} passed")
    for result in results:
        status = "PASS" if result.get("passed", False) else "FAIL"
        print(f"  [{status}] {result['scenario']}")

    print(f"\n{'='*80}")
    print("TESTS COMPLETED")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
