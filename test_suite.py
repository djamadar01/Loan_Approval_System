"""
Test Suite for DecisionSynthesis MCP Server
Comprehensive tests for all decision analysis tools and edge cases.
"""

import unittest
import json
import math
import sys
sys.path.insert(0, '/home/ubuntu/Desktop/demo')

from server import (
    Factor,
    DecisionContext,
    DecisionTreeConfig,
    calculate_approval_score,
    generate_decision_rationale,
    assess_confidence_level,
    format_decision_output,
)


class TestFactorValidation(unittest.TestCase):
    """Test Factor validation and data model."""

    def test_valid_factor_creation(self):
        """Test creating a valid factor."""
        factor = Factor(
            name="Test Factor",
            value=75,
            weight=0.5,
            category="financial",
            description="A test factor"
        )
        self.assertTrue(factor.validate())

    def test_factor_value_bounds(self):
        """Test factor value boundaries."""
        factor_valid = Factor("Test", 0, 0.5, "cat", "")
        self.assertTrue(factor_valid.validate())

        factor_invalid = Factor("Test", -1, 0.5, "cat", "")
        self.assertFalse(factor_invalid.validate())

    def test_factor_weight_bounds(self):
        """Test factor weight boundaries."""
        factor_valid = Factor("Test", 50, 0.001, "cat", "")
        self.assertTrue(factor_valid.validate())

        factor_invalid = Factor("Test", 50, 0, "cat", "")
        self.assertFalse(factor_invalid.validate())


class TestApprovalScoreCalculation(unittest.TestCase):
    """Test approval score calculation."""

    def setUp(self):
        self.factors = [
            {"name": "Factor 1", "value": 80, "weight": 0.4, "category": "financial"},
            {"name": "Factor 2", "value": 60, "weight": 0.3, "category": "risk"},
            {"name": "Factor 3", "value": 90, "weight": 0.3, "category": "operational"}
        ]

    def test_weighted_average_calculation(self):
        """Test weighted average method."""
        result = calculate_approval_score(self.factors, normalization="weighted_average")
        expected_score = 77.0
        self.assertAlmostEqual(result["overall_score"], expected_score, places=1)

    def test_empty_factors_error(self):
        """Test that empty factors list raises error."""
        with self.assertRaises(ValueError):
            calculate_approval_score([])

    def test_category_aggregation(self):
        """Test category-level score aggregation."""
        result = calculate_approval_score(self.factors)
        self.assertIn("category_scores", result)
        self.assertIn("financial", result["category_scores"])


class TestDecisionRationale(unittest.TestCase):
    """Test decision rationale generation."""

    def setUp(self):
        self.factors = [
            {
                "name": "Financial ROI",
                "value": 85,
                "weight": 0.35,
                "category": "financial",
                "evidence": ["Projected 40% cost savings"]
            },
            {
                "name": "Risk Level",
                "value": 45,
                "weight": 0.30,
                "category": "risk",
                "evidence": ["Known challenges"]
            }
        ]
        self.context = {
            "title": "Infrastructure Investment",
            "description": "Capital investment decision"
        }

    def test_rationale_generation(self):
        """Test basic rationale generation."""
        result = generate_decision_rationale(self.context, self.factors, 75.0)
        self.assertIn("factor_explanations", result)
        self.assertIn("category_summary", result)
        self.assertIn("overall_recommendation", result)

    def test_recommendation_logic(self):
        """Test recommendation generation based on score."""
        result = generate_decision_rationale(self.context, self.factors, 80.0)
        self.assertIn("STRONG APPROVAL", result["overall_recommendation"])


