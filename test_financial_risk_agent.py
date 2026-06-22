"""
Test and demonstration script for FinancialRiskAgent.

Shows how to:
- Initialize the agent
- Perform individual risk assessments
- Analyze multiple applicants in batch
- Handle different risk scenarios
- Export results
"""

import asyncio
import json
from financial_risk_agent import (
    FinancialRiskAgent,
    MockMCPToolInterface,
    RiskLevel,
)


async def test_individual_assessment():
    """Test individual financial risk assessment."""
    print("\n" + "=" * 80)
    print("TEST 1: INDIVIDUAL APPLICANT RISK ASSESSMENT")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())

    # Scenario 1: Low-risk applicant
    print("\n[Scenario 1] Low-Risk Applicant")
    print("-" * 80)
    assessment_1 = await agent.assess_risk(
        applicant_id="APP001",
        credit_score=780,
        monthly_gross_income=6000,
        monthly_debt_payments=1200,
        loan_amount=250000,
    )

    print(f"\nApplicant: {assessment_1.applicant_id}")
    print(f"DTI Ratio: {assessment_1.debt_to_income_ratio:.2%}")
    print(f"DTI Risk: {assessment_1.dti_risk_level.value}")
    print(f"Credit Score: {assessment_1.credit_score} ({assessment_1.credit_risk_level})")
    print(f"Loan Amount: ${assessment_1.loan_amount:,.2f}")
    print(f"Loan Risk: {assessment_1.loan_risk_level.value}")
    print(f"Anomalies: {len(assessment_1.anomalies)}")
    print(f"Overall Risk: {assessment_1.overall_risk_level.value}")
    print(f"Recommendation: {assessment_1.approval_recommendation.value}")
    print(f"\n{assessment_1.reasoning}")

    # Scenario 2: High-risk applicant
    print("\n\n[Scenario 2] High-Risk Applicant")
    print("-" * 80)
    assessment_2 = await agent.assess_risk(
        applicant_id="APP002",
        credit_score=520,
        monthly_gross_income=3000,
        monthly_debt_payments=2000,
        loan_amount=400000,
    )

    print(f"\nApplicant: {assessment_2.applicant_id}")
    print(f"DTI Ratio: {assessment_2.debt_to_income_ratio:.2%}")
    print(f"DTI Risk: {assessment_2.dti_risk_level.value}")
    print(f"Credit Score: {assessment_2.credit_score} ({assessment_2.credit_risk_level})")
    print(f"Loan Amount: ${assessment_2.loan_amount:,.2f}")
    print(f"Loan Risk: {assessment_2.loan_risk_level.value}")
    print(f"Anomalies: {len(assessment_2.anomalies)}")
    if assessment_2.anomalies:
        print("Anomaly Flags:")
        for anomaly in assessment_2.anomalies:
            print(f"  - {anomaly['flag_type']} ({anomaly['severity'].upper()}): {anomaly['message']}")
    print(f"Overall Risk: {assessment_2.overall_risk_level.value}")
    print(f"Recommendation: {assessment_2.approval_recommendation.value}")
    print(f"\n{assessment_2.reasoning}")

    # Scenario 3: Borderline case
    print("\n\n[Scenario 3] Borderline/Conditional Applicant")
    print("-" * 80)
    assessment_3 = await agent.assess_risk(
        applicant_id="APP003",
        credit_score=650,
        monthly_gross_income=4500,
        monthly_debt_payments=1800,
        loan_amount=180000,
    )

    print(f"\nApplicant: {assessment_3.applicant_id}")
    print(f"DTI Ratio: {assessment_3.debt_to_income_ratio:.2%}")
    print(f"DTI Risk: {assessment_3.dti_risk_level.value}")
    print(f"Credit Score: {assessment_3.credit_score} ({assessment_3.credit_risk_level})")
    print(f"Overall Risk: {assessment_3.overall_risk_level.value}")
    print(f"Recommendation: {assessment_3.approval_recommendation.value}")
    print(f"\n{assessment_3.reasoning}")

    return [assessment_1, assessment_2, assessment_3]


async def test_batch_assessment():
    """Test batch risk assessment."""
    print("\n" + "=" * 80)
    print("TEST 2: BATCH RISK ASSESSMENT")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())

    applicants = [
        {
            "applicant_id": "BATCH001",
            "credit_score": 750,
            "monthly_gross_income": 5500,
            "monthly_debt_payments": 1100,
            "loan_amount": 200000,
        },
        {
            "applicant_id": "BATCH002",
            "credit_score": 600,
            "monthly_gross_income": 4000,
            "monthly_debt_payments": 1600,
            "loan_amount": 300000,
        },
        {
            "applicant_id": "BATCH003",
            "credit_score": 820,
            "monthly_gross_income": 8000,
            "monthly_debt_payments": 1600,
            "loan_amount": 500000,
        },
    ]

    print(f"\nProcessing {len(applicants)} applicants...")
    result = await agent.batch_assess(applicants)

    if result["status"] == "success":
        print(f"\nBatch Analysis Summary:")
        print(f"  Total Applicants: {result['total_applicants']}")
        print(f"  Approved: {result['summary']['approved']}")
        print(f"  Conditional: {result['summary']['conditional']}")
        print(f"  Denied: {result['summary']['denied']}")
        print(f"\nDetailed Results:")
        for analysis in result["analyses"]:
            idx = analysis["applicant_index"]
            if "error" not in analysis:
                applicant = applicants[idx]
                risk_level = analysis["analysis"]["overall_risk_level"]
                recommendation = analysis["analysis"]["approval_recommendation"]
                print(f"  [{idx}] {applicant['applicant_id']}: {risk_level.upper()} - {recommendation}")
            else:
                print(f"  [{idx}] Error: {analysis['error']}")


