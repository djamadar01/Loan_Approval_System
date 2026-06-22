"""
Analytics Dashboard Page

Provides comprehensive analytics and business intelligence for loan processing system.
Features include:
- Total applications count KPI
- Approval rate pie chart
- Average decision score chart over time
- Risk distribution histogram
- Processing time statistics
- Date range filters with interactive charts using Plotly and Altair
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import altair as alt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import json
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Status and risk level constants
STATUS_COLORS = {
    "pending": "#FFA500",
    "approved": "#28A745",
    "rejected": "#DC3545",
    "review_required": "#007BFF",
    "conditional_approval": "#FF8C00"
}

RISK_COLORS = {
    "low": "#28A745",
    "medium": "#FFA500",
    "high": "#DC3545",
    "very_high": "#8B0000"
}


def initialize_session_state():
    """Initialize session state variables for analytics."""
    if "analytics_data" not in st.session_state:
        st.session_state.analytics_data = []
    if "date_range_start" not in st.session_state:
        st.session_state.date_range_start = datetime.now() - timedelta(days=90)
    if "date_range_end" not in st.session_state:
        st.session_state.date_range_end = datetime.now()


def load_sample_analytics_data() -> List[Dict[str, Any]]:
    """
    Load sample application data for analytics.
    In production, this would load from the database.
    """
    np.random.seed(42)
    applications = []

    # Generate 100 sample applications over the last 90 days
    for i in range(100):
        days_ago = np.random.randint(0, 90)
        submission_date = datetime.now() - timedelta(days=days_ago)

        # Randomly assign status
        status_choice = np.random.choice(
            ["approved", "rejected", "pending", "review_required", "conditional_approval"],
            p=[0.40, 0.15, 0.20, 0.15, 0.10]
        )

        # Assign risk level based on status tendency
        if status_choice == "approved":
            risk_level = np.random.choice(["low", "medium"], p=[0.7, 0.3])
        elif status_choice == "rejected":
            risk_level = np.random.choice(["high", "very_high"], p=[0.5, 0.5])
        else:
            risk_level = np.random.choice(["low", "medium", "high", "very_high"], p=[0.2, 0.4, 0.3, 0.1])

        # Generate risk score based on risk level
        risk_score_ranges = {
            "low": (20, 35),
            "medium": (40, 60),
            "high": (65, 80),
            "very_high": (85, 100)
        }
        risk_score = np.random.uniform(*risk_score_ranges[risk_level])

        # Calculate processing days
        processing_days = np.random.randint(1, 15) if status_choice != "pending" else None

        decision_date = (submission_date + timedelta(days=processing_days)) if processing_days else None

        applications.append({
            "id": f"APP-{i+1:03d}",
            "applicant_name": f"Applicant {i+1}",
            "applicant_id": f"AP{i+1:03d}",
            "email": f"applicant{i+1}@example.com",
            "loan_amount": np.random.randint(50000, 500000),
            "loan_purpose": np.random.choice(["home_purchase", "auto_purchase", "education", "debt_consolidation", "business"]),
            "status": status_choice,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "credit_score": np.random.randint(550, 800),
            "dti_ratio": np.random.uniform(15, 55),
            "submission_date": submission_date.isoformat(),
            "decision_date": decision_date.isoformat() if decision_date else None,
            "confidence": np.random.uniform(0.5, 0.99),
            "factors": {
                "credit_score": np.random.uniform(0.3, 1.0),
                "debt_to_income_ratio": np.random.uniform(0.3, 1.0),
                "employment_stability": np.random.uniform(0.3, 1.0),
                "assets": np.random.uniform(0.3, 1.0),
                "income_level": np.random.uniform(0.3, 1.0)
            },
            "explanation": f"Application {status_choice.replace('_', ' ').title()}. Risk assessment completed.",
            "conditions": [],
            "recommended_interest_rate": np.random.uniform(3.5, 8.0) if status_choice in ["approved", "conditional_approval"] else None,
            "processing_time_days": processing_days,
            "next_steps": []
        })

    return applications


def filter_data_by_date_range(
    applications: List[Dict[str, Any]],
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Filter applications by date range."""
    filtered = []
    for app in applications:
        submission_date = datetime.fromisoformat(app["submission_date"])
        if start_date <= submission_date <= end_date:
            filtered.append(app)
    return filtered


