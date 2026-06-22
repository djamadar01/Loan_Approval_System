"""
Pydantic models for loan application processing system.
Includes validation rules, field constraints, and JSON schema examples.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, validator, root_validator


# ============================================================================
# Enums for Loan Processing
# ============================================================================

class LoanPurpose(str, Enum):
    """Allowed loan purposes."""
    HOME_PURCHASE = "home_purchase"
    REFINANCE = "refinance"
    HOME_IMPROVEMENT = "home_improvement"
    DEBT_CONSOLIDATION = "debt_consolidation"
    AUTO_PURCHASE = "auto_purchase"
    BUSINESS = "business"
    EDUCATION = "education"
    PERSONAL = "personal"
    OTHER = "other"


class EmploymentStatus(str, Enum):
    """Employment status options."""
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    RETIRED = "retired"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    HOMEMAKER = "homemaker"


class LoanDecision(str, Enum):
    """Loan decision classifications."""
    APPROVED = "approved"
    CONDITIONAL_APPROVAL = "conditional_approval"
    DENIED = "denied"
    REVIEW_REQUIRED = "review_required"


class RiskLevel(str, Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EducationLevel(str, Enum):
    """Education level options."""
    HIGH_SCHOOL = "high_school"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    DOCTORATE = "doctorate"
    OTHER = "other"


# ============================================================================
# Financial Data Model
# ============================================================================

class FinancialDataModel(BaseModel):
    """
    Detailed financial information of the applicant.

    Example:
        {
            "annual_income": 75000.00,
            "monthly_debt_obligations": 800.00,
            "credit_score": 720,
            "savings": 25000.00,
            "checking_balance": 5000.00,
            "investment_portfolio": 50000.00,
            "existing_debts": [
                {
                    "type": "credit_card",
                    "balance": 5000.00,
                    "monthly_payment": 200.00,
                    "interest_rate": 18.5
                }
            ],
            "bankruptcy_history": false,
            "years_employed": 5
        }
    """
    annual_income: float = Field(
        ...,
        gt=0,
        description="Annual gross income in USD"
    )
    monthly_debt_obligations: float = Field(
        default=0.0,
        ge=0,
        description="Total monthly debt payments"
    )
    credit_score: int = Field(
        ...,
        ge=300,
        le=850,
        description="Credit score (FICO or equivalent)"
    )
    savings: float = Field(
        default=0.0,
        ge=0,
        description="Liquid savings balance in USD"
    )
    checking_balance: float = Field(
        default=0.0,
        ge=0,
        description="Checking account balance in USD"
    )
    investment_portfolio: float = Field(
        default=0.0,
        ge=0,
        description="Total investment assets in USD"
    )
    existing_debts: List[Dict[str, Any]] = Field(
        default=[],
        description="List of existing debts with details"
    )
    bankruptcy_history: bool = Field(
        default=False,
        description="Whether applicant has filed for bankruptcy"
    )
    foreclosure_history: bool = Field(
        default=False,
        description="Whether applicant has experienced foreclosure"
    )
    years_employed: float = Field(
        ge=0,
        description="Years in current employment"
    )
    employment_status: EmploymentStatus = Field(
        ...,
        description="Current employment status"
    )

    @validator('monthly_debt_obligations', 'savings', 'checking_balance', 'investment_portfolio')
    def validate_amounts(cls, v):
        """Ensure financial amounts are reasonable."""
        if v < 0:
            raise ValueError("Financial amounts cannot be negative")
        if v > 1_000_000_000:
            raise ValueError("Financial amount exceeds reasonable limits")
        return v

    @validator('annual_income')
    def validate_income(cls, v):
        """Validate annual income is within reasonable bounds."""
        if v <= 0:
            raise ValueError("Annual income must be positive")
        if v > 1_000_000_000:
            raise ValueError("Annual income exceeds reasonable limits")
        return v

    @property
    def debt_to_income_ratio(self) -> float:
        """Calculate debt-to-income ratio."""
        if self.annual_income <= 0:
            return 0.0
        monthly_income = self.annual_income / 12
        if monthly_income == 0:
            return 0.0
        return (self.monthly_debt_obligations / monthly_income) * 100

    @property
    def total_liquid_assets(self) -> float:
        """Calculate total liquid assets."""
        return self.savings + self.checking_balance

    @property
    def total_assets(self) -> float:
        """Calculate total assets including investments."""
        return self.total_liquid_assets + self.investment_portfolio

    class Config:
        use_enum_values = False
        schema_extra = {
            "example": {
                "annual_income": 75000.00,
                "monthly_debt_obligations": 800.00,
                "credit_score": 720,
                "savings": 25000.00,
                "checking_balance": 5000.00,
                "investment_portfolio": 50000.00,
                "existing_debts": [],
                "bankruptcy_history": False,
                "foreclosure_history": False,
                "years_employed": 5,
                "employment_status": "employed"
            }
        }


# ============================================================================
# Applicant Profile Model
# ============================================================================

class ApplicantProfileModel(BaseModel):
    """
    Personal and demographic information about the loan applicant.

    Example:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "date_of_birth": "1985-06-15",
            "ssn_last_four": "1234",
            "address": "123 Main St, Anytown, CA 90210",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "90210",
            "country": "USA",
            "marital_status": "married",
            "dependents": 2,
            "education_level": "bachelors",
            "years_at_address": 3,
            "home_ownership_status": "renting"
        }
    """
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Applicant's first name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Applicant's last name"
    )
    email: EmailStr = Field(
        ...,
        description="Applicant's email address"
    )
    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Applicant's phone number"
    )
    date_of_birth: date = Field(
        ...,
        description="Applicant's date of birth (YYYY-MM-DD)"
    )
    ssn_last_four: str = Field(
        ...,
        regex="^\\d{4}$",
        description="Last four digits of Social Security Number"
    )
    address: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Full street address"
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="City"
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="State code (e.g., 'CA', 'NY')"
    )
    zip_code: str = Field(
        ...,
        regex="^\\d{5}(-\\d{4})?$",
        description="ZIP code (e.g., '90210' or '90210-1234')"
    )
    country: str = Field(
        default="USA",
        min_length=2,
        max_length=50,
        description="Country of residence"
    )
    marital_status: str = Field(
        ...,
        description="Marital status (single, married, divorced, widowed)"
    )
    dependents: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Number of dependents"
    )
    education_level: EducationLevel = Field(
        ...,
        description="Highest level of education"
    )
    years_at_address: float = Field(
        default=0,
        ge=0,
        description="Years at current address"
    )
    home_ownership_status: str = Field(
        ...,
        description="Home ownership status (own, rent, other)"
    )

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        # Remove common formatting characters
        cleaned = ''.join(c for c in v if c.isdigit())
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v

    @validator('state')
    def validate_state_code(cls, v):
        """Validate state code is two letters."""
        if not v.isalpha() or len(v) != 2:
            raise ValueError("State code must be two letters (e.g., 'CA')")
        return v.upper()

    @validator('date_of_birth')
    def validate_age(cls, v):
        """Ensure applicant is at least 18 years old."""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Applicant must be at least 18 years old")
        if age > 120:
            raise ValueError("Invalid date of birth")
        return v

    @property
    def age(self) -> int:
        """Calculate applicant's current age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def full_name(self) -> str:
        """Get applicant's full name."""
        return f"{self.first_name} {self.last_name}"

    class Config:
        use_enum_values = False
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "date_of_birth": "1985-06-15",
                "ssn_last_four": "1234",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "90210",
                "country": "USA",
                "marital_status": "married",
                "dependents": 2,
                "education_level": "bachelors",
                "years_at_address": 3,
                "home_ownership_status": "renting"
            }
        }


