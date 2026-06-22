# 🎨 HOW TO START THE UI AND GIVE INPUT

## ⚡ QUICK START (2 minutes)

### Step 1: Open Terminal
```bash
cd /home/ubuntu/Desktop/demo
```

### Step 2: Start Streamlit UI
```bash
streamlit run app.py
```

### Step 3: View in Browser
The UI will automatically open at:
```
http://localhost:8501
```

---

## 📋 IF STREAMLIT IS NOT INSTALLED

### Install Streamlit
```bash
pip install streamlit
```

### Then run:
```bash
cd /home/ubuntu/Desktop/demo
streamlit run app.py
```

---

## 🎯 USING THE UI - STEP BY STEP

### **Page 1: Home/Dashboard**
When you open the app, you'll see:
- System overview
- Total applications processed
- Decision breakdown (approved vs rejected)
- Navigation sidebar

### **Page 2: Submit Application (MAIN)**

#### Fill in the form with applicant details:

**Personal Information:**
- Applicant ID: e.g., `APP_TEST_001`
- Name: e.g., `John Doe`
- Age: e.g., `35`

**Employment:**
- Employment Status: Select from dropdown
  - `employed`
  - `self-employed`
  - `unemployed`
- Years Employed: e.g., `8`

**Credit:**
- Credit Score: e.g., `750` (0-900 scale)

**Education:**
- Education Level: Select from dropdown
  - `high_school`
  - `bachelor`
  - `master`
  - `phd`

**Financial Information:**
- Annual Income: e.g., `75000`
- Monthly Expenses: e.g., `3000`
- Savings: e.g., `25000`
- Total Liabilities: e.g., `50000`

**Loan Request:**
- Loan Amount: e.g., `50000`
- Loan Tenure (months): e.g., `60`
- Existing Loans Count: e.g., `2`

### **Step 3: Click "Submit Application"**

The system will:
1. ✅ Validate input
2. ✅ Run profile analysis
3. ✅ Calculate financial risk
4. ✅ Make decision
5. ✅ Check compliance
6. ✅ Display results

### **Step 4: View Results**

You'll see:
```
DECISION: APPROVED ✓
SCORE: 92.25
CONFIDENCE: 95%

Key Factors:
+ Excellent credit score
+ Stable employment
+ Good savings
- Moderate DTI ratio

Compliance: PASSED ✓
```

---

## 📊 TEST SCENARIOS

### **Scenario 1: Approval Case**
```
Name: John Smith
Age: 35
Employment: employed (8 years)
Credit Score: 750
Education: bachelor
Income: $75,000
Expenses: $3,000
Savings: $25,000
Liabilities: $50,000
Loan: $50,000 for 60 months
Existing Loans: 2

Expected: APPROVED (Score ~92)
```

### **Scenario 2: Rejection Case**
```
Name: Robert Wilson
Age: 45
Employment: unemployed (0 years)
Credit Score: 450
Education: high_school
Income: $20,000
Expenses: $5,000
Savings: $1,000
Liabilities: $80,000
Loan: $100,000 for 60 months
Existing Loans: 5

Expected: REJECTED (Score ~5)
```

### **Scenario 3: Manual Review Case**
```
Name: Sarah Johnson
Age: 40
Employment: self-employed (3 years)
Credit Score: 650
Education: bachelor
Income: $60,000
Expenses: $3,500
Savings: $10,000
Liabilities: $40,000
Loan: $50,000 for 60 months
Existing Loans: 3

Expected: MANUAL_REVIEW (Score ~45)
```

---

## 📱 UI PAGES EXPLAINED

### **1. Home Page**
- Overview of system
- Statistics (total apps, approval rate)
- Quick navigation

### **2. Submit Application** ⭐ **MAIN PAGE**
- Form to submit new application
- Real-time validation
- Decision results display
- Detailed breakdown

### **3. Application History**
- View all submitted applications
- Search by applicant ID
- Filter by decision
- Export to CSV

### **4. Analytics**
- Approval rate chart
- Decision distribution
- Average score
- Risk analysis
- Time trends

### **5. Admin Settings** (if available)
- Configure risk thresholds
- Adjust decision weights
- View system health
- Check logs

---

## 🎮 INTERACTIVE FEATURES

### **Real-time Input Validation**
- ✅ Form validates as you type
- ✅ Shows errors for invalid inputs
- ✅ Prevents invalid submission

### **Decision Results**
- ✅ Decision type (Approved/Rejected/Review)
- ✅ Risk score (0-100)
- ✅ Confidence level (0-100%)
- ✅ Key factors breakdown
- ✅ Compliance status

### **History Tracking**
- ✅ All applications saved
- ✅ View past decisions
- ✅ Search functionality
- ✅ Export results

### **Analytics Dashboard**
- ✅ Charts and visualizations
- ✅ Statistical analysis
- ✅ Trend analysis
- ✅ Performance metrics

---

## 🔧 TROUBLESHOOTING

### **If Port 8501 is Already in Use**
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

### **If Page Doesn't Load**
```bash
# Clear cache and restart
rm -rf ~/.streamlit/
streamlit run app.py
```

