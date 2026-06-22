# Decision Logic Framework - Explainable AI for Loan Decisions

## Executive Summary

This document provides comprehensive transparency into the loan decision-making system, detailing how multiple autonomous agents contribute risk assessments that are synthesized into final lending decisions through a multi-factor scoring algorithm with transparent weighting, thresholds, and confidence scoring.

**Key Principles:**
- **Multi-Agent Architecture:** Financial, Operational, Compliance, and Reputational risk agents assess independent dimensions
- **Weighted Risk Aggregation:** Component risks combined via explicit weights (Financial: 35%, Operational: 25%, Compliance: 25%, Reputational: 15%)
- **Decision Classification:** Three-tier outcomes (Approve/Review/Reject) with confidence levels
- **Full Explainability:** Every decision includes detailed factors, reasoning, and audit trail

---

## 1. Multi-Factor Scoring Algorithm

### 1.1 Overall Risk Score Calculation

The system uses a **weighted average** to calculate the overall risk score from four independent risk dimensions:

```
Overall Risk Score = (Financial × 0.35) + (Operational × 0.25) + (Compliance × 0.25) + (Reputational × 0.15)
```

**Output Range:** 0-100 (higher = riskier)

#### Weight Justification

| Risk Factor | Weight | Rationale |
|---|---|---|
| **Financial Risk** | 35% | Primary determinant of repayment capacity (income, debt ratios, credit history) |
| **Operational Risk** | 25% | Applicant's ability to manage obligations (employment stability, income volatility) |
| **Compliance Risk** | 25% | Regulatory and legal exposure (background checks, compliance violations) |
| **Reputational Risk** | 15% | Market and institutional confidence factors (historical performance, industry reputation) |

### 1.2 Component Risk Assessment

Each agent produces a risk score (0-100) based on domain-specific factors:

#### 1.2.1 Financial Risk Agent

**Formula:**
```
Financial Risk = 100 - [Income Stability (25%) + Credit Quality (25%) + DTI Analysis (25%) + Delinquency Factor (25%)]
```

**Inputs Analyzed:**
- Credit Score (300-850) → normalized to risk component
- Debt-to-Income Ratio (calculated from monthly debt / monthly income)
- Recent Delinquencies (count, severity, recency)
- Monthly Income Stability (trend analysis)

**Example Calculation:**
```
Applicant: Credit Score 750, DTI 35%, 0 delinquencies, $6,000/month income (stable)

Credit Component = 75/100 (750 FICO = good → 75 points)
DTI Component = 80/100 (35% DTI = healthy threshold)
Delinquency Component = 100/100 (zero delinquencies = maximum score)
Income Component = 85/100 (stable, sufficient income)

Average = (75 + 80 + 100 + 85) / 4 = 85
Financial Risk = 100 - 85 = 15 (low financial risk)
```

#### 1.2.2 Operational Risk Agent

**Formula:**
```
Operational Risk = (Volatility Factor × 0.4) + (Trend Risk × 0.3) + (Employment Stability × 0.3)
```

**Inputs Analyzed:**
- Income Volatility (low/moderate/high)
- Income Trend (increasing/stable/decreasing)
- Employment Type & Verification (employed/self-employed/seasonal)
- Time at Current Position

**Risk Mapping:**

| Volatility | Score Contribution | Trend | Score Contribution | Combined Risk |
|---|---|---|---|---|
| Low | 20 | Increasing | 15 | 23 (low) |
| Low | 20 | Stable | 25 | 22 (low) |
| Moderate | 40 | Stable | 25 | 37 (medium) |
| High | 60 | Decreasing | 40 | 56 (high) |

#### 1.2.3 Compliance Risk Agent

**Formula:**
```
Compliance Risk = (Background Violations × 0.4) + (Regulatory Status × 0.3) + (Documentation Completeness × 0.3)
```

**Inputs Analyzed:**
- Criminal Background Checks
- Regulatory Violations (bankruptcy, fraud, liens)
- AML/KYC Compliance Status
- Documentation Completeness (missing required fields)
- Industry-Specific Regulatory Flags

**Scoring Logic:**
```
- No violations: 0 points
- Minor violations (resolved): 20 points
- Moderate violations (recent): 50 points
- Severe violations (active): 85+ points
- Incomplete documentation: +10-30 points
```

#### 1.2.4 Reputational Risk Agent

**Formula:**
```
Reputational Risk = (Payment History × 0.4) + (Market Perception × 0.3) + (Industry Standing × 0.3)
```

**Inputs Analyzed:**
- Historical Payment Performance (on-time %, late payments)
- Public Records & News Sentiment
- Business Reputation Scores (if applicable)
- Credit Inquiries (recent, frequency)

**Example Mapping:**
```
- Excellent payment history (≥95% on-time): 10 risk points
- Good history (85-94% on-time): 25 risk points
- Fair history (70-84% on-time): 45 risk points
- Poor history (<70% on-time): 75 risk points
```

---

## 2. Risk Calculation Formulas

### 2.1 Aggregation Process

The decision synthesis engine receives four independent risk scores and applies the weighted formula:

```python
def calculate_overall_risk(financial, operational, compliance, reputational):
    weights = {
        'financial': 0.35,
        'operational': 0.25,
        'compliance': 0.25,
        'reputational': 0.15
    }
    
    risk_score = (
        financial * weights['financial'] +
        operational * weights['operational'] +
        compliance * weights['compliance'] +
        reputational * weights['reputational']
    )
    
    return min(100, max(0, int(round(risk_score))))
```

### 2.2 Risk Score Thresholds

| Risk Score Range | Classification | Action | Confidence Baseline |
|---|---|---|---|
| 0-49 | **Low Risk** | Typically Approve | 90-95% |
| 50-84 | **Medium-High Risk** | Review Required | 70-85% |
| 85-100 | **High Risk** | Typically Reject | 90-95% |

### 2.3 Conditional Risk Adjustments

The system applies **dynamic adjustments** based on critical factors:

#### Adjustment A: Critical Issues Present
```
if has_critical_issues and not has_mitigating_factors:
    effective_risk_score += 15  (increase score 15 points)
    confidence_level *= 0.85  (reduce confidence)
```

#### Adjustment B: Mitigating Factors Present
```
if has_mitigating_factors and critical_issues:
    effective_risk_score -= 10  (reduce score 10 points)
    confidence_level *= 1.05  (maintain confidence)
```

#### Adjustment C: Escalation Required
```
if requires_escalation:
    decision = "REVIEW"  (override to manual review)
    confidence_level = max(confidence_level, 0.85)
```