# ============================================================================
# Loan Application Request Model
# ============================================================================

class LoanApplicationRequest(BaseModel):
    """
    Complete loan application request with all applicant information.

    Example:
        {
            "applicant": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "date_of_birth": "1985-06-15",
                "ssn_last_four": "1234",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "90210",
                "country": "USA",
                "marital_status": "married",
                "dependents": 2,
                "education_level": "bachelors",
                "years_at_address": 3,
                "home_ownership_status": "renting"
            },
            "financial_data": {
                "annual_income": 75000.00,
                "monthly_debt_obligations": 800.00,
                "credit_score": 720,
                "savings": 25000.00,
                "checking_balance": 5000.00,
                "investment_portfolio": 50000.00,
                "existing_debts": [],
                "bankruptcy_history": false,
                "foreclosure_history": false,
                "years_employed": 5,
                "employment_status": "employed"
            },
            "loan_amount": 250000.00,
            "loan_term_months": 360,
            "loan_purpose": "home_purchase",
            "co_applicant": null,
            "notes": "First-time homebuyer"
        }
    """
    applicant: ApplicantProfileModel = Field(
        ...,
        description="Primary applicant information"
    )
    financial_data: FinancialDataModel = Field(
        ...,
        description="Applicant's financial information"
    )
    loan_amount: float = Field(
        ...,
        gt=0,
        le=10_000_000,
        description="Requested loan amount in USD"
    )
    loan_term_months: int = Field(
        ...,
        ge=6,
        le=600,
        description="Requested loan term in months"
    )
    loan_purpose: LoanPurpose = Field(
        ...,
        description="Purpose of the loan"
    )
    co_applicant: Optional[ApplicantProfileModel] = Field(
        default=None,
        description="Co-applicant information if applicable"
    )
    co_applicant_financial: Optional[FinancialDataModel] = Field(
        default=None,
        description="Co-applicant financial data if applicable"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Additional notes or comments about the application"
    )
    submission_datetime: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when application was submitted"
    )

    @root_validator
    def validate_co_applicant_pair(cls, values):
        """Ensure co-applicant data is either both provided or both missing."""
        co_applicant = values.get('co_applicant')
        co_applicant_financial = values.get('co_applicant_financial')

        if (co_applicant is None) != (co_applicant_financial is None):
            raise ValueError(
                "Co-applicant profile and financial data must both be provided or both be omitted"
            )
        return values

    @validator('loan_amount')
    def validate_loan_amount(cls, v):
        """Validate loan amount is reasonable."""
        if v <= 0:
            raise ValueError("Loan amount must be positive")
        return v

    @property
    def monthly_payment_estimate(self) -> float:
        """Estimate monthly payment (simple calculation)."""
        monthly_rate = 0.05 / 12  # Assume 5% annual rate
        n = self.loan_term_months
        if n == 0:
            return 0.0
        return self.loan_amount * (monthly_rate * (1 + monthly_rate) ** n) / (
            (1 + monthly_rate) ** n - 1
        )

    @property
    def has_co_applicant(self) -> bool:
        """Check if application has a co-applicant."""
        return self.co_applicant is not None

    class Config:
        use_enum_values = False
        schema_extra = {
            "example": {
                "applicant": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1-555-123-4567",
                    "date_of_birth": "1985-06-15",
                    "ssn_last_four": "1234",
                    "address": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip_code": "90210",
                    "country": "USA",
                    "marital_status": "married",
                    "dependents": 2,
                    "education_level": "bachelors",
                    "years_at_address": 3,
                    "home_ownership_status": "renting"
                },
                "financial_data": {
                    "annual_income": 75000.00,
                    "monthly_debt_obligations": 800.00,
                    "credit_score": 720,
                    "savings": 25000.00,
                    "checking_balance": 5000.00,
                    "investment_portfolio": 50000.00,
                    "existing_debts": [],
                    "bankruptcy_history": False,
                    "foreclosure_history": False,
                    "years_employed": 5,
                    "employment_status": "employed"
                },
                "loan_amount": 250000.00,
                "loan_term_months": 360,
                "loan_purpose": "home_purchase",
                "co_applicant": None,
                "co_applicant_financial": None,
                "notes": "First-time homebuyer"
            }
        }


