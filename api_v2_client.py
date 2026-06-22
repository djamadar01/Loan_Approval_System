"""
Client library for API v2 endpoints.

Provides convenient Python interface to all advanced API endpoints:
1. Analytics - GET /api/v2/decisions/analytics
2. Batch Processing - POST /api/v2/applications/batch
3. Explainability - GET /api/v2/applications/{id}/explainability
4. What-If Analysis - POST /api/v2/applications/{id}/what-if
5. WebSocket Live Updates - WS /ws/live-updates
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import httpx
import websockets
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ApplicationData:
    """Loan application data."""
    applicant_id: str
    profile: Dict[str, Any]
    credit_score: int
    loan_amount: float
    tenure: int
    liabilities: float
    location: str


@dataclass
class BatchSubmissionResult:
    """Result of batch submission."""
    batch_id: str
    total_applications: int
    status: str
    created_at: str
    estimated_completion: str


@dataclass
class Scenario:
    """What-if scenario."""
    scenario_name: str
    changes: Dict[str, Any]
    description: Optional[str] = None


# ============================================================================
# API CLIENT
# ============================================================================

class LoanApplicationAPIv2Client:
    """
    Client for Loan Application API v2.

    Provides convenient methods for all endpoints with automatic error handling,
    retry logic, and async support.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session: Optional[httpx.AsyncClient] = None
        logger.info(f"Initialized API client for {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    @asynccontextmanager
    async def _get_session(self):
        """Get or create HTTP session."""
        if self.session is None:
            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
            try:
                yield self.session
            finally:
                await self.session.aclose()
                self.session = None
        else:
            yield self.session

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        async with self._get_session() as session:
            for attempt in range(self.max_retries):
                try:
                    url = f"{endpoint}"
                    headers = self._get_headers()

                    response = await session.request(
                        method,
                        url,
                        headers=headers,
                        **kwargs
                    )

                    response.raise_for_status()
                    return response.json()

                except httpx.HTTPError as e:
                    if attempt == self.max_retries - 1:
                        logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Request attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2 ** attempt)

    # ========================================================================
    # ANALYTICS ENDPOINT
    # ========================================================================

    async def get_analytics(
        self,
        period: str = "last_7_days",
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated decision analytics.

        Args:
            period: Time period (last_24_hours, last_7_days, last_30_days, all_time)
            group_by: Optional grouping dimension

        Returns:
            Analytics data dictionary

        Example:
            >>> client = LoanApplicationAPIv2Client()
            >>> async with client:
            ...     analytics = await client.get_analytics("last_7_days")
            ...     print(f"Approval rate: {analytics['metrics']['approval_rate']}")
        """
        logger.info(f"Fetching analytics for period: {period}")

        params = {"period": period}
        if group_by:
            params["group_by"] = group_by

        return await self._request("GET", "/api/v2/decisions/analytics", params=params)

    # ========================================================================
    # BATCH PROCESSING ENDPOINT
    # ========================================================================

    async def submit_batch(
        self,
        applications: List[Dict[str, Any]],
        priority: str = "normal",
        notify_on_completion: bool = True
    ) -> BatchSubmissionResult:
        """
        Submit batch of loan applications.

        Args:
            applications: List of application dictionaries
            priority: Processing priority (normal, high, low)
            notify_on_completion: Send notification when batch completes

        Returns:
            BatchSubmissionResult with batch ID and tracking info

        Example:
            >>> applications = [
            ...     {
            ...         "applicant_id": "APP-001",
            ...         "profile": {...},
            ...         "credit_score": 720,
            ...         ...
            ...     }
            ... ]
            >>> result = await client.submit_batch(applications, priority="high")
            >>> print(f"Batch ID: {result.batch_id}")
        """
        logger.info(f"Submitting batch with {len(applications)} applications")

        payload = {
            "applications": applications,
            "priority": priority,
            "notify_on_completion": notify_on_completion
        }

        response = await self._request(
            "POST",
            "/api/v2/applications/batch",
            json=payload
        )

        return BatchSubmissionResult(
            batch_id=response["batch_id"],
            total_applications=response["total_applications"],
            status=response["status"],
            created_at=response["created_at"],
            estimated_completion=response["estimated_completion"]
        )

    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get status of batch processing job.

        Args:
            batch_id: Batch ID from submission

        Returns:
            Batch status dictionary

        Example:
            >>> status = await client.get_batch_status("BATCH-20240619-ABCD1234")
            >>> print(f"Status: {status['status']}, Processed: {status['processed']}")
        """
        logger.info(f"Fetching batch status: {batch_id}")

        return await self._request(
            "GET",
            f"/api/v2/batches/{batch_id}/status"
        )

    # ========================================================================
    # EXPLAINABILITY ENDPOINT
    # ========================================================================

    async def get_explainability(
        self,
        application_id: str,
        include_alternatives: bool = True,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Get detailed decision explainability.

        Args:
            application_id: Application ID to explain
            include_alternatives: Include alternative decision paths
            confidence_level: Confidence level for uncertainty intervals

        Returns:
            Detailed explainability data

        Example:
            >>> explanation = await client.get_explainability("APP-001")
            >>> print(f"Decision: {explanation['classification']}")
            >>> for factor in explanation['key_factors']:
            ...     print(f"  - {factor['factor_name']}: {factor['explanation']}")
        """
        logger.info(f"Fetching explainability for application: {application_id}")

        params = {
            "include_alternatives": include_alternatives,
            "confidence_level": confidence_level
        }

        return await self._request(
            "GET",
            f"/api/v2/applications/{application_id}/explainability",
            params=params
        )

    # ========================================================================
    # WHAT-IF ANALYSIS ENDPOINT
    # ========================================================================

    async def what_if_analysis(
        self,
        application_id: str,
        scenarios: List[Scenario]
    ) -> Dict[str, Any]:
        """
        Perform what-if scenario analysis.

        Args:
            application_id: Base application ID
            scenarios: List of Scenario objects to analyze

        Returns:
            Analysis results with comparisons and insights

        Example:
            >>> scenarios = [
            ...     Scenario(
            ...         scenario_name="Higher Income",
            ...         changes={"annual_income": 100000},
            ...         description="If income was $100k"
            ...     ),
            ...     Scenario(
            ...         scenario_name="Lower Credit Score",
            ...         changes={"credit_score": 650}
            ...     )
            ... ]
            >>> results = await client.what_if_analysis("APP-001", scenarios)
            >>> for scenario in results["scenarios"]:
            ...     print(f"{scenario['scenario_name']}: {scenario['predicted_classification']}")
        """
        logger.info(f"Running what-if analysis for {application_id} with {len(scenarios)} scenarios")

        payload = {
            "scenarios": [
                {
                    "scenario_name": s.scenario_name,
                    "changes": s.changes,
                    "description": s.description
                }
                for s in scenarios
            ],
            "base_application_id": application_id
        }

        return await self._request(
            "POST",
            f"/api/v2/applications/{application_id}/what-if",
            json=payload
        )

    # ========================================================================
    # WEBSOCKET ENDPOINT
    # ========================================================================

    async def websocket_live_updates(
        self,
        callback: Callable[[Dict[str, Any]], None],
        topics: Optional[List[str]] = None
    ):
        """
        Connect to WebSocket for real-time updates.

        Args:
            callback: Async callback function for messages
            topics: Optional list of topics to subscribe to

        Example:
            >>> async def handle_message(msg):
            ...     print(f"Received: {msg['type']}")
            >>>
            >>> await client.websocket_live_updates(
            ...     handle_message,
            ...     topics=["batch_processing", "applications"]
            ... )
        """
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/live-updates"

        logger.info(f"Connecting to WebSocket: {ws_url}")

        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("WebSocket connected")

                # Subscribe to topics if provided
                if topics:
                    for topic in topics:
                        await websocket.send(json.dumps({
                            "action": "subscribe",
                            "topic": topic
                        }))
                        logger.info(f"Subscribed to topic: {topic}")

                # Receive messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        logger.debug(f"Received message: {data.get('type')}")
                        await callback(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {message}")

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            raise

    # ========================================================================
    # HEALTH & INFO ENDPOINTS
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.

        Returns:
            Health status dictionary
        """
        logger.info("Checking API health")
        return await self._request("GET", "/api/v2/health")

    async def get_info(self) -> Dict[str, Any]:
        """
        Get API information.

        Returns:
            API information dictionary
        """
        logger.info("Fetching API information")
        return await self._request("GET", "/api/v2/info")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def create_sample_applications(count: int = 5) -> List[Dict[str, Any]]:
    """Create sample applications for batch testing."""
    applications = []

    for i in range(count):
        applications.append({
            "applicant_id": f"DEMO-APP-{i+1:03d}",
            "profile": {
                "name": f"Applicant {i+1}",
                "age": 25 + (i * 5),
                "employment_status": "full_time",
                "employment_years": 2 + i,
                "education_level": "bachelor",
                "annual_income": 60000 + (i * 10000),
                "monthly_expenses": 2000 + (i * 200),
                "savings": 10000 + (i * 5000),
                "existing_loans": 1
            },
            "credit_score": 650 + (i * 15),
            "loan_amount": 20000 + (i * 5000),
            "tenure": 60,
            "liabilities": 8000 + (i * 1000),
            "location": "New York, NY"
        })

    return applications


# ============================================================================
# MAIN - EXAMPLE USAGE
# ============================================================================

async def main():
    """Example usage of API v2 client."""
    logging.basicConfig(level=logging.INFO)

    # Initialize client
    client = LoanApplicationAPIv2Client(base_url="http://localhost:8001")

    async with client:
        # 1. Health check
        print("\n" + "="*60)
        print("1. HEALTH CHECK")
        print("="*60)
        health = await client.health_check()
        print(f"Status: {health['status']}")
        print(f"Version: {health['version']}")
        print(f"WebSocket Enabled: {health['websocket_enabled']}")

        # 2. Get Analytics
        print("\n" + "="*60)
        print("2. GET ANALYTICS")
        print("="*60)
        analytics = await client.get_analytics(period="last_7_days")
        metrics = analytics["metrics"]
        print(f"Total Applications: {metrics['total_applications']}")
        print(f"Approval Rate: {metrics['approval_rate']:.1%}")
        print(f"Average Risk Score: {metrics['average_risk_score']:.1f}")
        print(f"Average Processing Time: {metrics['average_processing_time_ms']:.1f}ms")

        # 3. Submit Batch
        print("\n" + "="*60)
        print("3. SUBMIT BATCH")
        print("="*60)
        applications = await create_sample_applications(3)
        batch_result = await client.submit_batch(
            applications,
            priority="normal",
            notify_on_completion=True
        )
        print(f"Batch ID: {batch_result.batch_id}")
        print(f"Total Applications: {batch_result.total_applications}")
        print(f"Status: {batch_result.status}")
        print(f"Estimated Completion: {batch_result.estimated_completion}")

        # 4. Check Batch Status
        print("\n" + "="*60)
        print("4. BATCH STATUS")
        print("="*60)
        await asyncio.sleep(1)  # Wait a bit for processing
        status = await client.get_batch_status(batch_result.batch_id)
        print(f"Status: {status['status']}")
        print(f"Processed: {status.get('processed', 0)}/{status['total_applications']}")

        # 5. Get Explainability
        print("\n" + "="*60)
        print("5. EXPLAINABILITY")
        print("="*60)
        explanation = await client.get_explainability("APP-DEMO-001")
        print(f"Decision: {explanation['classification']}")
        print(f"Risk Score: {explanation['risk_score']:.1f}")
        print("Key Factors:")
        for factor in explanation["key_factors"][:3]:
            print(f"  - {factor['factor_name']}: {factor['explanation']}")

        # 6. What-If Analysis
        print("\n" + "="*60)
        print("6. WHAT-IF ANALYSIS")
        print("="*60)
        scenarios = [
            Scenario(
                scenario_name="Higher Income",
                changes={"annual_income": 100000},
                description="If annual income was $100,000"
            ),
            Scenario(
                scenario_name="Lower Credit Score",
                changes={"credit_score": 650},
                description="If credit score was 650"
            ),
            Scenario(
                scenario_name="Lower Debt",
                changes={"liabilities": 5000},
                description="If liabilities were $5,000"
            )
        ]

        what_if_results = await client.what_if_analysis("APP-DEMO-001", scenarios)
        print("Original Decision:")
        print(f"  Classification: {what_if_results['original_decision']['classification']}")
        print(f"  Risk Score: {what_if_results['original_decision']['risk_score']:.1f}")

        print("\nScenario Results:")
        for scenario in what_if_results["scenarios"]:
            print(f"\n  {scenario['scenario_name']}:")
            print(f"    Predicted Classification: {scenario['predicted_classification']}")
            print(f"    Predicted Risk Score: {scenario['predicted_risk_score']:.1f}")
            print(f"    Decision Impact: {scenario['decision_impact']}")

        print("\nInsights:")
        for insight in what_if_results["insights"][:3]:
            print(f"  - {insight}")

        # 7. API Info
        print("\n" + "="*60)
        print("7. API INFO")
        print("="*60)
        info = await client.get_info()
        print(f"API Name: {info['name']}")
        print(f"Version: {info['version']}")
        print(f"Features:")
        for feature in info["features"]:
            print(f"  - {feature}")


if __name__ == "__main__":
    asyncio.run(main())
