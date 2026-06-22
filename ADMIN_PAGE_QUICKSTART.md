# Admin Page Quick Start Guide

## Getting Started in 5 Minutes

### 1. Launch the Admin Page

```bash
cd /home/ubuntu/Desktop/demo
streamlit run pages/admin.py
```

This will start the Streamlit application and open it in your browser at `http://localhost:8501`

### 2. Login

Use one of these test accounts:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin (full access) |
| manager | manager123 | Manager (system monitoring) |
| analyst | analyst123 | Analyst (log viewer) |

Click the "Login" button after entering credentials.

### 3. Navigate Using the Sidebar

Once logged in, you'll see a sidebar menu with these options:

- **📊 Dashboard** - Overview and recent actions
- **⚙️ Risk Configuration** - Edit risk thresholds (Admin only)
- **🏥 System Health** - Monitor system status (Manager+)
- **📈 Database Stats** - View database statistics (Manager+)
- **📋 Audit Logs** - View and filter logs (Analyst+)
- **👥 User Management** - Manage users (Admin only)

## Common Tasks

### Configure Risk Thresholds (Admin)

1. Login as `admin`
2. Select "⚙️ Risk Configuration" from sidebar
3. Adjust threshold values:
   - Minimum Credit Score: 620 (default)
   - Maximum Debt-to-Income: 43% (default)
   - Employment Years: 2.0 years (default)
4. Click "💾 Save Changes"
5. Check the audit log to confirm

**Key Settings:**
- Credit Score Range: 300-850
- Debt-to-Income: 0-100%
- Risk Score Thresholds: 0-100
- Approval Confidence: 0.0-1.0

### Monitor System Health (Manager)

1. Login as `manager`
2. Select "🏥 System Health"
3. View real-time metrics:
   - System status (healthy/error)
   - API response time
   - CPU, Memory, Disk usage
   - Database connection status

### View Database Statistics (Manager)

1. Login as `manager`
2. Select "📈 Database Stats"
3. See metrics like:
   - Total applications (1,245)
   - Approval rate (71.6%)
   - Average processing time (4.2 days)
   - Database size (156.7 MB)

### View Audit Logs (Analyst)

1. Login as `analyst`
2. Select "📋 Audit Logs"
3. Filter logs by:
   - Action type (Login, Logout, Config Update, etc.)
   - Username (partial match)
   - Number of recent logs
4. Download logs as CSV for external audit

### Create New User (Admin)

1. Login as `admin`
2. Select "👥 User Management"
3. Click "Create User" tab
4. Fill in:
   - Username: `john_doe`
   - Password: (minimum 8 characters)
   - Confirm Password
   - Role: Select from dropdown
5. Click "Create User"

### Update User Roles (Admin)

1. Login as `admin`
2. Select "👥 User Management"
3. Click "Manage Roles" tab
4. Select user from dropdown
5. Assign new role
6. Click "💾 Update Role"

## Understanding Access Levels

### Admin
- **Access Level:** Full system access
- **Can Do:** Configure settings, manage users, view all logs
- **Typical User:** System administrator

### Manager
- **Access Level:** System monitoring
- **Can Do:** View health status, database stats, recent logs
- **Typical User:** Operations manager

### Analyst
- **Access Level:** Log viewer
- **Can Do:** View and filter all audit logs
- **Typical User:** Compliance officer, analyst

### Viewer
- **Access Level:** Read-only dashboard
- **Can Do:** View public statistics (if expanded)
- **Typical User:** Executive review

## File Locations

```
/home/ubuntu/Desktop/demo/
├── pages/
│   └── admin.py                    # Main admin page
├── config/
│   └── risk_thresholds.json        # Saved configuration
└── logs/
    └── admin_YYYY-MM-DD.log        # Daily audit logs
```

## Key Features Overview

### 1. Risk Thresholds Configuration
- Manage credit score minimums
- Set debt-to-income limits
- Configure risk score classifications
- Define approval confidence thresholds
- Persist settings to JSON file
- Full audit trail of changes

### 2. System Health Monitoring
- Real-time API response times
- CPU/Memory/Disk usage
- Database connection status
- System uptime tracking
- Color-coded status indicators

### 3. Database Statistics
- Total application count
- Decision breakdown (approved/rejected/pending)
- Approval rate calculation
- Database size reporting
- Average processing time
- Visual breakdown chart

