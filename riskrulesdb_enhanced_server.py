#!/usr/bin/env python3
"""
Enhanced RiskRulesDB MCP Server - Production-Grade Financial Risk Analysis Engine
Features:
1. Configurable Risk Thresholds API - Dynamic threshold management
2. Historical Risk Trending - Time-series risk analysis
3. Anomaly Detection with ML (Simulated) - Statistical pattern recognition
4. Regulatory Rule Versioning - Version control for compliance rules
5. Custom Rule Engine Extensibility - Plugin-style rule definition
"""

import json
import logging
import sys
import hashlib
from dataclasses import dataclass, asdict, field
from typing import Any, Optional, Dict, List, Tuple, Callable
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod
import statistics
import random

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP package not installed. Install with: pip install fastmcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of detected anomalies"""
    SPENDING_SPIKE = "spending_spike"
    UNUSUAL_PATTERN = "unusual_pattern"
    HIGH_VELOCITY = "high_velocity"
    ACCOUNT_AGE = "account_age"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    INCOME_VARIANCE = "income_variance"


@dataclass
class RiskThreshold:
    """Risk threshold definition"""
    name: str
    metric: str
    low_threshold: float
    moderate_threshold: float
    high_threshold: float
    critical_threshold: float
    unit: str
    description: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RiskDataPoint:
    """Single point in risk history"""
    timestamp: str
    entity_id: str
    risk_score: float
    risk_level: str
    dti_ratio: float
    credit_score: int
    loan_amount: float
    monthly_income: float
    anomaly_count: int
    notes: str = ""


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection"""
    anomalies_detected: List[Dict[str, Any]]
    risk_score: float
    summary: str
    recommended_actions: List[str]
    ml_model_used: str = "simulated_isolation_forest"
    confidence: float = 0.95


@dataclass
class RegulatoryRule:
    """Regulatory compliance rule with versioning"""
    rule_id: str
    name: str
    description: str
    rule_type: str  # e.g., "ECOA", "FCRA", "GLBA"
    version: str
    effective_date: str
    content: Dict[str, Any]
    validation_logic: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    archived: bool = False


@dataclass
class CustomRuleDefinition:
    """Custom rule engine rule definition"""
    rule_id: str
    name: str
    description: str
    rule_type: str  # "threshold", "complex", "ml_based"
    parameters: Dict[str, Any]
    enabled: bool = True
    priority: int = 100
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# FEATURE 1: CONFIGURABLE RISK THRESHOLDS API
# ============================================================================

