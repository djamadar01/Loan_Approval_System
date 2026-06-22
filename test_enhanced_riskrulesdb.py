#!/usr/bin/env python3
"""
Test and demonstration file for the enhanced RiskRulesDB MCP Server.
Demonstrates all 5 new features:
1. Configurable Risk Thresholds API
2. Historical Risk Trending
3. Anomaly Detection with ML (Simulated)
4. Regulatory Rule Versioning
5. Custom Rule Engine Extensibility
"""

import json
from datetime import datetime, timedelta
import sys

# Note: In real usage, this would be called via MCP client
# This is a demonstration of the feature usage


def demonstrate_configurable_thresholds():
    """Demonstrate Feature 1: Configurable Risk Thresholds API"""
    print("\n" + "="*80)
    print("FEATURE 1: CONFIGURABLE RISK THRESHOLDS API")
    print("="*80)

    demo = {
        "description": "Dynamically configure and manage risk thresholds",
        "use_cases": [
            "Update thresholds based on regulatory changes",
            "A/B test different risk policies",
            "Support multiple loan products with different thresholds",
            "Emergency threshold adjustments during market volatility",
        ],
        "tool_calls": {
            "configure_risk_threshold": {
                "description": "Update existing threshold values",
                "example": {
                    "metric": "debt_to_income_ratio",
                    "low_threshold": 0.0,
                    "moderate_threshold": 0.40,  # Updated from 0.36
                    "high_threshold": 0.55,      # Updated from 0.50
                    "critical_threshold": 0.80,  # Updated from 0.75
                },
                "purpose": "Adapt to new regulatory requirements",
            },
            "add_custom_risk_threshold": {
                "description": "Add new custom metric thresholds",
                "example": {
                    "metric": "unemployment_rate",
                    "name": "Unemployment Risk",
                    "low_threshold": 0.02,
                    "moderate_threshold": 0.05,
                    "high_threshold": 0.08,
                    "critical_threshold": 0.12,
                    "unit": "percentage",
                    "description": "Track local unemployment as risk factor",
                },
                "purpose": "Extend risk assessment to macro indicators",
            },
            "get_all_risk_thresholds": {
                "description": "Audit all configured thresholds",
                "example": {
                    "purpose": "Verify current configuration and audit trail",
                }
            },
        }
    }

    print(json.dumps(demo, indent=2))
    return demo


def demonstrate_historical_trending():
    """Demonstrate Feature 2: Historical Risk Trending"""
    print("\n" + "="*80)
    print("FEATURE 2: HISTORICAL RISK TRENDING")
    print("="*80)

    demo = {
        "description": "Track risk metrics over time and identify trends",
        "use_cases": [
            "Detect deteriorating credit profiles before defaults",
            "Identify risk portfolio composition changes",
            "Validate effectiveness of risk policy changes",
            "Create early warning systems for portfolio risk",
            "Benchmark against industry cohorts",
        ],
        "tool_calls": {
            "record_risk_assessment": {
                "description": "Store risk assessment in time-series database",
                "example": {
                    "entity_id": "applicant_12345",
                    "risk_score": 0.42,
                    "risk_level": "moderate",
                    "dti_ratio": 0.38,
                    "credit_score": 690,
                    "loan_amount": 150000,
                    "monthly_income": 5000,
                    "anomaly_count": 1,
                    "notes": "Minor spending spike detected",
                },
                "frequency": "After each risk assessment",
            },
            "get_risk_history": {
                "description": "Retrieve historical assessments for an entity",
                "example": {
                    "entity_id": "applicant_12345",
                    "limit": 50,
                },
                "returns": "Last 50 risk assessments with timestamps",
            },
            "calculate_risk_trend": {
                "description": "Analyze trend direction and velocity",
                "example": {
                    "entity_id": "applicant_12345",
                    "period_days": 30,
                },
                "returns": {
                    "trend_direction": "deteriorating",
                    "risk_change": 0.08,
                    "statistics": "mean, median, min, max, stdev",
                }
            },
            "get_cohort_statistics": {
                "description": "Compare risk cohorts",
                "example": {
                    "risk_level": "critical",
                    "period_days": 30,
                },
                "returns": "Statistics for all critical-risk entities in last 30 days",
            },
        }
    }

    print(json.dumps(demo, indent=2))
    return demo


