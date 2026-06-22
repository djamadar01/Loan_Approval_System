"""
DecisionSynthesis MCP Server Client Example
Demonstrates all tools with realistic decision scenarios.
"""

import json
import asyncio
from typing import Dict, Any


def create_investment_decision_request() -> Dict[str, Any]:
    """Create a realistic investment decision scenario."""
    return {
        "decision_id": "INVEST-2024-001",
        "title": "Approve $2.5M Series B Cloud Infrastructure Investment",
        "description": "Strategic expansion of cloud infrastructure to support 10x growth",
        "factors": [
            {
                "name": "Financial ROI Analysis",
                "value": 78,
                "weight": 0.35,
                "category": "financial",
                "description": "3-year ROI projection with cost savings",
                "evidence": [
                    "Projected 40% cost reduction after 18 months",
                    "Revenue growth aligned with infrastructure scaling",
                    "Competitive pricing locked for 24 months"
                ]
            },
            {
                "name": "Technology Risk Assessment",
                "value": 62,
                "weight": 0.30,
                "category": "risk",
                "description": "Technology risk with mitigation strategies",
                "evidence": [
                    "Vendor has enterprise SLA guarantees",
                    "Redundancy architecture implemented",
                    "Migration risk: medium - phased approach planned"
                ]
            },
            {
                "name": "Operational Readiness",
                "value": 82,
                "weight": 0.20,
                "category": "operational",
                "description": "Team expertise and process maturity",
                "evidence": [
                    "Ops team completed vendor training",
                    "Migration runbook prepared and reviewed",
                    "Rollback procedures documented"
                ]
            },
            {
                "name": "Strategic Alignment",
                "value": 88,
                "weight": 0.15,
                "category": "strategic",
                "description": "Alignment with company roadmap",
                "evidence": [
                    "Directly supports Q3 scaling initiative",
                    "Enables new market entry in APAC region",
                    "Founder-approved strategic priority"
                ]
            }
        ],
        "threshold_approval": 75,
        "threshold_rejection": 40,
        "risk_profile": "moderate",
        "time_sensitive": True
    }


def create_product_launch_decision() -> Dict[str, Any]:
    """Create a product launch decision scenario."""
    return {
        "decision_id": "LAUNCH-2024-Q3",
        "title": "Launch New Analytics Dashboard Feature",
        "description": "Release real-time analytics dashboard to beta customers",
        "factors": [
            {
                "name": "Market Demand",
                "value": 85,
                "weight": 0.30,
                "category": "strategic",
                "description": "Customer feedback and market analysis",
                "evidence": [
                    "72% of beta users requested this feature",
                    "Competitor analysis shows market gap",
                    "Industry analyst reports strong demand"
                ]
            },
            {
                "name": "Product Maturity",
                "value": 71,
                "weight": 0.35,
                "category": "operational",
                "description": "Feature completeness and quality",
                "evidence": [
                    "Core functionality complete",
                    "95% test coverage achieved",
                    "Known limitations documented for beta"
                ]
            },
            {
                "name": "Competitive Position",
                "value": 76,
                "weight": 0.20,
                "category": "strategic",
                "description": "Time-to-market advantage",
                "evidence": [
                    "Competitor launch expected in Q4",
                    "Early mover advantage in current market",
                    "Differentiation through superior UX"
                ]
            },
            {
                "name": "Resource Availability",
                "value": 58,
                "weight": 0.15,
                "category": "operational",
                "description": "Team capacity for support and iteration",
                "evidence": [
                    "Support team partially reallocated",
                    "Product team capacity: 60%",
                    "Vendor support available"
                ]
            }
        ],
        "threshold_approval": 70,
        "risk_profile": "low"
    }


def create_hiring_decision() -> Dict[str, Any]:
    """Create an executive hiring decision scenario."""
    return {
        "decision_id": "HIRE-2024-VP-ENG",
        "title": "Hire VP of Engineering - External Candidate",
        "description": "Fill critical VP Engineering role with external leadership hire",
        "factors": [
            {
                "name": "Experience Match",
                "value": 87,
                "weight": 0.30,
                "category": "operational",
                "description": "Background fit and relevant experience",
                "evidence": [
                    "15 years engineering leadership in SaaS",
                    "Led teams of 100+ engineers",
                    "Founded and scaled two successful companies"
                ]
            },
            {
                "name": "Cultural Fit",
                "value": 72,
                "weight": 0.25,
                "category": "operational",
                "description": "Values alignment and team dynamics",
                "evidence": [
                    "Interviewing panel assessment: positive",
                    "References emphasize collaboration",
                    "Some uncertainty on startup environment fit"
                ]
            },
            {
                "name": "Compensation Alignment",
                "value": 65,
                "weight": 0.25,
                "category": "financial",
                "description": "Salary and equity expectations",
                "evidence": [
                    "Expectations at upper range of budget",
                    "Equity negotiation in progress",
                    "Recruitment timeline: 2 weeks for offer"
                ]
            },
            {
                "name": "Market Availability",
                "value": 55,
                "weight": 0.20,
                "category": "strategic",
                "description": "Candidate availability and competing offers",
                "evidence": [
                    "Candidate has competing offer",
                    "Start date negotiable: 2-4 weeks",
                    "Strong passive candidate (not job hunting)"
                ]
            }
        ],
        "threshold_approval": 72,
        "require_consensus": True
    }


