# Admin Settings and Management Page

## Overview

The admin page (`pages/admin.py`) provides a comprehensive interface for system administration, configuration, and user management of the loan application processing system. It includes authentication, authorization, and audit logging capabilities.

## Features

### 1. Authentication & Authorization

#### Login System
- **Username/Password Authentication**: Secure login with SHA-256 password hashing
- **Session Management**: 30-minute session timeout (configurable)
- **Session Validation**: Automatic session validity checking
- **Audit Logging**: All login/logout events are logged

#### Default Test Users
```
Admin Account:
  Username: admin
  Password: admin123
  Role: Admin

Manager Account:
  Username: manager
  Password: manager123
  Role: Manager

Analyst Account:
  Username: analyst
  Password: analyst123
  Role: Analyst
```

#### Role-Based Access Control (RBAC)
Four user roles with hierarchical permissions:

- **Admin** (Highest Access)
  - Access to all features
  - Risk threshold configuration
  - User management
  - System health monitoring
  - Database statistics
  - Log viewer and audit trails

- **Manager** (Mid-High Access)
  - System health monitoring
  - Database statistics
  - Read-only log viewer
  - Cannot modify configurations

- **Analyst** (Mid Access)
  - Log viewer and filtering
  - Read-only access to statistics
  - Cannot manage users or configurations

- **Viewer** (Basic Access)
  - Read-only dashboard
  - View public statistics only

### 2. Risk Thresholds Configuration

#### Configurable Parameters

**Minimum Thresholds:**
- `credit_score_minimum`: Minimum acceptable credit score (default: 620, range: 300-850)
- `employment_years_minimum`: Minimum years at current employment (default: 2.0)
- `savings_to_loan_ratio`: Minimum savings to loan amount ratio (default: 0.10)

**Maximum Thresholds:**
- `debt_to_income_maximum`: Maximum debt-to-income ratio in % (default: 43.0%)

**Risk Score Classification:**
- `risk_score_low_threshold`: Score threshold for low risk (default: 30.0)
- `risk_score_medium_threshold`: Score threshold for medium risk (default: 50.0)
- `risk_score_high_threshold`: Score threshold for high risk (default: 70.0)

**Approval Confidence Thresholds:**
- `approval_threshold_low`: Confidence required for low-risk approval (default: 0.85)
- `approval_threshold_medium`: Confidence required for medium-risk approval (default: 0.75)
- `approval_threshold_high`: Confidence required for high-risk approval (default: 0.65)

#### Configuration Management
- **Real-time Updates**: Changes take effect immediately
- **Persistent Storage**: Configurations saved to JSON file (`config/risk_thresholds.json`)
- **Reset Option**: One-click reset to default values
- **Audit Trail**: All configuration changes are logged with timestamp and user info

#### File Structure
```
config/
└── risk_thresholds.json
    {
      "credit_score_minimum": 620,
      "debt_to_income_maximum": 43.0,
      "employment_years_minimum": 2.0,
      "savings_to_loan_ratio": 0.10,
      "risk_score_low_threshold": 30.0,
      "risk_score_medium_threshold": 50.0,
      "risk_score_high_threshold": 70.0,
      "approval_threshold_low": 0.85,
      "approval_threshold_medium": 0.75,
      "approval_threshold_high": 0.65
    }
```

### 3. System Health Status

Real-time monitoring of system components:

**Metrics Displayed:**
- System Status: Overall health indicator (🟢 Healthy / 🔴 Error)
- API Response Time: Average latency in milliseconds
- Database Connection: Connection status
- Uptime: Hours system has been running

**System Resources:**
- Memory Usage: Current memory consumption percentage
- CPU Usage: Current CPU utilization percentage
- Disk Usage: Storage utilization percentage

**Status Indicators:**
- Color-coded status badges for quick visual reference
- Real-time updates (in production environment)

### 4. Database Statistics

Comprehensive database analytics:

**Key Metrics:**
- Total Applications: Complete count of all loan applications
- Total Users: Number of system users
- Total Loan Records: All financial records
- Database Size: Storage size in MB
- Last Backup: Timestamp of last backup

