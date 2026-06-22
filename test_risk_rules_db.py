#!/usr/bin/env python3
"""
Comprehensive test suite for RiskRulesDB MCP Server
Validates all business rules and calculation accuracy
"""

import sys
import json
from risk_rules_db_server import RiskRulesEngine, RiskLevel


class TestRunner:
    """Test runner for RiskRulesDB"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name: str, condition: bool, details: str = ""):
        """Record test result"""
        status = "✓ PASS" if condition else "✗ FAIL"
        self.tests.append({"name": name, "status": status, "condition": condition})
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{status}: {name}")
        if details and not condition:
            print(f"       {details}")

    def summary(self):
        """Print summary"""
        total = self.passed + self.failed
        pct = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'=' * 80}")
        print(f"Test Results: {self.passed}/{total} passed ({pct:.1f}%)")
        print(f"{'=' * 80}\n")
        return self.failed == 0


def test_dti_calculations():
    """Test DTI ratio calculations"""
    print("\n" + "=" * 80)
    print("DTI RATIO CALCULATION TESTS")
    print("=" * 80)
    runner = TestRunner()

    # Test 1: Low DTI (30%)
    dti = RiskRulesEngine.calculate_dti_ratio(2400, 8000)
    runner.test("DTI 30% = LOW risk", dti.risk_level == RiskLevel.LOW)
    runner.test("DTI ratio calculation", dti.ratio == 0.30)

    # Test 2: Medium DTI (45%)
    dti = RiskRulesEngine.calculate_dti_ratio(3600, 8000)
    runner.test("DTI 45% = MEDIUM risk", dti.risk_level == RiskLevel.MEDIUM)
    runner.test("DTI 45% ratio", dti.ratio == 0.45)

    # Test 3: High DTI (52%)
    dti = RiskRulesEngine.calculate_dti_ratio(4160, 8000)
    runner.test("DTI 52% = HIGH risk", dti.risk_level == RiskLevel.HIGH)

    # Test 4: Critical DTI (70%)
    dti = RiskRulesEngine.calculate_dti_ratio(5600, 8000)
    runner.test("DTI 70% = CRITICAL risk", dti.risk_level == RiskLevel.CRITICAL)

    # Test 5: Edge case - exactly at threshold (43%)
    dti = RiskRulesEngine.calculate_dti_ratio(3440, 8000)
    runner.test("DTI 43% at threshold", dti.risk_level == RiskLevel.LOW)

    # Test 6: Zero debt
    dti = RiskRulesEngine.calculate_dti_ratio(0, 8000)
    runner.test("DTI with zero debt", dti.ratio == 0.0)
    runner.test("Zero debt = LOW risk", dti.risk_level == RiskLevel.LOW)

    # Test 7: Error handling - zero income
    try:
        RiskRulesEngine.calculate_dti_ratio(1000, 0)
        runner.test("Zero income validation", False, "Should raise ValueError")
    except ValueError:
        runner.test("Zero income validation", True)

    return runner.summary()


def test_credit_score_assessment():
    """Test credit score risk assessment"""
    print("\n" + "=" * 80)
    print("CREDIT SCORE ASSESSMENT TESTS")
    print("=" * 80)
    runner = TestRunner()

    # Test 1: Excellent (800+)
    credit = RiskRulesEngine.assess_credit_score_risk(800)
    runner.test("Credit 800 = EXCELLENT", credit.risk_category == "EXCELLENT")
    runner.test("Credit 800 = LOW risk", credit.risk_level == RiskLevel.LOW)

    # Test 2: Good (700)
    credit = RiskRulesEngine.assess_credit_score_risk(700)
    runner.test("Credit 700 = GOOD", credit.risk_category == "GOOD")
    runner.test("Credit 700 = LOW risk", credit.risk_level == RiskLevel.LOW)

    # Test 3: Fair (620)
    credit = RiskRulesEngine.assess_credit_score_risk(620)
    runner.test("Credit 620 = FAIR", credit.risk_category == "FAIR")
    runner.test("Credit 620 = MEDIUM risk", credit.risk_level == RiskLevel.MEDIUM)

    # Test 4: Poor (550)
    credit = RiskRulesEngine.assess_credit_score_risk(550)
    runner.test("Credit 550 = POOR", credit.risk_category == "POOR")
    runner.test("Credit 550 = HIGH risk", credit.risk_level == RiskLevel.HIGH)

    # Test 5: Boundary - excellent min (750)
    credit = RiskRulesEngine.assess_credit_score_risk(750)
    runner.test("Credit 750 = EXCELLENT", credit.risk_category == "EXCELLENT")

    # Test 6: Boundary - good min (670)
    credit = RiskRulesEngine.assess_credit_score_risk(670)
    runner.test("Credit 670 = GOOD", credit.risk_category == "GOOD")

    # Test 7: Factors list for poor credit
    credit = RiskRulesEngine.assess_credit_score_risk(550)
    runner.test("Poor credit has factors", len(credit.factors) > 0)
    runner.test("Factors include defaults", any("default" in f.lower() for f in credit.factors))

    # Test 8: Error handling - out of range
    try:
        RiskRulesEngine.assess_credit_score_risk(900)
        runner.test("Score > 850 validation", False, "Should raise ValueError")
    except ValueError:
        runner.test("Score > 850 validation", True)

    try:
        RiskRulesEngine.assess_credit_score_risk(200)
        runner.test("Score < 300 validation", False, "Should raise ValueError")
    except ValueError:
        runner.test("Score < 300 validation", True)

    return runner.summary()


def test_loan_amount_assessment():
    """Test loan amount risk assessment"""
    print("\n" + "=" * 80)
    print("LOAN AMOUNT RISK ASSESSMENT TESTS")
    print("=" * 80)
    runner = TestRunner()

    # Test 1: Conservative (2x income)
    loan = RiskRulesEngine.assess_loan_amount_risk(200000, 100000)
    runner.test("Loan 2x income = LOW risk", loan.risk_level == RiskLevel.LOW)
    runner.test("Loan 2x income LTI", loan.ltv_ratio == 2.0)

    # Test 2: Moderate (3x income)
    loan = RiskRulesEngine.assess_loan_amount_risk(300000, 100000)
    runner.test("Loan 3x income = MEDIUM risk", loan.risk_level == RiskLevel.MEDIUM)
    runner.test("Loan 3x income LTI", loan.ltv_ratio == 3.0)

    # Test 3: Aggressive (3.5x income)
    loan = RiskRulesEngine.assess_loan_amount_risk(350000, 100000)
    runner.test("Loan 3.5x income = HIGH risk", loan.risk_level == RiskLevel.HIGH)

    # Test 4: Excessive (5x income)
    loan = RiskRulesEngine.assess_loan_amount_risk(500000, 100000)
    runner.test("Loan 5x income = CRITICAL risk", loan.risk_level == RiskLevel.CRITICAL)
    runner.test("Loan 5x income LTI", loan.ltv_ratio == 5.0)

    # Test 5: Max recommended loan calculation
    loan = RiskRulesEngine.assess_loan_amount_risk(300000, 100000)
    runner.test("Max recommended loan present", loan.max_recommended_loan > 0)
    runner.test("Max recommended reasonable", loan.max_recommended_loan >= 300000)

    # Test 6: Zero loan amount
    loan = RiskRulesEngine.assess_loan_amount_risk(0, 100000)
    runner.test("Zero loan = LOW risk", loan.risk_level == RiskLevel.LOW)

    # Test 7: Factors included
    loan = RiskRulesEngine.assess_loan_amount_risk(400000, 100000)
    runner.test("Loan factors included", len(loan.factors) > 0)

    # Test 8: Error handling
    try:
        RiskRulesEngine.assess_loan_amount_risk(100000, 0)
        runner.test("Zero income validation", False, "Should raise ValueError")
    except ValueError:
        runner.test("Zero income validation", True)

    return runner.summary()


def test_anomaly_detection():
    """Test anomaly detection"""
    print("\n" + "=" * 80)
    print("ANOMALY DETECTION TESTS")
    print("=" * 80)
    runner = TestRunner()

    # Test 1: No anomalies (clean profile)
    anomalies = RiskRulesEngine.detect_anomalies(
        dti_ratio=0.30,
        credit_score=750,
        loan_to_income=2.5,
        monthly_debt=2400,
        monthly_income=8000,
    )
    runner.test("Clean profile has no anomalies", not anomalies.has_anomalies)
    runner.test("Clean profile anomaly score", anomalies.anomaly_score == 0.0)

    # Test 2: High DTI anomaly
    anomalies = RiskRulesEngine.detect_anomalies(
        dti_ratio=0.55,
        credit_score=750,
        loan_to_income=2.5,
        monthly_debt=4400,
        monthly_income=8000,
    )
    runner.test("High DTI detected", "High DTI" in str(anomalies.flags))
    runner.test("High DTI has anomalies", anomalies.has_anomalies)

    # Test 3: Low credit score anomaly
    anomalies = RiskRulesEngine.detect_anomalies(
        dti_ratio=0.30,
        credit_score=580,
        loan_to_income=2.5,
        monthly_debt=2400,
        monthly_income=8000,
    )
    runner.test("Low credit detected", any("credit" in f.lower() for f in anomalies.flags))

    # Test 4: High loan-to-income anomaly
    anomalies = RiskRulesEngine.detect_anomalies(
        dti_ratio=0.30,
        credit_score=750,
        loan_to_income=4.5,
        monthly_debt=2400,
        monthly_income=8000,
    )
    runner.test("High LTI detected", any("loan" in f.lower() for f in anomalies.flags))

    # Test 5: Multiple anomalies
    anomalies = RiskRulesEngine.detect_anomalies(
        dti_ratio=0.60,
        credit_score=550,
        loan_to_income=5.0,
        monthly_debt=4800,
        monthly_income=8000,
    )
    runner.test("Multiple anomalies detected", len(anomalies.flags) >= 2)
    runner.test("Anomaly score > 0.5", anomalies.anomaly_score > 0.5)

    # Test 6: Anomaly score scaling
    anomalies = RiskRulesEngine.detect_anomalies(
        dti_ratio=0.30,
        credit_score=750,
        loan_to_income=2.5,
        monthly_debt=2400,
        monthly_income=8000,
    )
    runner.test("Anomaly score 0-1 range", 0 <= anomalies.anomaly_score <= 1.0)

    return runner.summary()


def test_business_rules_thresholds():
    """Test business rules threshold values"""
    print("\n" + "=" * 80)
    print("BUSINESS RULES THRESHOLD TESTS")
    print("=" * 80)
    runner = TestRunner()

    # DTI Rules
    runner.test(
        "DTI acceptable max = 0.43",
        RiskRulesEngine.DTI_RULES["acceptable_max"] == 0.43,
    )
    runner.test(
        "DTI warning threshold = 0.50",
        RiskRulesEngine.DTI_RULES["warning_threshold"] == 0.50,
    )
    runner.test(
        "DTI critical threshold = 0.60",
        RiskRulesEngine.DTI_RULES["critical_threshold"] == 0.60,
    )

    # Credit Score Rules
    runner.test(
        "Excellent credit min = 750",
        RiskRulesEngine.CREDIT_SCORE_RULES["excellent_min"] == 750,
    )
    runner.test(
        "Good credit min = 670",
        RiskRulesEngine.CREDIT_SCORE_RULES["good_min"] == 670,
    )
    runner.test(
        "Fair credit min = 580",
        RiskRulesEngine.CREDIT_SCORE_RULES["fair_min"] == 580,
    )

    # Loan Amount Rules
    runner.test(
        "Conservative ratio = 2.5",
        RiskRulesEngine.LOAN_AMOUNT_RULES["conservative_ratio"] == 2.5,
    )
    runner.test(
        "Moderate ratio = 3.0",
        RiskRulesEngine.LOAN_AMOUNT_RULES["moderate_ratio"] == 3.0,
    )
    runner.test(
        "Aggressive ratio = 3.5",
        RiskRulesEngine.LOAN_AMOUNT_RULES["aggressive_ratio"] == 3.5,
    )

    # Anomaly Rules
    runner.test(
        "Anomaly high DTI = 0.50",
        RiskRulesEngine.ANOMALY_DETECTION_RULES["high_dti_threshold"] == 0.50,
    )
    runner.test(
        "Anomaly low credit = 600",
        RiskRulesEngine.ANOMALY_DETECTION_RULES["low_credit_threshold"] == 600,
    )

    return runner.summary()


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n" + "=" * 80)
    print("EDGE CASE TESTS")
    print("=" * 80)
    runner = TestRunner()

    # Test 1: Very high income
    dti = RiskRulesEngine.calculate_dti_ratio(10000, 1000000)
    runner.test("Very high income", dti.ratio == 0.01)
    runner.test("Very high income = LOW risk", dti.risk_level == RiskLevel.LOW)

    # Test 2: Very low income
    dti = RiskRulesEngine.calculate_dti_ratio(100, 1000)
    runner.test("Very low income", dti.ratio == 0.1)

    # Test 3: Large loan amount
    loan = RiskRulesEngine.assess_loan_amount_risk(10000000, 500000)
    runner.test("Large loan amount", loan.ltv_ratio == 20.0)
    runner.test("Large loan = CRITICAL", loan.risk_level == RiskLevel.CRITICAL)

    # Test 4: Perfect borrower profile
    dti = RiskRulesEngine.calculate_dti_ratio(2000, 10000)
    credit = RiskRulesEngine.assess_credit_score_risk(850)
    loan = RiskRulesEngine.assess_loan_amount_risk(150000, 150000)
    runner.test("Perfect DTI", dti.risk_level == RiskLevel.LOW)
    runner.test("Perfect credit", credit.risk_level == RiskLevel.LOW)
    runner.test("Perfect loan", loan.risk_level == RiskLevel.LOW)

    # Test 5: Worst borrower profile
    dti = RiskRulesEngine.calculate_dti_ratio(5000, 5000)
    credit = RiskRulesEngine.assess_credit_score_risk(300)
    loan = RiskRulesEngine.assess_loan_amount_risk(1000000, 50000)
    runner.test("Worst DTI", dti.risk_level == RiskLevel.CRITICAL)
    runner.test("Worst credit", credit.risk_level == RiskLevel.HIGH)
    runner.test("Worst loan", loan.risk_level == RiskLevel.CRITICAL)

    return runner.summary()


def test_data_types_and_precision():
    """Test data type handling and numeric precision"""
    print("\n" + "=" * 80)
    print("DATA TYPE AND PRECISION TESTS")
    print("=" * 80)
    runner = TestRunner()

    # Test 1: Float precision
    dti = RiskRulesEngine.calculate_dti_ratio(2400.50, 8000.75)
    runner.test("Float DTI calculation", isinstance(dti.ratio, float))
    runner.test("DTI ratio rounded to 4 decimals", len(str(dti.ratio).split(".")[-1]) <= 4)

    # Test 2: Integer credit score
    credit = RiskRulesEngine.assess_credit_score_risk(750)
    runner.test("Credit score is integer", isinstance(credit.credit_score, int))

    # Test 3: Risk level is enum value
    dti = RiskRulesEngine.calculate_dti_ratio(2400, 8000)
    runner.test("Risk level is RiskLevel", isinstance(dti.risk_level, RiskLevel))

    # Test 4: Loan max is float
    loan = RiskRulesEngine.assess_loan_amount_risk(250000, 100000)
    runner.test("Max recommended is float", isinstance(loan.max_recommended_loan, float))

    # Test 5: Recommendation is string
    dti = RiskRulesEngine.calculate_dti_ratio(2400, 8000)
    runner.test("Recommendation is string", isinstance(dti.recommendation, str))

    # Test 6: Factors is list
    credit = RiskRulesEngine.assess_credit_score_risk(750)
    runner.test("Factors is list", isinstance(credit.factors, list))

    # Test 7: Anomaly flags is list
    anomalies = RiskRulesEngine.detect_anomalies(0.30, 750, 2.5, 2400, 8000)
    runner.test("Anomaly flags is list", isinstance(anomalies.flags, list))

    return runner.summary()


def main():
    """Run all tests"""
    print("\n" + "#" * 80)
    print("# RiskRulesDB - COMPREHENSIVE TEST SUITE")
    print("#" * 80)

    results = [
        ("DTI Calculations", test_dti_calculations()),
        ("Credit Score Assessment", test_credit_score_assessment()),
        ("Loan Amount Assessment", test_loan_amount_assessment()),
        ("Anomaly Detection", test_anomaly_detection()),
        ("Business Rules Thresholds", test_business_rules_thresholds()),
        ("Edge Cases", test_edge_cases()),
        ("Data Types & Precision", test_data_types_and_precision()),
    ]

    print("\n" + "#" * 80)
    print("# TEST SUMMARY")
    print("#" * 80)
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "#" * 80)
    if all_passed:
        print("# ALL TESTS PASSED!")
        print("#" * 80)
        return 0
    else:
        print("# SOME TESTS FAILED!")
        print("#" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
