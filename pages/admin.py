"""
Admin Settings and Management Page

Provides a comprehensive interface for system administration including:
- Configuration settings for risk thresholds (editable)
- System health status monitoring
- Database statistics (total records, storage size)
- Log viewer with filtering capabilities
- User role management
- Authentication and authorization checks
"""

import streamlit as st
import pandas as pd
import json
import logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
import os
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Constants and Enums
# ============================================================================

class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AccessLevel(int, Enum):
    """Access levels for different features."""
    ADMIN_ONLY = 0
    MANAGER_AND_UP = 1
    ANALYST_AND_UP = 2
    ALL_AUTHENTICATED = 3


# Permission mapping: role -> access level
ROLE_PERMISSIONS = {
    UserRole.ADMIN: AccessLevel.ADMIN_ONLY,
    UserRole.MANAGER: AccessLevel.MANAGER_AND_UP,
    UserRole.ANALYST: AccessLevel.ANALYST_AND_UP,
    UserRole.VIEWER: AccessLevel.ALL_AUTHENTICATED,
}

# Feature access requirements
FEATURE_ACCESS = {
    "risk_thresholds": AccessLevel.ADMIN_ONLY,
    "user_management": AccessLevel.ADMIN_ONLY,
    "system_health": AccessLevel.MANAGER_AND_UP,
    "database_stats": AccessLevel.MANAGER_AND_UP,
    "log_viewer": AccessLevel.ANALYST_AND_UP,
    "configuration": AccessLevel.ADMIN_ONLY,
}

# Default risk thresholds configuration
DEFAULT_RISK_THRESHOLDS = {
    "credit_score_minimum": 620,
    "debt_to_income_maximum": 43.0,
    "employment_years_minimum": 2.0,
    "savings_to_loan_ratio": 0.10,
    "risk_score_low_threshold": 30.0,
    "risk_score_medium_threshold": 50.0,
    "risk_score_high_threshold": 70.0,
    "approval_threshold_low": 0.85,
    "approval_threshold_medium": 0.75,
    "approval_threshold_high": 0.65,
}


# ============================================================================
# Authentication Functions
# ============================================================================

def initialize_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "login_time" not in st.session_state:
        st.session_state.login_time = None
    if "session_timeout_minutes" not in st.session_state:
        st.session_state.session_timeout_minutes = 30
    if "risk_thresholds" not in st.session_state:
        st.session_state.risk_thresholds = load_risk_thresholds()
    if "admin_logs" not in st.session_state:
        st.session_state.admin_logs = []


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_default_users() -> Dict[str, Dict[str, Any]]:
    """Get default admin users (in production, load from database)."""
    return {
        "admin": {
            "password_hash": hash_password("admin123"),
            "role": UserRole.ADMIN,
            "created_date": "2024-01-01",
            "active": True,
        },
        "manager": {
            "password_hash": hash_password("manager123"),
            "role": UserRole.MANAGER,
            "created_date": "2024-01-05",
            "active": True,
        },
        "analyst": {
            "password_hash": hash_password("analyst123"),
            "role": UserRole.ANALYST,
            "created_date": "2024-01-10",
            "active": True,
        },
    }


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.

    Args:
        username: Username to authenticate
        password: Password to verify

    Returns:
        True if authentication successful, False otherwise
    """
    users = get_default_users()

    if username not in users:
        logger.warning(f"Login attempt with non-existent user: {username}")
        return False

    user = users[username]

    if not user.get("active", False):
        logger.warning(f"Login attempt with inactive user: {username}")
        return False

    password_hash = hash_password(password)
    if user["password_hash"] != password_hash:
        logger.warning(f"Failed login attempt for user: {username}")
        return False

    logger.info(f"Successful authentication for user: {username}")
    return True


def login_user(username: str, role: UserRole):
    """Update session state with authenticated user info."""
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.user_role = role
    st.session_state.login_time = datetime.now()
    log_admin_action(f"User '{username}' logged in", "LOGIN", username)


def logout_user():
    """Log out the current user."""
    username = st.session_state.username
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.session_state.login_time = None
    log_admin_action(f"User '{username}' logged out", "LOGOUT", username)


def is_session_valid() -> bool:
    """Check if current session is still valid."""
    if not st.session_state.authenticated:
        return False

    if st.session_state.login_time is None:
        return False

    elapsed_minutes = (datetime.now() - st.session_state.login_time).total_seconds() / 60
    return elapsed_minutes < st.session_state.session_timeout_minutes


def check_access(required_access_level: AccessLevel) -> bool:
    """
    Check if the current user has required access level.

    Args:
        required_access_level: Minimum access level required

    Returns:
        True if user has sufficient access, False otherwise
    """
    if not st.session_state.authenticated or not is_session_valid():
        return False

    user_access_level = ROLE_PERMISSIONS.get(st.session_state.user_role, AccessLevel.ALL_AUTHENTICATED)
    return user_access_level <= required_access_level


def require_access(required_access_level: AccessLevel, feature_name: str = ""):
    """
    Require minimum access level. Shows error message and stops execution if not met.

    Args:
        required_access_level: Minimum access level required
        feature_name: Name of feature being accessed (for error message)
    """
    if not check_access(required_access_level):
        st.error(f"Access Denied. You do not have permission to access {feature_name}.")
        st.stop()


# ============================================================================
# Logging Functions
# ============================================================================

def log_admin_action(action: str, action_type: str, user: str, details: str = "") -> None:
    """Log an admin action for audit trail."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "action_type": action_type,
        "details": details,
    }
    st.session_state.admin_logs.append(log_entry)
    logger.info(f"ADMIN_ACTION: {action} by {user} ({action_type})")


