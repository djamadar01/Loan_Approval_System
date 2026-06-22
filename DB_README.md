# Database Module Documentation

## Overview

The `db.py` module provides a complete SQLite database solution for managing job application records. It includes:

- **SQLite Connection Management**: Thread-safe connection pooling with read/write serialization
- **Automated Schema Migrations**: Version-controlled schema evolution
- **Full CRUD Operations**: Create, Read, Update, Delete, List applications
- **Data Import/Export**: JSON serialization for backup and data transfer
- **Performance Optimizations**: Write-Ahead Logging (WAL), indexes, connection pooling
- **Production-Ready**: Logging, error handling, validation

## Quick Start

### Installation

```python
from db import Database, ApplicationRecord

# Initialize database
db = Database()  # Uses default location: ./application_history.db

# Or specify custom directory
db = Database(db_dir="/path/to/db/directory")
```

### Basic Usage

```python
from db import ApplicationRecord, get_db

# Get database instance
db = get_db()

# Create application record
app = ApplicationRecord(
    job_title="Senior Python Engineer",
    company_name="TechCorp",
    application_url="https://techcorp.com/jobs/123",
    status="applied",
    decision_reason="Strong backend team",
    salary_range="$150k - $180k",
    location="San Francisco, CA",
    match_score=0.92
)

app_id = db.create_application(app)
print(f"Created application: {app_id}")

# Retrieve application
retrieved = db.get_application(app_id)
print(f"{retrieved.job_title} at {retrieved.company_name}")

# Update application
retrieved.status = "interview"
retrieved.next_steps = "Phone screening scheduled"
db.update_application(retrieved)

# List applications
all_apps = db.list_applications()
interviews = db.list_applications(status="interview")

# Statistics
stats = db.get_statistics()
print(f"Total applications: {stats['total_applications']}")

# Cleanup
db.close()
```

## Core Components

### ApplicationRecord

Dataclass representing a single application record with all decision data.

**Fields:**
- `id` (int|None): Database record ID (auto-generated)
- `job_title` (str): Position title
- `company_name` (str): Company name
- `application_url` (str): Link to job posting
- `status` (str): Current status (applied, interview, rejected, offer)
- `decision_reason` (str): Why this job matters
- `analysis_summary` (str): AI analysis of fit
- `salary_range` (str): Compensation information
- `location` (str): Job location or remote
- `match_score` (float): 0.0-1.0 matching score
- `requirements_met` (str): JSON string of met requirements
- `strengths` (str): JSON string of application strengths
- `weaknesses` (str): JSON string of concerns
- `next_steps` (str): Planned actions
- `notes` (str): Additional context
- `created_at` (str): ISO format creation timestamp
- `updated_at` (str): ISO format last update timestamp

**Example:**
```python
from db import ApplicationRecord
import json

record = ApplicationRecord(
    job_title="ML Engineer",
    company_name="DataCorp",
    status="interview",
    match_score=0.88,
    requirements_met=json.dumps(["Python", "TensorFlow", "SQL"]),
    strengths=json.dumps(["Strong ML background", "Published research"]),
    weaknesses=json.dumps(["Limited production experience"])
)

# Convert to dictionary
data = record.to_dict()
```

### DatabaseConnectionPool

Thread-safe connection pooling for SQLite database.

**Features:**
- Maintains pool of reusable connections
- Automatic connection creation/cleanup
- Write operation serialization (SQLite limitation)
- Read/write separation
- PRAGMA optimizations (WAL, synchronous, foreign keys)

**Usage:**
```python
from db import DatabaseConnectionPool

pool = DatabaseConnectionPool(db_path="/path/to/db.sqlite", pool_size=5)

# Read connection
with pool.get_connection(write=False) as conn:
    cursor = conn.execute("SELECT * FROM applications")
    rows = cursor.fetchall()

# Write connection (serialized)
with pool.get_connection(write=True) as conn:
    conn.execute("INSERT INTO applications ...")
    conn.commit()

# Cleanup
pool.close_all()
```

### Database

Main database interface providing CRUD operations and management.

## CRUD Operations

### CREATE: create_application()

Create a new application record.

```python
from db import ApplicationRecord, get_db

db = get_db()

record = ApplicationRecord(
    job_title="Senior Engineer",
    company_name="TechCorp",
    application_url="https://techcorp.com/jobs/123",
    status="applied",
    salary_range="$150k-$180k",
    match_score=0.92
)

app_id = db.create_application(record)
print(f"Created: {app_id}")
```

**Parameters:**
- `record` (ApplicationRecord): Record to create

**Returns:**
- `int`: Auto-generated application ID

**Raises:**
- `ValueError`: If `job_title` or `company_name` missing

