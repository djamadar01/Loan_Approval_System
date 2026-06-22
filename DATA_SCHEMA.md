# DATA_SCHEMA.md - Comprehensive Data Architecture Documentation

## Table of Contents
1. [Database Schema (SQLite Tables)](#database-schema)
2. [MCP Server Data Models](#mcp-server-data-models)
3. [API Request/Response Schemas](#api-requestresponse-schemas)
4. [State Management Data Structures](#state-management-data-structures)
5. [Audit Log Schema](#audit-log-schema)
6. [Entity Relationship Diagram](#entity-relationship-diagram)
7. [Field Descriptions & Validation](#field-descriptions--validation)

---

## Database Schema

### Overview
The system uses SQLite databases with three main persistence layers:
- **applicantdb.sqlite**: Applicant profiles, credit history, employment records
- **audit_database.db**: Case tracking, notifications, compliance audit trails
- **application_history.db**: Application decision history

### 1. ApplicantDB Schema

#### Table: `applicants`
Primary table for applicant demographic and employment information.

```sql
CREATE TABLE IF NOT EXISTS applicants (
    id TEXT PRIMARY KEY,                          -- Unique identifier (APP001, APP002, etc.)
    first_name TEXT NOT NULL,                     -- Applicant first name (1-50 chars)
    last_name TEXT NOT NULL,                      -- Applicant last name (1-50 chars)
    email TEXT NOT NULL UNIQUE,                   -- Email address (must be valid format)
    phone TEXT,                                   -- Phone number (10-20 digits)
    ssn TEXT UNIQUE,                              -- Last 4 SSN digits or full SSN hash
    date_of_birth TEXT,                           -- ISO format (YYYY-MM-DD)
    address TEXT,                                 -- Full street address (5-100 chars)
    city TEXT,                                    -- City name (2-50 chars)
    state TEXT,                                   -- State code (2 chars, uppercase)
    zip_code TEXT,                                -- ZIP code (5 or 9 digit format)
    country TEXT DEFAULT 'USA',                   -- Country of residence
    marital_status TEXT,                          -- single, married, divorced, widowed
    dependents INTEGER DEFAULT 0,                 -- Number of dependents (0-20)
    education_level TEXT,                         -- high_school, associates, bachelors, masters, doctorate
    years_at_address REAL DEFAULT 0,              -- Years at current residence
    home_ownership_status TEXT,                   -- own, rent, other
    employment_status TEXT,                       -- employed, self_employed, retired, unemployed, student, homemaker
    employer_id TEXT,                             -- Foreign key to employers table
    annual_income REAL,                           -- Annual gross income in USD (>0, <1B)
    created_at TEXT NOT NULL,                     -- ISO timestamp of record creation
    updated_at TEXT NOT NULL                      -- ISO timestamp of last update
);

-- Performance indexes
CREATE INDEX idx_applicant_email ON applicants(email);
CREATE INDEX idx_applicant_ssn ON applicants(ssn);
CREATE INDEX idx_applicant_employer ON applicants(employer_id);
```

**Field Constraints:**
- `id`: Must be unique, typically formatted as APP-YYYYMMDD-XXXXX
- `email`: Must contain @ and valid format; uniqueness enforced
- `ssn`: Encrypted or hashed for security; unique constraint
- `phone`: Minimum 10 digits when cleaned of formatting
- `state`: Two-letter code, case-insensitive (converted to uppercase)
- `zip_code`: Either 5-digit (90210) or 9-digit format (90210-1234)
- `date_of_birth`: Applicant must be ≥18 years old; <120 years old
- `annual_income`: Positive number; reasonable upper limit enforced

---

#### Table: `credit_history`
Credit score tracking and payment history.

```sql
CREATE TABLE IF NOT EXISTS credit_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,         -- Internal record ID
    applicant_id TEXT NOT NULL,                   -- Foreign key to applicants(id)
    credit_score INTEGER,                         -- FICO score (300-850)
    total_debt REAL,                              -- Total outstanding debt in USD
    available_credit REAL,                        -- Available credit limit in USD
    payment_history TEXT,                         -- JSON: recent payment status and history
    delinquencies_count INTEGER DEFAULT 0,        -- Number of late payments
    recent_delinquencies INTEGER DEFAULT 0,       -- Late payments in past 7 years
    accounts_late INTEGER DEFAULT 0,              -- Accounts currently with late payments
    last_updated TEXT NOT NULL,                   -- ISO timestamp of last credit update
    updated_by TEXT,                              -- User/system that performed update
    FOREIGN KEY (applicant_id) REFERENCES applicants(id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX idx_credit_applicant ON credit_history(applicant_id);
CREATE INDEX idx_credit_score ON credit_history(credit_score);
CREATE INDEX idx_credit_updated ON credit_history(last_updated);
```

**Field Constraints:**
- `credit_score`: Integer between 300-850 (FICO range)
- `applicant_id`: Must exist in applicants table
- `payment_history`: JSON structure with timestamps and payment amounts

---

#### Table: `employers`
Employment verification and employer data.

```sql
CREATE TABLE IF NOT EXISTS employers (
    id TEXT PRIMARY KEY,                          -- Unique employer identifier
    company_name TEXT NOT NULL,                   -- Company legal name
    industry TEXT,                                -- Industry classification
    size TEXT,                                    -- Company size (small, medium, large, enterprise)
    annual_revenue REAL,                          -- Company annual revenue in USD
    phone TEXT,                                   -- Company phone number
    address TEXT,                                 -- Company address
    city TEXT,                                    -- Company city
    state TEXT,                                   -- Company state
    zip_code TEXT,                                -- Company ZIP code
    created_at TEXT NOT NULL,                     -- Record creation timestamp
    updated_at TEXT NOT NULL                      -- Record last update timestamp
);

-- Performance indexes
CREATE INDEX idx_employer_name ON employers(company_name);
```

---

#### Table: `employee_records`
Employment history and income verification.

```sql
CREATE TABLE IF NOT EXISTS employee_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,         -- Internal record ID
    applicant_id TEXT NOT NULL,                   -- Foreign key to applicants(id)
    employer_id TEXT NOT NULL,                    -- Foreign key to employers(id)
    job_title TEXT NOT NULL,                      -- Current job title
    start_date TEXT NOT NULL,                     -- Employment start date (ISO format)
    end_date TEXT,                                -- Employment end date (NULL if current)
    annual_salary REAL,                           -- Annual salary in USD
    employment_type TEXT,                         -- full_time, part_time, contract, seasonal
    verification_status TEXT DEFAULT 'pending',   -- pending, verified, failed
    verified_date TEXT,                           -- Date verification was completed
    verified_by TEXT,                             -- User/system that verified
    created_at TEXT NOT NULL,                     -- Record creation timestamp
    updated_at TEXT NOT NULL,                     -- Record last update timestamp
    FOREIGN KEY (applicant_id) REFERENCES applicants(id) ON DELETE CASCADE,
    FOREIGN KEY (employer_id) REFERENCES employers(id)
);

-- Performance indexes
CREATE INDEX idx_employee_applicant ON employee_records(applicant_id);
CREATE INDEX idx_employee_employer ON employee_records(employer_id);
CREATE INDEX idx_employee_verification ON employee_records(verification_status);
```

**Field Constraints:**
- `employment_type`: Must be one of predefined employment types
- `verification_status`: pending, verified, or failed
- `start_date`: Must be before end_date (if present)

---

### 2. Notification System Schema

#### Table: `cases`
Primary case tracking for loan applications and compliance.

```sql
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,                     -- Format: CASE-YYYYMMDD-RANDOM-CHECKSUM
    created_at TEXT NOT NULL,                     -- ISO timestamp of case creation
    updated_at TEXT NOT NULL,                     -- ISO timestamp of last update
    case_type TEXT NOT NULL,                      -- loan_application, compliance_review, risk_assessment, etc.
    status TEXT NOT NULL DEFAULT 'OPEN',          -- OPEN, IN_PROGRESS, PENDING_INFO, APPROVED, DENIED, CLOSED
    subject TEXT NOT NULL,                        -- Case subject/title
    description TEXT,                             -- Detailed case description
    priority TEXT DEFAULT 'MEDIUM',               -- LOW, MEDIUM, HIGH, CRITICAL
    assigned_to TEXT,                             -- Assigned reviewer/processor
    case_hash TEXT NOT NULL UNIQUE                -- SHA256 hash for duplicate detection
);

-- Performance indexes
CREATE INDEX idx_case_status ON cases(status);
CREATE INDEX idx_case_created ON cases(created_at);
CREATE INDEX idx_case_priority ON cases(priority);
```

**Case ID Format:**
```
CASE-YYYYMMDD-XXXXXXXX-XXXX
      |       |        |
      |       |        +-- MD5 checksum (first 4 chars)
      |       +---------- UUID (first 8 chars, uppercase)
      +------------------ Date in YYYYMMDD format
```

---

#### Table: `notifications`
Decision notification and communication log.

```sql
CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,             -- Format: NOTIF-XXXXXXXXXXXX
    case_id TEXT NOT NULL,                        -- Foreign key to cases(case_id)
    created_at TEXT NOT NULL,                     -- ISO timestamp of notification creation
    recipient_email TEXT NOT NULL,                -- Email address of recipient
    notification_type TEXT NOT NULL,              -- decision_approved, decision_denied, conditional_approval, etc.
    status TEXT NOT NULL DEFAULT 'SENT',          -- PENDING, SENT, FAILED, RETRYING, BOUNCED
    subject TEXT NOT NULL,                        -- Email subject line
    body TEXT NOT NULL,                           -- Email body content (HTML or plain text)
    delivery_timestamp TEXT,                      -- ISO timestamp when email was delivered
    retry_count INTEGER DEFAULT 0,                -- Number of delivery retry attempts
    error_message TEXT,                           -- Error message if delivery failed
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX idx_notification_case ON notifications(case_id);
CREATE INDEX idx_notification_status ON notifications(status);
CREATE INDEX idx_notification_created ON notifications(created_at);
```

**Notification Types:**
- `decision_approved`: Application approved
- `decision_denied`: Application denied
- `conditional_approval`: Conditional approval with requirements
- `document_request`: Request for additional documentation
- `verification_required`: Verification step needed
- `status_update`: General status update

---

#### Table: `compliance_actions`
Audit trail for regulatory compliance and decision justification.

```sql
CREATE TABLE IF NOT EXISTS compliance_actions (
    action_id TEXT PRIMARY KEY,                   -- Format: COMP-XXXXXXXXXXXX
    case_id TEXT NOT NULL,                        -- Foreign key to cases(case_id)
    created_at TEXT NOT NULL,                     -- ISO timestamp of action
    action_type TEXT NOT NULL,                    -- rule_application, verification, review, override, exception
    regulation TEXT NOT NULL,                     -- Applicable regulation (FCRA, ECOA, TILA, GLBA, etc.)
    actor TEXT NOT NULL,                          -- User/system performing action
    description TEXT NOT NULL,                    -- Detailed description of action
    evidence_hash TEXT,                           -- SHA256 hash of supporting evidence
    status TEXT NOT NULL DEFAULT 'RECORDED',      -- RECORDED, REVIEWED, APPROVED, DISPUTED
    tags TEXT,                                    -- JSON array of tags for categorization
    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX idx_compliance_case ON compliance_actions(case_id);
CREATE INDEX idx_compliance_regulation ON compliance_actions(regulation);
CREATE INDEX idx_compliance_created ON compliance_actions(created_at);
```

**Regulations:**
- FCRA: Fair Credit Reporting Act
- ECOA: Equal Credit Opportunity Act
- TILA: Truth in Lending Act
- GLBA: Gramm-Leach-Bliley Act
- CRA: Community Reinvestment Act
- SCRA: Servicemembers Civil Relief Act

---

#### Table: `summary_reports`
Aggregated compliance and operational reports.

```sql
CREATE TABLE IF NOT EXISTS summary_reports (
    report_id TEXT PRIMARY KEY,                   -- Format: REPORT-XXXXXXXXXXXX
    created_at TEXT NOT NULL,                     -- ISO timestamp of report generation
    report_type TEXT NOT NULL,                    -- daily, weekly, monthly, compliance, risk_analysis
    total_cases INTEGER,                          -- Total cases in reporting period
    cases_by_status TEXT,                         -- JSON: {"OPEN": 5, "IN_PROGRESS": 3, ...}
    compliance_actions_count INTEGER,             -- Total compliance actions recorded
    notifications_sent INTEGER,                   -- Total notifications sent
    high_priority_cases INTEGER,                  -- Count of high/critical priority cases
    approval_rate REAL,                           -- Percentage of approvals
    average_processing_days REAL,                 -- Average processing time
    report_data TEXT NOT NULL                     -- Complete report JSON
);

-- Performance indexes
CREATE INDEX idx_report_type ON summary_reports(report_type);
CREATE INDEX idx_report_created ON summary_reports(created_at);
```

---

### 3. Application History Schema

#### Table: `applications`
Historical record of all application decisions.

```sql
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,         -- Internal record ID
    job_title TEXT NOT NULL,                      -- Job title or application identifier
    company_name TEXT NOT NULL,                   -- Company/applicant name
    application_url TEXT,                         -- Reference URL or link
    status TEXT DEFAULT 'applied',                -- applied, interview, rejected, offer, approved, denied
    decision_reason TEXT,                         -- Detailed decision rationale
    analysis_summary TEXT,                        -- JSON: summary of analysis
    salary_range TEXT,                            -- Expected or offered salary range
    location TEXT,                                -- Geographic location
    match_score REAL,                             -- Match score (0-100)
    requirements_met TEXT,                        -- JSON: {"requirement": true/false}
    strengths TEXT,                               -- JSON array of strengths
    weaknesses TEXT,                              -- JSON array of weaknesses
    next_steps TEXT,                              -- Recommended next steps
    risk_score REAL,                              -- Overall risk assessment (0-100)
    risk_level TEXT,                              -- low, medium, high, very_high
    notes TEXT,                                   -- Additional notes or comments
    created_at TEXT NOT NULL,                     -- Application submission timestamp
    updated_at TEXT NOT NULL                      -- Last update timestamp
);

-- Performance indexes
CREATE INDEX idx_application_status ON applications(status);
CREATE INDEX idx_application_created ON applications(created_at);
CREATE INDEX idx_application_company ON applications(company_name);
```

**Field Constraints:**
- `status`: Limited to predefined application statuses
- `match_score`: 0-100 decimal value
- `requirements_met`: JSON object with boolean values
- `strengths` & `weaknesses`: JSON arrays of strings

---

## MCP Server Data Models

### ApplicantDB MCP Server

#### Input Parameters

##### `get_applicant_profile`
```json
{
    "applicant_id": "APP001",
    "include_credit_history": true,
    "include_employment": true
}
```

**Response Structure:**
```json
{
    "applicant_id": "APP001",
    "personal_info": {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "date_of_birth": "1985-06-15",
        "address": "123 Main St, Anytown, CA 90210",
        "marital_status": "married",
        "dependents": 2
    },
    "financial_info": {
        "annual_income": 75000.00,
        "monthly_debt_obligations": 800.00,
        "credit_score": 720,
        "credit_score_risk_level": "fair",
        "total_debt": 45000.00,
        "available_credit": 15000.00
    },
    "employment_info": {
        "current_employer": "Tech Corp Inc.",
        "job_title": "Software Engineer",
        "employment_status": "employed",
        "years_employed": 5,
        "income_stability_score": 85,
        "employment_risk_level": "low",
        "verification_status": "verified"
    },
    "credit_info": {
        "credit_score": 720,
        "risk_level": "fair",
        "recent_delinquencies": 0,
        "accounts_late": 0,
        "payment_history_summary": "Good payment record"
    },
    "application_status": {
        "completion_percentage": 95,
        "missing_documents": ["Employment verification"],
        "requires_action": false
    }
}
```

##### `list_all_applicants`
**Response Structure:**
```json
{
    "total_applicants": 5,
    "applicants": [
        {
            "applicant_id": "APP001",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "application_date": "2024-06-15T10:30:00Z",
            "status": "APPROVED",
            "credit_score": 750,
            "income_stability_score": 92
        }
    ]
}
```

##### `get_applicants_by_risk_level`
**Request:**
```json
{
    "risk_level": "low"
}
```

**Response Structure:**
```json
{
    "risk_level": "low",
    "count": 3,
    "applicants": [
        {
            "applicant_id": "APP001",
            "name": "Alice Johnson",
            "employment_risk": "low",
            "income_stability_score": 92,
            "credit_score": 750,
            "dti_ratio": 32.5
        }
    ]
}
```

---

### RiskRulesDB MCP Server

#### Risk Assessment Models

##### `DebtToIncomeAnalysis`
```json
{
    "ratio": 0.365,
    "risk_level": "good",
    "total_monthly_debt": 2190.00,
    "gross_monthly_income": 6250.00,
    "calculation_method": "standard",
    "meets_lending_standards": true,
    "industry_comparison": {
        "percentile": 75,
        "industry_average": 0.38,
        "recommended_maximum": 0.43
    }
}
```

**DTI Thresholds:**
- Excellent: ≤ 20%
- Good: 20% - 36%
- Acceptable: 36% - 43%
- High Risk: > 43%

---

##### `CreditScoreAnalysis`
```json
{
    "credit_score": 720,
    "risk_level": "fair",
    "risk_percentage": 5.0,
    "percentile": 65,
    "category": "good_credit",
    "industry_benchmarks": {
        "average_score": 715,
        "good_threshold": 670,
        "excellent_threshold": 750
    },
    "risk_factors": [
        "Recent inquiry",
        "High credit utilization"
    ],
    "recommendation": "Approve with standard terms"
}
```

**Credit Score Categories:**
- EXCELLENT (800+): 1% default risk
- GOOD (750-799): 2% default risk
- FAIR (670-749): 5% default risk
- POOR (580-669): 15% default risk
- VERY_POOR (<580): 30% default risk

---

##### `AnomalyDetectionResult`
```json
{
    "anomalies_detected": [
        {
            "type": "spending_spike",
            "severity": "high",
            "description": "Credit card spending increased 300% in last 30 days",
            "detected_at": "2024-06-18T14:30:00Z"
        }
    ],
    "risk_score": 42.5,
    "summary": "Multiple financial anomalies detected requiring review",
    "recommended_actions": [
        "Request explanation for recent spending pattern",
        "Verify employment income stability",
        "Obtain recent bank statements"
    ]
}
```

**Anomaly Types:**
- SPENDING_SPIKE: Unusual spending patterns
- UNUSUAL_PATTERN: Atypical financial activity
- HIGH_VELOCITY: Multiple rapid transactions
- ACCOUNT_AGE: New account detected
- GEOGRAPHIC_ANOMALY: Activity in unusual locations
- INCOME_VARIANCE: Income fluctuation

---

### Decision Synthesis MCP Server

#### Decision Request
```json
{
    "applicant_id": "APP001",
    "loan_amount": 250000,
    "loan_term_months": 360,
    "loan_purpose": "home_purchase",
    "include_risk_assessment": true
}
```

#### Decision Response
```json
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
    "explanation": "Application approved based on strong credit profile and employment history.",
    "conditions": ["Appraisal required"],
    "recommended_interest_rate": 4.5,
    "processing_time_days": 5,
    "next_steps": ["Appraisal scheduling", "Final verification"],
    "decision_timestamp": "2024-06-18T14:30:00Z"
}
```

---

## API Request/Response Schemas

### Loan Decision API

#### Endpoint: `POST /api/loan-decision`

**Request Body:**
```json
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
    "co_applicant_financial": null,
    "notes": "First-time homebuyer"
}
```

**Response (Success - 200 OK):**
```json
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
    "conditions": [],
    "recommended_interest_rate": 4.5,
    "processing_time_days": 5,
    "next_steps": ["Appraisal scheduling", "Final verification"],
    "decision_timestamp": "2024-06-18T14:30:00Z",
    "reviewer_notes": null
}
```

**Response (Error - 400 Bad Request):**
```json
{
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
```

---

#### Endpoint: `GET /api/application-status/{case_id}`

**Response (200 OK):**
```json
{
    "case_id": "APP-20240618-00123",
    "status": "IN_PROGRESS",
    "last_updated": "2024-06-18T14:35:00Z",
    "decision": null,
    "estimated_completion": "2024-06-23"
}
```

---

#### Endpoint: `POST /api/batch-applications`

**Request Body:**
```json
{
    "applications": [
        {
            "applicant": {...},
            "financial_data": {...},
            "loan_amount": 250000,
            "loan_term_months": 360,
            "loan_purpose": "home_purchase"
        }
    ]
}
```

**Response (200 OK):**
```json
{
    "total_processed": 5,
    "successful": 4,
    "failed": 1,
    "results": [
        {
            "case_id": "APP-20240618-00123",
            "status": "success",
            "classification": "approved"
        },
        {
            "case_id": "APP-20240618-00124",
            "status": "error",
            "error_code": "VALIDATION_ERROR"
        }
    ]
}
```

---

### Health & Monitoring Endpoints

#### Endpoint: `GET /health`

**Response (200 OK):**
```json
{
    "status": "healthy",
    "timestamp": "2024-06-18T14:30:00Z",
    "cpu_percent": 42.5,
    "memory_percent": 58.3,
    "disk_percent": 65.2,
    "errors": {
        "total_errors": 3,
        "errors_by_type": {
            "ValidationError": 2,
            "DatabaseError": 1
        },
        "recent_error_rate": 0.05
    },
    "uptime_seconds": 86400
}
```

---

#### Endpoint: `GET /metrics`

**Response (200 OK - Prometheus Format):**
```
# HELP requests_total Total number of requests
# TYPE requests_total counter
requests_total{method="POST",endpoint="/api/loan-decision",status="200"} 1542.0

# HELP request_duration_seconds Request duration in seconds
# TYPE request_duration_seconds histogram
request_duration_seconds_bucket{method="POST",endpoint="/api/loan-decision",le="0.1"} 1200.0

# HELP decision_duration_seconds Decision processing time in seconds
# TYPE decision_duration_seconds histogram
decision_duration_seconds_bucket{decision_type="loan_decision",le="0.05"} 850.0

# HELP errors_total Total number of errors
# TYPE errors_total counter
errors_total{error_type="ValidationError"} 125.0

# HELP cpu_usage_percent CPU usage percentage
# TYPE cpu_usage_percent gauge
cpu_usage_percent 42.5

# HELP memory_usage_percent Memory usage percentage
# TYPE memory_usage_percent gauge
memory_usage_percent 58.3

# HELP active_requests Number of active requests
# TYPE active_requests gauge
active_requests 3.0
```

---

#### Endpoint: `GET /api/errors?limit=50`

**Response (200 OK):**
```json
{
    "errors": [
        {
            "timestamp": "2024-06-18T14:28:00Z",
            "error_type": "ValidationError",
            "error_message": "Email address is invalid",
            "request_id": "REQ-20240618-00456",
            "context": {
                "field": "applicant.email",
                "attempted_value": "invalid-email"
            }
        }
    ],
    "stats": {
        "total_errors": 1542,
        "errors_by_type": {
            "ValidationError": 892,
            "DatabaseError": 325,
            "TimeoutError": 215,
            "AuthenticationError": 110
        },
        "recent_error_rate": 0.05
    }
}
```

---

## State Management Data Structures

### Application Processing State

#### In-Memory State Context

```python
@dataclass
class ApplicationProcessingState:
    """Current application processing state."""
    
    # Request tracking
    request_id: str                          # Unique request identifier
    case_id: str                             # Associated case ID
    submission_timestamp: datetime           # When request was submitted
    current_stage: str                       # Current processing stage
    
    # Applicant data cache
    applicant_profile: ApplicantProfileModel
    financial_data: FinancialDataModel
    co_applicant: Optional[ApplicantProfileModel]
    co_applicant_financial: Optional[FinancialDataModel]
    
    # Loan parameters
    loan_amount: float
    loan_term_months: int
    loan_purpose: str
    
    # Processing results
    risk_assessment: Optional[Dict[str, Any]]
    credit_analysis: Optional[Dict[str, Any]]
    anomaly_detection: Optional[Dict[str, Any]]
    decision: Optional[LoanDecisionResponse]
    
    # Status tracking
    processing_status: str                   # pending, in_progress, completed, failed
    error_log: List[Dict[str, Any]]         # Accumulated errors
    processing_duration_ms: Optional[float]
    completed_steps: List[str]               # Completed processing steps
```

---

#### Processing Pipeline Stages

```python
# Sequential processing stages
PROCESSING_STAGES = [
    "validation",           # Input validation
    "applicant_lookup",     # Retrieve applicant profile
    "risk_assessment",      # Calculate risk scores
    "credit_analysis",      # Analyze credit history
    "anomaly_detection",    # Detect financial anomalies
    "rule_engine",         # Apply business rules
    "decision_synthesis",   # Generate final decision
    "notification",        # Send notifications
    "audit_logging"        # Record in audit trail
]
```

---

### Risk Assessment State

```python
@dataclass
class RiskAssessmentState:
    """Risk assessment calculation state."""
    
    # Financial metrics
    debt_to_income_ratio: float
    credit_score: int
    credit_risk_level: str
    
    # Employment metrics
    employment_stability_score: float  # 0-100
    employment_risk_level: str         # low, medium, high
    years_employed: float
    
    # Asset metrics
    total_liquid_assets: float
    liquid_asset_to_debt_ratio: float
    
    # Anomalies detected
    anomalies: List[Dict[str, Any]]
    anomaly_risk_score: float
    
    # Business rules
    rules_violated: List[str]
    rules_passed: List[str]
    
    # Overall assessment
    overall_risk_score: float          # 0-100, lower is better
    risk_level: str                    # low, medium, high, very_high
    confidence_score: float            # 0-1, confidence in assessment
```

---

### Decision State

```python
@dataclass
class DecisionState:
    """Final decision state."""
    
    # Decision classification
    classification: str                 # approved, conditional_approval, denied, review_required
    risk_score: float
    risk_level: str
    confidence: float
    
    # Factor analysis (0-1 scale)
    factors: Dict[str, float]
        # credit_score, dti_ratio, employment_stability,
        # assets, income_level, loan_amount_reasonableness
    
    # Terms (if approved)
    approved: bool
    recommended_interest_rate: Optional[float]
    processing_time_estimate_days: Optional[int]
    
    # Conditions and next steps
    conditions: List[str]              # Required conditions
    next_steps: List[str]              # Recommended actions
    explanation: str                   # Human-readable rationale
    
    # Decision metadata
    decision_timestamp: datetime
    reviewed_by: Optional[str]         # User who reviewed
    reviewer_notes: Optional[str]
```

---

### Notification Queue State

```python
@dataclass
class NotificationQueueState:
    """Notification queue management."""
    
    pending_notifications: List[Dict[str, Any]]
    in_flight_notifications: Dict[str, Dict[str, Any]]
    delivery_attempts: Dict[str, int]
    failed_notifications: List[Dict[str, Any]]
    
    # Statistics
    total_sent: int
    total_failed: int
    retry_count: int
```

---

## Audit Log Schema

### Audit Log Structure

```python
@dataclass
class AuditLogEntry:
    """Comprehensive audit log entry."""
    
    # Event identification
    event_id: str                       # Unique event identifier
    timestamp: datetime                 # Event occurrence time
    event_type: str                     # Type of event
    
    # Case association
    case_id: str                        # Related case ID
    applicant_id: Optional[str]         # Related applicant
    
    # Actor information
    actor: str                          # User/system performing action
    actor_type: str                     # user, system, automated_process
    
    # Action details
    action: str                         # Specific action taken
    resource_type: str                  # What resource was affected
    resource_id: str                    # ID of affected resource
    
    # Data changes
    before_state: Optional[Dict[str, Any]]  # State before action
    after_state: Optional[Dict[str, Any]]   # State after action
    changes: Optional[Dict[str, Any]]       # Detailed changes
    
    # Compliance
    regulation: str                     # Applicable regulation
    justification: str                  # Why this action was taken
    evidence_hash: Optional[str]        # Hash of supporting evidence
    
    # Status
    status: str                         # success, failure, error
    error_message: Optional[str]        # Error details if failed
    
    # Metadata
    request_id: Optional[str]           # Related HTTP request
    source_system: str                  # Source system
    ip_address: Optional[str]          # Client IP address
```

---

### Audit Log Entries by Event Type

#### Approval Decision Event
```json
{
    "event_id": "EVT-20240618-001",
    "timestamp": "2024-06-18T14:30:00Z",
    "event_type": "decision_rendered",
    "case_id": "CASE-20240618-ABC123-XYZ",
    "applicant_id": "APP001",
    "actor": "system",
    "actor_type": "automated_process",
    "action": "render_loan_decision",
    "resource_type": "loan_application",
    "resource_id": "APP-20240618-00123",
    "before_state": {
        "status": "IN_PROGRESS",
        "decision": null
    },
    "after_state": {
        "status": "APPROVED",
        "decision": "approved",
        "interest_rate": 4.5
    },
    "changes": {
        "status": ["IN_PROGRESS", "APPROVED"],
        "decision": [null, "approved"],
        "risk_score": [null, 35.5]
    },
    "regulation": "TILA, ECOA",
    "justification": "All risk thresholds met; strong credit profile",
    "evidence_hash": "sha256:abc123...",
    "status": "success",
    "request_id": "REQ-20240618-00456",
    "source_system": "LoanDecisionAgent"
}
```

---

#### Document Verification Event
```json
{
    "event_id": "EVT-20240618-002",
    "timestamp": "2024-06-18T14:45:00Z",
    "event_type": "document_verified",
    "case_id": "CASE-20240618-ABC123-XYZ",
    "applicant_id": "APP001",
    "actor": "john.reviewer@bank.com",
    "actor_type": "user",
    "action": "verify_employment_documents",
    "resource_type": "document_submission",
    "resource_id": "DOC-EMP-001",
    "before_state": {
        "verification_status": "PENDING",
        "verified_by": null
    },
    "after_state": {
        "verification_status": "VERIFIED",
        "verified_by": "john.reviewer@bank.com",
        "verified_at": "2024-06-18T14:45:00Z"
    },
    "regulation": "FCRA",
    "justification": "Employment letter matches applicant records",
    "evidence_hash": "sha256:def456...",
    "status": "success",
    "source_system": "ApplicantDB"
}
```

---

#### Exception Override Event
```json
{
    "event_id": "EVT-20240618-003",
    "timestamp": "2024-06-18T15:00:00Z",
    "event_type": "exception_override",
    "case_id": "CASE-20240618-ABC123-XYZ",
    "applicant_id": "APP002",
    "actor": "supervisor.review@bank.com",
    "actor_type": "user",
    "action": "override_risk_decision",
    "resource_type": "decision_rule",
    "resource_id": "RULE-DTI-HIGH",
    "before_state": {
        "decision": "DENIED",
        "reason": "DTI ratio exceeds threshold"
    },
    "after_state": {
        "decision": "CONDITIONAL_APPROVAL",
        "reason": "Manager override - strong mitigating factors",
        "approved_by": "supervisor.review@bank.com"
    },
    "regulation": "ECOA",
    "justification": "High DTI offset by substantial liquid assets and excellent credit history",
    "evidence_hash": "sha256:ghi789...",
    "status": "success",
    "source_system": "LoanDecisionAgent"
}
```

---

#### Compliance Violation Event
```json
{
    "event_id": "EVT-20240618-004",
    "timestamp": "2024-06-18T15:15:00Z",
    "event_type": "compliance_violation_detected",
    "case_id": "CASE-20240618-ABC123-XYZ",
    "actor": "system",
    "actor_type": "automated_process",
    "action": "flag_potential_discrimination",
    "resource_type": "decision_pattern",
    "resource_id": "PATTERN-GENDER-BIAS-001",
    "changes": {
        "compliance_status": ["compliant", "violation_detected"]
    },
    "regulation": "ECOA",
    "justification": "Statistical analysis indicates potential gender-based disparate impact in approval rates",
    "evidence_hash": "sha256:jkl012...",
    "status": "success",
    "request_id": "REQ-COMPLIANCE-CHECK-001",
    "source_system": "ComplianceMonitor"
}
```

---

## Entity Relationship Diagram

### High-Level ERD

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          APPLICANTDB SCHEMA                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐      ┌─────────────────┐      ┌──────────────────┐   │
│  │ applicants   │      │ credit_history  │      │ employee_records │   │
│  ├──────────────┤◄─────┤─────────────────┤      ├──────────────────┤   │
│  │ id (PK)      │1    *│ id (PK)         │◄─────│ id (PK)          │   │
│  │ first_name   │      │ applicant_id(FK)│      │ applicant_id (FK)│   │
│  │ last_name    │      │ credit_score    │      │ employer_id (FK) │   │
│  │ email (UQ)   │      │ total_debt      │      │ job_title        │   │
│  │ ssn (UQ)     │      │ payment_history │      │ start_date       │   │
│  │ employer_id  ├─────►│ delinquencies   │      │ salary           │   │
│  │ annual_income│(FK)  │                 │      │ employment_type  │   │
│  │ created_at   │      │                 │      │ verification_status
│  │ updated_at   │      │                 │      │                  │   │
│  └──────────────┘      └─────────────────┘      └──────────────────┘   │
│       │1                                                      ▲          │
│       │                                                       │          │
│       └───────────────────────────────────────────────────────┘          │
│                     (employment verification)                 *          │
│                                                                           │
│  ┌──────────────┐                                                        │
│  │  employers   │                                                        │
│  ├──────────────┤                                                        │
│  │ id (PK)      │                                                        │
│  │ company_name │                                                        │
│  │ industry     │                                                        │
│  │ address      │                                                        │
│  │ created_at   │                                                        │
│  └──────────────┘                                                        │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                   NOTIFICATION SYSTEM SCHEMA (AUDIT)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐      ┌─────────────────┐      ┌──────────────────┐   │
│  │    cases     │      │ notifications   │      │compliance_actions│   │
│  ├──────────────┤◄─────┤─────────────────┤      ├──────────────────┤   │
│  │ case_id (PK) │1    *│ notification_id │      │ action_id (PK)   │   │
│  │ case_type    │      │ case_id (FK)    │      │ case_id (FK)     │   │
│  │ status       │      │ recipient_email │      │ action_type      │   │
│  │ subject      │      │ notification_type       │ regulation       │   │
│  │ priority     │      │ status          │      │ actor            │   │
│  │ assigned_to  │      │ subject         │      │ description      │   │
│  │ created_at   │      │ body            │      │ evidence_hash    │   │
│  │ case_hash    │      │ delivery_ts     │      │ status           │   │
│  └──────────────┘      │ retry_count     │      └──────────────────┘   │
│       │1                │                 │           │1                │
│       │                 └─────────────────┘           │                │
│       │                                               │                │
│       └───────────────────┬──────────────────────────┘                │
│                           │ *                                          │
│  ┌──────────────────────┐ │                                            │
│  │ summary_reports      │ │                                            │
│  ├──────────────────────┤ │                                            │
│  │ report_id (PK)       │ │                                            │
│  │ report_type          │ │                                            │
│  │ total_cases          │ │                                            │
│  │ cases_by_status      │ │                                            │
│  │ compliance_count     │ │                                            │
│  │ report_data          │ │                                            │
│  │ created_at           │◄┘                                            │
│  └──────────────────────┘                                              │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                   APPLICATION HISTORY SCHEMA                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐                                                   │
│  │  applications    │                                                   │
│  ├──────────────────┤                                                   │
│  │ id (PK)          │                                                   │
│  │ job_title        │                                                   │
│  │ company_name     │                                                   │
│  │ status           │                                                   │
│  │ decision_reason  │                                                   │
│  │ match_score      │                                                   │
│  │ risk_score       │                                                   │
│  │ risk_level       │                                                   │
│  │ requirements_met │                                                   │
│  │ strengths        │ (JSON arrays)                                     │
│  │ weaknesses       │                                                   │
│  │ next_steps       │                                                   │
│  │ created_at       │                                                   │
│  │ updated_at       │                                                   │
│  └──────────────────┘                                                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

KEY:
  PK  = Primary Key
  FK  = Foreign Key
  UQ  = Unique Constraint
  1   = One (side of relationship)
  *   = Many (side of relationship)
  ◄──► = One-to-Many relationship
```

---

## Field Descriptions & Validation

### Core Field Types

#### Financial Fields
| Field | Type | Range | Validation | Description |
|-------|------|-------|-----------|-------------|
| annual_income | REAL | 0 < x < 1B | Positive, reasonable bounds | Annual gross income in USD |
| credit_score | INTEGER | 300-850 | FICO range | Credit score (300=worst, 850=best) |
| debt_to_income_ratio | REAL | 0-1 | Percentage based | Monthly debt / monthly income |
| loan_amount | REAL | 1-10M | Positive, lending limits | Requested loan amount in USD |
| interest_rate | REAL | 0-30 | Percentage bounds | Annual percentage rate |

#### Date/Time Fields
| Field | Format | Timezone | Description |
|-------|--------|----------|-------------|
| created_at | ISO 8601 | UTC | Record creation timestamp |
| updated_at | ISO 8601 | UTC | Last modification timestamp |
| date_of_birth | YYYY-MM-DD | N/A | Birth date (age ≥18, <120) |
| start_date | YYYY-MM-DD | N/A | Employment/relationship start |
| end_date | YYYY-MM-DD | N/A | Employment/relationship end (nullable) |

#### Contact Fields
| Field | Pattern | Length | Validation |
|-------|---------|--------|-----------|
| email | RFC 5322 | 5-254 | Must contain @, valid format |
| phone | E.164 | 10-20 | Minimum 10 digits when cleaned |
| ssn_last_four | `\d{4}` | 4 | Exactly 4 digits |
| zip_code | `\d{5}(-\d{4})?` | 5-9 | 5-digit or 9-digit extended |

#### Enumeration Fields

**Employment Status:**
- `employed`: Full-time employed
- `self_employed`: Self-employed/business owner
- `retired`: Retired
- `unemployed`: Currently unemployed
- `student`: Full-time student
- `homemaker`: Homemaker/caregiver

**Decision Classification:**
- `approved`: Loan approved
- `conditional_approval`: Approved with conditions
- `denied`: Loan denied
- `review_required`: Requires manual review

**Risk Levels:**
- `low`: Low risk (approve)
- `medium`: Moderate risk (review or approve with conditions)
- `high`: High risk (further investigation needed)
- `very_high`: Critical risk (deny or escalate)

**Case Status:**
- `OPEN`: Case created, not yet processed
- `IN_PROGRESS`: Currently being processed
- `PENDING_INFO`: Awaiting additional information
- `APPROVED`: Decision made, approved
- `DENIED`: Decision made, denied
- `CLOSED`: Case completed and archived

---

### Validation Rules Summary

#### Applicant Profile
```
✓ All names: 1-50 characters
✓ Email: Valid format, unique in database
✓ Phone: 10+ digits minimum
✓ Age: 18-120 years
✓ State: 2-letter code, case-insensitive
✓ ZIP: Standard US format (5 or 9 digit)
✓ Dependents: 0-20
```

#### Financial Data
```
✓ Annual Income: > 0, < 1 billion
✓ Credit Score: 300-850 (FICO)
✓ Debt Obligations: >= 0
✓ All Assets: >= 0, < 1 billion
✓ DTI Ratio: <= 100% (constraint-dependent)
✓ Loan Term: 6-600 months
✓ Loan Amount: > 0, <= 10 million
```

#### Employment
```
✓ Years Employed: >= 0
✓ Employment Type: Predefined enum
✓ Salary: > 0, <= 1 billion
✓ Start Date: ISO format, before end date
✓ End Date: ISO format (optional, if provided must be >= start)
```

---

### Indexing Strategy

#### High-Priority Indexes
```sql
-- Applicant lookups
CREATE INDEX idx_applicant_email ON applicants(email);
CREATE INDEX idx_applicant_ssn ON applicants(ssn);

-- Case queries
CREATE INDEX idx_case_status ON cases(status);
CREATE INDEX idx_case_created ON cases(created_at);
CREATE INDEX idx_case_priority ON cases(priority);

-- Notification queries
CREATE INDEX idx_notification_case ON notifications(case_id);
CREATE INDEX idx_notification_status ON notifications(status);

-- Compliance queries
CREATE INDEX idx_compliance_regulation ON compliance_actions(regulation);
CREATE INDEX idx_compliance_case ON compliance_actions(case_id);

-- Report generation
CREATE INDEX idx_report_created ON summary_reports(created_at);
```

#### Query Performance Expectations
```
Applicant lookup by ID: O(1) - Primary key
Applicant lookup by email: O(log N) - Indexed
Case status query: O(log N) - Indexed
Notifications by case: O(log N) - Indexed
Compliance actions by regulation: O(log N) - Indexed
Recent cases (last 30 days): O(log N) - Date indexed
```

---

## Summary

This comprehensive data schema documentation provides:

1. **Complete SQLite Database Design** with 12 tables across 3 databases
2. **MCP Server Data Models** for ApplicantDB, RiskRulesDB, and Decision Synthesis
3. **RESTful API Schemas** with request/response examples and error handling
4. **State Management Structures** for application processing pipeline
5. **Audit Log Specifications** with compliance-focused event tracking
6. **Entity Relationship Diagram** showing all table relationships
7. **Field Validation Rules** ensuring data integrity
8. **Performance Optimization** through strategic indexing

The schema supports:
- Multi-applicant loan processing
- Real-time risk assessment
- Comprehensive audit trails for compliance
- Notification and case tracking
- Batch processing capabilities
- Monitoring and health checks
- Full ACID compliance through SQLite transactions

