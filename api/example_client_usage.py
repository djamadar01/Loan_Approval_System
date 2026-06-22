"""
Example usage of the Loan Application API client.

This module demonstrates:
1. Synchronous client usage
2. Asynchronous client usage
3. Batch processing
4. Error handling
5. Response parsing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import client
from loan_api_client import (
    LoanApplicationClient,
    SyncLoanApplicationClient,
    submit_loan_application_sync
)


# ============================================================================
# EXAMPLE 1: SYNCHRONOUS CLIENT
# ============================================================================

def example_1_sync_client():
    """Example 1: Using synchronous client."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Synchronous Client Usage")
    logger.info("=" * 60)

    try:
        # Create client
        client = SyncLoanApplicationClient(base_url="http://localhost:8000")

        # Check health
        try:
            health = client.health_check()
            logger.info(f"API Health: {health['status']}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            logger.info("Make sure the API server is running!")
            return

        # Submit application
        profile = {
            "name": "John Smith",
            "age": 35,
            "employment_status": "full_time",
            "employment_years": 8,
            "education_level": "bachelor",
            "annual_income": 75000,
            "monthly_expenses": 2500,
            "savings": 15000,
            "existing_loans": 1
        }

        logger.info("Submitting loan application...")
        decision = client.submit_application(
            applicant_id="APP-SYNC-001",
            profile=profile,
            credit_score=720,
            loan_amount=25000,
            tenure=60,
            liabilities=10000,
            location="New York, NY"
        )

        # Display results
        logger.info(f"Case ID: {decision.case_id}")
        logger.info(f"Classification: {decision.classification}")
        logger.info(f"Risk Score: {decision.risk_score:.1f}/100")
        logger.info(f"Confidence: {decision.confidence:.2%}")
        logger.info(f"Processing Time: {decision.processing_time_ms:.1f}ms")

        # Display key factors
        logger.info("\nKey Factors:")
        for factor in decision.factors[:3]:
            logger.info(f"  - {factor.factor_name}: {factor.impact} (weight: {factor.weight:.0%})")

        # Display explanation
        logger.info(f"\nDecision Explanation:\n{decision.explanation}")

        client.close()

    except Exception as e:
        logger.error(f"Error in sync client example: {e}", exc_info=True)


# ============================================================================
# EXAMPLE 2: ASYNCHRONOUS CLIENT
# ============================================================================

async def example_2_async_client():
    """Example 2: Using asynchronous client."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 2: Asynchronous Client Usage")
    logger.info("=" * 60)

    try:
        async with LoanApplicationClient(base_url="http://localhost:8000") as client:
            # Check health
            try:
                health = await client.health_check()
                logger.info(f"API Health: {health['status']}")
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                logger.info("Make sure the API server is running!")
                return

            # Submit application
            profile = {
                "name": "Sarah Johnson",
                "age": 40,
                "employment_status": "full_time",
                "employment_years": 15,
                "education_level": "graduate",
                "annual_income": 120000,
                "monthly_expenses": 2000,
                "savings": 50000,
                "existing_loans": 0
            }

            logger.info("Submitting loan application asynchronously...")
            decision = await client.submit_application(
                applicant_id="APP-ASYNC-001",
                profile=profile,
                credit_score=800,
                loan_amount=20000,
                tenure=60,
                liabilities=5000,
                location="San Francisco, CA"
            )

            # Display results
            logger.info(f"Case ID: {decision.case_id}")
            logger.info(f"Classification: {decision.classification}")
            logger.info(f"Risk Score: {decision.risk_score:.1f}/100")
            logger.info(f"Confidence: {decision.confidence:.2%}")

    except Exception as e:
        logger.error(f"Error in async client example: {e}", exc_info=True)


# ============================================================================
# EXAMPLE 3: BATCH PROCESSING
# ============================================================================

async def example_3_batch_processing():
    """Example 3: Batch processing multiple applications."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 3: Batch Processing")
    logger.info("=" * 60)

    try:
        async with LoanApplicationClient(base_url="http://localhost:8000") as client:
            # Create batch of applications
            applications = [
                {
                    "applicant_id": "APP-BATCH-001",
                    "profile": {
                        "name": "Alice Cooper",
                        "age": 32,
                        "employment_status": "full_time",
                        "employment_years": 6,
                        "education_level": "bachelor",
                        "annual_income": 65000,
                        "monthly_expenses": 2200,
                        "savings": 12000,
                        "existing_loans": 1
                    },
                    "credit_score": 710,
                    "loan_amount": 20000,
                    "tenure": 48,
                    "liabilities": 8000,
                    "location": "Boston, MA"
                },
                {
                    "applicant_id": "APP-BATCH-002",
                    "profile": {
                        "name": "Bob Davis",
                        "age": 28,
                        "employment_status": "part_time",
                        "employment_years": 2,
                        "education_level": "high_school",
                        "annual_income": 35000,
                        "monthly_expenses": 1800,
                        "savings": 3000,
                        "existing_loans": 2
                    },
                    "credit_score": 620,
                    "loan_amount": 15000,
                    "tenure": 60,
                    "liabilities": 12000,
                    "location": "Chicago, IL"
                },
                {
                    "applicant_id": "APP-BATCH-003",
                    "profile": {
                        "name": "Carol White",
                        "age": 45,
                        "employment_status": "full_time",
                        "employment_years": 12,
                        "education_level": "graduate",
                        "annual_income": 95000,
                        "monthly_expenses": 2800,
                        "savings": 35000,
                        "existing_loans": 0
                    },
                    "credit_score": 770,
                    "loan_amount": 30000,
                    "tenure": 72,
                    "liabilities": 3000,
                    "location": "Seattle, WA"
                }
            ]

            logger.info(f"Processing batch of {len(applications)} applications...")
            results = await client.submit_batch_applications(applications)

            # Display summary
            logger.info(f"\nBatch Processing Results:")
            logger.info(f"  Processed: {results['processed']}/{len(applications)}")
            logger.info(f"  Errors: {len(results['errors'])}")
            logger.info(f"  Total Time: {results['total_processing_time_ms']:.1f}ms")

            # Display individual results
            logger.info("\nDecisions:")
            for decision in results['decisions']:
                logger.info(
                    f"  {decision.case_id} - {decision.classification} "
                    f"(risk: {decision.risk_score:.1f}, confidence: {decision.confidence:.2%})"
                )

            # Display errors if any
            if results['errors']:
                logger.info("\nErrors:")
                for error in results['errors']:
                    logger.error(f"  {error['applicant_id']}: {error['error']}")

    except Exception as e:
        logger.error(f"Error in batch processing example: {e}", exc_info=True)