# ============================================================================
# Loan Decision Response Model
# ============================================================================

class LoanDecisionResponse(BaseModel):
    """
    Decision response for a loan application with detailed analysis.

    Example:
        {
            "case_id": "APP-20240618-00123",
            "classification": "approved",
            "risk_score": 35.5,
            "risk_level": "low",
            "confidence": 0.92,
            "factors": {
                "credit_score": 0.85,
                "debt_to_income_ratio": 0.78,
                "employment_stability": 0.90,
                "assets": 0.88,
                "income_level": 0.72
            },
            "explanation": "Application approved. Strong credit profile with excellent employment history.",
            "conditions": ["Provide proof of employment", "Appraisal required"],
            "recommended_interest_rate": 4.5,
            "processing_time_days": 5,
            "next_steps": ["Appraisal scheduling", "Final verification"],
            "decision_timestamp": "2024-06-18T14:30:00Z"
        }
    """
    case_id: str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="Unique application case identifier"
    )
    classification: LoanDecision = Field(
        ...,
        description="Final loan decision classification"
    )
    risk_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall risk score (0-100, lower is better)"
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Risk level classification"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence level of decision (0-1)"
    )
    factors: Dict[str, float] = Field(
        ...,
        description="Individual scoring factors (0-1 scale)"
    )
    explanation: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Human-readable explanation of the decision"
    )
    conditions: List[str] = Field(
        default=[],
        description="Conditions required for approval (if applicable)"
    )
    recommended_interest_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=30,
        description="Recommended interest rate percentage (if approved)"
    )
    processing_time_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=90,
        description="Estimated processing time in days"
    )
    next_steps: List[str] = Field(
        default=[],
        description="Recommended next steps for applicant"
    )
    decision_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when decision was made"
    )
    reviewer_notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Internal reviewer notes (optional)"
    )

    @validator('risk_score')
    def validate_risk_score(cls, v):
        """Ensure risk score is within valid range."""
        if v < 0 or v > 100:
            raise ValueError("Risk score must be between 0 and 100")
        return v

    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v

    @validator('factors')
    def validate_factors(cls, v):
        """Ensure all factor scores are between 0 and 1."""
        for factor_name, score in v.items():
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                raise ValueError(
                    f"Factor '{factor_name}' score must be between 0 and 1, got {score}"
                )
        return v

    @root_validator
    def validate_conditional_fields(cls, values):
        """Validate conditional field requirements based on decision."""
        classification = values.get('classification')
        recommended_rate = values.get('recommended_interest_rate')

        if classification == LoanDecision.APPROVED and recommended_rate is None:
            raise ValueError("Approved decisions must include recommended_interest_rate")

        return values

    @property
    def is_approved(self) -> bool:
        """Check if application was approved."""
        return self.classification in [LoanDecision.APPROVED, LoanDecision.CONDITIONAL_APPROVAL]

    @property
    def is_denied(self) -> bool:
        """Check if application was denied."""
        return self.classification == LoanDecision.DENIED

    class Config:
        use_enum_values = False
        schema_extra = {
            "example": {
                "case_id": "APP-20240618-00123",
                "classification": "approved",
                "risk_score": 35.5,
                "risk_level": "low",
                "confidence": 0.92,
                "factors": {
                    "credit_score": 0.85,
                    "debt_to_income_ratio": 0.78,
                    "employment_stability": 0.90,
                    "assets": 0.88,
                    "income_level": 0.72
                },
                "explanation": "Application approved. Strong credit profile with excellent employment history.",
                "conditions": [],
                "recommended_interest_rate": 4.5,
                "processing_time_days": 5,
                "next_steps": ["Appraisal scheduling", "Final verification"],
                "decision_timestamp": "2024-06-18T14:30:00Z",
                "reviewer_notes": None
            }
        }