### **If Form Won't Submit**
1. Check all required fields are filled
2. Verify numbers are valid ranges
3. Check console for error messages
4. Refresh page: Ctrl+R

### **If Results Don't Show**
1. Wait a moment (processing)
2. Check if application is still running
3. Look at console for errors
4. Restart app if needed

---

## 📊 EXAMPLE INPUT WALKTHROUGH

### **Complete Example:**

**Step 1:** Go to "Submit Application" page

**Step 2:** Fill in the form:
```
Applicant ID:        APP_DEMO_001
Name:               John Demo
Age:                35
Employment Status:  employed
Years Employed:     8
Credit Score:       750
Education Level:    bachelor
Annual Income:      75000
Monthly Expenses:   3000
Savings:            25000
Total Liabilities:  50000
Loan Amount:        50000
Loan Tenure:        60 (months)
Existing Loans:     2
```

**Step 3:** Click "Submit Application"

**Step 4:** See Results:
```
════════════════════════════
DECISION: APPROVED ✓
════════════════════════════

Risk Score:     92.25
Confidence:     95%

BREAKDOWN:
Profile Risk:    12.50
Financial Risk:  10.00
Combined Score:  92.25

KEY FACTORS:
✓ Excellent credit (750 score)
✓ Stable employment (8 years)
✓ Good savings ($25,000)
✓ Acceptable DTI (40%)
- Existing debt ($50,000)

COMPLIANCE: ✓ PASSED
- Age verification: OK
- AML/KYC check: OK
- Fraud detection: OK

CASE ID: CASE_20260620_001
════════════════════════════
```

---

## 🚀 ADVANCED OPTIONS

### **Run with Custom Configuration**
```bash
# Full width layout
streamlit run app.py --logger.level=debug

# Dark theme
streamlit run app.py --theme.base="dark"

# Different port
streamlit run app.py --server.port 9000
```

### **Run FastAPI Backend + Streamlit UI**
```bash
# Terminal 1: Start FastAPI
uvicorn main:app --port 8000

# Terminal 2: Start Streamlit
streamlit run app.py --server.port 8501
```

### **Run with Docker**
```bash
# Build
docker build -t loan-approval-system .

# Run
docker run -p 8000:8000 -p 8501:8501 loan-approval-system
```

---

## 💾 SAVING YOUR SESSION

### **Export Results**
In the "Application History" page:
1. Filter applications if needed
2. Click "Export to CSV"
3. Choose download location

### **View Decision Details**
Click on any application to see:
- Full decision details
- Risk factor breakdown
- Compliance checks
- Audit trail

---

## 🎓 WHAT TO EXPECT

### **Good Profile (Will Approve)**
- High credit score (750+)
- Stable employment (5+ years)
- Good savings
- Low DTI ratio
- **Expected Decision:** APPROVED ✓

### **Bad Profile (Will Reject)**
- Low credit score (<600)
- Unemployed
- No savings
- High DTI ratio
- **Expected Decision:** REJECTED ✓

### **Average Profile (Will Review)**
- Medium credit score (650)
- Recent employment
- Some savings
- Medium DTI ratio
- **Expected Decision:** MANUAL_REVIEW ⏳

---

## 📝 SAMPLE DATA TO COPY-PASTE

### **Good Applicant:**
```
Applicant ID: APP_GOOD_001
Name: Sarah Good
Age: 32
Employment: employed
Years: 7
Credit: 760
Education: bachelor
Income: 80000
Expenses: 2500
Savings: 35000
Liabilities: 40000
Loan Amount: 60000
Tenure: 60
Existing Loans: 1
```

### **Bad Applicant:**
```
Applicant ID: APP_BAD_001
Name: Robert Bad
Age: 50
Employment: unemployed
Years: 0
Credit: 420
Education: high_school
Income: 15000
Expenses: 6000
Savings: 500
Liabilities: 100000
Loan Amount: 150000
Tenure: 60
Existing Loans: 8
```

### **Average Applicant:**
```
Applicant ID: APP_AVG_001
Name: Mike Average
Age: 40
Employment: self-employed
Years: 3
Credit: 650
Education: bachelor
Income: 55000
Expenses: 3500
Savings: 12000
Liabilities: 45000
Loan Amount: 50000
Tenure: 60
Existing Loans: 2
```

---

## ✅ VERIFICATION CHECKLIST

After submitting an application, verify:

- [ ] Form accepted without errors
- [ ] Decision made (Approved/Rejected/Review)
- [ ] Risk score shown (0-100)
- [ ] Confidence level displayed
- [ ] Key factors listed
- [ ] Compliance status shown
- [ ] Results visible in UI
- [ ] Application in history
- [ ] Can export results

---

## 🎯 READY TO TEST!

1. ✅ Open terminal
2. ✅ Run `streamlit run app.py`
3. ✅ Browser opens automatically
4. ✅ Fill form with test data
5. ✅ Click Submit
6. ✅ See decision results

**It's that simple!** 🚀

---

**For more help:** Check `HOW_TO_EXECUTE.md` or `EXECUTION_GUIDE.md`

