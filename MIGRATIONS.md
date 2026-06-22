# Database Migrations Guide

## Overview

The database module (`db.py`) includes an automated migration system that manages schema versioning and evolution. Migrations are applied automatically when the database is initialized.

## Current Schema

### Version 1 (Current)

#### Tables

**applications**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT): Unique application identifier
- `job_title` (TEXT NOT NULL): Job position title
- `company_name` (TEXT NOT NULL): Company name
- `application_url` (TEXT): URL to job posting
- `status` (TEXT): Application status (applied, interview, rejected, offer, etc.)
- `decision_reason` (TEXT): Reason for applying or rejecting
- `analysis_summary` (TEXT): AI analysis summary
- `salary_range` (TEXT): Salary information
- `location` (TEXT): Job location
- `match_score` (REAL): Matching score (0.0-1.0)
- `requirements_met` (TEXT): JSON string of met requirements
- `strengths` (TEXT): JSON string of application strengths
- `weaknesses` (TEXT): JSON string of application weaknesses
- `next_steps` (TEXT): Next actions required
- `notes` (TEXT): Additional notes
- `created_at` (TEXT): Creation timestamp (ISO format)
- `updated_at` (TEXT): Last update timestamp (ISO format)

#### Indexes

- `idx_applications_company`: ON `company_name`
- `idx_applications_status`: ON `status`
- `idx_applications_created_at`: ON `created_at DESC`

#### Metadata Table

**_metadata**
- `key` (TEXT PRIMARY KEY): Metadata key
- `value` (TEXT): Metadata value

Stores:
- `schema_version`: Current schema version number

## Migration Process

### Automatic Migration

Migrations run automatically when `Database` is initialized:

```python
from db import Database

# Automatically runs any pending migrations
db = Database()

# Check schema version
stats = db.get_statistics()
```

### How It Works

1. **Version Check**: On initialization, the database checks `_metadata` table for current schema version
2. **Version Comparison**: Current version is compared against `Database.SCHEMA_VERSION`
3. **Migration Execution**: If versions differ, migrations are run sequentially
4. **Version Update**: After migration, schema version is updated in metadata

### Code Flow

```python
def _initialize_db(self):
    """Initialize database with schema and migrations."""
    with self.pool.get_connection(write=True) as conn:
        # Create metadata table
        conn.execute("CREATE TABLE IF NOT EXISTS _metadata ...")

        # Check current version
        cursor = conn.execute(
            "SELECT value FROM _metadata WHERE key = 'schema_version'"
        )
        current_version = int(row[0]) if row else 0

        # Run migrations if needed
        if current_version < self.SCHEMA_VERSION:
            self._run_migrations(conn, current_version)
            # Update version
            conn.execute(
                "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
                ("schema_version", str(self.SCHEMA_VERSION))
            )
            conn.commit()
```

## Adding New Migrations

### Step 1: Update Schema Version

```python
class Database:
    SCHEMA_VERSION = 2  # Increment version
```

### Step 2: Create Migration Method

```python
def _migrate_v2(self, conn: sqlite3.Connection):
    """Migration to version 2: Add new column."""
    conn.execute("""
        ALTER TABLE applications
        ADD COLUMN interview_feedback TEXT
    """)

    conn.execute("""
        CREATE INDEX idx_applications_interview_feedback
        ON applications(interview_feedback)
    """)

    conn.commit()
    logger.info("Migration v2 completed: Added interview_feedback column")
```

### Step 3: Update Migration Runner

```python
def _run_migrations(self, conn: sqlite3.Connection, from_version: int):
    """Run database migrations."""
    if from_version < 1:
        self._migrate_v1(conn)
    if from_version < 2:
        self._migrate_v2(conn)
```

## Common Migration Patterns

### Adding a Column

```python
def _migrate_v2(self, conn: sqlite3.Connection):
    """Add column with default value."""
    conn.execute("""
        ALTER TABLE applications
        ADD COLUMN new_field TEXT DEFAULT 'default_value'
    """)
    conn.commit()
```

### Adding an Index

```python
def _migrate_v2(self, conn: sqlite3.Connection):
    """Add performance index."""
    conn.execute("""
        CREATE INDEX idx_applications_new_field
        ON applications(new_field)
    """)
    conn.commit()
```

### Modifying Data

```python
def _migrate_v2(self, conn: sqlite3.Connection):
    """Migrate existing data."""
    # Update existing records
    conn.execute("""
        UPDATE applications
        SET new_field = 'converted_value'
        WHERE condition = true
    """)
    conn.commit()
```

### Creating New Table

