"""
Example usage patterns for the Loan Application Orchestrator.

This module demonstrates:
1. Basic single application processing
2. Batch processing multiple applications
3. Custom agent implementations
4. Monitoring and logging
5. Integration patterns
6. Error handling and recovery
"""

import json
import logging
import time
from typing import List, Tuple
from datetime import datetime

from loan_orchestrator import (
    compile_loan_orchestrator,
    ApplicantProfile,
    FinancialData,
    ApplicationStatus,
    DecisionType,
    RiskLevel,
    execute_application,
    format_state_for_output,
    ApplicantProfileAgent,
    FinancialRiskAgent,
    LoanDecisionAgent,
    ComplianceOrchestratorAgent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Basic Single Application Processing
# ============================================================================

def example_1_basic_processing():
    """Example 1: Process a single loan application."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Basic Single Application Processing")
    logger.info("=" * 60)

    # Initialize orchestrator
    orchestrator = compile_loan_orchestrator()

    # Create applicant profile
    profile = ApplicantProfile(
        applicant_id="APP001",
        name="John Smith",
        age=35,
        employment_status="full_time",
        employment_years=8,
        education_level="bachelor",
        credit_score=720,
        existing_loans=1,
    )

    # Create financial data
    financial = FinancialData(
        annual_income=75000,
        monthly_expenses=2500,
        savings=15000,
        loan_amount=25000,
        loan_term_months=60,
    )

    # Execute application
    logger.info(f"Processing application for {profile.name}")
    result = execute_application(
        orchestrator,
        profile.applicant_id,
        profile,
        financial,
    )

    # Display results
    output = format_state_for_output(result)
    logger.info(f"Final Status: {output['status']}")
    logger.info(f"Decision: {output['loan_decision']['decision']}")
    logger.info(f"Decision Score: {output['loan_decision']['decision_score']:.2f}")
    logger.info(f"Approval Probability: {output['loan_decision']['approval_probability']:.2f}")

    return output


# ============================================================================
# EXAMPLE 2: Batch Processing Multiple Applications
# ============================================================================

def create_test_applications() -> List[Tuple[str, ApplicantProfile, FinancialData]]:
    """Create a set of test applications with varying profiles."""
    applications = [
        # Excellent applicant (likely approval)
        (
            "APP_EXCELLENT",
            ApplicantProfile(
                applicant_id="APP_EXCELLENT",
                name="Sarah Johnson",
                age=40,
                employment_status="full_time",
                employment_years=15,
                education_level="graduate",
                credit_score=800,
                existing_loans=0,
            ),
            FinancialData(
                annual_income=120000,
                monthly_expenses=2000,
                savings=50000,
                loan_amount=20000,
                loan_term_months=60,
            ),
        ),

        # Good applicant (likely approval)
        (
            "APP_GOOD",
            ApplicantProfile(
                applicant_id="APP_GOOD",
                name="Michael Chen",
                age=38,
                employment_status="full_time",
                employment_years=10,
                education_level="bachelor",
                credit_score=750,
                existing_loans=1,
            ),
            FinancialData(
                annual_income=90000,
                monthly_expenses=2800,
                savings=20000,
                loan_amount=30000,
                loan_term_months=60,
            ),
        ),

        # Average applicant (likely conditional approval)
        (
            "APP_AVERAGE",
            ApplicantProfile(
                applicant_id="APP_AVERAGE",
                name="Jennifer Lee",
                age=32,
                employment_status="full_time",
                employment_years=5,
                education_level="bachelor",
                credit_score=680,
                existing_loans=2,
            ),
            FinancialData(
                annual_income=60000,
                monthly_expenses=2400,
                savings=8000,
                loan_amount=20000,
                loan_term_months=48,
            ),
        ),

        # Below average applicant (likely manual review)
        (
            "APP_BELOW_AVG",
            ApplicantProfile(
                applicant_id="APP_BELOW_AVG",
                name="David Martinez",
                age=28,
                employment_status="part_time",
                employment_years=2,
                education_level="high_school",
                credit_score=620,
                existing_loans=3,
            ),
            FinancialData(
                annual_income=40000,
                monthly_expenses=2200,
                savings=3000,
                loan_amount=25000,
                loan_term_months=60,
            ),
        ),

        # Poor applicant (likely rejection)
        (
            "APP_POOR",
            ApplicantProfile(
                applicant_id="APP_POOR",
                name="Robert Wilson",
                age=25,
                employment_status="unemployed",
                employment_years=0,
                education_level="high_school",
                credit_score=480,
                existing_loans=4,
            ),
            FinancialData(
                annual_income=25000,
                monthly_expenses=2800,
                savings=500,
                loan_amount=35000,
                loan_term_months=72,
            ),
        ),
    ]

    return applications


def example_2_batch_processing():
    """Example 2: Batch process multiple applications."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 2: Batch Processing Multiple Applications")
    logger.info("=" * 60)

    # Initialize orchestrator
    orchestrator = compile_loan_orchestrator()

    # Create test applications
    applications = create_test_applications()

    # Process all applications
    results = []
    start_time = time.time()

    for app_id, profile, financial in applications:
        logger.info(f"Processing {app_id}: {profile.name}")

        result = execute_application(
            orchestrator,
            app_id,
            profile,
            financial,
        )

        output = format_state_for_output(result)
        results.append(output)

        logger.info(
            f"  Status: {output['status']}, "
            f"Decision: {output['loan_decision']['decision']}, "
            f"Score: {output['loan_decision']['decision_score']:.2f}"
        )

    elapsed = time.time() - start_time

    # Summary statistics
    logger.info("\n--- Batch Processing Summary ---")
    logger.info(f"Total Applications: {len(results)}")
    logger.info(f"Processing Time: {elapsed:.2f}s")
    logger.info(f"Average Time per Application: {elapsed / len(results):.2f}s")

    # Decision statistics
    decisions = [r['loan_decision']['decision'] for r in results]
    logger.info(f"\nDecision Breakdown:")
    logger.info(f"  Approved: {decisions.count('approved')}")
    logger.info(f"  Rejected: {decisions.count('rejected')}")
    logger.info(f"  Conditional Approval: {decisions.count('conditional_approval')}")
    logger.info(f"  Manual Review: {decisions.count('manual_review')}")

    return results