---

## 3. Decision Tree Logic with Examples

### 3.1 Primary Decision Logic Flow

```
START: Receive [Financial, Operational, Compliance, Reputational] Risk Scores
│
├─ CALCULATE: Overall Risk Score (weighted average)
│
├─ EVALUATE: Critical Issues + Mitigating Factors + Escalation Flag
│
└─ CLASSIFY:
   │
   ├─ IF Risk ≥ 85 AND Has Critical Issues
   │  └─> REJECT (confidence: 0.95)
   │
   ├─ IF Has Critical Issues AND NOT Has Mitigating Factors
   │  └─> REJECT (confidence: 0.90)
   │
   ├─ IF Risk ≥ 50 AND Requires Escalation
   │  └─> REVIEW (confidence: 0.85)
   │
   ├─ IF Risk ≥ 50 AND Has Critical Issues
   │  └─> REVIEW (confidence: 0.80)
   │
   ├─ IF Risk < 50 AND NOT Has Critical Issues
   │  └─> APPROVE (confidence: 0.95)
   │
   ├─ IF Has Mitigating Factors
   │  └─> REVIEW (confidence: 0.75)
   │
   └─ DEFAULT
      └─> REVIEW (confidence: 0.70)
```

### 3.2 Decision Tree Example 1: Low-Risk Approval

**Scenario:** Strong professional, excellent credit, stable income

**Input Data:**
```
Financial Risk: 20      (excellent credit, low debt)
Operational Risk: 15    (stable employed, good income)
Compliance Risk: 10     (clean background, complete docs)
Reputational Risk: 12   (excellent payment history)
Critical Issues: false
Mitigating Factors: true
Requires Escalation: false
```

**Calculation:**
```
Risk Score = (20 × 0.35) + (15 × 0.25) + (10 × 0.25) + (12 × 0.15)
           = 7.0 + 3.75 + 2.5 + 1.8
           = 15.05
           = 15 (rounded)

Risk Classification: Low Risk (15 < 50)
Critical Issues: No
Decision Logic Path: Risk < 50 AND NOT critical_issues → APPROVE
Confidence Level: 0.95 (95%)

OUTPUT:
  Decision: APPROVE
  Risk Score: 15/100
  Confidence: 95%
  Key Factors: [
    "Risk score 15 within acceptable range",
    "No critical issues identified",
    "Mitigating factors present"
  ]
```

### 3.3 Decision Tree Example 2: Medium-Risk Review

**Scenario:** Applicant with rising income but recent DTI concerns

**Input Data:**
```
Financial Risk: 55      (decent credit, moderate DTI increase)
Operational Risk: 48    (increasing income but recent job change)
Compliance Risk: 35     (clean record, some docs pending)
Reputational Risk: 42   (good history, small recent delinquency)
Critical Issues: true
Mitigating Factors: true
Requires Escalation: false
```

**Calculation:**
```
Risk Score = (55 × 0.35) + (48 × 0.25) + (35 × 0.25) + (42 × 0.15)
           = 19.25 + 12.0 + 8.75 + 6.3
           = 46.3
           = 46 (rounded)

Risk Classification: Low-Medium (46 < 50, but has critical issues)
Critical Issues: Yes
Mitigating Factors: Yes
Decision Logic Path: Critical issues WITH mitigation possible → REVIEW
Confidence Level: 0.80 (80%)

OUTPUT:
  Decision: REVIEW
  Risk Score: 46/100
  Confidence: 80%
  Key Factors: [
    "Critical issues present but mitigable",
    "Recent employment change requires verification",
    "DTI trending upward - monitor for approval",
    "Request income verification from new employer"
  ]
  Recommendation: "Approve if recent DTI trend stabilizes; obtain 3 months recent pay stubs"
```

### 3.4 Decision Tree Example 3: High-Risk Rejection

**Scenario:** Applicant with significant financial and compliance concerns

**Input Data:**
```
Financial Risk: 85      (poor credit, high DTI, delinquencies)
Operational Risk: 78    (volatile self-employment income)
Compliance Risk: 72     (prior bankruptcy, liens present)
Reputational Risk: 68   (multiple late payments)
Critical Issues: true
Mitigating Factors: false
Requires Escalation: false
```

**Calculation:**
```
Risk Score = (85 × 0.35) + (78 × 0.25) + (72 × 0.25) + (68 × 0.15)
           = 29.75 + 19.5 + 18.0 + 10.2
           = 77.45
           = 77 (rounded)

Risk Classification: Medium-High (77 in 50-84 range)
Critical Issues: Yes
Mitigating Factors: No
Decision Logic Path: Critical issues + NOT mitigable → REJECT
Confidence Level: 0.90 (90%)

OUTPUT:
  Decision: REJECT
  Risk Score: 77/100
  Confidence: 90%
  Key Factors: [
    "Critical financial issues without mitigation",
    "Prior bankruptcy indicates serious financial distress",
    "Multiple delinquencies show payment difficulties",
    "Self-employment income volatility unacceptable"
  ]
  Recommendation: "Decline loan. Consider re-application after 2 years with improved credit history"
```

### 3.5 Decision Tree Example 4: Escalation Case

**Scenario:** Edge case requiring human judgment

**Input Data:**
```
Financial Risk: 62      (moderate credit issues)
Operational Risk: 45    (stable employment)
Compliance Risk: 52     (complex regulatory situation)
Reputational Risk: 48   (fair payment history)
Critical Issues: false
Mitigating Factors: true
Requires Escalation: true  (complex regulatory flag)
```

**Calculation:**
```
Risk Score = (62 × 0.35) + (45 × 0.25) + (52 × 0.25) + (48 × 0.15)
           = 21.7 + 11.25 + 13.0 + 7.2
           = 53.15
           = 53 (rounded)

Risk Classification: Medium-High (53 in 50-84 range)
Escalation Flag: Yes
Decision Logic Path: Escalation required → REVIEW (mandatory human review)
Confidence Level: 0.85 (85%)

OUTPUT:
  Decision: REVIEW
  Risk Score: 53/100
  Confidence: 85%
  Escalation Status: REQUIRED
  Key Factors: [
    "Risk score 53 in medium-high range (50-84)",
    "Escalation required for regulatory compliance review",
    "Mitigating factors present - proceed with caution"
  ]
  Recommendation: "Route to senior underwriter for compliance review before approval"
```

---

## 4. Agent Contributions to Final Decision

### 4.1 Agent Responsibility Matrix

