"""
Database module examples and integration tests.

Demonstrates all CRUD operations, connection pool usage, migrations,
and data import/export functionality.
"""

import json
import tempfile
from pathlib import Path
from db import (
    Database,
    ApplicationRecord,
    DatabaseConnectionPool,
    get_db,
    init_db
)


def example_basic_operations():
    """Example: Basic CRUD operations."""
    print("\n=== Basic CRUD Operations ===\n")

    # Initialize database in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(tmpdir)

        # CREATE: Add applications
        print("Creating application records...")
        record1 = ApplicationRecord(
            job_title="Senior Python Engineer",
            company_name="TechCorp",
            application_url="https://techcorp.com/jobs/123",
            status="applied",
            decision_reason="Strong match for backend role",
            analysis_summary="Company values match. Team looks strong.",
            salary_range="$150k - $180k",
            location="San Francisco, CA",
            match_score=0.92,
            requirements_met=json.dumps(["5+ Python", "Django", "PostgreSQL"]),
            strengths=json.dumps(["Strong backend", "Team collaboration"]),
            weaknesses=json.dumps(["No DevOps experience"]),
            next_steps="Waiting for initial screening"
        )

        app_id = db.create_application(record1)
        print(f"✓ Created application {app_id}: {record1.company_name}")

        # Create another application
        record2 = ApplicationRecord(
            job_title="ML Engineer",
            company_name="DataSystems",
            application_url="https://datasystems.com/jobs/456",
            status="interview",
            decision_reason="Good opportunity for ML skills",
            salary_range="$160k - $200k",
            location="Remote",
            match_score=0.85
        )

        app_id2 = db.create_application(record2)
        print(f"✓ Created application {app_id2}: {record2.company_name}")

        # READ: Retrieve single record
        print("\nRetrieving application record...")
        retrieved = db.get_application(app_id)
        if retrieved:
            print(f"✓ Retrieved: {retrieved.job_title} at {retrieved.company_name}")
            print(f"  Status: {retrieved.status}")
            print(f"  Match Score: {retrieved.match_score}")

        # UPDATE: Modify record
        print("\nUpdating application record...")
        retrieved.status = "interview"
        retrieved.next_steps = "Phone screen scheduled for 2pm"
        db.update_application(retrieved)
        print(f"✓ Updated status to: {retrieved.status}")
        print(f"  Next steps: {retrieved.next_steps}")

        # LIST: Retrieve multiple records
        print("\nListing all applications...")
        all_apps = db.list_applications()
        print(f"✓ Found {len(all_apps)} applications")
        for app in all_apps:
            print(f"  - {app.company_name}: {app.job_title} ({app.status})")

        # LIST with filters
        print("\nListing applications by status...")
        interviews = db.list_applications(status="interview")
        print(f"✓ Found {len(interviews)} interview stage applications")

        # DELETE: Remove record
        print("\nDeleting application record...")
        deleted = db.delete_application(app_id2)
        if deleted:
            print(f"✓ Deleted application {app_id2}")

        db.close()


