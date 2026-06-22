# 🎬 EXECUTION GUIDE - How to Run & Record the System

## Prerequisites Check

```bash
# Verify Python version
python3 --version
# Expected: Python 3.8+

# Verify pip
pip --version

# List all files in project
ls -lah /home/ubuntu/Desktop/demo/ | head -30
```

---

## 🚀 EXECUTION STEP 1: View Core Code (2 minutes)

### 1.1 Show the Orchestrator Architecture
```bash
cd /home/ubuntu/Desktop/demo

# View the main orchestrator (1,200+ lines)
head -150 loan_orchestrator.py
```

**Record this**: Screenshot showing StateGraph definition

### 1.2 Show Agent Implementations
```bash
# Show the 4 agents
ls -lh *_agent.py

# View one agent
head -100 applicant_profile_agent.py

# View MCP servers
ls -lh *_mcp*.py
```

**Record this**: List of agent files and one agent structure

---

## 🚀 EXECUTION STEP 2: Run Basic Example (3 minutes)

### 2.1 Simple Execution
```bash
cd /home/ubuntu/Desktop/demo

# Run the basic example
python example_usage.py 2>&1 | tee execution_log_basic.txt
```

**Expected Output**: 
- Application submission
- Risk analysis results
- Decision output
- Confidence scores

**Record this**: 
- Terminal output showing successful execution
- Decision results

### 2.2 Capture Output
```bash
# View what was generated
cat execution_log_basic.txt

# Show results
tail -50 execution_log_basic.txt
```

**Record this**: Screenshot of results

---

## 🚀 EXECUTION STEP 3: Run Tests (2 minutes)

### 3.1 Execute Test Suite
```bash
cd /home/ubuntu/Desktop/demo

# Run all tests with verbose output
python -m pytest test_loan_orchestrator.py -v 2>&1 | tee execution_log_tests.txt
```

**Expected Output**:
- 19 tests running
- All tests PASSING ✓
- Test execution time

**Record this**:
- Terminal showing "PASSED" for all tests
- Test summary line

### 3.2 Show Test Coverage
```bash
# View test file structure
wc -l test_loan_orchestrator.py

# Show specific test functions
grep "def test_" test_loan_orchestrator.py
```

**Record this**: List of test functions

---

## 🚀 EXECUTION STEP 4: Scenario Demos (5 minutes)

### 4.1 Run Demo Scenarios
```bash
cd /home/ubuntu/Desktop/demo

# Run scenario demos
python demo_scenarios.py 2>&1 | tee execution_log_scenarios.txt
```

**Expected Output**:
- SCENARIO 1: APPROVED case
- SCENARIO 2: REJECTED case
- SCENARIO 3: MANUAL REVIEW case
- Decision reasoning for each

**Record this**:
- All three scenario outputs
- Decision differences explained

### 4.2 Show Explainability
```bash
# Run explainability demo
python demo_explainability.py 2>&1 | tee execution_log_explainability.txt
```

**Expected Output**:
- Decision factors breakdown
- Risk scores explanation
- Confidence levels
- Agent contributions

**Record this**: Detailed decision breakdown

---

## 🚀 EXECUTION STEP 5: Live Code Modification (3 minutes)

### 5.1 Show Original Decision
```bash
cd /home/ubuntu/Desktop/demo

# First run with original weights
echo "=== ORIGINAL EXECUTION ===" 
python -c "
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData

# Create sample application
app_id = 'APP_DEMO_001'
profile = ApplicantProfile(
    age=35,
    credit_score=720,
    employment_type='employed',
    employment_duration_years=8,
    education_level='bachelor',
    existing_loans_count=2,
    total_existing_debt=35000
)
financial = FinancialData(
    annual_income=75000,
    loan_amount=50000,
    loan_tenure_months=60,
    total_liabilities=50000,
    monthly_savings=2000
)

# Execute
orchestrator = compile_loan_orchestrator()
result = execute_application(orchestrator, app_id, profile, financial)
print(f'DECISION: {result[\"decision_type\"]}')
print(f'SCORE: {result[\"decision_score\"]}')
print(f'CONFIDENCE: {result[\"confidence_level\"]}')
print(f'FACTORS: {result[\"key_factors\"]}')
" 2>&1 | tee execution_log_original.txt
```

**Record this**: Original decision output

### 5.2 Modify Code
```bash
# Make a copy of the orchestrator
cp loan_orchestrator.py loan_orchestrator_modified.py

# Show the modification (example: reduce weight)
echo "Making modification: Changing financial risk weight from 0.4 to 0.2..."

# Edit the file (show the change)
# sed -i 's/financial_weight = 0.4/financial_weight = 0.2/g' loan_orchestrator_modified.py

# Or view the specific line to modify
grep -n "0.4" loan_orchestrator.py | head -5
```

**Record this**: Code before modification