# ============================================================================
# Error Response Model
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Standardized error response format.

    Example:
        {
            "error_code": "INVALID_REQUEST",
            "message": "Email address is invalid",
            "details": {
                "field": "applicant.email",
                "value": "invalid-email",
                "constraint": "valid email format required"
            },
            "timestamp": "2024-06-18T14:30:00Z",
            "request_id": "REQ-20240618-00456"
        }
    """
    error_code: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Machine-readable error code"
    )
    message: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details (field-specific info, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when error occurred"
    )
    request_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique request identifier for tracking"
    )

    @validator('error_code')
    def validate_error_code(cls, v):
        """Ensure error code contains only valid characters."""
        if not all(c.isalnum() or c == '_' for c in v):
            raise ValueError("Error code must contain only alphanumeric characters and underscores")
        return v

    class Config:
        schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Email address is invalid",
                "details": {
                    "field": "applicant.email",
                    "value": "invalid-email",
                    "constraint": "valid email format required"
                },
                "timestamp": "2024-06-18T14:30:00Z",
                "request_id": "REQ-20240618-00456"
            }
        }


# ============================================================================
# Additional Utility Models
# ============================================================================

class BatchApplicationResponse(BaseModel):
    """Response for batch application processing."""
    total_processed: int = Field(..., ge=0, description="Total applications processed")
    successful: int = Field(..., ge=0, description="Successfully processed applications")
    failed: int = Field(..., ge=0, description="Failed applications")
    results: List[Dict[str, Any]] = Field(default=[], description="Individual results")


class ApplicationStatusResponse(BaseModel):
    """Response for checking application status."""
    case_id: str = Field(..., description="Application case ID")
    status: str = Field(..., description="Current application status")
    last_updated: datetime = Field(..., description="Last update timestamp")
    decision: Optional[LoanDecision] = Field(default=None, description="Final decision if available")
    estimated_completion: Optional[date] = Field(default=None, description="Estimated completion date")
