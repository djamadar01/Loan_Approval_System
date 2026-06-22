"""
Production DecisionSynthesis MCP Server
Provides decision tree configuration, approval scoring, rationale generation,
confidence assessment, and structured output formatting.
"""

import asyncio
import json
import math
from dataclasses import dataclass, asdict, field
from typing import Any, Optional, Dict, List
from enum import Enum

import anthropic

# ============================================================================
# Data Models
# ============================================================================


class DecisionOutcome(str, Enum):
    """Possible decision outcomes."""
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"
    DEFERRED = "deferred"


class ConfidenceLevel(str, Enum):
    """Confidence levels with Bayesian scoring."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Factor:
    """Represents a decision factor with weighted importance."""
    name: str
    value: float  # 0-100 score
    weight: float  # 0-1 importance weight
    category: str  # e.g., "financial", "risk", "operational", "strategic"
    description: str
    evidence: List[str] = field(default_factory=list)

    def validate(self) -> bool:
        """Validate factor values."""
        return (0 <= self.value <= 100 and
                0 <= self.weight <= 1 and
                self.weight > 0 and
                len(self.name) > 0)


@dataclass
class DecisionContext:
    """Context for decision making."""
    decision_id: str
    title: str
    description: str
    factors: List[Factor]
    threshold_approval: float = 70.0  # 0-100
    threshold_rejection: float = 40.0  # 0-100
    require_consensus: bool = False
    time_sensitive: bool = False
    risk_profile: str = "moderate"  # low, moderate, high


@dataclass
class BayesianPrior:
    """Bayesian prior for confidence scoring."""
    prior_probability: float = 0.5  # Initial belief
    evidence_strength: float = 1.0  # Strength multiplier
    uncertainty_factor: float = 0.1  # Epistemic uncertainty


@dataclass
class DecisionOutput:
    """Structured decision output."""
    decision_id: str
    outcome: str
    approval_score: float
    confidence_level: str
    confidence_score: float
    rationale: Dict[str, Any]
    factors_analysis: List[Dict[str, Any]]
    recommendations: List[str]
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Decision Tree Configuration
# ============================================================================


class DecisionTreeConfig:
    """Decision tree configuration and rules."""

    def __init__(self):
        self.rules: Dict[str, Any] = {
            "financial": {
                "high_impact": {"threshold": 1_000_000, "min_approval": 85},
                "medium_impact": {"threshold": 100_000, "min_approval": 70},
                "low_impact": {"threshold": 0, "min_approval": 50},
            },
            "risk": {
                "critical": {"exposure": 0.8, "min_approval": 90},
                "high": {"exposure": 0.5, "min_approval": 75},
                "moderate": {"exposure": 0.3, "min_approval": 60},
                "low": {"exposure": 0, "min_approval": 40},
            },
            "time_sensitivity": {
                "urgent": {"hours": 24, "bypass_allowed": True},
                "normal": {"hours": 168, "bypass_allowed": False},
                "flexible": {"hours": 0, "bypass_allowed": False},
            },
        }
        self.category_weights = {
            "financial": 0.35,
            "risk": 0.30,
            "operational": 0.20,
            "strategic": 0.15,
        }

    def get_minimum_approval(self, category: str, severity: str) -> float:
        """Get minimum approval score for category/severity combo."""
        if category in self.rules and severity in self.rules[category]:
            return self.rules[category][severity].get("min_approval", 50)
        return 50.0

    def get_category_weight(self, category: str) -> float:
        """Get normalized weight for category."""
        return self.category_weights.get(category, 0.25)


# ============================================================================
# Decision Processing Tools
# ============================================================================


def calculate_approval_score(
    factors: List[Dict[str, Any]],
    normalization: str = "weighted_average"
) -> Dict[str, Any]:
    """
    Calculate approval score using weighted factors.

    Args:
        factors: List of factor dicts with name, value, weight, category
        normalization: Method for aggregation ("weighted_average", "harmonic", "geometric")

    Returns:
        Dict with score, component scores, and details
    """
    if not factors:
        raise ValueError("At least one factor required")

    # Convert to Factor objects for validation
    factor_objs = []
    for f in factors:
        try:
            factor = Factor(
                name=f["name"],
                value=float(f["value"]),
                weight=float(f["weight"]),
                category=f.get("category", "general"),
                description=f.get("description", ""),
                evidence=f.get("evidence", [])
            )
            if not factor.validate():
                raise ValueError(f"Invalid factor: {f['name']}")
            factor_objs.append(factor)
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid factor format: {e}")

    # Normalize weights
    total_weight = sum(f.weight for f in factor_objs)
    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")

    normalized_factors = [
        {
            "name": f.name,
            "value": f.value,
            "weight": f.weight / total_weight,
            "category": f.category,
            "contribution": (f.value * f.weight / total_weight)
        }
        for f in factor_objs
    ]

    # Calculate score by method
    if normalization == "weighted_average":
        score = sum(f["contribution"] for f in normalized_factors)
    elif normalization == "harmonic":
        # Harmonic mean weighted
        harmonic_parts = [f["weight"] / max(f["value"], 1) for f in normalized_factors]
        score = sum(f["weight"] for f in normalized_factors) / max(sum(harmonic_parts), 0.001)
    elif normalization == "geometric":
        # Geometric mean weighted
        geometric_product = 1.0
        for f in normalized_factors:
            geometric_product *= f["value"] ** f["weight"]
        score = geometric_product
    else:
        raise ValueError(f"Unknown normalization method: {normalization}")

    # Category-level aggregation
    category_scores = {}
    category_weights_total = {}
    for f in normalized_factors:
        cat = f["category"]
        if cat not in category_scores:
            category_scores[cat] = 0
            category_weights_total[cat] = 0
        category_scores[cat] += f["contribution"]
        category_weights_total[cat] += f["weight"]

    return {
        "overall_score": round(score, 2),
        "normalized_factors": normalized_factors,
        "category_scores": {
            cat: round(category_scores[cat] / max(category_weights_total[cat], 1), 2)
            for cat in category_scores
        },
        "method": normalization,
        "factor_count": len(normalized_factors),
    }


def generate_decision_rationale(
    decision_context: Dict[str, Any],
    factors: List[Dict[str, Any]],
    approval_score: float
) -> Dict[str, Any]:
    """
    Generate detailed rationale explaining each factor's contribution.

    Args:
        decision_context: Context dict with title, description
        factors: List of factor dicts
        approval_score: Overall approval score

    Returns:
        Dict with detailed rationale and explanations
    """
    config = DecisionTreeConfig()

    # Factor-level explanations
    factor_explanations = []
    for factor in factors:
        value = factor.get("value", 0)
        weight = factor.get("weight", 0)
        category = factor.get("category", "general")

        # Determine impact level
        if value >= 80:
            impact = "strong positive"
            confidence_word = "significantly supports"
        elif value >= 60:
            impact = "positive"
            confidence_word = "supports"
        elif value >= 40:
            impact = "neutral"
            confidence_word = "somewhat supports"
        elif value >= 20:
            impact = "negative"
            confidence_word = "questions"
        else:
            impact = "strong negative"
            confidence_word = "strongly opposes"

        weight_pct = weight * 100 if weight <= 1 else weight

        explanation = {
            "factor": factor["name"],
            "score": value,
            "weight": f"{weight_pct:.1f}%",
            "category": category,
            "impact": impact,
            "explanation": f"This {impact} factor {confidence_word} the decision. "
                          f"With {weight_pct:.1f}% weight and score of {value}/100, "
                          f"it {'significantly' if weight >= 0.25 else 'moderately' if weight >= 0.15 else 'minimally'} "
                          f"influences the outcome.",
            "evidence": factor.get("evidence", []),
        }
        factor_explanations.append(explanation)

    # Category-level summary
    category_summary = {}
    for cat in config.category_weights:
        cat_factors = [f for f in factor_explanations if f["category"] == cat]
        if cat_factors:
            avg_score = sum(f["score"] for f in cat_factors) / len(cat_factors)
            category_summary[cat] = {
                "average_score": round(avg_score, 1),
                "factor_count": len(cat_factors),
                "weight_importance": f"{config.category_weights[cat] * 100:.0f}%",
            }

    # Overall recommendation
    if approval_score >= 75:
        recommendation = "STRONG APPROVAL - High confidence in decision"
        reasoning = "The factors strongly align in favor of this decision"
    elif approval_score >= 60:
        recommendation = "CONDITIONAL APPROVAL - Moderate confidence"
        reasoning = "Most factors support this decision with some considerations"
    elif approval_score >= 45:
        recommendation = "DEFERRED - Further analysis needed"
        reasoning = "Mixed signals require additional information or conditions"
    else:
        recommendation = "REJECTION - Significant concerns"
        reasoning = "The factors predominantly oppose this decision"

    return {
        "decision_title": decision_context.get("title", "Untitled"),
        "factor_explanations": factor_explanations,
        "category_summary": category_summary,
        "overall_recommendation": recommendation,
        "recommendation_reasoning": reasoning,
        "score_interpretation": f"Score of {approval_score:.1f}/100",
    }


def assess_confidence_level(
    approval_score: float,
    factor_variance: float,
    data_quality: float = 0.8,
    priors: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Assess confidence level using Bayesian scoring.

    Args:
        approval_score: The calculated approval score (0-100)
        factor_variance: Variance in factor scores (0-1)
        data_quality: Quality of input data (0-1)
        priors: Optional Bayesian priors

    Returns:
        Dict with confidence level, score, and Bayesian analysis
    """
    if not 0 <= approval_score <= 100:
        raise ValueError("Approval score must be 0-100")
    if not 0 <= factor_variance <= 1:
        raise ValueError("Factor variance must be 0-1")
    if not 0 <= data_quality <= 1:
        raise ValueError("Data quality must be 0-1")

    # Set defaults for Bayesian priors
    if priors is None:
        priors = {}
    prior_prob = priors.get("prior_probability", 0.5)
    evidence_strength = priors.get("evidence_strength", 1.0)
    uncertainty = priors.get("uncertainty_factor", 0.1)

    # Normalize score to probability
    normalized_score = approval_score / 100.0

    # Apply Bayesian update (Bayes' theorem)
    likelihood_ratio = (normalized_score / (1 - normalized_score + 0.001)) if normalized_score < 1 else 100
    posterior_odds = prior_prob / (1 - prior_prob) * likelihood_ratio * evidence_strength
    posterior_prob = posterior_odds / (1 + posterior_odds)

    # Adjust for uncertainty and variance
    certainty_factor = (1 - factor_variance) * data_quality
    adjusted_confidence = posterior_prob * certainty_factor

    # Add epistemic uncertainty
    uncertainty_penalty = uncertainty * math.sqrt(factor_variance)
    final_confidence = max(0, adjusted_confidence - uncertainty_penalty)

    # Determine confidence level
    if final_confidence >= 0.85:
        level = ConfidenceLevel.VERY_HIGH.value
    elif final_confidence >= 0.70:
        level = ConfidenceLevel.HIGH.value
    elif final_confidence >= 0.55:
        level = ConfidenceLevel.MEDIUM.value
    elif final_confidence >= 0.40:
        level = ConfidenceLevel.LOW.value
    else:
        level = ConfidenceLevel.VERY_LOW.value

    return {
        "confidence_level": level,
        "confidence_score": round(final_confidence, 3),
        "posterior_probability": round(posterior_prob, 3),
        "certainty_factor": round(certainty_factor, 3),
        "bayesian_analysis": {
            "prior_probability": round(prior_prob, 3),
            "likelihood_ratio": round(likelihood_ratio, 3),
            "posterior_odds": round(posterior_odds, 3),
            "evidence_strength_multiplier": evidence_strength,
            "epistemic_uncertainty": round(uncertainty_penalty, 3),
        },
        "factors": {
            "approval_score": approval_score,
            "factor_variance": round(factor_variance, 3),
            "data_quality": round(data_quality, 3),
        },
    }


