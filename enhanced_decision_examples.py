"""
Practical Usage Examples for Enhanced DecisionSynthesis MCP Server

This file demonstrates real-world usage patterns for each feature.
"""

import json
from typing import Dict, Any, List


# ============================================================================
# Example 1: Decision Explainability in Action
# ============================================================================

def example_1_loan_application_explainability():
    """
    Use Case: Loan Officer Reviews Loan Application Rejection

    A customer applied for a loan and was rejected. They want to understand why.
    The loan officer uses explain_decision() to provide detailed reasoning.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: LOAN APPLICATION EXPLAINABILITY".center(80))
    print("=" * 80)

    print("\nScenario:")
    print("  Customer: John Smith")
    print("  Application: Personal loan for $50,000")
    print("  Decision: REJECTED")
    print("  Challenge: Customer wants to know why")

    loan_params = {
        "financial_risk": 65,      # Recent late payments
        "operational_risk": 45,    # Stable employment
        "compliance_risk": 35,     # Good credit history
        "reputational_risk": 40,   # Mixed business references
        "has_critical_issues": True,      # Recent delinquency
        "has_mitigating_factors": False,  # No strong mitigators
        "requires_escalation": False,
    }

    print("\nRisk Profile:")
    for key, value in loan_params.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    print("\nWhat the Loan Officer Tells the Customer Using explain_decision():")
    print("\n  'Your application was rejected for the following reasons:\n")
    print("  PRIMARY REASONS:")
    print("    1. Financial Risk (65/100): Recent payment history shows delinquency")
    print("       • Multiple late payments in last 6 months")
    print("       • This is a critical factor (35% weight)")
    print("")
    print("    2. Critical Issues Detected:")
    print("       • Unmitigable financial delinquency")
    print("       • No compensating factors")
    print("")
    print("  DECISION PATH:")
    print("    [1] Calculate Risk Score → 52.75/100")
    print("    [2] Evaluate Critical Factors → Has delinquency")
    print("    [3] Check Escalation → Not flagged")
    print("    [4] Risk in medium range but critical issue present")
    print("    [5] Final Classification → REJECT")
    print("")
    print("  IMPACT BREAKDOWN:")
    print("    • Financial Impact (65 × 0.35): 22.75")
    print("    • Operational Impact (45 × 0.25): 11.25")
    print("    • Compliance Impact (35 × 0.25): 8.75")
    print("    • Reputational Impact (40 × 0.15): 6.00")
    print("")
    print("  RECOMMENDATION:")
    print("    Reapply after 12+ months of clean payment history")

    print("\n✓ BENEFIT: Customer understands specific reasons and can take action")


# ============================================================================
# Example 2: What-If Analysis for Risk Mitigation
# ============================================================================

def example_2_what_if_risk_mitigation():
    """
    Use Case: Company Planning Vendor Risk Mitigation

    A company is evaluating a vendor but the risk is too high. They want to
    explore what mitigations would be needed to change the decision.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: WHAT-IF ANALYSIS FOR RISK MITIGATION".center(80))
    print("=" * 80)

    print("\nScenario:")
    print("  Vendor: International Logistics Co.")
    print("  Current Decision: REVIEW (High Risk)")
    print("  Objective: Identify mitigation strategies to enable approval")

    vendor_params = {
        "financial_risk": 70,
        "operational_risk": 65,
        "compliance_risk": 75,
        "reputational_risk": 60,
        "has_critical_issues": True,
        "has_mitigating_factors": False,
        "requires_escalation": True,
    }

    print("\nCurrent Risk Profile:")
    print(f"  Overall Risk Score: ~71/100")
    print(f"  Status: High operational and compliance risks")

    scenarios_to_explore = [
        {
            "name": "Add Compliance Certification",
            "description": "Vendor obtains ISO 27001 certification",
            "compliance_risk": 45,  # Reduced from 75
        },
        {
            "name": "Financial Audit & Guarantee",
            "description": "Third-party audit + performance bond",
            "financial_risk": 40,  # Reduced from 70
        },
        {
            "name": "Phased Implementation",
            "description": "Start with limited scope and expand if successful",
            "has_mitigating_factors": True,  # Added
        },
        {
            "name": "Insurance & Indemnification",
            "description": "Cyber insurance + liability coverage",
            "reputational_risk": 35,  # Reduced from 60
        },
    ]

    print("\nWhat-If Analysis Results:")
    print("\n  SCENARIO 1: Add Compliance Certification (ISO 27001)")
    print("    • Original Decision: REVIEW")
    print("    • Compliance Risk: 75 → 45 (↓30)")
    print("    • New Risk Score: ~63 (↓8)")
    print("    • New Decision: LIKELY REVIEW")
    print("    • Status: Improvement but still not approval-ready")

    print("\n  SCENARIO 2: Financial Audit & Performance Bond")
    print("    • Original Decision: REVIEW")
    print("    • Financial Risk: 70 → 40 (↓30)")
    print("    • New Risk Score: ~59 (↓12)")
    print("    • New Decision: LIKELY REVIEW")
    print("    • Status: Significant improvement, medium confidence")

    print("\n  SCENARIO 3: Phased Implementation + Add Mitigators")
    print("    • Original Decision: REVIEW")
    print("    • Add Mitigating Factors: True")
    print("    • New Decision: REVIEW → LIKELY APPROVE")
    print("    • Status: Could change decision!")

    print("\n  SCENARIO 4: Insurance & Indemnification")
    print("    • Original Decision: REVIEW")
    print("    • Reputational Risk: 60 → 35 (↓25)")
    print("    • New Risk Score: ~65 (↓6)")
    print("    • New Decision: LIKELY REVIEW")
    print("    • Status: Moderate improvement")

    print("\n  COMBINED STRATEGY RECOMMENDATION:")
    print("    ✓ SCENARIO 1 + SCENARIO 3 = LIKELY APPROVAL")
    print("    ")
    print("    Suggested Approach:")
    print("    1. Require ISO 27001 certification (addresses compliance)")
    print("    2. Implement phased pilot (provides mitigation)")
    print("    3. Add insurance coverage (reduces reputational risk)")
    print("    ")
    print("    Expected Result: Approval of limited initial contract")

    print("\n✓ BENEFIT: Clear path forward identified for vendor relationship")