# ============================================================================
# EXAMPLE 4: ERROR HANDLING
# ============================================================================

async def example_4_error_handling():
    """Example 4: Error handling and validation."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 4: Error Handling")
    logger.info("=" * 60)

    try:
        async with LoanApplicationClient(base_url="http://localhost:8000") as client:
            # Example 1: Invalid credit score
            logger.info("\nTesting invalid credit score...")
            try:
                decision = await client.submit_application(
                    applicant_id="APP-ERROR-001",
                    profile={
                        "name": "Test User",
                        "age": 35,
                        "employment_status": "full_time",
                        "employment_years": 5,
                        "education_level": "bachelor",
                        "annual_income": 75000,
                        "monthly_expenses": 2500,
                        "savings": 15000,
                        "existing_loans": 1
                    },
                    credit_score=200,  # Below minimum
                    loan_amount=25000,
                    tenure=60,
                    liabilities=10000,
                    location="New York, NY"
                )
            except Exception as e:
                logger.info(f"  Expected error caught: {type(e).__name__}")
                logger.info(f"  Error details: {str(e)[:100]}...")

            # Example 2: Invalid age
            logger.info("\nTesting invalid age...")
            try:
                decision = await client.submit_application(
                    applicant_id="APP-ERROR-002",
                    profile={
                        "name": "Test User",
                        "age": 15,  # Below minimum
                        "employment_status": "full_time",
                        "employment_years": 5,
                        "education_level": "bachelor",
                        "annual_income": 75000,
                        "monthly_expenses": 2500,
                        "savings": 15000,
                        "existing_loans": 1
                    },
                    credit_score=720,
                    loan_amount=25000,
                    tenure=60,
                    liabilities=10000,
                    location="New York, NY"
                )
            except Exception as e:
                logger.info(f"  Expected error caught: {type(e).__name__}")
                logger.info(f"  Error details: {str(e)[:100]}...")

            # Example 3: Invalid tenure
            logger.info("\nTesting invalid tenure...")
            try:
                decision = await client.submit_application(
                    applicant_id="APP-ERROR-003",
                    profile={
                        "name": "Test User",
                        "age": 35,
                        "employment_status": "full_time",
                        "employment_years": 5,
                        "education_level": "bachelor",
                        "annual_income": 75000,
                        "monthly_expenses": 2500,
                        "savings": 15000,
                        "existing_loans": 1
                    },
                    credit_score=720,
                    loan_amount=25000,
                    tenure=500,  # Above maximum
                    liabilities=10000,
                    location="New York, NY"
                )
            except Exception as e:
                logger.info(f"  Expected error caught: {type(e).__name__}")
                logger.info(f"  Error details: {str(e)[:100]}...")

    except Exception as e:
        logger.error(f"Error in error handling example: {e}", exc_info=True)


# ============================================================================
# EXAMPLE 5: CONVENIENCE FUNCTION
# ============================================================================

def example_5_convenience_function():
    """Example 5: Using convenience function."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 5: Convenience Function")
    logger.info("=" * 60)

    try:
        profile = {
            "name": "Michael Brown",
            "age": 38,
            "employment_status": "full_time",
            "employment_years": 10,
            "education_level": "bachelor",
            "annual_income": 90000,
            "monthly_expenses": 2800,
            "savings": 20000,
            "existing_loans": 1
        }

        logger.info("Using convenience function for single application...")
        decision = submit_loan_application_sync(
            applicant_id="APP-CONVENIENCE-001",
            profile=profile,
            credit_score=750,
            loan_amount=30000,
            tenure=60,
            liabilities=10000,
            location="Austin, TX"
        )

        logger.info(f"Case ID: {decision.case_id}")
        logger.info(f"Classification: {decision.classification}")
        logger.info(f"Risk Score: {decision.risk_score:.1f}")

    except Exception as e:
        logger.error(f"Error in convenience function example: {e}", exc_info=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all examples."""
    logger.info("Loan Application API - Client Usage Examples")
    logger.info("=" * 60)

    # Run synchronous example
    example_1_sync_client()
    logger.info("\n")

    # Run async example
    asyncio.run(example_2_async_client())
    logger.info("\n")

    # Run batch processing example
    asyncio.run(example_3_batch_processing())
    logger.info("\n")

    # Run error handling example
    asyncio.run(example_4_error_handling())
    logger.info("\n")

    # Run convenience function example
    example_5_convenience_function()

    logger.info("\n" + "=" * 60)
    logger.info("Examples completed!")


if __name__ == "__main__":
    main()
