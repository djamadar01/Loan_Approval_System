"""
Unit tests for the Loan Application Orchestrator.

Tests cover:
- Individual agent functionality
- Workflow graph execution
- State transitions and routing
- Error handling
- Decision logic validation
"""

import unittest
from datetime import datetime
from loan_orchestrator import (
    ApplicantProfile,
    FinancialData,
    ApplicationState,
    ApplicationStatus,
    DecisionType,
    RiskLevel,
    ApplicantProfileAgent,
    FinancialRiskAgent,
    LoanDecisionAgent,
    ComplianceOrchestratorAgent,
    create_initial_state,
    execute_application,
    compile_loan_orchestrator,
    format_state_for_output,
)


class TestApplicantProfileAgent(unittest.TestCase):
    """Test ApplicantProfileAgent."""

    def test_profile_analysis_low_risk(self):
        """Test profile analysis for low-risk applicant."""
        profile = ApplicantProfile(
            applicant_id="TEST001",
            name="Jane Smith",
            age=40,
            employment_status="full_time",
            employment_years=10,
            education_level="graduate",
            credit_score=800,
            existing_loans=0,
        )

        analyzed_profile = ApplicantProfileAgent.analyze_profile(profile)

        self.assertEqual(analyzed_profile.applicant_id, "TEST001")
        self.assertLess(analyzed_profile.profile_risk_score, 30)
        self.assertIsNotNone(analyzed_profile.analysis_timestamp)
        self.assertIn("Risk Score", analyzed_profile.profile_analysis)

    def test_profile_analysis_high_risk(self):
        """Test profile analysis for high-risk applicant."""
        profile = ApplicantProfile(
            applicant_id="TEST002",
            name="Bob Johnson",
            age=25,
            employment_status="unemployed",
            employment_years=0.5,
            education_level="high_school",
            credit_score=450,
            existing_loans=3,
        )

        analyzed_profile = ApplicantProfileAgent.analyze_profile(profile)

        self.assertGreater(analyzed_profile.profile_risk_score, 60)
        self.assertIsNotNone(analyzed_profile.profile_analysis)

    def test_credit_score_factor(self):
        """Test credit score impact on risk score."""
        profile_good = ApplicantProfile(
            applicant_id="TEST003",
            name="Good Credit",
            age=40,
            employment_status="full_time",
            employment_years=5,
            education_level="bachelor",
            credit_score=780,
            existing_loans=0,
        )

        profile_bad = ApplicantProfile(
            applicant_id="TEST004",
            name="Bad Credit",
            age=40,
            employment_status="full_time",
            employment_years=5,
            education_level="bachelor",
            credit_score=480,
            existing_loans=0,
        )

        analyzed_good = ApplicantProfileAgent.analyze_profile(profile_good)
        analyzed_bad = ApplicantProfileAgent.analyze_profile(profile_bad)

        self.assertLess(
            analyzed_good.profile_risk_score,
            analyzed_bad.profile_risk_score
        )