**Timestamps:**
- Automatically sets `created_at` and `updated_at` to current time

### READ: get_application()

Retrieve a single application by ID.

```python
app = db.get_application(1)
if app:
    print(f"{app.job_title} at {app.company_name}")
else:
    print("Application not found")
```

**Parameters:**
- `app_id` (int): Application ID

**Returns:**
- `ApplicationRecord|None`: Record if found, None otherwise

### UPDATE: update_application()

Update an existing application record.

```python
app = db.get_application(1)
app.status = "interview"
app.next_steps = "Prepare for technical assessment"
success = db.update_application(app)
print(f"Updated: {success}")
```

**Parameters:**
- `record` (ApplicationRecord): Record with ID and updated values

**Returns:**
- `bool`: True if updated, False if not found

**Raises:**
- `ValueError`: If `record.id` is not set

**Timestamps:**
- Automatically updates `updated_at` to current time

### DELETE: delete_application()

Delete an application record.

```python
deleted = db.delete_application(1)
if deleted:
    print("Application deleted")
else:
    print("Application not found")
```

**Parameters:**
- `app_id` (int): Application ID

**Returns:**
- `bool`: True if deleted, False if not found

### LIST: list_applications()

Retrieve multiple applications with optional filtering.

```python
# Get all applications
all_apps = db.list_applications()

# Filter by status
interviews = db.list_applications(status="interview")

# Filter by company (partial match)
google_apps = db.list_applications(company="Google")

# Combined filters
results = db.list_applications(
    status="applied",
    company="Tech",
    limit=50,
    offset=0,
    order_by="created_at DESC"
)
```

**Parameters:**
- `status` (str|None): Filter by status
- `company` (str|None): Filter by company name (partial match)
- `limit` (int): Maximum records (default: 100)
- `offset` (int): Skip records (default: 0)
- `order_by` (str): SQL ORDER BY clause (default: "created_at DESC")

**Returns:**
- `List[ApplicationRecord]`: List of matching records

## Advanced Features

### Statistics

Get database statistics and analytics.

```python
stats = db.get_statistics()
print(f"Total applications: {stats['total_applications']}")
print(f"By status: {stats['by_status']}")
print(f"Average match score: {stats['average_match_score']}")

# Output example:
# Total applications: 47
# By status: {'applied': 15, 'interview': 8, 'rejected': 12, 'offer': 2}
# Average match score: 0.78
```

**Returns:**
- `dict` with keys:
  - `total_applications` (int)
  - `by_status` (dict): Status -> count mapping
  - `average_match_score` (float|None)

### Import/Export

#### Export to JSON

```python
export_count = db.export_to_json("backup.json")
print(f"Exported {export_count} records")
```

**Parameters:**
- `filepath` (str): Output file path

**Returns:**
- `int`: Number of records exported

**Format:**
```json
[
  {
    "id": 1,
    "job_title": "Senior Engineer",
    "company_name": "TechCorp",
    "status": "applied",
    "match_score": 0.92,
    ...
  },
  ...
]
```

#### Import from JSON

```python
import_count = db.import_from_json("backup.json")
print(f"Imported {import_count} records")
```

**Parameters:**
- `filepath` (str): Input file path

**Returns:**
- `int`: Number of records imported

**Notes:**
- Ignores `id`, `created_at`, `updated_at` fields
- Generates new timestamps for imported records
- Useful for data migration and backup restoration

### Migrations

Automatic schema management with version control.

```python
# Migrations run automatically on Database initialization
db = Database()

# Check schema version (in code):
# Database.SCHEMA_VERSION = 1 (current)
```

**Features:**
- Automatic version checking
- Sequential migration application
- Backward compatibility
- Schema verification

See `MIGRATIONS.md` for detailed migration guide.

## Connection Management

### Singleton Pattern

Use `get_db()` for application-wide database access.

```python
from db import get_db, init_db

# Initialize (first call)
db = init_db()

# Or retrieve existing instance
db = get_db()

# Same instance is returned
db1 = get_db()
db2 = get_db()
assert db1 is db2  # True
```

### Resource Cleanup

```python
db = Database()

try:
    # Use database
    apps = db.list_applications()
finally:
    # Always close
    db.close()
```

Or with context manager pattern:

```python
def cleanup_database():
    """Custom cleanup function for application shutdown."""
    try:
        db = get_db()
        db.close()
    except Exception as e:
        logger.error(f"Error closing database: {e}")
```

## Error Handling

### Validation Errors

```python
from db import ApplicationRecord

try:
    record = ApplicationRecord(job_title="")  # Missing company_name
    db.create_application(record)
except ValueError as e:
    print(f"Validation error: {e}")
```

### Update Non-existent Record