# ============================================================================
# Example 3: Confidence Intervals for Threshold Setting
# ============================================================================

def example_3_confidence_intervals():
    """
    Use Case: Setting Risk Thresholds for Automated Decisions

    A bank wants to set automated decision thresholds but needs to account
    for measurement uncertainty. They use confidence intervals to set robust thresholds.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: CONFIDENCE INTERVALS FOR THRESHOLD SETTING".center(80))
    print("=" * 80)

    print("\nScenario:")
    print("  Bank: Large Financial Institution")
    print("  Objective: Set automated approval thresholds")
    print("  Challenge: Account for measurement error and variability")

    print("\nCurrent Proposed Thresholds:")
    print("  • APPROVE if Risk Score < 50")
    print("  • REVIEW if Risk Score 50-85")
    print("  • REJECT if Risk Score >= 85")

    print("\nProblem: What if true risk is near boundary?")
    print("  Example: Measured Score = 48, but True Score = 52")
    print("           Would approve when should review!")

    # Confidence interval example
    sample_size = 150
    import math

    def show_ci(score, threshold, label):
        z_score = 1.96
        population_std = 20
        se = population_std / math.sqrt(sample_size)
        moe = z_score * se
        lower = max(0, score - moe)
        upper = min(100, score + moe)

        print(f"\n  {label}:")
        print(f"    Measured Score: {score}")
        print(f"    95% CI: [{lower:.1f}, {upper:.1f}]")
        print(f"    Margin of Error: ±{moe:.1f}")

        if upper < threshold and label.startswith("Edge Case"):
            print(f"    Status: ✓ Safe (upper CI < {threshold})")
        elif lower > threshold and label.startswith("Edge Case"):
            print(f"    Status: ⚠ Risky (lower CI > {threshold})")
        else:
            print(f"    Status: Could cross threshold")

    show_ci(48, 50, "Edge Case A (near 50 boundary)")
    show_ci(52, 50, "Edge Case B (near 50 boundary)")
    show_ci(83, 85, "Edge Case C (near 85 boundary)")

    print("\n\nRECOMMENDED ADJUSTED THRESHOLDS (with confidence buffers):")
    print("  • APPROVE if Risk Score < 45  (buffer: 5 points)")
    print("  • REVIEW if Risk Score 45-80  (buffer: 5 points)")
    print("  • REJECT if Risk Score >= 80  (buffer: 5 points)")

    print("\n  Rationale:")
    print("    With sample size 150, margin of error ≈ 3.3 points")
    print("    5-point buffers provide safety margin against measurement error")
    print("    Reduces probability of threshold-crossing false decisions")

    print("\n✓ BENEFIT: More robust automated thresholds with measurement uncertainty")


# ============================================================================
# Example 4: Decision Probability Scoring
# ============================================================================

def example_4_probability_scoring():
    """
    Use Case: Human Reviewer Resource Allocation

    A call center has N reviewers and needs to decide which cases to send to humans
    vs. which to auto-approve. They use probability scores to optimize allocation.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: DECISION PROBABILITY SCORING FOR RESOURCE ALLOCATION".center(80))
    print("=" * 80)

    print("\nScenario:")
    print("  Call Center: Loan Approval Bureau")
    print("  Volume: 10,000 applications/day")
    print("  Constraint: Only 200 human reviewers available (2%)")
    print("  Challenge: Which 2% to route to humans?")

    cases = [
        {
            "id": "APP-001",
            "risk_score": 25,
            "category": "LOW",
            "approve_prob": 0.92,
            "reject_prob": 0.02,
            "review_prob": 0.06,
            "entropy": 0.18,
        },
        {
            "id": "APP-002",
            "risk_score": 62,
            "category": "MEDIUM",
            "approve_prob": 0.54,
            "reject_prob": 0.06,
            "review_prob": 0.40,
            "entropy": 0.62,
        },
        {
            "id": "APP-003",
            "risk_score": 88,
            "category": "HIGH",
            "approve_prob": 0.02,
            "reject_prob": 0.83,
            "review_prob": 0.15,
            "entropy": 0.28,
        },
        {
            "id": "APP-004",
            "risk_score": 51,
            "category": "MEDIUM",
            "approve_prob": 0.48,
            "reject_prob": 0.15,
            "review_prob": 0.37,
            "entropy": 0.68,
        },
    ]

    print("\nDECISION PROBABILITY ANALYSIS:")
    print("-" * 80)
    print(f"{'Case':<12} {'Risk':<8} {'Approve%':<10} {'Reject%':<10} {'Review%':<10} {'Entropy':<8}")
    print("-" * 80)

    for case in cases:
        print(
            f"{case['id']:<12} {case['risk_score']:<8} "
            f"{case['approve_prob']*100:<10.0f} {case['reject_prob']*100:<10.0f} "
            f"{case['review_prob']*100:<10.0f} {case['entropy']:<8.2f}"
        )

    print("\nHUMAN REVIEW STRATEGY (High Entropy First):")
    print("  Priority 1 (High Uncertainty - MUST REVIEW):")
    print("    • APP-004: Entropy 0.68 (highly uncertain)")
    print("    • APP-002: Entropy 0.62 (moderately uncertain)")
    print("")
    print("  Priority 2 (Extreme Cases - AUTO-DECIDE):")
    print("    • APP-001: Entropy 0.18 (92% approve - auto-approve)")
    print("    • APP-003: Entropy 0.28 (83% reject - auto-reject)")

    print("\nRECOMMENDED ROUTING STRATEGY:")
    print("  Entropy > 0.60 → Route to Human Reviewer")
    print("  Entropy 0.30-0.60 → Route to Secondary Screening")
    print("  Entropy < 0.30 → Auto-Approve/Reject")

    print("\nEXPECTED OUTCOME:")
    print("  • HIGH confidence auto-approvals: 70%")
    print("  • HIGH confidence auto-rejections: 20%")
    print("  • Borderline cases to human review: 10% (1,000/day)")
    print("  • 200 reviewers can handle 5 cases/hour = 1,600/day")
    print("  • ✓ RESULT: 60% surplus human capacity for complex cases")

    print("\n✓ BENEFIT: Optimal resource allocation based on decision uncertainty")


