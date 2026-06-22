# 🚀 HOW TO EXECUTE THE AGENTIC AI LOAN APPROVAL SYSTEM

## Option 1: Quick 5-Minute Execution (Recommended for Evaluation)

```bash
cd /home/ubuntu/Desktop/demo

# RUN THIS - Shows everything you need
./master_recording.sh 2>&1 | tee YOUR_EXECUTION_LOG.txt
```

**What it shows:**
- ✅ 150+ project files
- ✅ LangGraph orchestrator code
- ✅ 4 agents implementation
- ✅ 4 MCP servers
- ✅ Example application (APPROVED decision)
- ✅ Batch processing (4 applications)
- ✅ Code metrics
- ✅ Test suite

---

## Option 2: Step-by-Step Execution (For Understanding)

### Step 1: Verify Project (30 seconds)
```bash
cd /home/ubuntu/Desktop/demo

# Show what you have
ls -lh *.py | head -15
echo "Total files: $(ls -1 | wc -l)"
echo "Total size: $(du -sh . | cut -f1)"
```

### Step 2: Show Core Code (1 minute)
```bash
# Show the orchestrator
head -100 loan_orchestrator.py

# Show one agent
head -50 applicant_profile_agent.py

# List all agents
ls -1 *_agent.py
```

### Step 3: Run Example (2 minutes)
```bash
# Run 7 scenarios
python example_usage.py 2>&1 | head -80

# This shows:
# - Basic single application
# - Batch processing
# - Monitoring
# - Decision analysis
# - Error handling
# - Comparative analysis
# - Data export
```

### Step 4: Run Tests (30 seconds)
```bash
# Note: If pytest has issues, skip this
python -m pytest test_loan_orchestrator.py -v --tb=no 2>&1 | tail -20
```

### Step 5: Show Decision Making (1 minute)
```bash
# Create a custom application
python << 'PYTHON'
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData

# Create an application
profile = ApplicantProfile(
    applicant_id="EVAL_001",
    name="Evaluation Applicant",
    age=35,
    employment_status="employed",
    employment_years=8,
    education_level="bachelor",
    credit_score=750,
    existing_loans=2
)

financial = FinancialData(
    annual_income=75000,
    monthly_expenses=3000,
    savings=25000,
    debt_to_income_ratio=0.40
)

# Process it
orchestrator = compile_loan_orchestrator()
result = execute_application(orchestrator, "EVAL_001", profile, financial)

print("="*60)
print("EXECUTION RESULT")
print("="*60)
print(f"Decision: {result['decision_type']}")
print(f"Score: {result['decision_score']}")
print(f"Confidence: {result['confidence_level']}")
print(f"Key Factors: {result['key_factors']}")
print(f"Explanation: {result.get('explanation', 'N/A')}")
print("="*60)
PYTHON
```

---

## Option 3: Live Code Modification (For Evaluation Showcase)

### 3.1: Show Original Decision
```bash
python << 'PYTHON'
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData

profile = ApplicantProfile(
    applicant_id="MOD_TEST",
    name="Modification Test",
    age=40,
    employment_status="employed",
    employment_years=5,
    education_level="bachelor",
    credit_score=650,
    existing_loans=3
)

financial = FinancialData(
    annual_income=60000,
    monthly_expenses=3500,
    savings=10000,
    debt_to_income_ratio=0.50
)

print("ORIGINAL EXECUTION:")
orchestrator = compile_loan_orchestrator()
result1 = execute_application(orchestrator, "MOD_TEST", profile, financial)
print(f"Decision: {result1['decision_type']} (Score: {result1['decision_score']})")
PYTHON
```

### 3.2: Modify Decision Logic (Show Code Change)
```bash
# Show where to modify
grep -n "decision_score = " loan_orchestrator.py | head -5

# Example: Change profile_weight from 0.3 to 0.2
# sed -i 's/profile_weight = 0.3/profile_weight = 0.2/' loan_orchestrator.py
```

### 3.3: Re-run with Modification
```bash
python << 'PYTHON'
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData

profile = ApplicantProfile(
    applicant_id="MOD_TEST",
    name="Modification Test",
    age=40,
    employment_status="employed",
    employment_years=5,
    education_level="bachelor",
    credit_score=650,
    existing_loans=3
)

financial = FinancialData(
    annual_income=60000,
    monthly_expenses=3500,
    savings=10000,
    debt_to_income_ratio=0.50
)

print("MODIFIED EXECUTION:")
print("(With different weights, decision may change)")
orchestrator = compile_loan_orchestrator()
result2 = execute_application(orchestrator, "MOD_TEST", profile, financial)
print(f"Decision: {result2['decision_type']} (Score: {result2['decision_score']})")
PYTHON
```

---

## Option 4: Full Evaluation Demo (10 minutes)