**Application Analytics:**
- Total Approved: Count of approved applications
- Total Rejected: Count of rejected applications
- Total Pending: Count of pending applications
- Average Processing Time: Days to decision
- Approval Rate: Percentage of approved applications

**Breakdown Visualization:**
- Table showing status distribution
- Calculated percentages for each status
- Easy-to-read metrics cards

### 5. Log Viewer with Filtering

Comprehensive audit trail system:

#### Log Types Tracked
- `LOGIN`: User login events
- `LOGOUT`: User logout events
- `CONFIG_UPDATE`: Configuration changes
- `USER_CREATE`: New user creation
- `USER_UPDATE`: User role updates
- `USER_DEACTIVATE`: User account deactivation

#### Filtering Capabilities
- **Filter by Action Type**: Multiple selection of log types
- **Filter by User**: Partial text matching for username
- **Display Limit**: Configurable number of recent logs to show
- **Time-based Sorting**: Automatic sorting by timestamp (most recent first)

#### Log Entry Structure
```python
{
    "timestamp": "2024-06-19T14:30:00.000000",
    "user": "admin",
    "action": "Risk thresholds updated",
    "action_type": "CONFIG_UPDATE",
    "details": "{...configuration details...}"
}
```

#### Export Functionality
- **CSV Download**: Export filtered logs as CSV file
- **Automatic Naming**: Files include timestamp for easy identification
- **Timestamp Format**: Human-readable format in exports

### 6. User Role Management

Complete user administration interface:

#### Features

**View Users Tab:**
- Display all users in table format
- Shows username, role, creation date, and active status
- Real-time updates

**Create User Tab:**
- Create new user accounts
- Set username and password
- Assign initial role
- Password confirmation requirement
- Minimum 8-character password validation
- Automatic logging of user creation

**Manage Roles Tab:**
- Update existing user roles
- Change role assignments
- Activate/deactivate user accounts
- Self-account protection (cannot modify own account)
- Immediate effect of changes

#### User Attributes
- Username: Unique identifier
- Role: One of [Admin, Manager, Analyst, Viewer]
- Creation Date: Account creation timestamp
- Active Status: Boolean flag (active/inactive)
- Last Login: Timestamp of last successful login

#### Role Assignment
Easy dropdown-based role selection with all available roles:
- Admin
- Manager
- Analyst
- Viewer

## File Structure

```
/home/ubuntu/Desktop/demo/
├── pages/
│   ├── admin.py              (Main admin page)
│   ├── analytics.py          (Existing analytics page)
│   └── history.py            (Existing history page)
├── config/
│   └── risk_thresholds.json  (Persistent configuration)
└── logs/
    └── admin_YYYY-MM-DD.log  (Daily log files)
```

## Usage

### Starting the Application

1. **Run Streamlit Application:**
   ```bash
   streamlit run pages/admin.py
   ```

2. **Access the Application:**
   - Open browser to `http://localhost:8501`
   - You'll be directed to the login page

3. **Login:**
   - Use one of the default test credentials
   - Click "Login" button

4. **Navigate Sections:**
   - Use sidebar menu to select different admin sections
   - Each section has specific access requirements

### Typical Workflows

#### Configure Risk Thresholds (Admin Only)
1. Login as admin
2. Navigate to "⚙️ Risk Configuration"
3. Adjust threshold values as needed
4. Click "💾 Save Changes"
5. View confirmation and audit log entry

#### Monitor System Health (Manager+)
1. Login as manager or admin
2. Navigate to "🏥 System Health"
3. Review key metrics
4. Monitor resource usage

#### View Audit Logs (Analyst+)
1. Login as analyst or higher
2. Navigate to "📋 Audit Logs"
3. Apply filters as needed
4. Download logs for external audit if required

#### Manage Users (Admin Only)
1. Login as admin
2. Navigate to "👥 User Management"
3. Use tabs for different operations:
   - View Users: See all user accounts
   - Create User: Add new user
   - Manage Roles: Update roles or deactivate users

## Technical Details

### Authentication Flow
```
User Input (username/password)
    ↓
Authenticate User (check against default users)
    ↓
Hash Password (SHA-256)
    ↓
Compare with stored hash
    ↓
Create Session (store in session_state)
    ↓
Log Authentication Event
```

