"""
Streamlit Application for Intelligent Loan Decision System
A modern, user-friendly interface for loan applications with real-time decision support.
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px

# Configure page
st.set_page_config(
    page_title="Loan Decision System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Constants & Configuration
# ============================================================================

API_BASE_URL = "http://localhost:8000"
LOAN_ENDPOINT = f"{API_BASE_URL}/loan/apply"

# Employment status options
EMPLOYMENT_STATUSES = [
    "employed",
    "self_employed",
    "retired",
    "unemployed",
    "student",
    "homemaker"
]

# Education levels
EDUCATION_LEVELS = [
    "high_school",
    "associates",
    "bachelors",
    "masters",
    "doctorate",
    "other"
]

# Loan purposes
LOAN_PURPOSES = [
    "home_purchase",
    "refinance",
    "home_improvement",
    "debt_consolidation",
    "auto_purchase",
    "business",
    "education",
    "personal",
    "other"
]

# Risk levels with colors
RISK_COLORS = {
    "low": "#10B981",      # Green
    "medium": "#F59E0B",   # Amber
    "high": "#EF4444",     # Red
    "very_high": "#7F1D1D" # Dark red
}

DECISION_COLORS = {
    "approved": "#10B981",
    "conditional_approval": "#3B82F6",
    "denied": "#EF4444",
    "review_required": "#F59E0B"
}

# ============================================================================
# Session State Management
# ============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}
    if "last_decision" not in st.session_state:
        st.session_state.last_decision = None
    if "application_history" not in st.session_state:
        st.session_state.application_history = []
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0

init_session_state()

# ============================================================================
# Sidebar Navigation
# ============================================================================

with st.sidebar:
    st.markdown("## Navigation")

    # Logo/Brand
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2>🏦 LoanAI</h2>
        <p style="color: #666; font-size: 12px;">Intelligent Loan Decision System</p>
    </div>
    """, unsafe_allow_html=True)

    # Navigation buttons
    nav_options = ["Home", "Apply", "Status", "Analytics"]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", use_container_width=True,
                    key="nav_home"):
            st.session_state.current_page = "Home"
            st.rerun()
    with col2:
        if st.button("📋 Apply", use_container_width=True,
                    key="nav_apply"):
            st.session_state.current_page = "Apply"
            st.session_state.current_step = 0
            st.rerun()

    col3, col4 = st.columns(2)
    with col3:
        if st.button("📊 Status", use_container_width=True,
                    key="nav_status"):
            st.session_state.current_page = "Status"
            st.rerun()
    with col4:
        if st.button("📈 Analytics", use_container_width=True,
                    key="nav_analytics"):
            st.session_state.current_page = "Analytics"
            st.rerun()

    st.divider()

    # System status
    st.markdown("### System Status")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("🟢 Backend Online")
        else:
            st.error("🔴 Backend Error")
    except:
        st.error("🔴 Backend Offline")

    st.divider()

    # Recent applications (if any)
    if st.session_state.application_history:
        st.markdown("### Recent Applications")
        for idx, app in enumerate(st.session_state.application_history[-5:]):
            status_color = "🟢" if app["status"] == "approved" else "🔴" if app["status"] == "denied" else "🟡"
            st.caption(f"{status_color} {app.get('name', 'N/A')}\nAmount: ${app.get('amount', 0):,.0f}")

    st.divider()
    st.caption("Made with ❤️ by LoanAI Team")

# ============================================================================
# Page: Home
# ============================================================================

