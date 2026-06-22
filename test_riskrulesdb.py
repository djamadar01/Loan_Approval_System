#!/usr/bin/env python3
"""
Test Suite for RiskRulesDB MCP Server
Comprehensive testing of financial risk analysis functionality.
"""

import json
from riskrulesdb_mcp_server import (
    RiskRulesEngine,
    RiskLevel,
    CreditScoreRiskLevel,
    analyze_financial_risk,
    calculate_dti_threshold,
    get_risk_thresholds,
    batch_risk_analysis,
)


class TestRiskRulesEngine:
    """Test the core business rules engine."""

    def test_dti_excellent(self):
        """Test DTI calculation for excellent ratio."""
        result = RiskRulesEngine.calculate_dti(1000, 6000)
        assert result.debt_to_income_ratio == 1000 / 6000
        assert result.risk_level == RiskLevel.LOW
        assert "Excellent" in result.recommendation

    def test_dti_good(self):
        """Test DTI calculation for good ratio."""
        result = RiskRulesEngine.calculate_dti(1800, 5000)
        assert result.risk_level == RiskLevel.LOW
        assert "Good" in result.recommendation

    def test_dti_acceptable(self):
        """Test DTI calculation for acceptable ratio."""
        result = RiskRulesEngine.calculate_dti(2000, 5000)
        assert result.risk_level == RiskLevel.MEDIUM
        assert "Acceptable" in result.recommendation

    def test_dti_high(self):
        """Test DTI calculation for high ratio."""
        result = RiskRulesEngine.calculate_dti(2300, 5000)
        assert result.risk_level == RiskLevel.HIGH
        assert "High" in result.recommendation

    def test_dti_critical(self):
        """Test DTI calculation for critical ratio."""
        result = RiskRulesEngine.calculate_dti(2600, 5000)
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Critical" in result.recommendation

    def test_dti_zero_income_error(self):
        """Test DTI with zero income raises error."""
        try:
            RiskRulesEngine.calculate_dti(1000, 0)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "positive" in str(e)

    def test_credit_score_excellent(self):
        """Test credit score assessment for excellent score."""
        result = RiskRulesEngine.calculate_credit_risk(820)
        assert result.risk_level == CreditScoreRiskLevel.EXCELLENT
        assert result.risk_percentage == 1.0
        assert "Excellent" in result.recommendation

    def test_credit_score_good(self):
        """Test credit score assessment for good score."""
        result = RiskRulesEngine.calculate_credit_risk(770)
        assert result.risk_level == CreditScoreRiskLevel.GOOD
        assert result.risk_percentage == 2.0

    def test_credit_score_fair(self):
        """Test credit score assessment for fair score."""
        result = RiskRulesEngine.calculate_credit_risk(700)
        assert result.risk_level == CreditScoreRiskLevel.FAIR
        assert result.risk_percentage == 5.0

    def test_credit_score_poor(self):
        """Test credit score assessment for poor score."""
        result = RiskRulesEngine.calculate_credit_risk(620)
        assert result.risk_level == CreditScoreRiskLevel.POOR
        assert result.risk_percentage == 15.0

    def test_credit_score_very_poor(self):
        """Test credit score assessment for very poor score."""
        result = RiskRulesEngine.calculate_credit_risk(520)
        assert result.risk_level == CreditScoreRiskLevel.VERY_POOR
        assert result.risk_percentage == 30.0

    def test_credit_score_boundary_800(self):
        """Test credit score at boundary (800)."""
        result = RiskRulesEngine.calculate_credit_risk(800)
        assert result.risk_level == CreditScoreRiskLevel.EXCELLENT

    def test_credit_score_boundary_750(self):
        """Test credit score at boundary (750)."""
        result = RiskRulesEngine.calculate_credit_risk(750)
        assert result.risk_level == CreditScoreRiskLevel.GOOD

    def test_credit_score_invalid_low(self):
        """Test credit score below minimum."""
        try:
            RiskRulesEngine.calculate_credit_risk(299)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_credit_score_invalid_high(self):
        """Test credit score above maximum."""
        try:
            RiskRulesEngine.calculate_credit_risk(851)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_loan_risk_low(self):
        """Test loan amount assessment for low risk."""
        result = RiskRulesEngine.calculate_loan_risk(100000, 5000, 500)
        assert result.risk_level == RiskLevel.LOW

    def test_loan_risk_medium(self):
        """Test loan amount assessment for medium risk."""
        result = RiskRulesEngine.calculate_loan_risk(150000, 5000, 500)
        assert result.risk_level == RiskLevel.MEDIUM

    def test_loan_risk_high(self):
        """Test loan amount assessment for high risk."""
        result = RiskRulesEngine.calculate_loan_risk(200000, 5000, 500)
        assert result.risk_level == RiskLevel.HIGH

    def test_loan_risk_zero_loan(self):
        """Test loan amount of zero."""
        result = RiskRulesEngine.calculate_loan_risk(0, 5000, 500)
        assert result.loan_amount == 0
        assert result.risk_level == RiskLevel.LOW

    def test_loan_risk_negative_loan_error(self):
        """Test negative loan amount raises error."""
        try:
            RiskRulesEngine.calculate_loan_risk(-100, 5000, 500)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_anomaly_extreme_dti(self):
        """Test anomaly detection for extreme DTI."""
        anomalies = RiskRulesEngine.detect_anomalies(
            credit_score=700,
            monthly_income=2000,
            monthly_debt_payments=1300,
            loan_amount=100000,
        )
        extreme_dti = [a for a in anomalies if a.flag_type == "EXTREME_DTI"]
        assert len(extreme_dti) > 0
        assert extreme_dti[0].severity == RiskLevel.CRITICAL

    def test_anomaly_very_low_credit_score(self):
        """Test anomaly detection for very low credit score."""
        anomalies = RiskRulesEngine.detect_anomalies(
            credit_score=450,
            monthly_income=5000,
            monthly_debt_payments=1000,
            loan_amount=100000,
        )
        low_credit = [a for a in anomalies if a.flag_type == "VERY_LOW_CREDIT_SCORE"]
        assert len(low_credit) > 0
        assert low_credit[0].severity == RiskLevel.CRITICAL

    def test_anomaly_low_income(self):
        """Test anomaly detection for low income."""
        anomalies = RiskRulesEngine.detect_anomalies(
            credit_score=700,
            monthly_income=1000,
            monthly_debt_payments=200,
            loan_amount=50000,
        )
        low_income = [a for a in anomalies if a.flag_type == "LOW_INCOME"]
        assert len(low_income) > 0
        assert low_income[0].severity == RiskLevel.HIGH

    def test_anomaly_large_loan_amount(self):
        """Test anomaly detection for large loan amount."""
        anomalies = RiskRulesEngine.detect_anomalies(
            credit_score=700,
            monthly_income=2000,
            monthly_debt_payments=200,
            loan_amount=1500000,
        )
        large_loan = [a for a in anomalies if a.flag_type == "LARGE_LOAN_AMOUNT"]
        assert len(large_loan) > 0
        assert large_loan[0].severity == RiskLevel.HIGH

    def test_anomaly_dti_spike(self):
        """Test anomaly detection for DTI spike."""
        anomalies = RiskRulesEngine.detect_anomalies(
            credit_score=700,
            monthly_income=5000,
            monthly_debt_payments=2500,
            loan_amount=100000,
            previous_dti=0.20,
        )
        dti_spike = [a for a in anomalies if a.flag_type == "DTI_SPIKE"]
        assert len(dti_spike) > 0
        assert dti_spike[0].severity == RiskLevel.MEDIUM

    def test_anomaly_no_anomalies(self):
        """Test clean profile with no anomalies."""
        anomalies = RiskRulesEngine.detect_anomalies(
            credit_score=750,
            monthly_income=8000,
            monthly_debt_payments=1000,
            loan_amount=200000,
        )
        assert len(anomalies) == 0

    def test_overall_risk_low(self):
        """Test overall risk calculation for low risk."""
        risk, recommendation = RiskRulesEngine.calculate_overall_risk(
            RiskLevel.LOW,
            CreditScoreRiskLevel.EXCELLENT,
            RiskLevel.LOW,
            anomaly_count=0,
        )
        assert risk == RiskLevel.LOW
        assert "APPROVE" in recommendation

    def test_overall_risk_medium(self):
        """Test overall risk calculation for medium risk."""
        risk, recommendation = RiskRulesEngine.calculate_overall_risk(
            RiskLevel.MEDIUM,
            CreditScoreRiskLevel.FAIR,
            RiskLevel.MEDIUM,
            anomaly_count=0,
        )
        assert risk == RiskLevel.MEDIUM
        assert "REVIEW" in recommendation

    def test_overall_risk_high(self):
        """Test overall risk calculation for high risk."""
        risk, recommendation = RiskRulesEngine.calculate_overall_risk(
            RiskLevel.HIGH,
            CreditScoreRiskLevel.POOR,
            RiskLevel.HIGH,
            anomaly_count=0,
        )
        assert risk == RiskLevel.HIGH
        assert "CONDITIONAL" in recommendation

    def test_overall_risk_critical(self):
        """Test overall risk calculation for critical risk."""
        risk, recommendation = RiskRulesEngine.calculate_overall_risk(
            RiskLevel.CRITICAL,
            CreditScoreRiskLevel.VERY_POOR,
            RiskLevel.CRITICAL,
            anomaly_count=0,
        )
        assert risk == RiskLevel.CRITICAL
        assert "DENY" in recommendation

    def test_overall_risk_with_anomalies(self):
        """Test overall risk calculation with anomalies."""
        risk, recommendation = RiskRulesEngine.calculate_overall_risk(
            RiskLevel.MEDIUM,
            CreditScoreRiskLevel.FAIR,
            RiskLevel.MEDIUM,
            anomaly_count=3,
        )
        # Anomalies should push toward higher risk
        assert risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class TestFinancialRiskAnalysisTool:
    """Test the main analysis tool."""

    def test_low_risk_profile(self):
        """Test analysis of low-risk applicant."""
        result = analyze_financial_risk(
            credit_score=780,
            monthly_gross_income=6000,
            monthly_debt_payments=1200,
            loan_amount=250000,
        )
        assert result["status"] == "success"
        assert result["analysis"]["overall_risk_level"] == "low"
        assert "APPROVE" in result["analysis"]["approval_recommendation"]

    def test_medium_risk_profile(self):
        """Test analysis of medium-risk applicant."""
        result = analyze_financial_risk(
            credit_score=700,
            monthly_gross_income=5000,
            monthly_debt_payments=1500,
            loan_amount=200000,
        )
        assert result["status"] == "success"
        assert result["analysis"]["overall_risk_level"] in ["medium", "high"]

    def test_high_risk_profile(self):
        """Test analysis of high-risk applicant."""
        result = analyze_financial_risk(
            credit_score=550,
            monthly_gross_income=3500,
            monthly_debt_payments=2000,
            loan_amount=300000,
        )
        assert result["status"] == "success"
        assert result["analysis"]["overall_risk_level"] in ["high", "critical"]

    def test_validation_credit_score_low(self):
        """Test validation of credit score too low."""
        result = analyze_financial_risk(
            credit_score=299,
            monthly_gross_income=5000,
            monthly_debt_payments=1000,
            loan_amount=100000,
        )
        assert result["status"] == "error"
        assert "300-850" in result["error"]

    def test_validation_credit_score_high(self):
        """Test validation of credit score too high."""
        result = analyze_financial_risk(
            credit_score=851,
            monthly_gross_income=5000,
            monthly_debt_payments=1000,
            loan_amount=100000,
        )
        assert result["status"] == "error"

    def test_validation_income_zero(self):
        """Test validation of zero income."""
        result = analyze_financial_risk(
            credit_score=700,
            monthly_gross_income=0,
            monthly_debt_payments=1000,
            loan_amount=100000,
        )
        assert result["status"] == "error"
        assert "positive" in result["error"]

    def test_validation_income_negative(self):
        """Test validation of negative income."""
        result = analyze_financial_risk(
            credit_score=700,
            monthly_gross_income=-5000,
            monthly_debt_payments=1000,
            loan_amount=100000,
        )
        assert result["status"] == "error"

    def test_validation_debt_negative(self):
        """Test validation of negative debt."""
        result = analyze_financial_risk(
            credit_score=700,
            monthly_gross_income=5000,
            monthly_debt_payments=-1000,
            loan_amount=100000,
        )
        assert result["status"] == "error"

    def test_validation_loan_negative(self):
        """Test validation of negative loan."""
        result = analyze_financial_risk(
            credit_score=700,
            monthly_gross_income=5000,
            monthly_debt_payments=1000,
            loan_amount=-100000,
        )
        assert result["status"] == "error"

    def test_previous_dti_for_spike_detection(self):
        """Test DTI spike detection with previous DTI."""
        result = analyze_financial_risk(
            credit_score=700,
            monthly_gross_income=5000,
            monthly_debt_payments=2500,
            loan_amount=100000,
            previous_dti=0.20,
        )
        assert result["status"] == "success"
        # Should detect DTI spike
        anomalies = result["analysis"]["anomalies"]
        dti_spike = [a for a in anomalies if a["flag_type"] == "DTI_SPIKE"]
        assert len(dti_spike) > 0

    def test_response_structure(self):
        """Test that response has complete structure."""
        result = analyze_financial_risk(
            credit_score=750,
            monthly_gross_income=6000,
            monthly_debt_payments=1200,
            loan_amount=250000,
        )
        assert result["status"] == "success"
        analysis = result["analysis"]
        assert "dti_analysis" in analysis
        assert "credit_analysis" in analysis
        assert "loan_analysis" in analysis
        assert "anomalies" in analysis
        assert "overall_risk_level" in analysis
        assert "approval_recommendation" in analysis

    def test_dti_analysis_structure(self):
        """Test DTI analysis has correct fields."""
        result = analyze_financial_risk(
            credit_score=750,
            monthly_gross_income=6000,
            monthly_debt_payments=1200,
            loan_amount=250000,
        )
        dti = result["analysis"]["dti_analysis"]
        assert "monthly_debt_payments" in dti
        assert "monthly_gross_income" in dti
        assert "debt_to_income_ratio" in dti
        assert "risk_level" in dti
        assert "recommendation" in dti