| Agent | Input Factors | Output Score | Decision Impact | Weight |
|---|---|---|---|---|
| **Financial Risk** | Credit score, DTI, delinquencies, income | Risk: 0-100 | Primary repayment capacity indicator | 35% |
| **Operational Risk** | Employment stability, income volatility, trend | Risk: 0-100 | Ongoing ability to meet obligations | 25% |
| **Compliance Risk** | Background, violations, documentation, AML | Risk: 0-100 | Legal/regulatory gatekeeping | 25% |
| **Reputational Risk** | Payment history, public records, industry standing | Risk: 0-100 | Market confidence and track record | 15% |

### 4.2 Agent Independence & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ RAW APPLICANT DATA (from ApplicantDB)                       │
│ - Credit report                                              │
│ - Employment history                                         │
│ - Income documentation                                       │
│ - Background check results                                   │
│ - Application completeness                                   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Financial Risk   │ │ Operational Risk │ │ Compliance Risk  │
│ Agent            │ │ Agent            │ │ Agent            │
│                  │ │                  │ │                  │
│ Analyzes:        │ │ Analyzes:        │ │ Analyzes:        │
│ - Credit Score   │ │ - Income Trend   │ │ - Background     │
│ - DTI Ratio      │ │ - Volatility     │ │ - Violations     │
│ - Delinquencies  │ │ - Employment     │ │ - Documentation  │
│ - Debt History   │ │ - Stability      │ │ - AML Status     │
│                  │ │                  │ │                  │
│ Output: 0-100    │ │ Output: 0-100    │ │ Output: 0-100    │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Reputational     │
                    │ Risk Agent       │
                    │                  │
                    │ Analyzes:        │
                    │ - Payment        │
                    │   History        │
                    │ - Public Records │
                    │ - Reputation     │
                    │ - Credit Inquire │
                    │                  │
                    │ Output: 0-100    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
           35% weight    25% weight     (15% weight for Reputational)
           (Financial)   (Operational)
              │              │
              └──────────────┼──────────┐
                             │          │
                             ▼          ▼
                    ┌──────────────────────┐
                    │ Decision Synthesis   │
                    │ Engine               │
                    │                      │
                    │ Weighted Aggregation │
                    │ + Decision Logic     │
                    │ + Confidence Calc    │
                    └────────────┬─────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │ FINAL DECISION       │
                    │                      │
                    │ - Classification     │
                    │ - Risk Score (0-100) │
                    │ - Confidence (%)     │
                    │ - Key Factors        │
                    │ - Recommendation     │
                    └──────────────────────┘
```

### 4.3 Agent Contribution Examples

#### Scenario: Agent Disagreement

**Input Scores:**
- Financial: 30 (low risk) - strong credit, low DTI
- Operational: 70 (high risk) - recent job loss, seeking employment
- Compliance: 20 (low risk) - clean background
- Reputational: 35 (low-medium) - generally good payment history

**Weighted Calculation:**
```
Overall = (30 × 0.35) + (70 × 0.25) + (20 × 0.25) + (35 × 0.15)
        = 10.5 + 17.5 + 5.0 + 5.25
        = 38.25
        = 38 (low-medium risk)

Decision Logic: Risk < 50, no critical issues
→ APPROVE (with conditions)
→ Confidence: 0.85

Key Insight: Despite operational risk spike, overall approval due to 
             strong financial fundamentals + positive compliance factors
             35% weight on financial outweighs 25% operational concern
```

**Recommendation:**
```
"Approve with condition: Employment verification required within 30 days.
 If applicant secures employment, maintain approval.
 If unemployed beyond 60 days, re-evaluate risk profile."
```

---

## 5. Confidence Scoring Methodology

### 5.1 Confidence Level Calculation

Confidence reflects the **certainty of the decision**, not its favorability.

```python
def calculate_confidence(risk_score, has_critical_issues, 
                         has_mitigating_factors, requires_escalation):
    # Base confidence determined by decision type
    if risk_score >= 85 and has_critical_issues:
        base_confidence = 0.95  # High certainty for rejections
    elif has_critical_issues and not has_mitigating_factors:
        base_confidence = 0.90
    elif risk_score >= 50 and requires_escalation:
        base_confidence = 0.85  # Escalations still highly certain
    elif risk_score >= 50 and has_critical_issues:
        base_confidence = 0.80
    elif risk_score < 50 and not has_critical_issues:
        base_confidence = 0.95  # High certainty for clean approvals
    elif has_mitigating_factors:
        base_confidence = 0.75  # Moderate certainty when factors mitigate
    else:
        base_confidence = 0.70  # Default review confidence
    
    # Adjustments based on data completeness
    confidence = base_confidence
    
    # Reduce confidence if data incomplete
    if incomplete_documentation:
        confidence *= 0.90
    
    # Increase confidence if multiple agents agree
    if agent_consensus_high:
        confidence = min(1.0, confidence + 0.05)
    
    # Ensure bounds
    return max(0.0, min(1.0, confidence))
```

### 5.2 Confidence Levels by Decision Type

| Decision | Base Confidence | Interpretation |
|---|---|---|
| **APPROVE (Clean)** | 90-95% | Strong agreement across agents; clear low-risk profile |
| **APPROVE (Conditional)** | 75-85% | Generally positive but requires follow-up verification |
| **REVIEW** | 70-85% | Mixed signals or requires human judgment; medium certainty |
| **REJECT (High Risk)** | 90-95% | Strong agreement that risk exceeds tolerance |
| **REJECT (Unmitigable)** | 85-90% | Critical issues without remediation path |

### 5.3 Confidence Adjustments

#### Adjustment Factor 1: Data Completeness
```
Missing Critical Fields: -15% confidence
Incomplete Verification: -10% confidence
All Data Provided: No adjustment
```

#### Adjustment Factor 2: Agent Consensus
```
All 4 agents agree on risk level: +5% confidence
3 of 4 agents agree: +2% confidence
Mixed opinion (2-2 or close spread): No adjustment
```

#### Adjustment Factor 3: Decision Consistency
```
If Risk Score AND Critical Issues align with Decision:
  → No adjustment (baseline confidence applies)

If Mitigating Factors override Risk Score:
  → -5% confidence (adding uncertainty from override)

If Escalation flag applied:
  → +2% confidence (routing to expert review reduces uncertainty)
