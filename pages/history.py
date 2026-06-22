"""
Application History Page

Provides a comprehensive interface for viewing and managing submitted loan applications.
Features include:
- Table of submitted applications with sorting and filtering
- Application status tracking (Pending, Approved, Rejected, Review)
- Search by applicant ID or name
- Export to CSV functionality
- Detailed view for each application showing decision reasoning
"""

import streamlit as st
import pandas as pd
import csv
from io import StringIO
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application status options
STATUS_OPTIONS = {
    "Pending": "pending",
    "Approved": "approved",
    "Rejected": "rejected",
    "Review": "review_required",
    "Conditional Approval": "conditional_approval"
}

STATUS_COLORS = {
    "pending": "🟡",
    "approved": "🟢",
    "rejected": "🔴",
    "review_required": "🔵",
    "conditional_approval": "🟠"
}

RISK_LEVELS = {
    "low": "🟢 Low Risk",
    "medium": "🟡 Medium Risk",
    "high": "🔴 High Risk",
    "very_high": "⛔ Very High Risk"
}


def initialize_session_state():
    """Initialize session state variables."""
    if "applications_data" not in st.session_state:
        st.session_state.applications_data = []
    if "selected_app_id" not in st.session_state:
        st.session_state.selected_app_id = None
    if "show_detail_view" not in st.session_state:
        st.session_state.show_detail_view = False


