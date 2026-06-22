"""
Advanced integration examples for DecisionSynthesis MCP server.

Demonstrates real-world usage patterns and integration scenarios.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from decision_synthesis_mcp import synthesize_decision, DecisionRuleSet


# Real-world domain models
@dataclass
class LoanApplication:
    """Loan application with risk assessment"""
    applicant_id: str
    loan_amount: float
    applicant_credit_score: int
    employment_status: str
    debt_to_income_ratio: float
    collateral_value: Optional[float] = None
    years_in_business: Optional[int] = None

    def assess_risks(self) -> Dict[str, float]:
        """Convert application attributes to risk scores"""
        financial_risk = self._calculate_financial_risk()
        operational_risk = self._calculate_operational_risk()
        compliance_risk = self._calculate_compliance_risk()
        reputational_risk = self._calculate_reputational_risk()

        return {
            "financial_risk": financial_risk,
            "operational_risk": operational_risk,
            "compliance_risk": compliance_risk,
            "reputational_risk": reputational_risk,
            "has_critical_issues": self._has_critical_issues(),
            "has_mitigating_factors": self._has_mitigating_factors(),
            "requires_escalation": self._requires_escalation(),
        }

    def _calculate_financial_risk(self) -> float:
        """Calculate financial risk based on credit score and DTI"""
        credit_risk = max(0, 100 - (self.applicant_credit_score / 8))
        dti_risk = min(100, self.debt_to_income_ratio * 10)
        return (credit_risk + dti_risk) / 2

    def _calculate_operational_risk(self) -> float:
        """Calculate operational risk based on employment stability"""
        if self.employment_status == "employed":
            return 20
        elif self.employment_status == "self_employed":
            return 50
        else:
            return 80

    def _calculate_compliance_risk(self) -> float:
        """Calculate compliance risk"""
        # Simplified: higher DTI might indicate compliance concerns
        return min(100, self.debt_to_income_ratio * 5)

    def _calculate_reputational_risk(self) -> float:
        """Calculate reputational risk"""
        if self.applicant_credit_score < 300:
            return 70
        elif self.applicant_credit_score < 600:
            return 40
        else:
            return 15

    def _has_critical_issues(self) -> bool:
        """Identify critical issues"""
        return (
            self.applicant_credit_score < 350 or
            self.debt_to_income_ratio > 0.8
        )

    def _has_mitigating_factors(self) -> bool:
        """Identify mitigating factors"""
        return (
            self.collateral_value is not None and
            self.collateral_value >= self.loan_amount * 1.2
        )

    def _requires_escalation(self) -> bool:
        """Determine if escalation required"""
        return self.debt_to_income_ratio > 0.6


@dataclass
class VendorApplication:
    """Vendor assessment with risk evaluation"""
    vendor_id: str
    company_name: str
    years_established: int
    financial_rating: str
    compliance_certifications: List[str]
    references: int
    transaction_volume: float

    def assess_risks(self) -> Dict[str, float]:
        """Convert vendor attributes to risk scores"""
        return {
            "financial_risk": self._calculate_financial_risk(),
            "operational_risk": self._calculate_operational_risk(),
            "compliance_risk": self._calculate_compliance_risk(),
            "reputational_risk": self._calculate_reputational_risk(),
            "has_critical_issues": self._has_critical_issues(),
            "has_mitigating_factors": self._has_mitigating_factors(),
            "requires_escalation": self._requires_escalation(),
        }

    def _calculate_financial_risk(self) -> float:
        """Calculate based on financial rating"""
        rating_map = {"AAA": 5, "AA": 15, "A": 25, "BBB": 50, "BB": 70, "B": 85}
        return rating_map.get(self.financial_rating, 60)

    def _calculate_operational_risk(self) -> float:
        """Calculate based on stability and years established"""
        if self.years_established < 2:
            return 70
        elif self.years_established < 5:
            return 40
        else:
            return 20

    def _calculate_compliance_risk(self) -> float:
        """Calculate based on certifications"""
        base_risk = 50
        risk_reduction = len(self.compliance_certifications) * 15
        return max(0, base_risk - risk_reduction)

    def _calculate_reputational_risk(self) -> float:
        """Calculate based on references"""
        if self.references >= 5:
            return 10
        elif self.references >= 3:
            return 30
        else:
            return 60

    def _has_critical_issues(self) -> bool:
        """Check for critical issues"""
        return (
            self.years_established < 1 or
            self.financial_rating in ["BB", "B"]
        )

    def _has_mitigating_factors(self) -> bool:
        """Check for mitigating factors"""
        return (
            len(self.compliance_certifications) >= 3 and
            self.references >= 3
        )

    def _requires_escalation(self) -> bool:
        """Check if escalation required"""
        return self.years_established < 2 or self.financial_rating == "BBB"


class DecisionWorkflow:
    """Workflow for processing decisions with DecisionSynthesis"""

    @staticmethod
    def evaluate_loan(application: LoanApplication) -> Dict[str, Any]:
        """Evaluate a loan application"""
        print(f"\n{'='*80}")
        print(f"Evaluating Loan Application: {application.applicant_id}")
        print(f"{'='*80}")

        # Assess risks
        risks = application.assess_risks()
        print(f"\nRisk Assessment:")
        for key, value in risks.items():
            if not key.startswith("has_") and key != "requires_escalation":
                print(f"  {key}: {value:.1f}")

        # Get decision
        result = synthesize_decision(**risks)

        print(f"\nDecision Result:")
        print(f"  Classification: {result.classification}")
        print(f"  Risk Score: {result.risk_score}/100")
        print(f"  Confidence: {result.confidence_level:.2%}")

        # Prepare response
        return {
            "application_id": application.applicant_id,
            "decision": result.classification,
            "risk_score": result.risk_score,
            "confidence": result.confidence_level,
            "factors": result.key_decision_factors,
            "explanation": result.explanation,
        }

    @staticmethod
    def evaluate_vendor(application: VendorApplication) -> Dict[str, Any]:
        """Evaluate a vendor application"""
        print(f"\n{'='*80}")
        print(f"Evaluating Vendor Application: {application.vendor_id}")
        print(f"Company: {application.company_name}")
        print(f"{'='*80}")

        # Assess risks
        risks = application.assess_risks()
        print(f"\nRisk Assessment:")
        for key, value in risks.items():
            if not key.startswith("has_") and key != "requires_escalation":
                print(f"  {key}: {value:.1f}")

        # Get decision
        result = synthesize_decision(**risks)

        print(f"\nDecision Result:")
        print(f"  Classification: {result.classification}")
        print(f"  Risk Score: {result.risk_score}/100")
        print(f"  Confidence: {result.confidence_level:.2%}")

        # Prepare response
        return {
            "vendor_id": application.vendor_id,
            "company_name": application.company_name,
            "decision": result.classification,
            "risk_score": result.risk_score,
            "confidence": result.confidence_level,
            "factors": result.key_decision_factors,
            "explanation": result.explanation,
        }


def demonstrate_loan_decisions():
    """Demonstrate loan decision scenarios"""
    print("\n" + "="*80)
    print("LOAN DECISION SCENARIOS")
    print("="*80)

    workflow = DecisionWorkflow()

    # Scenario 1: Good applicant (should approve)
    app1 = LoanApplication(
        applicant_id="LOAN001",
        loan_amount=50000,
        applicant_credit_score=750,
        employment_status="employed",
        debt_to_income_ratio=0.35,
        collateral_value=60000,
    )
    result1 = workflow.evaluate_loan(app1)

    # Scenario 2: Risky applicant (should review)
    app2 = LoanApplication(
        applicant_id="LOAN002",
        loan_amount=100000,
        applicant_credit_score=620,
        employment_status="self_employed",
        debt_to_income_ratio=0.65,
        collateral_value=None,
    )
    result2 = workflow.evaluate_loan(app2)

    # Scenario 3: Very risky applicant (should reject)
    app3 = LoanApplication(
        applicant_id="LOAN003",
        loan_amount=75000,
        applicant_credit_score=300,
        employment_status="unemployed",
        debt_to_income_ratio=0.85,
        collateral_value=None,
    )
    result3 = workflow.evaluate_loan(app3)

    return [result1, result2, result3]


def demonstrate_vendor_decisions():
    """Demonstrate vendor decision scenarios"""
    print("\n" + "="*80)
    print("VENDOR DECISION SCENARIOS")
    print("="*80)

    workflow = DecisionWorkflow()

    # Scenario 1: Established vendor (should approve)
    vendor1 = VendorApplication(
        vendor_id="VENDOR001",
        company_name="Acme Corp",
        years_established=10,
        financial_rating="AA",
        compliance_certifications=["ISO9001", "SOC2", "ISO27001"],
        references=5,
        transaction_volume=1000000,
    )
    result1 = workflow.evaluate_vendor(vendor1)

    # Scenario 2: New vendor with some certs (should review)
    vendor2 = VendorApplication(
        vendor_id="VENDOR002",
        company_name="StartUp Inc",
        years_established=1.5,
        financial_rating="BBB",
        compliance_certifications=["ISO9001"],
        references=2,
        transaction_volume=50000,
    )
    result2 = workflow.evaluate_vendor(vendor2)

    # Scenario 3: High-risk vendor (should reject)
    vendor3 = VendorApplication(
        vendor_id="VENDOR003",
        company_name="Risky Ltd",
        years_established=0.5,
        financial_rating="B",
        compliance_certifications=[],
        references=0,
        transaction_volume=5000,
    )
    result3 = workflow.evaluate_vendor(vendor3)

    return [result1, result2, result3]


def export_decisions(decisions: List[Dict], filename: str):
    """Export decisions to JSON"""
    with open(filename, "w") as f:
        json.dump(decisions, f, indent=2)
    print(f"\nDecisions exported to {filename}")


def main():
    """Run all demonstrations"""
    print("\n" + "="*80)
    print("DecisionSynthesis MCP - Integration Examples")
    print("="*80)

    # Run loan decisions
    loan_decisions = demonstrate_loan_decisions()

    # Run vendor decisions
    vendor_decisions = demonstrate_vendor_decisions()

    # Export results
    export_decisions(
        loan_decisions,
        "loan_decisions.json"
    )
    export_decisions(
        vendor_decisions,
        "vendor_decisions.json"
    )

    print("\n" + "="*80)
    print("Integration Examples Complete")
    print("="*80)
    print(f"\nTotal Loan Decisions: {len(loan_decisions)}")
    print(f"Total Vendor Decisions: {len(vendor_decisions)}")
    print("\nExported files:")
    print("  - loan_decisions.json")
    print("  - vendor_decisions.json")


if __name__ == "__main__":
    main()
