#!/usr/bin/env python3
"""
Comprehensive test suite for Production RiskRulesDB MCP Server
Tests all major components and features
"""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, '/home/ubuntu/Desktop/demo')

from riskrulesdb_production import (
    RiskRulesDBServer,
    RiskLevel,
    AnomalyType,
    DebtToIncomeResult,
    CreditScoreRiskResult,
    AnomalyDetectionResult
)


class TestRiskRulesDBServer(unittest.TestCase):
    """Test suite for RiskRulesDB Server"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.server = RiskRulesDBServer("riskrulesdb_config.json")

    def test_server_initialization(self):
        """Test server initializes correctly"""
        self.assertIsNotNone(self.server.config)
        self.assertIsNotNone(self.server.mcp)
        self.assertIsNotNone(self.server.logger)

    def test_config_loading(self):
        """Test configuration is loaded correctly"""
        self.assertIn("risk_thresholds", self.server.config)
        self.assertIn("industry_benchmarks", self.server.config)
        self.assertIn("business_rules", self.server.config)

    # ========================================================================
    # DTI Calculation Tests
    # ========================================================================

    def test_dti_calculation_standard_method(self):
        """Test DTI calculation with standard method"""
        result = self.server._calculate_dti(
            total_debt=1500,
            income=5000,
            method="standard"
        )

        self.assertIsInstance(result, DebtToIncomeResult)
        self.assertEqual(result.ratio, 0.3)
        self.assertEqual(result.calculation_method, "standard")
        self.assertEqual(result.risk_level, RiskLevel.LOW.value)
        self.assertTrue(result.meets_lending_standards)

    def test_dti_calculation_inclusive_method(self):
        """Test DTI calculation with inclusive method"""
        result = self.server._calculate_dti(
            total_debt=1500,
            income=5000,
            proposed_new_payment=500,
            method="inclusive"
        )

        self.assertEqual(result.ratio, 0.4)
        self.assertEqual(result.calculation_method, "inclusive")
        self.assertEqual(result.total_monthly_debt, 2000)

    def test_dti_calculation_conservative_method(self):
        """Test DTI calculation with conservative method"""
        result = self.server._calculate_dti(
            total_debt=1500,
            income=5000,
            proposed_new_payment=500,
            method="conservative"
        )

        self.assertGreater(result.ratio, 0.4)
        self.assertEqual(result.calculation_method, "conservative")

    def test_dti_risk_levels(self):
        """Test DTI risk level classification"""
        test_cases = [
            (0.2, RiskLevel.LOW.value),
            (0.4, RiskLevel.MODERATE.value),
            (0.6, RiskLevel.HIGH.value),
            (0.8, RiskLevel.CRITICAL.value)
        ]

        for dti_ratio, expected_level in test_cases:
            result = self.server._calculate_dti(
                total_debt=dti_ratio * 5000,
                income=5000
            )
            self.assertEqual(result.risk_level, expected_level)

    def test_dti_invalid_income(self):
        """Test DTI calculation with invalid income"""
        result = self.server.calculate_debt_to_income(
            total_monthly_debt=1500,
            gross_monthly_income=-5000
        )

        self.assertIn("error", result)

    def test_dti_industry_comparison(self):
        """Test DTI industry comparison calculation"""
        result = self.server._calculate_dti(
            total_debt=1500,
            income=5000
        )

        self.assertIn("industry_comparison", result.industry_comparison)
        self.assertGreater(len(result.industry_comparison), 0)

    # ========================================================================
    # Credit Score Risk Tests
    # ========================================================================

    def test_credit_score_excellent(self):
        """Test excellent credit score assessment"""
        result = self.server._assess_credit_risk(
            credit_score=780,
            industry="personal_loans",
            inquiries=1,
            late_payments=0
        )

        self.assertEqual(result.category, "excellent")
        self.assertEqual(result.risk_level, RiskLevel.LOW.value)
        self.assertGreater(result.percentile, 70)

    def test_credit_score_poor(self):
        """Test poor credit score assessment"""
        result = self.server._assess_credit_risk(
            credit_score=550,
            industry="personal_loans",
            inquiries=8,
            late_payments=3
        )

        self.assertEqual(result.category, "poor")
        self.assertEqual(result.risk_level, RiskLevel.HIGH.value)
        self.assertGreater(len(result.risk_factors), 0)

    def test_credit_score_very_poor(self):
        """Test very poor credit score assessment"""
        result = self.server._assess_credit_risk(
            credit_score=400,
            industry="personal_loans",
            inquiries=0,
            late_payments=0
        )

        self.assertEqual(result.category, "very_poor")
        self.assertEqual(result.risk_level, RiskLevel.CRITICAL.value)

    def test_credit_score_industry_benchmarks(self):
        """Test industry benchmarks in credit assessment"""
        for industry in ["personal_loans", "mortgage", "auto_loan", "credit_card"]:
            result = self.server._assess_credit_risk(
                credit_score=700,
                industry=industry
            )

            self.assertIn("industry_benchmarks", result.industry_benchmarks)
            self.assertIn("average_score", result.industry_benchmarks)

    def test_credit_percentile_calculation(self):
        """Test credit score percentile calculation"""
        percentile_low = self.server._calculate_credit_percentile(600, 650)
        percentile_high = self.server._calculate_credit_percentile(750, 650)

        self.assertLess(percentile_low, percentile_high)
        self.assertGreater(percentile_low, 0)
        self.assertLess(percentile_high, 100)

    # ========================================================================
    # Anomaly Detection Tests
    # ========================================================================

    def test_account_age_anomaly(self):
        """Test detection of new account anomalies"""
        result = self.server._detect_anomalies(
            transactions=[],
            account_age=15,
            baseline_spending=2000,
            locations=[]
        )

        self.assertGreater(len(result.anomalies_detected), 0)
        self.assertEqual(result.anomalies_detected[0]["type"], AnomalyType.ACCOUNT_AGE.value)

    def test_spending_spike_anomaly(self):
        """Test detection of spending spikes"""
        transactions = [
            {"date": "2024-01-01", "amount": 100, "category": "groceries"},
            {"date": "2024-01-02", "amount": 120, "category": "groceries"},
            {"date": "2024-01-03", "amount": 110, "category": "groceries"},
            {"date": "2024-01-04", "amount": 5000, "category": "luxury"},
        ]

        result = self.server._detect_anomalies(
            transactions=transactions,
            account_age=365,
            baseline_spending=110,
            locations=[]
        )

        # Check for spending spike anomaly
        spike_anomalies = [a for a in result.anomalies_detected if a["type"] == AnomalyType.SPENDING_SPIKE.value]
        self.assertGreater(len(spike_anomalies), 0)

    def test_geographic_anomaly(self):
        """Test detection of geographic anomalies"""
        locations = ["New York", "Los Angeles", "Miami", "Chicago"]

        result = self.server._detect_anomalies(
            transactions=[],
            account_age=365,
            baseline_spending=2000,
            locations=locations
        )

        geo_anomalies = [a for a in result.anomalies_detected if a["type"] == AnomalyType.GEOGRAPHIC_ANOMALY.value]
        self.assertGreater(len(geo_anomalies), 0)

    def test_no_anomalies_normal_case(self):
        """Test normal financial profile with no anomalies"""
        result = self.server._detect_anomalies(
            transactions=[
                {"date": "2024-01-01", "amount": 100},
                {"date": "2024-01-02", "amount": 95},
                {"date": "2024-01-03", "amount": 105},
            ],
            account_age=365,
            baseline_spending=100,
            locations=["New York"]
        )

        self.assertEqual(result.risk_score, 0.0)
        self.assertIn("No anomalies", result.summary or len(result.anomalies_detected) == 0)

    def test_anomaly_risk_score_calculation(self):
        """Test anomaly risk score calculation"""
        anomalies = [
            {"severity": "high", "risk_score": 0.9},
            {"severity": "medium", "risk_score": 0.6},
            {"severity": "low", "risk_score": 0.2}
        ]

        risk_score = self.server._calculate_overall_anomaly_risk(anomalies)

        self.assertGreater(risk_score, 0)
        self.assertLessEqual(risk_score, 1.0)

    # ========================================================================
    # Business Rules Tests
    # ========================================================================

    def test_ecoa_compliance_check(self):
        """Test ECOA (Equal Credit Opportunity Act) compliance"""
        applicant_data = {
            "name": "John Doe",
            "credit_score": 700,
            "annual_income": 75000
        }

        result = self.server._check_ecoa_compliance(applicant_data)
        self.assertTrue(result["compliant"])

    def test_ecoa_compliance_violation(self):
        """Test ECOA compliance with prohibited criteria"""
        applicant_data = {
            "name": "John Doe",
            "age": 65,
            "race": "Caucasian",
            "credit_score": 700
        }

        result = self.server._check_ecoa_compliance(applicant_data)
        self.assertFalse(result["compliant"])
        self.assertGreater(len(result["violations"]), 0)

    def test_fcra_compliance_check(self):
        """Test FCRA (Fair Credit Reporting Act) compliance"""
        applicant_data = {"credit_report_used": True}

        result = self.server._check_fcra_compliance(applicant_data)
        self.assertTrue(result["compliant"])

    def test_fcra_compliance_violation(self):
        """Test FCRA compliance violation"""
        applicant_data = {}

        result = self.server._check_fcra_compliance(applicant_data)
        self.assertFalse(result["compliant"])

    def test_lending_limits_check(self):
        """Test lending limits compliance"""
        applicant_data = {
            "debt_to_income": 0.35,
            "credit_score": 700,
            "annual_income": 75000
        }
        loan_details = {}
        limits = {
            "max_dti_ratio": 0.75,
            "min_credit_score": 500,
            "minimum_income": 15000
        }

        result = self.server._check_lending_limits(applicant_data, loan_details, limits)
        self.assertTrue(result["compliant"])

    def test_lending_limits_dti_violation(self):
        """Test lending limits DTI violation"""
        applicant_data = {
            "debt_to_income": 0.80,
            "credit_score": 700,
            "annual_income": 75000
        }
        loan_details = {}
        limits = {
            "max_dti_ratio": 0.75,
            "min_credit_score": 500,
            "minimum_income": 15000
        }

        result = self.server._check_lending_limits(applicant_data, loan_details, limits)
        self.assertFalse(result["compliant"])

    def test_fraud_detection_rules(self):
        """Test fraud detection rules"""
        applicant_data = {
            "account_age_days": 365,
            "applications_7_days": 1
        }
        loan_details = {"requested_amount": 25000}

        result = self.server._check_fraud_detection(applicant_data, loan_details)
        self.assertTrue(result["compliant"])

    def test_fraud_detection_synthetic_identity(self):
        """Test fraud detection for synthetic identity"""
        applicant_data = {
            "account_age_days": 15,
            "applications_7_days": 1
        }
        loan_details = {"requested_amount": 75000}

        result = self.server._check_fraud_detection(applicant_data, loan_details)
        self.assertFalse(result["compliant"])
        self.assertGreater(result["fraud_score"], 0)

    def test_fraud_detection_velocity(self):
        """Test fraud detection for high velocity"""
        applicant_data = {
            "account_age_days": 365,
            "applications_7_days": 8
        }
        loan_details = {"requested_amount": 25000}

        result = self.server._check_fraud_detection(applicant_data, loan_details)
        self.assertFalse(result["compliant"])

    def test_apply_business_rules_all(self):
        """Test applying all business rules"""
        applicant_data = {
            "name": "Jane Doe",
            "credit_score": 700,
            "annual_income": 75000,
            "debt_to_income": 0.35,
            "credit_report_used": True,
            "account_age_days": 365,
            "applications_7_days": 1
        }
        loan_details = {"requested_amount": 25000}

        result = self.server._apply_rules(applicant_data, loan_details, ["all"])

        self.assertIn("rules_applied", result)
        self.assertIn("overall_compliance", result)
        self.assertIn("violations", result)
        self.assertGreater(len(result["rules_applied"]), 0)

    # ========================================================================
    # Tool Interface Tests
    # ========================================================================

    def test_calculate_debt_to_income_tool(self):
        """Test calculate_debt_to_income tool interface"""
        result = self.server.calculate_debt_to_income(
            total_monthly_debt=1500,
            gross_monthly_income=5000,
            calculation_method="standard"
        )

        self.assertIn("ratio", result)
        self.assertIn("risk_level", result)

    def test_assess_credit_score_risk_tool(self):
        """Test assess_credit_score_risk tool interface"""
        result = self.server.assess_credit_score_risk(
            credit_score=700,
            industry_type="personal_loans"
        )

        self.assertIn("credit_score", result)
        self.assertIn("risk_level", result)

    def test_detect_financial_anomalies_tool(self):
        """Test detect_financial_anomalies tool interface"""
        result = self.server.detect_financial_anomalies(
            transaction_history=[],
            account_age_days=365,
            baseline_monthly_spending=2000
        )

        self.assertIn("anomalies_detected", result)
        self.assertIn("risk_score", result)

    def test_apply_business_rules_tool(self):
        """Test apply_business_rules tool interface"""
        result = self.server.apply_business_rules(
            applicant_data={"credit_score": 700},
            loan_details={}
        )

        self.assertIn("rules_applied", result)
        self.assertIn("overall_compliance", result)

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_complete_risk_assessment_low_risk(self):
        """Test complete risk assessment for low-risk applicant"""
        dti_result = self.server._calculate_dti(1500, 5000)
        credit_result = self.server._assess_credit_risk(750, "personal_loans")
        anomaly_result = self.server._detect_anomalies([], 365, 2000, ["New York"])

        self.assertEqual(dti_result.risk_level, RiskLevel.LOW.value)
        self.assertEqual(credit_result.risk_level, RiskLevel.LOW.value)
        self.assertEqual(anomaly_result.risk_score, 0.0)

    def test_complete_risk_assessment_high_risk(self):
        """Test complete risk assessment for high-risk applicant"""
        dti_result = self.server._calculate_dti(3000, 4000)
        credit_result = self.server._assess_credit_risk(550, "personal_loans", 8, 3)
        anomaly_result = self.server._detect_anomalies([], 15, 2000, [])

        self.assertEqual(dti_result.risk_level, RiskLevel.CRITICAL.value)
        self.assertEqual(credit_result.risk_level, RiskLevel.HIGH.value)
        self.assertGreater(anomaly_result.risk_score, 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.server = RiskRulesDBServer("riskrulesdb_config.json")

    def test_zero_income(self):
        """Test handling of zero income"""
        result = self.server.calculate_debt_to_income(
            total_monthly_debt=1000,
            gross_monthly_income=0
        )
        self.assertIn("error", result)

    def test_negative_debt(self):
        """Test handling of negative debt (should be allowed as offset)"""
        result = self.server._calculate_dti(
            total_debt=-500,
            income=5000
        )
        self.assertEqual(result.ratio, -0.1)

    def test_very_high_credit_score(self):
        """Test handling of very high credit score"""
        result = self.server._assess_credit_risk(850, "personal_loans")
        self.assertEqual(result.category, "excellent")

    def test_very_low_credit_score(self):
        """Test handling of very low credit score"""
        result = self.server._assess_credit_risk(300, "personal_loans")
        self.assertEqual(result.category, "very_poor")

    def test_empty_transaction_history(self):
        """Test anomaly detection with empty transaction history"""
        result = self.server._detect_anomalies([], 365, 2000, [])
        self.assertIsInstance(result, AnomalyDetectionResult)

    def test_single_transaction(self):
        """Test anomaly detection with single transaction"""
        result = self.server._detect_anomalies(
            [{"date": "2024-01-01", "amount": 100}],
            365,
            100,
            []
        )
        self.assertIsInstance(result, AnomalyDetectionResult)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestRiskRulesDBServer))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