# ============================================================================
# EXAMPLE 3: Monitoring and Logging
# ============================================================================

def example_3_monitoring_and_logging():
    """Example 3: Monitor workflow execution and extract detailed logs."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 3: Monitoring and Logging")
    logger.info("=" * 60)

    # Initialize orchestrator
    orchestrator = compile_loan_orchestrator()

    # Create application
    profile = ApplicantProfile(
        applicant_id="APP_MONITORING",
        name="Emma Davis",
        age=36,
        employment_status="full_time",
        employment_years=7,
        education_level="bachelor",
        credit_score=710,
        existing_loans=1,
    )

    financial = FinancialData(
        annual_income=80000,
        monthly_expenses=2600,
        savings=12000,
        loan_amount=22000,
        loan_term_months=54,
    )

    # Execute application
    logger.info("Processing application with detailed monitoring")
    result = execute_application(
        orchestrator,
        profile.applicant_id,
        profile,
        financial,
    )

    # Extract execution timeline
    logger.info("\n--- Execution Timeline ---")
    total_time = 0
    for log_entry in result["execution_log"]:
        logger.info(
            f"{log_entry['step']}: {log_entry['status']}"
        )

    # Extract and display risk scores
    logger.info("\n--- Risk Assessment Details ---")
    if result["risk_assessment"]:
        risk = result["risk_assessment"]
        logger.info(f"Overall Risk Level: {risk['overall_risk_level']}")
        logger.info(f"Risk Score: {risk['risk_score']:.2f}")
        logger.info(f"Credit Risk: {risk['credit_risk']:.2f}")
        logger.info(f"Income Risk: {risk['income_risk']:.2f}")
        logger.info(f"Debt Risk: {risk['debt_risk']:.2f}")
        logger.info(f"Employment Risk: {risk['employment_risk']:.2f}")

        if risk["risk_factors"]:
            logger.info("Risk Factors:")
            for factor in risk["risk_factors"]:
                logger.info(f"  - {factor}")

        if risk["mitigating_factors"]:
            logger.info("Mitigating Factors:")
            for factor in risk["mitigating_factors"]:
                logger.info(f"  + {factor}")

    # Extract compliance details
    logger.info("\n--- Compliance Details ---")
    if result["compliance_result"]:
        compliance = result["compliance_result"]
        logger.info(f"Compliant: {compliance['is_compliant']}")
        logger.info("Compliance Checks:")
        for check_name, check_result in compliance["compliance_checks"].items():
            status = "✓" if check_result else "✗"
            logger.info(f"  {status} {check_name}")

        if compliance["flags"]:
            logger.info("Flags:")
            for flag in compliance["flags"]:
                logger.info(f"  ! {flag}")

        if compliance["required_actions"]:
            logger.info("Required Actions:")
            for action in compliance["required_actions"]:
                logger.info(f"  > {action}")

    # Error handling
    if result["errors"]:
        logger.error(f"\n--- Errors Encountered ({len(result['errors'])}) ---")
        for error in result["errors"]:
            logger.error(f"{error['step']}: {error['error']}")

    return result


# ============================================================================
# EXAMPLE 4: Decision Rationale Analysis
# ============================================================================

def example_4_decision_rationale():
    """Example 4: Analyze decision rationale for different profiles."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 4: Decision Rationale Analysis")
    logger.info("=" * 60)

    orchestrator = compile_loan_orchestrator()
    applications = create_test_applications()

    for app_id, profile, financial in applications:
        result = execute_application(
            orchestrator,
            app_id,
            profile,
            financial,
        )

        output = format_state_for_output(result)

        logger.info(f"\n--- {app_id}: {profile.name} ---")
        logger.info(f"Credit Score: {profile.credit_score}")
        logger.info(f"Employment: {profile.employment_status} ({profile.employment_years} years)")
        logger.info(f"Income: ${financial.annual_income:,.0f}")
        logger.info(f"Debt-to-Income: {output['financial_data']['debt_to_income_ratio']:.2%}")

        decision = output["loan_decision"]
        logger.info(f"\nDecision: {decision['decision']}")
        logger.info(f"Score: {decision['decision_score']:.2f}/100")
        logger.info(f"Approval Probability: {decision['approval_probability']:.2%}")
        logger.info(f"Rationale: {decision['rationale']}")

        if decision["conditions"]:
            logger.info("Conditions:")
            for cond in decision["conditions"]:
                logger.info(f"  - {cond}")

        if decision["required_documents"]:
            logger.info("Required Documents:")
            for doc in decision["required_documents"]:
                logger.info(f"  - {doc}")

    return