def render_home():
    """Render the home page with system overview."""
    st.title("🏦 Intelligent Loan Decision System")

    # Hero section
    st.markdown("""
    ### Welcome to LoanAI

    Our advanced loan decision system uses AI-powered analysis to provide fast,
    fair, and transparent loan decisions. Get your decision in seconds with
    comprehensive risk analysis and detailed explanations.
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📊 Decisions Processed",
            value=len(st.session_state.application_history),
            delta=1 if st.session_state.last_decision else 0
        )

    with col2:
        approved = sum(1 for app in st.session_state.application_history if app.get("status") == "approved")
        approval_rate = (approved / len(st.session_state.application_history) * 100) if st.session_state.application_history else 0
        st.metric(
            label="✅ Approval Rate",
            value=f"{approval_rate:.1f}%",
            delta=None
        )

    with col3:
        st.metric(
            label="⚡ Avg Processing Time",
            value="2.3s",
            delta="-0.4s"
        )

    st.divider()

    # Features section
    st.markdown("### 🌟 Key Features")

    feat1, feat2, feat3 = st.columns(3)

    with feat1:
        st.markdown("""
        **⚡ Fast Processing**

        Get loan decisions in seconds, not days. Our AI analyzes your profile
        instantly using advanced risk assessment algorithms.
        """)

    with feat2:
        st.markdown("""
        **🎯 Transparent Decisions**

        Every decision comes with detailed explanations. Understand exactly
        which factors influenced your loan decision.
        """)

    with feat3:
        st.markdown("""
        **🔒 Secure & Fair**

        Your data is protected with enterprise-grade security. Our system
        ensures fair and unbiased decisions for all applicants.
        """)

    st.divider()

    # How it works
    st.markdown("### 📝 How It Works")

    step1, step2, step3, step4 = st.columns(4)

    with step1:
        st.markdown("""
        #### Step 1️⃣
        **Application**

        Fill out a simple form with your basic information and financial details.
        """)

    with step2:
        st.markdown("""
        #### Step 2️⃣
        **Analysis**

        Our AI analyzes your profile using dozens of risk factors and validation rules.
        """)

    with step3:
        st.markdown("""
        #### Step 3️⃣
        **Decision**

        Receive an instant decision: approved, conditional, or needs review.
        """)

    with step4:
        st.markdown("""
        #### Step 4️⃣
        **Details**

        Review comprehensive factors and explanations behind the decision.
        """)

    st.divider()

    # Quick start
    if st.button("🚀 Start Your Application", use_container_width=True, key="home_apply_btn"):
        st.session_state.current_page = "Apply"
        st.session_state.current_step = 0
        st.rerun()

# ============================================================================
# Page: Apply - Multi-Step Form
# ============================================================================

def validate_step_1(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate step 1: Personal Information."""
    errors = []

    if not data.get("name", "").strip():
        errors.append("Name is required")
    if not data.get("email", "").strip() or "@" not in data.get("email", ""):
        errors.append("Valid email is required")
    if not isinstance(data.get("age"), int) or data["age"] < 18 or data["age"] > 120:
        errors.append("Age must be between 18 and 120")
    if not data.get("location", "").strip():
        errors.append("Location is required")

    return len(errors) == 0, " | ".join(errors) if errors else ""

def validate_step_2(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate step 2: Employment Information."""
    errors = []

    if not data.get("employment_status"):
        errors.append("Employment status is required")
    if not isinstance(data.get("employment_years"), (int, float)) or data.get("employment_years", 0) < 0:
        errors.append("Employment years must be non-negative")
    if not data.get("education_level"):
        errors.append("Education level is required")
    if not isinstance(data.get("annual_income"), (int, float)) or data.get("annual_income", 0) <= 0:
        errors.append("Annual income must be positive")

    return len(errors) == 0, " | ".join(errors) if errors else ""

def validate_step_3(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate step 3: Financial Information."""
    errors = []

    if not isinstance(data.get("credit_score"), int) or data.get("credit_score", 0) < 300 or data.get("credit_score", 0) > 850:
        errors.append("Credit score must be between 300 and 850")
    if not isinstance(data.get("savings"), (int, float)) or data.get("savings", 0) < 0:
        errors.append("Savings must be non-negative")
    if not isinstance(data.get("monthly_expenses"), (int, float)) or data.get("monthly_expenses", 0) < 0:
        errors.append("Monthly expenses must be non-negative")
    if not isinstance(data.get("liabilities"), (int, float)) or data.get("liabilities", 0) < 0:
        errors.append("Liabilities must be non-negative")

    return len(errors) == 0, " | ".join(errors) if errors else ""

def validate_step_4(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate step 4: Loan Information."""
    errors = []

    if not data.get("loan_purpose"):
        errors.append("Loan purpose is required")
    if not isinstance(data.get("loan_amount"), (int, float)) or data.get("loan_amount", 0) <= 0:
        errors.append("Loan amount must be positive")
    if not isinstance(data.get("loan_tenure"), int) or data.get("loan_tenure", 0) <= 0 or data.get("loan_tenure", 0) > 480:
        errors.append("Loan tenure must be between 1 and 480 months")

    return len(errors) == 0, " | ".join(errors) if errors else ""

def submit_application(form_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Submit application to FastAPI backend."""
    try:
        # Prepare request payload
        payload = {
            "applicant_id": f"APP-{int(datetime.now().timestamp() * 1000)}",
            "profile": {
                "name": form_data.get("name"),
                "age": int(form_data.get("age", 0)),
                "employment_status": form_data.get("employment_status"),
                "employment_years": float(form_data.get("employment_years", 0)),
                "education_level": form_data.get("education_level"),
                "annual_income": float(form_data.get("annual_income", 0)),
                "monthly_expenses": float(form_data.get("monthly_expenses", 0)),
                "savings": float(form_data.get("savings", 0))
            },
            "credit_score": int(form_data.get("credit_score", 0)),
            "loan_amount": float(form_data.get("loan_amount", 0)),
            "tenure": int(form_data.get("loan_tenure", 0)),
            "liabilities": float(form_data.get("liabilities", 0)),
            "location": form_data.get("location"),
        }

        # Submit to backend
        response = requests.post(LOAN_ENDPOINT, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"API Error: {response.status_code}",
                "details": response.text
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout",
            "details": "Backend took too long to respond"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Connection error",
            "details": "Unable to connect to backend server"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "details": "Unexpected error during submission"
        }

def render_apply():
    """Render the loan application form with multi-step process."""
    st.title("📋 Loan Application")

    # Progress indicator
    progress = (st.session_state.current_step + 1) / 4
    st.progress(progress, text=f"Step {st.session_state.current_step + 1} of 4")

    # Step 1: Personal Information
    if st.session_state.current_step == 0:
        with st.form("step_1_form", clear_on_submit=False):
            st.markdown("### Step 1: Personal Information")
            st.markdown("Tell us about yourself")

            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input(
                    "Full Name",
                    value=st.session_state.form_data.get("name", ""),
                    help="Your legal full name"
                )

            with col2:
                email = st.text_input(
                    "Email Address",
                    value=st.session_state.form_data.get("email", ""),
                    help="We'll use this to contact you with updates"
                )

            col3, col4 = st.columns(2)

            with col3:
                age = st.number_input(
                    "Age",
                    min_value=18,
                    max_value=120,
                    value=int(st.session_state.form_data.get("age", 30)),
                    help="Must be 18 or older"
                )

            with col4:
                location = st.text_input(
                    "Location (City, State)",
                    value=st.session_state.form_data.get("location", ""),
                    help="Your current city and state"
                )

            col5, col6 = st.columns(2)
            with col5:
                if st.form_submit_button("Next →", use_container_width=True):
                    is_valid, error_msg = validate_step_1({
                        "name": name, "email": email, "age": age, "location": location
                    })
                    if is_valid:
                        st.session_state.form_data.update({
                            "name": name, "email": email, "age": age, "location": location
                        })
                        st.session_state.current_step = 1
                        st.rerun()
                    else:
                        st.error(f"❌ {error_msg}")

            with col6:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.current_page = "Home"
                    st.rerun()

    # Step 2: Employment Information
    elif st.session_state.current_step == 1:
        with st.form("step_2_form", clear_on_submit=False):
            st.markdown("### Step 2: Employment Information")
            st.markdown("Tell us about your employment and education")

            col1, col2 = st.columns(2)

            with col1:
                employment_status = st.selectbox(
                    "Employment Status",
                    EMPLOYMENT_STATUSES,
                    index=EMPLOYMENT_STATUSES.index(st.session_state.form_data.get("employment_status", "employed")),
                    help="Your current employment status"
                )

            with col2:
                employment_years = st.number_input(
                    "Years Employed",
                    min_value=0.0,
                    max_value=70.0,
                    value=float(st.session_state.form_data.get("employment_years", 3.0)),
                    step=0.5,
                    help="Total years in current employment"
                )

            col3, col4 = st.columns(2)

            with col3:
                education_level = st.selectbox(
                    "Education Level",
                    EDUCATION_LEVELS,
                    index=EDUCATION_LEVELS.index(st.session_state.form_data.get("education_level", "bachelors")),
                    help="Your highest level of education"
                )

            with col4:
                annual_income = st.number_input(
                    "Annual Income ($)",
                    min_value=1000.0,
                    value=float(st.session_state.form_data.get("annual_income", 50000.0)),
                    step=1000.0,
                    help="Your gross annual income"
                )

            # Info box
            with st.expander("💡 Why we need this info"):
                st.markdown("""
                - **Employment Status** helps us assess income stability
                - **Years Employed** indicates job tenure and commitment
                - **Education Level** correlates with earning potential
                - **Annual Income** helps calculate your debt-to-income ratio
                """)

            col5, col6, col7 = st.columns(3)
            with col5:
                if st.form_submit_button("← Back", use_container_width=True):
                    st.session_state.current_step = 0
                    st.rerun()

            with col6:
                if st.form_submit_button("Next →", use_container_width=True):
                    is_valid, error_msg = validate_step_2({
                        "employment_status": employment_status,
                        "employment_years": employment_years,
                        "education_level": education_level,
                        "annual_income": annual_income
                    })
                    if is_valid:
                        st.session_state.form_data.update({
                            "employment_status": employment_status,
                            "employment_years": employment_years,
                            "education_level": education_level,
                            "annual_income": annual_income
                        })
                        st.session_state.current_step = 2
                        st.rerun()
                    else:
                        st.error(f"❌ {error_msg}")

            with col7:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.current_page = "Home"
                    st.rerun()

    # Step 3: Financial Information
    elif st.session_state.current_step == 2:
        with st.form("step_3_form", clear_on_submit=False):
            st.markdown("### Step 3: Financial Information")
            st.markdown("Provide details about your financial situation")

            col1, col2 = st.columns(2)

            with col1:
                credit_score = st.slider(
                    "Credit Score",
                    min_value=300,
                    max_value=850,
                    value=int(st.session_state.form_data.get("credit_score", 720)),
                    step=10,
                    help="Your FICO credit score (300-850)"
                )

            with col2:
                savings = st.number_input(
                    "Savings ($)",
                    min_value=0.0,
                    value=float(st.session_state.form_data.get("savings", 10000.0)),
                    step=1000.0,
                    help="Total savings and cash reserves"
                )

            col3, col4 = st.columns(2)

            with col3:
                monthly_expenses = st.number_input(
                    "Monthly Expenses ($)",
                    min_value=0.0,
                    value=float(st.session_state.form_data.get("monthly_expenses", 2000.0)),
                    step=100.0,
                    help="Average monthly living expenses"
                )

            with col4:
                liabilities = st.number_input(
                    "Existing Liabilities ($)",
                    min_value=0.0,
                    value=float(st.session_state.form_data.get("liabilities", 5000.0)),
                    step=1000.0,
                    help="Total existing debts (credit cards, car loans, etc.)"
                )

            # Credit score explanation
            with st.expander("💳 Credit Score Guide"):
                st.markdown("""
                - **300-579**: Poor - May face difficulty getting approved
                - **580-669**: Fair - Higher interest rates likely
                - **670-739**: Good - Standard terms
                - **740-799**: Very Good - Favorable terms
                - **800+**: Excellent - Best rates available
                """)

            col5, col6, col7 = st.columns(3)
            with col5:
                if st.form_submit_button("← Back", use_container_width=True):
                    st.session_state.current_step = 1
                    st.rerun()

            with col6:
                if st.form_submit_button("Next →", use_container_width=True):
                    is_valid, error_msg = validate_step_3({
                        "credit_score": credit_score,
                        "savings": savings,
                        "monthly_expenses": monthly_expenses,
                        "liabilities": liabilities
                    })
                    if is_valid:
                        st.session_state.form_data.update({
                            "credit_score": credit_score,
                            "savings": savings,
                            "monthly_expenses": monthly_expenses,
                            "liabilities": liabilities
                        })
                        st.session_state.current_step = 3
                        st.rerun()
                    else:
                        st.error(f"❌ {error_msg}")

            with col7:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.current_page = "Home"
                    st.rerun()

    # Step 4: Loan Information
    elif st.session_state.current_step == 3:
        with st.form("step_4_form", clear_on_submit=False):
            st.markdown("### Step 4: Loan Information")
            st.markdown("Tell us about the loan you're requesting")

            col1, col2 = st.columns(2)

            with col1:
                loan_purpose = st.selectbox(
                    "Loan Purpose",
                    LOAN_PURPOSES,
                    index=LOAN_PURPOSES.index(st.session_state.form_data.get("loan_purpose", "personal")),
                    help="What is the primary purpose of this loan?"
                )

            with col2:
                loan_amount = st.number_input(
                    "Loan Amount ($)",
                    min_value=1000.0,
                    value=float(st.session_state.form_data.get("loan_amount", 25000.0)),
                    step=1000.0,
                    help="Total amount you wish to borrow"
                )

            col3, col4 = st.columns(2)

            with col3:
                loan_tenure = st.slider(
                    "Loan Tenure (months)",
                    min_value=1,
                    max_value=480,
                    value=int(st.session_state.form_data.get("loan_tenure", 60)),
                    step=3,
                    help="Total repayment period in months"
                )

            with col4:
                st.metric(
                    "Estimated Monthly Payment",
                    f"${loan_amount / max(loan_tenure, 1) * 1.05:,.0f}",
                    help="Rough estimate at 5% interest"
                )

            # Calculate and display metrics
            st.divider()
            st.markdown("### Financial Summary")

            dti_ratio = (st.session_state.form_data.get("liabilities", 0) / 12 + loan_amount / max(loan_tenure, 1)) / (st.session_state.form_data.get("annual_income", 1) / 12) * 100

            col5, col6, col7 = st.columns(3)
            with col5:
                st.metric("Debt-to-Income Ratio", f"{min(dti_ratio, 100):.1f}%", help="Lower is better")
            with col6:
                savings_ratio = st.session_state.form_data.get("savings", 0) / max(st.session_state.form_data.get("annual_income", 1), 1) * 100
                st.metric("Savings Ratio", f"{savings_ratio:.1f}%", help="Your emergency fund")
            with col7:
                st.metric("Credit Score", st.session_state.form_data.get("credit_score", 0))

            # Loan info
            with st.expander("💡 Loan Terms Info"):
                st.markdown("""
                - **Shorter tenure** = Higher monthly payment but less total interest
                - **Longer tenure** = Lower monthly payment but more total interest
                - **DTI Ratio** should ideally be below 43% for approval
                - **Credit Score** affects interest rate and approval likelihood
                """)

            col8, col9, col10 = st.columns(3)
            with col8:
                if st.form_submit_button("← Back", use_container_width=True):
                    st.session_state.current_step = 2
                    st.rerun()

            with col9:
                if st.form_submit_button("🚀 Submit Application", use_container_width=True, type="primary"):
                    is_valid, error_msg = validate_step_4({
                        "loan_purpose": loan_purpose,
                        "loan_amount": loan_amount,
                        "loan_tenure": loan_tenure
                    })
                    if is_valid:
                        st.session_state.form_data.update({
                            "loan_purpose": loan_purpose,
                            "loan_amount": loan_amount,
                            "loan_tenure": loan_tenure
                        })

                        # Submit to backend
                        with st.spinner("⏳ Analyzing your application..."):
                            result = submit_application(st.session_state.form_data)

                        if result["success"]:
                            st.session_state.last_decision = result["data"]
                            app_entry = {
                                "name": st.session_state.form_data.get("name"),
                                "amount": loan_amount,
                                "status": result["data"].get("classification"),
                                "timestamp": datetime.now().isoformat()
                            }
                            st.session_state.application_history.append(app_entry)
                            st.session_state.current_page = "Status"
                            st.rerun()
                        else:
                            st.error(f"❌ Submission failed: {result.get('error')}")
                            st.caption(result.get('details'))
                    else:
                        st.error(f"❌ {error_msg}")

            with col10:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.current_page = "Home"
                    st.rerun()

# ============================================================================
# Page: Status - Results Display
# ============================================================================

def render_status():
    """Render the decision results page with beautiful visualization."""
    st.title("📊 Application Status & Decision")

    if not st.session_state.last_decision:
        st.info("No application results to display. Submit an application to see results.")
        if st.button("Start New Application"):
            st.session_state.current_page = "Apply"
            st.session_state.current_step = 0
            st.rerun()
        return

    decision = st.session_state.last_decision
    classification = decision.get("classification", "review_required").lower()
    risk_score = decision.get("risk_score", 50)
    confidence = decision.get("confidence", 0)

    # Main decision banner
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        decision_color = DECISION_COLORS.get(classification, "#6B7280")
        decision_text = classification.replace("_", " ").title()

        st.markdown(f"""
        <div style="
            background-color: {decision_color};
            color: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        ">
            <h1 style="margin: 0; font-size: 48px;">✓</h1>
            <h2 style="margin: 10px 0 0 0;">{decision_text}</h2>
            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Decision ID: {decision.get('case_id', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

    # Key metrics
    st.markdown("### Key Metrics")

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric(
            "Risk Score",
            f"{risk_score:.1f}/100",
            delta=None,
            help="Lower is better - indicates lower risk"
        )

    with metric2:
        st.metric(
            "Confidence Level",
            f"{confidence * 100:.0f}%",
            delta=None,
            help="How confident we are in this decision"
        )

    with metric3:
        loan_amount = st.session_state.form_data.get("loan_amount", 0)
        st.metric(
            "Requested Amount",
            f"${loan_amount:,.0f}",
            delta=None
        )

    with metric4:
        credit_score = st.session_state.form_data.get("credit_score", 0)
        st.metric(
            "Credit Score",
            credit_score,
            delta=None
        )

    st.divider()

    # Decision explanation
    st.markdown("### Decision Explanation")
    st.info(decision.get("explanation", "No explanation available"))

    # Risk visualization
    st.markdown("### Risk Assessment")

    col1, col2 = st.columns(2)

    with col1:
        # Risk gauge chart
        fig = go.Figure(data=[
            go.Indicator(
                mode="gauge+number+delta",
                value=risk_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Risk Score"},
                delta={'reference': 50},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "#10B981"},
                        {'range': [25, 50], 'color': "#F59E0B"},
                        {'range': [50, 75], 'color': "#EF4444"},
                        {'range': [75, 100], 'color': "#7F1D1D"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 75
                    }
                }
            )
        ])
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Confidence gauge
        fig = go.Figure(data=[
            go.Indicator(
                mode="gauge+number",
                value=confidence * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Decision Confidence"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 40], 'color': "#FEE2E2"},
                        {'range': [40, 70], 'color': "#FCD34D"},
                        {'range': [70, 100], 'color': "#D1FAE5"}
                    ]
                }
            )
        ])
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Risk factors
    st.markdown("### Risk Factors Analysis")

    factors = decision.get("factors", [])
    if factors:
        # Create factor comparison chart
        factor_df = pd.DataFrame(factors)

        if not factor_df.empty and "weight" in factor_df.columns:
            factor_df = factor_df.sort_values("weight", ascending=True)

            fig = go.Figure(data=[
                go.Bar(
                    y=factor_df.get("factor_name", factor_df.get("name", [])),
                    x=factor_df["weight"] * 100,
                    orientation='h',
                    marker=dict(
                        color=factor_df["weight"] * 100,
                        colorscale='RdYlGn_r',
                        showscale=True
                    )
                )
            ])
            fig.update_layout(
                title="Factor Weight Distribution",
                xaxis_title="Weight (%)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        # Factor details table
        st.markdown("#### Individual Factors")

        for idx, factor in enumerate(factors, 1):
            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                impact = factor.get("impact", "neutral").upper()
                if impact == "POSITIVE":
                    st.success(f"✓ {impact}")
                elif impact == "NEGATIVE":
                    st.error(f"✗ {impact}")
                else:
                    st.info(f"● {impact}")

            with col2:
                st.markdown(f"""
                **{factor.get('factor_name', 'N/A')}**

                {factor.get('explanation', 'No explanation')}
                """)

            with col3:
                st.metric("Value", f"{factor.get('value', 0):.0f}")
    else:
        st.info("No factor details available")

    st.divider()

    # Conditions and requirements
    if decision.get("conditions"):
        st.markdown("### Conditions for Approval")
        for idx, condition in enumerate(decision.get("conditions", []), 1):
            st.info(f"📋 {condition}")

    if decision.get("required_documents"):
        st.markdown("### Required Documents")
        for idx, doc in enumerate(decision.get("required_documents", []), 1):
            st.checkbox(doc, disabled=False, key=f"doc_{idx}")

    st.divider()

    # Processing details
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Processing Time",
            f"{decision.get('processing_time_ms', 0):.0f}ms",
            help="Time to generate decision"
        )

    with col2:
        st.metric(
            "Processed At",
            decision.get("processed_at", "N/A")[:10],
            help="Decision timestamp"
        )

    with col3:
        if st.button("📋 New Application"):
            st.session_state.current_page = "Apply"
            st.session_state.current_step = 0
            st.session_state.form_data = {}
            st.rerun()

# ============================================================================
# Page: Analytics
# ============================================================================

def render_analytics():
    """Render analytics and insights page."""
    st.title("📈 Analytics & Insights")

    if not st.session_state.application_history:
        st.info("No application history yet. Submit some applications to see analytics.")
        return

    # Convert history to dataframe
    df = pd.DataFrame(st.session_state.application_history)

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    total_apps = len(df)
    approved = len(df[df["status"] == "approved"])
    denied = len(df[df["status"] == "denied"])
    conditional = len(df[df["status"] == "conditional_approval"])

    with col1:
        st.metric("Total Applications", total_apps)

    with col2:
        st.metric("✅ Approved", approved, delta=f"{approved/total_apps*100:.0f}%")

    with col3:
        st.metric("❌ Denied", denied, delta=f"{denied/total_apps*100:.0f}%")

    with col4:
        st.metric("⏳ Conditional", conditional, delta=f"{conditional/total_apps*100:.0f}%")

    st.divider()

    # Decision distribution
    st.markdown("### Decision Distribution")

    col1, col2 = st.columns(2)

    with col1:
        status_counts = df["status"].value_counts()
        fig = go.Figure(data=[
            go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                marker=dict(
                    colors=[DECISION_COLORS.get(s, "#6B7280") for s in status_counts.index]
                )
            )
        ])
        fig.update_layout(title="Decision Status Distribution", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Application amount statistics
        df["amount_numeric"] = pd.to_numeric(df["amount"], errors="coerce")

        fig = go.Figure(data=[
            go.Box(
                y=df["amount_numeric"],
                name="Loan Amounts",
                marker_color="#3B82F6",
                boxmean='sd'
            )
        ])
        fig.update_layout(
            title="Loan Amount Distribution",
            yaxis_title="Amount ($)",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Timeline
    st.markdown("### Application Timeline")

    if "timestamp" in df.columns:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df_timeline = df.sort_values("timestamp_dt")

        fig = go.Figure()
        for status in df["status"].unique():
            df_status = df_timeline[df_timeline["status"] == status]
            fig.add_trace(go.Scatter(
                x=df_status["timestamp_dt"],
                y=df_status["amount_numeric"],
                mode='markers+lines',
                name=status,
                marker=dict(size=10, color=DECISION_COLORS.get(status, "#6B7280")),
                line=dict(color=DECISION_COLORS.get(status, "#6B7280"))
            ))

        fig.update_layout(
            title="Applications Over Time",
            xaxis_title="Date",
            yaxis_title="Loan Amount ($)",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Recent applications table
    st.markdown("### Recent Applications")

    display_df = df[["name", "amount", "status", "timestamp"]].copy()
    display_df.columns = ["Name", "Amount", "Status", "Timestamp"]
    display_df["Status"] = display_df["Status"].str.replace("_", " ").str.title()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(format="$%,.0f"),
            "Status": st.column_config.TextColumn(),
        }
    )

# ============================================================================
# Main Application Flow
# ============================================================================

def main():
    """Main application entry point."""

    # Route to appropriate page
    if st.session_state.current_page == "Home":
        render_home()
    elif st.session_state.current_page == "Apply":
        render_apply()
    elif st.session_state.current_page == "Status":
        render_status()
    elif st.session_state.current_page == "Analytics":
        render_analytics()

if __name__ == "__main__":
    main()