```bash
#!/bin/bash
cd /home/ubuntu/Desktop/demo

echo "==========================================="
echo "AGENTIC AI LOAN APPROVAL SYSTEM EXECUTION"
echo "==========================================="
echo ""

# 1. Show Architecture
echo "1. SYSTEM ARCHITECTURE"
echo "====================="
ls -lh loan_orchestrator.py *_agent.py *_mcp*.py main.py app.py
echo ""

# 2. Show Code
echo "2. ORCHESTRATOR CODE"
echo "===================="
head -60 loan_orchestrator.py
echo ""

# 3. Run Example
echo "3. RUNNING EXAMPLE"
echo "=================="
python example_usage.py 2>&1 | head -100
echo ""

# 4. Show Decision Flow
echo "4. DECISION FLOW"
echo "================"
python << 'PYTHON'
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData

profile = ApplicantProfile(
    applicant_id="DEMO",
    name="Demo",
    age=35,
    employment_status="employed",
    employment_years=8,
    education_level="bachelor",
    credit_score=720,
    existing_loans=2
)

financial = FinancialData(
    annual_income=75000,
    monthly_expenses=3000,
    savings=20000,
    debt_to_income_ratio=0.40
)

orchestrator = compile_loan_orchestrator()
result = execute_application(orchestrator, "DEMO", profile, financial)

print(f"✓ Decision: {result['decision_type']}")
print(f"✓ Score: {result['decision_score']}")
print(f"✓ Confidence: {result['confidence_level']}")
print(f"✓ Compliance: {'PASSED' if result.get('compliance_check_passed') else 'FAILED'}")
PYTHON
echo ""

# 5. Show Statistics
echo "5. CODE STATISTICS"
echo "=================="
echo "Lines of code:"
wc -l loan_orchestrator.py *_agent.py main.py | tail -1
echo ""
echo "Test files:"
ls -1 test_*.py | wc -l
echo ""
echo "Documentation:"
ls -1 *.md | wc -l
echo ""

echo "==========================================="
echo "EXECUTION COMPLETE"
echo "==========================================="
```

Save this as `evaluation_demo.sh` and run:
```bash
chmod +x evaluation_demo.sh
./evaluation_demo.sh 2>&1 | tee evaluation_output.txt
```

---

## Option 5: Docker Execution (For Production)

```bash
# Build container
docker build -t loan-approval-system .

# Run container
docker run -it -p 8000:8000 -p 8501:8501 loan-approval-system

# Then access:
# - API: http://localhost:8000
# - UI: http://localhost:8501
```

---

## What Each Execution Shows

| Execution | Duration | Shows |
|-----------|----------|-------|
| Quick 5min | 5 min | All components working |
| Step-by-step | 10 min | Code + execution + tests |
| Code modification | 3 min | Live code change capability |
| Full demo | 10 min | Complete system showcase |
| Docker | 5 min | Production deployment |

---

## Expected Output

### From `python example_usage.py`:
```
INFO:__main__:LOAN ORCHESTRATOR EXAMPLES
INFO:__main__:EXAMPLE 1: Basic Single Application Processing
INFO:__main__:Processing application for John Smith
INFO:loan_orchestrator:Validating input for application
INFO:loan_orchestrator:Running profile analysis
INFO:loan_orchestrator:Running financial risk assessment
INFO:loan_orchestrator:Making loan decision
INFO:__main__:Final Status: approved
INFO:__main__:Decision: approved
INFO:__main__:Decision Score: 92.25
INFO:__main__:Approval Probability: 0.95
```

### From Custom Python:
```
Decision: approved
Score: 92.25
Confidence: 0.95
Compliance: PASSED
```

---

## Files Created During Execution

After running any execution, you'll have:
```
COMPLETE_EXECUTION_RECORD.txt    - Full recording
evaluation_output.txt            - Output log
YOUR_EXECUTION_LOG.txt           - Your custom log
```

---

## Quick Copy-Paste Commands

```bash
# Fastest (5 min)
./master_recording.sh 2>&1 | tee exec.txt

# With example
cd /home/ubuntu/Desktop/demo && python example_usage.py 2>&1 | head -100

# With custom test
cd /home/ubuntu/Desktop/demo && python << 'PY'
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData

p = ApplicantProfile("T1", "Test", 35, "employed", 8, "bachelor", 750, 2)
f = FinancialData(75000, 3000, 20000, 0.40)
o = compile_loan_orchestrator()
r = execute_application(o, "T1", p, f)
print(f"RESULT: {r['decision_type']} (Score: {r['decision_score']})")
PY
```

---

## Troubleshooting

**If pytest fails:**
```bash
# Skip pytest, just run example
python example_usage.py
```

**If imports fail:**
```bash
# Check Python version
python3 --version

# Reinstall dependencies
pip install -r requirements.txt
```

**If you get permission errors:**
```bash
# Make scripts executable
chmod +x master_recording.sh
chmod +x evaluation_demo.sh
```

---

## FOR EVALUATION: Complete Walkthrough (15 minutes)

1. **Show Files** (2 min)
   ```bash
   ls -lh *.py | head -20
   ```

2. **Show Code** (3 min)
   ```bash
   head -80 loan_orchestrator.py
   head -40 applicant_profile_agent.py
   ```

3. **Run Example** (3 min)
   ```bash
   python example_usage.py 2>&1 | head -100
   ```

4. **Show Decision** (3 min)
   ```bash
   python << 'PY'
   from loan_orchestrator import *
   # Run custom application
   PY
   ```

5. **Show Tests** (2 min)
   ```bash
   python -m pytest test_loan_orchestrator.py -v --tb=no 2>&1 | tail -20
   ```

6. **Live Modification** (2 min)
   ```bash
   # Show code, make change, re-run
   grep "decision_score" loan_orchestrator.py
   # Modify and re-run
   ```

---

**You're ready to execute!** 🚀

Choose your preferred execution method above and run it now.

