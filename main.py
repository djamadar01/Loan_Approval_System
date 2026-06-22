"""
FastAPI Main Application for Loan Decision System

This module provides the core REST API for the loan decision system with:
- Health monitoring endpoint
- Loan application submission with validation
- Application status checking
- Decision filtering and pagination
- Error handling middleware
- CORS setup
- LangGraph orchestrator initialization
"""

import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, validator
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE VALIDATION
# ============================================================================

class PersonalInfo(BaseModel):
    """Personal information of the applicant."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., regex=r'^\+?1?\d{9,15}$')
    date_of_birth: str = Field(..., description="Date in YYYY-MM-DD format")

    @validator('date_of_birth')
    def validate_dob(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v


class EmploymentInfo(BaseModel):
    """Employment information of the applicant."""
    employer_name: str = Field(..., min_length=1, max_length=200)
    job_title: str = Field(..., min_length=1, max_length=100)
    employment_status: str = Field(..., regex=r'^(employed|self-employed|unemployed|retired)$')
    years_employed: float = Field(..., ge=0, le=70)
    monthly_income: float = Field(..., gt=0)


class FinancialInfo(BaseModel):
    """Financial information of the applicant."""
    annual_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., ge=0)
    credit_score: int = Field(..., ge=300, le=850)
    existing_loans_count: int = Field(..., ge=0)
    savings_amount: float = Field(..., ge=0)


class LoanDetails(BaseModel):
    """Loan application details."""
    loan_amount: float = Field(..., gt=0, le=1000000)
    loan_term_months: int = Field(..., ge=6, le=360)
    loan_purpose: str = Field(..., regex=r'^(home|auto|personal|business|education)$')
    collateral_type: Optional[str] = Field(None, regex=r'^(property|vehicle|cash|none)$')
    collateral_value: float = Field(default=0, ge=0)


class LoanApplicationRequest(BaseModel):
    """Complete loan application request."""
    personal_info: PersonalInfo
    employment_info: EmploymentInfo
    financial_info: FinancialInfo
    loan_details: LoanDetails
    additional_notes: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "personal_info": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "date_of_birth": "1990-01-15"
                },
                "employment_info": {
                    "employer_name": "Tech Corp",
                    "job_title": "Software Engineer",
                    "employment_status": "employed",
                    "years_employed": 5.5,
                    "monthly_income": 8000
                },
                "financial_info": {
                    "annual_income": 96000,
                    "monthly_expenses": 3000,
                    "credit_score": 750,
                    "existing_loans_count": 1,
                    "savings_amount": 50000
                },
                "loan_details": {
                    "loan_amount": 250000,
                    "loan_term_months": 360,
                    "loan_purpose": "home",
                    "collateral_type": "property",
                    "collateral_value": 300000
                },
                "additional_notes": "No additional information"
            }
        }


class ApplicationStatus(BaseModel):
    """Loan application status response."""
    application_id: str
    status: str = Field(..., regex=r'^(pending|approved|rejected|under_review|flagged)$')
    applicant_name: str
    loan_amount: float
    submission_date: str
    last_updated: str
    current_stage: Optional[str] = None
    notes: Optional[str] = None


class DecisionRecord(BaseModel):
    """Individual decision record."""
    application_id: str
    applicant_name: str
    loan_amount: float
    decision: str = Field(..., regex=r'^(approved|rejected|conditional|manual_review)$')
    risk_score: float = Field(..., ge=0, le=100)
    decision_date: str
    decision_reason: str
    approved_amount: Optional[float] = None
    conditions: Optional[List[str]] = None


class DecisionsResponse(BaseModel):
    """Paginated decisions response."""
    decisions: List[DecisionRecord]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    orchestrator_ready: bool
    database_connected: bool


class ApplicationResponse(BaseModel):
    """Loan application response."""
    application_id: str
    status: str
    message: str
    submission_timestamp: str
    estimated_processing_time_hours: int


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str
    timestamp: str
    request_id: Optional[str] = None


# ============================================================================
# APPLICATION STATE
# ============================================================================

class ApplicationState:
    """Global application state."""
    def __init__(self):
        self.orchestrator = None
        self.db_connected = False
        self.applications_store: Dict[str, Dict[str, Any]] = {}
        self.decisions_store: List[Dict[str, Any]] = []
        self._application_counter = 0

    def get_next_application_id(self) -> str:
        """Generate next application ID."""
        self._application_counter += 1
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"APP-{timestamp}-{self._application_counter:06d}"


# Global state
app_state = ApplicationState()


# ============================================================================
# MIDDLEWARE & ERROR HANDLING
# ============================================================================

class ErrorHandlingMiddleware:
    """Custom error handling middleware."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
            error_response = {
                "error": "Internal server error",
                "detail": str(exc),
                "timestamp": datetime.now().isoformat()
            }
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [[b"content-type", b"application/json"]],
            })
            await send({
                "type": "http.response.body",
                "body": str(error_response).encode("utf-8"),
            })


# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================

async def initialize_orchestrator():
    """Initialize the LangGraph orchestrator."""
    try:
        logger.info("Initializing LangGraph orchestrator...")

        # Import orchestrator module
        try:
            from loan_orchestrator import create_orchestrator
            app_state.orchestrator = create_orchestrator()
            logger.info("LangGraph orchestrator initialized successfully")
            return True
        except ImportError:
            logger.warning("LangGraph orchestrator module not available, using mock orchestrator")
            app_state.orchestrator = {
                "status": "mock",
                "version": "1.0.0"
            }
            return True
    except Exception as exc:
        logger.error(f"Failed to initialize orchestrator: {str(exc)}")
        return False


async def initialize_database_connection():
    """Initialize database connection."""
    try:
        logger.info("Initializing database connection...")

        # Mock database initialization
        # In production, this would connect to actual database
        app_state.db_connected = True
        logger.info("Database connection initialized")
        return True
    except Exception as exc:
        logger.error(f"Failed to initialize database: {str(exc)}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting up application...")

    # Initialize orchestrator
    orchestrator_ready = await initialize_orchestrator()

    # Initialize database
    db_connected = await initialize_database_connection()

    if orchestrator_ready and db_connected:
        logger.info("Application startup complete")
    else:
        logger.warning("Application startup completed with warnings")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    app_state.orchestrator = None
    app_state.db_connected = False
    logger.info("Application shutdown complete")


# ============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Loan Decision System API",
    description="REST API for loan application processing and decision management",
    version="1.0.0",
    lifespan=lifespan
)