def calculate_kpis(applications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate key performance indicators."""
    if not applications:
        return {
            "total_applications": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "approval_rate": 0.0,
            "avg_risk_score": 0.0,
            "avg_credit_score": 0.0,
            "avg_processing_time": 0.0,
            "avg_dti_ratio": 0.0
        }

    total = len(applications)
    approved = len([a for a in applications if a["status"] in ["approved", "conditional_approval"]])
    rejected = len([a for a in applications if a["status"] == "rejected"])

    # Calculate averages for completed applications
    completed_apps = [a for a in applications if a["decision_date"] is not None]

    avg_risk_score = np.mean([a["risk_score"] for a in applications]) if applications else 0.0
    avg_credit_score = np.mean([a["credit_score"] for a in applications]) if applications else 0.0
    avg_dti_ratio = np.mean([a["dti_ratio"] for a in applications]) if applications else 0.0

    processing_times = [a["processing_time_days"] for a in completed_apps if a["processing_time_days"] is not None]
    avg_processing_time = np.mean(processing_times) if processing_times else 0.0

    return {
        "total_applications": total,
        "total_approved": approved,
        "total_rejected": rejected,
        "approval_rate": (approved / total * 100) if total > 0 else 0.0,
        "avg_risk_score": avg_risk_score,
        "avg_credit_score": avg_credit_score,
        "avg_processing_time": avg_processing_time,
        "avg_dti_ratio": avg_dti_ratio
    }


def render_kpi_metrics(kpis: Dict[str, Any]):
    """Render KPI metrics in columns."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Applications",
            value=f"{kpis['total_applications']:,}",
            delta=None
        )

    with col2:
        st.metric(
            label="Approval Rate",
            value=f"{kpis['approval_rate']:.1f}%",
            delta=None
        )

    with col3:
        st.metric(
            label="Avg Risk Score",
            value=f"{kpis['avg_risk_score']:.1f}",
            delta=None
        )

    with col4:
        st.metric(
            label="Avg Processing (days)",
            value=f"{kpis['avg_processing_time']:.1f}",
            delta=None
        )


def create_approval_rate_pie_chart(applications: List[Dict[str, Any]]) -> go.Figure:
    """Create approval rate pie chart using Plotly."""
    if not applications:
        return go.Figure()

    status_counts = {}
    for app in applications:
        status = app["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    # Map internal status to display names
    status_labels = {
        "approved": "Approved",
        "rejected": "Rejected",
        "pending": "Pending",
        "review_required": "Review Required",
        "conditional_approval": "Conditional Approval"
    }

    labels = [status_labels.get(k, k) for k in status_counts.keys()]
    values = list(status_counts.values())
    colors = [STATUS_COLORS.get(k, "#gray") for k in status_counts.keys()]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        textposition='inside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title="Application Status Distribution",
        height=400,
        showlegend=True,
        font=dict(size=12)
    )

    return fig


def create_risk_distribution_histogram(applications: List[Dict[str, Any]]) -> go.Figure:
    """Create risk distribution histogram using Plotly."""
    if not applications:
        return go.Figure()

    risk_scores = [app["risk_score"] for app in applications]
    risk_levels = [app["risk_level"] for app in applications]

    # Create histogram
    fig = go.Figure()

    # Add histogram trace
    fig.add_trace(go.Histogram(
        x=risk_scores,
        nbinsx=20,
        marker=dict(color='#007BFF'),
        name='Risk Score Distribution',
        hovertemplate='Risk Score: %{x:.1f}<br>Count: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Risk Score Distribution",
        xaxis_title="Risk Score",
        yaxis_title="Number of Applications",
        height=400,
        hovermode='x unified',
        showlegend=True,
        xaxis=dict(range=[0, 100])
    )

    return fig


def create_decision_score_chart(applications: List[Dict[str, Any]]) -> go.Figure:
    """Create average decision score over time using Plotly."""
    if not applications:
        return go.Figure()

    # Prepare data
    df_data = []
    for app in applications:
        submission_date = datetime.fromisoformat(app["submission_date"])
        df_data.append({
            "date": submission_date.date(),
            "risk_score": app["risk_score"],
            "confidence": app["confidence"],
            "status": app["status"]
        })

    df = pd.DataFrame(df_data)

    # Aggregate by date
    daily_avg = df.groupby("date").agg({
        "risk_score": "mean",
        "confidence": "mean"
    }).reset_index()

    # Create figure with secondary y-axis
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily_avg["date"],
        y=daily_avg["risk_score"],
        name="Avg Risk Score",
        mode='lines+markers',
        line=dict(color='#DC3545', width=2),
        yaxis='y1',
        hovertemplate='Date: %{x}<br>Avg Risk Score: %{y:.2f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=daily_avg["date"],
        y=daily_avg["confidence"],
        name="Avg Confidence",
        mode='lines+markers',
        line=dict(color='#28A745', width=2),
        yaxis='y2',
        hovertemplate='Date: %{x}<br>Avg Confidence: %{y:.3f}<extra></extra>'
    ))

    fig.update_layout(
        title="Average Decision Metrics Over Time",
        xaxis_title="Date",
        yaxis=dict(
            title="Avg Risk Score",
            titlefont=dict(color='#DC3545'),
            tickfont=dict(color='#DC3545')
        ),
        yaxis2=dict(
            title="Avg Confidence",
            titlefont=dict(color='#28A745'),
            tickfont=dict(color='#28A745'),
            overlaying='y',
            side='right'
        ),
        height=400,
        hovermode='x unified',
        showlegend=True
    )

    return fig


