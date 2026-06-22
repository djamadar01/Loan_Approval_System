# Database Quick Reference

## Initialization

```python
from db import Database, get_db, ApplicationRecord

# Initialize database (auto-migrations)
db = Database()

# Or use singleton pattern
db = get_db()

# With custom directory
db = Database(db_dir="/custom/path")
```

## ApplicationRecord Fields

```python
record = ApplicationRecord(
    # Required
    job_title="Position Title",           # string
    company_name="Company Name",          # string

    # URLs & Locations
    application_url="https://...",        # string
    location="San Francisco, CA",         # string

    # Status & Decisions
    status="applied",                     # string (applied|interview|rejected|offer)
    decision_reason="Why this job",       # string
    analysis_summary="AI analysis",       # string
    next_steps="What's next",             # string

    # Scoring & Assessment
    match_score=0.92,                     # float (0.0-1.0)
    salary_range="$150k-$180k",           # string

    # JSON Fields (store lists/dicts as JSON strings)
    requirements_met='["Python","SQL"]',  # string
    strengths='["Strong team"]',          # string
    weaknesses='["No DevOps"]',           # string

    # Additional
    notes="Extra notes",                  # string
)
```

## CRUD Operations

### CREATE
```python
app_id = db.create_application(record)
```

### READ
```python
app = db.get_application(app_id)
```

### UPDATE
```python
app.status = "interview"
db.update_application(app)
```

### DELETE
```python
db.delete_application(app_id)
```

### LIST
```python
# All records
apps = db.list_applications()

# Filtered
apps = db.list_applications(status="applied")
apps = db.list_applications(company="Tech")

# Paginated
apps = db.list_applications(limit=50, offset=0)

# Custom sort
apps = db.list_applications(order_by="match_score DESC")
```

## Queries

### Count by Status
```python
stats = db.get_statistics()
stats['by_status']  # {'applied': 15, 'interview': 8, ...}
```

### High Match Score Applications
```python
apps = db.list_applications(limit=1000)
high_match = [a for a in apps if a.match_score >= 0.85]
```

### Recent Applications
```python
apps = db.list_applications(order_by="created_at DESC", limit=10)
```

### Find by Partial Company Name
```python
apps = db.list_applications(company="Google")  # Partial match
```

## Import/Export

### Export to JSON
```python
db.export_to_json("backup.json")
```

### Import from JSON
```python
db.import_from_json("backup.json")
```

## Working with JSON Fields

### Store Complex Data
```python
import json

requirements = ["Python 3.8+", "PostgreSQL", "Docker"]
record.requirements_met = json.dumps(requirements)

strengths = {
    "backend": True,
    "team_collaboration": 8,
    "published_papers": 2
}
record.strengths = json.dumps(strengths)
```

### Parse JSON Fields
```python
import json

requirements = json.loads(record.requirements_met)
strengths = json.loads(record.strengths)
```

## Common Patterns

### Check if Application Exists
```python
existing = db.list_applications(company="TechCorp")
if existing:
    print("Already applied to this company")
```

### Update All Records for Company
```python
apps = db.list_applications(company="Google")
for app in apps:
    app.status = "rejected"
    db.update_application(app)
```

### Get Statistics
```python
stats = db.get_statistics()
print(f"Total: {stats['total_applications']}")
print(f"Average score: {stats['average_match_score']}")
```

### Batch Operations
```python
# Create multiple records
for job in job_list:
    app = ApplicationRecord(
        job_title=job['title'],
        company_name=job['company']
    )
    db.create_application(app)
```

## Error Handling

### Validation Error
```python
try:
    record = ApplicationRecord(job_title="")  # Missing company_name
    db.create_application(record)
except ValueError as e:
    print(f"Error: {e}")
```

### Record Not Found
```python
app = db.get_application(99999)
if app is None:
    print("Not found")
```

### Update Non-existent Record
```python
success = db.update_application(record)
if not success:
    print("Record not found")
```

## Connection Management

### Close Database
```python
db.close()
```

### Singleton Pattern
```python
from db import get_db

# First call initializes
db1 = get_db()

# Subsequent calls return same instance
db2 = get_db()
assert db1 is db2  # True
```