class TestDTIThresholdTool:
    """Test DTI threshold calculation tool."""

    def test_dti_threshold_standard(self):
        """Test DTI threshold with standard 36% target."""
        result = calculate_dti_threshold(5000)
        assert result["status"] == "success"
        assert result["max_debt_payment"] == 1800.0
        assert "36%" in result["message"]

    def test_dti_threshold_custom(self):
        """Test DTI threshold with custom target."""
        result = calculate_dti_threshold(5000, target_dti=0.20)
        assert result["status"] == "success"
        assert result["max_debt_payment"] == 1000.0

    def test_dti_threshold_zero_income(self):
        """Test DTI threshold with zero income."""
        result = calculate_dti_threshold(0)
        assert result["status"] == "error"

    def test_dti_threshold_negative_income(self):
        """Test DTI threshold with negative income."""
        result = calculate_dti_threshold(-5000)
        assert result["status"] == "error"

    def test_dti_threshold_invalid_dti_zero(self):
        """Test DTI threshold with zero DTI."""
        result = calculate_dti_threshold(5000, target_dti=0)
        assert result["status"] == "error"

    def test_dti_threshold_invalid_dti_above_one(self):
        """Test DTI threshold with DTI > 1."""
        result = calculate_dti_threshold(5000, target_dti=1.5)
        assert result["status"] == "error"