def load_sample_data() -> List[Dict[str, Any]]:
    """
    Load sample application data.
    In production, this would load from the database.
    """
    return [
        {
            "id": "APP-001",
            "applicant_name": "John Smith",
            "applicant_id": "AP001",
            "email": "john.smith@example.com",
            "loan_amount": 250000,
            "loan_purpose": "home_purchase",
            "status": "approved",
            "risk_level": "low",
            "risk_score": 35.5,
            "credit_score": 745,
            "dti_ratio": 28.5,
            "submission_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "decision_date": (datetime.now() - timedelta(days=2)).isoformat(),
            "confidence": 0.92,
            "factors": {
                "credit_score": 0.85,
                "debt_to_income_ratio": 0.78,
                "employment_stability": 0.90,
                "assets": 0.88,
                "income_level": 0.72
            },
            "explanation": "Application approved. Strong credit profile with excellent employment history and substantial savings. Debt-to-income ratio is within acceptable limits.",
            "conditions": [],
            "recommended_interest_rate": 4.5,
            "processing_time_days": 3,
            "next_steps": ["Final documentation", "Appraisal scheduling"],
            "reviewer_notes": "Well-qualified applicant. Recommend approval."
        },
        {
            "id": "APP-002",
            "applicant_name": "Sarah Johnson",
            "applicant_id": "AP002",
            "email": "sarah.j@example.com",
            "loan_amount": 180000,
            "loan_purpose": "auto_purchase",
            "status": "pending",
            "risk_level": "medium",
            "risk_score": 52.3,
            "credit_score": 680,
            "dti_ratio": 35.2,
            "submission_date": (datetime.now() - timedelta(days=2)).isoformat(),
            "decision_date": None,
            "confidence": 0.75,
            "factors": {
                "credit_score": 0.65,
                "debt_to_income_ratio": 0.60,
                "employment_stability": 0.80,
                "assets": 0.70,
                "income_level": 0.65
            },
            "explanation": "Application under review. Moderate credit score with acceptable employment history. Additional verification needed for recent credit inquiries.",
            "conditions": ["Explanation of recent credit inquiries", "Verification of employment"],
            "recommended_interest_rate": 6.2,
            "processing_time_days": None,
            "next_steps": ["Contact applicant for documentation", "Verify employment"],
            "reviewer_notes": "Requires clarification on recent credit activity."
        },
        {
            "id": "APP-003",
            "applicant_name": "Michael Chen",
            "applicant_id": "AP003",
            "email": "m.chen@example.com",
            "loan_amount": 95000,
            "loan_purpose": "education",
            "status": "review_required",
            "risk_level": "high",
            "risk_score": 72.1,
            "credit_score": 620,
            "dti_ratio": 42.8,
            "submission_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "decision_date": None,
            "confidence": 0.55,
            "factors": {
                "credit_score": 0.45,
                "debt_to_income_ratio": 0.35,
                "employment_stability": 0.60,
                "assets": 0.50,
                "income_level": 0.55
            },
            "explanation": "Application flagged for review. Lower credit score and elevated debt-to-income ratio indicate higher risk. Recommend senior reviewer assessment.",
            "conditions": ["Senior reviewer assessment", "Income verification", "Debt consolidation discussion"],
            "recommended_interest_rate": 7.5,
            "processing_time_days": None,
            "next_steps": ["Schedule senior review", "Obtain recent tax returns", "Discuss debt management"],
            "reviewer_notes": "Risk factors warrant senior management review. Possible conditional approval with higher rate."
        },
        {
            "id": "APP-004",
            "applicant_name": "Emily Rodriguez",
            "applicant_id": "AP004",
            "email": "emily.r@example.com",
            "loan_amount": 350000,
            "loan_purpose": "home_purchase",
            "status": "rejected",
            "risk_level": "very_high",
            "risk_score": 88.5,
            "credit_score": 580,
            "dti_ratio": 58.3,
            "submission_date": (datetime.now() - timedelta(days=10)).isoformat(),
            "decision_date": (datetime.now() - timedelta(days=8)).isoformat(),
            "confidence": 0.88,
            "factors": {
                "credit_score": 0.25,
                "debt_to_income_ratio": 0.20,
                "employment_stability": 0.55,
                "assets": 0.30,
                "income_level": 0.40
            },
            "explanation": "Application denied. Significant risk factors including low credit score, high debt-to-income ratio, and insufficient assets. Recent late payments on credit report.",
            "conditions": [],
            "recommended_interest_rate": None,
            "processing_time_days": 2,
            "next_steps": ["Appeal process available", "Consider credit improvement program", "Reapply after 6 months"],
            "reviewer_notes": "Recommend decline. Multiple risk factors present. Applicant may reapply after improving credit profile."
        },
        {
            "id": "APP-005",
            "applicant_name": "David Thompson",
            "applicant_id": "AP005",
            "email": "d.thompson@example.com",
            "loan_amount": 200000,
            "loan_purpose": "debt_consolidation",
            "status": "conditional_approval",
            "risk_level": "medium",
            "risk_score": 48.7,
            "credit_score": 700,
            "dti_ratio": 32.1,
            "submission_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "decision_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "confidence": 0.81,
            "factors": {
                "credit_score": 0.75,
                "debt_to_income_ratio": 0.70,
                "employment_stability": 0.85,
                "assets": 0.65,
                "income_level": 0.78
            },
            "explanation": "Application conditionally approved. Generally positive profile with stable employment. Approval contingent on providing payroll verification and proof of debts to be consolidated.",
            "conditions": ["Recent payroll stubs (2 months)", "Documentation of debts for consolidation", "Proof of savings account"],
            "recommended_interest_rate": 5.8,
            "processing_time_days": 5,
            "next_steps": ["Submit required documentation", "Final verification", "Loan agreement review"],
            "reviewer_notes": "Good candidate. Conditional approval appropriate pending document verification."
        }
    ]