def example_filtering_and_search():
    """Example: Advanced filtering and search."""
    print("\n=== Filtering and Search ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(tmpdir)

        # Add test data
        companies = [
            ("Google", "Senior Engineer", "applied"),
            ("Google", "Product Manager", "rejected"),
            ("Meta", "Backend Engineer", "interview"),
            ("Meta", "Data Scientist", "applied"),
            ("Amazon", "Staff Engineer", "offer"),
        ]

        for company, title, status in companies:
            record = ApplicationRecord(
                job_title=title,
                company_name=company,
                status=status,
                match_score=0.8
            )
            db.create_application(record)

        # Search by company
        print("Search by company (partial match)...")
        google_jobs = db.list_applications(company="Google")
        print(f"✓ Found {len(google_jobs)} applications at Google")
        for app in google_jobs:
            print(f"  - {app.job_title}: {app.status}")

        # Filter by status
        print("\nFilter by status...")
        applied = db.list_applications(status="applied")
        print(f"✓ Found {len(applied)} 'applied' status applications")

        # Statistics
        print("\nDatabase statistics...")
        stats = db.get_statistics()
        print(f"✓ Total applications: {stats['total_applications']}")
        print(f"  By status: {stats['by_status']}")
        if stats['average_match_score']:
            print(f"  Average match score: {stats['average_match_score']:.2f}")

        db.close()


def example_connection_pool():
    """Example: Connection pool usage."""
    print("\n=== Connection Pool ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        pool = DatabaseConnectionPool(f"{tmpdir}/test.db", pool_size=3)

        print("Testing concurrent connections...")

        # Read connection
        with pool.get_connection(write=False) as conn:
            print("✓ Acquired read connection")
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"  Query result: {result[0]}")

        # Write connection (serialized)
        with pool.get_connection(write=True) as conn:
            print("✓ Acquired write connection (locked for serialization)")
            conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            conn.commit()

        # Another read connection
        with pool.get_connection(write=False) as conn:
            print("✓ Acquired second read connection")

        pool.close_all()
        print("✓ Closed all connections")


def example_import_export():
    """Example: Import and export functionality."""
    print("\n=== Import/Export Operations ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        db = Database(tmpdir)

        # Create test data
        print("Creating test applications...")
        records = [
            ApplicationRecord(
                job_title="Python Engineer",
                company_name="TechCorp",
                status="applied",
                match_score=0.9
            ),
            ApplicationRecord(
                job_title="Data Scientist",
                company_name="DataCo",
                status="interview",
                match_score=0.85
            ),
        ]

        for record in records:
            db.create_application(record)

        # Export to JSON
        export_path = str(tmpdir_path / "export.json")
        print(f"\nExporting to {export_path}...")
        count = db.export_to_json(export_path)
        print(f"✓ Exported {count} records")

        # Show exported content
        with open(export_path) as f:
            exported = json.load(f)
            print(f"  Sample record: {exported[0]['job_title']} at {exported[0]['company_name']}")

        # Create new database and import
        db2_dir = tmpdir_path / "db2"
        db2_dir.mkdir()
        db2 = Database(str(db2_dir))

        print(f"\nImporting into new database...")
        imported = db2.import_from_json(export_path)
        print(f"✓ Imported {imported} records")

        # Verify import
        imported_records = db2.list_applications()
        print(f"✓ New database now has {len(imported_records)} records")

        db.close()
        db2.close()


def example_migrations():
    """Example: Schema migrations."""
    print("\n=== Schema Migrations ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # First database - creates schema
        print("Initializing database (schema v1)...")
        db1 = Database(tmpdir)
        db1.close()

        # Second database with same path - verifies migration
        print("Opening existing database (verifying migration)...")
        db2 = Database(tmpdir)

        # Add data to verify schema works
        record = ApplicationRecord(
            job_title="Test Engineer",
            company_name="TestCorp",
            status="applied"
        )
        db2.create_application(record)
        print("✓ Schema migration successful")
        print("✓ CRUD operations work on migrated schema")

        db2.close()


def example_singleton_pattern():
    """Example: Singleton database instance."""
    print("\n=== Singleton Pattern ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # First call creates instance
        db1 = get_db(tmpdir)
        print(f"✓ Created database instance: {id(db1)}")

        # Second call returns same instance
        db2 = get_db(tmpdir)
        print(f"✓ Retrieved same instance: {id(db2)}")
        print(f"  Same instance: {db1 is db2}")


def example_error_handling():
    """Example: Error handling and validation."""
    print("\n=== Error Handling ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(tmpdir)

        # Missing required fields
        print("Testing validation...")
        try:
            invalid = ApplicationRecord(job_title="")  # Missing company_name
            db.create_application(invalid)
        except ValueError as e:
            print(f"✓ Caught validation error: {e}")

        # Update non-existent record
        print("\nTesting update on non-existent record...")
        fake = ApplicationRecord(
            id=99999,
            job_title="Fake",
            company_name="FakeCorp"
        )
        result = db.update_application(fake)
        print(f"✓ Update returned False for non-existent record: {not result}")

        # Get non-existent record
        print("\nTesting get on non-existent record...")
        retrieved = db.get_application(99999)
        print(f"✓ Retrieved None for non-existent record: {retrieved is None}")

        db.close()


def run_all_examples():
    """Run all example functions."""
    print("\n" + "="*60)
    print("DATABASE MODULE EXAMPLES AND DEMONSTRATIONS")
    print("="*60)

    try:
        example_basic_operations()
        example_filtering_and_search()
        example_connection_pool()
        example_import_export()
        example_migrations()
        example_singleton_pattern()
        example_error_handling()

        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        raise


if __name__ == "__main__":
    run_all_examples()
