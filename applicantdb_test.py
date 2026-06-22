#!/usr/bin/env python3
"""
Test suite for ApplicantDB MCP Server
Tests all core functionality including database operations, validation, and caching.
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from applicantdb_mcp_server import (
    ApplicantDB,
    EmployerDB,
    DatabaseError,
    ValidationError,
)


class TestApplicantDB(unittest.TestCase):
    """Test cases for ApplicantDB class."""

    def setUp(self):
        """Set up test database."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_applicants.sqlite"
        self.db = ApplicantDB(self.db_path)

    def tearDown(self):
        """Clean up test database."""
        shutil.rmtree(self.test_dir)

    def test_database_initialization(self):
        """Test that database initializes correctly."""
        self.assertTrue(self.db_path.exists())

        # Check that tables exist
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

        table_names = {row[0] for row in tables}
        self.assertIn('applicants', table_names)
        self.assertIn('credit_history', table_names)

    def test_create_applicant_success(self):
        """Test successful applicant creation."""
        applicant_data = {
            'id': 'APP001',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '555-1234',
            'ssn': '123-45-6789',
            'annual_income': 75000.00
        }

        applicant_id = self.db.create_applicant(applicant_data)
        self.assertEqual(applicant_id, 'APP001')

        # Verify record was created
        applicant = self.db.get_applicant('APP001')
        self.assertIsNotNone(applicant)
        self.assertEqual(applicant['first_name'], 'John')
        self.assertEqual(applicant['email'], 'john@example.com')

    def test_create_applicant_missing_required_fields(self):
        """Test applicant creation with missing required fields."""
        # Missing last_name
        incomplete_data = {
            'id': 'APP002',
            'first_name': 'Jane',
            'email': 'jane@example.com'
        }

        with self.assertRaises(ValidationError) as context:
            self.db.create_applicant(incomplete_data)
        self.assertIn('last_name', str(context.exception))

    def test_create_applicant_invalid_email(self):
        """Test applicant creation with invalid email."""
        applicant_data = {
            'id': 'APP003',
            'first_name': 'Bob',
            'last_name': 'Smith',
            'email': 'invalid-email',
        }

        with self.assertRaises(ValidationError) as context:
            self.db.create_applicant(applicant_data)
        self.assertIn('email', str(context.exception))

    def test_create_applicant_duplicate_id(self):
        """Test applicant creation with duplicate ID."""
        applicant_data = {
            'id': 'APP004',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice@example.com',
        }

        self.db.create_applicant(applicant_data)

        # Try to create with same ID
        with self.assertRaises(DatabaseError):
            self.db.create_applicant(applicant_data)

    def test_get_applicant_not_found(self):
        """Test retrieving non-existent applicant."""
        result = self.db.get_applicant('NONEXISTENT')
        self.assertIsNone(result)

    def test_add_credit_update_success(self):
        """Test successful credit update."""
        # Create applicant first
        applicant_data = {
            'id': 'APP005',
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'email': 'charlie@example.com',
        }
        self.db.create_applicant(applicant_data)

        # Add credit update
        credit_data = {
            'credit_score': 750,
            'total_debt': 15000.00,
            'available_credit': 25000.00,
            'payment_history': ['on_time', 'on_time', 'late_30_days']
        }

        record_id = self.db.add_credit_update('APP005', credit_data, 'test_user')
        self.assertIsNotNone(record_id)

        # Verify record was created
        history = self.db.get_credit_history('APP005')
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['credit_score'], 750)

    def test_add_credit_update_invalid_score(self):
        """Test credit update with invalid credit score."""
        # Create applicant first
        applicant_data = {
            'id': 'APP006',
            'first_name': 'Diana',
            'last_name': 'Prince',
            'email': 'diana@example.com',
        }
        self.db.create_applicant(applicant_data)

        # Try to add invalid credit score
        credit_data = {'credit_score': 900}  # Invalid: > 850

        with self.assertRaises(ValidationError) as context:
            self.db.add_credit_update('APP006', credit_data)
        self.assertIn('credit score', str(context.exception))

    def test_add_credit_update_applicant_not_found(self):
        """Test credit update for non-existent applicant."""
        credit_data = {'credit_score': 750}

        with self.assertRaises(ValidationError):
            self.db.add_credit_update('NONEXISTENT', credit_data)

    def test_credit_history_ordering(self):
        """Test that credit history is ordered by most recent first."""
        # Create applicant
        applicant_data = {
            'id': 'APP007',
            'first_name': 'Eve',
            'last_name': 'Adam',
            'email': 'eve@example.com',
        }
        self.db.create_applicant(applicant_data)

        # Add multiple credit updates
        for i in range(3):
            credit_data = {'credit_score': 700 + i * 10}
            self.db.add_credit_update('APP007', credit_data)

        # Get history
        history = self.db.get_credit_history('APP007')
        self.assertEqual(len(history), 3)

        # Verify ordering (newest first)
        self.assertGreaterEqual(history[0]['last_updated'], history[1]['last_updated'])
        self.assertGreaterEqual(history[1]['last_updated'], history[2]['last_updated'])