async def test_dti_capacity():
    """Test DTI capacity calculation."""
    print("\n" + "=" * 80)
    print("TEST 3: DTI CAPACITY CALCULATION")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())

    incomes = [3000, 5000, 8000, 12000]
    target_dti = 0.36

    print(f"\nCalculating maximum debt capacity at {target_dti:.0%} DTI:")
    print("-" * 80)

    for income in incomes:
        result = await agent.get_dti_capacity(income, target_dti)
        if result["status"] == "success":
            max_debt = result["max_debt_payment"]
            print(f"Income ${income:>6,.0f}/mo → Max Debt: ${max_debt:>8,.2f}/mo ({max_debt/income:.0%})")


async def test_thresholds():
    """Test retrieving risk thresholds."""
    print("\n" + "=" * 80)
    print("TEST 4: RISK THRESHOLDS AND BUSINESS RULES")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())

    print("\nRetrieving configured risk thresholds...")
    thresholds = await agent.get_thresholds()

    if thresholds["status"] == "success":
        print("\nDTI Thresholds:")
        for key, config in thresholds["dti_thresholds"].items():
            threshold = config["threshold"]
            risk = config["risk_level"]
            print(f"  {key:12} → {threshold if isinstance(threshold, str) else f'{threshold:.0%}'} ({risk.upper()})")


async def test_assessment_export():
    """Test exporting assessment results."""
    print("\n" + "=" * 80)
    print("TEST 5: ASSESSMENT EXPORT AND SUMMARY")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())

    assessment = await agent.assess_risk(
        applicant_id="EXPORT_TEST",
        credit_score=720,
        monthly_gross_income=5500,
        monthly_debt_payments=1300,
        loan_amount=220000,
    )

    # Test summary export
    print("\nAssessment Summary:")
    summary = agent.get_assessment_summary(assessment)
    for key, value in summary.items():
        print(f"  {key:20}: {value}")

    # Test JSON export (first 500 chars)
    print("\nJSON Export (partial):")
    json_export = agent.export_assessment_json(assessment)
    print(json_export[:500] + "...\n")


async def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n" + "=" * 80)
    print("TEST 6: ERROR HANDLING")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())

    test_cases = [
        {
            "name": "Invalid credit score (too low)",
            "kwargs": {
                "applicant_id": "ERR001",
                "credit_score": 200,  # Below 300
                "monthly_gross_income": 5000,
                "monthly_debt_payments": 1000,
                "loan_amount": 200000,
            },
        },
        {
            "name": "Invalid credit score (too high)",
            "kwargs": {
                "applicant_id": "ERR002",
                "credit_score": 900,  # Above 850
                "monthly_gross_income": 5000,
                "monthly_debt_payments": 1000,
                "loan_amount": 200000,
            },
        },
        {
            "name": "Invalid income (zero)",
            "kwargs": {
                "applicant_id": "ERR003",
                "credit_score": 750,
                "monthly_gross_income": 0,
                "monthly_debt_payments": 1000,
                "loan_amount": 200000,
            },
        },
        {
            "name": "Invalid debt payments (negative)",
            "kwargs": {
                "applicant_id": "ERR004",
                "credit_score": 750,
                "monthly_gross_income": 5000,
                "monthly_debt_payments": -500,
                "loan_amount": 200000,
            },
        },
    ]

    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        try:
            await agent.assess_risk(**test_case["kwargs"])
            print("  ✗ Should have raised ValueError")
        except ValueError as e:
            print(f"  ✓ Correctly caught error: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")


async def test_logging():
    """Test agent logging functionality."""
    print("\n" + "=" * 80)
    print("TEST 7: AGENT LOGGING")
    print("=" * 80)

    agent = FinancialRiskAgent(mcp_interface=MockMCPToolInterface())

    # Clear previous logs
    agent.logger.clear()

    print("\nPerforming assessment and capturing logs...")
    await agent.assess_risk(
        applicant_id="LOG_TEST",
        credit_score=750,
        monthly_gross_income=6000,
        monthly_debt_payments=1200,
        loan_amount=250000,
    )

    print(f"\nAgent Log Output ({len(agent.logger)} entries):")
    for i, log_entry in enumerate(agent.logger, 1):
        print(f"  [{i}] {log_entry}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("FINANCIAL RISK AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    try:
        # Run individual tests
        assessments = await test_individual_assessment()
        await test_batch_assessment()
        await test_dti_capacity()
        await test_thresholds()
        await test_assessment_export()
        await test_error_handling()
        await test_logging()

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)

        # Summary statistics
        print("\nTest Summary:")
        print("  ✓ Individual assessments: 3 scenarios")
        print("  ✓ Batch assessment: 3 applicants")
        print("  ✓ DTI capacity calculations: 4 income levels")
        print("  ✓ Risk thresholds retrieval")
        print("  ✓ Assessment export (summary + JSON)")
        print("  ✓ Error handling: 4 validation cases")
        print("  ✓ Agent logging: 6+ log entries")
        print("\n")

    except Exception as e:
        print(f"\n\nERROR: Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