def demonstrate_ml_anomaly_detection():
    """Demonstrate Feature 3: Anomaly Detection with ML (Simulated)"""
    print("\n" + "="*80)
    print("FEATURE 3: ANOMALY DETECTION WITH ML (SIMULATED)")
    print("="*80)

    demo = {
        "description": "Detect unusual financial patterns using ML ensemble",
        "ml_methods": {
            "zscore": {
                "description": "Statistical anomaly detection",
                "advantage": "Fast, interpretable, no training required",
                "threshold": "Z-score > 3.0 indicates anomaly",
            },
            "isolation_forest": {
                "description": "Simulated Isolation Forest for multivariate anomalies",
                "advantage": "Detects complex patterns, handles multiple features",
                "contamination": 0.1,
            },
            "spending_pattern_analysis": {
                "description": "Detect spending spikes and pattern changes",
                "advantage": "Identifies lifestyle inflation and sudden life changes",
                "spike_threshold": "1.5x average spending",
            },
            "velocity_detection": {
                "description": "High-velocity transaction/loan detection",
                "advantage": "Fraud prevention, rapid account takeover detection",
                "threshold": "50x monthly income",
            },
        },
        "anomaly_types": {
            "SPENDING_SPIKE": "Unusual increase in spending",
            "UNUSUAL_PATTERN": "Deviation from historical behavior",
            "HIGH_VELOCITY": "Rapid or excessive transaction volume",
            "ACCOUNT_AGE": "New account behavior anomalies",
            "GEOGRAPHIC_ANOMALY": "Transactions from unusual locations",
            "INCOME_VARIANCE": "Income level changes",
        },
        "tool_calls": {
            "detect_financial_anomalies": {
                "description": "Run ML anomaly detection",
                "example": {
                    "entity_id": "applicant_12345",
                    "dti_ratio": 0.68,
                    "credit_score": 485,
                    "loan_amount": 500000,
                    "monthly_income": 4500,
                    "spending_pattern": [2000, 2100, 2150, 5800],  # Spike!
                },
                "returns": {
                    "anomalies": [
                        {
                            "type": "spending_spike",
                            "severity": "high",
                            "message": "Recent spending spike: 2.7x average",
                            "score": 0.6,
                        }
                    ],
                    "overall_risk_score": 0.72,
                    "ml_model": "ensemble_iso_forest_zscore",
                    "confidence": 0.92,
                }
            }
        }
    }

    print(json.dumps(demo, indent=2))
    return demo


def demonstrate_regulatory_versioning():
    """Demonstrate Feature 4: Regulatory Rule Versioning"""
    print("\n" + "="*80)
    print("FEATURE 4: REGULATORY RULE VERSIONING")
    print("="*80)

    demo = {
        "description": "Version control for regulatory compliance rules",
        "use_cases": [
            "Track regulatory rule changes over time",
            "Maintain audit trail of compliance updates",
            "Support gradual rollout of new rules",
            "Archive outdated rules for historical reference",
            "Validate decisions against rule version at time of decision",
        ],
        "default_rules": [
            {
                "id": "ECOA_001",
                "name": "Equal Credit Opportunity Act",
                "version": "2.0",
                "description": "Prohibits discrimination in credit decisions",
            },
            {
                "id": "FCRA_001",
                "name": "Fair Credit Reporting Act",
                "version": "1.5",
                "description": "Consumer credit reporting protections",
            },
            {
                "id": "GLBA_001",
                "name": "Gramm-Leach-Bliley Act",
                "version": "1.0",
                "description": "Privacy protection for financial information",
            },
        ],
        "tool_calls": {
            "get_active_regulatory_rules": {
                "description": "Retrieve all active compliance rules",
                "returns": "Rules organized by type with version history",
            },
            "create_regulatory_rule_version": {
                "description": "Create new rule version",
                "example": {
                    "rule_id": "ECOA",
                    "version": "3.0",
                    "effective_date": "2025-01-01",
                    "content": {
                        "prohibited_criteria": ["age", "race", "color", "religion", "national_origin"],
                        "new_requirement": "Algorithmic bias testing",
                    }
                }
            },
            "validate_compliance": {
                "description": "Check entity against current rules",
                "example": {
                    "entity_data": {
                        "entity_id": "applicant_12345",
                        "dti_ratio": 0.38,
                        "credit_score": 690,
                    },
                    "rule_types": ["ECOA", "FCRA"],
                },
                "returns": {
                    "compliant": True,
                    "violations": [],
                }
            },
        }
    }

    print(json.dumps(demo, indent=2))
    return demo


