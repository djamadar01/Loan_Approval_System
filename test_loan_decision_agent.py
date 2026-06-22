"""
Unit tests for LoanDecisionAgent

Tests cover:
- Single decision making
- Batch decision processing
- Decision rule retrieval
- Input validation
- Error handling
- Decision result serialization
"""

import pytest
import asyncio
from loan_decision_agent import (
    LoanDecisionAgent,
    MockMCPToolInterface,
    RiskAssessmentInput,
    DecisionFactors,
    LoanDecisionResult,
    DecisionClassification,
    ValidationError,
    AgentError,
)


# ============================================================================
# Test Data and Fixtures
# ============================================================================


@pytest.fixture
def mcp_interface():
    """Fixture providing mock MCP interface."""
    return MockMCPToolInterface()


@pytest.fixture
def agent(mcp_interface):
    """Fixture providing LoanDecisionAgent instance."""
    return LoanDecisionAgent(mcp_interface=mcp_interface, verbose=False)


# ============================================================================
# Tests for RiskAssessmentInput
# ============================================================================


class TestRiskAssessmentInput:
    """Tests for RiskAssessmentInput data class."""

    def test_valid_risk_assessment(self):
        """Test valid risk assessment initialization."""
        assessment = RiskAssessmentInput(
            financial_risk=25.0,
            operational_risk=20.0,
            compliance_risk=15.0,
            reputational_risk=10.0,
        )
        assessment.validate()  # Should not raise

    def test_risk_assessment_boundary_values(self):
        """Test risk assessment with boundary values."""
        assessment = RiskAssessmentInput(
            financial_risk=0,
            operational_risk=50,
            compliance_risk=100,
            reputational_risk=75,
        )
        assessment.validate()  # Should not raise

    def test_risk_assessment_invalid_range(self):
        """Test risk assessment with out-of-range values."""
        assessment = RiskAssessmentInput(
            financial_risk=150,  # > 100
            operational_risk=20.0,
            compliance_risk=15.0,
            reputational_risk=10.0,
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_risk_assessment_negative_value(self):
        """Test risk assessment with negative value."""
        assessment = RiskAssessmentInput(
            financial_risk=-10,
            operational_risk=20.0,
            compliance_risk=15.0,
            reputational_risk=10.0,
        )
        with pytest.raises(ValidationError):
            assessment.validate()

    def test_risk_assessment_to_dict(self):
        """Test risk assessment conversion to dictionary."""
        assessment = RiskAssessmentInput(
            financial_risk=25.0,
            operational_risk=20.0,
            compliance_risk=15.0,
            reputational_risk=10.0,
        )
        result = assessment.to_dict()
        assert result["financial_risk"] == 25.0
        assert result["operational_risk"] == 20.0


# ============================================================================
# Tests for DecisionFactors
# ============================================================================


class TestDecisionFactors:
    """Tests for DecisionFactors data class."""

    def test_valid_decision_factors(self):
        """Test valid decision factors initialization."""
        factors = DecisionFactors(
            critical_issues=True,
            mitigating_factors=True,
            requires_escalation=False,
            key_factors=["Factor 1", "Factor 2"],
        )
        factors.validate()  # Should not raise

    def test_decision_factors_empty_key_factors(self):
        """Test decision factors with empty key factors list."""
        factors = DecisionFactors(
            critical_issues=False,
            mitigating_factors=False,
            requires_escalation=False,
            key_factors=[],
        )
        factors.validate()  # Should not raise

    def test_decision_factors_invalid_critical_issues_type(self):
        """Test decision factors with invalid critical_issues type."""
        factors = DecisionFactors(
            critical_issues="yes",  # Should be bool
            mitigating_factors=True,
            requires_escalation=False,
            key_factors=["Factor"],
        )
        with pytest.raises(ValidationError):
            factors.validate()

    def test_decision_factors_non_string_key_factors(self):
        """Test decision factors with non-string key factors."""
        factors = DecisionFactors(
            critical_issues=True,
            mitigating_factors=True,
            requires_escalation=False,
            key_factors=["Factor 1", 123],  # 123 is not a string
        )
        with pytest.raises(ValidationError):
            factors.validate()


# ============================================================================
# Tests for Single Decision Making
# ============================================================================


class TestSingleDecision:
    """Tests for single decision making."""

    @pytest.mark.asyncio
    async def test_low_risk_approval(self, agent):
        """Test decision for low-risk applicant results in approval."""
        result = await agent.make_decision(
            applicant_id="TEST_LOW_RISK",
            financial_risk=20,
            operational_risk=15,
            compliance_risk=10,
            reputational_risk=8,
            has_critical_issues=False,
            has_mitigating_factors=True,
        )

        assert result.applicant_id == "TEST_LOW_RISK"
        assert result.classification == DecisionClassification.APPROVE
        assert result.risk_score < 50
        assert result.confidence_level >= 0.85

    @pytest.mark.asyncio
    async def test_high_risk_rejection(self, agent):
        """Test decision for high-risk applicant results in rejection."""
        result = await agent.make_decision(
            applicant_id="TEST_HIGH_RISK",
            financial_risk=90,
            operational_risk=85,
            compliance_risk=92,
            reputational_risk=80,
            has_critical_issues=True,
            has_mitigating_factors=False,
        )

        assert result.applicant_id == "TEST_HIGH_RISK"
        assert result.classification == DecisionClassification.REJECT
        assert result.risk_score >= 85
        assert result.confidence_level >= 0.85

    @pytest.mark.asyncio
    async def test_medium_risk_review(self, agent):
        """Test decision for medium-risk applicant results in review."""
        result = await agent.make_decision(
            applicant_id="TEST_MEDIUM_RISK",
            financial_risk=50,
            operational_risk=55,
            compliance_risk=45,
            reputational_risk=35,
            has_critical_issues=True,
            has_mitigating_factors=True,
            requires_escalation=True,
        )

        assert result.applicant_id == "TEST_MEDIUM_RISK"
        assert result.classification == DecisionClassification.REVIEW
        assert 50 <= result.risk_score < 85

    @pytest.mark.asyncio
    async def test_decision_result_structure(self, agent):
        """Test decision result contains all required fields."""
        result = await agent.make_decision(
            applicant_id="TEST_STRUCTURE",
            financial_risk=30,
            operational_risk=25,
            compliance_risk=20,
            reputational_risk=15,
        )

        # Check all required attributes
        assert result.applicant_id == "TEST_STRUCTURE"
        assert isinstance(result.classification, DecisionClassification)
        assert 0 <= result.risk_score <= 100
        assert 0.0 <= result.confidence_level <= 1.0
        assert isinstance(result.key_decision_factors, list)
        assert isinstance(result.explanation, str)
        assert result.explanation  # Non-empty
        assert result.timestamp  # Has timestamp

    @pytest.mark.asyncio
    async def test_decision_validation_on_failure(self, agent):
        """Test decision validation catches invalid inputs."""
        with pytest.raises(AgentError):
            await agent.make_decision(
                applicant_id="TEST_INVALID",
                financial_risk=150,  # Invalid: > 100
                operational_risk=25,
                compliance_risk=20,
                reputational_risk=15,
            )


# ============================================================================
# Tests for Batch Decision Processing
# ============================================================================


class TestBatchDecisions:
    """Tests for batch decision processing."""

    @pytest.mark.asyncio
    async def test_batch_processing_success(self, agent):
        """Test successful batch processing of multiple applicants."""
        requests = [
            {
                "applicant_id": "BATCH_001",
                "financial_risk": 20,
                "operational_risk": 15,
                "compliance_risk": 10,
                "reputational_risk": 8,
            },
            {
                "applicant_id": "BATCH_002",
                "financial_risk": 50,
                "operational_risk": 55,
                "compliance_risk": 45,
                "reputational_risk": 35,
            },
            {
                "applicant_id": "BATCH_003",
                "financial_risk": 90,
                "operational_risk": 85,
                "compliance_risk": 92,
                "reputational_risk": 80,
            },
        ]

        result = await agent.batch_make_decisions(requests)

        assert result["status"] == "success"
        assert result["total_requests"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert len(result["decisions"]) == 3
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_batch_decision_distribution(self, agent):
        """Test batch processing generates correct decision distribution."""
        requests = [
            {
                "applicant_id": f"APP_{i}",
                "financial_risk": 20,
                "operational_risk": 20,
                "compliance_risk": 20,
                "reputational_risk": 20,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
            }
            for i in range(5)
        ]

        result = await agent.batch_make_decisions(requests)

        summary = result["summary"]
        assert summary["approved"] + summary["rejected"] + summary["review"] == 5

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, agent):
        """Test batch processing handles partial failures gracefully."""
        requests = [
            {
                "applicant_id": "VALID_001",
                "financial_risk": 30,
                "operational_risk": 25,
                "compliance_risk": 20,
                "reputational_risk": 15,
            },
            {
                "applicant_id": "INVALID_001",
                "financial_risk": 150,  # Invalid
                "operational_risk": 25,
                "compliance_risk": 20,
                "reputational_risk": 15,
            },
            {
                "applicant_id": "VALID_002",
                "financial_risk": 40,
                "operational_risk": 35,
                "compliance_risk": 30,
                "reputational_risk": 25,
            },
        ]

        result = await agent.batch_make_decisions(requests)

        # Should be partial success
        assert result["status"] == "partial_success"
        assert result["successful"] == 2
        assert result["failed"] == 1
        assert len(result["decisions"]) == 2
        assert len(result["errors"]) == 1
        assert result["errors"][0]["applicant_id"] == "INVALID_001"

    @pytest.mark.asyncio
    async def test_batch_empty_requests(self, agent):
        """Test batch processing with empty request list."""
        result = await agent.batch_make_decisions([])

        assert result["status"] == "success"
        assert result["total_requests"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0
        assert len(result["decisions"]) == 0

    @pytest.mark.asyncio
    async def test_batch_approval_rate_calculation(self, agent):
        """Test batch processing calculates approval rate correctly."""
        requests = [
            {
                "applicant_id": "LOW_RISK",
                "financial_risk": 10,
                "operational_risk": 10,
                "compliance_risk": 10,
                "reputational_risk": 10,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
            }
            for _ in range(3)
        ] + [
            {
                "applicant_id": "HIGH_RISK",
                "financial_risk": 90,
                "operational_risk": 90,
                "compliance_risk": 90,
                "reputational_risk": 90,
                "has_critical_issues": True,
                "has_mitigating_factors": False,
            }
            for _ in range(2)
        ]

        result = await agent.batch_make_decisions(requests)

        summary = result["summary"]
        # Should have some approvals and rejections
        assert summary["approved"] > 0 or summary["rejected"] > 0


# ============================================================================
# Tests for Decision Rules
# ============================================================================


class TestDecisionRules:
    """Tests for decision rule retrieval."""

    @pytest.mark.asyncio
    async def test_get_decision_rules(self, agent):
        """Test retrieving decision rules from MCP server."""
        rules = await agent.get_decision_rules()

        assert "risk_score_calculation" in rules
        assert "classification_rules" in rules
        assert "thresholds" in rules

    @pytest.mark.asyncio
    async def test_decision_rules_structure(self, agent):
        """Test decision rules have correct structure."""
        rules = await agent.get_decision_rules()

        # Check risk score calculation
        calc_rules = rules["risk_score_calculation"]
        assert "weights" in calc_rules
        assert "financial_risk" in calc_rules["weights"]
        assert "operational_risk" in calc_rules["weights"]
        assert "compliance_risk" in calc_rules["weights"]
        assert "reputational_risk" in calc_rules["weights"]

        # Check classification rules
        class_rules = rules["classification_rules"]
        assert "APPROVE" in class_rules
        assert "REJECT" in class_rules
        assert "REVIEW" in class_rules

        # Check thresholds
        thresholds = rules["thresholds"]
        assert "low_risk" in thresholds
        assert "medium_high_risk" in thresholds
        assert "high_risk" in thresholds

    @pytest.mark.asyncio
    async def test_decision_rules_weights_sum(self, agent):
        """Test decision rule weights sum to 1.0."""
        rules = await agent.get_decision_rules()

        weights = rules["risk_score_calculation"]["weights"]
        total_weight = sum(weights.values())

        assert abs(total_weight - 1.0) < 0.001  # Allow for floating point error


# ============================================================================
# Tests for Result Serialization
# ============================================================================


class TestResultSerialization:
    """Tests for decision result serialization."""

    @pytest.mark.asyncio
    async def test_decision_to_dict(self, agent):
        """Test converting decision to dictionary."""
        result = await agent.make_decision(
            applicant_id="TEST_DICT",
            financial_risk=35,
            operational_risk=30,
            compliance_risk=25,
            reputational_risk=20,
        )

        result_dict = result.to_dict()

        assert result_dict["applicant_id"] == "TEST_DICT"
        assert "classification" in result_dict
        assert "risk_score" in result_dict
        assert "confidence_level" in result_dict
        assert "key_decision_factors" in result_dict
        assert "explanation" in result_dict
        assert "timestamp" in result_dict

    @pytest.mark.asyncio
    async def test_decision_to_json(self, agent):
        """Test converting decision to JSON."""
        result = await agent.make_decision(
            applicant_id="TEST_JSON",
            financial_risk=40,
            operational_risk=35,
            compliance_risk=30,
            reputational_risk=25,
        )

        json_str = result.to_json()

        assert isinstance(json_str, str)
        assert "TEST_JSON" in json_str
        assert "classification" in json_str

        # Test JSON is valid
        import json

        parsed = json.loads(json_str)
        assert parsed["applicant_id"] == "TEST_JSON"

    @pytest.mark.asyncio
    async def test_export_decision_json(self, agent):
        """Test exporting decision as JSON via agent method."""
        result = await agent.make_decision(
            applicant_id="TEST_EXPORT",
            financial_risk=45,
            operational_risk=40,
            compliance_risk=35,
            reputational_risk=30,
        )

        json_str = agent.export_decision_json(result)

        assert isinstance(json_str, str)
        assert "TEST_EXPORT" in json_str

        import json

        parsed = json.loads(json_str)
        assert parsed["applicant_id"] == "TEST_EXPORT"


# ============================================================================
# Tests for Decision Summary
# ============================================================================


class TestDecisionSummary:
    """Tests for decision summary generation."""

    @pytest.mark.asyncio
    async def test_get_decision_summary(self, agent):
        """Test generating decision summary."""
        result = await agent.make_decision(
            applicant_id="TEST_SUMMARY",
            financial_risk=50,
            operational_risk=45,
            compliance_risk=40,
            reputational_risk=35,
        )

        summary = agent.get_decision_summary(result)

        assert "Applicant ID" in summary
        assert "Decision" in summary
        assert "Risk Score" in summary
        assert "Confidence" in summary
        assert "Timestamp" in summary
        assert summary["Applicant ID"] == "TEST_SUMMARY"


# ============================================================================
# Main Test Execution
# ============================================================================


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