# ============================================================================
# Example 5: Bias Detection in Action
# ============================================================================

def example_5_bias_detection():
    """
    Use Case: Regulatory Audit of Decision System

    A regulator is auditing a loan approval system for fair lending compliance.
    They use bias detection to identify systematic unfairness.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: BIAS DETECTION IN REGULATORY AUDIT".center(80))
    print("=" * 80)

    print("\nScenario:")
    print("  Regulator: Consumer Financial Protection Bureau (CFPB)")
    print("  Bank: Community First Bank")
    print("  Audit: Fair lending compliance review")
    print("  Concern: Possible algorithmic bias in loan decisions")

    print("\nBIAS DETECTION RESULTS:")

    biases = [
        {
            "type": "FACTOR_DOMINANCE",
            "severity": "MEDIUM",
            "description": "Compliance risk dominates decision",
            "impact": "Compliance contributes 48% of decision weight vs expected 25%",
            "finding": "BIAS DETECTED: Compliance weight is 92% higher than specified",
        },
        {
            "type": "RISK_SKEW",
            "severity": "LOW",
            "description": "Risk factor distribution imbalanced",
            "impact": "Financial risk varies more than others",
            "finding": "ACCEPTABLE: Within normal variance (Std Dev 22)",
        },
        {
            "type": "THRESHOLD_BIAS",
            "severity": "HIGH",
            "description": "Threshold application unfair",
            "impact": "High compliance scores heavily penalize women-owned businesses",
            "finding": "BIAS DETECTED: Compliance score threshold is discriminatory",
        },
    ]

    for i, bias in enumerate(biases, 1):
        severity_emoji = "🔴" if bias["severity"] == "HIGH" else "🟡" if bias["severity"] == "MEDIUM" else "🟢"
        print(f"\n  {i}. {severity_emoji} {bias['type']} ({bias['severity']})")
        print(f"     Description: {bias['description']}")
        print(f"     Impact: {bias['impact']}")
        print(f"     Finding: {bias['finding']}")

    print("\n\nREGULATORY FINDINGS:")
    print("  Overall Bias Score: 0.42/1.0 (MODERATE RISK)")
    print("")
    print("  VIOLATIONS IDENTIFIED:")
    print("    1. Compliance risk is over-weighted vs. policy")
    print("    2. Threshold application differs by applicant demographics")
    print("    3. Escalation bias: Some groups over-escalated")

    print("\n  ENFORCEMENT ACTIONS TAKEN:")
    print("    • $2.1M civil penalty for discriminatory practices")
    print("    • Required to recalibrate risk weights")
    print("    • Quarterly fairness audits for 3 years")
    print("    • Retraining of loan officers")

    print("\n  REMEDIATION:")
    print("    1. Adjust compliance weight from 35% to 20%")
    print("    2. Implement demographic parity checks")
    print("    3. Regular bias detection monitoring")
    print("    4. Independent fairness audits")

    print("\n✓ BENEFIT: Proactive bias detection prevents regulatory issues")


# ============================================================================
# Example 6: Integrated Multi-Feature Analysis
# ============================================================================

def example_6_integrated_analysis():
    """
    Use Case: Comprehensive Pre-Decision Analysis

    A company performs comprehensive analysis before making high-value decisions,
    using all features together.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 6: INTEGRATED MULTI-FEATURE ANALYSIS".center(80))
    print("=" * 80)

    print("\nScenario:")
    print("  Company: Global Supply Chain Corp")
    print("  Decision: $50M partnership with international supplier")
    print("  Complexity: High stakes, multiple uncertainties")
    print("  Approach: Comprehensive analysis using all features")

    supplier_params = {
        "financial_risk": 55,
        "operational_risk": 50,
        "compliance_risk": 48,
        "reputational_risk": 45,
        "has_critical_issues": False,
        "has_mitigating_factors": True,
        "requires_escalation": False,
    }

    print("\n1. EXPLAINABILITY: Why is the decision REVIEW?")
    print("   • Medium-high risk profile (score 50.55)")
    print("   • Mitigating factors present (long track record)")
    print("   • No critical unmitigable issues")
    print("   • Recommendation: Requires executive review")

    print("\n2. WHAT-IF ANALYSIS: What changes the decision?")
    print("   • Improve compliance to 30: Risk drops to 46 → Could APPROVE")
    print("   • Add performance guarantee: Risk drops to 47 → Could APPROVE")
    print("   • Extend contract review period: Enables APPROVE with conditions")

    print("\n3. CONFIDENCE INTERVALS: How certain are our estimates?")
    print("   • Financial Risk: 55 [±4] = [51, 59]")
    print("   • Operational Risk: 50 [±4] = [46, 54]")
    print("   • Compliance Risk: 48 [±4] = [44, 52]")
    print("   • Overall Score: 50.55 [±3.2] = [47.35, 53.75]")
    print("   • Implication: Could be as low as 47 (below review threshold)")

    print("\n4. PROBABILITY SCORING: What's the likely outcome?")
    print("   • Approve Probability: 48%")
    print("   • Review Probability: 37%")
    print("   • Reject Probability: 15%")
    print("   • Entropy: 0.58 (moderate uncertainty)")
    print("   • Most Likely: APPROVE (but with conditions)")

    print("\n5. BIAS DETECTION: Are we being fair?")
    print("   • Overall Bias Score: 0.08 (low bias)")
    print("   • Risk distribution: Balanced (Std Dev 4.2)")
    print("   • No factor dominance detected")
    print("   • Decision thresholds appear fair")
    print("   • Escalation criteria consistently applied")

    print("\n\nINTEGRATED RECOMMENDATION:")
    print("=" * 80)
    print("DECISION: CONDITIONAL APPROVAL")
    print("")
    print("CONDITIONS:")
    print("  1. Improve compliance score from 48 to 35 within 6 months")
    print("  2. Add $5M performance guarantee")
    print("  3. Quarterly compliance reviews (vs annual)")
    print("  4. Pilot program: Start with 30% of planned volume")
    print("")
    print("RATIONALE:")
    print("  • Explainability: Clear path through decision logic")
    print("  • What-If: These conditions would enable approval")
    print("  • Confidence: Even worst-case estimates support review decision")
    print("  • Probability: 48% approval probability with conditions")
    print("  • Fairness: No bias detected in decision process")
    print("")
    print("EXPECTED OUTCOME:")
    print("  • Full partnership if conditions met (12-month timeline)")
    print("  • Managed risk exposure during pilot phase")
    print("  • Clear escalation path if conditions not met")

    print("\n✓ BENEFIT: Well-informed decision with clear rationale and contingency path")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run all examples"""
    print("\n")
    print("=" * 80)
    print("ENHANCED DECISIONSYNTHESIS MCP - PRACTICAL EXAMPLES".center(80))
    print("=" * 80)
    print("\nThese examples demonstrate real-world usage of each feature.")

    # Run all examples
    example_1_loan_application_explainability()
    example_2_what_if_risk_mitigation()
    example_3_confidence_intervals()
    example_4_probability_scoring()
    example_5_bias_detection()
    example_6_integrated_analysis()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY".center(80))
    print("=" * 80)

    print("\nKey Takeaways:")
    print("  ✓ Explainability → Justify decisions to stakeholders")
    print("  ✓ What-If Analysis → Plan strategies for change")
    print("  ✓ Confidence Intervals → Account for measurement uncertainty")
    print("  ✓ Probability Scoring → Optimize resource allocation")
    print("  ✓ Bias Detection → Ensure fairness and compliance")
    print("  ✓ Integrated Analysis → Comprehensive decision support")

    print("\nWhen to Use Each Feature:")
    print("  • High-stakes decisions → Use ALL features")
    print("  • Customer communications → Use Explainability")
    print("  • Strategic planning → Use What-If Analysis")
    print("  • System calibration → Use Confidence Intervals")
    print("  • Resource optimization → Use Probability Scoring")
    print("  • Regulatory compliance → Use Bias Detection")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
