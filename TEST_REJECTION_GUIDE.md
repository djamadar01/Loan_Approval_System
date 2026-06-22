# Testing Loan Rejection Scenario

## 📋 Rejection Customer Details

Use these customer details to trigger a **REJECTED** loan decision:

### Basic Information
```
Name: James Smith
Applicant ID: APP_REJECT_001
Age: 25 years old
Employment: Unemployed
Years Employed: 0
Education: High School
Credit Score: 350
Existing Loans: 5
```

### Financial Information
```
Annual Income: $18,000
Monthly Expenses: $2,500
Savings: $500
Total Liabilities: $30,000
```

## 🔴 Why This Gets REJECTED

| Factor | Value | Why Rejected |
|--------|-------|-------------|
| **Credit Score** | 350 | ❌ Far below 750 (risk +40) |
| **Employment** | Unemployed | ❌ Highest employment risk (+30) |
| **Employment Years** | 0 | ❌ No employment history (+20) |
| **DTI Ratio** | 1.67 | ❌ Way above 0.3 threshold (risk +40) |
| **Savings** | $500 | ❌ Only covers 2 days expenses (risk +20) |
| **Age** | 25 | ⚠ Below optimal 30-50 range |
| **Education** | High School | ⚠ Lowest education level |

## 📊 Expected Result

```
Decision: ❌ REJECTED
Decision Score: 2.00/100
Approval Probability: 5%
Overall Risk Level: CRITICAL (97.5/100)

Rejection Reason:
"Loan application does not meet minimum approval criteria. 
Risk factors: Low credit score: 350, Currently unemployed, 
High DTI ratio: 1.67"
```

## 🌐 Using With Flask Web UI

### 1. Start the Flask Server
```bash
cd /home/ubuntu/Desktop/demo
python flask_app.py
```

### 2. Open Browser
```
http://localhost:5000
```

### 3. Fill Form With These Values

| Field | Value |
|-------|-------|
| Applicant ID | APP_REJECT_001 |
| Name | James Smith |
| Age | 25 |
| Employment Status | Unemployed |
| Years Employed | 0 |
| Credit Score | 350 |
| Education | High School |
| Annual Income | 18000 |
| Monthly Expenses | 2500 |
| Savings | 500 |
| Total Liabilities | 30000 |
| Existing Loans | 5 |

### 4. Click "Submit Application"

Result will show:
- ❌ **REJECTED**
- Score: 2.00/100
- Risk: CRITICAL
- Full audit trail

## 🔗 Using With API

### cURL Command
```bash
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP_REJECT_001",
    "name": "James Smith",
    "age": 25,
    "employment_status": "unemployed",
    "employment_years": 0,
    "credit_score": 350,
    "education_level": "high_school",
    "annual_income": 18000,
    "monthly_expenses": 2500,
    "savings": 500,
    "total_liabilities": 30000,
    "existing_loans": 5
  }'
```

### Expected Response
```json
{
  "success": true,
  "result": {
    "applicant_id": "APP_REJECT_001",
    "name": "James Smith",
    "decision": "REJECTED",
    "score": 2.0,
    "confidence": 5.0,
    "key_factors": [
      "Loan application does not meet minimum approval criteria. Risk factors: Low credit score: 350, Currently unemployed, High DTI ratio: 1.67"
    ],
    "compliance": true,
    "timestamp": "2026-06-22T..."
  }
}
```

## 🎯 Decision Scoring Logic

The orchestrator calculates rejection like this:

```
Decision Score = 100.0
  - (Profile Risk: 100) × 0.3  = 30 points
  - (Financial Risk: 95) × 0.4 = 38 points
  - (Risk Level Penalty: 20)    = 20 points
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Final Score = 2.0 (< 40 threshold for rejection)
```

## 📈 Comparison: Approval vs Rejection

### ✅ APPROVED Profile (For Reference)
```json
{
  "name": "John Doe",
  "age": 35,
  "employment_status": "employed",
  "employment_years": 8,
  "credit_score": 750,
  "education_level": "bachelor",
  "annual_income": 75000,
  "monthly_expenses": 3000,
  "savings": 25000,
  "total_liabilities": 50000,
  "existing_loans": 2
}
```
**Result: APPROVED (87.75/100)**

### ❌ REJECTED Profile (Current)
```json
{
  "name": "James Smith",
  "age": 25,
  "employment_status": "unemployed",
  "employment_years": 0,
  "credit_score": 350,
  "education_level": "high_school",
  "annual_income": 18000,
  "monthly_expenses": 2500,
  "savings": 500,
  "total_liabilities": 30000,
  "existing_loans": 5
}
```
**Result: REJECTED (2.00/100)**

## 🔧 How to Adjust Risk

To test different scenarios:

| Change | Effect | Outcome |
|--------|--------|---------|
| Increase credit_score to 600 | Risk -25 | Might move to MANUAL_REVIEW |
| Add employment | Risk -30 | Might move to MANUAL_REVIEW |
| Reduce monthly_expenses | Risk -15 | Still REJECTED |
| All three above | Combined | Might move to CONDITIONAL |

## 📝 Test Cases

### Test Case 1: Pure Rejection (Current)
- **Purpose**: Verify rejection path works
- **Profile**: James Smith (APP_REJECT_001)
- **Expected**: REJECTED with score 2.0

### Test Case 2: Marginal Rejection
- **Purpose**: Test boundary conditions
- **Profile**: Modify James Smith with credit_score=400, employment_years=1
- **Expected**: REJECTED with score ~15-20

### Test Case 3: Manual Review Border
- **Purpose**: Test 40-60 score range
- **Profile**: Modify James Smith with credit_score=500, employed, 2 years
- **Expected**: MANUAL_REVIEW

## 📚 Related Files

- `REJECTION_SCENARIO.json` - Complete JSON payload
- `flask_app.py` - Web server (start here)
- `loan_orchestrator.py` - Core logic
- `templates/index.html` - Web form
- `EVALUATION_REPORT_DANISH_JAMADAR.md` - Full system evaluation

## 🚀 Quick Test

Run this one-liner to test rejection directly:

```bash
python << 'EOF'
import sys; sys.path.insert(0, '/home/ubuntu/Desktop/demo')
from loan_orchestrator import *
profile = ApplicantProfile(applicant_id='TEST', name='James Smith', age=25, employment_status='unemployed', employment_years=0, education_level='high_school', credit_score=350, existing_loans=5)
financial = FinancialData(annual_income=18000, monthly_expenses=2500, savings=500, debt_to_income_ratio=1.67)
orch = compile_loan_orchestrator()
result = execute_application(orch, 'TEST', profile, financial)
print(f"Decision: {result['loan_decision'].decision.value}")
print(f"Score: {result['loan_decision'].decision_score}")
EOF
```

---

**Result: REJECTED ❌ (Score: 2.0/100)**