def format_decision_output(
    decision_id: str,
    title: str,
    approval_score: float,
    confidence_level: str,
    confidence_score: float,
    rationale: Dict[str, Any],
    factors: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format decision output as structured JSON.

    Args:
        decision_id: Unique decision identifier
        title: Decision title
        approval_score: Overall approval score
        confidence_level: Confidence level string
        confidence_score: Confidence score (0-1)
        rationale: Detailed rationale dict
        factors: List of factors analyzed
        metadata: Optional additional metadata

    Returns:
        Structured DecisionOutput dict
    """
    # Determine outcome
    if approval_score >= 70:
        outcome = DecisionOutcome.APPROVED.value
        recommendations = [
            "Proceed with implementation",
            "Monitor key success indicators",
            "Establish feedback loop for continuous improvement"
        ]
    elif approval_score >= 50:
        outcome = DecisionOutcome.CONDITIONAL.value
        recommendations = [
            "Identify and address conditional requirements",
            "Establish success criteria and checkpoints",
            "Plan for contingency scenarios"
        ]
    elif approval_score >= 30:
        outcome = DecisionOutcome.DEFERRED.value
        recommendations = [
            "Gather additional information",
            "Revisit decision after obtaining more data",
            "Consider alternative approaches"
        ]
    else:
        outcome = DecisionOutcome.REJECTED.value
        recommendations = [
            "Explore alternative options",
            "Address primary concerns identified",
            "Reassess after conditions change"
        ]

    # Build factors analysis
    factors_analysis = []
    for factor in factors:
        factors_analysis.append({
            "name": factor.get("name", "Unknown"),
            "score": factor.get("value", 0),
            "weight": factor.get("weight", 0),
            "category": factor.get("category", "general"),
            "evidence": factor.get("evidence", []),
            "contribution_impact": (
                factor.get("value", 0) * (factor.get("weight", 0) / max(sum(f.get("weight", 0) for f in factors), 1))
            ),
        })

    # Build decision conditions
    conditions = []
    if approval_score < 70:
        if approval_score < 50:
            conditions.append("Requires further analysis before proceeding")
        else:
            conditions.append("Conditional approval pending requirement fulfillment")
    if confidence_score < 0.6:
        conditions.append("Lower confidence requires additional validation")

    # Construct output
    decision_output = {
        "decision_id": decision_id,
        "title": title,
        "outcome": outcome,
        "scores": {
            "approval": round(approval_score, 2),
            "confidence": round(confidence_score, 3),
        },
        "confidence_level": confidence_level,
        "rationale": rationale,
        "factors_analysis": factors_analysis,
        "recommendations": recommendations,
        "conditions": conditions,
        "metadata": metadata or {},
    }

    return decision_output


# ============================================================================
# MCP Server Implementation
# ============================================================================


async def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """Process tool calls and return results."""

    try:
        if tool_name == "calculate_approval_score":
            result = calculate_approval_score(
                factors=tool_input.get("factors", []),
                normalization=tool_input.get("normalization", "weighted_average")
            )
            return json.dumps(result, indent=2)

        elif tool_name == "generate_decision_rationale":
            result = generate_decision_rationale(
                decision_context=tool_input.get("decision_context", {}),
                factors=tool_input.get("factors", []),
                approval_score=tool_input.get("approval_score", 50.0)
            )
            return json.dumps(result, indent=2)

        elif tool_name == "assess_confidence_level":
            result = assess_confidence_level(
                approval_score=tool_input.get("approval_score", 50.0),
                factor_variance=tool_input.get("factor_variance", 0.2),
                data_quality=tool_input.get("data_quality", 0.8),
                priors=tool_input.get("priors")
            )
            return json.dumps(result, indent=2)

        elif tool_name == "format_decision_output":
            result = format_decision_output(
                decision_id=tool_input.get("decision_id", "UNKNOWN"),
                title=tool_input.get("title", "Untitled Decision"),
                approval_score=tool_input.get("approval_score", 50.0),
                confidence_level=tool_input.get("confidence_level", "medium"),
                confidence_score=tool_input.get("confidence_score", 0.5),
                rationale=tool_input.get("rationale", {}),
                factors=tool_input.get("factors", []),
                metadata=tool_input.get("metadata")
            )
            return json.dumps(result, indent=2)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def get_tools() -> list:
    """Return tool definitions for MCP."""
    return [
        {
            "name": "calculate_approval_score",
            "description": "Calculate approval score using weighted factors with configurable aggregation method",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "factors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Factor name"},
                                "value": {"type": "number", "minimum": 0, "maximum": 100, "description": "Score 0-100"},
                                "weight": {"type": "number", "minimum": 0, "maximum": 1, "description": "Importance weight"},
                                "category": {"type": "string", "description": "Factor category"},
                                "description": {"type": "string", "description": "Factor description"},
                                "evidence": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Supporting evidence"
                                }
                            },
                            "required": ["name", "value", "weight"]
                        },
                        "description": "List of decision factors"
                    },
                    "normalization": {
                        "type": "string",
                        "enum": ["weighted_average", "harmonic", "geometric"],
                        "description": "Score aggregation method"
                    }
                },
                "required": ["factors"]
            }
        },
        {
            "name": "generate_decision_rationale",
            "description": "Generate detailed rationale explaining each factor's contribution to the decision",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "decision_context": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "description": "Decision context"
                    },
                    "factors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "number"},
                                "weight": {"type": "number"},
                                "category": {"type": "string"},
                                "evidence": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "description": "Analyzed factors"
                    },
                    "approval_score": {
                        "type": "number",
                        "description": "Overall approval score"
                    }
                },
                "required": ["decision_context", "factors", "approval_score"]
            }
        },
        {
            "name": "assess_confidence_level",
            "description": "Assess confidence level using Bayesian probability scoring",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "approval_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Approval score 0-100"
                    },
                    "factor_variance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Variance in factor scores"
                    },
                    "data_quality": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Quality of input data"
                    },
                    "priors": {
                        "type": "object",
                        "properties": {
                            "prior_probability": {"type": "number"},
                            "evidence_strength": {"type": "number"},
                            "uncertainty_factor": {"type": "number"}
                        },
                        "description": "Bayesian prior parameters"
                    }
                },
                "required": ["approval_score", "factor_variance"]
            }
        },
        {
            "name": "format_decision_output",
            "description": "Format decision analysis as structured JSON output",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "decision_id": {"type": "string", "description": "Unique decision identifier"},
                    "title": {"type": "string", "description": "Decision title"},
                    "approval_score": {
                        "type": "number",
                        "description": "Overall approval score"
                    },
                    "confidence_level": {
                        "type": "string",
                        "enum": ["very_low", "low", "medium", "high", "very_high"]
                    },
                    "confidence_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "rationale": {"type": "object", "description": "Decision rationale"},
                    "factors": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Analyzed factors"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata"
                    }
                },
                "required": ["decision_id", "title", "approval_score", "confidence_level", "confidence_score", "rationale", "factors"]
            }
        }
    ]


async def run_server():
    """Run the MCP server using stdio transport."""
    client = anthropic.Anthropic()

    print("DecisionSynthesis MCP Server started")

    tools = get_tools()
    messages = []

    # Example: Process a sample decision request
    sample_request = """
    Analyze the following decision using the DecisionSynthesis tools:

    Decision: "Approve $500,000 investment in AI infrastructure expansion"

    Factors:
    1. Financial Impact: Score 75/100, Weight 0.35 (ROI projections support investment)
    2. Risk Assessment: Score 65/100, Weight 0.30 (Moderate technology risk)
    3. Operational Readiness: Score 80/100, Weight 0.20 (Team prepared)
    4. Strategic Alignment: Score 85/100, Weight 0.15 (Aligns with roadmap)

    Please:
    1. Calculate the approval score
    2. Generate detailed rationale
    3. Assess confidence level
    4. Format final output
    """

    messages.append({
        "role": "user",
        "content": sample_request
    })

    print("\n" + "="*70)
    print("Processing Decision Analysis Request")
    print("="*70)
    print(sample_request)

    # Agentic loop
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Extract and print final response
            for block in response.content:
                if hasattr(block, 'text'):
                    print("\n" + "="*70)
                    print("Final Analysis")
                    print("="*70)
                    print(block.text)
            break

        if response.stop_reason == "tool_use":
            # Process tool calls
            tool_calls_made = False

            for block in response.content:
                if hasattr(block, 'text') and block.text:
                    print("\n[Claude]:", block.text)

                if block.type == "tool_use":
                    tool_calls_made = True
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    print(f"\n[Tool Call] {tool_name}")
                    print(f"Input: {json.dumps(tool_input, indent=2)}")

                    # Execute tool
                    tool_result = await process_tool_call(tool_name, tool_input)

                    print(f"Result: {tool_result[:200]}...")

                    # Add assistant response and tool result to messages
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": tool_result
                            }
                        ]
                    })

            if not tool_calls_made:
                break
        else:
            break

    print("\n" + "="*70)
    print("Server shutdown")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(run_server())