# ============================================================================
# EXAMPLE 5: Error Handling and Recovery
# ============================================================================

def example_5_error_handling():
    """Example 5: Demonstrate error handling and recovery."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 5: Error Handling and Recovery")
    logger.info("=" * 60)

    orchestrator = compile_loan_orchestrator()

    # Test case 1: Incomplete financial data
    logger.info("\nTest 1: Incomplete Financial Data")
    profile = ApplicantProfile(
        applicant_id="APP_ERROR1",
        name="Test User 1",
        age=30,
        employment_status="full_time",
        employment_years=3,
        education_level="bachelor",
        credit_score=650,
        existing_loans=1,
    )

    financial = FinancialData(
        annual_income=50000,
        monthly_expenses=1500,
        savings=3000,
        # Missing loan_amount and loan_term_months
    )

    result = execute_application(
        orchestrator,
        "APP_ERROR1",
        profile,
        financial,
    )

    output = format_state_for_output(result)
    logger.info(f"Status: {output['status']}")
    if output["errors"]:
        logger.info("Errors encountered:")
        for error in output["errors"]:
            logger.info(f"  {error['step']}: {error['error']}")

    # Test case 2: Extreme credit score
    logger.info("\nTest 2: Extreme Credit Score")
    profile = ApplicantProfile(
        applicant_id="APP_ERROR2",
        name="Test User 2",
        age=45,
        employment_status="full_time",
        employment_years=20,
        education_level="graduate",
        credit_score=850,  # Perfect score
        existing_loans=0,
    )

    financial = FinancialData(
        annual_income=200000,
        monthly_expenses=3000,
        savings=100000,
        loan_amount=50000,
        loan_term_months=120,
    )

    result = execute_application(
        orchestrator,
        "APP_ERROR2",
        profile,
        financial,
    )

    output = format_state_for_output(result)
    logger.info(f"Status: {output['status']}")
    logger.info(f"Decision: {output['loan_decision']['decision']}")
    logger.info(f"Decision Score: {output['loan_decision']['decision_score']:.2f}")

    return


# ============================================================================
# EXAMPLE 6: Comparative Analysis
# ============================================================================

def example_6_comparative_analysis():
    """Example 6: Compare decisions across similar profiles."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 6: Comparative Analysis")
    logger.info("=" * 60)

    orchestrator = compile_loan_orchestrator()

    # Create similar profiles with one variable difference
    profiles_to_compare = [
        # Variable 1: Credit Score Impact
        ("Credit 550", ApplicantProfile(
            applicant_id="COMP_CREDIT_550",
            name="Comp User 1",
            age=35, employment_status="full_time", employment_years=5,
            education_level="bachelor", credit_score=550, existing_loans=2,
        )),
        ("Credit 650", ApplicantProfile(
            applicant_id="COMP_CREDIT_650",
            name="Comp User 2",
            age=35, employment_status="full_time", employment_years=5,
            education_level="bachelor", credit_score=650, existing_loans=2,
        )),
        ("Credit 750", ApplicantProfile(
            applicant_id="COMP_CREDIT_750",
            name="Comp User 3",
            age=35, employment_status="full_time", employment_years=5,
            education_level="bachelor", credit_score=750, existing_loans=2,
        )),
    ]

    financial = FinancialData(
        annual_income=70000,
        monthly_expenses=2400,
        savings=10000,
        loan_amount=20000,
        loan_term_months=60,
    )

    logger.info("\nCredit Score Impact Analysis:")
    logger.info("-" * 80)
    logger.info(f"{'Credit Score':<15} {'Profile Risk':<15} {'Decision':<20} {'Score':<10}")
    logger.info("-" * 80)

    for label, profile in profiles_to_compare:
        result = execute_application(
            orchestrator,
            profile.applicant_id,
            profile,
            financial,
        )

        output = format_state_for_output(result)
        profile_risk = output["applicant_profile"]["profile_risk_score"]
        decision = output["loan_decision"]["decision"]
        score = output["loan_decision"]["decision_score"]

        logger.info(
            f"{profile.credit_score:<15} {profile_risk:<15.2f} "
            f"{decision:<20} {score:<10.2f}"
        )

    return