```

---

## 6. Real Example Walkthroughs: Input → Output

### 6.1 Complete Walkthrough Example 1: Homebuyer - Approval Case

#### 6.1.1 Input Data

**Applicant Profile:**
```
ID: APP_HB_2024_001
Name: Sarah Chen
Requested Loan: $350,000
Purpose: Primary residence
Income: $8,500/month (W-2 employed)
```

**Raw Data from ApplicantDB:**
```json
{
  "applicant_id": "APP_HB_2024_001",
  "credit_score": 780,
  "monthly_gross_income": 8500,
  "monthly_debt_payments": 1200,
  "employment_status": "employed",
  "time_at_job": "5 years",
  "recent_delinquencies": 0,
  "credit_inquiries_6m": 2,
  "income_trend": "stable",
  "income_volatility": "low",
  "background_violations": [],
  "documentation_completeness": 98,
  "payment_history_ontime_percent": 98,
  "public_records": [],
  "industry_reputation": "professional"
}
```

#### 6.1.2 Agent Analysis

**Financial Risk Agent Analysis:**
```
Input:
  - Credit Score: 780 (excellent)
  - DTI Current: 1200 / 8500 = 14.1% (very healthy)
  - DTI Projected: (1200 + 1050) / 8500 = 26.5% (excellent)
  - Delinquencies: 0 (perfect)
  - Income Level: $8,500/month (sufficient)

Scoring:
  - Credit Component: 85/100 (780 is "excellent")
  - DTI Component: 95/100 (14% is ideal; projected 26.5% still excellent)
  - Delinquency Component: 100/100 (zero delinquencies)
  - Income Component: 90/100 (strong, stable income)
  - Average: (85 + 95 + 100 + 90) / 4 = 92.5
  - Financial Risk Score: 100 - 92.5 = 7.5 → 8 (low financial risk)

Output: Financial Risk = 8/100
```

**Operational Risk Agent Analysis:**
```
Input:
  - Income Trend: Stable
  - Income Volatility: Low
  - Employment Type: W-2 Employed
  - Time at Position: 5 years
  - Income Level: $8,500/month

Scoring:
  - Volatility Factor: 20/100 (low = minimal risk)
  - Trend Factor: 10/100 (stable = no risk)
  - Employment Stability: 5/100 (5 years employed = excellent)
  - Combined: (20 × 0.4) + (10 × 0.3) + (5 × 0.3) = 8 + 3 + 1.5 = 12.5

Output: Operational Risk = 12/100
```

**Compliance Risk Agent Analysis:**
```
Input:
  - Background Violations: None
  - Documentation Complete: 98%
  - AML/KYC Status: Passed
  - Recent Regulatory Flags: None

Scoring:
  - Violation Component: 0/100 (clean record)
  - Regulatory Component: 0/100 (compliant)
  - Documentation Component: 2/100 (98% complete → minor points)
  - Combined: 0 + 0 + 2 = 2

Output: Compliance Risk = 2/100
```

**Reputational Risk Agent Analysis:**
```
Input:
  - Payment History: 98% on-time
  - Recent Delinquencies: 0
  - Public Records: None
  - Credit Inquiries (6mo): 2 (normal)
  - Industry Standing: Professional

Scoring:
  - Payment History: 5/100 (98% on-time = excellent)
  - Public Records: 0/100 (none)
  - Industry Standing: 3/100 (professional = good standing)
  - Combined: 5 + 0 + 3 = 8

Output: Reputational Risk = 8/100
```

#### 6.1.3 Decision Synthesis

**Risk Score Calculation:**
```
Overall Risk = (8 × 0.35) + (12 × 0.25) + (2 × 0.25) + (8 × 0.15)
             = 2.8 + 3.0 + 0.5 + 1.2
             = 7.5
             = 8 (rounded)

Risk Classification: Low Risk (8 < 50)
```

**Decision Logic Application:**
```
Check 1: Risk Score ≥ 85? No
Check 2: Critical Issues? No
Check 3: Has Mitigating Factors? Yes (strong financial profile)
Check 4: Risk < 50? Yes
Check 5: No critical issues? Yes

Decision Path Taken: "Risk < 50 AND NOT Has Critical Issues"
→ APPROVE

Confidence Calculation:
  - Base (Low risk, no issues): 0.95
  - Data completeness (98%): 0.95 × 0.98 = 0.931 → round to 0.93
  - Agent consensus (all agents very low risk): 0.93 + 0.02 = 0.95

