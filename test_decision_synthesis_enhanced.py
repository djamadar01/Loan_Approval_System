"""
Comprehensive test and demonstration client for the Enhanced DecisionSynthesis MCP server.

Demonstrates all new features:
1. Decision Explainability
2. What-if Analysis
3. Confidence Intervals
4. Decision Probabilities
5. Bias Detection
"""

import json
import sys
import math
import statistics
from typing import Any


class EnhancedDecisionSynthesisDemo:
    """Comprehensive demo client for enhanced DecisionSynthesis features"""

    def __init__(self):
        self.scenarios = []

    def add_scenario(self, name: str, description: str, params: dict):
        """Add a test scenario"""
        scenario = {
            "name": name,
            "description": description,
            "params": params
        }
        self.scenarios.append(scenario)
        return self

    def build_scenarios(self):
        """Build comprehensive test scenarios"""

        # Scenario 1: Low risk, straightforward approval
        self.add_scenario(
            "Low Risk - Straightforward Approval",
            "Application with low risk across all categories - should auto-approve",
            {
                "financial_risk": 10,
                "operational_risk": 15,
                "compliance_risk": 5,
                "reputational_risk": 8,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
                "requires_escalation": False,
            }
        )

        # Scenario 2: Medium-high risk requiring review
        self.add_scenario(
            "Medium-High Risk - Review Required",
            "Application with moderate risk but mitigating factors present",
            {
                "financial_risk": 60,
                "operational_risk": 55,
                "compliance_risk": 50,
                "reputational_risk": 45,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
                "requires_escalation": False,
            }
        )

        # Scenario 3: High risk with critical issues
        self.add_scenario(
            "High Risk - Critical Issues",
            "Application with high risk scores and critical issues requiring expert review",
            {
                "financial_risk": 75,
                "operational_risk": 70,
                "compliance_risk": 80,
                "reputational_risk": 65,
                "has_critical_issues": True,
                "has_mitigating_factors": False,
                "requires_escalation": True,
            }
        )

        # Scenario 4: Extreme compliance risk
        self.add_scenario(
            "Extreme Compliance Risk - Likely Rejection",
            "Application with critical compliance violations",
            {
                "financial_risk": 20,
                "operational_risk": 25,
                "compliance_risk": 95,
                "reputational_risk": 30,
                "has_critical_issues": True,
                "has_mitigating_factors": False,
                "requires_escalation": True,
            }
        )

        # Scenario 5: Skewed risk profile
        self.add_scenario(
            "Skewed Risk Profile - Operational Heavy",
            "Application with highly skewed risk factors - potential bias",
            {
                "financial_risk": 5,
                "operational_risk": 85,
                "compliance_risk": 10,
                "reputational_risk": 8,
                "has_critical_issues": False,
                "has_mitigating_factors": True,
                "requires_escalation": False,
            }
        )

        return self

    def print_header(self, title: str, level: int = 1):
        """Print formatted header"""
        if level == 1:
            print("\n" + "=" * 80)
            print(title.center(80))
            print("=" * 80 + "\n")
        elif level == 2:
            print("\n" + "-" * 80)
            print(title)
            print("-" * 80)
        else:
            print(f"\n>>> {title}")

    def print_section(self, title: str):
        """Print section header"""
        print(f"\n  {title}")
        print(f"  {'-' * (len(title))}")

    def demonstrate_explainability(self):
        """Demonstrate decision explainability feature"""
        self.print_header("FEATURE 1: DECISION EXPLAINABILITY", level=1)

        print("Decision explainability provides detailed reasoning for each decision:")
        print("- Primary reasons with impact scores")
        print("- Contributing factors and their weights")
        print("- Step-by-step decision path through the logic")
        print("- Rule chain showing which rules were evaluated")
        print("- Impact breakdown of each risk category")

        # Example with scenario 1
        scenario = self.scenarios[0]
        params = scenario["params"]

        print(f"\n>>> Analyzing: {scenario['name']}")
        print(f"    Description: {scenario['description']}")

        from decision_synthesis_enhanced import EnhancedDecisionRuleSet

        risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
            financial_risk=params["financial_risk"],
            operational_risk=params["operational_risk"],
            compliance_risk=params["compliance_risk"],
            reputational_risk=params["reputational_risk"],
        )

        classification, confidence, factors = EnhancedDecisionRuleSet.classify_decision(
            risk_score=risk_score,
            has_critical_issues=params["has_critical_issues"],
            has_mitigating_factors=params["has_mitigating_factors"],
            requires_escalation=params["requires_escalation"],
        )

        print(f"\n  Decision Summary:")
        print(f"  ├─ Classification: {classification.value}")
        print(f"  ├─ Risk Score: {risk_score}/100")
        print(f"  ├─ Confidence: {confidence:.2f}")
        print(f"  └─ Key Factors:")
        for factor in factors:
            print(f"     - {factor}")

        print(f"\n  Risk Factor Impact Analysis:")
        weights = {"financial": 0.35, "operational": 0.25, "compliance": 0.25, "reputational": 0.15}
        impacts = {
            "Financial": params["financial_risk"] * weights["financial"],
            "Operational": params["operational_risk"] * weights["operational"],
            "Compliance": params["compliance_risk"] * weights["compliance"],
            "Reputational": params["reputational_risk"] * weights["reputational"],
        }
        for factor, impact in impacts.items():
            print(f"  ├─ {factor}: {impact:.1f}")

        print(f"\n  Expected API Response:")
        print(f"  ├─ primary_reasons: [High-impact reasons ranked by influence]")
        print(f"  ├─ contributing_factors: [Secondary factors]")
        print(f"  ├─ decision_path: [Step-by-step logic path]")
        print(f"  ├─ rule_chain: [Rules evaluated and results]")
        print(f"  └─ impact_breakdown: [Detailed impact analysis]")

    def demonstrate_whatif_analysis(self):
        """Demonstrate what-if analysis feature"""
        self.print_header("FEATURE 2: WHAT-IF ANALYSIS", level=1)

        print("What-if analysis explores how decision changes with different conditions:")
        print("- Reduce financial risk by 50%")
        print("- Add strong mitigating factors")
        print("- Reduce all risks by 25%")
        print("- Increase compliance risk to critical")

        scenario = self.scenarios[2]  # High risk scenario
        params = scenario["params"]

        print(f"\n>>> Analyzing: {scenario['name']}")
        print(f"    Description: {scenario['description']}")

        from decision_synthesis_enhanced import EnhancedDecisionRuleSet

        original_risk = EnhancedDecisionRuleSet.calculate_risk_score(
            financial_risk=params["financial_risk"],
            operational_risk=params["operational_risk"],
            compliance_risk=params["compliance_risk"],
            reputational_risk=params["reputational_risk"],
        )

        original_class, _, _ = EnhancedDecisionRuleSet.classify_decision(
            risk_score=original_risk,
            has_critical_issues=params["has_critical_issues"],
            has_mitigating_factors=params["has_mitigating_factors"],
            requires_escalation=params["requires_escalation"],
        )

        print(f"\n  Original Decision: {original_class.value} (Risk Score: {original_risk}/100)")

        # Scenario A: Reduce financial risk by 50%
        scenario_a_risk = EnhancedDecisionRuleSet.calculate_risk_score(
            financial_risk=params["financial_risk"] * 0.5,
            operational_risk=params["operational_risk"],
            compliance_risk=params["compliance_risk"],
            reputational_risk=params["reputational_risk"],
        )
        scenario_a_class, _, _ = EnhancedDecisionRuleSet.classify_decision(
            risk_score=scenario_a_risk,
            has_critical_issues=params["has_critical_issues"],
            has_mitigating_factors=params["has_mitigating_factors"],
            requires_escalation=params["requires_escalation"],
        )
        print(f"\n  Scenario A: Reduce Financial Risk by 50%")
        print(f"  ├─ New Risk Score: {scenario_a_risk}/100 (delta: {scenario_a_risk - original_risk:+d})")
        print(f"  ├─ New Decision: {scenario_a_class.value}")
        print(f"  └─ Changed: {'Yes' if scenario_a_class != original_class else 'No'}")

        # Scenario B: Add mitigation
        scenario_b_risk = original_risk
        scenario_b_class, _, _ = EnhancedDecisionRuleSet.classify_decision(
            risk_score=scenario_b_risk,
            has_critical_issues=params["has_critical_issues"],
            has_mitigating_factors=True,  # Changed
            requires_escalation=params["requires_escalation"],
        )
        print(f"\n  Scenario B: Add Strong Mitigating Factors")
        print(f"  ├─ New Risk Score: {scenario_b_risk}/100 (delta: 0)")
        print(f"  ├─ New Decision: {scenario_b_class.value}")
        print(f"  └─ Changed: {'Yes' if scenario_b_class != original_class else 'No'}")

        # Scenario C: Reduce all risks by 25%
        scenario_c_risk = EnhancedDecisionRuleSet.calculate_risk_score(
            financial_risk=params["financial_risk"] * 0.75,
            operational_risk=params["operational_risk"] * 0.75,
            compliance_risk=params["compliance_risk"] * 0.75,
            reputational_risk=params["reputational_risk"] * 0.75,
        )
        scenario_c_class, _, _ = EnhancedDecisionRuleSet.classify_decision(
            risk_score=scenario_c_risk,
            has_critical_issues=params["has_critical_issues"],
            has_mitigating_factors=params["has_mitigating_factors"],
            requires_escalation=params["requires_escalation"],
        )
        print(f"\n  Scenario C: Reduce All Risks by 25%")
        print(f"  ├─ New Risk Score: {scenario_c_risk}/100 (delta: {scenario_c_risk - original_risk:+d})")
        print(f"  ├─ New Decision: {scenario_c_class.value}")
        print(f"  └─ Changed: {'Yes' if scenario_c_class != original_class else 'No'}")

    def demonstrate_confidence_intervals(self):
        """Demonstrate confidence interval calculation"""
        self.print_header("FEATURE 3: CONFIDENCE INTERVAL CALCULATION", level=1)

        print("Confidence intervals provide statistical bounds on estimates:")
        print("- 95% confidence level used throughout")
        print("- Accounts for measurement uncertainty")
        print("- Shows range of plausible true values")
        print("- Helps understand estimate precision")

        scenario = self.scenarios[0]  # Low risk scenario
        params = scenario["params"]

        print(f"\n>>> Analyzing: {scenario['name']}")

        import math

        # Calculate confidence intervals for each risk factor
        sample_size = 100
        z_score = 1.96
        population_std = 20

        def calc_interval(point_est: float) -> tuple:
            se = population_std / math.sqrt(sample_size)
            moe = z_score * se
            lower = max(0, point_est - moe)
            upper = min(100, point_est + moe)
            return lower, upper, moe

        factors = {
            "Financial Risk": params["financial_risk"],
            "Operational Risk": params["operational_risk"],
            "Compliance Risk": params["compliance_risk"],
            "Reputational Risk": params["reputational_risk"],
        }

        print(f"\n  95% Confidence Intervals (sample size={sample_size}):")
        for factor_name, value in factors.items():
            lower, upper, moe = calc_interval(value)
            print(f"\n  {factor_name}: {value:.1f}")
            print(f"  ├─ Lower Bound (95%): {lower:.1f}")
            print(f"  ├─ Upper Bound (95%): {upper:.1f}")
            print(f"  └─ Margin of Error: ±{moe:.1f}")

    def demonstrate_probability_scoring(self):
        """Demonstrate decision probability scoring"""
        self.print_header("FEATURE 4: DECISION PROBABILITY SCORING", level=1)

        print("Probability scoring quantifies uncertainty in decision outcomes:")
        print("- Probability for Approve, Reject, and Review classifications")
        print("- Based on risk profile and decision history")
        print("- Entropy measure of decision uncertainty")
        print("- Shows most likely decision")

        scenarios_to_demo = [
            (self.scenarios[0], "Low Risk"),
            (self.scenarios[2], "High Risk"),
        ]

        for scenario, label in scenarios_to_demo:
            params = scenario["params"]
            print(f"\n>>> {label}: {scenario['name']}")

            from decision_synthesis_enhanced import EnhancedDecisionRuleSet

            risk_score = EnhancedDecisionRuleSet.calculate_risk_score(
                financial_risk=params["financial_risk"],
                operational_risk=params["operational_risk"],
                compliance_risk=params["compliance_risk"],
                reputational_risk=params["reputational_risk"],
            )

            # Determine risk category
            if risk_score < 50:
                base_approve, base_review, base_reject = 0.90, 0.08, 0.02
            elif risk_score < 85:
                base_approve, base_review, base_reject = 0.54, 0.40, 0.06
            else:
                base_approve, base_review, base_reject = 0.02, 0.15, 0.83

            print(f"\n  Probabilities (Risk Score: {risk_score}/100):")
            print(f"  ├─ Approve: {base_approve:.1%}")
            print(f"  ├─ Review: {base_review:.1%}")
            print(f"  └─ Reject: {base_reject:.1%}")

            import math
            entropies = [-p * math.log2(p) if p > 0 else 0 for p in [base_approve, base_review, base_reject]]
            entropy = sum(entropies)
            max_entropy = math.log2(3)
            normalized_entropy = entropy / max_entropy

            print(f"\n  Decision Uncertainty:")
            print(f"  ├─ Entropy: {normalized_entropy:.2f}/1.0")
            if normalized_entropy < 0.3:
                print(f"  └─ Assessment: Low uncertainty - confident decision")
            elif normalized_entropy < 0.7:
                print(f"  └─ Assessment: Moderate uncertainty")
            else:
                print(f"  └─ Assessment: High uncertainty - needs careful review")

    def demonstrate_bias_detection(self):
        """Demonstrate bias detection feature"""
        self.print_header("FEATURE 5: BIAS DETECTION CHECKS", level=1)

        print("Bias detection identifies potential unfairness in decision logic:")
        print("- Risk Skew: Disproportionate weighting of risk factors")
        print("- Threshold Bias: Unfair threshold application")
        print("- Factor Dominance: Single factor over-dominance")
        print("- Consistency Bias: Inconsistent rule application")
        print("- Escalation Bias: Unfair escalation criteria")

        # Demonstrate on a skewed scenario
        scenario = self.scenarios[4]  # Skewed risk profile
        params = scenario["params"]

        print(f"\n>>> Analyzing: {scenario['name']}")
        print(f"    Description: {scenario['description']}")

        risks = {
            "Financial": params["financial_risk"],
            "Operational": params["operational_risk"],
            "Compliance": params["compliance_risk"],
            "Reputational": params["reputational_risk"],
        }

        weights = {"Financial": 0.35, "Operational": 0.25, "Compliance": 0.25, "Reputational": 0.15}

        print(f"\n  Risk Distribution:")
        values = list(risks.values())
        import statistics
        mean_val = statistics.mean(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)

        for name, value in risks.items():
            print(f"  ├─ {name}: {value}")

        print(f"\n  Distribution Analysis:")
        print(f"  ├─ Mean: {mean_val:.1f}")
        print(f"  ├─ Std Dev: {std_dev:.1f}")
        print(f"  └─ Range: {max(values) - min(values)}")

        if std_dev > 25:
            print(f"\n  ⚠️ BIAS DETECTED: High risk skew")
            print(f"     Standard deviation of {std_dev:.1f} indicates unbalanced risk profile")

        # Factor dominance
        impacts = {name: risks[name] * weights[name] for name in risks}
        total_impact = sum(impacts.values())
        max_factor = max(impacts, key=impacts.get)
        max_percentage = (impacts[max_factor] / total_impact * 100) if total_impact > 0 else 0

        print(f"\n  Factor Impact Analysis:")
        for name, impact in impacts.items():
            pct = (impact / total_impact * 100) if total_impact > 0 else 0
            print(f"  ├─ {name}: {pct:.1f}%")

        if max_percentage > 45:
            print(f"\n  ⚠️ BIAS DETECTED: Factor dominance")
            print(f"     {max_factor} contributes {max_percentage:.1f}% of decision impact")
            print(f"     Risk: Decision may not consider balanced risk profile")

        print(f"\n  Recommendations:")
        print(f"  ├─ Review weight distribution across risk categories")
        print(f"  ├─ Investigate why operational risk is so elevated")
        print(f"  ├─ Consider adjusting weights if imbalance is unintentional")
        print(f"  └─ Monitor for systematic bias patterns")

    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        self.print_header("ENHANCED FEATURES SUMMARY REPORT", level=1)

        features = {
            "1. Decision Explainability": {
                "description": "Explains why decisions are made",
                "provides": [
                    "Primary decision reasons",
                    "Contributing factors analysis",
                    "Step-by-step decision path",
                    "Rule evaluation chain",
                    "Risk factor impact breakdown"
                ],
                "use_cases": [
                    "Justify decisions to stakeholders",
                    "Audit decision quality",
                    "Train decision makers",
                    "Debug decision logic"
                ]
            },
            "2. What-If Analysis": {
                "description": "Models decision changes under different conditions",
                "provides": [
                    "Scenario-based decision modeling",
                    "Sensitivity analysis",
                    "Impact quantification",
                    "Decision stability assessment",
                    "Risk mitigation planning"
                ],
                "use_cases": [
                    "Explore mitigation strategies",
                    "Assess decision sensitivity",
                    "Plan risk interventions",
                    "Evaluate alternative paths"
                ]
            },
            "3. Confidence Intervals": {
                "description": "Statistical bounds on risk estimates",
                "provides": [
                    "95% confidence bounds",
                    "Margin of error calculation",
                    "Measurement uncertainty",
                    "Estimate precision",
                    "Decision robustness"
                ],
                "use_cases": [
                    "Understand estimate precision",
                    "Account for uncertainty",
                    "Set decision thresholds",
                    "Risk management planning"
                ]
            },
            "4. Decision Probabilities": {
                "description": "Quantifies likelihood of each decision",
                "provides": [
                    "Approve/Reject/Review probabilities",
                    "Most likely decision",
                    "Decision entropy (uncertainty)",
                    "Probability distributions",
                    "Confidence assessment"
                ],
                "use_cases": [
                    "Assess decision confidence",
                    "Identify borderline cases",
                    "Plan human review allocation",
                    "Quantify decision uncertainty"
                ]
            },
            "5. Bias Detection": {
                "description": "Identifies potential unfairness in decisions",
                "detects": [
                    "Risk skew (unbalanced factors)",
                    "Threshold bias (unfair cutoffs)",
                    "Factor dominance (over-weighting)",
                    "Consistency bias (uneven rules)",
                    "Escalation bias (unfair escalation)"
                ],
                "use_cases": [
                    "Ensure decision fairness",
                    "Audit for discrimination",
                    "Improve decision consistency",
                    "Identify rule problems"
                ]
            }
        }

        for feature_name, feature_info in features.items():
            print(f"\n{feature_name}")
            print(f"{'=' * 70}")
            print(f"Description: {feature_info['description']}")

            if "provides" in feature_info:
                print(f"\nProvides:")
                for item in feature_info["provides"]:
                    print(f"  ✓ {item}")

            if "detects" in feature_info:
                print(f"\nDetects:")
                for item in feature_info["detects"]:
                    print(f"  • {item}")

            print(f"\nUse Cases:")
            for use_case in feature_info["use_cases"]:
                print(f"  → {use_case}")

    def run_full_demonstration(self):
        """Run complete demonstration of all features"""
        print("\n")
        print("=" * 80)
        print("ENHANCED DECISIONSYNTHESIS MCP SERVER - COMPLETE DEMONSTRATION".center(80))
        print("=" * 80)

        print("\nThis demo showcases 5 major enhancements to the DecisionSynthesis MCP server:")
        print("  1. Decision Explainability API")
        print("  2. What-If Analysis Tool")
        print("  3. Confidence Interval Calculation")
        print("  4. Decision Probability Scoring")
        print("  5. Bias Detection Checks")

        # Run demonstrations
        self.demonstrate_explainability()
        self.demonstrate_whatif_analysis()
        self.demonstrate_confidence_intervals()
        self.demonstrate_probability_scoring()
        self.demonstrate_bias_detection()

        # Summary
        self.generate_summary_report()

        # Usage instructions
        self.print_header("GETTING STARTED", level=1)

        print("Installation:")
        print("  pip install fastmcp pydantic")

        print("\nStarting the Enhanced Server:")
        print("  python -m decision_synthesis_enhanced")

        print("\nAPI Endpoints Available:")
        print("  • synthesize_decision() - Original decision synthesis")
        print("  • explain_decision() - Detailed explainability report")
        print("  • whatif_analysis() - What-if scenario analysis")
        print("  • calculate_confidence_intervals() - Statistical confidence bounds")
        print("  • calculate_decision_probabilities() - Decision probability scoring")
        print("  • detect_decision_biases() - Bias detection analysis")
        print("  • get_decision_rules() - View decision rules and thresholds")

        print("\nConfiguration:")
        print("  Add to your Claude or MCP client config:")
        print('  "tools": [')
        print('    {')
        print('      "name": "decision_synthesis",')
        print('      "description": "Advanced decision synthesis with explainability and analytics",')
        print('      "url": "http://localhost:8000"')
        print('    }')
        print('  ]')

        print("\n" + "=" * 80)
        print("Demonstration Complete".center(80))
        print("=" * 80 + "\n")


def main():
    """Main demonstration function"""
    # Create and run demo
    demo = EnhancedDecisionSynthesisDemo()
    demo.build_scenarios()
    demo.run_full_demonstration()


if __name__ == "__main__":
    main()