def demonstrate_custom_rule_engine():
    """Demonstrate Feature 5: Custom Rule Engine Extensibility"""
    print("\n" + "="*80)
    print("FEATURE 5: CUSTOM RULE ENGINE EXTENSIBILITY")
    print("="*80)

    demo = {
        "description": "Plugin-style custom rule engine for business logic",
        "use_cases": [
            "Implement product-specific rules",
            "Support rapid rule changes without code deployment",
            "Enable business teams to define rules",
            "Create complex multi-condition logic",
            "Support A/B testing of rule variations",
        ],
        "rule_types": {
            "threshold": "Simple threshold-based conditions",
            "complex": "Multi-condition logic with AND/OR",
            "ml_based": "ML model-based rules (extensible)",
        },
        "tool_calls": {
            "create_custom_threshold_rule": {
                "description": "Create threshold-based rule",
                "example": {
                    "rule_id": "max_debt_to_income",
                    "name": "Maximum DTI for Personal Loans",
                    "metric": "dti_ratio",
                    "threshold": 0.43,
                    "operator": "<=",
                },
                "effect": "Reject if DTI > 43%",
            },
            "create_custom_complex_rule": {
                "description": "Create complex multi-condition rule",
                "example": {
                    "rule_id": "high_risk_profile",
                    "name": "High Risk Profile",
                    "conditions": [
                        {
                            "metric": "dti_ratio",
                            "operator": ">",
                            "value": 0.50,
                        },
                        {
                            "metric": "credit_score",
                            "operator": "<",
                            "value": 600,
                        },
                    ],
                    "logic": "AND",
                },
                "effect": "Triggers if BOTH conditions true",
            },
            "evaluate_custom_rules": {
                "description": "Evaluate rules against data",
                "example": {
                    "data": {
                        "dti_ratio": 0.55,
                        "credit_score": 580,
                        "loan_amount": 100000,
                    },
                    "rule_ids": ["max_debt_to_income", "high_risk_profile"],
                },
                "returns": {
                    "rules_evaluated": 2,
                    "results": [
                        {
                            "rule_id": "max_debt_to_income",
                            "passes": False,
                            "message": "DTI 0.55 > 0.43",
                        }
                    ],
                    "overall_compliance_score": 0.5,
                }
            },
            "get_custom_rules": {
                "description": "List all registered custom rules",
                "returns": "All rules with priority and status",
            },
        }
    }

    print(json.dumps(demo, indent=2))
    return demo


def demonstrate_comprehensive_analysis():
    """Demonstrate the Comprehensive Analysis Tool"""
    print("\n" + "="*80)
    print("COMPREHENSIVE RISK ANALYSIS (All Features Combined)")
    print("="*80)

    demo = {
        "description": "Single tool that orchestrates all 5 features",
        "tool": "comprehensive_risk_analysis",
        "input": {
            "entity_id": "applicant_98765",
            "dti_ratio": 0.42,
            "credit_score": 675,
            "loan_amount": 200000,
            "monthly_income": 5200,
            "spending_pattern": [3200, 3400, 3600, 4800],
        },
        "analysis_steps": [
            "Step 1: Evaluate against configurable thresholds",
            "Step 2: Record in historical database and calculate trends",
            "Step 3: Run ML anomaly detection ensemble",
            "Step 4: Validate regulatory compliance",
            "Step 5: Evaluate custom business rules",
            "Step 6: Synthesize all into final recommendation",
        ],
        "sample_output": {
            "status": "success",
            "entity_id": "applicant_98765",
            "analyses": {
                "threshold_evaluation": {
                    "dti": {"risk_level": "moderate", "score": 0.40},
                    "credit": {"risk_level": "moderate", "score": 0.40},
                },
                "anomaly_detection": {
                    "anomalies": [
                        {
                            "type": "spending_spike",
                            "severity": "medium",
                            "message": "Recent spending spike: 1.3x average",
                        }
                    ],
                    "risk_score": 0.35,
                },
                "historical_trend": {
                    "direction": "stable",
                    "risk_change": 0.02,
                },
                "regulatory_compliance": {
                    "compliant": True,
                    "violations": [],
                },
                "custom_rules": {
                    "rules_evaluated": 4,
                    "compliance_score": 0.85,
                },
            },
            "final_assessment": {
                "overall_risk_score": 0.38,
                "overall_risk_level": "moderate",
                "final_recommendation": "APPROVE WITH MONITORING",
            }
        }
    }

    print(json.dumps(demo, indent=2))
    return demo


