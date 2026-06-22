"""
Complete Loan Decision Workflow

This demonstrates the full workflow integrating:
1. ApplicantProfileAgent - fetches applicant information
2. FinancialRiskAgent - analyzes financial risk
3. LoanDecisionAgent - synthesizes final decision

This shows how multiple agents work together to produce a loan decision.
"""

import asyncio
from typing import Dict, Any
from dataclasses import dataclass
import datetime


# ============================================================================
# Workflow Data Classes
# ============================================================================


@dataclass
class WorkflowInput:
    """Input data for complete workflow."""
    applicant_id: str
    credit_score: int
    monthly_gross_income: float
    monthly_debt_payments: float
    loan_amount: float


@dataclass
class RiskAssessmentOutput:
    """Risk assessment output from agents."""
    financial_risk: float  # 0-100
    operational_risk: float  # 0-100
    compliance_risk: float  # 0-100
    reputational_risk: float  # 0-100
    has_critical_issues: bool
    has_mitigating_factors: bool


@dataclass
class WorkflowResult:
    """Final workflow result with decision and trace."""
    applicant_id: str
    final_decision: str  # Approve/Reject/Review
    risk_score: int
    confidence_level: float
    key_factors: list
    explanation: str
    risk_assessments: RiskAssessmentOutput
    workflow_status: str  # success/failure
    timestamp: str


# ============================================================================
# Simulated Agents (Mock Implementations)
# ============================================================================


class ApplicantProfileAgentMock:
    """Mock ApplicantProfileAgent for demonstration."""

    async def fetch_profile(self, applicant_id: str) -> Dict[str, Any]:
        """Fetch applicant profile."""
        return {
            "applicant_id": applicant_id,
            "name": f"Applicant {applicant_id}",
            "employment_status": "employed",
            "employment_history_years": 5,
            "monthly_income_stability": 0.85,
            "recent_delinquencies": 0,
            "credit_score": 750,
        }


class FinancialRiskAgentMock:
    """Mock FinancialRiskAgent for demonstration."""

    async def assess_financial_risk(
        self,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
    ) -> Dict[str, Any]:
        """Assess financial risk."""
        # Simplified DTI calculation
        dti = (monthly_debt_payments + (loan_amount / 12 / 360)) / monthly_gross_income

        # Risk factors
        credit_risk = max(0, 100 - (credit_score - 300) / 5.5)  # 300-850 -> 0-100
        dti_risk = min(100, dti * 100)  # Convert ratio to percentage

        financial_risk = (credit_risk * 0.4 + dti_risk * 0.6)

        return {
            "financial_risk": financial_risk,
            "credit_score": credit_score,
            "dti_ratio": dti,
            "credit_risk_component": credit_risk,
            "dti_risk_component": dti_risk,
            "recommendation": "good" if financial_risk < 50 else "review",
        }


class ComplianceAgentMock:
    """Mock ComplianceAgent for demonstration."""

    async def assess_compliance_risk(self, applicant_id: str) -> Dict[str, Any]:
        """Assess compliance risk."""
        import random

        # Simplified compliance risk assessment
        compliance_risk = random.uniform(10, 40)
        critical_issues = compliance_risk > 35

        return {
            "compliance_risk": compliance_risk,
            "critical_issues": critical_issues,
            "aml_screening": "pass" if compliance_risk < 30 else "review",
            "sanctions_screening": "pass",
        }


class OperationalRiskAgentMock:
    """Mock OperationalRiskAgent for demonstration."""

    async def assess_operational_risk(self, applicant_id: str) -> Dict[str, Any]:
        """Assess operational risk."""
        import random

        operational_risk = random.uniform(15, 45)
        mitigating_factors = random.choice([True, False])

        return {
            "operational_risk": operational_risk,
            "mitigating_factors": mitigating_factors,
            "process_risks": "standard",
            "escalation_required": operational_risk > 40,
        }