def create_risk_by_status_chart(applications: List[Dict[str, Any]]) -> alt.Chart:
    """Create risk distribution by status using Altair."""
    if not applications:
        return alt.Chart()

    df_data = []
    for app in applications:
        df_data.append({
            "Status": app["status"].replace("_", " ").title(),
            "Risk Level": app["risk_level"].title(),
            "Count": 1
        })

    df = pd.DataFrame(df_data)
    risk_status_counts = df.groupby(["Status", "Risk Level"]).size().reset_index(name="Count")

    # Color scale for risk levels
    risk_order = ["Low", "Medium", "High", "Very_high"]

    chart = alt.Chart(risk_status_counts).mark_bar().encode(
        x=alt.X("Status", title="Application Status"),
        y=alt.Y("Count", title="Number of Applications"),
        color=alt.Color(
            "Risk Level",
            scale=alt.Scale(
                domain=["Low", "Medium", "High", "Very_high"],
                range=["#28A745", "#FFA500", "#DC3545", "#8B0000"]
            )
        ),
        tooltip=["Status", "Risk Level", "Count"]
    ).properties(
        width=500,
        height=400,
        title="Risk Levels by Application Status"
    )

    return chart


def create_processing_time_statistics(applications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate processing time statistics."""
    processing_times = []

    for app in applications:
        if app["processing_time_days"] is not None:
            processing_times.append(app["processing_time_days"])

    if not processing_times:
        return {
            "min": 0,
            "max": 0,
            "median": 0,
            "mean": 0,
            "std": 0,
            "count": 0
        }

    processing_times = np.array(processing_times)

    return {
        "min": float(np.min(processing_times)),
        "max": float(np.max(processing_times)),
        "median": float(np.median(processing_times)),
        "mean": float(np.mean(processing_times)),
        "std": float(np.std(processing_times)),
        "count": len(processing_times)
    }


def create_processing_time_distribution(applications: List[Dict[str, Any]]) -> go.Figure:
    """Create processing time distribution using Plotly."""
    processing_times = [
        app["processing_time_days"]
        for app in applications
        if app["processing_time_days"] is not None
    ]

    if not processing_times:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Box(
        y=processing_times,
        name="Processing Time (Days)",
        boxmean='sd',
        marker=dict(color='#007BFF'),
        hovertemplate='Processing Time: %{y} days<extra></extra>'
    ))

    fig.update_layout(
        title="Processing Time Distribution (Box Plot)",
        yaxis_title="Days to Process",
        height=400,
        showlegend=True,
        xaxis_showticklabels=False
    )

    return fig


def create_approval_rate_by_risk_level(applications: List[Dict[str, Any]]) -> alt.Chart:
    """Create approval rate by risk level using Altair."""
    if not applications:
        return alt.Chart()

    df_data = []
    for app in applications:
        is_approved = app["status"] in ["approved", "conditional_approval"]
        df_data.append({
            "Risk Level": app["risk_level"].title(),
            "Approved": "Yes" if is_approved else "No",
            "Count": 1
        })

    df = pd.DataFrame(df_data)
    approval_by_risk = df.groupby(["Risk Level", "Approved"]).size().reset_index(name="Count")

    chart = alt.Chart(approval_by_risk).mark_bar().encode(
        x=alt.X("Risk Level", title="Risk Level"),
        y=alt.Y("Count", title="Number of Applications"),
        color=alt.Color(
            "Approved",
            scale=alt.Scale(domain=["Yes", "No"], range=["#28A745", "#DC3545"])
        ),
        tooltip=["Risk Level", "Approved", "Count"]
    ).properties(
        width=500,
        height=400,
        title="Approval Rate by Risk Level"
    )

    return chart


def render_page():
    """Render the analytics dashboard page."""
    st.set_page_config(
        page_title="Analytics Dashboard",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Analytics Dashboard")
    st.write("Comprehensive analytics and business intelligence for loan processing system")

    # Initialize session state
    initialize_session_state()

    # Load data
    applications = load_sample_analytics_data()

    # Date range filter
    st.sidebar.markdown("### Filter Options")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=90),
            key="date_start"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="date_end"
        )

    # Convert to datetime for filtering
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # Filter data by date range
    filtered_applications = filter_data_by_date_range(
        applications,
        start_datetime,
        end_datetime
    )

    # Calculate KPIs
    kpis = calculate_kpis(filtered_applications)

    # Display KPI metrics
    st.markdown("### Key Performance Indicators")
    render_kpi_metrics(kpis)

    # Divider
    st.markdown("---")

    # Row 1: Approval Rate Pie Chart and Risk Distribution Histogram
    st.markdown("### Application Status & Risk Analysis")
    col1, col2 = st.columns(2)

    with col1:
        pie_chart = create_approval_rate_pie_chart(filtered_applications)
        st.plotly_chart(pie_chart, use_container_width=True)

    with col2:
        histogram = create_risk_distribution_histogram(filtered_applications)
        st.plotly_chart(histogram, use_container_width=True)

    # Divider
    st.markdown("---")

    # Row 2: Decision Score Trend Chart
    st.markdown("### Decision Metrics Over Time")
    decision_chart = create_decision_score_chart(filtered_applications)
    st.plotly_chart(decision_chart, use_container_width=True)

    # Divider
    st.markdown("---")

    # Row 3: Risk by Status (Altair) and Approval by Risk Level (Altair)
    st.markdown("### Risk & Approval Analysis")
    col1, col2 = st.columns(2)

    with col1:
        risk_status_chart = create_risk_by_status_chart(filtered_applications)
        st.altair_chart(risk_status_chart, use_container_width=True)

    with col2:
        approval_risk_chart = create_approval_rate_by_risk_level(filtered_applications)
        st.altair_chart(approval_risk_chart, use_container_width=True)

    # Divider
    st.markdown("---")

    # Row 4: Processing Time Statistics
    st.markdown("### Processing Time Statistics")

    stats = create_processing_time_statistics(filtered_applications)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Min (days)", f"{stats['min']:.0f}")

    with col2:
        st.metric("Max (days)", f"{stats['max']:.0f}")

    with col3:
        st.metric("Mean (days)", f"{stats['mean']:.1f}")

    with col4:
        st.metric("Median (days)", f"{stats['median']:.1f}")

    with col5:
        st.metric("Std Dev", f"{stats['std']:.2f}")

    # Processing time distribution chart
    st.markdown("### Processing Time Distribution")
    processing_chart = create_processing_time_distribution(filtered_applications)
    st.plotly_chart(processing_chart, use_container_width=True)

    # Divider
    st.markdown("---")

    # Additional Statistics
    st.markdown("### Additional Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Avg Credit Score",
            f"{kpis['avg_credit_score']:.0f}",
            delta=None
        )

    with col2:
        st.metric(
            "Avg DTI Ratio",
            f"{kpis['avg_dti_ratio']:.1f}%",
            delta=None
        )

    with col3:
        total_loan_volume = sum([app["loan_amount"] for app in filtered_applications])
        st.metric(
            "Total Loan Volume",
            f"${total_loan_volume:,.0f}",
            delta=None
        )

    with col4:
        rejected_count = len([a for a in filtered_applications if a["status"] == "rejected"])
        st.metric(
            "Rejected Applications",
            f"{rejected_count}",
            delta=None
        )

    # Footer
    st.markdown("---")
    st.caption(
        f"Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Data range: {start_date} to {end_date} | "
        f"Total records shown: {len(filtered_applications)}"
    )


if __name__ == "__main__":
    render_page()
