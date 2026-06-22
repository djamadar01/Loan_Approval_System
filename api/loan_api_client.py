"""
Client library for the Loan Application API.

Provides a high-level client for submitting loan applications and handling responses.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

import httpx
from pydantic import ValidationError

# Import request/response models
from loan_application_api import (
    LoanApplicationRequest,
    LoanDecisionResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)


class LoanApplicationClient:
    """Client for interacting with the Loan Application API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        verify_ssl: bool = True
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            verify=verify_ssl
        )
        logger.info(f"Initialized LoanApplicationClient: {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Closed LoanApplicationClient")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check API server health.

        Returns:
            Dictionary with health status

        Raises:
            httpx.HTTPError: If request fails
        """
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()

    async def submit_application(
        self,
        applicant_id: str,
        profile: Dict[str, Any],
        credit_score: int,
        loan_amount: float,
        tenure: int,
        liabilities: float,
        location: str,
        timestamp: Optional[str] = None
    ) -> LoanDecisionResponse:
        """
        Submit a loan application.

        Args:
            applicant_id: Unique applicant identifier
            profile: Applicant profile dictionary containing:
                - name: Applicant name
                - age: Age in years
                - employment_status: full_time, part_time, self_employed, unemployed
                - employment_years: Years of employment
                - education_level: high_school, bachelor, graduate
                - annual_income: Annual income in currency units
                - monthly_expenses: Monthly expenses
                - savings: Savings amount
                - existing_loans: Number of existing loans
            credit_score: Credit score (300-850)
            loan_amount: Requested loan amount
            tenure: Loan tenure in months
            liabilities: Total existing liabilities
            location: Applicant location
            timestamp: Application timestamp (defaults to current time)

        Returns:
            LoanDecisionResponse with decision details

        Raises:
            httpx.HTTPError: If request fails
            ValidationError: If response validation fails
            ValueError: If input validation fails
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        try:
            request = LoanApplicationRequest(
                applicant_id=applicant_id,
                profile=profile,
                credit_score=credit_score,
                loan_amount=loan_amount,
                tenure=tenure,
                liabilities=liabilities,
                location=location,
                timestamp=timestamp
            )
        except ValidationError as e:
            logger.error(f"Request validation failed: {e}")
            raise

        logger.info(
            f"Submitting application for {applicant_id}: "
            f"loan_amount={loan_amount}, tenure={tenure} months"
        )

        try:
            response = await self.client.post(
                "/submit-application",
                json=request.model_dump()
            )
            response.raise_for_status()

            # Parse response
            response_data = response.json()
            decision = LoanDecisionResponse(**response_data)

            logger.info(
                f"Application processed: case_id={decision.case_id}, "
                f"classification={decision.classification}, "
                f"risk_score={decision.risk_score:.1f}"
            )

            return decision

        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed with status {e.response.status_code}")
            try:
                error_data = e.response.json()
                logger.error(f"Error details: {error_data}")
            except:
                logger.error(f"Response body: {e.response.text}")
            raise
        except ValidationError as e:
            logger.error(f"Response validation failed: {e}")
            raise

    async def submit_batch_applications(
        self,
        applications: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Submit multiple applications sequentially.

        Args:
            applications: List of application dictionaries with required fields

        Returns:
            Dictionary with results:
                - processed: Count of successfully processed applications
                - decisions: List of LoanDecisionResponse objects
                - errors: List of error details
                - total_processing_time_ms: Total processing time

        Example:
            ```python
            async with LoanApplicationClient() as client:
                results = await client.submit_batch_applications([
                    {
                        "applicant_id": "APP001",
                        "profile": {...},
                        "credit_score": 720,
                        ...
                    },
                    ...
                ])
            ```
        """
        decisions = []
        errors = []
        total_time = 0.0

        logger.info(f"Processing batch of {len(applications)} applications")

        for app_data in applications:
            try:
                decision = await self.submit_application(**app_data)
                decisions.append(decision)
                total_time += decision.processing_time_ms

            except Exception as e:
                error_info = {
                    "applicant_id": app_data.get("applicant_id", "unknown"),
                    "error": str(e),
                    "type": type(e).__name__
                }
                errors.append(error_info)
                logger.error(f"Failed to process application: {error_info}")

        logger.info(
            f"Batch processing complete: "
            f"processed={len(decisions)}, errors={len(errors)}, "
            f"total_time={total_time:.1f}ms"
        )

        return {
            "processed": len(decisions),
            "decisions": decisions,
            "errors": errors,
            "total_processing_time_ms": total_time
        }


class SyncLoanApplicationClient:
    """Synchronous wrapper around the async client."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        verify_ssl: bool = True
    ):
        """Initialize the synchronous client."""
        import asyncio

        self.base_url = base_url
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client = None
        self._loop = None

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, will create one in methods
            pass

    def _get_loop(self):
        """Get or create event loop."""
        import asyncio

        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

        return self._loop

    async def _init_client(self):
        """Initialize async client."""
        if self._client is None:
            self._client = LoanApplicationClient(
                base_url=self.base_url,
                timeout=self.timeout,
                verify_ssl=self.verify_ssl
            )

    def health_check(self) -> Dict[str, Any]:
        """Check API server health."""
        loop = self._get_loop()
        return loop.run_until_complete(self._run_async(self._health_check_async()))

    async def _health_check_async(self) -> Dict[str, Any]:
        """Async health check."""
        await self._init_client()
        return await self._client.health_check()

    def submit_application(
        self,
        applicant_id: str,
        profile: Dict[str, Any],
        credit_score: int,
        loan_amount: float,
        tenure: int,
        liabilities: float,
        location: str,
        timestamp: Optional[str] = None
    ) -> LoanDecisionResponse:
        """Submit a loan application (synchronous)."""
        loop = self._get_loop()
        return loop.run_until_complete(
            self._submit_application_async(
                applicant_id, profile, credit_score, loan_amount,
                tenure, liabilities, location, timestamp
            )
        )

    async def _submit_application_async(
        self,
        applicant_id: str,
        profile: Dict[str, Any],
        credit_score: int,
        loan_amount: float,
        tenure: int,
        liabilities: float,
        location: str,
        timestamp: Optional[str] = None
    ) -> LoanDecisionResponse:
        """Async submit application."""
        await self._init_client()
        return await self._client.submit_application(
            applicant_id, profile, credit_score, loan_amount,
            tenure, liabilities, location, timestamp
        )

    def close(self):
        """Close the client."""
        import asyncio

        if self._client:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(self._client.close())