```python
record = ApplicationRecord(
    id=99999,  # Non-existent ID
    job_title="Test",
    company_name="Test Corp"
)

success = db.update_application(record)
if not success:
    print("Record not found")
```

### Database Errors

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Errors logged to application logger
# Check logs for database operation details
```

## Performance Considerations

### Indexing

The database includes indexes on:
- `company_name`: For company filtering
- `status`: For status filtering
- `created_at DESC`: For time-ordered queries

### Connection Pooling

```python
# Default pool size: 5 connections
db = Database()

# Custom pool size
db = Database(pool_size=10)
```

### Write-Ahead Logging (WAL)

Database uses WAL mode for better concurrency:
- Allows reads during writes
- Better performance for concurrent access
- Enables connection pooling

### Large Datasets

For querying large tables, use pagination:

```python
page_size = 100
page = 0

while True:
    apps = db.list_applications(
        limit=page_size,
        offset=page * page_size
    )

    if not apps:
        break

    # Process page
    for app in apps:
        print(app.job_title)

    page += 1
```

## Logging

Database operations are logged to the application logger.

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('db')
logger.setLevel(logging.DEBUG)
```

**Log Levels:**
- `INFO`: CRUD operations, migrations
- `WARNING`: Updates on non-existent records
- `ERROR`: Critical database failures

## Common Patterns

### Check if Application Exists

```python
def application_exists(db, job_title: str, company: str) -> bool:
    """Check if application already exists."""
    results = db.list_applications(company=company)
    return any(app.job_title == job_title for app in results)
```

### Batch Updates

```python
def update_status_by_company(db, company: str, new_status: str):
    """Update all applications for a company."""
    apps = db.list_applications(company=company)

    for app in apps:
        app.status = new_status
        db.update_application(app)

    return len(apps)
```

### Find High-Match Applications

```python
def get_promising_applications(db, min_score: float = 0.8):
    """Get applications with high match scores."""
    all_apps = db.list_applications(limit=10000)
    return [app for app in all_apps if app.match_score and app.match_score >= min_score]
```

### Count by Status

```python
stats = db.get_statistics()
applied = stats['by_status'].get('applied', 0)
interviews = stats['by_status'].get('interview', 0)
offers = stats['by_status'].get('offer', 0)

print(f"Applied: {applied}, Interviews: {interviews}, Offers: {offers}")
```

## Files

### Core Implementation
- **db.py**: Main database module (700+ lines)
  - `Database` class: Main interface
  - `ApplicationRecord` dataclass: Data schema
  - `DatabaseConnectionPool` class: Connection management
  - Helper functions: `get_db()`, `init_db()`

### Examples & Tests
- **db_example.py**: Comprehensive examples
  - Basic CRUD operations
  - Filtering and search
  - Connection pooling
  - Import/export
  - Schema migrations
  - Error handling

### Documentation
- **MIGRATIONS.md**: Schema versioning guide
  - Migration process
  - Adding new migrations
  - Best practices
  - Troubleshooting

- **DB_README.md**: This file
  - Quick start
  - API reference
  - Common patterns
  - Performance tips

## Testing

Run example demonstrations:

```bash
python db_example.py
```

Output shows all features working correctly:
```
✓ Created application
✓ Retrieved application
✓ Updated application
✓ Listed applications
✓ Deleted application
✓ Exported to JSON
✓ Imported from JSON
✓ Schema migration successful
```

## Integration

### Flask/FastAPI

```python
from db import get_db, ApplicationRecord

app = FastAPI()

@app.get("/applications")
def list_apps():
    db = get_db()
    apps = db.list_applications()
    return [app.to_dict() for app in apps]

@app.post("/applications")
def create_app(data: dict):
    db = get_db()
    record = ApplicationRecord(**data)
    app_id = db.create_application(record)
    return {"id": app_id}
```

### CLI

```python
import click
from db import get_db

@click.group()
def cli():
    pass

@cli.command()
def list_apps():
    """List all applications."""
    db = get_db()
    apps = db.list_applications()
    for app in apps:
        click.echo(f"{app.company_name}: {app.job_title} ({app.status})")

if __name__ == "__main__":
    cli()
```

### Backup Strategy

```python
import shutil
from pathlib import Path
from db import get_db

def backup_database():
    """Create timestamped database backup."""
    db = get_db()
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"application_history_{timestamp}.db"

    shutil.copy(db.db_path, backup_path)
    return backup_path
```

## Requirements

- Python 3.7+
- SQLite3 (included with Python)
- No external dependencies

## License

Part of the Application Decision System.

## Support

For issues or questions:
1. Check logs at `logging.DEBUG` level
2. Review `MIGRATIONS.md` for schema issues
3. See `db_example.py` for usage patterns
4. Check database file permissions and disk space