def get_log_file_path() -> Path:
    """Get path to system log file."""
    log_dir = Path("/home/ubuntu/Desktop/demo/logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir / f"admin_{datetime.now().strftime('%Y-%m-%d')}.log"


def read_system_logs(max_lines: int = 100) -> List[str]:
    """Read system logs from file."""
    log_file = get_log_file_path()

    if not log_file.exists():
        return []

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return [f"Error reading logs: {str(e)}"]


# ============================================================================
# Configuration Management
# ============================================================================

def get_config_file_path() -> Path:
    """Get path to configuration file."""
    config_dir = Path("/home/ubuntu/Desktop/demo/config")
    config_dir.mkdir(exist_ok=True)
    return config_dir / "risk_thresholds.json"


def load_risk_thresholds() -> Dict[str, float]:
    """Load risk thresholds from configuration file."""
    config_file = get_config_file_path()

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                logger.info("Risk thresholds loaded from configuration file")
                return config
        except Exception as e:
            logger.error(f"Error loading risk thresholds: {e}")
            return DEFAULT_RISK_THRESHOLDS.copy()

    return DEFAULT_RISK_THRESHOLDS.copy()


def save_risk_thresholds(thresholds: Dict[str, float]) -> bool:
    """Save risk thresholds to configuration file."""
    config_file = get_config_file_path()

    try:
        with open(config_file, 'w') as f:
            json.dump(thresholds, f, indent=2)
        log_admin_action(
            "Risk thresholds updated",
            "CONFIG_UPDATE",
            st.session_state.username,
            json.dumps(thresholds)
        )
        logger.info("Risk thresholds saved to configuration file")
        return True
    except Exception as e:
        logger.error(f"Error saving risk thresholds: {e}")
        st.error(f"Failed to save configuration: {str(e)}")
        return False


# ============================================================================
# Database Functions
# ============================================================================

def get_database_stats() -> Dict[str, Any]:
    """Get statistics about the database."""
    try:
        # In production, query actual database
        db_stats = {
            "total_applications": 1_245,
            "total_users": 23,
            "total_loan_records": 3_892,
            "database_size_mb": 156.7,
            "last_backup": (datetime.now() - timedelta(hours=2)).isoformat(),
            "total_approved": 892,
            "total_rejected": 198,
            "total_pending": 155,
            "average_processing_time_days": 4.2,
        }
        return db_stats
    except Exception as e:
        logger.error(f"Error fetching database stats: {e}")
        return {}


def get_system_health() -> Dict[str, Any]:
    """Get current system health status."""
    try:
        health = {
            "status": "healthy",
            "api_response_time_ms": 45,
            "database_connection": "connected",
            "memory_usage_percent": 62.3,
            "cpu_usage_percent": 28.5,
            "disk_usage_percent": 45.2,
            "uptime_hours": 72,
            "last_check": datetime.now().isoformat(),
        }
        return health
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# User Management
# ============================================================================

def get_all_users() -> List[Dict[str, Any]]:
    """Get list of all users with their details."""
    users = get_default_users()
    user_list = []

    for username, user_data in users.items():
        user_list.append({
            "username": username,
            "role": user_data["role"].value,
            "created_date": user_data["created_date"],
            "active": user_data["active"],
            "last_login": None,  # In production, fetch from database
        })

    return user_list


def create_user(username: str, password: str, role: UserRole) -> bool:
    """Create a new user (in production, save to database)."""
    try:
        log_admin_action(
            f"New user created: {username} with role {role.value}",
            "USER_CREATE",
            st.session_state.username,
            f"role={role.value}"
        )
        logger.info(f"User created: {username} with role {role.value}")
        return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False


def update_user_role(username: str, new_role: UserRole) -> bool:
    """Update user's role."""
    try:
        log_admin_action(
            f"User role updated: {username}",
            "USER_UPDATE",
            st.session_state.username,
            f"new_role={new_role.value}"
        )
        logger.info(f"User role updated: {username} -> {new_role.value}")
        return True
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        return False


def deactivate_user(username: str) -> bool:
    """Deactivate a user account."""
    try:
        log_admin_action(
            f"User deactivated: {username}",
            "USER_DEACTIVATE",
            st.session_state.username
        )
        logger.info(f"User deactivated: {username}")
        return True
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        return False


# ============================================================================
# UI Components
# ============================================================================

def render_login_page():
    """Render login page."""
    st.set_page_config(
        page_title="Admin Login",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("## 🔐 Admin Portal Login")
        st.markdown("---")

        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            elif authenticate_user(username, password):
                users = get_default_users()
                user_role = users[username]["role"]
                login_user(username, user_role)
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid username or password")

        st.markdown("---")
        st.markdown(
            """
            **Demo Credentials:**
            - Username: `admin` | Password: `admin123` | Role: Admin
            - Username: `manager` | Password: `manager123` | Role: Manager
            - Username: `analyst` | Password: `analyst123` | Role: Analyst
            """
        )


def render_top_bar():
    """Render top navigation bar with user info."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"### 👤 Logged in as: **{st.session_state.username}** ({st.session_state.user_role.value.upper()})")

    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()


def render_risk_thresholds_config():
    """Render risk thresholds configuration section."""
    require_access(FEATURE_ACCESS["risk_thresholds"], "Risk Thresholds Configuration")

    st.markdown("## ⚙️ Risk Thresholds Configuration")
    st.markdown("Configure the risk assessment thresholds for loan applications")
    st.markdown("---")

    # Create columns for better layout
    col1, col2 = st.columns(2)

    thresholds = st.session_state.risk_thresholds.copy()

    with col1:
        st.markdown("### Minimum Thresholds")
        thresholds["credit_score_minimum"] = st.number_input(
            "Minimum Credit Score",
            value=thresholds["credit_score_minimum"],
            min_value=300,
            max_value=850,
            help="Minimum acceptable credit score"
        )

        thresholds["employment_years_minimum"] = st.number_input(
            "Minimum Employment Years",
            value=thresholds["employment_years_minimum"],
            min_value=0.0,
            max_value=50.0,
            step=0.5,
            help="Minimum years at current employment"
        )

        thresholds["savings_to_loan_ratio"] = st.number_input(
            "Savings to Loan Ratio",
            value=thresholds["savings_to_loan_ratio"],
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            help="Minimum ratio of savings to loan amount"
        )

    with col2:
        st.markdown("### Maximum Thresholds")
        thresholds["debt_to_income_maximum"] = st.number_input(
            "Maximum Debt-to-Income Ratio (%)",
            value=thresholds["debt_to_income_maximum"],
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            help="Maximum acceptable debt-to-income ratio"
        )

    # Risk Score Classification
    st.markdown("### Risk Score Classification")
    col1, col2, col3 = st.columns(3)

    with col1:
        thresholds["risk_score_low_threshold"] = st.number_input(
            "Low Risk Threshold",
            value=thresholds["risk_score_low_threshold"],
            min_value=0.0,
            max_value=100.0,
            step=1.0
        )

    with col2:
        thresholds["risk_score_medium_threshold"] = st.number_input(
            "Medium Risk Threshold",
            value=thresholds["risk_score_medium_threshold"],
            min_value=0.0,
            max_value=100.0,
            step=1.0
        )

    with col3:
        thresholds["risk_score_high_threshold"] = st.number_input(
            "High Risk Threshold",
            value=thresholds["risk_score_high_threshold"],
            min_value=0.0,
            max_value=100.0,
            step=1.0
        )

    # Approval Confidence Thresholds
    st.markdown("### Approval Confidence Thresholds")
    col1, col2, col3 = st.columns(3)

    with col1:
        thresholds["approval_threshold_low"] = st.number_input(
            "Low Risk Approval Threshold",
            value=thresholds["approval_threshold_low"],
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )

    with col2:
        thresholds["approval_threshold_medium"] = st.number_input(
            "Medium Risk Approval Threshold",
            value=thresholds["approval_threshold_medium"],
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )

    with col3:
        thresholds["approval_threshold_high"] = st.number_input(
            "High Risk Approval Threshold",
            value=thresholds["approval_threshold_high"],
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Save Changes", use_container_width=True):
            if save_risk_thresholds(thresholds):
                st.session_state.risk_thresholds = thresholds
                st.success("Risk thresholds updated successfully!")
                st.rerun()

    with col2:
        if st.button("↺ Reset to Defaults", use_container_width=True):
            if save_risk_thresholds(DEFAULT_RISK_THRESHOLDS.copy()):
                st.session_state.risk_thresholds = DEFAULT_RISK_THRESHOLDS.copy()
                st.success("Reset to default thresholds!")
                st.rerun()


def render_system_health():
    """Render system health status section."""
    require_access(FEATURE_ACCESS["system_health"], "System Health")

    st.markdown("## 🏥 System Health Status")
    st.markdown("---")

    health = get_system_health()

    col1, col2, col3, col4 = st.columns(4)

    status_color = "🟢" if health.get("status") == "healthy" else "🔴"
    with col1:
        st.metric("System Status", f"{status_color} {health.get('status', 'unknown').upper()}")

    with col2:
        st.metric("API Response Time", f"{health.get('api_response_time_ms', 0)}ms")

    with col3:
        st.metric("Uptime", f"{health.get('uptime_hours', 0)}h")

    with col4:
        st.metric("DB Connection", health.get("database_connection", "unknown"))

    # System metrics
    st.markdown("### System Metrics")
    col1, col2, col3 = st.columns(3)

    with col1:
        memory = health.get("memory_usage_percent", 0)
        st.metric("Memory Usage", f"{memory}%")

    with col2:
        cpu = health.get("cpu_usage_percent", 0)
        st.metric("CPU Usage", f"{cpu}%")

    with col3:
        disk = health.get("disk_usage_percent", 0)
        st.metric("Disk Usage", f"{disk}%")


def render_database_stats():
    """Render database statistics section."""
    require_access(FEATURE_ACCESS["database_stats"], "Database Statistics")

    st.markdown("## 📊 Database Statistics")
    st.markdown("---")

    stats = get_database_stats()

    # Key statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Applications", f"{stats.get('total_applications', 0):,}")

    with col2:
        st.metric("Total Users", f"{stats.get('total_users', 0)}")

    with col3:
        st.metric("Database Size", f"{stats.get('database_size_mb', 0):.1f} MB")

    with col4:
        st.metric("Avg Processing Time", f"{stats.get('average_processing_time_days', 0):.1f} days")

    # Application breakdown
    st.markdown("### Application Decision Breakdown")

    breakdown_data = {
        "Status": ["Approved", "Rejected", "Pending"],
        "Count": [
            stats.get("total_approved", 0),
            stats.get("total_rejected", 0),
            stats.get("total_pending", 0)
        ]
    }
    df_breakdown = pd.DataFrame(breakdown_data)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

    with col2:
        # Calculate percentages
        total = sum(breakdown_data["Count"])
        if total > 0:
            percentages = [count / total * 100 for count in breakdown_data["Count"]]
            breakdown_data["Percentage"] = [f"{p:.1f}%" for p in percentages]

            st.markdown("### Approval Rate")
            approval_rate = (stats.get("total_approved", 0) / total * 100) if total > 0 else 0
            st.metric("Approval Rate", f"{approval_rate:.1f}%")


def render_log_viewer():
    """Render log viewer with filtering."""
    require_access(FEATURE_ACCESS["log_viewer"], "Log Viewer")

    st.markdown("## 📋 Admin Action Logs")
    st.markdown("View and filter system and admin action logs")
    st.markdown("---")

    # Log filtering options
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_action_type = st.multiselect(
            "Filter by Action Type",
            options=["LOGIN", "LOGOUT", "CONFIG_UPDATE", "USER_CREATE", "USER_UPDATE", "USER_DEACTIVATE"],
            default=[]
        )

    with col2:
        filter_user = st.text_input("Filter by User (partial match)")

    with col3:
        max_logs = st.number_input("Show last N logs", value=100, min_value=10, max_value=1000)

    # Get logs from session state
    logs = st.session_state.admin_logs.copy()

    # Apply filters
    if filter_action_type:
        logs = [log for log in logs if log.get("action_type") in filter_action_type]

    if filter_user:
        logs = [log for log in logs if filter_user.lower() in log.get("user", "").lower()]

    # Sort by timestamp descending and limit
    logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:max_logs]

    if logs:
        # Convert to DataFrame for display
        df_logs = pd.DataFrame(logs)
        df_logs["timestamp"] = pd.to_datetime(df_logs["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")

        st.dataframe(
            df_logs[["timestamp", "user", "action_type", "action", "details"]],
            use_container_width=True,
            hide_index=True
        )

        # Export logs
        csv_logs = df_logs.to_csv(index=False)
        st.download_button(
            label="📥 Download Logs as CSV",
            data=csv_logs,
            file_name=f"admin_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No logs found matching the filters")


def render_user_management():
    """Render user role management section."""
    require_access(FEATURE_ACCESS["user_management"], "User Management")

    st.markdown("## 👥 User Role Management")
    st.markdown("Manage user accounts and roles")
    st.markdown("---")

    # Create tabs for user management sections
    tab1, tab2, tab3 = st.tabs(["View Users", "Create User", "Manage Roles"])

    with tab1:
        st.markdown("### All Users")
        users_list = get_all_users()
        df_users = pd.DataFrame(users_list)

        st.dataframe(
            df_users,
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.markdown("### Create New User")

        with st.form("create_user_form"):
            new_username = st.text_input("Username", placeholder="e.g., john_doe")
            new_password = st.text_input("Password", type="password", placeholder="Enter strong password")
            confirm_password = st.text_input("Confirm Password", type="password")
            new_role = st.selectbox(
                "User Role",
                options=[r.value for r in UserRole],
                format_func=lambda x: x.upper()
            )

            if st.form_submit_button("Create User", use_container_width=True):
                if not new_username:
                    st.error("Username is required")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    if create_user(new_username, new_password, UserRole(new_role)):
                        st.success(f"User '{new_username}' created successfully with role '{new_role}'")
                    else:
                        st.error("Failed to create user")

    with tab3:
        st.markdown("### Update User Roles")

        users_list = get_all_users()
        user_options = {u["username"]: u for u in users_list}

        selected_username = st.selectbox(
            "Select User to Modify",
            options=list(user_options.keys())
        )

        if selected_username and selected_username != st.session_state.username:
            user_info = user_options[selected_username]

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown(f"**Current Role:** {user_info['role'].upper()}")
                new_role = st.selectbox(
                    "Assign New Role",
                    options=[r.value for r in UserRole],
                    format_func=lambda x: x.upper(),
                    key="role_select"
                )

            with col2:
                st.markdown(f"**Created:** {user_info['created_date']}")
                is_active = st.checkbox(f"Active", value=user_info['active'])

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("💾 Update Role", use_container_width=True):
                    if update_user_role(selected_username, UserRole(new_role)):
                        st.success(f"Role updated for '{selected_username}'")
                    else:
                        st.error("Failed to update user role")

            with col2:
                if not is_active:
                    if st.button("🚫 Deactivate User", use_container_width=True, type="secondary"):
                        if deactivate_user(selected_username):
                            st.success(f"User '{selected_username}' deactivated")
                        else:
                            st.error("Failed to deactivate user")
        elif selected_username == st.session_state.username:
            st.warning("You cannot modify your own account")


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main admin page application."""
    initialize_session_state()

    # Check authentication
    if not st.session_state.authenticated or not is_session_valid():
        render_login_page()
        return

    # Configure page
    st.set_page_config(
        page_title="Admin Panel",
        page_icon="⚙️",
        layout="wide",
    )

    # Render top bar
    render_top_bar()
    st.markdown("---")

    # Create sidebar navigation
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio(
        "Select Section",
        options=[
            "📊 Dashboard",
            "⚙️ Risk Configuration",
            "🏥 System Health",
            "📈 Database Stats",
            "📋 Audit Logs",
            "👥 User Management",
        ]
    )

    # Render selected page
    if page == "📊 Dashboard":
        st.markdown("## 📊 Admin Dashboard")
        st.markdown("---")

        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Logged in User", st.session_state.username)
        with col2:
            login_time = st.session_state.login_time.strftime("%H:%M:%S") if st.session_state.login_time else "N/A"
            st.metric("Login Time", login_time)
        with col3:
            st.metric("User Role", st.session_state.user_role.value.upper())

        st.markdown("### Recent Admin Actions")
        recent_logs = sorted(
            st.session_state.admin_logs,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:5]

        if recent_logs:
            df_recent = pd.DataFrame(recent_logs)
            df_recent["timestamp"] = pd.to_datetime(df_recent["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(
                df_recent[["timestamp", "user", "action_type", "action"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No admin actions logged yet")

    elif page == "⚙️ Risk Configuration":
        render_risk_thresholds_config()

    elif page == "🏥 System Health":
        render_system_health()

    elif page == "📈 Database Stats":
        render_database_stats()

    elif page == "📋 Audit Logs":
        render_log_viewer()

    elif page == "👥 User Management":
        render_user_management()

    # Session timeout warning
    if st.session_state.login_time:
        elapsed_minutes = (datetime.now() - st.session_state.login_time).total_seconds() / 60
        remaining_minutes = st.session_state.session_timeout_minutes - elapsed_minutes

        if remaining_minutes < 5:
            st.warning(f"⏰ Session will expire in {int(remaining_minutes)} minutes. Consider saving your work.")


if __name__ == "__main__":
    main()