# Convenience functions for simple usage

def submit_loan_application_sync(
    applicant_id: str,
    profile: Dict[str, Any],
    credit_score: int,
    loan_amount: float,
    tenure: int,
    liabilities: float,
    location: str,
    api_url: str = "http://localhost:8000"
) -> LoanDecisionResponse:
    """
    Convenience function for synchronous application submission.

    Args:
        applicant_id: Unique applicant identifier
        profile: Applicant profile dictionary
        credit_score: Credit score
        loan_amount: Requested loan amount
        tenure: Loan tenure in months
        liabilities: Total existing liabilities
        location: Applicant location
        api_url: API server URL

    Returns:
        LoanDecisionResponse with decision details

    Example:
        ```python
        decision = submit_loan_application_sync(
            applicant_id="APP001",
            profile={
                "name": "John Doe",
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
            tenure=60,
            liabilities=10000,
            location="New York, NY"
        )
        print(f"Decision: {decision.classification}")
        print(f"Risk Score: {decision.risk_score}")
        ```
    """
    client = SyncLoanApplicationClient(base_url=api_url)
    try:
        return client.submit_application(
            applicant_id=applicant_id,
            profile=profile,
            credit_score=credit_score,
            loan_amount=loan_amount,
            tenure=tenure,
            liabilities=liabilities,
            location=location
        )
    finally:
        client.close()