class TestBatchRiskAnalysisTool:
    """Test batch processing tool."""

    def test_batch_three_applicants(self):
        """Test batch processing with three applicants."""
        applicants = [
            {
                "credit_score": 750,
                "monthly_gross_income": 5500,
                "monthly_debt_payments": 1100,
                "loan_amount": 200000,
            },
            {
                "credit_score": 600,
                "monthly_gross_income": 4000,
                "monthly_debt_payments": 1600,
                "loan_amount": 300000,
            },
            {
                "credit_score": 820,
                "monthly_gross_income": 8000,
                "monthly_debt_payments": 1600,
                "loan_amount": 500000,
            },
        ]
        result = batch_risk_analysis(applicants)
        assert result["status"] == "success"
        assert result["total_applicants"] == 3
        assert len(result["analyses"]) == 3
        assert "summary" in result
        assert "approved" in result["summary"]
        assert "conditional" in result["summary"]
        assert "denied" in result["summary"]

    def test_batch_empty_list(self):
        """Test batch with empty list."""
        result = batch_risk_analysis([])
        assert result["status"] == "error"
        assert "empty" in result["error"]

    def test_batch_single_applicant(self):
        """Test batch with single applicant."""
        applicants = [
            {
                "credit_score": 750,
                "monthly_gross_income": 5500,
                "monthly_debt_payments": 1100,
                "loan_amount": 200000,
            }
        ]
        result = batch_risk_analysis(applicants)
        assert result["status"] == "success"
        assert result["total_applicants"] == 1

    def test_batch_not_a_list(self):
        """Test batch with non-list input."""
        result = batch_risk_analysis({"credit_score": 750})
        assert result["status"] == "error"
        assert "list" in result["error"]

    def test_batch_too_many_applicants(self):
        """Test batch with more than 100 applicants."""
        applicants = [
            {
                "credit_score": 750,
                "monthly_gross_income": 5000,
                "monthly_debt_payments": 1000,
                "loan_amount": 200000,
            }
        ] * 101
        result = batch_risk_analysis(applicants)
        assert result["status"] == "error"
        assert "100" in result["error"]