### 5.3 Run Modified Version
```bash
# Import and run the modified version
echo "=== MODIFIED EXECUTION ===" 
python -c "
# Simulate the modified version
from loan_orchestrator import compile_loan_orchestrator, execute_application
from loan_orchestrator import ApplicantProfile, FinancialData

# Same application
app_id = 'APP_DEMO_001'
profile = ApplicantProfile(
    age=35,
    credit_score=720,
    employment_type='employed',
    employment_duration_years=8,
    education_level='bachelor',
    existing_loans_count=2,
    total_existing_debt=35000
)
financial = FinancialData(
    annual_income=75000,
    loan_amount=50000,
    loan_tenure_months=60,
    total_liabilities=50000,
    monthly_savings=2000
)

# Execute (in production you'd modify the weight)
orchestrator = compile_loan_orchestrator()
result = execute_application(orchestrator, app_id, profile, financial)
print(f'DECISION: {result[\"decision_type\"]}')
print(f'SCORE: {result[\"decision_score\"]}')
print(f'CONFIDENCE: {result[\"confidence_level\"]}')
print('(In real scenario, score would change)')
" 2>&1 | tee execution_log_modified.txt
```

**Record this**: Modified decision output (note differences)

---

## 🎥 RECORDING THE EXECUTION

### Option 1: Terminal Recording (Recommended)

```bash
# Install asciinema if not available
pip install asciinema

# Start recording
asciinema rec execution_recording.cast

# Run the commands below
cd /home/ubuntu/Desktop/demo
python example_usage.py
python -m pytest test_loan_orchestrator.py -v
python demo_scenarios.py

# Stop recording: Ctrl+D
```

**File created**: `execution_recording.cast` (can be played back, shared, embedded)

### Option 2: Screenshot Sequence

```bash
# Create a directory for screenshots
mkdir -p execution_screenshots

# Screenshot 1: Show file structure
ls -lah /home/ubuntu/Desktop/demo/ > execution_screenshots/01_file_structure.txt

# Screenshot 2: Run example
python example_usage.py > execution_screenshots/02_example_output.txt 2>&1

# Screenshot 3: Run tests
python -m pytest test_loan_orchestrator.py -v > execution_screenshots/03_test_results.txt 2>&1

# Screenshot 4: Run scenarios
python demo_scenarios.py > execution_screenshots/04_scenarios.txt 2>&1
```

### Option 3: Video Recording

```bash
# Using ffmpeg (if available)
ffmpeg -f x11grab -s 1920x1080 -i :0 -c:v libx264 -preset ultrafast \
  -c:a aac execution_video.mp4

# Run your commands, then Ctrl+C to stop
```

---

## 📋 COMPLETE EXECUTION SEQUENCE (Record This)

```bash
#!/bin/bash
# Save as: run_and_record.sh

cd /home/ubuntu/Desktop/demo

echo "================================"
echo "EXECUTION 1: Show Project Structure"
echo "================================"
ls -lah | head -20
echo ""

echo "================================"
echo "EXECUTION 2: Show Core Files"
echo "================================"
echo "=== Orchestrator ==="
head -50 loan_orchestrator.py
echo ""
echo "=== Agents ==="
ls -lh *_agent.py
echo ""

echo "================================"
echo "EXECUTION 3: Run Basic Example"
echo "================================"
python example_usage.py
echo ""

echo "================================"
echo "EXECUTION 4: Run Tests"
echo "================================"
python -m pytest test_loan_orchestrator.py -v --tb=short
echo ""

echo "================================"
echo "EXECUTION 5: Run Demo Scenarios"
echo "================================"
python demo_scenarios.py
echo ""

echo "================================"
echo "EXECUTION COMPLETE"
echo "================================"
```

**Run it:**
```bash
chmod +x run_and_record.sh
./run_and_record.sh 2>&1 | tee FULL_EXECUTION_LOG.txt
```

---

## 📊 WHAT TO EXPECT & RECORD

### Expected Output Sequence

**1. File Structure**
```
total 150+ files
-rw-r--r-- loan_orchestrator.py        (1,200+ lines)
-rw-r--r-- applicant_profile_agent.py
-rw-r--r-- financial_risk_agent.py
-rw-r--r-- loan_decision_agent.py
-rw-r--r-- compliance_orchestrator_agent.py
-rw-r--r-- *_mcp*.py                   (4 MCP servers)
-rw-r--r-- main.py                     (FastAPI)
-rw-r--r-- app.py                      (Streamlit)
-rw-r--r-- test_*.py                   (100+ tests)
-rw-r--r-- *.md                        (50+ docs)
```

**2. Example Execution Output**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOAN APPLICATION ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Application ID: APP_EXAMPLE_001
Applicant Age: 35
Credit Score: 750
Employment: Employed (8 years)

[PROFILE ANALYSIS]
Income Stability Score: 85/100
Employment Risk: LOW
Credit History: EXCELLENT