## Timestamps

Automatically managed:
```python
record.created_at  # ISO format string
record.updated_at  # ISO format string

# Example: "2025-02-15T14:30:45.123456"
```

## Status Values

Common status values:
- `"applied"` - Initial application sent
- `"interview"` - Interview scheduled
- `"rejected"` - Application rejected
- `"offer"` - Job offer received
- `"accepted"` - Offer accepted
- `"declined"` - Offer declined

## Sorting Options

```python
# By creation date (newest first)
apps = db.list_applications(order_by="created_at DESC")

# By match score (highest first)
apps = db.list_applications(order_by="match_score DESC")

# By company name
apps = db.list_applications(order_by="company_name ASC")

# Multiple fields
apps = db.list_applications(order_by="status ASC, created_at DESC")
```

## Data Export

### JSON Format
```json
{
  "id": 1,
  "job_title": "Senior Engineer",
  "company_name": "TechCorp",
  "status": "applied",
  "match_score": 0.92,
  "created_at": "2025-02-15T14:30:45",
  "updated_at": "2025-02-16T09:15:30"
}
```

### CSV Export
```python
import csv
import json

apps = db.list_applications(limit=1000)

with open('applications.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['company_name', 'job_title', 'status', 'match_score'])
    writer.writeheader()
    for app in apps:
        writer.writerow({
            'company_name': app.company_name,
            'job_title': app.job_title,
            'status': app.status,
            'match_score': app.match_score
        })
```

## Debugging

### Enable Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)
# Now see detailed database operations
```

### Check Database File
```python
from pathlib import Path

db = get_db()
print(f"Database: {db.db_path}")
print(f"Size: {Path(db.db_path).stat().st_size} bytes")
```

### Verify Connection
```python
stats = db.get_statistics()
print(f"Total records: {stats['total_applications']}")
```

## Performance Tips

### Limit Query Results
```python
# Bad: Load all 10,000 records
apps = db.list_applications(limit=10000)

# Good: Paginate
apps = db.list_applications(limit=100, offset=0)
```

### Use Filters Early
```python
# Bad: Filter in code
apps = db.list_applications()
interviews = [a for a in apps if a.status == "interview"]

# Good: Filter in database
interviews = db.list_applications(status="interview")
```

### Batch Large Operations
```python
# Process records in chunks
batch_size = 100
for offset in range(0, 10000, batch_size):
    apps = db.list_applications(limit=batch_size, offset=offset)
    # Process batch
```

## Schema Information

- Database file: `application_history.db`
- Main table: `applications`
- Schema version: 1
- Indexes: company_name, status, created_at

See `MIGRATIONS.md` for schema details.

## Integration Examples

### Flask Endpoint
```python
from flask import Flask
from db import get_db

@app.route('/api/applications')
def get_applications():
    db = get_db()
    apps = db.list_applications()
    return [app.to_dict() for app in apps]
```

### CLI Command
```python
@click.command()
@click.option('--status', help='Filter by status')
def list_apps(status):
    db = get_db()
    apps = db.list_applications(status=status)
    for app in apps:
        print(f"{app.company_name}: {app.job_title}")
```

### Scheduled Task
```python
from db import get_db
from datetime import datetime

def cleanup_old_applications():
    """Remove old rejected applications."""
    db = get_db()
    apps = db.list_applications(status="rejected")
    
    for app in apps:
        if app.created_at < "2024-01-01":
            db.delete_application(app.id)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "db file is locked" | Close all connections, check file permissions |
| "ValueError: job_title required" | Ensure job_title and company_name set |
| "No database found" | Call `Database()` to initialize |
| "Record not found on update" | Verify ID exists before updating |
| "Slow queries" | Add limit, use filters, check indexes |

## Database Location

Default: `./application_history.db` in current directory

Override:
```python
db = Database(db_dir="/path/to/directory")
# Creates: /path/to/directory/application_history.db
```

## Version Info

- Schema version: 1
- Python requirement: 3.7+
- SQLite: Built-in (no install needed)

## Related Docs

- **DB_README.md** - Full documentation
- **MIGRATIONS.md** - Schema evolution guide
- **db_example.py** - Working code examples