class TestConfidenceAssessment(unittest.TestCase):
    """Test Bayesian confidence assessment."""

    def test_confidence_level_determination(self):
        """Test confidence level classification."""
        result = assess_confidence_level(85, 0.05, 0.95)
        self.assertEqual(result["confidence_level"], "very_high")

        result = assess_confidence_level(50, 0.8, 0.3)
        self.assertEqual(result["confidence_level"], "very_low")

    def test_bayesian_posterior(self):
        """Test Bayesian posterior calculation."""
        result = assess_confidence_level(75, 0.2, 0.8, {"prior_probability": 0.5})
        self.assertIn("posterior_probability", result)
        self.assertGreater(result["posterior_probability"], 0.5)

    def test_invalid_score_range(self):
        """Test validation of approval score range."""
        with self.assertRaises(ValueError):
            assess_confidence_level(-10, 0.2, 0.8)


class TestDecisionOutput(unittest.TestCase):
    """Test structured decision output."""

    def setUp(self):
        self.factors = [
            {"name": "Factor 1", "value": 80, "weight": 0.5, "category": "financial"},
            {"name": "Factor 2", "value": 70, "weight": 0.5, "category": "risk"}
        ]

    def test_output_structure(self):
        """Test output has correct structure."""
        result = format_decision_output(
            "TEST-001",
            "Test Decision",
            75.0,
            "high",
            0.78,
            {"recommendation": "Approve"},
            self.factors
        )

        self.assertIn("decision_id", result)
        self.assertIn("outcome", result)
        self.assertIn("recommendations", result)

    def test_outcome_determination(self):
        """Test outcome based on score."""
        result = format_decision_output("ID1", "Title", 75.0, "high", 0.8, {}, self.factors)
        self.assertEqual(result["outcome"], "approved")

        result = format_decision_output("ID2", "Title", 55.0, "medium", 0.6, {}, self.factors)
        self.assertEqual(result["outcome"], "conditional")

    def test_json_serialization(self):
        """Test JSON serialization."""
        result = format_decision_output("ID", "Title", 75.0, "high", 0.8, {}, self.factors)
        json_str = json.dumps(result)
        self.assertIsInstance(json_str, str)


class TestDecisionTreeConfig(unittest.TestCase):
    """Test decision tree configuration."""

    def setUp(self):
        self.config = DecisionTreeConfig()

    def test_minimum_approval_retrieval(self):
        """Test getting minimum approval."""
        min_approval = self.config.get_minimum_approval("financial", "high_impact")
        self.assertEqual(min_approval, 85)

    def test_category_weight_retrieval(self):
        """Test getting category weights."""
        weight = self.config.get_category_weight("financial")
        self.assertEqual(weight, 0.35)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow."""

    def test_complete_workflow(self):
        """Test complete decision analysis workflow."""
        factors = [
            {"name": "ROI", "value": 80, "weight": 0.4, "category": "financial", "evidence": []},
            {"name": "Risk", "value": 65, "weight": 0.35, "category": "risk", "evidence": []},
            {"name": "Operations", "value": 75, "weight": 0.25, "category": "operational", "evidence": []}
        ]

        # Calculate score
        score_result = calculate_approval_score(factors)
        approval_score = score_result["overall_score"]
        self.assertGreater(approval_score, 0)
        self.assertLess(approval_score, 100)

        # Generate rationale
        rationale_result = generate_decision_rationale(
            {"title": "Test", "description": "Testing"},
            factors,
            approval_score
        )
        self.assertIn("factor_explanations", rationale_result)

        # Assess confidence
        confidence_result = assess_confidence_level(approval_score, 0.15, 0.85)
        self.assertIn(confidence_result["confidence_level"],
                     ["very_low", "low", "medium", "high", "very_high"])

        # Format output
        output = format_decision_output(
            "INT-001",
            "Integration Test",
            approval_score,
            confidence_result["confidence_level"],
            confidence_result["confidence_score"],
            rationale_result,
            factors
        )

        self.assertEqual(output["decision_id"], "INT-001")
        self.assertGreater(len(output["recommendations"]), 0)


def run_test_suite():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestFactorValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestApprovalScoreCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionRationale))
    suite.addTests(loader.loadTestsFromTestCase(TestConfidenceAssessment))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionOutput))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionTreeConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
