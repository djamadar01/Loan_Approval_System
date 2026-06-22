#!/usr/bin/env python3
"""
ApplicantDB MCP Client Example
Demonstrates how to use the ApplicantDB server for applicant management.
"""

import sys
from pathlib import Path
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from applicantdb_mcp_server import (
    ApplicantDB,
    EmployerDB,
    DatabaseError,
    ValidationError,
)


class ApplicantDBClient:
    """High-level client for ApplicantDB operations."""

    def __init__(self, db_path=None, employer_db_path=None):
        """Initialize client with optional custom database paths."""
        if db_path is None:
            db_path = Path.home() / ".mcp_applicantdb" / "applicantdb.sqlite"
        if employer_db_path is None:
            employer_db_path = Path.home() / ".mcp_applicantdb" / "employers.sqlite"

        self.applicant_db = ApplicantDB(Path(db_path))
        self.employer_db = EmployerDB(Path(employer_db_path))

    def register_applicant(
        self,
        applicant_id: str,
        first_name: str,
        last_name: str,
        email: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Register a new applicant in the system."""
        try:
            applicant_data = {
                'id': applicant_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                **kwargs
            }
            applicant_id = self.applicant_db.create_applicant(applicant_data)
            return {
                'success': True,
                'applicant_id': applicant_id,
                'message': f'Applicant {applicant_id} registered successfully'
            }
        except (ValidationError, DatabaseError) as e:
            return {
                'success': False,
                'error': str(e)
            }

    def update_credit_profile(
        self,
        applicant_id: str,
        credit_score: int,
        total_debt: float = None,
        available_credit: float = None,
        payment_history: list = None
    ) -> Dict[str, Any]:
        """Update applicant's credit profile."""
        try:
            credit_data = {
                'credit_score': credit_score,
                'total_debt': total_debt,
                'available_credit': available_credit,
                'payment_history': payment_history or []
            }
            record_id = self.applicant_db.add_credit_update(applicant_id, credit_data)
            return {
                'success': True,
                'record_id': record_id,
                'message': f'Credit profile updated for {applicant_id}'
            }
        except (ValidationError, DatabaseError) as e:
            return {
                'success': False,
                'error': str(e)
            }

    def register_employer(
        self,
        employer_id: str,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Register a new employer in the system."""
        try:
            employer_data = {
                'id': employer_id,
                'name': name,
                **kwargs
            }
            self.employer_db.add_employer(employer_data)
            return {
                'success': True,
                'employer_id': employer_id,
                'message': f'Employer {employer_id} registered successfully'
            }
        except (ValidationError, DatabaseError) as e:
            return {
                'success': False,
                'error': str(e)
            }

    def verify_applicant_employment(
        self,
        applicant_id: str,
        employer_id: str,
        employee_id: str = None,
        job_title: str = None,
        salary: float = None,
        start_date: str = None
    ) -> Dict[str, Any]:
        """Verify applicant's employment with an employer."""
        try:
            employee_data = {
                'employee_id': employee_id,
                'job_title': job_title,
                'salary': salary,
                'start_date': start_date,
                'current_status': 'active'
            }
            result = self.employer_db.verify_employment(applicant_id, employer_id, employee_data)
            return {
                'success': True,
                'verification': result
            }
        except (ValidationError, DatabaseError) as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_complete_profile(self, applicant_id: str) -> Dict[str, Any]:
        """Retrieve complete applicant profile."""
        try:
            applicant = self.applicant_db.get_applicant(applicant_id)
            if not applicant:
                return {
                    'success': False,
                    'error': f'Applicant {applicant_id} not found'
                }

            credit_history = self.applicant_db.get_credit_history(applicant_id)
            employment_records = self.employer_db.get_employment_records(applicant_id)

            return {
                'success': True,
                'profile': {
                    'applicant': dict(applicant),
                    'credit_history': [dict(record) for record in credit_history],
                    'employment_records': employment_records
                }
            }
        except DatabaseError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            conn_app = self.applicant_db.get_connection()
            cursor = conn_app.cursor()

            cursor.execute('SELECT COUNT(*) FROM applicants')
            applicant_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM credit_history')
            credit_records = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM applicants WHERE employment_status = "active"')
            active_count = cursor.fetchone()[0]

            conn_app.close()

            conn_emp = self.employer_db.get_connection()
            cursor = conn_emp.cursor()

            cursor.execute('SELECT COUNT(*) FROM employers')
            employer_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM employee_records')
            employment_records = cursor.fetchone()[0]

            conn_emp.close()

            return {
                'success': True,
                'statistics': {
                    'total_applicants': applicant_count,
                    'active_applicants': active_count,
                    'credit_records': credit_records,
                    'employers_registered': employer_count,
                    'employment_verifications': employment_records
                }
            }
        except DatabaseError as e:
            return {
                'success': False,
                'error': str(e)
            }


def demo_workflow():
    """Demonstrate complete ApplicantDB workflow."""
    print("=" * 70)
    print("ApplicantDB MCP Server - Complete Workflow Demo")
    print("=" * 70)

    client = ApplicantDBClient()

    # 1. Register employers
    print("\n[1] Registering employers...")
    employers = [
        {
            'id': 'EMP_ACME',
            'name': 'ACME Corporation',
            'industry': 'Technology',
            'headquarters_state': 'CA',
            'employee_count': 10000
        },
        {
            'id': 'EMP_GLOBEX',
            'name': 'Globex Corporation',
            'industry': 'Finance',
            'headquarters_state': 'NY',
            'employee_count': 5000
        }
    ]

    for emp in employers:
        result = client.register_employer(
            employer_id=emp['id'],
            name=emp['name'],
            **{k: v for k, v in emp.items() if k not in ['id', 'name']}
        )
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {result.get('message', result.get('error'))}")

    # 2. Register applicants
    print("\n[2] Registering applicants...")
    applicants = [
        {
            'applicant_id': 'APP_001',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice.johnson@example.com',
            'phone': '555-0101',
            'ssn': '123-45-6701',
            'date_of_birth': '1990-05-15',
            'address': '123 Main St',
            'city': 'San Francisco',
            'state': 'CA',
            'zip_code': '94102',
            'annual_income': 95000.00
        },
        {
            'applicant_id': 'APP_002',
            'first_name': 'Bob',
            'last_name': 'Smith',
            'email': 'bob.smith@example.com',
            'phone': '555-0102',
            'ssn': '123-45-6702',
            'date_of_birth': '1988-03-22',
            'address': '456 Oak Ave',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'annual_income': 105000.00
        },
        {
            'applicant_id': 'APP_003',
            'first_name': 'Carol',
            'last_name': 'Davis',
            'email': 'carol.davis@example.com',
            'phone': '555-0103',
            'ssn': '123-45-6703',
            'date_of_birth': '1992-07-08',
            'address': '789 Pine Rd',
            'city': 'Austin',
            'state': 'TX',
            'zip_code': '78701',
            'annual_income': 85000.00,
            'employment_status': 'employed',
            'employer_id': 'EMP_ACME'
        }
    ]

    for app in applicants:
        result = client.register_applicant(**app)
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {result.get('message', result.get('error'))}")

    # 3. Update credit profiles
    print("\n[3] Updating credit profiles...")
    credit_updates = [
        {
            'applicant_id': 'APP_001',
            'credit_score': 785,
            'total_debt': 25000.00,
            'available_credit': 50000.00,
            'payment_history': ['on_time', 'on_time', 'on_time']
        },
        {
            'applicant_id': 'APP_002',
            'credit_score': 720,
            'total_debt': 35000.00,
            'available_credit': 40000.00,
            'payment_history': ['on_time', 'late_30_days', 'on_time']
        },
        {
            'applicant_id': 'APP_003',
            'credit_score': 805,
            'total_debt': 15000.00,
            'available_credit': 75000.00,
            'payment_history': ['on_time', 'on_time', 'on_time']
        }
    ]

    for update in credit_updates:
        result = client.update_credit_profile(**update)
        status = "✓" if result['success'] else "✗"
        print(f"  {status} Credit updated: {update['applicant_id']} (Score: {update['credit_score']})")

    # 4. Verify employment
    print("\n[4] Verifying employment...")
    employment_verifications = [
        {
            'applicant_id': 'APP_001',
            'employer_id': 'EMP_ACME',
            'employee_id': 'EMP-001-98765',
            'job_title': 'Senior Software Engineer',
            'salary': 95000.00,
            'start_date': '2020-01-15'
        },
        {
            'applicant_id': 'APP_002',
            'employer_id': 'EMP_GLOBEX',
            'employee_id': 'EMP-002-98764',
            'job_title': 'Financial Analyst',
            'salary': 105000.00,
            'start_date': '2019-06-01'
        }
    ]

    for verification in employment_verifications:
        result = client.verify_applicant_employment(**verification)
        status = "✓" if result['success'] else "✗"
        if result['success']:
            ver_id = result['verification']['verification_id']
            print(f"  {status} Employment verified: {verification['applicant_id']} (ID: {ver_id})")
        else:
            print(f"  {status} Error: {result['error']}")

    # 5. Retrieve complete profiles
    print("\n[5] Retrieving complete applicant profiles...")
    for app_id in ['APP_001', 'APP_002', 'APP_003']:
        result = client.get_complete_profile(app_id)
        if result['success']:
            profile = result['profile']
            app = profile['applicant']
            print(f"\n  Applicant: {app['first_name']} {app['last_name']}")
            print(f"    Email: {app['email']}")
            print(f"    Income: ${app['annual_income']:,.2f}")
            print(f"    Credit Records: {len(profile['credit_history'])}")
            if profile['credit_history']:
                latest_credit = profile['credit_history'][0]
                print(f"    Latest Credit Score: {latest_credit['credit_score']}")
            print(f"    Employment Verifications: {len(profile['employment_records'])}")
        else:
            print(f"  Error retrieving {app_id}: {result['error']}")

    # 6. Database statistics
    print("\n[6] Database Statistics...")
    stats_result = client.get_database_stats()
    if stats_result['success']:
        stats = stats_result['statistics']
        print(f"  Total Applicants: {stats['total_applicants']}")
        print(f"  Active Applicants: {stats['active_applicants']}")
        print(f"  Credit Records: {stats['credit_records']}")
        print(f"  Employers Registered: {stats['employers_registered']}")
        print(f"  Employment Verifications: {stats['employment_verifications']}")
    else:
        print(f"  Error: {stats_result['error']}")

    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    try:
        demo_workflow()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