def demonstrate_integration_scenarios():
    """Demonstrate real-world integration scenarios"""
    print("\n" + "="*80)
    print("REAL-WORLD INTEGRATION SCENARIOS")
    print("="*80)

    scenarios = {
        "Scenario 1: Policy Change Rollout": {
            "description": "Rolling out stricter lending standards",
            "steps": [
                "1. Create new rule version: configure_risk_threshold()",
                "2. A/B test on subset: evaluate_custom_rules()",
                "3. Monitor cohort stats: get_cohort_statistics()",
                "4. Gradual rollout: Archive old rule version",
                "5. Audit impact: calculate_risk_trend()",
            ],
        },
        "Scenario 2: Portfolio Risk Monitoring": {
            "description": "Early warning system for deteriorating portfolios",
            "steps": [
                "1. Record all assessments: record_risk_assessment()",
                "2. Daily cohort analysis: get_cohort_statistics('high')",
                "3. Trend detection: calculate_risk_trend()",
                "4. Alert on deterioration: If trend_direction = 'deteriorating'",
                "5. Manual review: Escalate for underwriter review",
            ],
        },
        "Scenario 3: Fraud Detection": {
            "description": "Detecting suspicious account activity",
            "steps": [
                "1. Monitor velocity: detect_financial_anomalies()",
                "2. Pattern analysis: ML anomaly detection catches anomalies",
                "3. Rule triggers: Custom rule for velocity > threshold",
                "4. Complex logic: Multiple indicators trigger review",
                "5. Investigation: Pass to fraud team with full context",
            ],
        },
        "Scenario 4: Regulatory Audit": {
            "description": "Ensuring ECOA/FCRA compliance",
            "steps": [
                "1. Get active rules: get_active_regulatory_rules()",
                "2. Validate sample: validate_compliance(entity_data)",
                "3. Historical audit: Review rule versions over time",
                "4. Document compliance: Archive version used per decision",
                "5. Report findings: Show version history and validation",
            ],
        },
    }

    print(json.dumps(scenarios, indent=2))
    return scenarios