### 4. Audit Log Viewer
- Filter by action type
- Search by username
- Sort by timestamp
- Download as CSV
- Color-coded entry types

### 5. User Management
- View all users and roles
- Create new users with role assignment
- Update existing user roles
- Activate/deactivate accounts
- Self-protection (can't modify own account)

### 6. Authentication & Authorization
- SHA-256 password hashing
- 30-minute session timeout
- Role-based access control
- Feature-level permissions
- Automatic session expiration warnings

## Troubleshooting

### "Access Denied" Error
- Check your user role has permission for this feature
- Role hierarchy: Admin > Manager > Analyst > Viewer
- Refer to "Understanding Access Levels" above

### Configuration Not Saving
- Verify `config/` directory exists
- Check disk space availability
- Ensure write permissions to directory
- Check logs for error messages

### Login Failed
- Verify username (case-sensitive)
- Check password (case-sensitive)
- Try default accounts first
- Check if account is active

### Session Timeout
- Default timeout is 30 minutes of inactivity
- You'll get a warning at 5 minutes remaining
- Simply login again to continue
- Warning appears at top of page

### Can't See Features
- Make sure you're logged in
- Check your user role
- Refer to role permissions table above
- Contact admin if you need higher access

## Configuration Deep Dive

### Default Risk Thresholds

```json
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

### Risk Score Range
- 0-30: Low Risk (needs 0.85 confidence)
- 30-50: Medium Risk (needs 0.75 confidence)
- 50-70: High Risk (needs 0.65 confidence)
- 70-100: Very High Risk (needs 0.50 confidence)

## Testing

Run the test suite to verify functionality:

```bash
python test_admin_page.py
```

Expected output: 35 tests pass with 0 failures

## Next Steps

1. **Customize Thresholds**: Update risk thresholds for your organization
2. **Create Users**: Add team members with appropriate roles
3. **Monitor System**: Set up regular health checks
4. **Review Logs**: Regularly audit admin actions for compliance
5. **Backup Configuration**: Save risk_thresholds.json regularly

## Support & Documentation

- Full documentation: `ADMIN_PAGE_DOCUMENTATION.md`
- API reference: See end of documentation file
- Examples: Default user accounts in code
- Tests: `test_admin_page.py` for validation

## Key Shortcuts

| Action | Shortcut |
|--------|----------|
| Save Configuration | Ctrl+S (custom button) |
| Download Logs | Click "📥 Download Logs as CSV" |
| Reset to Defaults | Click "↺ Reset to Defaults" |
| Logout | Click "🚪 Logout" in top right |

## Tips & Tricks

1. **Bulk Export**: Use CSV download for bulk log analysis
2. **Quick Stats**: Dashboard shows recent actions at a glance
3. **Filter Logs**: Use multiple filters for precise queries
4. **Role Hierarchy**: Remember admin > manager > analyst > viewer
5. **Auto-Save**: Configuration changes save immediately to disk
6. **Session Security**: Active sessions expire automatically
7. **Audit Trail**: Every action is logged with timestamp and user
8. **Reset Option**: One-click reset to defaults if needed

## Common Use Cases

### Use Case 1: Quarterly Risk Review
1. Login as admin
2. Go to Risk Configuration
3. Document current settings
4. Review recent market conditions
5. Adjust thresholds accordingly
6. Save and document change

### Use Case 2: User Onboarding
1. Login as admin
2. Go to User Management > Create User
3. Enter new user details
4. Assign appropriate role
5. Share credentials securely
6. Verify access in audit logs

### Use Case 3: Compliance Audit
1. Login as analyst
2. Go to Audit Logs
3. Set date range filters
4. Download logs as CSV
5. Export for external auditors
6. Review with compliance team

### Use Case 4: System Monitoring
1. Login as manager daily
2. Check System Health status
3. Review Database Stats
4. Monitor trends over time
5. Alert if metrics decline

## Performance Notes

- Configuration loads instantly from JSON
- Logs display up to 100 entries (configurable)
- Database stats are cached for performance
- UI is responsive with no delays

## Security Reminders

1. **Never share passwords** - Each user gets unique credentials
2. **Change default passwords** - Update after first login
3. **Review logs regularly** - Monitor for suspicious activity
4. **Use strong passwords** - Minimum 8 characters recommended
5. **Logout when done** - Click "🚪 Logout" button
6. **Session timeout** - Automatic expiration after 30 minutes
7. **Audit trail** - All actions logged for compliance
