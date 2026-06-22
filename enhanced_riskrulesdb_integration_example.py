#!/usr/bin/env python3
"""
Integration Example: Using Enhanced RiskRulesDB in a Real Lending Workflow

This example demonstrates how to integrate the Enhanced RiskRulesDB server
into a complete lending decision pipeline with all 5 advanced features.
"""

import json
from datetime import datetime, timedelta


class EnhancedLendingWorkflow:
    """Example lending workflow using Enhanced RiskRulesDB"""

    def __init__(self):
        """Initialize the lending workflow"""
        self.applicants = []
        self.decisions = []

    def scenario_1_new_applicant_assessment(self):
        """
        Scenario 1: Complete Assessment of New Applicant

        Uses: Configurable Thresholds + ML Anomaly Detection +
              Regulatory Compliance + Custom Rules
        """
        print("\n" + "="*80)
        print("SCENARIO 1: NEW APPLICANT ASSESSMENT")
        print("="*80)

        applicant = {
            "entity_id": "applicant_20250115_001",
            "name": "John Smith",
            "application_date": datetime.now().isoformat(),
            "financial_profile": {
                "monthly_income": 5500,
                "annual_income": 66000,
                "dti_ratio": 0.35,
                "credit_score": 695,
                "loan_amount": 200000,
                "loan_purpose": "Auto Purchase",
                "existing_debts": 1925,  # Monthly
                "spending_pattern": [2200, 2300, 2250, 2400],
            }
        }

        print("\n1. STEP 1: Configure Thresholds for Auto Loan Product")
        print("-" * 60)
        print("Tool: configure_risk_threshold()")
        print("Action: Set auto loan specific DTI threshold to 0.40 (less strict than personal)")
        config_result = {
            "metric": "debt_to_income_ratio",
            "low_threshold": 0.0,
            "moderate_threshold": 0.40,  # Auto specific
            "high_threshold": 0.55,
            "critical_threshold": 0.80,
            "status": "success"
        }
        print(json.dumps(config_result, indent=2))

        print("\n2. STEP 2: Run Comprehensive Risk Analysis")
        print("-" * 60)
        print("Tool: comprehensive_risk_analysis()")
        print("Input:")
        print(json.dumps({
            "entity_id": applicant["entity_id"],
            "dti_ratio": applicant["financial_profile"]["dti_ratio"],
            "credit_score": applicant["financial_profile"]["credit_score"],
            "loan_amount": applicant["financial_profile"]["loan_amount"],
            "monthly_income": applicant["financial_profile"]["monthly_income"],
            "spending_pattern": applicant["financial_profile"]["spending_pattern"]
        }, indent=2))

        analysis_result = {
            "status": "success",
            "entity_id": applicant["entity_id"],
            "analyses": {
                "threshold_evaluation": {
                    "dti": {"risk_level": "moderate", "score": 0.38},
                    "credit": {"risk_level": "moderate", "score": 0.35}
                },
                "anomaly_detection": {
                    "anomalies_detected": [],
                    "overall_risk_score": 0.25,
                    "summary": "No significant anomalies detected",
                    "ml_model": "ensemble_iso_forest_zscore",
                    "confidence": 0.88
                },
                "regulatory_compliance": {
                    "compliant": True,
                    "violations": []
                },
                "custom_rules": {
                    "rules_evaluated": 3,
                    "compliance_score": 0.92
                }
            },
            "final_assessment": {
                "overall_risk_score": 0.33,
                "overall_risk_level": "moderate",
                "final_recommendation": "APPROVE WITH MONITORING"
            }
        }

        print("\nResult:")
        print(json.dumps(analysis_result, indent=2))

        print("\n3. STEP 3: Record Assessment in History")
        print("-" * 60)
        print("Tool: record_risk_assessment()")
        print("Action: Store for future trending analysis")
        history_record = {
            "status": "success",
            "entity_id": applicant["entity_id"],
            "timestamp": datetime.now().isoformat(),
            "note": "Initial assessment on application"
        }
        print(json.dumps(history_record, indent=2))

        print("\n4. FINAL DECISION")
        print("-" * 60)
        decision = {
            "applicant_id": applicant["entity_id"],
            "decision": "APPROVED",
            "loan_amount": applicant["financial_profile"]["loan_amount"],
            "recommended_rate": "4.25%",
            "conditions": [
                "Standard underwriting review required",
                "Verify employment",
                "Obtain homeowners insurance quote"
            ],
            "risk_assessment": analysis_result["final_assessment"]
        }
        print(json.dumps(decision, indent=2))

        return decision

    def scenario_2_portfolio_monitoring(self):
        """
        Scenario 2: Daily Portfolio Risk Monitoring

        Uses: Historical Trending + Cohort Statistics + Anomaly Detection
        """
        print("\n" + "="*80)
        print("SCENARIO 2: DAILY PORTFOLIO RISK MONITORING")
        print("="*80)

        print("\n1. DAILY BATCH: Record Today's Risk Assessments")
        print("-" * 60)
        print("Tool: record_risk_assessment() x N")

        today_records = [
            {
                "entity_id": f"applicant_daily_{i}",
                "risk_score": 0.35 + (i * 0.08),
                "risk_level": "moderate" if i < 3 else "high",
                "metrics": f"DTI: {0.35 + i*0.05}, Credit: {680 - i*20}"
            }
            for i in range(5)
        ]

        print(f"Recording {len(today_records)} assessments...")
        for rec in today_records:
            print(f"  - {rec['entity_id']}: {rec['risk_level']}")

        print("\n2. ANALYSIS: Get Cohort Statistics")
        print("-" * 60)
        print("Tool: get_cohort_statistics()")
        print("Analysis: High-risk entities over last 30 days")

        cohort_analysis = {
            "status": "success",
            "risk_level": "high",
            "period_days": 30,
            "record_count": 234,
            "unique_entities": 187,
            "statistics": {
                "risk_score": {
                    "mean": 0.68,
                    "median": 0.71,
                    "stdev": 0.12,
                    "min": 0.52,
                    "max": 0.95
                },
                "dti_ratio": {
                    "mean": 0.54,
                    "median": 0.56,
                    "min": 0.45,
                    "max": 0.82
                }
            },
            "trend_observation": "Slight increase in mean risk score (0.65 -> 0.68)",
            "alert": "High-risk portfolio growing 2% month-over-month"
        }

        print(json.dumps(cohort_analysis, indent=2))

        print("\n3. TREND ANALYSIS: Monitor Top Declining Applicants")
        print("-" * 60)
        print("Tool: calculate_risk_trend() x N")

        declining_applicants = [
            {
                "entity_id": "applicant_decline_001",
                "trend_direction": "deteriorating",
                "risk_change": 0.15,
                "initial_score": 0.35,
                "current_score": 0.50,
                "recommendation": "Manual review recommended"
            },
            {
                "entity_id": "applicant_decline_002",
                "trend_direction": "deteriorating",
                "risk_change": 0.22,
                "initial_score": 0.42,
                "current_score": 0.64,
                "recommendation": "Escalate to senior risk officer"
            }
        ]

        print(f"Identified {len(declining_applicants)} deteriorating profiles:")
        for applicant in declining_applicants:
            print(f"  - {applicant['entity_id']}: {applicant['trend_direction']}")
            print(f"    Risk change: {applicant['risk_change']:.2f} " +
                  f"({applicant['initial_score']:.2f} -> {applicant['current_score']:.2f})")
            print(f"    Action: {applicant['recommendation']}")

        print("\n4. PORTFOLIO ACTIONS")
        print("-" * 60)
        actions = [
            "Schedule review calls with 5 most-deteriorated applicants",
            "Alert portfolio managers to high-risk segment growth",
            "Review recent threshold policy changes for impact",
            "Consider proactive loss mitigation outreach"
        ]
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")

        return cohort_analysis

    def scenario_3_policy_rollout_ab_test(self):
        """
        Scenario 3: A/B Test of New Lending Policy

        Uses: Configurable Thresholds + Custom Rules + Trend Analysis
        """
        print("\n" + "="*80)
        print("SCENARIO 3: NEW POLICY A/B TEST ROLLOUT")
        print("="*80)

        print("\n BACKGROUND:")
        print("-" * 60)
        print("Goal: Tighten DTI threshold from 0.43 to 0.40 to reduce defaults")
        print("Approach: A/B test on 10% of applicants, measure impact")

        print("\n1. STEP 1: Configure New Thresholds")
        print("-" * 60)
        print("Tool: configure_risk_threshold()")

        new_config = {
            "metric": "debt_to_income_ratio",
            "old_values": {
                "moderate": 0.36,
                "high": 0.50,
                "critical": 0.75
            },
            "new_values": {
                "moderate": 0.36,
                "high": 0.40,  # TIGHTER
                "critical": 0.60  # TIGHTER
            },
            "effective_date": "2025-02-01",
            "test_percentage": 10,
            "expected_impact": "5-8% reduction in approvals"
        }

        print(json.dumps(new_config, indent=2))

        print("\n2. STEP 2: Create Test Rules")
        print("-" * 60)
        print("Tool: create_custom_complex_rule()")

        test_rules = [
            {
                "rule_id": "test_group_high_dti",
                "name": "Test Group: Strict DTI",
                "conditions": [
                    {"metric": "test_group", "operator": "==", "value": "treatment"},
                    {"metric": "dti_ratio", "operator": "<=", "value": 0.40}
                ],
                "logic": "AND",
                "purpose": "Apply strict DTI to test group only"
            },
            {
                "rule_id": "control_group_standard",
                "name": "Control Group: Standard DTI",
                "conditions": [
                    {"metric": "test_group", "operator": "==", "value": "control"},
                    {"metric": "dti_ratio", "operator": "<=", "value": 0.43}
                ],
                "logic": "AND",
                "purpose": "Keep existing standards for control"
            }
        ]

        print("Registering test rules...")
        for rule in test_rules:
            print(f"  ✓ {rule['rule_id']}: {rule['name']}")

        print("\n3. STEP 3: Daily Performance Tracking")
        print("-" * 60)
        print("Tool: get_cohort_statistics() - Compare groups")

        ab_test_results = {
            "test_period": "2025-02-01 to 2025-02-07",
            "sample_size": {
                "treatment": 523,
                "control": 4677
            },
            "results": {
                "treatment_group": {
                    "approval_rate": 0.68,
                    "avg_risk_score": 0.35,
                    "default_rate_estimate": 0.015
                },
                "control_group": {
                    "approval_rate": 0.73,
                    "avg_risk_score": 0.40,
                    "default_rate_estimate": 0.022
                }
            },
            "findings": {
                "approval_impact": "Tight DTI reduces approvals by 5%",
                "risk_improvement": "Test group has 0.05 lower average risk",
                "estimated_default_reduction": "32% fewer defaults in test group"
            }
        }

        print(json.dumps(ab_test_results, indent=2))

        print("\n4. DECISION & ROLLOUT PLAN")
        print("-" * 60)
        decision = {
            "test_outcome": "POSITIVE - Proceed with rollout",
            "findings_summary": "Tighter DTI significantly reduces portfolio risk",
            "rollout_schedule": {
                "phase_1": "Week 1-2: 25% of portfolio (low risk)",
                "phase_2": "Week 3-4: 50% of portfolio (medium risk)",
                "phase_3": "Week 5+: 100% rollout",
            },
            "monitoring": {
                "daily": "Track approval rates and risk scores",
                "weekly": "Monitor trend direction by cohort",
                "monthly": "Full statistical analysis"
            }
        }

        print(json.dumps(decision, indent=2))

        return ab_test_results

    def scenario_4_fraud_investigation(self):
        """
        Scenario 4: Fraud Investigation Workflow

        Uses: Anomaly Detection + Custom Rules + History Analysis
        """
        print("\n" + "="*80)
        print("SCENARIO 4: FRAUD INVESTIGATION WORKFLOW")
        print("="*80)

        print("\nFLAG: Unusual loan application detected")
        print("-" * 60)

        suspicious_app = {
            "entity_id": "applicant_flagged_20250115",
            "flags_triggered": [
                "HIGH_VELOCITY",
                "SPENDING_SPIKE",
                "UNUSUAL_PATTERN"
            ]
        }

        print("\n1. STEP 1: Detailed Anomaly Analysis")
        print("-" * 60)
        print("Tool: detect_financial_anomalies()")

        anomaly_result = {
            "entity_id": suspicious_app["entity_id"],
            "anomalies": [
                {
                    "type": "HIGH_VELOCITY",
                    "severity": "critical",
                    "message": "Requested loan: $500k (89x monthly income)",
                    "score": 0.85
                },
                {
                    "type": "SPENDING_SPIKE",
                    "severity": "high",
                    "message": "Spending spike from $2.5k to $6.2k in last 2 days",
                    "score": 0.72
                },
                {
                    "type": "UNUSUAL_PATTERN",
                    "severity": "medium",
                    "message": "Pattern deviation (Z-score: 3.8)",
                    "score": 0.68
                }
            ],
            "overall_risk_score": 0.75,
            "ml_model": "ensemble_iso_forest_zscore",
            "confidence": 0.94,
            "recommendations": [
                "ESCALATE TO FRAUD TEAM IMMEDIATELY",
                "Request photo ID verification",
                "Verify recent address change",
                "Contact applicant to confirm application"
            ]
        }

        print(json.dumps(anomaly_result, indent=2))

        print("\n2. STEP 2: Historical Analysis")
        print("-" * 60)
        print("Tool: get_risk_history()")

        history = {
            "entity_id": suspicious_app["entity_id"],
            "history_found": True,
            "previous_applications": 3,
            "observations": [
                "Similar pattern 6 months ago (rejected)",
                "Different email used previously",
                "Geographic inconsistencies",
                "Multiple names/SSN variations"
            ]
        }

        print("Historical record analysis:")
        for obs in history["observations"]:
            print(f"  ⚠ {obs}")

        print("\n3. STEP 3: Regulatory Rule Validation")
        print("-" * 60)
        print("Tool: validate_compliance()")

        compliance_check = {
            "ecoa_compliant": True,
            "fcra_compliant": False,
            "violations": [
                "FCRA: Credit verification procedure not followed before adverse action"
            ],
            "note": "Fraud investigation triggers FCRA requirements"
        }

        print(json.dumps(compliance_check, indent=2))

        print("\n4. FRAUD INVESTIGATION DECISION")
        print("-" * 60)
        fraud_decision = {
            "status": "FRAUD_SUSPECTED",
            "recommended_action": "DENY & INVESTIGATE",
            "reasons": [
                "Multiple high-severity anomalies",
                "Similar pattern in history",
                "Geographic red flags",
                "High ML confidence (0.94)"
            ],
            "next_steps": [
                "1. Escalate to Anti-Fraud Department",
                "2. File Suspicious Activity Report (SAR)",
                "3. Verify applicant identity",
                "4. Check against fraud databases",
                "5. Archive evidence for compliance"
            ],
            "timeline": "Complete within 24 hours"
        }

        print(json.dumps(fraud_decision, indent=2))

        return fraud_decision

    def scenario_5_regulatory_audit(self):
        """
        Scenario 5: Regulatory Compliance Audit

        Uses: Regulatory Versioning + Compliance Validation + History
        """
        print("\n" + "="*80)
        print("SCENARIO 5: REGULATORY COMPLIANCE AUDIT")
        print("="*80)

        print("\nAUDIT: Quarterly ECOA/FCRA Compliance Review")
        print("-" * 60)

        print("\n1. STEP 1: Review Active Rules")
        print("-" * 60)
        print("Tool: get_active_regulatory_rules()")

        active_rules = {
            "ECOA": {
                "current_version": "2.0",
                "effective_date": "2024-01-01",
                "last_updated": "2024-06-15",
                "status": "ACTIVE"
            },
            "FCRA": {
                "current_version": "1.5",
                "effective_date": "2023-06-15",
                "last_updated": "2024-03-01",
                "status": "ACTIVE"
            },
            "GLBA": {
                "current_version": "1.0",
                "effective_date": "2023-01-01",
                "last_updated": "2023-12-01",
                "status": "ACTIVE"
            }
        }

        print("Active Regulatory Rules:")
        print(json.dumps(active_rules, indent=2))

        print("\n2. STEP 2: Sample Validation")
        print("-" * 60)
        print("Tool: validate_compliance() x N")

        sample_validations = [
            {
                "applicant_id": "audit_sample_001",
                "ecoa_compliant": True,
                "fcra_compliant": True,
                "violations": []
            },
            {
                "applicant_id": "audit_sample_002",
                "ecoa_compliant": True,
                "fcra_compliant": True,
                "violations": []
            },
            {
                "applicant_id": "audit_sample_003",
                "ecoa_compliant": False,
                "fcra_compliant": True,
                "violations": ["Age used in credit decision model"]
            }
        ]

        print(f"Validated {len(sample_validations)} random samples")
        compliant = sum(1 for s in sample_validations if s["ecoa_compliant"] and s["fcra_compliant"])
        print(f"Compliance rate: {compliant}/{len(sample_validations)} = {100*compliant/len(sample_validations):.0f}%")

        print("\n3. STEP 3: Version History Review")
        print("-" * 60)
        print("Tool: get_active_regulatory_rules() - Version history")

        version_history = {
            "ECOA": [
                {"version": "2.0", "effective": "2024-01-01", "status": "ACTIVE"},
                {"version": "1.5", "effective": "2023-01-01", "status": "ARCHIVED"},
                {"version": "1.0", "effective": "2022-01-01", "status": "ARCHIVED"}
            ],
            "FCRA": [
                {"version": "1.5", "effective": "2023-06-15", "status": "ACTIVE"},
                {"version": "1.0", "effective": "2023-01-01", "status": "ARCHIVED"}
            ]
        }

        print("Version audit trail available for each regulation")
        print("Enables audit of decisions against rules at time of decision")

        print("\n4. AUDIT REPORT")
        print("-" * 60)
        audit_report = {
            "audit_date": datetime.now().isoformat(),
            "audit_period": "Q1 2025",
            "sample_size": len(sample_validations),
            "compliance_summary": {
                "ecoa_compliant": f"{100*compliant/len(sample_validations):.0f}%",
                "fcra_compliant": "100%",
                "overall_compliance": "97%"
            },
            "findings": [
                "✓ ECOA rules properly implemented",
                "✓ FCRA disclosure procedures followed",
                "⚠ 1 potential discrimination flag found (age in model)",
                "✓ Complete audit trail maintained"
            ],
            "recommendations": [
                "Remediate age variable in credit model",
                "Revalidate 10 applications with previous rule version",
                "Increase monitoring of ECOA compliance",
                "Continue quarterly audits"
            ],
            "certification": "Compliant with federal lending regulations (97%+ compliance rate)"
        }

        print(json.dumps(audit_report, indent=2))

        return audit_report