def generate_feature_summary():
    """Generate summary of all features"""
    print("\n" + "="*80)
    print("ENHANCED RISKRULESDB - FEATURE SUMMARY")
    print("="*80)

    summary = {
        "server_name": "RiskRulesDB-Enhanced",
        "version": "2.0.0",
        "release_date": datetime.now().isoformat(),
        "features": {
            "1_configurable_thresholds": {
                "tools": 3,
                "capabilities": [
                    "Dynamic threshold configuration",
                    "Custom metric support",
                    "Multi-product configurations",
                    "Threshold audit trail",
                ],
                "benefit": "Adapt to regulatory changes without code deployment",
            },
            "2_historical_trending": {
                "tools": 4,
                "capabilities": [
                    "Time-series risk storage",
                    "Entity history tracking",
                    "Trend analysis and forecasting",
                    "Cohort statistics",
                ],
                "benefit": "Early warning system for portfolio deterioration",
            },
            "3_ml_anomaly_detection": {
                "tools": 1,
                "capabilities": [
                    "Ensemble ML methods",
                    "Z-score analysis",
                    "Isolation Forest (simulated)",
                    "Spending pattern analysis",
                    "Velocity detection",
                    "Confidence scoring",
                ],
                "benefit": "Detect fraud and unusual patterns automatically",
            },
            "4_regulatory_versioning": {
                "tools": 3,
                "capabilities": [
                    "Rule version control",
                    "Multiple regulation support (ECOA, FCRA, GLBA)",
                    "Archive historical versions",
                    "Compliance validation",
                ],
                "benefit": "Maintain audit trail and support regulatory changes",
            },
            "5_custom_rule_engine": {
                "tools": 4,
                "capabilities": [
                    "Threshold-based rules",
                    "Complex multi-condition logic",
                    "Plugin-style extensibility",
                    "Rule priority management",
                ],
                "benefit": "Enable business teams to implement rules without developers",
            },
        },
        "total_tools": 15,
        "deployment_model": "MCP Server (FastMCP)",
        "ml_approach": "Simulated Ensemble (Ready for real ML integration)",
    }

    print(json.dumps(summary, indent=2))
    return summary


def main():
    """Run all demonstrations"""
    print("\n" + "="*80)
    print("ENHANCED RISKRULESDB MCP SERVER - COMPREHENSIVE DEMONSTRATION")
    print("="*80)

    # Run all demonstrations
    demonstrate_configurable_thresholds()
    demonstrate_historical_trending()
    demonstrate_ml_anomaly_detection()
    demonstrate_regulatory_versioning()
    demonstrate_custom_rule_engine()
    demonstrate_comprehensive_analysis()
    demonstrate_integration_scenarios()
    summary = generate_feature_summary()

    # Print usage guide
    print("\n" + "="*80)
    print("USAGE GUIDE")
    print("="*80)

    usage = {
        "quick_start": {
            "1_configure_thresholds": "configure_risk_threshold(metric='debt_to_income_ratio', ...)",
            "2_record_history": "record_risk_assessment(entity_id='app_123', ...)",
            "3_detect_anomalies": "detect_financial_anomalies(entity_id='app_123', ...)",
            "4_check_compliance": "validate_compliance(entity_data={...})",
            "5_run_custom_rules": "evaluate_custom_rules(data={...})",
        },
        "comprehensive": "comprehensive_risk_analysis(entity_id='app_123', ...) - Runs all above!",
        "server_info": "get_server_info() - Get all available tools",
    }

    print(json.dumps(usage, indent=2))

    print("\n" + "="*80)
    print("DEPLOYMENT INSTRUCTIONS")
    print("="*80)

    deployment = {
        "local_testing": {
            "1_install": "pip install fastmcp",
            "2_run": "python riskrulesdb_enhanced_server.py",
            "3_test": "python test_enhanced_riskrulesdb.py",
        },
        "mcp_client_integration": {
            "config": "Add to Claude settings.json or MCP client config",
            "example": {
                "command": "python",
                "args": ["riskrulesdb_enhanced_server.py"],
            }
        },
        "documentation": "See tool docstrings for complete parameter documentation",
    }

    print(json.dumps(deployment, indent=2))

    print("\n" + "="*80)
    print("KEY IMPROVEMENTS SUMMARY")
    print("="*80)

    improvements = [
        "✓ Feature 1: Configurable Risk Thresholds - Dynamic policy management",
        "✓ Feature 2: Historical Risk Trending - Time-series analysis and early warnings",
        "✓ Feature 3: ML Anomaly Detection - Ensemble methods for pattern recognition",
        "✓ Feature 4: Regulatory Versioning - Version control for compliance rules",
        "✓ Feature 5: Custom Rule Engine - Extensible rule framework for business logic",
        "✓ Comprehensive Analysis Tool - Orchestrates all features in one call",
        "✓ Production-Ready - Includes error handling, validation, and logging",
        "✓ Scalable - Simulated ML ready for real integration",
        "✓ Audit Trail - Full history for compliance and monitoring",
        "✓ Extensible - Plugin architecture for custom requirements",
    ]

    for improvement in improvements:
        print(improvement)

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