Final Confidence: 0.95 (95%)
```

**Key Decision Factors:**
```
1. "Risk score 8 within excellent range (0-49)"
2. "Excellent credit score (780) with perfect payment history"
3. "DTI ratio 14% - well below 43% acceptable threshold"
4. "Stable W-2 employment for 5+ years"
5. "Clean background and complete documentation"
6. "No delinquencies or compliance issues"
```

#### 6.1.4 Final Decision Output

```json
{
  "applicant_id": "APP_HB_2024_001",
  "classification": "APPROVE",
  "risk_score": 8,
  "confidence_level": 0.95,
  "recommendation": "APPROVE - Strong financial profile with excellent creditworthiness",
  "key_decision_factors": [
    "Risk score 8 within excellent range (0-49)",
    "Excellent credit score (780) - demonstrates reliable repayment history",
    "Current DTI 14% (excellent) with projected DTI 26.5% (very healthy)",
    "Perfect payment history: 98% on-time payments",
    "Stable W-2 employment for 5+ years - low employment risk",
    "Zero recent delinquencies",
    "Complete documentation (98%)",
    "Clean background check and compliance status",
    "Professional industry standing"
  ],
  "explanation": "Applicant demonstrates exceptional financial responsibility and capacity...",
  "risk_breakdown": {
    "financial_risk": 8,
    "operational_risk": 12,
    "compliance_risk": 2,
    "reputational_risk": 8
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Loan Officer Note:**
```
"Approval recommended. Applicant meets all criteria for standard mortgage
 product. Loan amount of $350,000 is appropriate for income level and
 DTI ratio. Standard underwriting process can proceed with confidence.
 No additional verification required beyond standard procedures."
```

---

### 6.2 Complete Walkthrough Example 2: Business Loan - Review Case

#### 6.2.1 Input Data

**Applicant Profile:**
```
ID: APP_BUS_2024_002
Name: Michael Rodriguez (Self-Employed)
Requested Loan: $100,000
Purpose: Business expansion
Income: $7,200/month (self-employed, consulting)
```

**Raw Data from ApplicantDB:**
```json
{
  "applicant_id": "APP_BUS_2024_002",
  "credit_score": 695,
  "monthly_gross_income": 7200,
  "monthly_debt_payments": 2100,
  "employment_status": "self-employed",
  "business_age": "3 years",
  "income_trend": "increasing",
  "income_volatility": "moderate",
  "recent_delinquencies": 1,
  "delinquency_age": "8 months",
  "credit_inquiries_6m": 4,
  "background_violations": ["lien_filed_2021_resolved"],
  "documentation_completeness": 82,
  "payment_history_ontime_percent": 87,
  "missing_documents": ["tax_returns_2_years", "business_plan"],
  "critical_flag": "recent_credit_inquiry_spike"
}
```

#### 6.2.2 Agent Analysis

**Financial Risk Agent Analysis:**
```
Input:
  - Credit Score: 695 (fair/good border)
  - DTI Current: 2100 / 7200 = 29.2% (acceptable but high)
  - DTI Projected: (2100 + 300) / 7200 = 33.3% (still acceptable)
  - Recent Delinquencies: 1 (8 months old)
  - Income Level: $7,200/month (moderate)

Scoring:
  - Credit Component: 65/100 (695 is borderline)
  - DTI Component: 60/100 (29% is high, projected 33% acceptable)
  - Delinquency Component: 50/100 (one recent delinquency)
  - Income Component: 70/100 (moderate level)
  - Average: (65 + 60 + 50 + 70) / 4 = 61.25
  - Financial Risk Score: 100 - 61.25 = 38.75 → 39

Output: Financial Risk = 39/100 (moderate financial risk)
```

**Operational Risk Agent Analysis:**
```
Input:
  - Income Trend: Increasing
  - Income Volatility: Moderate
  - Employment Type: Self-Employed
  - Business Age: 3 years
  - Income Level: $7,200/month

Scoring:
  - Volatility Factor: 40/100 (moderate = some risk)
  - Trend Factor: 20/100 (increasing = positive)
  - Employment Stability: 45/100 (self-employed, 3 years = moderate)
  - Combined: (40 × 0.4) + (20 × 0.3) + (45 × 0.3) = 16 + 6 + 13.5 = 35.5

Output: Operational Risk = 36/100 (moderate operational risk)

Critical Operational Factor: Self-employment income less predictable than W-2
```

**Compliance Risk Agent Analysis:**
```
Input:
  - Background Violations: Lien filed 2021 (resolved)
  - Documentation Complete: 82%
  - Missing Documents: 2 critical items (tax returns, business plan)
  - Credit Inquiries: 4 in 6 months (elevated)

Scoring:
  - Violation Component: 20/100 (resolved lien = 20 points)
  - Documentation Component: 18/100 (82% complete, 2 critical missing)
  - Regulatory Component: 15/100 (elevated credit inquiries = risk flag)
  - Combined: 20 + 18 + 15 = 53

Output: Compliance Risk = 53/100 (medium-high compliance risk)

Critical Compliance Factor: Missing financial documentation = cannot fully verify income
```

**Reputational Risk Agent Analysis:**
```
Input:
  - Payment History: 87% on-time
  - Recent Delinquencies: 1 (8 months ago)
  - Public Records: None (lien resolved)
  - Credit Inquiries (6mo): 4 (suggests seeking credit)

Scoring:
  - Payment History: 13/100 (87% on-time = fair, not excellent)
  - Delinquency Component: 20/100 (one recent shows struggle)
  - Public Records: 0/100 (resolved = clean now)
  - Inquiry Pattern: 10/100 (multiple recent inquiries = seeking credit)
  - Combined: 13 + 20 + 0 + 10 = 43

Output: Reputational Risk = 43/100 (medium reputational risk)

Critical Reputation Factor: Recent delinquency + multiple credit inquiries = potential financial stress
```

#### 6.2.3 Decision Synthesis

**Risk Score Calculation:**
```
Overall Risk = (39 × 0.35) + (36 × 0.25) + (53 × 0.25) + (43 × 0.15)
             = 13.65 + 9.0 + 13.25 + 6.45
             = 42.35
             = 42 (rounded)

Risk Classification: Low-Medium Risk (42 < 50)
```

**Critical Issues Identified:**
```
1. Missing Financial Documentation (tax returns 2 years)
   - Reason: Cannot verify self-employment income stability
   - Severity: Critical (blocks verification)

2. Business Plan Not Provided
   - Reason: Cannot assess use of funds or ROI
   - Severity: Critical (blocks business evaluation)

3. Recent Delinquency + Multiple Credit Inquiries
   - Reason: Suggests applicant under financial stress
   - Severity: High (indicates cash flow problems)

4. Self-Employment Income Volatility
   - Reason: Income projections less reliable
   - Severity: Medium (but offset by increasing trend)
```

**Mitigating Factors Identified:**
```
1. Income Trend is Increasing
   - Demonstrates business growth capability
   - Positive indicator for future capacity

2. Resolved Legal Lien
   - Shows willingness to resolve past issues
   - No active legal threats

3. Current DTI Still Acceptable
   - 29.2% current is within limits
   - Projected 33.3% remains acceptable
```

**Decision Logic Application:**
```
Check 1: Risk ≥ 85? No (42)
Check 2: Risk ≥ 50? No (42)
Check 3: Has Critical Issues? Yes (missing docs, delinquency)
Check 4: Has Mitigating Factors? Yes (increasing income, resolved lien)

Decision Path: "Critical issues WITH mitigation possible"
→ REVIEW

Confidence Calculation:
  - Base (Medium risk + critical issues with mitigation): 0.80
  - Data completeness (82%): 0.80 × 0.85 = 0.68 → round to 0.68
  - Missing critical data reduces confidence further: 0.68 - 0.05 = 0.63
  - Escalation flag (manual review needed): 0.63 + 0.15 = 0.78

Final Confidence: 0.78 (78%)
```

**Key Decision Factors:**
```
1. "Risk score 42 in low-medium range (0-49)"
2. "Critical documentation missing - tax returns and business plan required"
3. "Recent delinquency (8 months ago) indicates past cash flow stress"
4. "Self-employment income volatility moderately elevated"
5. "Mitigating factor: Income trend is increasing"
6. "Mitigating factor: Previous lien has been resolved"
7. "Current DTI 29.2% acceptable; projected DTI 33.3% acceptable"
8. "Multiple recent credit inquiries suggest seeking alternative funding"
```

#### 6.2.4 Final Decision Output

```json
{
  "applicant_id": "APP_BUS_2024_002",
  "classification": "REVIEW",
  "risk_score": 42,
  "confidence_level": 0.78,
  "requires_escalation": true,
  "escalation_reason": "Missing critical financial documentation and recent delinquency require underwriter judgment",
  "recommendation": "CONDITIONAL REVIEW - Request documentation; eligible for approval upon satisfactory verification",
  "key_decision_factors": [
    "Risk score 42 in low-medium range",
    "CRITICAL: Missing 2-year tax returns - cannot verify self-employment income",
    "CRITICAL: No business plan provided - cannot assess loan use and feasibility",
    "Recent delinquency (8 months ago) indicates past financial difficulty",
    "Self-employment income volatility moderate but trend is positive (increasing)",
    "DTI ratio 29.2% current (acceptable) and 33.3% projected (acceptable)",
    "Resolved legal lien from 2021 shows willingness to address obligations",
    "Multiple recent credit inquiries may indicate financial stress",
    "Fair payment history (87% on-time) but recent delinquency concerning"
  ],
  "required_actions": [
    "Obtain and verify 2 years of complete tax returns",
    "Request detailed business plan outlining loan use and revenue projections",
    "Obtain last 3 months of bank statements to verify income stability",
    "Request explanation for recent delinquency - was it resolved?",
    "Clarify purpose of multiple recent credit inquiries",
    "Consider requiring enhanced collateral or personal guarantee"
  ],
  "explanation": "While the overall risk score is moderate, critical gaps in documentation..."
}
```

**Loan Officer Review Note:**
```
"This application warrants manual review by senior underwriter.

POSITIVE FACTORS:
- Risk score 42 is acceptable
- Income trend is positive (business growing)
- DTI ratios acceptable
- Resolved historical lien shows good faith

CONCERNS TO RESOLVE:
- Cannot verify actual self-employment income without 2-year tax returns
- Recent delinquency (only 8 months ago) must be explained
- Multiple credit inquiries suggest applicant may be seeking funding elsewhere
- No business plan to justify $100K loan request

RECOMMENDED PATH:
1. Request documents within 5 business days
2. If documentation satisfactory → Likely Approval
3. If documentation inadequate → Recommend Decline or Reduce Loan Amount
4. Consider requiring co-signer or personal guarantee for risk mitigation

TIMELINE: Escalation case - expect 7-10 business days for underwriting review"
```

---

### 6.3 Complete Walkthrough Example 3: High-Risk Rejection Case

#### 6.3.1 Input Data

**Applicant Profile:**
```
ID: APP_RISK_2024_003
Name: James Thompson
Requested Loan: $75,000
Purpose: Debt consolidation
Income: $4,500/month
```

**Raw Data from ApplicantDB:**
```json
{
  "applicant_id": "APP_RISK_2024_003",
  "credit_score": 580,
  "monthly_gross_income": 4500,
  "monthly_debt_payments": 2800,
  "employment_status": "employed",
  "time_at_job": "6 months",
  "recent_delinquencies": 3,
  "delinquency_ages": ["2 months", "4 months", "6 months"],
  "charge_offs": 1,
  "bankruptcy": true,
  "bankruptcy_age": "3 years",
  "background_violations": ["fraud_allegation_2020", "fraud_charge_dismissed"],
  "documentation_completeness": 65,
  "payment_history_ontime_percent": 61,
  "public_records": ["civil_judgment_2019_unresolved"],
  "critical_flags": ["multiple_delinquencies", "fraud_history", "high_dti", "limited_stability"]
}
```

#### 6.3.2 Agent Analysis

**Financial Risk Agent Analysis:**
```
Input:
  - Credit Score: 580 (poor)
  - DTI Current: 2800 / 4500 = 62.2% (dangerous level)
  - DTI Projected: (2800 + 300) / 4500 = 68.9% (unacceptable)
  - Delinquencies: 3 recent
  - Charge-offs: 1
  - Bankruptcy: 3 years ago

Scoring:
  - Credit Component: 25/100 (580 = poor)
  - DTI Component: 10/100 (62% is dangerous; projected 68.9% impossible)
  - Delinquency Component: 15/100 (three recent delinquencies)
  - Charge-off Component: 5/100 (one charge-off indicates default)
  - Average: (25 + 10 + 15 + 5) / 4 = 13.75
  - Financial Risk Score: 100 - 13.75 = 86.25 → 86

Output: Financial Risk = 86/100 (CRITICAL - High financial risk)

Critical Issue: DTI at 62% means applicant cannot afford current obligations,
               much less additional debt
```

**Operational Risk Agent Analysis:**
```
Input:
  - Employment Status: Employed
  - Time at Job: 6 months (recent change)
  - Employment History: Multiple short-term positions (inferred from 6mo tenure)
  - Income Level: $4,500/month (low)

Scoring:
  - Employment Stability: 70/100 (only 6 months at current job = high turnover risk)
  - Income Level: 60/100 (low income for debt obligations)
  - Trend: Unknown (likely negative given bankruptcy 3yr ago)
  - Combined: (70 × 0.4) + (60 × 0.3) + (70 × 0.3) = 28 + 18 + 21 = 67

Output: Operational Risk = 67/100 (CRITICAL - High operational risk)

Critical Issue: Recent job change + low income = high probability of 
               employment loss or further income reduction
```

**Compliance Risk Agent Analysis:**
```
Input:
  - Background Violations: Fraud allegation (dismissed but on record)
  - Bankruptcy: Yes, 3 years ago (still visible on credit report)
  - Documentation Completeness: 65%
  - Public Records: Unresolved civil judgment from 2019

Scoring:
  - Fraud History: 40/100 (dismissed charge still raises concerns)
  - Bankruptcy: 50/100 (within 7-year reporting period)
  - Unresolved Judgment: 35/100 (active legal issue)
  - Documentation: 35/100 (only 65% complete)
  - Combined: 40 + 50 + 35 + 35 = 160 → cap at 100

Output: Compliance Risk = 95/100 (CRITICAL - Severe compliance risk)

Critical Issues: 
  1. Unresolved civil judgment indicates ongoing legal trouble
  2. Fraud allegation (even if dismissed) shows pattern risk
  3. Recent bankruptcy (3 years) within FHA/conventional limits
  4. Incomplete documentation hides information
```

**Reputational Risk Agent Analysis:**
```
Input:
  - Payment History: 61% on-time (very poor)
  - Delinquencies: 3 recent
  - Charge-offs: 1
  - Bankruptcy: 3 years ago
  - Public Records: Unresolved judgment

Scoring:
  - Payment History: 39/100 (61% on-time = severe default risk)
  - Delinquency Pattern: 50/100 (multiple recent = ongoing problem)
  - Charge-off: 20/100 (past default)
  - Bankruptcy: 40/100 (recent in terms of lending history)
  - Legal Issues: 30/100 (unresolved judgment)
  - Combined: 39 + 50 + 20 + 40 + 30 = 179 → normalized to 85/100

Output: Reputational Risk = 85/100 (CRITICAL - Severe reputational risk)

Critical Issue: Pattern shows chronic inability/unwillingness to meet 
               financial obligations
```

#### 6.3.3 Decision Synthesis

**Risk Score Calculation:**
```
Overall Risk = (86 × 0.35) + (67 × 0.25) + (95 × 0.25) + (85 × 0.15)
             = 30.1 + 16.75 + 23.75 + 12.75
             = 83.35
             = 83 (rounded)

Risk Classification: Medium-High Risk (83 in 50-84 range, borderline high)

CRITICAL ALERT: Score approaches high-risk threshold (85+)
```

**Critical Issues Assessment:**
```
Issue 1: UNMITIGABLE - Current DTI 62% is UNSUSTAINABLE
         - Applicant cannot afford current debt
         - Adding $75K loan mathematically impossible
         - Projected DTI 68.9% confirms applicant will DEFAULT
         - Severity: CRITICAL - Direct default prediction

Issue 2: UNMITIGABLE - Pattern of Non-Payment
         - 3 delinquencies in recent 6 months
         - 1 charge-off (past default)
         - 61% on-time payment rate (vs 85%+ industry standard)
         - Pattern shows applicant cannot/will not pay
         - Severity: CRITICAL - Behavioral risk

Issue 3: UNMITIGABLE - Active Legal Issues
         - Unresolved civil judgment from 2019
         - Fraud allegation on record (even if dismissed)
         - Indicates ongoing legal/compliance problems
         - Severity: CRITICAL - Legal exposure

Issue 4: SEVERE - Recent Major Financial Event
         - Bankruptcy only 3 years ago
         - Multiple delinquencies after bankruptcy
         - Shows no improvement trajectory post-bankruptcy
         - Severity: SEVERE - Bankruptcy didn't stabilize finances
```

**Mitigating Factors:**
```
Looking for ANY factors that might mitigate critical issues...

Possible Mitigant 1: "Requesting debt consolidation"
  - Analysis: Does NOT mitigate
  - Reason: Consolidation doesn't reduce total debt; if applicant cannot
            pay $2,800 now, paying $2,800 consolidated doesn't help
  - Actually makes worse: Adding $75K increases total debt to restructure

Possible Mitigant 2: "Currently employed"
  - Analysis: Does NOT mitigate
  - Reason: Employed for only 6 months (risky stability)
  - Plus: Even with employment, DTI unsustainable

Possible Mitigant 3: "Charged-off debt can be cleared"
  - Analysis: Does NOT mitigate
  - Reason: Clearing old debt doesn't address current delinquencies
  - Pattern suggests applicant will default on new loan too

CONCLUSION: NO MEANINGFUL MITIGATING FACTORS EXISTS
```

**Decision Logic Application:**
```
Check 1: Risk ≥ 85? Near-threshold (83, but borderline)
Check 2: Has Critical Issues? YES - Multiple unmitigable issues
Check 3: Has Mitigating Factors? NO - No meaningful mitigation

Decision Path: "Has critical issues AND NOT has mitigating factors"
→ REJECT

Confidence Calculation:
  - Base (Unmitigable critical issues): 0.90
  - Multiple confirmation of risk (all 4 agents high risk): 0.90 + 0.05 = 0.95
  - Data completeness (65%): 0.95 × 0.95 = 0.9025
  - Mathematical certainty (DTI makes default inevitable): 0.9025 + 0.02 = 0.92

Final Confidence: 0.92 (92%)

HIGH CONFIDENCE REJECTION: System and agents agree this is unacceptable risk
```

**Key Decision Factors:**
```
CRITICAL - Unmitigable Financial Insolvency:
1. "Current DTI 62% is mathematically unsustainable (over 43% threshold)"
2. "Projected DTI 68.9% makes loan default statistically certain"
3. "Cannot add $75K debt when current obligations are unpaid"

CRITICAL - Pattern of Non-Payment:
4. "3 recent delinquencies (2, 4, 6 months old) show ongoing payment failures"
5. "1 charge-off indicates past default on obligation"
6. "61% on-time payment rate far below industry standard (85%+)"

CRITICAL - Legal and Compliance Risks:
7. "Unresolved civil judgment from 2019 indicates ongoing legal exposure"
8. "Fraud allegation history (even if dismissed) raises conduct concerns"
9. "Bankruptcy 3 years ago - no meaningful recovery demonstrated"

OPERATIONAL - Stability Concerns:
10. "Only 6 months at current job - employment stability questionable"
11. "Low income ($4,500/month) insufficient for current obligations"
```

#### 6.3.4 Final Decision Output

```json
{
  "applicant_id": "APP_RISK_2024_003",
  "classification": "REJECT",
  "risk_score": 83,
  "confidence_level": 0.92,
  "requires_escalation": false,
  "recommendation": "DECLINE - Applicant presents unacceptable financial risk due to mathematical insolvency and pattern of non-payment",
  "denial_reason": "Mathematical default probability exceeds acceptable threshold",
  "key_decision_factors": [
    "CRITICAL: Current DTI 62.2% is unsustainable (acceptable max: 43%)",
    "CRITICAL: Projected DTI 68.9% makes loan default statistically inevitable",
    "CRITICAL: 3 recent delinquencies (2, 4, 6 months old) show ongoing default pattern",
    "CRITICAL: Past charge-off confirms prior default on loan obligations",
    "CRITICAL: 61% on-time payment rate indicates fundamental inability to meet obligations",
    "CRITICAL: Unresolved civil judgment from 2019 indicates active legal issues",
    "CRITICAL: Fraud allegation history (dismissed but on record) raises concerns",
    "SEVERE: Bankruptcy 3 years ago with no recovery trajectory",
    "SEVERE: Only 6 months employment tenure indicates instability",
    "SEVERE: Monthly income $4,500 insufficient for debt level"
  ],
  "technical_analysis": {
    "dti_current": "62.2% (unacceptable; max acceptable 43-50%)",
    "dti_projected": "68.9% (loan would make situation worse)",
    "payment_history": "61% on-time (vs 85%+ industry standard)",
    "default_probability": "High (pattern + mathematical insolvency)",
    "recovery_trajectory": "Negative (bankruptcy + continued delinquencies)"
  },
  "recommendation_details": "Applicant should not be approved under any circumstances for unsecured personal loan. Risk profile indicates systematic inability to manage debt obligations. Recommend: (1) Deny application, (2) Suggest applicant work with credit counseling before reapplying, (3) Re-evaluate in 12+ months if material circumstances improve (job stability, DTI reduction)",
  "risk_breakdown": {
    "financial_risk": 86,
    "operational_risk": 67,
    "compliance_risk": 95,
    "reputational_risk": 85
  },
  "timestamp": "2024-01-15T14:45:00Z"
}
```

**Loan Officer Decline Notice:**
```
DECISION: APPLICATION DENIED

Applicant: James Thompson (APP_RISK_2024_003)
Loan Amount Requested: $75,000
Purpose: Debt Consolidation
Decision Date: 2024-01-15

REASON FOR DENIAL:
Your loan application has been declined based on financial analysis indicating
unacceptable credit risk.

KEY CONCERNS:
1. DEBT-TO-INCOME RATIO: Your current monthly debt payments ($2,800) represent
   62% of your monthly income ($4,500). This ratio is unsustainable and exceeds
   our maximum acceptable threshold of 43%. Adding a $75,000 loan would increase
   your obligations to 68.9%, making it mathematically impossible to meet all
   obligations.

2. PAYMENT HISTORY: You have three recent delinquencies on your credit report
   (2, 4, and 6 months old), indicating ongoing difficulty managing current
   obligations. Additionally, one account was charged off (defaulted), and your
   overall on-time payment rate is only 61%.

3. BANKRUPTCY HISTORY: Your bankruptcy from 3 years ago, combined with continued
   delinquencies, indicates that your financial situation has not stabilized.

4. LEGAL ISSUES: An unresolved civil judgment from 2019 remains on your record.

WHAT YOU CAN DO:
We encourage you to take the following steps and reapply in 12+ months:
- Work with a credit counselor to develop a debt management plan
- Bring all delinquent accounts current
- Establish 12+ months of on-time payment history
- Increase income or reduce monthly debt obligations to below 43% DTI
- Resolve outstanding legal judgment

We appreciate your interest in our lending products. Please feel free to
contact us if you have questions about this decision.
```

---

## 7. Decision Framework Summary

### 7.1 Decision Matrix Quick Reference

| Risk Score | Status | Likely Decision | Confidence | Typical Path |
|---|---|---|---|---|
| 0-25 | Excellent | Approve | 95% | No escalation |
| 26-49 | Good | Approve | 90-95% | No escalation |
| 50-64 | Moderate | Review | 75-85% | Human review |
| 65-84 | High | Review | 80-85% | Escalation required |
| 85-100 | Very High | Reject | 90-95% | No escalation needed |

### 7.2 Agent Contribution Summary

- **Financial Agent (35% weight):** Primary decision driver - repayment capacity
- **Operational Agent (25% weight):** Stability and likelihood of continued capacity
- **Compliance Agent (25% weight):** Legal gatekeeping - regulatory requirements
- **Reputational Agent (15% weight):** Historical performance and market confidence

### 7.3 Confidence Level Interpretation

- **90-95%:** High confidence - strong agreement across agents, clear decision
- **80-89%:** Good confidence - minor uncertainties but decision well-supported
- **70-79%:** Moderate confidence - mitigating factors or mixed signals present
- **60-69%:** Low confidence - significant uncertainty; recommend human review
- **<60%:** Very low confidence - insufficient data or conflicting signals

### 7.4 Key Design Principles

1. **Transparency:** Every decision shows calculation, inputs, and reasoning
2. **Auditability:** Full trace from raw data → agent assessments → final decision
3. **Explainability:** Human-readable factors and recommendation explanations
4. **Consistency:** Same inputs produce same outputs across time
5. **Accountability:** Weights and rules documented and subject to change management
6. **Flexibility:** Manual review and escalation paths for edge cases

---

## Appendix A: Glossary

- **DTI (Debt-to-Income):** Monthly debt obligations divided by monthly gross income
- **Confidence Level:** Certainty of decision (0.0-1.0), NOT favorability of outcome
- **Risk Score:** Aggregate measure 0-100 combining four risk dimensions
- **Critical Issues:** Factors that may independently trigger rejection
- **Mitigating Factors:** Positive factors that can offset concerns
- **Escalation:** Flag for human expert review before final decision
- **Agent:** Autonomous module assessing one risk dimension independently

---

## Appendix B: Audit Trail Example

```json
{
  "audit_trail": {
    "decision_id": "DEC_2024_001_APP001",
    "timestamp": "2024-01-15T10:30:00Z",
    "stages": [
      {
        "stage": "data_ingestion",
        "timestamp": "2024-01-15T10:29:00Z",
        "source": "ApplicantDB",
        "record_count": 1,
        "fields_extracted": 18,
        "validation_status": "passed"
      },
      {
        "stage": "financial_risk_agent",
        "timestamp": "2024-01-15T10:29:30Z",
        "input_summary": "Credit 780, DTI 14%, 0 delinq",
        "output": { "risk_score": 8 },
        "reasoning": "Excellent credit, low DTI"
      },
      {
        "stage": "operational_risk_agent",
        "timestamp": "2024-01-15T10:29:45Z",
        "input_summary": "W-2 employed 5yr, stable income",
        "output": { "risk_score": 12 },
        "reasoning": "Stable employment, low volatility"
      },
      {
        "stage": "compliance_risk_agent",
        "timestamp": "2024-01-15T10:30:00Z",
        "input_summary": "Clean background, 98% docs",
        "output": { "risk_score": 2 },
        "reasoning": "No violations, complete documentation"
      },
      {
        "stage": "decision_synthesis",
        "timestamp": "2024-01-15T10:30:15Z",
        "calculation": "(8*0.35)+(12*0.25)+(2*0.25)+(8*0.15)=7.5",
        "final_risk_score": 8,
        "decision_path": "Risk < 50, no critical issues",
        "classification": "APPROVE",
        "confidence": 0.95
      }
    ],
    "decision": "APPROVE",
    "risk_score": 8,
    "confidence": 0.95,
    "exported_by": "DecisionSynthesisEngine_v1.2.1",
    "can_be_reviewed_until": "2024-04-15T23:59:59Z"
  }
}
```

---

**Document Version:** 1.0
**Last Updated:** 2024-01-15
**Applicable To:** LoanDecisionAgent, DecisionSynthesis MCP Server, All Risk Agents
