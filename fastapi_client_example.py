"""
FastAPI Loan Decision System - Client Example

Demonstrates how to interact with all API endpoints:
- Health check
- Submit loan application
- Get application status
- Query decisions with filtering and pagination
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class LoanDecisionAPIClient:
    """Client for Loan Decision System API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client with base URL."""
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "LoanDecisionClient/1.0"
        })

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Health check failed: {e}")
            return None

    def submit_application(self, application_data: Dict[str, Any]) -> Optional[str]:
        """
        Submit a loan application.

        Args:
            application_data: Complete application request data

        Returns:
            Application ID if successful, None otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/applications",
                json=application_data
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Application submitted: {result['application_id']}")
            return result['application_id']
        except requests.exceptions.RequestException as e:
            print(f"✗ Application submission failed: {e}")
            if hasattr(e.response, 'json'):
                try:
                    error = e.response.json()
                    print(f"  Error details: {error.get('detail', error)}")
                except:
                    pass
            return None

    def get_application_status(self, app_id: str) -> Dict[str, Any]:
        """
        Get status of a submitted application.

        Args:
            app_id: Application ID

        Returns:
            Application status data
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/applications/{app_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get application status: {e}")
            return None

    def get_decisions(
        self,
        page: int = 1,
        page_size: int = 10,
        decision_filter: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        sort_by: str = "decision_date",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get decisions with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Results per page
            decision_filter: Filter by decision type (approved, rejected, conditional, manual_review, all)
            min_risk_score: Minimum risk score (0-100)
            max_risk_score: Maximum risk score (0-100)
            sort_by: Sort field (decision_date, risk_score, loan_amount)
            sort_order: Sort order (asc, desc)

        Returns:
            Paginated decisions data
        """
        try:
            params = {
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "sort_order": sort_order
            }

            if decision_filter:
                params["decision_filter"] = decision_filter
            if min_risk_score is not None:
                params["min_risk_score"] = min_risk_score
            if max_risk_score is not None:
                params["max_risk_score"] = max_risk_score

            response = self.session.get(
                f"{self.base_url}/api/v1/decisions",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to get decisions: {e}")
            return None


def create_sample_application() -> Dict[str, Any]:
    """Create a sample loan application."""
    return {
        "personal_info": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+14155552671",
            "date_of_birth": "1990-05-15"
        },
        "employment_info": {
            "employer_name": "Tech Innovations Inc.",
            "job_title": "Senior Software Engineer",
            "employment_status": "employed",
            "years_employed": 7.5,
            "monthly_income": 9500
        },
        "financial_info": {
            "annual_income": 114000,
            "monthly_expenses": 3500,
            "credit_score": 780,
            "existing_loans_count": 1,
            "savings_amount": 85000
        },
        "loan_details": {
            "loan_amount": 350000,
            "loan_term_months": 360,
            "loan_purpose": "home",
            "collateral_type": "property",
            "collateral_value": 450000
        },
        "additional_notes": "First-time home buyer, excellent credit history"
    }


def create_application_with_high_dti() -> Dict[str, Any]:
    """Create an application with high debt-to-income ratio (should fail)."""
    return {
        "personal_info": {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "+14155552672",
            "date_of_birth": "1995-08-20"
        },
        "employment_info": {
            "employer_name": "Retail Store XYZ",
            "job_title": "Sales Associate",
            "employment_status": "employed",
            "years_employed": 2.0,
            "monthly_income": 3000
        },
        "financial_info": {
            "annual_income": 36000,
            "monthly_expenses": 2500,
            "credit_score": 650,
            "existing_loans_count": 3,
            "savings_amount": 5000
        },
        "loan_details": {
            "loan_amount": 50000,
            "loan_term_months": 60,
            "loan_purpose": "auto",
            "collateral_type": "vehicle",
            "collateral_value": 55000
        },
        "additional_notes": "Need vehicle for work commute"
    }


def create_invalid_application() -> Dict[str, Any]:
    """Create an invalid application (missing required fields)."""
    return {
        "personal_info": {
            "first_name": "Bob",
            "last_name": "Johnson",
            "email": "invalid-email",  # Invalid email format
            "phone": "123",  # Invalid phone format
            "date_of_birth": "15-05-1990"  # Invalid date format
        },
        "employment_info": {
            "employer_name": "Company ABC",
            "job_title": "Manager",
            "employment_status": "employed",
            "years_employed": 5,
            "monthly_income": 7000
        },
        "financial_info": {
            "annual_income": 84000,
            "monthly_expenses": 2000,
            "credit_score": 900,  # Invalid: > 850
            "existing_loans_count": 1,
            "savings_amount": 25000
        },
        "loan_details": {
            "loan_amount": 300000,
            "loan_term_months": 360,
            "loan_purpose": "home",
            "collateral_type": "property",
            "collateral_value": 350000
        }
    }


def demo_health_check(client: LoanDecisionAPIClient):
    """Demo: Health check endpoint."""
    print("\n" + "=" * 70)
    print("DEMO 1: Health Check")
    print("=" * 70)

    health = client.health_check()
    if health:
        print(f"✓ API Status: {health['status']}")
        print(f"  Version: {health['version']}")
        print(f"  Orchestrator Ready: {health['orchestrator_ready']}")
        print(f"  Database Connected: {health['database_connected']}")
        print(f"  Timestamp: {health['timestamp']}")
    else:
        print("✗ Health check failed")