# Add custom error handling middleware
app.add_middleware(ErrorHandlingMiddleware)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    max_age=600,
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc),
            timestamp=datetime.now().isoformat(),
            request_id=request.headers.get("X-Request-ID")
        ).dict()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation error",
            detail=str(exc),
            timestamp=datetime.now().isoformat(),
            request_id=request.headers.get("X-Request-ID")
        ).dict()
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns system status including orchestrator and database connection status.
    """
    return HealthResponse(
        status="healthy" if (app_state.orchestrator and app_state.db_connected) else "degraded",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        orchestrator_ready=app_state.orchestrator is not None,
        database_connected=app_state.db_connected
    )


@app.post(
    "/api/v1/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Loan Applications"]
)
async def submit_loan_application(request: LoanApplicationRequest):
    """
    Submit a new loan application.

    Validates all required information and enqueues the application for processing.

    Request body includes:
    - Personal information (name, email, phone, DOB)
    - Employment information (employer, job title, income, tenure)
    - Financial information (income, expenses, credit score, existing loans)
    - Loan details (amount, term, purpose, collateral)

    Returns application ID and estimated processing time.
    """
    try:
        logger.info(f"Processing loan application from {request.personal_info.first_name} {request.personal_info.last_name}")

        # Generate application ID
        app_id = app_state.get_next_application_id()

        # Validate debt-to-income ratio
        monthly_income = request.employment_info.monthly_income
        monthly_expenses = request.financial_info.monthly_expenses
        loan_amount = request.loan_details.loan_amount
        loan_term_months = request.loan_details.loan_term_months

        # Calculate estimated monthly payment (simple approximation)
        monthly_rate = 0.05 / 12  # 5% annual rate
        monthly_payment = (loan_amount * monthly_rate * (1 + monthly_rate)**loan_term_months) / ((1 + monthly_rate)**loan_term_months - 1)
        total_monthly_obligations = monthly_expenses + monthly_payment
        dti_ratio = total_monthly_obligations / monthly_income if monthly_income > 0 else 0

        if dti_ratio > 0.50:  # Debt-to-income ratio should not exceed 50%
            raise ValueError(f"Debt-to-income ratio {dti_ratio:.2%} exceeds maximum allowed (50%)")

        # Store application
        app_state.applications_store[app_id] = {
            "application_id": app_id,
            "status": "pending",
            "personal_info": request.personal_info.dict(),
            "employment_info": request.employment_info.dict(),
            "financial_info": request.financial_info.dict(),
            "loan_details": request.loan_details.dict(),
            "additional_notes": request.additional_notes,
            "submission_date": datetime.now().isoformat(),
            "dti_ratio": dti_ratio,
        }

        logger.info(f"Application {app_id} submitted successfully")

        # Would trigger orchestrator processing in production
        # if app_state.orchestrator:
        #     await app_state.orchestrator.process_application(app_id)

        return ApplicationResponse(
            application_id=app_id,
            status="received",
            message=f"Application {app_id} has been received and queued for processing",
            submission_timestamp=datetime.now().isoformat(),
            estimated_processing_time_hours=24
        )

    except ValueError as exc:
        logger.warning(f"Validation error in application submission: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"Error processing application: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process loan application"
        )


@app.get(
    "/api/v1/applications/{app_id}",
    response_model=ApplicationStatus,
    tags=["Loan Applications"]
)
async def get_application_status(
    app_id: str = Path(..., description="The application ID to retrieve")
):
    """
    Retrieve the status of a loan application.

    Returns current processing status, applicant information, and any notes.
    """
    try:
        if app_id not in app_state.applications_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )

        app_data = app_state.applications_store[app_id]

        return ApplicationStatus(
            application_id=app_id,
            status=app_data.get("status", "pending"),
            applicant_name=f"{app_data['personal_info']['first_name']} {app_data['personal_info']['last_name']}",
            loan_amount=app_data["loan_details"]["loan_amount"],
            submission_date=app_data["submission_date"],
            last_updated=app_data.get("last_updated", app_data["submission_date"]),
            current_stage=app_data.get("current_stage", "queued"),
            notes=app_data.get("notes")
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving application {app_id}: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application status"
        )


@app.get(
    "/api/v1/decisions",
    response_model=DecisionsResponse,
    tags=["Decisions"]
)
async def get_decisions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of decisions per page"),
    decision_filter: Optional[str] = Query(None, regex=r'^(approved|rejected|conditional|manual_review|all)$', description="Filter by decision type"),
    min_risk_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum risk score"),
    max_risk_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum risk score"),
    sort_by: Optional[str] = Query("decision_date", regex=r'^(decision_date|risk_score|loan_amount)$', description="Sort field"),
    sort_order: Optional[str] = Query("desc", regex=r'^(asc|desc)$', description="Sort order"),
):
    """
    Retrieve loan decisions with filtering and pagination.

    Supports filtering by:
    - Decision type (approved, rejected, conditional, manual_review)
    - Risk score range
    - Sorting by decision date, risk score, or loan amount

    Returns paginated results with total count and metadata.
    """
    try:
        # Filter decisions
        filtered_decisions = app_state.decisions_store.copy()

        if decision_filter and decision_filter != "all":
            filtered_decisions = [d for d in filtered_decisions if d.get("decision") == decision_filter]

        if min_risk_score is not None:
            filtered_decisions = [d for d in filtered_decisions if d.get("risk_score", 0) >= min_risk_score]

        if max_risk_score is not None:
            filtered_decisions = [d for d in filtered_decisions if d.get("risk_score", 0) <= max_risk_score]

        # Sort decisions
        reverse_sort = sort_order == "desc"
        if sort_by == "decision_date":
            filtered_decisions.sort(
                key=lambda d: d.get("decision_date", ""),
                reverse=reverse_sort
            )
        elif sort_by == "risk_score":
            filtered_decisions.sort(
                key=lambda d: d.get("risk_score", 0),
                reverse=reverse_sort
            )
        elif sort_by == "loan_amount":
            filtered_decisions.sort(
                key=lambda d: d.get("loan_amount", 0),
                reverse=reverse_sort
            )

        # Paginate
        total_count = len(filtered_decisions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_decisions = filtered_decisions[start_idx:end_idx]

        # Convert to response models
        decision_records = [
            DecisionRecord(
                application_id=d.get("application_id", ""),
                applicant_name=d.get("applicant_name", ""),
                loan_amount=d.get("loan_amount", 0),
                decision=d.get("decision", ""),
                risk_score=d.get("risk_score", 0),
                decision_date=d.get("decision_date", ""),
                decision_reason=d.get("decision_reason", ""),
                approved_amount=d.get("approved_amount"),
                conditions=d.get("conditions")
            )
            for d in paginated_decisions
        ]

        return DecisionsResponse(
            decisions=decision_records,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=(end_idx < total_count)
        )

    except Exception as exc:
        logger.error(f"Error retrieving decisions: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve decisions"
        )


# ============================================================================
# ROOT AND DOCUMENTATION ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Loan Decision System API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/api/v1", tags=["API Info"])
async def api_info():
    """API v1 information and available endpoints."""
    return {
        "api_version": "v1",
        "endpoints": {
            "health": "GET /health",
            "submit_application": "POST /api/v1/applications",
            "get_application_status": "GET /api/v1/applications/{app_id}",
            "get_decisions": "GET /api/v1/decisions"
        }
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(f"Starting FastAPI server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