def create_dataframe_for_display(applications: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a dataframe suitable for display in the UI.
    """
    display_data = []
    for app in applications:
        display_data.append({
            "ID": app["id"],
            "Applicant": app["applicant_name"],
            "Email": app["email"],
            "Loan Amount": f"${app['loan_amount']:,.0f}",
            "Purpose": app["loan_purpose"].replace("_", " ").title(),
            "Status": STATUS_COLORS.get(app["status"], "❓") + " " + app["status"].replace("_", " ").title(),
            "Risk": RISK_LEVELS.get(app["risk_level"], "Unknown"),
            "Credit Score": app["credit_score"],
            "DTI Ratio": f"{app['dti_ratio']:.1f}%",
            "Submitted": pd.to_datetime(app["submission_date"]).strftime("%Y-%m-%d"),
            "Full Data": app  # Store full data for access
        })

    df = pd.DataFrame(display_data)
    return df


def filter_applications(
    applications: List[Dict[str, Any]],
    status_filter: Optional[str] = None,
    risk_filter: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter applications based on criteria.
    """
    filtered = applications.copy()

    if status_filter and status_filter != "All":
        filtered = [app for app in filtered if app["status"] == STATUS_OPTIONS.get(status_filter, status_filter)]

    if risk_filter and risk_filter != "All":
        filtered = [app for app in filtered if app["risk_level"] == risk_filter]

    if search_query:
        search_lower = search_query.lower()
        filtered = [
            app for app in filtered
            if search_lower in app["id"].lower() or
               search_lower in app["applicant_name"].lower() or
               search_lower in app["applicant_id"].lower()
        ]

    return filtered


def export_to_csv(applications: List[Dict[str, Any]]) -> str:
    """
    Export applications data to CSV format.
    """
    output = StringIO()

    if not applications:
        return ""

    # Define CSV columns
    fieldnames = [
        "Application ID",
        "Applicant Name",
        "Applicant ID",
        "Email",
        "Loan Amount",
        "Loan Purpose",
        "Status",
        "Risk Level",
        "Risk Score",
        "Credit Score",
        "DTI Ratio",
        "Confidence",
        "Recommended Rate",
        "Submission Date",
        "Decision Date",
        "Explanation"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for app in applications:
        writer.writerow({
            "Application ID": app["id"],
            "Applicant Name": app["applicant_name"],
            "Applicant ID": app["applicant_id"],
            "Email": app["email"],
            "Loan Amount": app["loan_amount"],
            "Loan Purpose": app["loan_purpose"],
            "Status": app["status"],
            "Risk Level": app["risk_level"],
            "Risk Score": f"{app['risk_score']:.2f}",
            "Credit Score": app["credit_score"],
            "DTI Ratio": f"{app['dti_ratio']:.2f}",
            "Confidence": f"{app['confidence']:.2f}",
            "Recommended Rate": app.get("recommended_interest_rate", "N/A"),
            "Submission Date": app["submission_date"],
            "Decision Date": app["decision_date"] or "Pending",
            "Explanation": app["explanation"]
        })

    return output.getvalue()


def display_detail_view(application: Dict[str, Any]):
    """
    Display detailed view of an application.
    """
    st.header(f"Application Details - {application['id']}")

    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Financial Analysis", "Decision Reasoning", "Action Items"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Applicant Information")
            st.write(f"**Name:** {application['applicant_name']}")
            st.write(f"**ID:** {application['applicant_id']}")
            st.write(f"**Email:** {application['email']}")
            st.write(f"**Submitted:** {pd.to_datetime(application['submission_date']).strftime('%Y-%m-%d %H:%M')}")

        with col2:
            st.subheader("Application Status")
            status_key = application["status"]
            status_emoji = STATUS_COLORS.get(status_key, "❓")
            st.metric("Status", f"{status_emoji} {status_key.replace('_', ' ').title()}")
            st.metric("Risk Level", RISK_LEVELS.get(application["risk_level"], "Unknown"))
            st.metric("Risk Score", f"{application['risk_score']:.2f}")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Loan Details")
            st.write(f"**Loan Amount:** ${application['loan_amount']:,.2f}")
            st.write(f"**Purpose:** {application['loan_purpose'].replace('_', ' ').title()}")
            st.write(f"**Requested Term:** 360 months (30 years)")

        with col2:
            st.subheader("Key Metrics")
            st.metric("Credit Score", application["credit_score"])
            st.metric("Debt-to-Income Ratio", f"{application['dti_ratio']:.2f}%")
            st.metric("Decision Confidence", f"{application['confidence']:.0%}")

    with tab2:
        st.subheader("Financial Analysis")

        # Display risk factors
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Risk Factors (0-1 scale):**")
            factors_df = pd.DataFrame([application["factors"]])
            for factor, score in application["factors"].items():
                color = "🟢" if score >= 0.75 else "🟡" if score >= 0.5 else "🔴"
                st.write(f"{color} {factor.replace('_', ' ').title()}: {score:.2f}")

        with col2:
            # Visualize factors as a progress bar
            st.write("**Factor Breakdown:**")
            for factor, score in application["factors"].items():
                st.progress(score, text=f"{factor.replace('_', ' ').title()}: {score:.0%}")

    with tab3:
        st.subheader("Decision Reasoning")

        st.write("**Explanation:**")
        st.info(application["explanation"])

        if application["conditions"]:
            st.write("**Conditions:**")
            for condition in application["conditions"]:
                st.write(f"• {condition}")

        if application.get("recommended_interest_rate"):
            st.write(f"**Recommended Interest Rate:** {application['recommended_interest_rate']:.2f}%")

        if application.get("reviewer_notes"):
            st.write("**Reviewer Notes:**")
            st.write(application["reviewer_notes"])

    with tab4:
        st.subheader("Action Items")

        if application["next_steps"]:
            for idx, step in enumerate(application["next_steps"], 1):
                st.write(f"{idx}. {step}")

        st.divider()

        # Status action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Mark as Approved", key=f"approve_{application['id']}"):
                st.success("Application marked as approved!")

        with col2:
            if st.button("Request Review", key=f"review_{application['id']}"):
                st.info("Application flagged for review!")

        with col3:
            if st.button("Reject Application", key=f"reject_{application['id']}"):
                st.error("Application rejected!")


def display_table_view(df: pd.DataFrame):
    """
    Display applications in table format.
    """
    # Remove the "Full Data" column from display
    display_df = df.drop("Full Data", axis=1)

    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )


def display_statistics(applications: List[Dict[str, Any]]):
    """
    Display statistics about applications.
    """
    st.subheader("Statistics")

    col1, col2, col3, col4, col5 = st.columns(5)

    total = len(applications)
    approved = len([a for a in applications if a["status"] == "approved"])
    rejected = len([a for a in applications if a["status"] == "rejected"])
    pending = len([a for a in applications if a["status"] == "pending"])
    review = len([a for a in applications if a["status"] == "review_required"])

    with col1:
        st.metric("Total Applications", total)
    with col2:
        st.metric("Approved", approved)
    with col3:
        st.metric("Rejected", rejected)
    with col4:
        st.metric("Pending", pending)
    with col5:
        st.metric("Under Review", review)

    # Additional metrics
    col1, col2, col3 = st.columns(3)

    avg_credit = sum(a["credit_score"] for a in applications) / len(applications) if applications else 0
    avg_risk = sum(a["risk_score"] for a in applications) / len(applications) if applications else 0
    total_loan_value = sum(a["loan_amount"] for a in applications)

    with col1:
        st.metric("Avg Credit Score", f"{avg_credit:.0f}")
    with col2:
        st.metric("Avg Risk Score", f"{avg_risk:.2f}")
    with col3:
        st.metric("Total Loan Value", f"${total_loan_value:,.0f}")