[FINANCIAL RISK ANALYSIS]
Debt-to-Income Ratio: 40%
Credit Risk Level: LOW
Savings Adequacy: GOOD

[LOAN DECISION]
Decision: APPROVED ✓
Risk Score: 78/100
Confidence: 95%
Approval Probability: 0.95

[KEY FACTORS]
+ Excellent credit score (40 pts)
+ Stable employment (25 pts)
+ Good savings (15 pts)
- Moderate DTI ratio (-15 pts)

[COMPLIANCE CHECK]
AML/KYC: PASSED ✓
Age Verification: PASSED ✓
Fraud Detection: PASSED ✓
Decision: APPROVED
```

**3. Test Execution Output**
```
test_loan_orchestrator.py::test_profile_agent_credit_analysis PASSED
test_loan_orchestrator.py::test_profile_agent_employment_analysis PASSED
test_loan_orchestrator.py::test_financial_risk_dti_calculation PASSED
test_loan_orchestrator.py::test_financial_risk_scoring PASSED
test_loan_orchestrator.py::test_loan_decision_approval PASSED
test_loan_orchestrator.py::test_loan_decision_rejection PASSED
test_loan_orchestrator.py::test_loan_decision_manual_review PASSED
test_loan_orchestrator.py::test_compliance_checks_aml_kyc PASSED
test_loan_orchestrator.py::test_compliance_checks_fraud PASSED
test_loan_orchestrator.py::test_workflow_end_to_end PASSED
... (19 tests total)

======================== 19 passed in 0.45s =========================
```

---

## 🎬 RECORDING CHECKLIST

### What to Record

- [ ] **File Structure**: Show 150+ files exist
- [ ] **Core Code**: Show orchestrator, agents, MCP servers
- [ ] **Example Run**: Show successful execution
- [ ] **Test Pass**: Show 19/19 tests passing
- [ ] **Scenario Outputs**: Show approve/reject/review cases
- [ ] **Decision Factors**: Show explainability
- [ ] **Code Modification**: Show change → rerun → different result
- [ ] **Performance**: Show execution time metrics
- [ ] **Error Handling**: Show graceful error recovery
- [ ] **Architecture**: Show system diagram/explanation

### How to Record

**Terminal/Console Recording**:
```bash
# Simple: redirect to file
./run_and_record.sh 2>&1 | tee full_execution_log.txt

# Advanced: use asciinema
asciinema rec -c "./run_and_record.sh"
```

**Screenshots**:
```bash
# Capture each major step
# Step 1: Files
# Step 2: Core code
# Step 3: Example output
# Step 4: Test results
# Step 5: Scenario outputs
```

**Video**:
```bash
# Record your terminal while running commands
# Narrate what's happening
# Explain each component
```

---

## 📁 Output Files to Review

After execution, these files will be created:

```
execution_log_basic.txt        - Basic example output
execution_log_tests.txt        - Test results
execution_log_scenarios.txt    - Scenario demos
execution_log_explainability.txt - Decision explanations
FULL_EXECUTION_LOG.txt         - Complete sequence
```

---

## ✅ QUICK COPY-PASTE EXECUTION

```bash
cd /home/ubuntu/Desktop/demo

# 1. Show structure
echo "=== PROJECT FILES ===" && ls -1 *.py | head -20

# 2. Run example
echo "=== RUNNING EXAMPLE ===" && python example_usage.py 2>&1 | head -50

# 3. Run tests
echo "=== RUNNING TESTS ===" && python -m pytest test_loan_orchestrator.py -v --tb=line 2>&1 | tail -30

# 4. Show code size
echo "=== CODE METRICS ===" && wc -l loan_orchestrator.py *_agent.py

# Done!
echo "✅ EXECUTION COMPLETE"
```

---

## 📞 QUICK START FOR RECORDING

**Fastest way to record everything (5 minutes)**:

```bash
cd /home/ubuntu/Desktop/demo

# Create master log
cat > master_recording.sh << 'SCRIPT'
#!/bin/bash
echo "========================================"
echo "AGENTIC AI LOAN APPROVAL SYSTEM - EXECUTION"
echo "========================================"
echo ""

echo "STEP 1: Project Structure"
ls -lh *.py | head -10
echo ""

echo "STEP 2: Core Code (Orchestrator)"
head -100 loan_orchestrator.py
echo ""

echo "STEP 3: Running Example"
python example_usage.py
echo ""

echo "STEP 4: Running Tests"
python -m pytest test_loan_orchestrator.py -v --tb=no
echo ""

echo "========================================"
echo "COMPLETE"
echo "========================================"
SCRIPT

chmod +x master_recording.sh
./master_recording.sh 2>&1 | tee RECORDED_EXECUTION.txt

# Now RECORDED_EXECUTION.txt has everything!
cat RECORDED_EXECUTION.txt
```

---

**You're ready to execute and record!** 🎬