# ============================================================================
# EXAMPLE 7: Data Export and Reporting
# ============================================================================

def example_7_data_export():
    """Example 7: Export results for reporting and analysis."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 7: Data Export and Reporting")
    logger.info("=" * 60)

    orchestrator = compile_loan_orchestrator()
    applications = create_test_applications()

    # Process all applications
    all_results = []
    for app_id, profile, financial in applications:
        result = execute_application(
            orchestrator,
            app_id,
            profile,
            financial,
        )
        output = format_state_for_output(result)
        all_results.append(output)

    # Export to JSON
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_applications": len(all_results),
        "applications": all_results,
        "summary": {
            "approved": sum(1 for r in all_results if r["status"] == "approved"),
            "rejected": sum(1 for r in all_results if r["status"] == "rejected"),
            "flagged": sum(1 for r in all_results if r["status"] == "flagged"),
            "compliance_checked": sum(1 for r in all_results
                                     if r["status"] == "compliance_checked"),
        },
    }

    # Save to file
    export_file = "/tmp/loan_applications_export.json"
    with open(export_file, "w") as f:
        json.dump(export_data, f, indent=2, default=str)

    logger.info(f"\nExport Summary:")
    logger.info(f"Total Applications: {export_data['total_applications']}")
    logger.info(f"Approved: {export_data['summary']['approved']}")
    logger.info(f"Rejected: {export_data['summary']['rejected']}")
    logger.info(f"Flagged: {export_data['summary']['flagged']}")
    logger.info(f"Compliance Checked: {export_data['summary']['compliance_checked']}")
    logger.info(f"\nExport saved to: {export_file}")

    return export_data


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all examples."""
    logger.info("\n")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 10 + "LOAN ORCHESTRATOR EXAMPLES" + " " * 23 + "║")
    logger.info("╚" + "═" * 58 + "╝")

    try:
        # Example 1
        example_1_basic_processing()

        # Example 2
        example_2_batch_processing()

        # Example 3
        example_3_monitoring_and_logging()

        # Example 4
        example_4_decision_rationale()

        # Example 5
        example_5_error_handling()

        # Example 6
        example_6_comparative_analysis()

        # Example 7
        example_7_data_export()

        logger.info("\n" + "=" * 60)
        logger.info("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during example execution: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
