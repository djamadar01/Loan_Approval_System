"""
Comprehensive test suite for ApplicantProfileAgent.

Tests cover:
- Profile fetching and parsing
- Data validation and error handling
- Risk calculations and scoring
- Recommendation generation
- Portfolio analysis
- Edge cases and error scenarios
"""

import pytest
from applicant_profile_agent import (
    ApplicantProfileAgent,
    ValidationError,
    AgentError,
    IncomeStabilityAssessment,
    EmploymentRiskAssessment,
    CreditHistorySummary,
    ApplicantProfileSummary,
    calculate_credit_rating,
    calculate_income_risk_indicator,
    calculate_overall_risk_score,
    generate_employment_risk_rationale,
    generate_overall_recommendation
)


# ============================================================================
# Test Data Models
# ============================================================================


class TestIncomeStabilityAssessment:
    """Test IncomeStabilityAssessment data class."""

    def test_valid_income_stability(self):
        """Test creation of valid income stability assessment."""
        assessment = IncomeStabilityAssessment(
            score=85,
            trend="increasing",
            volatility="low",
            average_monthly=5250.00,
            risk_indicator="healthy"
        )
        assessment.validate()
        assert assessment.score == 85
        assert assessment.trend == "increasing"

    def test_invalid_score_too_high(self):
        """Test validation rejects score > 100."""
        assessment = IncomeStabilityAssessment(
            score=105,
            trend="increasing",
            volatility="low",
            average_monthly=5250.00,
            risk_indicator="healthy"
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_invalid_score_negative(self):
        """Test validation rejects negative score."""
        assessment = IncomeStabilityAssessment(
            score=-10,
            trend="increasing",
            volatility="low",
            average_monthly=5250.00,
            risk_indicator="healthy"
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_invalid_trend(self):
        """Test validation rejects invalid trend."""
        assessment = IncomeStabilityAssessment(
            score=85,
            trend="unknown",
            volatility="low",
            average_monthly=5250.00,
            risk_indicator="healthy"
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_invalid_volatility(self):
        """Test validation rejects invalid volatility."""
        assessment = IncomeStabilityAssessment(
            score=85,
            trend="increasing",
            volatility="extreme",
            average_monthly=5250.00,
            risk_indicator="healthy"
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_negative_income(self):
        """Test validation rejects negative average monthly income."""
        assessment = IncomeStabilityAssessment(
            score=85,
            trend="increasing",
            volatility="low",
            average_monthly=-1000.00,
            risk_indicator="healthy"
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        assessment = IncomeStabilityAssessment(
            score=85,
            trend="increasing",
            volatility="low",
            average_monthly=5250.00,
            risk_indicator="healthy"
        )
        result = assessment.to_dict()
        assert isinstance(result, dict)
        assert result["score"] == 85
        assert result["trend"] == "increasing"


class TestEmploymentRiskAssessment:
    """Test EmploymentRiskAssessment data class."""

    def test_valid_employment_risk(self):
        """Test creation of valid employment risk assessment."""
        assessment = EmploymentRiskAssessment(
            risk_level="low",
            rationale="Strong income stability; good credit history"
        )
        assessment.validate()
        assert assessment.risk_level == "low"

    def test_invalid_risk_level(self):
        """Test validation rejects invalid risk level."""
        assessment = EmploymentRiskAssessment(
            risk_level="critical",
            rationale="Some rationale"
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_empty_rationale(self):
        """Test validation rejects empty rationale."""
        assessment = EmploymentRiskAssessment(
            risk_level="low",
            rationale=""
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        assessment = EmploymentRiskAssessment(
            risk_level="medium",
            rationale="Moderate income with some concerns"
        )
        result = assessment.to_dict()
        assert result["risk_level"] == "medium"


class TestCreditHistorySummary:
    """Test CreditHistorySummary data class."""

    def test_valid_credit_history(self):
        """Test creation of valid credit history summary."""
        summary = CreditHistorySummary(
            credit_score=750,
            accounts_on_time=8,
            accounts_late=0,
            total_debt=15000.00,
            debt_to_income_ratio=28.6,
            delinquencies=0,
            credit_rating="excellent"
        )
        summary.validate()
        assert summary.credit_score == 750

    def test_invalid_credit_score_too_low(self):
        """Test validation rejects credit score < 300."""
        summary = CreditHistorySummary(
            credit_score=250,
            accounts_on_time=8,
            accounts_late=0,
            total_debt=15000.00,
            debt_to_income_ratio=28.6,
            delinquencies=0,
            credit_rating="excellent"
        )
        with pytest.raises(ValidationError):
            summary.validate()

    def test_invalid_credit_score_too_high(self):
        """Test validation rejects credit score > 850."""
        summary = CreditHistorySummary(
            credit_score=900,
            accounts_on_time=8,
            accounts_late=0,
            total_debt=15000.00,
            debt_to_income_ratio=28.6,
            delinquencies=0,
            credit_rating="excellent"
        )
        with pytest.raises(ValidationError):
            summary.validate()

    def test_negative_account_counts(self):
        """Test validation rejects negative account counts."""
        summary = CreditHistorySummary(
            credit_score=750,
            accounts_on_time=-1,
            accounts_late=0,
            total_debt=15000.00,
            debt_to_income_ratio=28.6,
            delinquencies=0,
            credit_rating="excellent"
        )
        with pytest.raises(ValidationError):
            summary.validate()

    def test_negative_debt(self):
        """Test validation rejects negative total debt."""
        summary = CreditHistorySummary(
            credit_score=750,
            accounts_on_time=8,
            accounts_late=0,
            total_debt=-1000.00,
            debt_to_income_ratio=28.6,
            delinquencies=0,
            credit_rating="excellent"
        )
        with pytest.raises(ValidationError):
            summary.validate()

    def test_negative_dti(self):
        """Test validation rejects negative DTI ratio."""
        summary = CreditHistorySummary(
            credit_score=750,
            accounts_on_time=8,
            accounts_late=0,
            total_debt=15000.00,
            debt_to_income_ratio=-5.0,
            delinquencies=0,
            credit_rating="excellent"
        )
        with pytest.raises(ValidationError):
            summary.validate()

    def test_negative_delinquencies(self):
        """Test validation rejects negative delinquencies."""
        summary = CreditHistorySummary(
            credit_score=750,
            accounts_on_time=8,
            accounts_late=0,
            total_debt=15000.00,
            debt_to_income_ratio=28.6,
            delinquencies=-1,
            credit_rating="excellent"
        )
        with pytest.raises(ValidationError):
            summary.validate()


# ============================================================================
# Test Calculation Functions
# ============================================================================


class TestCreditRatingCalculation:
    """Test credit rating calculation from FICO score."""

    def test_excellent_rating(self):
        """Test excellent credit rating for scores >= 750."""
        assert calculate_credit_rating(800) == "excellent"
        assert calculate_credit_rating(750) == "excellent"

    def test_good_rating(self):
        """Test good credit rating for scores 700-749."""
        assert calculate_credit_rating(725) == "good"
        assert calculate_credit_rating(700) == "good"

    def test_fair_rating(self):
        """Test fair credit rating for scores 650-699."""
        assert calculate_credit_rating(675) == "fair"
        assert calculate_credit_rating(650) == "fair"

    def test_poor_rating(self):
        """Test poor credit rating for scores < 650."""
        assert calculate_credit_rating(600) == "poor"
        assert calculate_credit_rating(300) == "poor"

    def test_boundary_values(self):
        """Test boundary values for credit ratings."""
        assert calculate_credit_rating(849) == "excellent"
        assert calculate_credit_rating(749) == "good"
        assert calculate_credit_rating(699) == "fair"
        assert calculate_credit_rating(649) == "poor"


class TestIncomeRiskIndicator:
    """Test income risk indicator calculation."""

    def test_healthy_indicator(self):
        """Test healthy indicator for strong income."""
        assert calculate_income_risk_indicator(85, "increasing", "low") == "healthy"
        assert calculate_income_risk_indicator(90, "stable", "low") == "healthy"

    def test_caution_indicator(self):
        """Test caution indicator for moderate income."""
        assert calculate_income_risk_indicator(60, "stable", "moderate") == "caution"
        assert calculate_income_risk_indicator(75, "decreasing", "low") == "caution"

    def test_critical_indicator(self):
        """Test critical indicator for weak income."""
        assert calculate_income_risk_indicator(30, "decreasing", "high") == "critical"
        assert calculate_income_risk_indicator(40, "stable", "high") == "critical"


class TestOverallRiskScore:
    """Test overall risk score calculation."""

    def test_low_risk_applicant(self):
        """Test score calculation for low-risk applicant."""
        score = calculate_overall_risk_score(
            income_score=85,
            credit_score=750,
            dti_ratio=28.6,
            delinquencies=0,
            risk_level="low"
        )
        assert 70 <= score <= 100

    def test_medium_risk_applicant(self):
        """Test score calculation for medium-risk applicant."""
        score = calculate_overall_risk_score(
            income_score=62,
            credit_score=680,
            dti_ratio=73.7,
            delinquencies=1,
            risk_level="medium"
        )
        assert 0 <= score <= 100

    def test_high_risk_applicant(self):
        """Test score calculation for high-risk applicant."""
        score = calculate_overall_risk_score(
            income_score=45,
            credit_score=580,
            dti_ratio=144.8,
            delinquencies=3,
            risk_level="high"
        )
        assert 0 <= score <= 100

    def test_score_bounds(self):
        """Test that score is always between 0 and 100."""
        # Test extreme cases
        score_low = calculate_overall_risk_score(0, 300, 200, 10, "high")
        score_high = calculate_overall_risk_score(100, 850, 0, 0, "low")

        assert 0 <= score_low <= 100
        assert 0 <= score_high <= 100


class TestEmploymentRiskRationale:
    """Test employment risk rationale generation."""

    def test_strong_income_rationale(self):
        """Test rationale for strong income."""
        rationale = generate_employment_risk_rationale(85, "increasing", 28.6, 0, "low")
        assert "Strong income stability" in rationale
        assert "improving" in rationale
        assert "No recent delinquencies" in rationale

    def test_weak_income_rationale(self):
        """Test rationale for weak income."""
        rationale = generate_employment_risk_rationale(30, "decreasing", 144.8, 3, "high")
        assert "Low income stability" in rationale
        assert "declining" in rationale
        assert "High DTI" in rationale
        assert "3 recent delinquencies" in rationale

    def test_moderate_income_rationale(self):
        """Test rationale for moderate income."""
        rationale = generate_employment_risk_rationale(60, "stable", 50.0, 1, "medium")
        assert "Moderate income stability" in rationale
        assert "Moderate DTI" in rationale or "Moderate DTI" in rationale


class TestOverallRecommendation:
    """Test overall recommendation generation."""

    def test_incomplete_application_recommendation(self):
        """Test recommendation for incomplete applications."""
        rec = generate_overall_recommendation(50, 50, ["pay_stubs"], 700, 40)
        assert "REQUEST ADDITIONAL INFORMATION" in rec

    def test_missing_documents_recommendation(self):
        """Test recommendation when documents are pending."""
        rec = generate_overall_recommendation(60, 85, ["employment_verification_letter"], 720, 40)
        assert "CONDITIONAL APPROVAL" in rec
        assert "employment_verification_letter" in rec

    def test_low_credit_score_recommendation(self):
        """Test recommendation for low credit score."""
        rec = generate_overall_recommendation(40, 90, [], 580, 40)
        assert "REVIEW REQUIRED" in rec

    def test_high_dti_recommendation(self):
        """Test recommendation for high DTI."""
        rec = generate_overall_recommendation(50, 90, [], 700, 60)
        assert "REVIEW REQUIRED" in rec

    def test_strong_profile_recommendation(self):
        """Test recommendation for strong profile."""
        rec = generate_overall_recommendation(80, 100, [], 750, 30)
        assert "APPROVE" in rec

    def test_conditional_approval_recommendation(self):
        """Test recommendation for conditional approval."""
        rec = generate_overall_recommendation(65, 100, [], 700, 45)
        assert "CONDITIONAL APPROVAL" in rec or "APPROVE" in rec


# ============================================================================
# Test ApplicantProfileAgent
# ============================================================================


class TestApplicantProfileAgent:
    """Test ApplicantProfileAgent main functionality."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return ApplicantProfileAgent(verbose=False)

    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = ApplicantProfileAgent(verbose=True)
        assert agent.verbose is True

    def test_fetch_valid_applicant(self, agent):
        """Test fetching valid applicant profile."""
        profile = agent.fetch_applicant_profile("APP001")
        assert profile.applicant_id == "APP001"
        assert profile.name == "Alice Johnson"
        assert isinstance(profile.income_stability, IncomeStabilityAssessment)
        assert isinstance(profile.employment_risk, EmploymentRiskAssessment)
        assert isinstance(profile.credit_history, CreditHistorySummary)

    def test_fetch_invalid_applicant(self, agent):
        """Test error handling for invalid applicant ID."""
        with pytest.raises(AgentError):
            agent.fetch_applicant_profile("INVALID")

    def test_profile_validation(self, agent):
        """Test that profile is validated after fetching."""
        profile = agent.fetch_applicant_profile("APP002")
        # Profile should pass validation or would have raised AgentError
        assert profile.overall_risk_score >= 0
        assert profile.overall_risk_score <= 100

    def test_fetch_all_applicants(self, agent):
        """Test fetching all applicants."""
        applicants = agent.fetch_all_applicants()
        assert len(applicants) > 0
        assert all("applicant_id" in app for app in applicants)
        assert all("name" in app for app in applicants)

    def test_fetch_applicants_by_risk_low(self, agent):
        """Test fetching low-risk applicants."""
        applicants = agent.fetch_applicants_by_risk("low")
        assert len(applicants) > 0
        assert all(app["employment_risk"] == "low" for app in applicants)

    def test_fetch_applicants_by_risk_medium(self, agent):
        """Test fetching medium-risk applicants."""
        applicants = agent.fetch_applicants_by_risk("medium")
        assert all(app["employment_risk"] == "medium" for app in applicants)

    def test_fetch_applicants_by_risk_high(self, agent):
        """Test fetching high-risk applicants."""
        applicants = agent.fetch_applicants_by_risk("high")
        assert all(app["employment_risk"] == "high" for app in applicants)

    def test_fetch_invalid_risk_level(self, agent):
        """Test error handling for invalid risk level."""
        with pytest.raises(AgentError):
            agent.fetch_applicants_by_risk("invalid")

    def test_fetch_applications_requiring_action(self, agent):
        """Test fetching applications requiring action."""
        result = agent.fetch_applications_requiring_action()
        assert "incomplete_count" in result
        assert "missing_docs_count" in result
        assert "applications" in result

    def test_analyze_risk_portfolio(self, agent):
        """Test portfolio analysis."""
        portfolio = agent.analyze_risk_portfolio()
        assert "low" in portfolio
        assert "medium" in portfolio
        assert "high" in portfolio
        assert "total" in portfolio
        assert "distribution" in portfolio
        assert portfolio["total"] > 0

    def test_portfolio_distribution_percentages(self, agent):
        """Test that portfolio distribution percentages are valid."""
        portfolio = agent.analyze_risk_portfolio()
        total_percentage = sum(portfolio["distribution"].values())
        assert abs(total_percentage - 100.0) < 0.1  # Allow small rounding error


# ============================================================================
# Test Profile Summary Output
# ============================================================================


class TestApplicantProfileSummary:
    """Test ApplicantProfileSummary output formatting."""

    def test_profile_summary_validation(self):
        """Test profile summary validation."""
        summary = ApplicantProfileSummary(
            applicant_id="APP001",
            name="Alice Johnson",
            email="alice@example.com",
            phone="555-0101",
            income_stability=IncomeStabilityAssessment(
                score=85, trend="increasing", volatility="low",
                average_monthly=5250, risk_indicator="healthy"
            ),
            employment_risk=EmploymentRiskAssessment(
                risk_level="low", rationale="Strong profile"
            ),
            credit_history=CreditHistorySummary(
                credit_score=750, accounts_on_time=8, accounts_late=0,
                total_debt=15000, debt_to_income_ratio=28.6,
                delinquencies=0, credit_rating="excellent"
            ),
            application_status="approved",
            application_date="2026-06-01",
            completion_percentage=100,
            missing_fields=[],
            overall_risk_score=85,
            recommendation="APPROVE"
        )
        summary.validate()

    def test_profile_summary_to_dict(self):
        """Test profile summary conversion to dictionary."""
        summary = ApplicantProfileSummary(
            applicant_id="APP001",
            name="Alice Johnson",
            email="alice@example.com",
            phone="555-0101",
            income_stability=IncomeStabilityAssessment(
                score=85, trend="increasing", volatility="low",
                average_monthly=5250, risk_indicator="healthy"
            ),
            employment_risk=EmploymentRiskAssessment(
                risk_level="low", rationale="Strong profile"
            ),
            credit_history=CreditHistorySummary(
                credit_score=750, accounts_on_time=8, accounts_late=0,
                total_debt=15000, debt_to_income_ratio=28.6,
                delinquencies=0, credit_rating="excellent"
            ),
            application_status="approved",
            application_date="2026-06-01",
            completion_percentage=100,
            missing_fields=[],
            overall_risk_score=85,
            recommendation="APPROVE"
        )
        result = summary.to_dict()
        assert isinstance(result, dict)
        assert result["applicant_id"] == "APP001"
        assert result["name"] == "Alice Johnson"

    def test_profile_summary_to_json(self):
        """Test profile summary conversion to JSON."""
        summary = ApplicantProfileSummary(
            applicant_id="APP001",
            name="Alice Johnson",
            email="alice@example.com",
            phone="555-0101",
            income_stability=IncomeStabilityAssessment(
                score=85, trend="increasing", volatility="low",
                average_monthly=5250, risk_indicator="healthy"
            ),
            employment_risk=EmploymentRiskAssessment(
                risk_level="low", rationale="Strong profile"
            ),
            credit_history=CreditHistorySummary(
                credit_score=750, accounts_on_time=8, accounts_late=0,
                total_debt=15000, debt_to_income_ratio=28.6,
                delinquencies=0, credit_rating="excellent"
            ),
            application_status="approved",
            application_date="2026-06-01",
            completion_percentage=100,
            missing_fields=[],
            overall_risk_score=85,
            recommendation="APPROVE"
        )
        json_output = summary.to_json()
        assert isinstance(json_output, str)
        assert "APP001" in json_output
        assert "Alice Johnson" in json_output


# ============================================================================
# Test Error Handling and Edge Cases
# ============================================================================


class TestErrorHandling:
    """Test comprehensive error handling."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return ApplicantProfileAgent(verbose=False)

    def test_agent_error_on_invalid_applicant(self, agent):
        """Test AgentError is raised for invalid applicant."""
        with pytest.raises(AgentError):
            agent.fetch_applicant_profile("NONEXISTENT")

    def test_validation_error_is_wrapped(self, agent):
        """Test that validation errors are wrapped as AgentError."""
        with pytest.raises(AgentError):
            agent.fetch_applicant_profile("INVALID")

    def test_all_applicants_handles_empty_result(self, agent):
        """Test handling of applicant list."""
        applicants = agent.fetch_all_applicants()
        # Should return list (possibly empty), not raise
        assert isinstance(applicants, list)

    def test_risk_filter_with_all_levels(self, agent):
        """Test risk filtering works for all valid levels."""
        for risk_level in ["low", "medium", "high"]:
            try:
                result = agent.fetch_applicants_by_risk(risk_level)
                assert isinstance(result, list)
            except AgentError:
                pytest.fail(f"Failed for risk level: {risk_level}")


# ============================================================================
# Test Integration Scenarios
# ============================================================================


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return ApplicantProfileAgent(verbose=False)

    def test_analyze_specific_applicant_workflow(self, agent):
        """Test workflow for analyzing a specific applicant."""
        # Fetch profile
        profile = agent.fetch_applicant_profile("APP001")

        # Verify all components are present
        assert profile.applicant_id == "APP001"
        assert profile.income_stability.score >= 0
        assert profile.employment_risk.risk_level in ["low", "medium", "high"]
        assert profile.credit_history.credit_score >= 300
        assert profile.overall_risk_score >= 0

    def test_portfolio_review_workflow(self, agent):
        """Test workflow for portfolio review."""
        # Get all applicants
        all_apps = agent.fetch_all_applicants()
        assert len(all_apps) > 0

        # Analyze risk distribution
        portfolio = agent.analyze_risk_portfolio()
        total = portfolio["total"]
        assert total == len(all_apps)

        # Verify percentages sum to ~100
        distribution_sum = sum(portfolio["distribution"].values())
        assert abs(distribution_sum - 100.0) < 1.0

    def test_pending_actions_workflow(self, agent):
        """Test workflow for identifying pending actions."""
        result = agent.fetch_applications_requiring_action()

        # Should have incomplete applications
        assert result["incomplete_count"] > 0

        # Each application should have metadata
        for app in result["applications"]:
            assert "applicant_id" in app
            assert "name" in app
            assert "missing_fields" in app

    def test_cross_risk_analysis_workflow(self, agent):
        """Test workflow for cross-risk analysis."""
        results = {}
        for risk_level in ["low", "medium", "high"]:
            results[risk_level] = agent.fetch_applicants_by_risk(risk_level)

        # Should have data for at least one risk level
        total_apps = sum(len(apps) for apps in results.values())
        assert total_apps > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