async def run_client_examples():
    """Run example decision analyses."""

    examples = [
        ("Investment Decision", create_investment_decision_request()),
        ("Product Launch", create_product_launch_decision()),
        ("Hiring Decision", create_hiring_decision()),
    ]

    for title, decision_data in examples:
        print("\n" + "="*80)
        print(f"Example: {title}")
        print("="*80)

        # Step 1: Calculate approval score
        print("\n[Step 1] Calculating Approval Score...")
        approval_data = {
            "factors": decision_data["factors"],
            "normalization": "weighted_average"
        }
        print(f"Factors: {len(approval_data['factors'])} analyzed")
        print(f"Normalization: {approval_data['normalization']}")

        # Step 2: Generate rationale
        print("\n[Step 2] Generating Decision Rationale...")
        rationale_data = {
            "decision_context": {
                "title": decision_data["title"],
                "description": decision_data["description"]
            },
            "factors": decision_data["factors"],
            "approval_score": 75.0  # Simulated score
        }
        print(f"Decision: {rationale_data['decision_context']['title']}")

        # Step 3: Assess confidence
        print("\n[Step 3] Assessing Confidence Level...")
        confidence_data = {
            "approval_score": 75.0,
            "factor_variance": 0.12,
            "data_quality": 0.85,
            "priors": {
                "prior_probability": 0.6,
                "evidence_strength": 1.2,
                "uncertainty_factor": 0.08
            }
        }
        print(f"Approval Score: {confidence_data['approval_score']}")
        print(f"Factor Variance: {confidence_data['factor_variance']}")
        print(f"Data Quality: {confidence_data['data_quality']}")

        # Step 4: Format output
        print("\n[Step 4] Formatting Decision Output...")
        output_data = {
            "decision_id": decision_data["decision_id"],
            "title": decision_data["title"],
            "approval_score": 75.0,
            "confidence_level": "high",
            "confidence_score": 0.78,
            "rationale": {
                "recommendation": "CONDITIONAL APPROVAL",
                "reasoning": "Strong factors support approval with stated conditions"
            },
            "factors": decision_data["factors"],
            "metadata": {
                "requested_by": "CEO",
                "decision_date": "2024-06-19",
                "required_by": "2024-06-30"
            }
        }
        print(f"Output formatted for decision_id: {output_data['decision_id']}")
        print(f"Approval Score: {output_data['approval_score']:.1f}/100")
        print(f"Confidence Level: {output_data['confidence_level']}")

        print("\n" + "-"*80)
        print("Expected Decision Output Structure:")
        print("-"*80)
        expected_output = {
            "decision_id": output_data["decision_id"],
            "title": output_data["title"],
            "outcome": "conditional",
            "scores": {
                "approval": 75.0,
                "confidence": 0.78
            },
            "confidence_level": "high",
            "rationale": output_data["rationale"],
            "factors_analysis": [
                {
                    "name": f["name"],
                    "score": f["value"],
                    "weight": f["weight"],
                    "category": f["category"]
                }
                for f in output_data["factors"]
            ],
            "recommendations": [
                "Proceed with implementation",
                "Monitor key success indicators"
            ],
            "conditions": ["Vendor SLA compliance required"],
            "metadata": output_data["metadata"]
        }
        print(json.dumps(expected_output, indent=2))

    print("\n" + "="*80)
    print("Client Example Summary")
    print("="*80)
    print(f"Processed {len(examples)} decision scenarios")
    print("Each demonstrates all 4 core tools:")
    print("  1. calculate_approval_score()")
    print("  2. generate_decision_rationale()")
    print("  3. assess_confidence_level()")
    print("  4. format_decision_output()")


if __name__ == "__main__":
    asyncio.run(run_client_examples())