class TestEmployerDB(unittest.TestCase):
    """Test cases for EmployerDB class."""

    def setUp(self):
        """Set up test database."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_employers.sqlite"
        self.db = EmployerDB(self.db_path)

        # Also need applicant DB for employment verification
        self.applicant_db_path = Path(self.test_dir) / "test_applicants.sqlite"
        self.applicant_db = ApplicantDB(self.applicant_db_path)

    def tearDown(self):
        """Clean up test database."""
        shutil.rmtree(self.test_dir)

    def test_database_initialization(self):
        """Test that employer database initializes correctly."""
        self.assertTrue(self.db_path.exists())

        # Check that tables exist
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

        table_names = {row[0] for row in tables}
        self.assertIn('employers', table_names)
        self.assertIn('employee_records', table_names)

    def test_add_employer_success(self):
        """Test successful employer addition."""
        employer_data = {
            'id': 'EMP001',
            'name': 'Tech Corp Inc',
            'industry': 'Technology',
            'headquarters_state': 'CA',
            'employee_count': 5000
        }

        employer_id = self.db.add_employer(employer_data)
        self.assertEqual(employer_id, 'EMP001')

    def test_add_employer_missing_required_fields(self):
        """Test employer addition with missing required fields."""
        employer_data = {
            'name': 'Tech Corp Inc'  # Missing 'id'
        }

        with self.assertRaises(ValidationError):
            self.db.add_employer(employer_data)

    def test_verify_employment_success(self):
        """Test successful employment verification."""
        # Add employer
        employer_data = {
            'id': 'EMP002',
            'name': 'Finance Solutions',
            'industry': 'Finance'
        }
        self.db.add_employer(employer_data)

        # Create applicant
        applicant_data = {
            'id': 'APP008',
            'first_name': 'Frank',
            'last_name': 'Green',
            'email': 'frank@example.com',
        }
        self.applicant_db.create_applicant(applicant_data)

        # Verify employment
        employee_data = {
            'employee_id': 'EMP123456',
            'job_title': 'Senior Analyst',
            'salary': 95000.00,
            'start_date': '2020-01-15',
            'current_status': 'active'
        }

        result = self.db.verify_employment('APP008', 'EMP002', employee_data)

        self.assertTrue(result['status'] == 'verified')
        self.assertEqual(result['employer_name'], 'Finance Solutions')
        self.assertIn('verification_id', result)

    def test_verify_employment_employer_not_found(self):
        """Test employment verification with non-existent employer."""
        employee_data = {'employee_id': 'EMP999'}

        with self.assertRaises(ValidationError):
            self.db.verify_employment('APP009', 'NONEXISTENT', employee_data)

    def test_get_employment_records(self):
        """Test retrieving employment records for an applicant."""
        # Add employer
        employer_data = {
            'id': 'EMP003',
            'name': 'Global Industries',
            'industry': 'Manufacturing'
        }
        self.db.add_employer(employer_data)

        # Create applicant
        applicant_data = {
            'id': 'APP010',
            'first_name': 'Grace',
            'last_name': 'Hall',
            'email': 'grace@example.com',
        }
        self.applicant_db.create_applicant(applicant_data)

        # Verify employment
        employee_data = {
            'employee_id': 'EMP654321',
            'job_title': 'Manager',
            'salary': 85000.00
        }
        self.db.verify_employment('APP010', 'EMP003', employee_data)

        # Get records
        records = self.db.get_employment_records('APP010')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['employer_name'], 'Global Industries')
        self.assertEqual(records[0]['job_title'], 'Manager')

    def test_employment_records_empty(self):
        """Test getting employment records for applicant with no records."""
        records = self.db.get_employment_records('NONEXISTENT')
        self.assertEqual(len(records), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test databases."""
        self.test_dir = tempfile.mkdtemp()
        self.applicant_db = ApplicantDB(Path(self.test_dir) / "test_applicants.sqlite")
        self.employer_db = EmployerDB(Path(self.test_dir) / "test_employers.sqlite")

    def tearDown(self):
        """Clean up test databases."""
        shutil.rmtree(self.test_dir)

    def test_complete_applicant_workflow(self):
        """Test complete applicant workflow: create, add credit, verify employment."""
        # Create applicant
        applicant_data = {
            'id': 'APP_WORKFLOW_001',
            'first_name': 'Henry',
            'last_name': 'Iron',
            'email': 'henry@example.com',
            'phone': '555-9999',
            'annual_income': 120000.00
        }
        self.applicant_db.create_applicant(applicant_data)

        # Add credit information
        credit_data = {
            'credit_score': 780,
            'total_debt': 20000.00,
            'available_credit': 30000.00
        }
        credit_id = self.applicant_db.add_credit_update('APP_WORKFLOW_001', credit_data)
        self.assertIsNotNone(credit_id)

        # Add employer and verify employment
        employer_data = {
            'id': 'EMP_WORKFLOW_001',
            'name': 'Enterprise Systems',
            'industry': 'Technology',
            'headquarters_state': 'NY'
        }
        self.employer_db.add_employer(employer_data)

        employee_data = {
            'employee_id': 'ENT-123456',
            'job_title': 'Senior Developer',
            'salary': 120000.00,
            'start_date': '2018-06-01'
        }
        verification = self.employer_db.verify_employment(
            'APP_WORKFLOW_001',
            'EMP_WORKFLOW_001',
            employee_data
        )
        self.assertTrue(verification['status'] == 'verified')

        # Verify all data is retrievable
        applicant = self.applicant_db.get_applicant('APP_WORKFLOW_001')
        self.assertEqual(applicant['first_name'], 'Henry')

        credit_history = self.applicant_db.get_credit_history('APP_WORKFLOW_001')
        self.assertEqual(len(credit_history), 1)
        self.assertEqual(credit_history[0]['credit_score'], 780)

        employment_records = self.employer_db.get_employment_records('APP_WORKFLOW_001')
        self.assertEqual(len(employment_records), 1)
        self.assertEqual(employment_records[0]['job_title'], 'Senior Developer')

    def test_multiple_applicants_isolation(self):
        """Test that multiple applicants' data remains isolated."""
        # Create two applicants
        for i in range(2):
            applicant_data = {
                'id': f'APP_ISO_{i}',
                'first_name': f'Applicant{i}',
                'last_name': 'Test',
                'email': f'applicant{i}@example.com',
            }
            self.applicant_db.create_applicant(applicant_data)

            # Add different credit scores
            credit_data = {'credit_score': 700 + i * 50}
            self.applicant_db.add_credit_update(f'APP_ISO_{i}', credit_data)

        # Verify isolation
        credit_0 = self.applicant_db.get_credit_history('APP_ISO_0')
        credit_1 = self.applicant_db.get_credit_history('APP_ISO_1')

        self.assertEqual(credit_0[0]['credit_score'], 700)
        self.assertEqual(credit_1[0]['credit_score'], 750)


def run_tests():
    """Run all tests with verbose output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestApplicantDB))
    suite.addTests(loader.loadTestsFromTestCase(TestEmployerDB))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