class TestRiskThresholdsTool:
    """Test risk thresholds retrieval tool."""

    def test_get_risk_thresholds(self):
        """Test getting risk thresholds."""
        result = get_risk_thresholds()
        assert result["status"] == "success"
        assert "dti_thresholds" in result
        assert "credit_score_thresholds" in result
        assert "loan_to_income_ratio_thresholds" in result
        assert "anomaly_detection_triggers" in result

    def test_dti_thresholds_structure(self):
        """Test DTI thresholds structure."""
        result = get_risk_thresholds()
        dti = result["dti_thresholds"]
        assert "excellent" in dti
        assert "good" in dti
        assert "acceptable" in dti
        assert "high" in dti
        assert "critical" in dti


def run_all_tests():
    """Run all tests and report results."""
    test_classes = [
        TestRiskRulesEngine,
        TestFinancialRiskAnalysisTool,
        TestDTIThresholdTool,
        TestBatchRiskAnalysisTool,
        TestRiskThresholdsTool,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print(f"{'='*60}")

        instance = test_class()
        test_methods = [
            method for method in dir(instance) if method.startswith("test_")
        ]

        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                passed_tests += 1
                print(f"✓ {method_name}")
            except AssertionError as e:
                failed_tests += 1
                print(f"✗ {method_name}")
                print(f"  Error: {str(e)}")
            except Exception as e:
                failed_tests += 1
                print(f"✗ {method_name}")
                print(f"  Exception: {str(e)}")

    print(f"\n{'='*60}")
    print(f"Test Results Summary")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    return failed_tests == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
