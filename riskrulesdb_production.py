#!/usr/bin/env python3
"""
Production RiskRulesDB MCP Server
Comprehensive financial risk assessment and regulatory compliance engine

Features:
1. Configurable risk thresholds in JSON config
2. Multiple calculation methods for debt-to-income ratio
3. Industry benchmarks for credit score risk assessment
4. Statistical anomaly detection using multiple methods
5. Regulatory compliance and business rules engine
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import statistics
from enum import Enum
import math

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP package not installed. Install with: pip install fastmcp")
    sys.exit(1)


# ============================================================================
# Configuration and Constants
# ============================================================================

class RiskLevel(str, Enum):
    """Risk level classifications"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of detected anomalies"""
    SPENDING_SPIKE = "spending_spike"
    UNUSUAL_PATTERN = "unusual_pattern"
    HIGH_VELOCITY = "high_velocity"
    ACCOUNT_AGE = "account_age"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    INCOME_VARIANCE = "income_variance"


@dataclass
class DebtToIncomeResult:
    """Result of debt-to-income calculation"""
    ratio: float
    risk_level: str
    total_monthly_debt: float
    gross_monthly_income: float
    calculation_method: str
    meets_lending_standards: bool
    industry_comparison: Dict[str, Any]


@dataclass
class CreditScoreRiskResult:
    """Result of credit score risk assessment"""
    credit_score: int
    risk_level: str
    category: str
    percentile: float
    industry_benchmarks: Dict[str, Any]
    risk_factors: List[str]
    recommendation: str


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection"""
    anomalies_detected: List[Dict[str, Any]]
    risk_score: float
    summary: str
    recommended_actions: List[str]


@dataclass
class BusinessRuleResult:
    """Result of business rule application"""
    rules_applied: List[str]
    overall_compliance: bool
    violations: List[str]
    regulatory_status: Dict[str, Any]
    recommendation: str


# ============================================================================
# Risk Rules DB Server
# ============================================================================

class RiskRulesDBServer:
    """Production-grade Risk Rules Database MCP Server"""

    def __init__(self, config_path: str = "riskrulesdb_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.setup_logging()
        self.mcp = FastMCP("RiskRulesDB")
        self._register_tools()

    def setup_logging(self) -> None:
        """Configure logging"""
        log_level = self.config.get("server_config", {}).get("log_level", "INFO")
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("RiskRulesDB")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.config_path}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "server_config": {"name": "RiskRulesDB", "version": "1.0.0"},
            "risk_thresholds": {},
            "industry_benchmarks": {},
            "business_rules": {}
        }

    def _register_tools(self) -> None:
        """Register FastMCP tools"""
        self.mcp.register_tool("calculate_debt_to_income", self.calculate_debt_to_income, {
            "total_monthly_debt": {
                "type": "number",
                "description": "Total monthly debt payments in dollars"
            },
            "gross_monthly_income": {
                "type": "number",
                "description": "Gross monthly income in dollars"
            },
            "proposed_new_payment": {
                "type": "number",
                "description": "Proposed new loan payment (optional)",
                "default": 0
            },
            "calculation_method": {
                "type": "string",
                "enum": ["standard", "inclusive", "conservative"],
                "description": "Calculation method to use",
                "default": "standard"
            }
        })

        self.mcp.register_tool("assess_credit_score_risk", self.assess_credit_score_risk, {
            "credit_score": {
                "type": "integer",
                "description": "Credit score (300-850)"
            },
            "industry_type": {
                "type": "string",
                "enum": ["personal_loans", "mortgage", "auto_loan", "credit_card"],
                "description": "Type of lending industry",
                "default": "personal_loans"
            },
            "inquiries_last_6_months": {
                "type": "integer",
                "description": "Number of inquiries in last 6 months",
                "default": 0
            },
            "late_payments_last_24_months": {
                "type": "integer",
                "description": "Number of late payments in last 24 months",
                "default": 0
            }
        })

        self.mcp.register_tool("detect_financial_anomalies", self.detect_financial_anomalies, {
            "transaction_history": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "amount": {"type": "number"},
                        "category": {"type": "string"},
                        "merchant": {"type": "string"}
                    }
                },
                "description": "Recent transaction history"
            },
            "account_age_days": {
                "type": "integer",
                "description": "Age of account in days"
            },
            "baseline_monthly_spending": {
                "type": "number",
                "description": "Average monthly spending baseline"
            },
            "geographic_locations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Geographic locations of transactions"
            }
        })

        self.mcp.register_tool("apply_business_rules", self.apply_business_rules, {
            "applicant_data": {
                "type": "object",
                "description": "Applicant information"
            },
            "loan_details": {
                "type": "object",
                "description": "Loan request details"
            },
            "rules_to_apply": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific rules to apply",
                "default": ["all"]
            }
        })

    # ========================================================================
    # Tool Implementations
    # ========================================================================

    def calculate_debt_to_income(self, **kwargs) -> Dict[str, Any]:
        """Calculate debt-to-income ratio with multiple methods"""
        try:
            total_debt = kwargs.get("total_monthly_debt", 0)
            income = kwargs.get("gross_monthly_income", 0)
            proposed_payment = kwargs.get("proposed_new_payment", 0)
            method = kwargs.get("calculation_method", "standard")

            if income <= 0:
                return {
                    "error": "Invalid income amount",
                    "details": "Gross monthly income must be greater than 0"
                }

            result = self._calculate_dti(total_debt, income, proposed_payment, method)
            return asdict(result)

        except Exception as e:
            self.logger.error(f"Error calculating DTI: {e}")
            return {"error": str(e)}

    def assess_credit_score_risk(self, **kwargs) -> Dict[str, Any]:
        """Assess credit score risk with industry benchmarks"""
        try:
            credit_score = kwargs.get("credit_score")
            industry = kwargs.get("industry_type", "personal_loans")
            inquiries = kwargs.get("inquiries_last_6_months", 0)
            late_payments = kwargs.get("late_payments_last_24_months", 0)

            result = self._assess_credit_risk(
                credit_score, industry, inquiries, late_payments
            )
            return asdict(result)

        except Exception as e:
            self.logger.error(f"Error assessing credit risk: {e}")
            return {"error": str(e)}

    def detect_financial_anomalies(self, **kwargs) -> Dict[str, Any]:
        """Detect financial anomalies using statistical methods"""
        try:
            transactions = kwargs.get("transaction_history", [])
            account_age = kwargs.get("account_age_days", 0)
            baseline_spending = kwargs.get("baseline_monthly_spending", 0)
            locations = kwargs.get("geographic_locations", [])

            result = self._detect_anomalies(
                transactions, account_age, baseline_spending, locations
            )
            return asdict(result)

        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return {"error": str(e)}

    def apply_business_rules(self, **kwargs) -> Dict[str, Any]:
        """Apply regulatory and business rules"""
        try:
            applicant_data = kwargs.get("applicant_data", {})
            loan_details = kwargs.get("loan_details", {})
            rules = kwargs.get("rules_to_apply", ["all"])

            results = self._apply_rules(applicant_data, loan_details, rules)
            return results

        except Exception as e:
            self.logger.error(f"Error applying business rules: {e}")
            return {"error": str(e)}

    # ========================================================================
    # Internal Calculation Methods
    # ========================================================================

    def _calculate_dti(
        self,
        total_debt: float,
        income: float,
        proposed_payment: float = 0,
        method: str = "standard"
    ) -> DebtToIncomeResult:
        """Calculate debt-to-income ratio"""
        thresholds = self.config.get("risk_thresholds", {}).get("debt_to_income", {})

        if method == "standard":
            ratio = total_debt / income
            effective_debt = total_debt
            effective_income = income
        elif method == "inclusive":
            ratio = (total_debt + proposed_payment) / income
            effective_debt = total_debt + proposed_payment
            effective_income = income
        elif method == "conservative":
            ratio = (total_debt + proposed_payment) / (income * 0.8)
            effective_debt = total_debt + proposed_payment
            effective_income = income * 0.8
        else:
            method = "standard"
            ratio = total_debt / income
            effective_debt = total_debt
            effective_income = income

        # Determine risk level
        risk_level = self._get_dti_risk_level(ratio, thresholds)

        # Industry comparison
        industry_benchmarks = self._get_industry_comparison(ratio)

        # Check lending standards
        max_dti = self.config.get("business_rules", {}).get("lending_limits", {}).get("max_dti_ratio", 0.75)
        meets_standards = ratio <= max_dti

        return DebtToIncomeResult(
            ratio=round(ratio, 4),
            risk_level=risk_level,
            total_monthly_debt=round(effective_debt, 2),
            gross_monthly_income=round(effective_income, 2),
            calculation_method=method,
            meets_lending_standards=meets_standards,
            industry_comparison=industry_benchmarks
        )

    def _get_dti_risk_level(self, ratio: float, thresholds: Dict) -> str:
        """Determine DTI risk level"""
        if ratio <= thresholds.get("low_risk", {}).get("max_ratio", 0.36):
            return RiskLevel.LOW.value
        elif ratio <= thresholds.get("moderate_risk", {}).get("max_ratio", 0.50):
            return RiskLevel.MODERATE.value
        elif ratio <= thresholds.get("high_risk", {}).get("max_ratio", 0.75):
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.CRITICAL.value

    def _get_industry_comparison(self, dti_ratio: float) -> Dict[str, Any]:
        """Compare DTI ratio to industry benchmarks"""
        benchmarks = self.config.get("industry_benchmarks", {})
        comparison = {}

        for industry, data in benchmarks.items():
            avg_dti = data.get("avg_debt_to_income", 0)
            comparison[industry] = {
                "average_dti": avg_dti,
                "vs_applicant": round(dti_ratio - avg_dti, 4),
                "percentile_estimate": self._estimate_percentile(dti_ratio, avg_dti)
            }

        return comparison

    def _estimate_percentile(self, value: float, mean: float) -> float:
        """Estimate percentile position"""
        if value <= mean:
            return round((value / mean) * 100, 1) if mean > 0 else 0.0
        else:
            return min(100.0, round(100 + ((value - mean) / mean) * 20, 1))

    def _assess_credit_risk(
        self,
        credit_score: int,
        industry: str,
        inquiries: int,
        late_payments: int
    ) -> CreditScoreRiskResult:
        """Assess credit score risk"""
        score_ranges = self.config.get("risk_thresholds", {}).get("credit_score", {})
        benchmarks = self.config.get("industry_benchmarks", {}).get(industry, {})

        # Determine category and risk level
        category, risk_level = self._get_credit_category(credit_score, score_ranges)

        # Calculate percentile
        avg_score = benchmarks.get("avg_credit_score", 650)
        percentile = self._calculate_credit_percentile(credit_score, avg_score)

        # Identify risk factors
        risk_factors = []
        if late_payments > 0:
            risk_factors.append(f"Late payments: {late_payments} in last 24 months")
        if inquiries > 5:
            risk_factors.append(f"High inquiry rate: {inquiries} inquiries in last 6 months")
        if credit_score < 600:
            risk_factors.append("Credit score below 600 threshold")

        # Generate recommendation
        recommendation = self._get_credit_recommendation(
            risk_level, category, late_payments, inquiries
        )

        return CreditScoreRiskResult(
            credit_score=credit_score,
            risk_level=risk_level,
            category=category,
            percentile=round(percentile, 1),
            industry_benchmarks={
                "average_score": benchmarks.get("avg_credit_score"),
                "default_rate": benchmarks.get("default_rate"),
                "approval_rate": benchmarks.get("approval_rate")
            },
            risk_factors=risk_factors,
            recommendation=recommendation
        )

    def _get_credit_category(self, score: int, ranges: Dict) -> Tuple[str, str]:
        """Determine credit score category and risk level"""
        if score >= ranges.get("excellent", {}).get("min_score", 750):
            return "excellent", RiskLevel.LOW.value
        elif score >= ranges.get("good", {}).get("min_score", 670):
            return "good", RiskLevel.LOW.value
        elif score >= ranges.get("fair", {}).get("min_score", 580):
            return "fair", RiskLevel.MODERATE.value
        elif score >= ranges.get("poor", {}).get("min_score", 500):
            return "poor", RiskLevel.HIGH.value
        else:
            return "very_poor", RiskLevel.CRITICAL.value

    def _calculate_credit_percentile(self, score: int, avg: int) -> float:
        """Calculate credit score percentile"""
        if score >= 750:
            base = 80
            additional = ((score - 750) / 100) * 20
        elif score >= 700:
            base = 70
            additional = ((score - 700) / 50) * 10
        elif score >= 650:
            base = 55
            additional = ((score - 650) / 50) * 15
        else:
            base = max(1, ((score - 300) / 350) * 55)
            additional = 0

        return min(99.9, base + additional)

    def _get_credit_recommendation(
        self, risk_level: str, category: str, late_payments: int, inquiries: int
    ) -> str:
        """Generate credit-based recommendation"""
        if risk_level == RiskLevel.CRITICAL.value:
            return "Recommend rejection or require significant mitigating factors"
        elif risk_level == RiskLevel.HIGH.value:
            actions = []
            if late_payments > 0:
                actions.append("address late payment history")
            if inquiries > 5:
                actions.append("reduce inquiry volume")
            return f"Recommend additional scrutiny; applicant should {' and '.join(actions)}"
        elif risk_level == RiskLevel.MODERATE.value:
            return "Recommend standard underwriting with monitoring"
        else:
            return "Recommend approval with favorable terms"

    def _detect_anomalies(
        self,
        transactions: List[Dict],
        account_age: int,
        baseline_spending: float,
        locations: List[str]
    ) -> AnomalyDetectionResult:
        """Detect financial anomalies using statistical methods"""
        anomalies = []
        config_anomaly = self.config.get("risk_thresholds", {}).get("anomaly_detection", {})

        # Check account age
        if account_age < config_anomaly.get("account_age_alert_days", 30):
            anomalies.append({
                "type": AnomalyType.ACCOUNT_AGE.value,
                "severity": "medium",
                "description": f"New account - only {account_age} days old",
                "risk_score": 0.6
            })

        # Analyze transactions
        if transactions:
            # Spending spike detection using z-score
            amounts = [t.get("amount", 0) for t in transactions]
            if amounts and len(amounts) > 1:
                avg_transaction = statistics.mean(amounts)
                std_dev = statistics.stdev(amounts)

                spike_threshold = config_anomaly.get("transaction_spike_threshold", 2.5)
                zscore_threshold = config_anomaly.get("unusual_patterns_zscore", 3.0)

                for tx in transactions:
                    amount = tx.get("amount", 0)
                    if std_dev > 0:
                        zscore = abs((amount - avg_transaction) / std_dev)
                        if zscore >= zscore_threshold:
                            anomalies.append({
                                "type": AnomalyType.SPENDING_SPIKE.value,
                                "severity": "high",
                                "description": f"Transaction of ${amount:.2f} significantly exceeds average",
                                "transaction": tx,
                                "risk_score": min(0.95, 0.5 + (zscore / 10))
                            })

        # Geographic anomaly detection
        if locations and len(set(locations)) > 3:
            anomalies.append({
                "type": AnomalyType.GEOGRAPHIC_ANOMALY.value,
                "severity": "medium",
                "description": f"Transactions from {len(set(locations))} different locations",
                "locations": locations,
                "risk_score": 0.55
            })

        # Calculate overall risk score
        overall_risk = self._calculate_overall_anomaly_risk(anomalies)

        # Generate recommended actions
        recommended_actions = self._get_anomaly_actions(anomalies)

        return AnomalyDetectionResult(
            anomalies_detected=anomalies,
            risk_score=round(overall_risk, 3),
            summary=f"Detected {len(anomalies)} financial anomalies",
            recommended_actions=recommended_actions
        )

    def _calculate_overall_anomaly_risk(self, anomalies: List[Dict]) -> float:
        """Calculate overall anomaly risk score using weighted averaging"""
        if not anomalies:
            return 0.0

        weights = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4
        }

        weighted_scores = []
        for anomaly in anomalies:
            severity = anomaly.get("severity", "medium")
            weight = weights.get(severity, 0.7)
            weighted_scores.append(anomaly.get("risk_score", 0.5) * weight)

        return min(1.0, sum(weighted_scores) / len(weighted_scores)) if weighted_scores else 0.0

    def _get_anomaly_actions(self, anomalies: List[Dict]) -> List[str]:
        """Generate recommended actions for anomalies"""
        actions = set()

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type")
            if anomaly_type == AnomalyType.SPENDING_SPIKE.value:
                actions.add("Review recent high-value transactions for legitimacy")
            elif anomaly_type == AnomalyType.ACCOUNT_AGE.value:
                actions.add("Verify account holder identity and documentation")
            elif anomaly_type == AnomalyType.GEOGRAPHIC_ANOMALY.value:
                actions.add("Investigate geographic transaction locations")
            elif anomaly_type == AnomalyType.HIGH_VELOCITY.value:
                actions.add("Monitor for rapid transaction patterns or fraud")

        return sorted(list(actions))

    def _apply_rules(
        self,
        applicant_data: Dict,
        loan_details: Dict,
        rules: List[str]
    ) -> Dict[str, Any]:
        """Apply regulatory and business rules"""
        results = {
            "rules_applied": [],
            "overall_compliance": True,
            "violations": [],
            "regulatory_status": {},
            "recommendation": "approved"
        }

        compliance_rules = self.config.get("business_rules", {})
        lending_limits = compliance_rules.get("lending_limits", {})

        # Apply ECOA compliance
        if "all" in rules or "ecoa" in rules:
            ecoa_result = self._check_ecoa_compliance(applicant_data)
            results["rules_applied"].append("ECOA")
            if not ecoa_result["compliant"]:
                results["overall_compliance"] = False
                results["violations"].extend(ecoa_result["violations"])
            results["regulatory_status"]["ecoa"] = ecoa_result

        # Apply FCRA compliance
        if "all" in rules or "fcra" in rules:
            fcra_result = self._check_fcra_compliance(applicant_data)
            results["rules_applied"].append("FCRA")
            if not fcra_result["compliant"]:
                results["overall_compliance"] = False
                results["violations"].extend(fcra_result["violations"])
            results["regulatory_status"]["fcra"] = fcra_result

        # Apply lending limits
        if "all" in rules or "lending_limits" in rules:
            limits_result = self._check_lending_limits(applicant_data, loan_details, lending_limits)
            results["rules_applied"].append("lending_limits")
            if not limits_result["compliant"]:
                results["overall_compliance"] = False
                results["violations"].extend(limits_result["violations"])
            results["regulatory_status"]["lending_limits"] = limits_result

        # Apply fraud detection
        if "all" in rules or "fraud_detection" in rules:
            fraud_result = self._check_fraud_detection(applicant_data, loan_details)
            results["rules_applied"].append("fraud_detection")
            if not fraud_result["compliant"]:
                results["overall_compliance"] = False
                results["violations"].extend(fraud_result["violations"])
            results["regulatory_status"]["fraud_detection"] = fraud_result

        # Set recommendation
        if not results["overall_compliance"]:
            results["recommendation"] = "review_required"
            if len(results["violations"]) > 3:
                results["recommendation"] = "rejection_recommended"

        return results

    def _check_ecoa_compliance(self, applicant_data: Dict) -> Dict[str, Any]:
        """Check Equal Credit Opportunity Act compliance"""
        prohibited = self.config.get("business_rules", {}).get("regulatory_compliance", {}).get("equal_credit_opportunity_act", {}).get("prohibited_criteria", [])

        violations = []
        for criterion in prohibited:
            if criterion in applicant_data:
                violations.append(f"Prohibited criterion '{criterion}' found in decision factors")

        return {
            "compliant": len(violations) == 0,
            "rule_name": "ECOA",
            "violations": violations,
            "remediation": ["Remove protected characteristic data from decision process"] if violations else []
        }

    def _check_fcra_compliance(self, applicant_data: Dict) -> Dict[str, Any]:
        """Check Fair Credit Reporting Act compliance"""
        violations = []

        if "credit_report_used" not in applicant_data:
            violations.append("No evidence of credit report disclosure to applicant")

        return {
            "compliant": len(violations) == 0,
            "rule_name": "FCRA",
            "violations": violations,
            "remediation": ["Provide credit report disclosure", "Document right to dispute"]
        }

    def _check_lending_limits(
        self, applicant_data: Dict, loan_details: Dict, limits: Dict
    ) -> Dict[str, Any]:
        """Check lending limits"""
        violations = []

        dti = applicant_data.get("debt_to_income", 0)
        if dti > limits.get("max_dti_ratio", 0.75):
            violations.append(f"DTI {dti:.2%} exceeds maximum {limits.get('max_dti_ratio', 0.75):.2%}")

        score = applicant_data.get("credit_score", 0)
        if score < limits.get("min_credit_score", 500):
            violations.append(f"Credit score {score} below minimum {limits.get('min_credit_score', 500)}")

        income = applicant_data.get("annual_income", 0)
        if income < limits.get("minimum_income", 15000):
            violations.append(f"Annual income ${income:,.0f} below minimum ${limits.get('minimum_income', 15000):,.0f}")

        return {
            "compliant": len(violations) == 0,
            "rule_name": "Lending Limits",
            "violations": violations,
            "remediation": ["Obtain compensating factors"] if violations else []
        }

    def _check_fraud_detection(self, applicant_data: Dict, loan_details: Dict) -> Dict[str, Any]:
        """Check fraud detection rules"""
        violations = []
        fraud_score = 0.0

        if applicant_data.get("account_age_days", 0) < 30 and loan_details.get("requested_amount", 0) > 50000:
            violations.append("New account with high credit request (synthetic identity risk)")
            fraud_score += 0.3

        applications_in_period = applicant_data.get("applications_7_days", 0)
        if applications_in_period > 3:
            violations.append(f"High application velocity: {applications_in_period} applications in 7 days")
            fraud_score += 0.4

        return {
            "compliant": fraud_score < 0.5,
            "rule_name": "Fraud Detection",
            "fraud_score": fraud_score,
            "violations": violations,
            "remediation": ["Request additional verification"] if violations else []
        }

    def run(self) -> None:
        """Run the MCP server"""
        self.logger.info("Starting RiskRulesDB MCP Server")
        self.mcp.run()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    config_path = os.getenv("RISKRULESDB_CONFIG", "riskrulesdb_config.json")
    server = RiskRulesDBServer(config_path)
    server.run()


if __name__ == "__main__":
    main()