def main():
    """Run all scenarios"""
    print("\n" + "="*80)
    print("ENHANCED RISKRULESDB - REAL-WORLD INTEGRATION SCENARIOS")
    print("="*80)

    workflow = EnhancedLendingWorkflow()

    # Run all scenarios
    scenario_1 = workflow.scenario_1_new_applicant_assessment()
    scenario_2 = workflow.scenario_2_portfolio_monitoring()
    scenario_3 = workflow.scenario_3_policy_rollout_ab_test()
    scenario_4 = workflow.scenario_4_fraud_investigation()
    scenario_5 = workflow.scenario_5_regulatory_audit()

    # Summary
    print("\n" + "="*80)
    print("INTEGRATION SUMMARY")
    print("="*80)

    summary = {
        "scenarios_completed": 5,
        "features_demonstrated": [
            "Configurable Thresholds",
            "Historical Trending",
            "ML Anomaly Detection",
            "Regulatory Versioning",
            "Custom Rule Engine"
        ],
        "real_world_use_cases": [
            "✓ Scenario 1: New applicant assessment",
            "✓ Scenario 2: Portfolio monitoring",
            "✓ Scenario 3: Policy A/B testing",
            "✓ Scenario 4: Fraud investigation",
            "✓ Scenario 5: Regulatory audit"
        ],
        "key_benefits": [
            "Comprehensive risk assessment",
            "Data-driven policy decisions",
            "Early fraud detection",
            "Regulatory compliance automation",
            "Adaptive lending rules"
        ]
    }

    print(json.dumps(summary, indent=2))

    print("\n" + "="*80)
    print("END OF INTEGRATION EXAMPLES")
    print("="*80)


if __name__ == "__main__":
    main()
