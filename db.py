"""
Database initialization and management module.

Provides SQLite connection management, schema definition, CRUD operations,
and database migrations for application history tracking.
"""

import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from threading import Lock

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ApplicationRecord:
    """Data class representing an application decision record."""
    id: Optional[int] = None
    job_title: str = ""
    company_name: str = ""
    application_url: str = ""
    status: str = ""  # applied, interview, rejected, offer, etc.
    decision_reason: str = ""
    analysis_summary: str = ""
    salary_range: Optional[str] = None
    location: Optional[str] = None
    match_score: Optional[float] = None
    requirements_met: Optional[str] = None  # JSON string
    strengths: Optional[str] = None  # JSON string
    weaknesses: Optional[str] = None  # JSON string
    next_steps: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return asdict(self)


class DatabaseConnectionPool:
    """
    Simple connection pool for SQLite database.

    Manages multiple database connections with thread-safe operations.
    SQLite has built-in support for concurrent reads, but writes are serialized.
    """

    def __init__(self, db_path: str, pool_size: int = 5):
        """
        Initialize connection pool.

        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections to maintain in pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self._lock = Lock()
        self._connections: List[sqlite3.Connection] = []
        self._write_lock = Lock()  # Serialize write operations

        # Initialize pool
        for _ in range(pool_size):
            conn = self._create_connection()
            self._connections.append(conn)

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimizations."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Better performance
        conn.execute("PRAGMA foreign_keys=ON")  # Enable foreign key constraints
        return conn

    @contextmanager
    def get_connection(self, write: bool = False):
        """
        Get a connection from the pool.

        Args:
            write: If True, acquire write lock for serialization

        Yields:
            sqlite3.Connection
        """
        if write:
            self._write_lock.acquire()

        try:
            with self._lock:
                if self._connections:
                    conn = self._connections.pop()
                else:
                    conn = self._create_connection()

            try:
                yield conn
            finally:
                with self._lock:
                    if len(self._connections) < self.pool_size:
                        self._connections.append(conn)
                    else:
                        conn.close()
        finally:
            if write:
                self._write_lock.release()

    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._connections:
                conn.close()
            self._connections.clear()


class Database:
    """Main database interface for application history."""

    # Database schema version for migrations
    SCHEMA_VERSION = 1
    DB_FILENAME = "application_history.db"

    def __init__(self, db_dir: Optional[str] = None, pool_size: int = 5):
        """
        Initialize database.

        Args:
            db_dir: Directory for database file (defaults to current directory)
            pool_size: Number of connections in pool
        """
        if db_dir is None:
            db_dir = str(Path.cwd())

        self.db_path = str(Path(db_dir) / self.DB_FILENAME)
        self.pool = DatabaseConnectionPool(self.db_path, pool_size)

        # Initialize database
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database with schema and migrations."""
        with self.pool.get_connection(write=True) as conn:
            # Create metadata table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Check schema version
            cursor = conn.execute(
                "SELECT value FROM _metadata WHERE key = 'schema_version'"
            )
            row = cursor.fetchone()
            current_version = int(row[0]) if row else 0

            # Run migrations if needed
            if current_version < self.SCHEMA_VERSION:
                self._run_migrations(conn, current_version)
                conn.execute(
                    "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
                    ("schema_version", str(self.SCHEMA_VERSION))
                )
                conn.commit()
                logger.info(f"Database migrated to schema version {self.SCHEMA_VERSION}")

    def _run_migrations(self, conn: sqlite3.Connection, from_version: int):
        """
        Run database migrations.

        Args:
            conn: Database connection
            from_version: Current schema version
        """
        if from_version < 1:
            self._migrate_v1(conn)

    def _migrate_v1(self, conn: sqlite3.Connection):
        """Migration to version 1: Create initial schema."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                application_url TEXT,
                status TEXT DEFAULT 'applied',
                decision_reason TEXT,
                analysis_summary TEXT,
                salary_range TEXT,
                location TEXT,
                match_score REAL,
                requirements_met TEXT,
                strengths TEXT,
                weaknesses TEXT,
                next_steps TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create indexes for common queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_applications_company
            ON applications(company_name)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_applications_status
            ON applications(status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_applications_created_at
            ON applications(created_at DESC)
        """)

        conn.commit()
        logger.info("Migration v1 completed: Created applications table and indexes")

    def create_application(self, record: ApplicationRecord) -> int:
        """
        Create a new application record.

        Args:
            record: ApplicationRecord instance

        Returns:
            ID of created record

        Raises:
            ValueError: If required fields are missing
        """
        if not record.job_title or not record.company_name:
            raise ValueError("job_title and company_name are required")

        now = datetime.now().isoformat()
        record.created_at = now
        record.updated_at = now

        with self.pool.get_connection(write=True) as conn:
            cursor = conn.execute("""
                INSERT INTO applications (
                    job_title, company_name, application_url, status,
                    decision_reason, analysis_summary, salary_range,
                    location, match_score, requirements_met, strengths,
                    weaknesses, next_steps, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.job_title, record.company_name, record.application_url,
                record.status, record.decision_reason, record.analysis_summary,
                record.salary_range, record.location, record.match_score,
                record.requirements_met, record.strengths, record.weaknesses,
                record.next_steps, record.notes, record.created_at, record.updated_at
            ))
            conn.commit()

            app_id = cursor.lastrowid
            logger.info(f"Created application record {app_id}: {record.company_name} - {record.job_title}")
            return app_id

    def get_application(self, app_id: int) -> Optional[ApplicationRecord]:
        """
        Retrieve a single application record by ID.

        Args:
            app_id: Application record ID

        Returns:
            ApplicationRecord or None if not found
        """
        with self.pool.get_connection(write=False) as conn:
            cursor = conn.execute(
                "SELECT * FROM applications WHERE id = ?", (app_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_record(row)

    def update_application(self, record: ApplicationRecord) -> bool:
        """
        Update an existing application record.

        Args:
            record: ApplicationRecord with updated data (must have id)

        Returns:
            True if update successful, False if record not found

        Raises:
            ValueError: If record.id is not set
        """
        if record.id is None:
            raise ValueError("ApplicationRecord.id must be set for updates")

        record.updated_at = datetime.now().isoformat()

        with self.pool.get_connection(write=True) as conn:
            cursor = conn.execute("""
                UPDATE applications SET
                    job_title = ?, company_name = ?, application_url = ?,
                    status = ?, decision_reason = ?, analysis_summary = ?,
                    salary_range = ?, location = ?, match_score = ?,
                    requirements_met = ?, strengths = ?, weaknesses = ?,
                    next_steps = ?, notes = ?, updated_at = ?
                WHERE id = ?
            """, (
                record.job_title, record.company_name, record.application_url,
                record.status, record.decision_reason, record.analysis_summary,
                record.salary_range, record.location, record.match_score,
                record.requirements_met, record.strengths, record.weaknesses,
                record.next_steps, record.notes, record.updated_at, record.id
            ))
            conn.commit()

            if cursor.rowcount == 0:
                logger.warning(f"No application found with id {record.id}")
                return False

            logger.info(f"Updated application record {record.id}")
            return True

    def list_applications(
        self,
        status: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC"
    ) -> List[ApplicationRecord]:
        """
        List applications with optional filtering.

        Args:
            status: Filter by status (e.g., 'applied', 'interview', 'rejected')
            company: Filter by company name (partial match)
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: SQL ORDER BY clause

        Returns:
            List of ApplicationRecord instances
        """
        query = "SELECT * FROM applications WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if company:
            query += " AND company_name LIKE ?"
            params.append(f"%{company}%")

        query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.pool.get_connection(write=False) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_record(row) for row in rows]

    def delete_application(self, app_id: int) -> bool:
        """
        Delete an application record.

        Args:
            app_id: Application record ID

        Returns:
            True if deletion successful, False if record not found
        """
        with self.pool.get_connection(write=True) as conn:
            cursor = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
            conn.commit()

            if cursor.rowcount == 0:
                logger.warning(f"No application found with id {app_id}")
                return False

            logger.info(f"Deleted application record {app_id}")
            return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        with self.pool.get_connection(write=False) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM applications")
            total_count = cursor.fetchone()[0]

            cursor = conn.execute("""
                SELECT status, COUNT(*) as count FROM applications
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor = conn.execute("""
                SELECT AVG(match_score) FROM applications
                WHERE match_score IS NOT NULL
            """)
            avg_match = cursor.fetchone()[0]

            return {
                "total_applications": total_count,
                "by_status": status_counts,
                "average_match_score": avg_match
            }

    def export_to_json(self, filepath: str) -> int:
        """
        Export all applications to JSON file.

        Args:
            filepath: Path to output JSON file

        Returns:
            Number of records exported
        """
        records = self.list_applications(limit=10000)

        with open(filepath, 'w') as f:
            json.dump(
                [record.to_dict() for record in records],
                f,
                indent=2
            )

        logger.info(f"Exported {len(records)} records to {filepath}")
        return len(records)

    def import_from_json(self, filepath: str) -> int:
        """
        Import applications from JSON file.

        Args:
            filepath: Path to input JSON file

        Returns:
            Number of records imported
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        count = 0
        for item in data:
            # Skip id, created_at, updated_at - they'll be regenerated
            item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)

            record = ApplicationRecord(**item)
            self.create_application(record)
            count += 1

        logger.info(f"Imported {count} records from {filepath}")
        return count

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ApplicationRecord:
        """Convert database row to ApplicationRecord."""
        return ApplicationRecord(
            id=row['id'],
            job_title=row['job_title'],
            company_name=row['company_name'],
            application_url=row['application_url'],
            status=row['status'],
            decision_reason=row['decision_reason'],
            analysis_summary=row['analysis_summary'],
            salary_range=row['salary_range'],
            location=row['location'],
            match_score=row['match_score'],
            requirements_met=row['requirements_met'],
            strengths=row['strengths'],
            weaknesses=row['weaknesses'],
            next_steps=row['next_steps'],
            notes=row['notes'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def close(self):
        """Close all database connections."""
        self.pool.close_all()
        logger.info("Database connections closed")


# Singleton instance
_db_instance: Optional[Database] = None


def get_db(db_dir: Optional[str] = None) -> Database:
    """
    Get or create database instance (singleton pattern).

    Args:
        db_dir: Directory for database file

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_dir)
    return _db_instance


def init_db(db_dir: Optional[str] = None) -> Database:
    """
    Initialize database (alias for get_db).

    Args:
        db_dir: Directory for database file

    Returns:
        Database instance
    """
    return get_db(db_dir)