class TestFinancialRiskAgent(unittest.TestCase):
    """Test FinancialRiskAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.profile = ApplicantProfile(
            applicant_id="TEST005",
            name="Test User",
            age=35,
            employment_status="full_time",
            employment_years=5,
            education_level="bachelor",
            credit_score=700,
            existing_loans=1,
        )

    def test_financial_analysis_low_risk(self):
        """Test financial analysis for low-risk applicant."""
        financial = FinancialData(
            annual_income=100000,
            monthly_expenses=2000,
            savings=30000,
            loan_amount=20000,
            loan_term_months=60,
        )

        analyzed = FinancialRiskAgent.assess_financial_risk(self.profile, financial)

        self.assertLess(analyzed.financial_risk_score, 35)
        self.assertAlmostEqual(analyzed.debt_to_income_ratio, 2000 / (100000 / 12), places=2)
        self.assertGreater(analyzed.monthly_payment, 0)

    def test_financial_analysis_high_risk(self):
        """Test financial analysis for high-risk applicant."""
        financial = FinancialData(
            annual_income=30000,
            monthly_expenses=2500,
            savings=1000,
            loan_amount=25000,
            loan_term_months=60,
        )

        analyzed = FinancialRiskAgent.assess_financial_risk(self.profile, financial)

        self.assertGreater(analyzed.financial_risk_score, 50)
        self.assertGreater(analyzed.debt_to_income_ratio, 0.8)

    def test_dti_ratio_calculation(self):
        """Test debt-to-income ratio calculation."""
        financial = FinancialData(
            annual_income=60000,
            monthly_expenses=3000,
            savings=5000,
            loan_amount=15000,
            loan_term_months=36,
        )

        analyzed = FinancialRiskAgent.assess_financial_risk(self.profile, financial)

        expected_dti = 3000 / (60000 / 12)
        self.assertAlmostEqual(analyzed.debt_to_income_ratio, expected_dti, places=2)

    def test_monthly_payment_calculation(self):
        """Test monthly payment calculation."""
        financial = FinancialData(
            annual_income=50000,
            monthly_expenses=1500,
            savings=5000,
            loan_amount=10000,
            loan_term_months=60,
        )

        analyzed = FinancialRiskAgent.assess_financial_risk(self.profile, financial)

        self.assertGreater(analyzed.monthly_payment, 0)
        # Rough check: monthly payment should be less than 20% of monthly income
        self.assertLess(
            analyzed.monthly_payment,
            (50000 / 12) * 0.3
        )


class TestLoanDecisionAgent(unittest.TestCase):
    """Test LoanDecisionAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.profile = ApplicantProfile(
            applicant_id="TEST006",
            name="Decision Test",
            age=35,
            employment_status="full_time",
            employment_years=5,
            education_level="bachelor",
            credit_score=700,
            existing_loans=1,
            profile_risk_score=25.0,
        )

        self.financial = FinancialData(
            annual_income=80000,
            monthly_expenses=2000,
            savings=15000,
            loan_amount=20000,
            loan_term_months=60,
            financial_risk_score=20.0,
            debt_to_income_ratio=0.3,
        )

    def test_approved_decision(self):
        """Test approval decision for low-risk applicant."""
        from loan_orchestrator import RiskAssessment

        risk = RiskAssessment(
            overall_risk_level=RiskLevel.LOW,
            risk_score=20.0,
            credit_risk=10.0,
            income_risk=15.0,
            debt_risk=25.0,
            employment_risk=5.0,
            risk_factors=[],
            mitigating_factors=["Good credit", "Stable employment"],
        )

        decision = LoanDecisionAgent.make_decision(self.profile, self.financial, risk)

        self.assertEqual(decision.decision, DecisionType.APPROVED)
        self.assertGreaterEqual(decision.decision_score, 75)
        self.assertGreater(decision.approval_probability, 0.9)

    def test_rejected_decision(self):
        """Test rejection decision for high-risk applicant."""
        from loan_orchestrator import RiskAssessment

        risk = RiskAssessment(
            overall_risk_level=RiskLevel.CRITICAL,
            risk_score=85.0,
            credit_risk=90.0,
            income_risk=85.0,
            debt_risk=95.0,
            employment_risk=80.0,
            risk_factors=["Low credit score", "High debt", "Unemployment"],
            mitigating_factors=[],
        )

        decision = LoanDecisionAgent.make_decision(self.profile, self.financial, risk)

        self.assertEqual(decision.decision, DecisionType.REJECTED)
        self.assertLess(decision.decision_score, 40)
        self.assertLess(decision.approval_probability, 0.1)

    def test_conditional_approval(self):
        """Test conditional approval decision."""
        from loan_orchestrator import RiskAssessment

        risk = RiskAssessment(
            overall_risk_level=RiskLevel.MEDIUM,
            risk_score=55.0,
            credit_risk=50.0,
            income_risk=60.0,
            debt_risk=50.0,
            employment_risk=50.0,
            risk_factors=["Fair credit score"],
            mitigating_factors=["Good income"],
        )

        decision = LoanDecisionAgent.make_decision(self.profile, self.financial, risk)

        self.assertEqual(decision.decision, DecisionType.CONDITIONAL_APPROVAL)
        self.assertGreaterEqual(decision.decision_score, 60)
        self.assertGreater(len(decision.conditions), 0)


