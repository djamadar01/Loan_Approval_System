"""
FastAPI application for Loan Application Processing with LangGraph Orchestration.

This module provides a REST API endpoint for submitting loan applications and
receiving detailed loan decisions with comprehensive validation, error handling,
and logging.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, ValidationError
from pydantic_core import PydanticUndefinedType

# Import orchestrator and data classes
import sys
sys.path.insert(0, '/home/ubuntu/Desktop/demo')
from loan_orchestrator import (
    compile_loan_orchestrator,
    execute_application,
    ApplicantProfile,
    FinancialData,
    DecisionType,
    RiskLevel,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoanApplicationRequest(BaseModel):
    """Request model for loan application submission."""

    applicant_id: str = Field(..., description="Unique applicant identifier", min_length=1)
    profile: Dict[str, Any] = Field(..., description="Applicant profile data")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (300-850)")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    tenure: int = Field(..., gt=0, le=480, description="Loan tenure in months (1-480)")
    liabilities: float = Field(..., ge=0, description="Total existing liabilities")
    location: str = Field(..., min_length=1, description="Applicant location")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(),
                          description="Application submission timestamp")

    @validator('applicant_id')
    def validate_applicant_id(cls, v):
        """Validate applicant ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Applicant ID must be alphanumeric with optional underscores/hyphens')
        return v

    @validator('profile')
    def validate_profile(cls, v):
        """Validate profile contains required fields."""
        required_fields = {'name', 'age', 'employment_status', 'employment_years',
                          'education_level', 'annual_income', 'monthly_expenses', 'savings'}
        if not isinstance(v, dict):
            raise ValueError('Profile must be a dictionary')
        missing = required_fields - set(v.keys())
        if missing:
            raise ValueError(f'Profile missing required fields: {missing}')

        # Validate age
        if not isinstance(v.get('age'), int) or v['age'] < 18 or v['age'] > 120:
            raise ValueError('Age must be an integer between 18 and 120')

        # Validate employment_years
        if not isinstance(v.get('employment_years'), (int, float)) or v['employment_years'] < 0:
            raise ValueError('Employment years must be non-negative')

        # Validate income and expenses
        if v.get('annual_income', 0) <= 0:
            raise ValueError('Annual income must be positive')
        if v.get('monthly_expenses', 0) < 0:
            raise ValueError('Monthly expenses must be non-negative')
        if v.get('savings', 0) < 0:
            raise ValueError('Savings must be non-negative')

        return v

    @validator('location')
    def validate_location(cls, v):
        """Validate location format."""
        if len(v.strip()) == 0:
            raise ValueError('Location cannot be empty or whitespace only')
        return v.strip()

    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError('Timestamp must be in ISO format')
        return v


class DecisionFactor(BaseModel):
    """Individual risk factor with explanation."""

    factor_name: str = Field(..., description="Name of the factor")
    impact: str = Field(..., description="Impact level: positive, neutral, negative")
    value: float = Field(..., description="Numeric value of the factor")
    weight: float = Field(..., description="Weight in final decision (0-1)")
    explanation: str = Field(..., description="Detailed explanation")


class LoanDecisionResponse(BaseModel):
    """Response model for loan decision."""

    case_id: str = Field(..., description="Unique case identifier for tracking")
    classification: str = Field(..., description="Decision classification: approved, rejected, manual_review, conditional_approval")
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score (0-100)")
    confidence: float = Field(..., ge=0, le=1, description="Decision confidence (0-1)")
    factors: List[DecisionFactor] = Field(..., description="Key factors influencing decision")
    explanation: str = Field(..., description="Comprehensive decision rationale")
    conditions: List[str] = Field(default_factory=list, description="Conditions for approval (if applicable)")
    required_documents: List[str] = Field(default_factory=list, description="Documents required for processing")
    processed_at: str = Field(..., description="Decision processing timestamp")
    processing_time_ms: float = Field(..., description="Processing duration in milliseconds")

    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "case_id": "CASE-20240618-001",
                "classification": "approved",
                "risk_score": 35.5,
                "confidence": 0.92,
                "factors": [
                    {
                        "factor_name": "Credit Score",
                        "impact": "positive",
                        "value": 750,
                        "weight": 0.35,
                        "explanation": "Excellent credit score indicates strong payment history"
                    }
                ],
                "explanation": "Application approved based on strong credit profile and financial stability",
                "conditions": [],
                "required_documents": ["Photo ID", "Proof of Income"],
                "processed_at": "2024-06-18T10:30:45.123Z",
                "processing_time_ms": 1234.5
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""

    error_code: str = Field(..., description="Error code identifier")
    error_message: str = Field(..., description="Error description")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    case_id: Optional[str] = Field(None, description="Associated case ID if applicable")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(),
                          description="Error timestamp")