class ReputationAgentMock:
    """Mock ReputationAgent for demonstration."""

    async def assess_reputational_risk(self, applicant_id: str) -> Dict[str, Any]:
        """Assess reputational risk."""
        import random

        reputational_risk = random.uniform(5, 30)

        return {
            "reputational_risk": reputational_risk,
            "negative_news": reputational_risk > 25,
            "industry_risk": "standard",
        }


# ============================================================================
# Main Workflow Orchestrator
# ============================================================================


class LoanDecisionWorkflow:
    """
    Orchestrates the complete loan decision workflow.

    Integrates multiple agents to produce a final loan decision with
    explainable factors and audit trail.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize workflow.

        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose

        # Initialize mock agents
        self.profile_agent = ApplicantProfileAgentMock()
        self.financial_agent = FinancialRiskAgentMock()
        self.compliance_agent = ComplianceAgentMock()
        self.operational_agent = OperationalRiskAgentMock()
        self.reputation_agent = ReputationAgentMock()

    def _log(self, message: str) -> None:
        """Log message if verbose."""
        if self.verbose:
            print(f"[WORKFLOW] {message}")

    async def process_application(
        self,
        applicant_id: str,
        credit_score: int,
        monthly_gross_income: float,
        monthly_debt_payments: float,
        loan_amount: float,
    ) -> WorkflowResult:
        """
        Process a loan application through the complete workflow.

        Args:
            applicant_id: Unique applicant identifier
            credit_score: Credit score (300-850)
            monthly_gross_income: Monthly gross income
            monthly_debt_payments: Monthly debt payments
            loan_amount: Requested loan amount

        Returns:
            WorkflowResult with final decision and trace
        """
        self._log(f"Starting workflow for applicant {applicant_id}")

        try:
            # Step 1: Fetch applicant profile
            self._log("Step 1/6: Fetching applicant profile")
            profile = await self.profile_agent.fetch_profile(applicant_id)
            self._log(f"  Profile retrieved: {profile['name']}")

            # Step 2: Assess financial risk
            self._log("Step 2/6: Assessing financial risk")
            financial_risk_result = await self.financial_agent.assess_financial_risk(
                credit_score=credit_score,
                monthly_gross_income=monthly_gross_income,
                monthly_debt_payments=monthly_debt_payments,
                loan_amount=loan_amount,
            )
            financial_risk = financial_risk_result["financial_risk"]
            self._log(f"  Financial Risk Score: {financial_risk:.1f}/100")

            # Step 3: Assess compliance risk
            self._log("Step 3/6: Assessing compliance risk")
            compliance_result = await self.compliance_agent.assess_compliance_risk(
                applicant_id
            )
            compliance_risk = compliance_result["compliance_risk"]
            self._log(f"  Compliance Risk Score: {compliance_risk:.1f}/100")

            # Step 4: Assess operational risk
            self._log("Step 4/6: Assessing operational risk")
            operational_result = await self.operational_agent.assess_operational_risk(
                applicant_id
            )
            operational_risk = operational_result["operational_risk"]
            self._log(f"  Operational Risk Score: {operational_risk:.1f}/100")

            # Step 5: Assess reputational risk
            self._log("Step 5/6: Assessing reputational risk")
            reputation_result = await self.reputation_agent.assess_reputational_risk(
                applicant_id
            )
            reputational_risk = reputation_result["reputational_risk"]
            self._log(f"  Reputational Risk Score: {reputational_risk:.1f}/100")

            # Step 6: Synthesize final decision (would call LoanDecisionAgent here)
            self._log("Step 6/6: Synthesizing final decision")

            # For demonstration, create a mock decision
            # In production, this would call LoanDecisionAgent.make_decision()
            final_decision = self._synthesize_decision(
                applicant_id=applicant_id,
                financial_risk=financial_risk,
                operational_risk=operational_risk,
                compliance_risk=compliance_risk,
                reputational_risk=reputational_risk,
                critical_issues=compliance_result["critical_issues"],
                mitigating_factors=operational_result["mitigating_factors"],
                escalation_required=operational_result["escalation_required"],
            )

            self._log(f"  Final Decision: {final_decision['classification']}")
            self._log("Workflow completed successfully")

            return WorkflowResult(
                applicant_id=applicant_id,
                final_decision=final_decision["classification"],
                risk_score=final_decision["risk_score"],
                confidence_level=final_decision["confidence_level"],
                key_factors=final_decision["key_factors"],
                explanation=final_decision["explanation"],
                risk_assessments=RiskAssessmentOutput(
                    financial_risk=financial_risk,
                    operational_risk=operational_risk,
                    compliance_risk=compliance_risk,
                    reputational_risk=reputational_risk,
                    has_critical_issues=compliance_result["critical_issues"],
                    has_mitigating_factors=operational_result["mitigating_factors"],
                ),
                workflow_status="success",
                timestamp=datetime.datetime.utcnow().isoformat(),
            )

        except Exception as e:
            self._log(f"Workflow failed: {str(e)}")
            raise

    def _synthesize_decision(
        self,
        applicant_id: str,
        financial_risk: float,
        operational_risk: float,
        compliance_risk: float,
        reputational_risk: float,
        critical_issues: bool,
        mitigating_factors: bool,
        escalation_required: bool,
    ) -> Dict[str, Any]:
        """
        Synthesize final decision (mock implementation).

        In production, this would call LoanDecisionAgent.make_decision()
        """
        # Calculate weighted risk score
        risk_score = int(
            round(
                financial_risk * 0.35
                + operational_risk * 0.25
                + compliance_risk * 0.25
                + reputational_risk * 0.15
            )
        )

        # Determine classification
        if risk_score >= 85 and critical_issues:
            classification = "Reject"
            confidence = 0.95
        elif critical_issues and not mitigating_factors:
            classification = "Reject"
            confidence = 0.9
        elif risk_score >= 50 and escalation_required:
            classification = "Review"
            confidence = 0.85
        elif risk_score >= 50 and critical_issues:
            classification = "Review"
            confidence = 0.8
        elif risk_score < 50 and not critical_issues:
            classification = "Approve"
            confidence = 0.95
        elif mitigating_factors:
            classification = "Review"
            confidence = 0.75
        else:
            classification = "Review"
            confidence = 0.7

        # Build factors
        factors = []
        if risk_score >= 85:
            factors.append(f"Risk score {risk_score} exceeds high-risk threshold")
        if critical_issues:
            factors.append("Critical issues identified")
        if mitigating_factors:
            factors.append("Mitigating factors present")
        if escalation_required:
            factors.append("Escalation required")

        return {
            "classification": classification,
            "risk_score": risk_score,
            "confidence_level": confidence,
            "key_factors": factors,
            "explanation": f"Decision: {classification} (Risk Score: {risk_score}/100)",
        }


# ============================================================================
# Example Usage
# ============================================================================


async def example_single_application():
    """Process a single loan application."""
    print("\n" + "=" * 80)
    print("LOAN DECISION WORKFLOW - SINGLE APPLICATION")
    print("=" * 80)

    workflow = LoanDecisionWorkflow(verbose=True)

    print("\nApplication Details:")
    print("  Applicant ID: APP_001")
    print("  Credit Score: 750")
    print("  Monthly Gross Income: $8,000")
    print("  Monthly Debt Payments: $1,500")
    print("  Requested Loan Amount: $300,000")

    try:
        result = await workflow.process_application(
            applicant_id="APP_001",
            credit_score=750,
            monthly_gross_income=8000,
            monthly_debt_payments=1500,
            loan_amount=300000,
        )

        print("\n" + "-" * 80)
        print("FINAL RESULT:")
        print("-" * 80)
        print(f"  Applicant ID: {result.applicant_id}")
        print(f"  Final Decision: {result.final_decision}")
        print(f"  Risk Score: {result.risk_score}/100")
        print(f"  Confidence Level: {result.confidence_level * 100:.0f}%")

        print("\n  Risk Assessment Breakdown:")
        print(f"    - Financial Risk: {result.risk_assessments.financial_risk:.1f}/100")
        print(
            f"    - Operational Risk: {result.risk_assessments.operational_risk:.1f}/100"
        )
        print(
            f"    - Compliance Risk: {result.risk_assessments.compliance_risk:.1f}/100"
        )
        print(
            f"    - Reputational Risk: {result.risk_assessments.reputational_risk:.1f}/100"
        )

        print("\n  Key Decision Factors:")
        for i, factor in enumerate(result.key_factors, 1):
            print(f"    {i}. {factor}")

        print(f"\n  Workflow Status: {result.workflow_status}")
        print(f"  Timestamp: {result.timestamp}")

    except Exception as e:
        print(f"\nError: {e}")


async def example_batch_applications():
    """Process multiple loan applications."""
    print("\n" + "=" * 80)
    print("LOAN DECISION WORKFLOW - BATCH PROCESSING")
    print("=" * 80)

    workflow = LoanDecisionWorkflow(verbose=False)

    applicants = [
        {
            "applicant_id": "BATCH_001",
            "credit_score": 800,
            "monthly_gross_income": 10000,
            "monthly_debt_payments": 1000,
            "loan_amount": 400000,
        },
        {
            "applicant_id": "BATCH_002",
            "credit_score": 650,
            "monthly_gross_income": 4000,
            "monthly_debt_payments": 1600,
            "loan_amount": 150000,
        },
        {
            "applicant_id": "BATCH_003",
            "credit_score": 720,
            "monthly_gross_income": 6500,
            "monthly_debt_payments": 1300,
            "loan_amount": 250000,
        },
    ]

    print(f"\nProcessing {len(applicants)} applications...\n")

    results = []
    for applicant in applicants:
        try:
            result = await workflow.process_application(
                applicant_id=applicant["applicant_id"],
                credit_score=applicant["credit_score"],
                monthly_gross_income=applicant["monthly_gross_income"],
                monthly_debt_payments=applicant["monthly_debt_payments"],
                loan_amount=applicant["loan_amount"],
            )
            results.append(result)
        except Exception as e:
            print(f"Error processing {applicant['applicant_id']}: {e}")

    # Summary
    print("-" * 80)
    print("BATCH PROCESSING SUMMARY:")
    print("-" * 80)
    print(f"Total Processed: {len(results)}")
    print(f"Approved: {sum(1 for r in results if r.final_decision == 'Approve')}")
    print(f"Rejected: {sum(1 for r in results if r.final_decision == 'Reject')}")
    print(f"Review: {sum(1 for r in results if r.final_decision == 'Review')}")

    print("\nDetailed Results:")
    for result in results:
        print(
            f"  {result.applicant_id}: {result.final_decision} "
            f"(Risk: {result.risk_score}/100, Confidence: {result.confidence_level*100:.0f}%)"
        )


async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("COMPLETE LOAN DECISION WORKFLOW")
    print("=" * 80)

    print("""
This example demonstrates how multiple agents work together to produce
a loan decision:

1. ApplicantProfileAgent - Fetches applicant information
2. FinancialRiskAgent - Analyzes financial risk
3. ComplianceAgent - Assesses compliance risk
4. OperationalRiskAgent - Evaluates operational risk
5. ReputationAgent - Measures reputational risk
6. LoanDecisionAgent - Synthesizes final decision

The workflow orchestrates these agents and produces a final decision
(Approve/Reject/Review) with confidence level and explainable factors.
    """)

    try:
        await example_single_application()
        await example_batch_applications()

        print("\n" + "=" * 80)
        print("WORKFLOW EXAMPLES COMPLETED")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError in examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