def main():
    """Main application."""
    st.set_page_config(
        page_title="Application History",
        page_icon="📋",
        layout="wide"
    )

    st.title("📋 Application History")
    st.markdown("View, filter, and manage submitted loan applications")

    # Initialize session state
    initialize_session_state()

    # Load sample data
    applications = load_sample_data()
    st.session_state.applications_data = applications

    # Sidebar for filters
    with st.sidebar:
        st.header("🔍 Filters")

        # Search box
        search_query = st.text_input(
            "Search by ID, Name, or Applicant ID",
            placeholder="Enter search term..."
        )

        # Status filter
        status_options = ["All"] + list(STATUS_OPTIONS.keys())
        status_filter = st.selectbox(
            "Filter by Status",
            status_options,
            index=0
        )

        # Risk level filter
        risk_options = ["All", "low", "medium", "high", "very_high"]
        risk_filter = st.selectbox(
            "Filter by Risk Level",
            risk_options,
            index=0
        )

        st.divider()

        # Date range filter
        st.write("**Date Range**")
        days_back = st.slider(
            "Show applications from last N days",
            1, 365, 30
        )

        st.divider()

        # Sort options
        sort_options = {
            "Newest First": ("submission_date", False),
            "Oldest First": ("submission_date", True),
            "Highest Risk": ("risk_score", False),
            "Lowest Risk": ("risk_score", True),
            "Largest Loan": ("loan_amount", False),
            "Smallest Loan": ("loan_amount", True),
        }
        sort_by = st.selectbox(
            "Sort by",
            list(sort_options.keys())
        )

    # Apply filters
    filtered_apps = filter_applications(
        applications,
        status_filter if status_filter != "All" else None,
        risk_filter if risk_filter != "All" else None,
        search_query
    )

    # Sort applications
    if sort_by in sort_options:
        sort_key, reverse = sort_options[sort_by]
        filtered_apps = sorted(
            filtered_apps,
            key=lambda x: x.get(sort_key, ""),
            reverse=reverse
        )

    # Main content area
    tab1, tab2, tab3 = st.tabs(["📊 Table View", "📈 Analytics", "⚙️ Manage"])

    with tab1:
        st.subheader(f"Showing {len(filtered_apps)} of {len(applications)} Applications")

        if filtered_apps:
            # Display statistics
            display_statistics(filtered_apps)

            st.divider()

            # Create dataframe
            df = create_dataframe_for_display(filtered_apps)

            # Display table
            display_table_view(df)

            st.divider()

            # Selection and detail view
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_id = st.selectbox(
                    "Select an application to view details:",
                    [app["id"] for app in filtered_apps],
                    key="app_selector"
                )

            with col2:
                if st.button("View Details", key="view_details_btn"):
                    st.session_state.selected_app_id = selected_id
                    st.session_state.show_detail_view = True

            # Display detail view if selected
            if st.session_state.show_detail_view and st.session_state.selected_app_id:
                selected_app = next(
                    (app for app in filtered_apps if app["id"] == st.session_state.selected_app_id),
                    None
                )
                if selected_app:
                    st.divider()
                    display_detail_view(selected_app)
        else:
            st.info("No applications match the selected criteria.")

    with tab2:
        st.subheader("Application Analytics")

        if filtered_apps:
            # Status distribution
            status_counts = {}
            for app in filtered_apps:
                status = app["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Status Distribution**")
                status_df = pd.DataFrame([status_counts]).T.reset_index()
                status_df.columns = ["Status", "Count"]
                st.bar_chart(status_df.set_index("Status"))

            with col2:
                st.write("**Risk Distribution**")
                risk_counts = {}
                for app in filtered_apps:
                    risk = app["risk_level"]
                    risk_counts[risk] = risk_counts.get(risk, 0) + 1

                risk_df = pd.DataFrame([risk_counts]).T.reset_index()
                risk_df.columns = ["Risk Level", "Count"]
                st.bar_chart(risk_df.set_index("Risk Level"))

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Loan Amount Distribution**")
                amounts = [app["loan_amount"] for app in filtered_apps]
                amounts_df = pd.DataFrame({"Loan Amount": amounts})
                st.histogram(amounts_df, x="Loan Amount", nbins=10)

            with col2:
                st.write("**Credit Score Distribution**")
                scores = [app["credit_score"] for app in filtered_apps]
                scores_df = pd.DataFrame({"Credit Score": scores})
                st.histogram(scores_df, x="Credit Score", nbins=10)
        else:
            st.info("No data available for analytics.")

    with tab3:
        st.subheader("Export & Management")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Export to CSV**")
            if st.button("Export Filtered Results", key="export_filtered"):
                csv_data = export_to_csv(filtered_apps)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_csv"
                )

        with col2:
            st.write("**Export All Applications**")
            if st.button("Export All", key="export_all"):
                csv_data = export_to_csv(applications)
                st.download_button(
                    label="Download All as CSV",
                    data=csv_data,
                    file_name=f"all_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_all_csv"
                )

        st.divider()

        st.write("**Bulk Actions**")

        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button("Approve All Pending", key="bulk_approve"):
                st.success(f"Approved {len([a for a in filtered_apps if a['status'] == 'pending'])} applications")

        with action_col2:
            if st.button("Flag for Review", key="bulk_review"):
                st.info(f"Flagged {len(filtered_apps)} applications for review")

        with action_col3:
            if st.button("Send Notifications", key="bulk_notify"):
                st.success(f"Notifications sent for {len(filtered_apps)} applications")


if __name__ == "__main__":
    main()