```python
def _migrate_v2(self, conn: sqlite3.Connection):
    """Create new table."""
    conn.execute("""
        CREATE TABLE interview_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            content TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    """)

    conn.execute("""
        CREATE INDEX idx_interview_notes_application
        ON interview_notes(application_id)
    """)

    conn.commit()
```

## Migration Best Practices

### 1. Backwards Compatibility

- Always use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`
- Don't remove columns; mark as deprecated or add nullable columns
- Support multiple schema versions simultaneously if possible

### 2. Testing

```python
def test_migration():
    """Test migration with fresh database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create v0 database
        db1 = Database(tmpdir)
        db1.create_application(ApplicationRecord(...))
        db1.close()

        # Reopen with new schema - triggers migration
        db2 = Database(tmpdir)
        apps = db2.list_applications()
        assert len(apps) == 1  # Existing data preserved
```

### 3. Large Data Migrations

For migrations that modify large datasets:

```python
def _migrate_v2(self, conn: sqlite3.Connection):
    """Migrate large dataset."""
    # Process in batches
    batch_size = 1000
    offset = 0

    while True:
        cursor = conn.execute(
            "SELECT id FROM applications LIMIT ? OFFSET ?",
            (batch_size, offset)
        )
        rows = cursor.fetchall()

        if not rows:
            break

        ids = [row[0] for row in rows]

        # Update batch
        conn.execute(
            f"UPDATE applications SET field = ? WHERE id IN ({','.join(['?']*len(ids))})",
            [new_value, *ids]
        )
        conn.commit()

        offset += batch_size
```

### 4. Error Handling

```python
def _migrate_v2(self, conn: sqlite3.Connection):
    """Migration with error handling."""
    try:
        conn.execute("""ALTER TABLE applications ADD COLUMN new_field TEXT""")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            logger.warning("Column already exists, skipping")
        else:
            raise

    conn.commit()
```

## Checking Migration Status

### Get Schema Version

```python
from db import get_db

db = get_db()
# Schema version is automatically managed during init
# Check by inspecting metadata:
with db.pool.get_connection() as conn:
    cursor = conn.execute(
        "SELECT value FROM _metadata WHERE key = 'schema_version'"
    )
    version = cursor.fetchone()[0]
    print(f"Current schema version: {version}")
```

### Verify Data Integrity

```python
def verify_migration():
    """Verify migration preserved data."""
    db = get_db()

    stats = db.get_statistics()
    print(f"Total records: {stats['total_applications']}")
    print(f"Status distribution: {stats['by_status']}")

    # Check specific data
    apps = db.list_applications(limit=10)
    for app in apps:
        assert app.id is not None
        assert app.job_title  # Required field
        assert app.company_name  # Required field
```

## Exporting Before Migration

For safety, export data before major migrations:

```python
from db import get_db

db = get_db()

# Create backup
db.export_to_json("backup_before_migration.json")

# Proceed with migration (will happen on reopen)
# If issues arise, restore from backup:
# db.import_from_json("backup_before_migration.json")
```

## Troubleshooting

### Schema Version Mismatch

If the schema version doesn't update:

1. Check database file is writable
2. Ensure `_metadata` table exists
3. Verify migration code ran without exceptions
4. Check logs for migration errors

### Failed Migration

If a migration fails during initialization:

1. Check exception logs
2. Database will remain at previous version
3. Fix the migration code
4. Reopen database to retry

### Rollback

Since SQLite doesn't support transactions for schema changes, rollback requires:

1. Restore from backup
2. Or manually revert schema with SQL
3. Update `_metadata` schema_version back to previous

Example:

```sql
-- Revert schema
DELETE FROM _metadata WHERE key = 'schema_version';
INSERT INTO _metadata (key, value) VALUES ('schema_version', '1');
```

## Performance Considerations

### Index Creation

- Indexes added during migration may be time-consuming on large tables
- Consider creating indexes in background for production databases
- Use `PRAGMA synchronous = NORMAL` for faster migration

### Data Migration

- Large data updates should be batched
- Migration time scales with data size
- Communicate migration windows to users

### WAL Mode

Database uses Write-Ahead Logging (WAL) mode for better concurrency:

```python
conn.execute("PRAGMA journal_mode=WAL")
```

This allows reads during writes, beneficial during long migrations.

## Related Topics

- **Import/Export**: See `export_to_json()` and `import_from_json()` in db.py
- **Connection Pool**: Thread-safe connections with automatic serialization
- **Schema**: See database initialization code in `_migrate_v1()`
- **CRUD Operations**: See `create_application()`, `update_application()`, etc.