### Access Control Flow
```
User Request → Check Authentication → Check Role → Check Feature Access → Grant/Deny Access
```

### Configuration Persistence
```
In-Memory Cache (session_state)
    ↓
User clicks Save
    ↓
Validate configuration
    ↓
Write to JSON file (config/risk_thresholds.json)
    ↓
Log configuration change
    ↓
Reload into session
```

### Logging System
```
Admin Action Occurs
    ↓
Create Log Entry (timestamp, user, action, type, details)
    ↓
Append to session_state.admin_logs
    ↓
Log to file (logs/admin_YYYY-MM-DD.log)
    ↓
Available for view in Log Viewer
```

## Security Considerations

### Current Implementation
- SHA-256 password hashing
- Session timeout (30 minutes default)
- Role-based access control
- Audit logging of all admin actions
- Self-protection (cannot modify own account)

### Production Recommendations
1. **Database Integration**: Store users in database, not in code
2. **Password Hashing**: Use bcrypt or argon2 instead of SHA-256
3. **Multi-Factor Authentication**: Add 2FA support
4. **SSL/TLS**: Enable HTTPS for all connections
5. **Rate Limiting**: Implement login attempt limiting
6. **Audit Log Encryption**: Encrypt sensitive log entries
7. **Access Logging**: Log all page accesses
8. **IP Whitelist**: Restrict admin access to known IPs
9. **Session Encryption**: Use secure session storage
10. **Regular Backups**: Automated backup of configuration

## Extension Points

The admin page is designed to be extensible. Common extensions:

### Adding New Features
1. Create feature access level in `FEATURE_ACCESS`
2. Add new section in sidebar navigation
3. Create render function with `require_access()` check
4. Implement functionality with audit logging

### Adding New Configuration Options
1. Add to `DEFAULT_RISK_THRESHOLDS`
2. Create UI controls in `render_risk_thresholds_config()`
3. Update save/load functions
4. Document new option

### Adding Custom Roles
1. Extend `UserRole` enum
2. Update `ROLE_PERMISSIONS` mapping
3. Update `FEATURE_ACCESS` for new permission levels
4. Create role-specific UI sections

## Troubleshooting

### Cannot Login
- Verify username and password (case-sensitive)
- Check if user account is active
- Default users: admin/admin123, manager/manager123, analyst/analyst123

### Configuration Changes Not Saving
- Check if `config/` directory exists (auto-created if missing)
- Verify file write permissions
- Check disk space availability
- Review logs for error messages

### Session Timeout
- Default timeout is 30 minutes
- Session warning appears at 5 minutes remaining
- Login again to start new session

### Access Denied Errors
- Verify your user role has required permissions
- Check role hierarchy: Admin > Manager > Analyst > Viewer
- Review audit logs to see access attempts

## API Reference

### Key Functions

#### Authentication
```python
authenticate_user(username: str, password: str) -> bool
login_user(username: str, role: UserRole)
logout_user()
is_session_valid() -> bool
check_access(required_access_level: AccessLevel) -> bool
```

#### Configuration
```python
load_risk_thresholds() -> Dict[str, float]
save_risk_thresholds(thresholds: Dict[str, float]) -> bool
get_config_file_path() -> Path
```

#### User Management
```python
get_all_users() -> List[Dict[str, Any]]
create_user(username: str, password: str, role: UserRole) -> bool
update_user_role(username: str, new_role: UserRole) -> bool
deactivate_user(username: str) -> bool
```

#### Logging
```python
log_admin_action(action: str, action_type: str, user: str, details: str)
read_system_logs(max_lines: int = 100) -> List[str]
```

#### System Information
```python
get_system_health() -> Dict[str, Any]
get_database_stats() -> Dict[str, Any]
```

## Version History

**v1.0 (2024-06-19)**
- Initial release
- Authentication and authorization
- Risk threshold configuration
- System health monitoring
- Database statistics
- Log viewer with filtering
- User role management
- Comprehensive audit trail

## Support

For issues, questions, or feature requests, please refer to the main project documentation or contact the development team.