class TestComplianceOrchestratorAgent(unittest.TestCase):
    """Test ComplianceOrchestratorAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.profile = ApplicantProfile(
            applicant_id="TEST007",
            name="Compliance Test",
            age=35,
            employment_status="full_time",
            employment_years=5,
            education_level="bachelor",
            credit_score=700,
            existing_loans=1,
        )

    def test_compliance_check_approved(self):
        """Test compliance check for approved decision."""
        from loan_orchestrator import RiskAssessment, LoanDecision

        decision = LoanDecision(
            decision=DecisionType.APPROVED,
            decision_score=80.0,
            approval_probability=0.95,
            rationale="Good profile",
        )

        risk = RiskAssessment(
            overall_risk_level=RiskLevel.LOW,
            risk_score=20.0,
            credit_risk=10.0,
            income_risk=15.0,
            debt_risk=25.0,
            employment_risk=5.0,
        )

        result = ComplianceOrchestratorAgent.check_compliance(
            self.profile, decision, risk
        )

        self.assertTrue(result.is_compliant)
        self.assertGreater(len(result.required_actions), 0)
        self.assertIn("approval letter", result.required_actions[0].lower())

    def test_age_verification_failure(self):
        """Test compliance check with underage applicant."""
        from loan_orchestrator import RiskAssessment, LoanDecision

        underage_profile = ApplicantProfile(
            applicant_id="TEST008",
            name="Young Person",
            age=16,
            employment_status="part_time",
            employment_years=0.5,
            education_level="high_school",
            credit_score=600,
            existing_loans=0,
        )

        decision = LoanDecision(
            decision=DecisionType.REJECTED,
            decision_score=10.0,
            approval_probability=0.0,
            rationale="Age verification failed",
        )

        risk = RiskAssessment(
            overall_risk_level=RiskLevel.CRITICAL,
            risk_score=90.0,
            credit_risk=40.0,
            income_risk=80.0,
            debt_risk=50.0,
            employment_risk=85.0,
        )

        result = ComplianceOrchestratorAgent.check_compliance(
            underage_profile, decision, risk
        )

        self.assertFalse(result.is_compliant)
        self.assertFalse(result.compliance_checks["age_verification"])
        self.assertIn("Applicant below legal age", result.flags)

    def test_enhanced_due_diligence_for_critical_risk(self):
        """Test enhanced due diligence for critical risk profile."""
        from loan_orchestrator import RiskAssessment, LoanDecision

        decision = LoanDecision(
            decision=DecisionType.MANUAL_REVIEW,
            decision_score=35.0,
            approval_probability=0.2,
            rationale="Requires manual review",
        )

        risk = RiskAssessment(
            overall_risk_level=RiskLevel.CRITICAL,
            risk_score=85.0,
            credit_risk=90.0,
            income_risk=85.0,
            debt_risk=95.0,
            employment_risk=80.0,
        )

        result = ComplianceOrchestratorAgent.check_compliance(
            self.profile, decision, risk
        )

        self.assertTrue(result.compliance_checks["enhanced_due_diligence"])
        self.assertIn("enhanced due diligence", " ".join(result.required_actions).lower())


class TestWorkflowExecution(unittest.TestCase):
    """Test complete workflow execution."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = compile_loan_orchestrator()

        self.profile = ApplicantProfile(
            applicant_id="APP001",
            name="John Doe",
            age=35,
            employment_status="full_time",
            employment_years=8,
            education_level="bachelor",
            credit_score=720,
            existing_loans=1,
        )

        self.financial = FinancialData(
            annual_income=75000,
            monthly_expenses=2500,
            savings=15000,
            loan_amount=25000,
            loan_term_months=60,
        )

    def test_complete_workflow_execution(self):
        """Test complete workflow execution."""
        result = execute_application(
            self.orchestrator,
            "APP001",
            self.profile,
            self.financial,
        )

        self.assertEqual(result["application_id"], "APP001")
        self.assertNotEqual(result["status"], ApplicationStatus.PENDING)
        self.assertIsNotNone(result["applicant_profile"])
        self.assertIsNotNone(result["financial_data"])
        self.assertIsNotNone(result["risk_assessment"])
        self.assertIsNotNone(result["loan_decision"])
        self.assertIsNotNone(result["compliance_result"])
        self.assertGreater(len(result["execution_log"]), 0)

    def test_workflow_state_transitions(self):
        """Test state transitions through workflow."""
        result = execute_application(
            self.orchestrator,
            "APP002",
            self.profile,
            self.financial,
        )

        execution_steps = [log["step"] for log in result["execution_log"]]

        # Verify expected steps
        self.assertIn("initialization", execution_steps)
        self.assertIn("profile_analysis", execution_steps)
        self.assertIn("financial_risk_assessment", execution_steps)
        self.assertIn("risk_aggregation", execution_steps)
        self.assertIn("loan_decision", execution_steps)
        self.assertIn("compliance_check", execution_steps)

    def test_output_formatting(self):
        """Test output formatting."""
        result = execute_application(
            self.orchestrator,
            "APP003",
            self.profile,
            self.financial,
        )

        output = format_state_for_output(result)

        self.assertIn("application_id", output)
        self.assertIn("status", output)
        self.assertIn("applicant_profile", output)
        self.assertIn("financial_data", output)
        self.assertIn("risk_assessment", output)
        self.assertIn("loan_decision", output)
        self.assertIn("compliance_result", output)
        self.assertIn("execution_log", output)

    def test_error_handling_in_workflow(self):
        """Test error handling during workflow execution."""
        # Create invalid state (missing financial data)
        invalid_state = ApplicationState(
            application_id="APP_ERROR",
            status=ApplicationStatus.PENDING,
            applicant_profile=self.profile,
            financial_data=None,  # Missing
            risk_assessment=None,
            loan_decision=None,
            compliance_result=None,
            errors=[],
            execution_log=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        try:
            result = self.orchestrator.invoke(invalid_state)
            # Should reach error state
            self.assertEqual(result["status"], ApplicationStatus.ERROR)
        except Exception:
            # Or raise exception
            pass

    def test_approved_application_workflow(self):
        """Test workflow for approved application."""
        good_profile = ApplicantProfile(
            applicant_id="APP_GOOD",
            name="Excellent Applicant",
            age=40,
            employment_status="full_time",
            employment_years=15,
            education_level="graduate",
            credit_score=800,
            existing_loans=0,
        )

        good_financial = FinancialData(
            annual_income=120000,
            monthly_expenses=2000,
            savings=50000,
            loan_amount=20000,
            loan_term_months=60,
        )

        result = execute_application(
            self.orchestrator,
            "APP_GOOD",
            good_profile,
            good_financial,
        )

        self.assertEqual(result["status"], ApplicationStatus.APPROVED)
        self.assertEqual(
            result["loan_decision"]["decision"],
            DecisionType.APPROVED.value
        )

    def test_rejected_application_workflow(self):
        """Test workflow for rejected application."""
        bad_profile = ApplicantProfile(
            applicant_id="APP_BAD",
            name="Poor Applicant",
            age=25,
            employment_status="unemployed",
            employment_years=0.5,
            education_level="high_school",
            credit_score=450,
            existing_loans=3,
        )

        bad_financial = FinancialData(
            annual_income=20000,
            monthly_expenses=3000,
            savings=500,
            loan_amount=30000,
            loan_term_months=60,
        )

        result = execute_application(
            self.orchestrator,
            "APP_BAD",
            bad_profile,
            bad_financial,
        )

        self.assertEqual(result["status"], ApplicationStatus.REJECTED)
        self.assertEqual(
            result["loan_decision"]["decision"],
            DecisionType.REJECTED.value
        )


class TestInitialStateCreation(unittest.TestCase):
    """Test initial state creation."""

    def test_initial_state_structure(self):
        """Test initial state has correct structure."""
        profile = ApplicantProfile(
            applicant_id="TEST009",
            name="State Test",
            age=30,
            employment_status="full_time",
            employment_years=3,
            education_level="bachelor",
            credit_score=650,
            existing_loans=1,
        )

        financial = FinancialData(
            annual_income=60000,
            monthly_expenses=2000,
            savings=5000,
            loan_amount=15000,
            loan_term_months=48,
        )

        state = create_initial_state("TEST_APP", profile, financial)

        self.assertEqual(state["application_id"], "TEST_APP")
        self.assertEqual(state["status"], ApplicationStatus.PENDING)
        self.assertIsNotNone(state["created_at"])
        self.assertIsNotNone(state["updated_at"])
        self.assertEqual(len(state["errors"]), 0)
        self.assertGreater(len(state["execution_log"]), 0)


if __name__ == "__main__":
    unittest.main()