def demo_submit_application(client: LoanDecisionAPIClient):
    """Demo: Submit loan application."""
    print("\n" + "=" * 70)
    print("DEMO 2: Submit Loan Application")
    print("=" * 70)

    # Valid application
    print("\n[A] Submitting valid application...")
    app_data = create_sample_application()
    print(json.dumps(app_data, indent=2))
    app_id = client.submit_application(app_data)

    if app_id:
        # Check status immediately
        print(f"\n[B] Checking status of {app_id}...")
        time.sleep(0.5)
        status = client.get_application_status(app_id)
        if status:
            print(f"✓ Application Status:")
            print(f"  ID: {status['application_id']}")
            print(f"  Status: {status['status']}")
            print(f"  Applicant: {status['applicant_name']}")
            print(f"  Loan Amount: ${status['loan_amount']:,.2f}")
            print(f"  Current Stage: {status['current_stage']}")


def demo_validation_errors(client: LoanDecisionAPIClient):
    """Demo: Validation errors."""
    print("\n" + "=" * 70)
    print("DEMO 3: Validation Errors")
    print("=" * 70)

    # High DTI application
    print("\n[A] Testing debt-to-income ratio validation...")
    app_data = create_application_with_high_dti()
    result = client.submit_application(app_data)
    if not result:
        print("  ✓ High DTI correctly rejected")

    # Invalid application
    print("\n[B] Testing input validation...")
    invalid_app = create_invalid_application()
    result = client.submit_application(invalid_app)
    if not result:
        print("  ✓ Invalid inputs correctly rejected")


def demo_decisions_filtering(client: LoanDecisionAPIClient):
    """Demo: Get decisions with filtering and pagination."""
    print("\n" + "=" * 70)
    print("DEMO 4: Get Decisions with Filtering and Pagination")
    print("=" * 70)

    # Get first page of all decisions
    print("\n[A] Getting all decisions (page 1, 10 per page)...")
    result = client.get_decisions(page=1, page_size=10)
    if result:
        print(f"✓ Total decisions: {result['total_count']}")
        print(f"  Page: {result['page']} of ~{(result['total_count'] + 9) // 10}")
        print(f"  Results on page: {len(result['decisions'])}")
        print(f"  Has more: {result['has_more']}")

    # Get approved decisions
    print("\n[B] Getting approved decisions...")
    result = client.get_decisions(
        page=1,
        page_size=10,
        decision_filter="approved"
    )
    if result:
        print(f"✓ Approved decisions: {result['total_count']}")
        if result['decisions']:
            for i, decision in enumerate(result['decisions'][:3], 1):
                print(f"  {i}. {decision['applicant_name']} - Risk Score: {decision['risk_score']:.1f}%")

    # Get high-risk decisions
    print("\n[C] Getting high-risk decisions (risk score > 70)...")
    result = client.get_decisions(
        page=1,
        page_size=10,
        min_risk_score=70,
        sort_by="risk_score",
        sort_order="desc"
    )
    if result:
        print(f"✓ High-risk decisions: {result['total_count']}")
        if result['decisions']:
            for i, decision in enumerate(result['decisions'][:3], 1):
                print(f"  {i}. {decision['applicant_name']} - Risk Score: {decision['risk_score']:.1f}%")

    # Get by risk score range
    print("\n[D] Getting medium-risk decisions (risk score 40-60)...")
    result = client.get_decisions(
        page=1,
        page_size=10,
        min_risk_score=40,
        max_risk_score=60,
        sort_by="loan_amount",
        sort_order="asc"
    )
    if result:
        print(f"✓ Medium-risk decisions: {result['total_count']}")
        if result['decisions']:
            for i, decision in enumerate(result['decisions'][:3], 1):
                print(f"  {i}. {decision['applicant_name']} - Loan: ${decision['loan_amount']:,.0f}")

    # Get rejected decisions
    print("\n[E] Getting rejected decisions...")
    result = client.get_decisions(
        page=1,
        page_size=5,
        decision_filter="rejected"
    )
    if result:
        print(f"✓ Rejected decisions: {result['total_count']}")

    # Pagination example
    print("\n[F] Pagination example (page 2)...")
    result = client.get_decisions(page=2, page_size=10)
    if result:
        print(f"✓ Showing page {result['page']} with {len(result['decisions'])} results")
        print(f"  Has more pages: {result['has_more']}")


def demo_error_handling(client: LoanDecisionAPIClient):
    """Demo: Error handling."""
    print("\n" + "=" * 70)
    print("DEMO 5: Error Handling")
    print("=" * 70)

    # Non-existent application
    print("\n[A] Requesting non-existent application...")
    status = client.get_application_status("APP-99999999-999999")
    if not status:
        print("  ✓ 404 error correctly handled")

    # Invalid parameters
    print("\n[B] Testing invalid query parameters...")
    result = client.session.get(
        f"{client.base_url}/api/v1/decisions",
        params={"page_size": 1000}  # Exceeds max
    )
    if result.status_code == 422:
        print("  ✓ Invalid parameters correctly rejected")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("Loan Decision System API - Client Examples")
    print("=" * 70)

    # Initialize client
    client = LoanDecisionAPIClient(base_url="http://localhost:8000")

    # Check connectivity
    print("\nChecking API connectivity...")
    health = client.health_check()
    if not health:
        print("✗ API is not running. Start it with: python main.py")
        return

    print(f"✓ Connected to API at {client.base_url}")

    # Run demos
    try:
        demo_health_check(client)
        demo_submit_application(client)
        demo_validation_errors(client)
        demo_decisions_filtering(client)
        demo_error_handling(client)

        print("\n" + "=" * 70)
        print("All demonstrations completed!")
        print("=" * 70)
        print("\nAccess the API documentation at:")
        print(f"  Swagger UI: {client.base_url}/docs")
        print(f"  ReDoc: {client.base_url}/redoc")

    except KeyboardInterrupt:
        print("\n\nDemonstration interrupted by user")
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