class ThresholdManager:
    """Manages dynamic risk thresholds"""

    def __init__(self):
        """Initialize threshold manager with default thresholds"""
        self.thresholds: Dict[str, RiskThreshold] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize default risk thresholds"""
        defaults = [
            RiskThreshold(
                name="DTI_Ratio",
                metric="debt_to_income_ratio",
                low_threshold=0.0,
                moderate_threshold=0.36,
                high_threshold=0.50,
                critical_threshold=0.75,
                unit="ratio",
                description="Debt-to-Income ratio thresholds",
            ),
            RiskThreshold(
                name="Credit_Score",
                metric="credit_score",
                low_threshold=750,
                moderate_threshold=670,
                high_threshold=580,
                critical_threshold=300,
                unit="score",
                description="Credit score thresholds",
            ),
            RiskThreshold(
                name="Loan_to_Income",
                metric="loan_to_income_ratio",
                low_threshold=0.0,
                moderate_threshold=2.5,
                high_threshold=3.5,
                critical_threshold=4.5,
                unit="ratio",
                description="Loan-to-Income ratio thresholds",
            ),
            RiskThreshold(
                name="Income_Level",
                metric="annual_income",
                low_threshold=100000,
                moderate_threshold=50000,
                high_threshold=30000,
                critical_threshold=15000,
                unit="dollars",
                description="Annual income thresholds",
            ),
        ]

        for threshold in defaults:
            self.thresholds[threshold.metric] = threshold

    def get_threshold(self, metric: str) -> Optional[RiskThreshold]:
        """Get threshold for a specific metric"""
        return self.thresholds.get(metric)

    def set_threshold(
        self,
        metric: str,
        low: float,
        moderate: float,
        high: float,
        critical: float,
    ) -> Dict[str, Any]:
        """Update threshold values"""
        if metric not in self.thresholds:
            return {
                "status": "error",
                "message": f"Metric {metric} not found",
            }

        threshold = self.thresholds[metric]
        threshold.low_threshold = low
        threshold.moderate_threshold = moderate
        threshold.high_threshold = high
        threshold.critical_threshold = critical
        threshold.updated_at = datetime.now().isoformat()

        logger.info(f"Updated threshold for {metric}")
        return {
            "status": "success",
            "metric": metric,
            "thresholds": asdict(threshold),
        }

    def add_custom_threshold(
        self,
        metric: str,
        name: str,
        low: float,
        moderate: float,
        high: float,
        critical: float,
        unit: str,
        description: str,
    ) -> Dict[str, Any]:
        """Add a new custom threshold"""
        if metric in self.thresholds:
            return {
                "status": "error",
                "message": f"Metric {metric} already exists",
            }

        threshold = RiskThreshold(
            name=name,
            metric=metric,
            low_threshold=low,
            moderate_threshold=moderate,
            high_threshold=high,
            critical_threshold=critical,
            unit=unit,
            description=description,
        )

        self.thresholds[metric] = threshold
        logger.info(f"Added custom threshold for {metric}")

        return {
            "status": "success",
            "metric": metric,
            "threshold": asdict(threshold),
        }

    def get_all_thresholds(self) -> Dict[str, Any]:
        """Get all configured thresholds"""
        return {
            "status": "success",
            "count": len(self.thresholds),
            "thresholds": {k: asdict(v) for k, v in self.thresholds.items()},
        }

    def evaluate_against_threshold(
        self, metric: str, value: float
    ) -> Tuple[str, float]:
        """Evaluate a value against thresholds"""
        threshold = self.thresholds.get(metric)
        if not threshold:
            return "unknown", 0.0

        # Determine risk level (handle inverse metrics like credit score)
        if metric == "credit_score":
            # For credit score, higher is better
            if value >= threshold.low_threshold:
                return "low", 0.1
            elif value >= threshold.moderate_threshold:
                return "moderate", 0.4
            elif value >= threshold.high_threshold:
                return "high", 0.7
            else:
                return "critical", 0.95
        else:
            # For other metrics, higher is worse
            if value <= threshold.low_threshold:
                return "low", 0.1
            elif value <= threshold.moderate_threshold:
                return "moderate", 0.4
            elif value <= threshold.high_threshold:
                return "high", 0.7
            else:
                return "critical", 0.95


# ============================================================================
# FEATURE 2: HISTORICAL RISK TRENDING
# ============================================================================

class RiskHistoryManager:
    """Manages historical risk data and trending analysis"""

    def __init__(self, max_history_points: int = 1000):
        """Initialize risk history manager"""
        self.history: List[RiskDataPoint] = []
        self.max_history_points = max_history_points
        self.entity_histories: Dict[str, List[RiskDataPoint]] = {}

    def record_risk_assessment(
        self,
        entity_id: str,
        risk_score: float,
        risk_level: str,
        dti_ratio: float,
        credit_score: int,
        loan_amount: float,
        monthly_income: float,
        anomaly_count: int,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Record a risk assessment in history"""
        data_point = RiskDataPoint(
            timestamp=datetime.now().isoformat(),
            entity_id=entity_id,
            risk_score=risk_score,
            risk_level=risk_level,
            dti_ratio=dti_ratio,
            credit_score=credit_score,
            loan_amount=loan_amount,
            monthly_income=monthly_income,
            anomaly_count=anomaly_count,
            notes=notes,
        )

        self.history.append(data_point)
        if entity_id not in self.entity_histories:
            self.entity_histories[entity_id] = []
        self.entity_histories[entity_id].append(data_point)

        # Maintain max history
        if len(self.history) > self.max_history_points:
            self.history = self.history[-self.max_history_points :]

        return {
            "status": "success",
            "entity_id": entity_id,
            "timestamp": data_point.timestamp,
        }

    def get_entity_history(
        self, entity_id: str, limit: int = 50
    ) -> Dict[str, Any]:
        """Get historical risk data for an entity"""
        history = self.entity_histories.get(entity_id, [])
        history = history[-limit:]  # Get last N records

        if not history:
            return {
                "status": "error",
                "message": f"No history found for entity {entity_id}",
            }

        return {
            "status": "success",
            "entity_id": entity_id,
            "record_count": len(history),
            "history": [asdict(h) for h in history],
        }

    def calculate_risk_trend(
        self, entity_id: str, period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate risk trend for an entity over a period"""
        history = self.entity_histories.get(entity_id, [])

        if not history:
            return {
                "status": "error",
                "message": f"No history found for entity {entity_id}",
            }

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=period_days)
        filtered = [
            h
            for h in history
            if datetime.fromisoformat(h.timestamp) >= cutoff_date
        ]

        if len(filtered) < 2:
            return {
                "status": "warning",
                "message": f"Insufficient data for trend (only {len(filtered)} records)",
            }

        # Calculate trend metrics
        risk_scores = [h.risk_score for h in filtered]
        dti_ratios = [h.dti_ratio for h in filtered]

        trend_direction = "stable"
        if len(risk_scores) >= 2:
            if risk_scores[-1] > risk_scores[0] * 1.1:
                trend_direction = "deteriorating"
            elif risk_scores[-1] < risk_scores[0] * 0.9:
                trend_direction = "improving"

        return {
            "status": "success",
            "entity_id": entity_id,
            "period_days": period_days,
            "record_count": len(filtered),
            "trend_direction": trend_direction,
            "risk_score_trend": {
                "initial": round(risk_scores[0], 3),
                "final": round(risk_scores[-1], 3),
                "change": round(risk_scores[-1] - risk_scores[0], 3),
                "min": round(min(risk_scores), 3),
                "max": round(max(risk_scores), 3),
                "average": round(statistics.mean(risk_scores), 3),
            },
            "dti_ratio_trend": {
                "initial": round(dti_ratios[0], 4),
                "final": round(dti_ratios[-1], 4),
                "change": round(dti_ratios[-1] - dti_ratios[0], 4),
                "average": round(statistics.mean(dti_ratios), 4),
            },
        }

    def get_cohort_statistics(
        self, risk_level: str, period_days: int = 30
    ) -> Dict[str, Any]:
        """Get statistics for a cohort of entities at a risk level"""
        cutoff_date = datetime.now() - timedelta(days=period_days)
        matching_records = [
            h
            for h in self.history
            if h.risk_level == risk_level
            and datetime.fromisoformat(h.timestamp) >= cutoff_date
        ]

        if not matching_records:
            return {
                "status": "error",
                "message": f"No records found for risk level {risk_level}",
            }

        risk_scores = [r.risk_score for r in matching_records]
        dti_ratios = [r.dti_ratio for r in matching_records]
        credit_scores = [r.credit_score for r in matching_records]

        return {
            "status": "success",
            "risk_level": risk_level,
            "period_days": period_days,
            "record_count": len(matching_records),
            "unique_entities": len(set(r.entity_id for r in matching_records)),
            "statistics": {
                "risk_score": {
                    "mean": round(statistics.mean(risk_scores), 3),
                    "median": round(statistics.median(risk_scores), 3),
                    "stdev": round(statistics.stdev(risk_scores), 3)
                    if len(risk_scores) > 1
                    else 0,
                    "min": round(min(risk_scores), 3),
                    "max": round(max(risk_scores), 3),
                },
                "dti_ratio": {
                    "mean": round(statistics.mean(dti_ratios), 4),
                    "median": round(statistics.median(dti_ratios), 4),
                    "min": round(min(dti_ratios), 4),
                    "max": round(max(dti_ratios), 4),
                },
                "credit_score": {
                    "mean": round(statistics.mean(credit_scores), 0),
                    "median": round(statistics.median(credit_scores), 0),
                    "min": min(credit_scores),
                    "max": max(credit_scores),
                },
            },
        }


# ============================================================================
# FEATURE 3: ANOMALY DETECTION WITH ML (SIMULATED)
# ============================================================================

class MLAnomalyDetector:
    """Simulated ML-based anomaly detection"""

    def __init__(self):
        """Initialize anomaly detector"""
        self.reference_profiles: Dict[str, Dict[str, float]] = {}

    def detect_anomalies(
        self,
        entity_id: str,
        dti_ratio: float,
        credit_score: int,
        loan_amount: float,
        monthly_income: float,
        spending_pattern: Optional[List[float]] = None,
        historical_data: Optional[List[RiskDataPoint]] = None,
    ) -> AnomalyDetectionResult:
        """Detect anomalies using simulated ML models"""
        anomalies = []
        scores = []

        # 1. Statistical Z-score anomaly detection
        if historical_data and len(historical_data) > 3:
            zscore_anomalies, zscore = self._zscore_anomaly_detection(
                dti_ratio, historical_data
            )
            anomalies.extend(zscore_anomalies)
            scores.append(zscore)

        # 2. Isolation Forest (simulated)
        isolation_score = self._simulated_isolation_forest(
            dti_ratio, credit_score, loan_amount, monthly_income
        )
        scores.append(isolation_score)

        if isolation_score > 0.7:
            anomalies.append(
                {
                    "type": AnomalyType.UNUSUAL_PATTERN.value,
                    "severity": "high",
                    "message": "Unusual financial pattern detected via isolation forest",
                    "score": round(isolation_score, 3),
                }
            )

        # 3. Spending pattern anomaly (if provided)
        if spending_pattern and len(spending_pattern) > 1:
            pattern_anomalies, pattern_score = self._spending_pattern_analysis(
                spending_pattern
            )
            anomalies.extend(pattern_anomalies)
            scores.append(pattern_score)

        # 4. Velocity detection
        velocity_anomalies = self._detect_high_velocity(
            loan_amount, monthly_income
        )
        if velocity_anomalies:
            anomalies.extend(velocity_anomalies)
            scores.append(0.6)

        # Calculate overall anomaly score
        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Generate summary and recommendations
        summary = self._generate_summary(anomalies, overall_score)
        recommendations = self._generate_recommendations(
            anomalies, overall_score
        )

        return AnomalyDetectionResult(
            anomalies_detected=anomalies,
            risk_score=round(overall_score, 3),
            summary=summary,
            recommended_actions=recommendations,
            ml_model_used="ensemble_iso_forest_zscore",
            confidence=round(min(0.95, 0.5 + overall_score / 2), 2),
        )

    def _zscore_anomaly_detection(
        self, current_value: float, historical_data: List[RiskDataPoint]
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Z-score based anomaly detection"""
        dti_values = [h.dti_ratio for h in historical_data]

        if len(dti_values) < 2:
            return [], 0.0

        mean = statistics.mean(dti_values)
        stdev = statistics.stdev(dti_values)

        if stdev == 0:
            return [], 0.0

        zscore = abs((current_value - mean) / stdev)
        anomalies = []

        if zscore > 3.0:
            anomalies.append(
                {
                    "type": AnomalyType.INCOME_VARIANCE.value,
                    "severity": "critical",
                    "message": f"Extreme deviation detected (Z-score: {zscore:.2f})",
                    "score": round(min(1.0, zscore / 5), 3),
                }
            )
        elif zscore > 2.0:
            anomalies.append(
                {
                    "type": AnomalyType.UNUSUAL_PATTERN.value,
                    "severity": "medium",
                    "message": f"Significant deviation from historical pattern (Z-score: {zscore:.2f})",
                    "score": round(zscore / 5, 3),
                }
            )

        return anomalies, min(1.0, zscore / 4)

    def _simulated_isolation_forest(
        self,
        dti_ratio: float,
        credit_score: int,
        loan_amount: float,
        monthly_income: float,
    ) -> float:
        """Simulated Isolation Forest anomaly detection"""
        # Normalize features
        features = {
            "dti": min(1.0, dti_ratio / 0.8),  # Cap at 0.8 for scoring
            "credit": (850 - credit_score) / 550,  # Inverse scoring
            "lti": min(1.0, loan_amount / (monthly_income * 60)),
        }

        # Simulated isolation paths - anomalies are isolated quickly
        isolation_score = 0.0

        # Heavy DTI
        if dti_ratio > 0.6:
            isolation_score += 0.3

        # Low credit score
        if credit_score < 500:
            isolation_score += 0.25

        # Extreme loan amount
        if monthly_income > 0 and loan_amount > monthly_income * 60:
            isolation_score += 0.2

        # Add random variance to simulate ML uncertainty
        isolation_score += random.uniform(-0.05, 0.05)

        return min(1.0, max(0.0, isolation_score))

    def _spending_pattern_analysis(
        self, spending_pattern: List[float]
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Analyze spending patterns for anomalies"""
        anomalies = []

        if len(spending_pattern) < 2:
            return [], 0.0

        # Calculate changes
        changes = [
            (spending_pattern[i] - spending_pattern[i - 1])
            / spending_pattern[i - 1]
            for i in range(1, len(spending_pattern))
            if spending_pattern[i - 1] > 0
        ]

        if not changes:
            return [], 0.0

        mean_change = statistics.mean(changes)
        avg_spend = statistics.mean(spending_pattern)

        # Detect spike
        if spending_pattern[-1] > avg_spend * 1.5:
            anomalies.append(
                {
                    "type": AnomalyType.SPENDING_SPIKE.value,
                    "severity": "medium",
                    "message": f"Recent spending spike detected: {spending_pattern[-1] / avg_spend:.1f}x average",
                    "score": 0.6,
                }
            )

        pattern_score = abs(mean_change)
        return anomalies, min(1.0, pattern_score)

    def _detect_high_velocity(
        self, loan_amount: float, monthly_income: float
    ) -> List[Dict[str, Any]]:
        """Detect high-velocity transactions/loans"""
        anomalies = []

        if monthly_income > 0:
            velocity_ratio = loan_amount / monthly_income

            if velocity_ratio > 50:  # More than 50x monthly income
                anomalies.append(
                    {
                        "type": AnomalyType.HIGH_VELOCITY.value,
                        "severity": "high",
                        "message": f"High-velocity loan request detected: {velocity_ratio:.1f}x monthly income",
                        "score": 0.7,
                    }
                )

        return anomalies

    def _generate_summary(
        self, anomalies: List[Dict[str, Any]], risk_score: float
    ) -> str:
        """Generate summary of anomalies"""
        if not anomalies:
            return "No significant anomalies detected."

        severity_counts = {}
        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        summary_parts = []
        for severity in ["critical", "high", "medium", "low"]:
            if severity in severity_counts:
                summary_parts.append(
                    f"{severity_counts[severity]} {severity} severity anomalies"
                )

        return f"Detected {', '.join(summary_parts)}. Overall anomaly risk score: {risk_score:.2f}"

    def _generate_recommendations(
        self, anomalies: List[Dict[str, Any]], risk_score: float
    ) -> List[str]:
        """Generate recommendations based on anomalies"""
        recommendations = []

        anomaly_types = {a.get("type") for a in anomalies}

        if AnomalyType.SPENDING_SPIKE.value in anomaly_types:
            recommendations.append(
                "Investigate recent spending spike - may indicate lifestyle inflation"
            )

        if AnomalyType.HIGH_VELOCITY.value in anomaly_types:
            recommendations.append(
                "Verify legitimacy of high-velocity loan request - consider fraud screening"
            )

        if AnomalyType.UNUSUAL_PATTERN.value in anomaly_types:
            recommendations.append(
                "Request additional documentation to explain unusual financial patterns"
            )

        if AnomalyType.INCOME_VARIANCE.value in anomaly_types:
            recommendations.append(
                "Verify income stability - recent changes may indicate volatility"
            )

        if risk_score > 0.7:
            recommendations.append("Escalate to senior risk officer for manual review")
            recommendations.append("Consider requesting co-signer or additional collateral")

        return recommendations


# ============================================================================
# FEATURE 4: REGULATORY RULE VERSIONING
# ============================================================================

class RegulatoryRuleManager:
    """Manages regulatory compliance rules with versioning"""

    def __init__(self):
        """Initialize regulatory rule manager"""
        self.rules: Dict[str, List[RegulatoryRule]] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default regulatory rules"""
        rules = [
            RegulatoryRule(
                rule_id="ECOA_001",
                name="Equal Credit Opportunity Act - Fair Lending",
                description="Prohibits discrimination based on protected characteristics",
                rule_type="ECOA",
                version="2.0",
                effective_date="2024-01-01",
                content={
                    "prohibited_criteria": [
                        "age",
                        "race",
                        "color",
                        "religion",
                        "national_origin",
                        "sex",
                        "marital_status",
                        "family_status",
                    ],
                    "required_disclosures": [
                        "adverse_action_notice",
                        "appraisal_copy_on_request",
                    ],
                },
            ),
            RegulatoryRule(
                rule_id="FCRA_001",
                name="Fair Credit Reporting Act - Consumer Rights",
                description="Protects consumer credit information and provides dispute rights",
                rule_type="FCRA",
                version="1.5",
                effective_date="2023-06-15",
                content={
                    "requires_disclosure": True,
                    "right_to_dispute": True,
                    "dispute_window_days": 30,
                    "credit_freeze_allowed": True,
                    "fraud_alert_available": True,
                },
            ),
            RegulatoryRule(
                rule_id="GLBA_001",
                name="Gramm-Leach-Bliley Act - Privacy",
                description="Protects nonpublic personal financial information",
                rule_type="GLBA",
                version="1.0",
                effective_date="2023-01-01",
                content={
                    "privacy_policy_required": True,
                    "opt_out_mechanism": True,
                    "data_security_standards": "PCI-DSS compliant",
                },
            ),
        ]

        for rule in rules:
            if rule.rule_type not in self.rules:
                self.rules[rule.rule_type] = []
            self.rules[rule.rule_type].append(rule)

    def get_rule_by_id(self, rule_id: str) -> Optional[RegulatoryRule]:
        """Get a specific rule by ID"""
        for rule_list in self.rules.values():
            for rule in rule_list:
                if rule.rule_id == rule_id:
                    return rule
        return None

    def get_latest_rule_version(
        self, rule_type: str
    ) -> Optional[RegulatoryRule]:
        """Get the latest version of a rule type"""
        if rule_type not in self.rules:
            return None

        rule_list = self.rules[rule_type]
        active_rules = [r for r in rule_list if not r.archived]

        return max(
            active_rules,
            key=lambda r: tuple(map(int, r.version.split("."))),
            default=None,
        )

    def create_rule_version(
        self,
        rule_id: str,
        name: str,
        description: str,
        rule_type: str,
        version: str,
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new version of a rule"""
        new_rule = RegulatoryRule(
            rule_id=f"{rule_id}_v{version}",
            name=name,
            description=description,
            rule_type=rule_type,
            version=version,
            effective_date=datetime.now().isoformat(),
            content=content,
        )

        if rule_type not in self.rules:
            self.rules[rule_type] = []

        self.rules[rule_type].append(new_rule)

        logger.info(
            f"Created new rule version: {new_rule.rule_id} version {version}"
        )

        return {
            "status": "success",
            "rule_id": new_rule.rule_id,
            "version": version,
            "created_at": new_rule.created_at,
        }

    def archive_rule_version(self, rule_id: str) -> Dict[str, Any]:
        """Archive a rule version"""
        rule = self.get_rule_by_id(rule_id)

        if not rule:
            return {
                "status": "error",
                "message": f"Rule {rule_id} not found",
            }

        rule.archived = True
        logger.info(f"Archived rule: {rule_id}")

        return {
            "status": "success",
            "rule_id": rule_id,
            "archived": True,
        }

    def get_all_active_rules(self) -> Dict[str, Any]:
        """Get all active rules"""
        active_rules = {}

        for rule_type, rule_list in self.rules.items():
            active_rules[rule_type] = [
                asdict(r) for r in rule_list if not r.archived
            ]

        return {
            "status": "success",
            "active_rule_count": sum(
                len(rules) for rules in active_rules.values()
            ),
            "rules_by_type": active_rules,
        }

    def validate_against_rules(
        self,
        entity_data: Dict[str, Any],
        rule_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate entity data against regulatory rules"""
        violations = []

        # Default to all rule types
        if not rule_types:
            rule_types = list(self.rules.keys())

        for rule_type in rule_types:
            rule = self.get_latest_rule_version(rule_type)

            if not rule:
                continue

            # Simple validation logic
            if rule_type == "ECOA":
                violations.extend(
                    self._validate_ecoa(entity_data, rule)
                )
            elif rule_type == "FCRA":
                violations.extend(
                    self._validate_fcra(entity_data, rule)
                )

        compliant = len(violations) == 0

        return {
            "status": "success",
            "compliant": compliant,
            "violations": violations,
            "validation_timestamp": datetime.now().isoformat(),
        }

    def _validate_ecoa(
        self, entity_data: Dict[str, Any], rule: RegulatoryRule
    ) -> List[str]:
        """Validate ECOA compliance"""
        violations = []
        prohibited = rule.content.get("prohibited_criteria", [])

        for criterion in prohibited:
            if criterion in entity_data and entity_data[criterion] is not None:
                # This is flagged as a potential violation if used in decision logic
                violations.append(
                    f"Potential ECOA violation: {criterion} present in decision data"
                )

        return violations

    def _validate_fcra(
        self, entity_data: Dict[str, Any], rule: RegulatoryRule
    ) -> List[str]:
        """Validate FCRA compliance"""
        violations = []

        # Check if credit file disclosure would be required
        if "credit_score" in entity_data and "disclosure_provided" not in entity_data:
            violations.append("FCRA: Credit disclosure not documented")

        return violations


# ============================================================================
# FEATURE 5: CUSTOM RULE ENGINE EXTENSIBILITY
# ============================================================================

class CustomRule(ABC):
    """Abstract base class for custom rules"""

    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Evaluate the rule against data. Returns (passes, message, score)"""
        pass


class ThresholdRule(CustomRule):
    """Custom threshold-based rule"""

    def __init__(
        self,
        rule_def: CustomRuleDefinition,
        threshold_value: float,
        comparison_operator: str,
    ):
        self.rule_def = rule_def
        self.threshold_value = threshold_value
        self.comparison_operator = comparison_operator

    def evaluate(self, data: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Evaluate threshold rule"""
        metric = self.rule_def.parameters.get("metric")
        value = data.get(metric, 0)

        operators = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
        }

        op_func = operators.get(self.comparison_operator)
        if not op_func:
            return False, "Invalid operator", 0.0

        passes = op_func(value, self.threshold_value)
        message = f"{self.rule_def.name}: {value} {self.comparison_operator} {self.threshold_value}"
        score = 0.0 if passes else 0.5

        return passes, message, score


class ComplexRule(CustomRule):
    """Complex multi-condition rule"""

    def __init__(self, rule_def: CustomRuleDefinition):
        self.rule_def = rule_def

    def evaluate(self, data: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Evaluate complex rule with multiple conditions"""
        conditions = self.rule_def.parameters.get("conditions", [])
        logic = self.rule_def.parameters.get("logic", "AND")

        results = []
        for condition in conditions:
            metric = condition.get("metric")
            operator = condition.get("operator")
            value = condition.get("value")

            data_value = data.get(metric, 0)

            operators = {
                ">": lambda a, b: a > b,
                "<": lambda a, b: a < b,
                ">=": lambda a, b: a >= b,
                "<=": lambda a, b: a <= b,
            }

            op_func = operators.get(operator)
            if op_func:
                results.append(op_func(data_value, value))

        if logic == "AND":
            passes = all(results)
        elif logic == "OR":
            passes = any(results)
        else:
            passes = True

        score = 0.0 if passes else 0.5
        message = f"{self.rule_def.name}: {'Passed' if passes else 'Failed'}"

        return passes, message, score


class CustomRuleEngine:
    """Extensible custom rule engine"""

    def __init__(self):
        """Initialize custom rule engine"""
        self.rules: Dict[str, CustomRule] = {}
        self.rule_definitions: Dict[str, CustomRuleDefinition] = {}

    def register_rule(
        self, rule_definition: CustomRuleDefinition, rule_instance: CustomRule
    ) -> Dict[str, Any]:
        """Register a custom rule"""
        self.rule_definitions[rule_definition.rule_id] = rule_definition
        self.rules[rule_definition.rule_id] = rule_instance

        logger.info(f"Registered custom rule: {rule_definition.name}")

        return {
            "status": "success",
            "rule_id": rule_definition.rule_id,
            "name": rule_definition.name,
        }

    def create_threshold_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        metric: str,
        threshold: float,
        operator: str,
    ) -> Dict[str, Any]:
        """Create and register a threshold rule"""
        rule_def = CustomRuleDefinition(
            rule_id=rule_id,
            name=name,
            description=description,
            rule_type="threshold",
            parameters={"metric": metric, "threshold": threshold, "operator": operator},
        )

        rule = ThresholdRule(rule_def, threshold, operator)
        return self.register_rule(rule_def, rule)

    def create_complex_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        conditions: List[Dict[str, Any]],
        logic: str = "AND",
    ) -> Dict[str, Any]:
        """Create and register a complex rule"""
        rule_def = CustomRuleDefinition(
            rule_id=rule_id,
            name=name,
            description=description,
            rule_type="complex",
            parameters={"conditions": conditions, "logic": logic},
        )

        rule = ComplexRule(rule_def)
        return self.register_rule(rule_def, rule)

    def evaluate_rules(
        self,
        data: Dict[str, Any],
        rule_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Evaluate rules against data"""
        rules_to_evaluate = []

        if rule_ids:
            for rule_id in rule_ids:
                if rule_id in self.rules:
                    rules_to_evaluate.append(rule_id)
        else:
            rules_to_evaluate = list(self.rules.keys())

        results = []
        total_score = 0.0

        for rule_id in rules_to_evaluate:
            rule = self.rules[rule_id]
            passes, message, score = rule.evaluate(data)

            results.append(
                {
                    "rule_id": rule_id,
                    "rule_name": self.rule_definitions[rule_id].name,
                    "passes": passes,
                    "message": message,
                    "score": score,
                }
            )

            total_score += score

        avg_score = total_score / len(results) if results else 0.0

        return {
            "status": "success",
            "rules_evaluated": len(results),
            "results": results,
            "overall_compliance_score": round(1.0 - avg_score, 3),
        }

    def get_all_rules(self) -> Dict[str, Any]:
        """Get all registered rules"""
        rules_data = []

        for rule_id, rule_def in self.rule_definitions.items():
            rules_data.append({
                "rule_id": rule_id,
                "name": rule_def.name,
                "description": rule_def.description,
                "rule_type": rule_def.rule_type,
                "enabled": rule_def.enabled,
                "priority": rule_def.priority,
                "created_at": rule_def.created_at,
            })

        return {
            "status": "success",
            "rule_count": len(rules_data),
            "rules": rules_data,
        }


# ============================================================================
# MAIN MCP SERVER
# ============================================================================

mcp = FastMCP("RiskRulesDB-Enhanced")

# Initialize managers
threshold_manager = ThresholdManager()
risk_history_manager = RiskHistoryManager()
anomaly_detector = MLAnomalyDetector()
regulatory_rule_manager = RegulatoryRuleManager()
custom_rule_engine = CustomRuleEngine()


# Feature 1: Configurable Risk Thresholds
@mcp.tool()
def configure_risk_threshold(
    metric: str,
    low_threshold: float,
    moderate_threshold: float,
    high_threshold: float,
    critical_threshold: float,
) -> Dict[str, Any]:
    """
    Configure or update risk thresholds for a specific metric.

    Args:
        metric: Metric name (e.g., 'debt_to_income_ratio', 'credit_score')
        low_threshold: Threshold for low risk
        moderate_threshold: Threshold for moderate risk
        high_threshold: Threshold for high risk
        critical_threshold: Threshold for critical risk

    Returns:
        Updated threshold configuration
    """
    return threshold_manager.set_threshold(
        metric, low_threshold, moderate_threshold, high_threshold, critical_threshold
    )


@mcp.tool()
def add_custom_risk_threshold(
    metric: str,
    name: str,
    low_threshold: float,
    moderate_threshold: float,
    high_threshold: float,
    critical_threshold: float,
    unit: str,
    description: str,
) -> Dict[str, Any]:
    """
    Add a new custom risk threshold for tracking new metrics.

    Args:
        metric: Unique metric identifier
        name: Human-readable name
        low_threshold: Threshold for low risk
        moderate_threshold: Threshold for moderate risk
        high_threshold: Threshold for high risk
        critical_threshold: Threshold for critical risk
        unit: Unit of measurement
        description: Description of the metric

    Returns:
        Newly created threshold
    """
    return threshold_manager.add_custom_threshold(
        metric, name, low_threshold, moderate_threshold, high_threshold,
        critical_threshold, unit, description
    )


@mcp.tool()
def get_all_risk_thresholds() -> Dict[str, Any]:
    """
    Retrieve all configured risk thresholds.

    Returns:
        All thresholds with current values
    """
    return threshold_manager.get_all_thresholds()


# Feature 2: Historical Risk Trending
@mcp.tool()
def record_risk_assessment(
    entity_id: str,
    risk_score: float,
    risk_level: str,
    dti_ratio: float,
    credit_score: int,
    loan_amount: float,
    monthly_income: float,
    anomaly_count: int,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Record a risk assessment in historical database.

    Args:
        entity_id: Unique entity identifier (e.g., applicant ID)
        risk_score: Overall risk score (0-1)
        risk_level: Risk level classification (low/moderate/high/critical)
        dti_ratio: Debt-to-Income ratio
        credit_score: Credit score
        loan_amount: Loan amount
        monthly_income: Monthly income
        anomaly_count: Number of detected anomalies
        notes: Optional notes

    Returns:
        Record confirmation with timestamp
    """
    return risk_history_manager.record_risk_assessment(
        entity_id, risk_score, risk_level, dti_ratio, credit_score,
        loan_amount, monthly_income, anomaly_count, notes
    )


@mcp.tool()
def get_risk_history(entity_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Retrieve historical risk assessments for an entity.

    Args:
        entity_id: Entity identifier
        limit: Maximum number of records to return

    Returns:
        Historical risk assessments
    """
    return risk_history_manager.get_entity_history(entity_id, limit)


@mcp.tool()
def calculate_risk_trend(
    entity_id: str, period_days: int = 30
) -> Dict[str, Any]:
    """
    Calculate risk trend for an entity over a time period.

    Args:
        entity_id: Entity identifier
        period_days: Number of days to analyze (default: 30)

    Returns:
        Trend analysis with direction and metrics
    """
    return risk_history_manager.calculate_risk_trend(entity_id, period_days)


@mcp.tool()
def get_cohort_statistics(
    risk_level: str, period_days: int = 30
) -> Dict[str, Any]:
    """
    Get statistics for a cohort of entities at a specific risk level.

    Args:
        risk_level: Risk level to analyze (low/moderate/high/critical)
        period_days: Time period for analysis (default: 30)

    Returns:
        Statistical analysis of the cohort
    """
    return risk_history_manager.get_cohort_statistics(risk_level, period_days)


# Feature 3: Anomaly Detection with ML
@mcp.tool()
def detect_financial_anomalies(
    entity_id: str,
    dti_ratio: float,
    credit_score: int,
    loan_amount: float,
    monthly_income: float,
    spending_pattern: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Detect anomalies in financial profile using ML (simulated).

    Uses ensemble approach:
    - Z-score statistical analysis
    - Isolation Forest (simulated)
    - Spending pattern analysis
    - Velocity detection

    Args:
        entity_id: Entity identifier
        dti_ratio: Debt-to-Income ratio
        credit_score: Credit score
        loan_amount: Loan amount
        monthly_income: Monthly income
        spending_pattern: Optional list of recent spending amounts

    Returns:
        Detected anomalies with risk scores and recommendations
    """
    # Get historical data if available
    history_result = risk_history_manager.get_entity_history(entity_id, limit=10)
    historical_data = None

    if history_result.get("status") == "success":
        historical_data = [
            RiskDataPoint(**h) for h in history_result.get("history", [])
        ]

    result = anomaly_detector.detect_anomalies(
        entity_id, dti_ratio, credit_score, loan_amount, monthly_income,
        spending_pattern, historical_data
    )

    return {
        "status": "success",
        "entity_id": entity_id,
        "anomaly_result": {
            "anomalies": result.anomalies_detected,
            "overall_risk_score": result.risk_score,
            "summary": result.summary,
            "recommendations": result.recommended_actions,
            "ml_model": result.ml_model_used,
            "confidence": result.confidence,
        }
    }


# Feature 4: Regulatory Rule Versioning
@mcp.tool()
def get_active_regulatory_rules() -> Dict[str, Any]:
    """
    Retrieve all active regulatory compliance rules.

    Returns:
        Active rules organized by type with versions
    """
    return regulatory_rule_manager.get_all_active_rules()


@mcp.tool()
def create_regulatory_rule_version(
    rule_id: str,
    name: str,
    description: str,
    rule_type: str,
    version: str,
    content: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a new version of a regulatory rule.

    Args:
        rule_id: Base rule ID
        name: Rule name
        description: Rule description
        rule_type: Type of rule (ECOA, FCRA, GLBA, etc.)
        version: Version number (e.g., "2.1")
        content: Rule content and parameters

    Returns:
        New rule version confirmation
    """
    return regulatory_rule_manager.create_rule_version(
        rule_id, name, description, rule_type, version, content
    )


@mcp.tool()
def validate_compliance(entity_data: Dict[str, Any], rule_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate entity data against regulatory rules.

    Args:
        entity_data: Entity data to validate
        rule_types: Optional list of rule types to validate against

    Returns:
        Compliance validation results with any violations
    """
    return regulatory_rule_manager.validate_against_rules(entity_data, rule_types)


# Feature 5: Custom Rule Engine
@mcp.tool()
def create_custom_threshold_rule(
    rule_id: str,
    name: str,
    description: str,
    metric: str,
    threshold: float,
    operator: str,
) -> Dict[str, Any]:
    """
    Create a custom threshold-based rule.

    Args:
        rule_id: Unique rule identifier
        name: Human-readable rule name
        description: Rule description
        metric: Metric to evaluate
        threshold: Threshold value
        operator: Comparison operator (>, <, >=, <=, ==)

    Returns:
        Registered rule confirmation
    """
    return custom_rule_engine.create_threshold_rule(
        rule_id, name, description, metric, threshold, operator
    )


@mcp.tool()
def create_custom_complex_rule(
    rule_id: str,
    name: str,
    description: str,
    conditions: List[Dict[str, Any]],
    logic: str = "AND",
) -> Dict[str, Any]:
    """
    Create a complex multi-condition rule.

    Args:
        rule_id: Unique rule identifier
        name: Human-readable rule name
        description: Rule description
        conditions: List of conditions, each with metric, operator, and value
        logic: Logical operator (AND or OR)

    Returns:
        Registered rule confirmation
    """
    return custom_rule_engine.create_complex_rule(
        rule_id, name, description, conditions, logic
    )


@mcp.tool()
def evaluate_custom_rules(
    data: Dict[str, Any], rule_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluate custom rules against data.

    Args:
        data: Data to evaluate against rules
        rule_ids: Optional list of specific rule IDs to evaluate

    Returns:
        Rule evaluation results with pass/fail status and compliance score
    """
    return custom_rule_engine.evaluate_rules(data, rule_ids)


@mcp.tool()
def get_custom_rules() -> Dict[str, Any]:
    """
    Retrieve all registered custom rules.

    Returns:
        List of all custom rules with details
    """
    return custom_rule_engine.get_all_rules()


# ============================================================================
# COMPREHENSIVE ANALYSIS TOOL
# ============================================================================

@mcp.tool()
def comprehensive_risk_analysis(
    entity_id: str,
    dti_ratio: float,
    credit_score: int,
    loan_amount: float,
    monthly_income: float,
    spending_pattern: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Perform comprehensive risk analysis using all enhanced features.

    Combines:
    1. Threshold-based risk evaluation
    2. Historical trending analysis
    3. ML-based anomaly detection
    4. Regulatory compliance checking
    5. Custom rule evaluation

    Args:
        entity_id: Entity identifier
        dti_ratio: Debt-to-Income ratio
        credit_score: Credit score
        loan_amount: Loan amount
        monthly_income: Monthly income
        spending_pattern: Optional spending pattern data

    Returns:
        Complete risk analysis across all features
    """
    timestamp = datetime.now().isoformat()
    results = {
        "status": "success",
        "entity_id": entity_id,
        "analysis_timestamp": timestamp,
        "analyses": {}
    }

    # 1. Threshold Evaluation
    dti_risk, dti_score = threshold_manager.evaluate_against_threshold(
        "debt_to_income_ratio", dti_ratio
    )
    credit_risk, credit_score_risk = threshold_manager.evaluate_against_threshold(
        "credit_score", credit_score
    )

    results["analyses"]["threshold_evaluation"] = {
        "dti": {"risk_level": dti_risk, "score": dti_score},
        "credit": {"risk_level": credit_risk, "score": credit_score_risk},
    }

    # 2. Calculate overall risk score
    overall_score = (dti_score + credit_score_risk) / 2
    overall_risk_level = "critical" if overall_score > 0.75 else \
                        "high" if overall_score > 0.50 else \
                        "moderate" if overall_score > 0.25 else "low"

    # 3. Record in history
    risk_history_manager.record_risk_assessment(
        entity_id, overall_score, overall_risk_level,
        dti_ratio, credit_score, loan_amount, monthly_income, 0
    )

    # 4. Anomaly Detection
    anomaly_result = anomaly_detector.detect_anomalies(
        entity_id, dti_ratio, credit_score, loan_amount,
        monthly_income, spending_pattern
    )

    results["analyses"]["anomaly_detection"] = {
        "anomalies": anomaly_result.anomalies_detected,
        "risk_score": anomaly_result.risk_score,
        "summary": anomaly_result.summary,
        "recommendations": anomaly_result.recommended_actions,
    }

    # 5. Trend Analysis
    trend_result = risk_history_manager.calculate_risk_trend(entity_id, 30)
    if trend_result.get("status") == "success":
        results["analyses"]["historical_trend"] = {
            "direction": trend_result.get("trend_direction"),
            "risk_change": trend_result.get("risk_score_trend", {}).get("change"),
        }

    # 6. Regulatory Compliance
    entity_data = {
        "entity_id": entity_id,
        "dti_ratio": dti_ratio,
        "credit_score": credit_score,
        "loan_amount": loan_amount,
    }

    compliance_result = regulatory_rule_manager.validate_against_rules(
        entity_data, ["ECOA", "FCRA"]
    )

    results["analyses"]["regulatory_compliance"] = {
        "compliant": compliance_result.get("compliant"),
        "violations": compliance_result.get("violations", []),
    }

    # 7. Custom Rules
    custom_rule_data = {
        "dti_ratio": dti_ratio,
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "monthly_income": monthly_income,
    }

    custom_result = custom_rule_engine.evaluate_rules(custom_rule_data)
    results["analyses"]["custom_rules"] = {
        "rules_evaluated": custom_result.get("rules_evaluated"),
        "compliance_score": custom_result.get("overall_compliance_score"),
    }

    # Final Recommendation
    final_score = (overall_score + anomaly_result.risk_score) / 2
    if final_score > 0.75 or not compliance_result.get("compliant"):
        recommendation = "DENY: Critical risk or regulatory violations"
    elif final_score > 0.50:
        recommendation = "CONDITIONAL: Review required"
    elif final_score > 0.25:
        recommendation = "APPROVE WITH MONITORING"
    else:
        recommendation = "APPROVE"

    results["final_assessment"] = {
        "overall_risk_score": round(final_score, 3),
        "overall_risk_level": overall_risk_level,
        "final_recommendation": recommendation,
    }

    return results


@mcp.tool()
def get_server_info() -> Dict[str, Any]:
    """Get enhanced server information and capabilities"""
    return {
        "name": "RiskRulesDB-Enhanced",
        "version": "2.0.0",
        "description": "Production-grade Financial Risk Analysis Engine with Advanced Features",
        "features": [
            "Configurable Risk Thresholds API",
            "Historical Risk Trending",
            "Anomaly Detection with ML (Simulated)",
            "Regulatory Rule Versioning",
            "Custom Rule Engine Extensibility",
        ],
        "tool_categories": {
            "threshold_management": [
                "configure_risk_threshold",
                "add_custom_risk_threshold",
                "get_all_risk_thresholds",
            ],
            "historical_analysis": [
                "record_risk_assessment",
                "get_risk_history",
                "calculate_risk_trend",
                "get_cohort_statistics",
            ],
            "anomaly_detection": [
                "detect_financial_anomalies",
            ],
            "regulatory_compliance": [
                "get_active_regulatory_rules",
                "create_regulatory_rule_version",
                "validate_compliance",
            ],
            "custom_rules": [
                "create_custom_threshold_rule",
                "create_custom_complex_rule",
                "evaluate_custom_rules",
                "get_custom_rules",
            ],
            "comprehensive": [
                "comprehensive_risk_analysis",
            ],
        },
        "ml_capabilities": {
            "anomaly_detection": {
                "methods": ["zscore", "isolation_forest", "spending_pattern_analysis", "velocity_detection"],
                "type": "simulated_ensemble",
                "confidence_range": "0.50-0.95",
            }
        },
    }


if __name__ == "__main__":
    logger.info("Starting RiskRulesDB Enhanced MCP Server")
    logger.info("Features: Configurable Thresholds, Historical Trending, ML Anomaly Detection, Rule Versioning, Custom Rules")
    mcp.run()