# ============================================================================
# GLOBAL STATE & INITIALIZATION
# ============================================================================

# Initialize orchestrator on startup
orchestrator = None


async def initialize_orchestrator():
    """Initialize the LangGraph orchestrator."""
    global orchestrator
    try:
        logger.info("Initializing LangGraph orchestrator...")
        orchestrator = compile_loan_orchestrator()
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        raise


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Loan Application API",
    description="REST API for loan application processing with LangGraph orchestration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ============================================================================
# MIDDLEWARE & ERROR HANDLERS
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and responses."""
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    start_time = datetime.now()
    response = await call_next(request)
    processing_time = (datetime.now() - start_time).total_seconds() * 1000

    logger.info(f"[{request_id}] Status: {response.status_code} - {processing_time:.2f}ms")
    return response


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")

    error_details = {
        "validation_errors": [
            {
                "field": ".".join(str(x) for x in err["loc"]),
                "type": err["type"],
                "message": err["msg"]
            }
            for err in exc.errors()
        ]
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "error_message": "Input validation failed",
            "details": error_details,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    case_id = getattr(request.state, 'case_id', None)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_message": "An unexpected error occurred during processing",
            "case_id": case_id,
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# ENDPOINTS
# ============================================================================



@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Dictionary with health status and orchestrator state
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_ready": orchestrator is not None,
        "version": "1.0.0"
    }


@app.post(
    "/submit-application",
    response_model=LoanDecisionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Loan Processing"],
    responses={
        200: {"description": "Loan application processed successfully"},
        400: {"description": "Invalid input data", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    }
)
async def submit_application(request: LoanApplicationRequest) -> LoanDecisionResponse:
    """
    Submit a loan application for processing.

    This endpoint accepts a loan application request, validates the input,
    invokes the LangGraph orchestrator for multi-agent decision processing,
    and returns a comprehensive loan decision response.

    Args:
        request: LoanApplicationRequest containing applicant and financial data

    Returns:
        LoanDecisionResponse with loan decision and supporting factors

    Raises:
        HTTPException: For validation errors or processing failures
    """
    global orchestrator

    # Generate case ID for tracking
    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    start_time = datetime.now()

    try:
        logger.info(f"[{case_id}] Processing application for applicant: {request.applicant_id}")

        if orchestrator is None:
            logger.error(f"[{case_id}] Orchestrator not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Orchestrator not initialized. Please try again later."
            )

        # Build applicant profile from request
        profile = ApplicantProfile(
            applicant_id=request.applicant_id,
            name=request.profile.get('name', 'Unknown'),
            age=request.profile.get('age', 0),
            employment_status=request.profile.get('employment_status', 'unknown'),
            employment_years=float(request.profile.get('employment_years', 0)),
            education_level=request.profile.get('education_level', 'unknown'),
            credit_score=request.credit_score,
            existing_loans=request.profile.get('existing_loans', 0),
        )

        logger.debug(f"[{case_id}] Built applicant profile: {profile.applicant_id}")

        # Build financial data from request
        annual_income = float(request.profile.get('annual_income', 0))
        monthly_expenses = float(request.profile.get('monthly_expenses', 0))
        savings = float(request.profile.get('savings', 0))

        financial = FinancialData(
            annual_income=annual_income,
            monthly_expenses=monthly_expenses,
            savings=savings,
            loan_amount=request.loan_amount,
            loan_term_months=request.tenure,
        )

        logger.debug(f"[{case_id}] Built financial data for loan amount: {request.loan_amount}")

        # Execute orchestrator
        logger.info(f"[{case_id}] Invoking LangGraph orchestrator...")
        result = execute_application(
            orchestrator,
            request.applicant_id,
            profile,
            financial,
        )

        logger.info(f"[{case_id}] Orchestrator execution completed")

        # Extract decision information
        loan_decision = result.get('loan_decision')
        risk_assessment = result.get('risk_assessment')
        applicant_profile = result.get('applicant_profile')
        financial_data = result.get('financial_data')

        if not loan_decision:
            logger.error(f"[{case_id}] No loan decision returned from orchestrator")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate loan decision"
            )

        # Map decision type to classification
        decision_mapping = {
            DecisionType.APPROVED: "approved",
            DecisionType.REJECTED: "rejected",
            DecisionType.MANUAL_REVIEW: "manual_review",
            DecisionType.CONDITIONAL_APPROVAL: "conditional_approval",
        }

        classification = decision_mapping.get(
            loan_decision.decision,
            "manual_review"
        )

        # Calculate confidence based on decision score and risk assessment
        decision_score = loan_decision.decision_score / 100.0
        risk_score_normalized = (risk_assessment.risk_score / 100.0) if risk_assessment else 0.5
        confidence = max(0.0, min(1.0, decision_score * (1 - risk_score_normalized * 0.3)))

        # Build decision factors from risk assessment
        factors = _build_decision_factors(
            profile=applicant_profile or profile,
            financial=financial_data or financial,
            risk_assessment=risk_assessment,
            decision=loan_decision
        )

        # Build explanation
        explanation = _build_explanation(
            classification=classification,
            decision=loan_decision,
            risk_assessment=risk_assessment,
            factors=factors
        )

        # Processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"[{case_id}] Application processed successfully - "
            f"Decision: {classification}, Risk: {risk_assessment.risk_score if risk_assessment else 0:.1f}, "
            f"Time: {processing_time:.1f}ms"
        )

        return LoanDecisionResponse(
            case_id=case_id,
            classification=classification,
            risk_score=risk_assessment.risk_score if risk_assessment else 50.0,
            confidence=confidence,
            factors=factors,
            explanation=explanation,
            conditions=loan_decision.conditions,
            required_documents=loan_decision.required_documents,
            processed_at=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )

    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"[{case_id}] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[{case_id}] Error processing application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing application: {str(e)}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _build_decision_factors(
    profile: ApplicantProfile,
    financial: FinancialData,
    risk_assessment,
    decision
) -> List[DecisionFactor]:
    """
    Build decision factors from assessment data.

    Args:
        profile: Applicant profile
        financial: Financial data
        risk_assessment: Risk assessment results
        decision: Loan decision

    Returns:
        List of DecisionFactor objects
    """
    factors = []

    # Credit score factor
    if profile.credit_score >= 750:
        impact = "positive"
        weight = 0.25
    elif profile.credit_score >= 650:
        impact = "neutral"
        weight = 0.15
    else:
        impact = "negative"
        weight = 0.25

    factors.append(DecisionFactor(
        factor_name="Credit Score",
        impact=impact,
        value=float(profile.credit_score),
        weight=weight,
        explanation=f"Credit score of {profile.credit_score} indicates {'strong' if profile.credit_score >= 700 else 'moderate' if profile.credit_score >= 600 else 'weak'} creditworthiness"
    ))

    # Employment stability
    employment_factors = {
        "full_time": ("positive", 0.20, "Stable full-time employment"),
        "self_employed": ("neutral", 0.12, "Self-employed income stability requires verification"),
        "part_time": ("negative", 0.15, "Part-time employment presents income variability risk"),
        "unemployed": ("negative", 0.25, "No employment income")
    }

    emp_status = profile.employment_status
    if emp_status in employment_factors:
        impact, weight, explanation = employment_factors[emp_status]
        factors.append(DecisionFactor(
            factor_name="Employment Status",
            impact=impact,
            value=1.0 if emp_status == "full_time" else 0.5 if emp_status in ["self_employed", "part_time"] else 0.0,
            weight=weight,
            explanation=explanation
        ))

    # Debt-to-income ratio
    if financial.debt_to_income_ratio is not None:
        if financial.debt_to_income_ratio <= 0.3:
            impact = "positive"
            weight = 0.15
            explanation = "Low debt-to-income ratio indicates strong repayment capacity"
        elif financial.debt_to_income_ratio <= 0.5:
            impact = "neutral"
            weight = 0.10
            explanation = "Moderate debt-to-income ratio within acceptable range"
        else:
            impact = "negative"
            weight = 0.15
            explanation = "High debt-to-income ratio presents repayment risk"

        factors.append(DecisionFactor(
            factor_name="Debt-to-Income Ratio",
            impact=impact,
            value=float(financial.debt_to_income_ratio),
            weight=weight,
            explanation=explanation
        ))

    # Risk factors from assessment
    if risk_assessment and hasattr(risk_assessment, 'risk_factors'):
        for risk_factor in risk_assessment.risk_factors[:3]:  # Top 3 risk factors
            factors.append(DecisionFactor(
                factor_name=f"Risk Factor: {risk_factor}",
                impact="negative",
                value=0.5,
                weight=0.10,
                explanation=f"Assessment identified: {risk_factor}"
            ))

    return factors


def _build_explanation(
    classification: str,
    decision,
    risk_assessment,
    factors: List[DecisionFactor]
) -> str:
    """
    Build comprehensive decision explanation.

    Args:
        classification: Decision classification
        decision: Loan decision object
        risk_assessment: Risk assessment results
        factors: List of decision factors

    Returns:
        Formatted explanation string
    """
    explanation_parts = []

    # Classification summary
    if classification == "approved":
        explanation_parts.append(
            "Your loan application has been APPROVED. "
            "You meet the lending criteria and can proceed with the next steps."
        )
    elif classification == "rejected":
        explanation_parts.append(
            "Your loan application has been REJECTED. "
            "Unfortunately, you do not meet the current lending criteria."
        )
    elif classification == "conditional_approval":
        explanation_parts.append(
            "Your loan application has received CONDITIONAL APPROVAL. "
            "Approval is contingent on meeting specific requirements."
        )
    else:
        explanation_parts.append(
            "Your loan application requires MANUAL REVIEW. "
            "A specialist will contact you shortly to discuss your application."
        )

    # Add rationale from decision
    if decision and hasattr(decision, 'rationale'):
        explanation_parts.append(f"\nRationale: {decision.rationale}")

    # Add risk assessment summary
    if risk_assessment:
        explanation_parts.append(
            f"\nRisk Assessment: Your application presents a {risk_assessment.overall_risk_level} "
            f"risk profile (score: {risk_assessment.risk_score:.1f}/100)."
        )

        if hasattr(risk_assessment, 'mitigating_factors') and risk_assessment.mitigating_factors:
            explanation_parts.append(
                f"Positive factors: {', '.join(risk_assessment.mitigating_factors[:3])}"
            )

    # Add key factors
    positive_factors = [f for f in factors if f.impact == "positive"]
    if positive_factors:
        factor_names = [f.factor_name for f in positive_factors[:2]]
        explanation_parts.append(
            f"\nStrengths: {', '.join(factor_names)}"
        )

    return " ".join(explanation_parts)


# ============================================================================
# TESTING ENDPOINT (for development)
# ============================================================================

@app.post("/test-application", response_model=LoanDecisionResponse, tags=["Testing"])
async def test_application() -> LoanDecisionResponse:
    """
    Submit a test loan application (development endpoint).

    Returns a sample decision response for testing purposes.
    """
    test_request = LoanApplicationRequest(
        applicant_id="TEST-001",
        profile={
            "name": "Test Applicant",
            "age": 35,
            "employment_status": "full_time",
            "employment_years": 5,
            "education_level": "bachelor",
            "annual_income": 75000,
            "monthly_expenses": 2500,
            "savings": 15000,
            "existing_loans": 1
        },
        credit_score=720,
        loan_amount=25000,
        tenure=60,
        liabilities=10000,
        location="New York, NY",
        timestamp=datetime.now().isoformat()
    )

    return await submit_application(test_request)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Loan Application API server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
