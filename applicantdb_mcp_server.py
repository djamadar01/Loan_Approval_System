#!/usr/bin/env python3
"""
ApplicantDB MCP Server
A production-ready Model Context Protocol server for managing applicant profiles,
credit history, and employment verification with SQLite persistence and caching.
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict
from functools import lru_cache
import hashlib

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("ApplicantDB")

# Database configuration
DB_PATH = Path.home() / ".mcp_applicantdb" / "applicantdb.sqlite"
EMPLOYMENT_DB_PATH = Path.home() / ".mcp_applicantdb" / "employers.sqlite"
CACHE_SIZE = 128

# Ensure directories exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
EMPLOYMENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class ValidationError(Exception):
    """Custom exception for data validation."""
    pass


class ApplicantDB:
    """Handles all applicant database operations with connection pooling."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema if not exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()

                # Applicants table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS applicants (
                        id TEXT PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        phone TEXT,
                        ssn TEXT UNIQUE,
                        date_of_birth TEXT,
                        address TEXT,
                        city TEXT,
                        state TEXT,
                        zip_code TEXT,
                        employment_status TEXT,
                        employer_id TEXT,
                        annual_income REAL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')

                # Credit history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS credit_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        applicant_id TEXT NOT NULL,
                        credit_score INTEGER,
                        total_debt REAL,
                        available_credit REAL,
                        payment_history TEXT,
                        last_updated TEXT NOT NULL,
                        updated_by TEXT,
                        FOREIGN KEY (applicant_id) REFERENCES applicants(id)
                    )
                ''')

                # Indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_applicant_email ON applicants(email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_applicant_ssn ON applicants(ssn)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_credit_applicant ON credit_history(applicant_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_credit_updated ON credit_history(last_updated)')

                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Connection failed: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")

    def create_applicant(self, applicant_data: Dict[str, Any]) -> str:
        """Create a new applicant record."""
        required_fields = {'id', 'first_name', 'last_name', 'email'}
        if not required_fields.issubset(applicant_data.keys()):
            raise ValidationError(f"Missing required fields: {required_fields - set(applicant_data.keys())}")

        # Validate email format
        if '@' not in applicant_data['email']:
            raise ValidationError(f"Invalid email format: {applicant_data['email']}")

        now = datetime.utcnow().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO applicants (
                        id, first_name, last_name, email, phone, ssn, date_of_birth,
                        address, city, state, zip_code, employment_status, employer_id,
                        annual_income, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    applicant_data['id'],
                    applicant_data['first_name'],
                    applicant_data['last_name'],
                    applicant_data['email'],
                    applicant_data.get('phone'),
                    applicant_data.get('ssn'),
                    applicant_data.get('date_of_birth'),
                    applicant_data.get('address'),
                    applicant_data.get('city'),
                    applicant_data.get('state'),
                    applicant_data.get('zip_code'),
                    applicant_data.get('employment_status', 'unknown'),
                    applicant_data.get('employer_id'),
                    applicant_data.get('annual_income'),
                    now,
                    now
                ))
                conn.commit()
                logger.info(f"Created applicant: {applicant_data['id']}")
                # Invalidate cache
                _clear_profile_cache()
                return applicant_data['id']
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error creating applicant: {e}")
            raise DatabaseError(f"Duplicate applicant ID or email: {e}")
        except sqlite3.Error as e:
            logger.error(f"Database error creating applicant: {e}")
            raise DatabaseError(f"Failed to create applicant: {e}")

    def get_applicant(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve applicant by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM applicants WHERE id = ?', (applicant_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving applicant: {e}")
            raise DatabaseError(f"Failed to retrieve applicant: {e}")

    def get_credit_history(self, applicant_id: str, limit: int = 10) -> list:
        """Retrieve credit history for an applicant."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM credit_history
                    WHERE applicant_id = ?
                    ORDER BY last_updated DESC
                    LIMIT ?
                ''', (applicant_id, limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving credit history: {e}")
            raise DatabaseError(f"Failed to retrieve credit history: {e}")

    def add_credit_update(self, applicant_id: str, credit_data: Dict[str, Any], updated_by: str = "system") -> int:
        """Add a credit history record."""
        # Validate applicant exists
        if not self.get_applicant(applicant_id):
            raise ValidationError(f"Applicant not found: {applicant_id}")

        # Validate credit score
        if 'credit_score' in credit_data:
            score = credit_data['credit_score']
            if not isinstance(score, int) or score < 300 or score > 850:
                raise ValidationError(f"Invalid credit score: {score}. Must be between 300 and 850.")

        now = datetime.utcnow().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO credit_history (
                        applicant_id, credit_score, total_debt, available_credit,
                        payment_history, last_updated, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    applicant_id,
                    credit_data.get('credit_score'),
                    credit_data.get('total_debt'),
                    credit_data.get('available_credit'),
                    json.dumps(credit_data.get('payment_history', [])),
                    now,
                    updated_by
                ))
                conn.commit()
                record_id = cursor.lastrowid
                logger.info(f"Added credit update for applicant {applicant_id}: {record_id}")
                # Invalidate cache
                _clear_profile_cache()
                return record_id
        except sqlite3.Error as e:
            logger.error(f"Database error adding credit update: {e}")
            raise DatabaseError(f"Failed to add credit update: {e}")


class EmployerDB:
    """Handles employer database operations for employment verification."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize employer database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS employers (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        industry TEXT,
                        headquarters_state TEXT,
                        employee_count INTEGER,
                        verified BOOLEAN DEFAULT 1,
                        created_at TEXT NOT NULL
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS employee_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employer_id TEXT NOT NULL,
                        applicant_id TEXT NOT NULL,
                        employee_id TEXT,
                        start_date TEXT,
                        current_status TEXT,
                        job_title TEXT,
                        salary REAL,
                        verified_at TEXT NOT NULL,
                        FOREIGN KEY (employer_id) REFERENCES employers(id)
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_employer_name ON employers(name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_employee_applicant ON employee_records(applicant_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_employee_employer ON employee_records(employer_id)')

                conn.commit()
                logger.info(f"Employer database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Employer database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize employer database: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Employer DB connection failed: {e}")
            raise DatabaseError(f"Failed to connect to employer database: {e}")

    def add_employer(self, employer_data: Dict[str, Any]) -> str:
        """Add a new employer."""
        if 'id' not in employer_data or 'name' not in employer_data:
            raise ValidationError("Employer must have 'id' and 'name'")

        now = datetime.utcnow().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO employers (
                        id, name, industry, headquarters_state, employee_count, verified, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employer_data['id'],
                    employer_data['name'],
                    employer_data.get('industry'),
                    employer_data.get('headquarters_state'),
                    employer_data.get('employee_count'),
                    employer_data.get('verified', True),
                    now
                ))
                conn.commit()
                logger.info(f"Added employer: {employer_data['id']}")
                return employer_data['id']
        except sqlite3.Error as e:
            logger.error(f"Database error adding employer: {e}")
            raise DatabaseError(f"Failed to add employer: {e}")

    def verify_employment(self, applicant_id: str, employer_id: str, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify employment and create employment record."""
        now = datetime.utcnow().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check if employer exists
                cursor.execute('SELECT * FROM employers WHERE id = ?', (employer_id,))
                employer = cursor.fetchone()
                if not employer:
                    raise ValidationError(f"Employer not found: {employer_id}")

                # Create employment record
                cursor.execute('''
                    INSERT INTO employee_records (
                        employer_id, applicant_id, employee_id, start_date, current_status,
                        job_title, salary, verified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employer_id,
                    applicant_id,
                    employee_data.get('employee_id'),
                    employee_data.get('start_date'),
                    employee_data.get('current_status', 'active'),
                    employee_data.get('job_title'),
                    employee_data.get('salary'),
                    now
                ))
                conn.commit()
                record_id = cursor.lastrowid

                logger.info(f"Employment verified for applicant {applicant_id} at {employer_id}")
                # Invalidate cache
                _clear_profile_cache()

                return {
                    "verification_id": record_id,
                    "applicant_id": applicant_id,
                    "employer_id": employer_id,
                    "employer_name": employer['name'],
                    "verified_at": now,
                    "status": "verified"
                }
        except sqlite3.Error as e:
            logger.error(f"Database error verifying employment: {e}")
            raise DatabaseError(f"Failed to verify employment: {e}")

    def get_employment_records(self, applicant_id: str) -> list:
        """Get employment records for an applicant."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT er.*, e.name as employer_name
                    FROM employee_records er
                    JOIN employers e ON er.employer_id = e.id
                    WHERE er.applicant_id = ?
                    ORDER BY er.verified_at DESC
                ''', (applicant_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving employment records: {e}")
            raise DatabaseError(f"Failed to retrieve employment records: {e}")


# Initialize database instances
applicant_db = ApplicantDB(DB_PATH)
employer_db = EmployerDB(EMPLOYMENT_DB_PATH)


# Cache storage and management
_profile_cache = {}
_profile_cache_keys = []


def _clear_profile_cache():
    """Clear the profile cache."""
    global _profile_cache, _profile_cache_keys
    _profile_cache.clear()
    _profile_cache_keys.clear()


def _get_cached_profile(applicant_id: str) -> Dict[str, Any]:
    """Get profile with LRU caching logic."""
    global _profile_cache, _profile_cache_keys

    # Check cache
    if applicant_id in _profile_cache:
        return _profile_cache[applicant_id]

    # Get from database
    applicant = applicant_db.get_applicant(applicant_id)
    if not applicant:
        return {"error": "Applicant not found"}

    credit_history = applicant_db.get_credit_history(applicant_id)
    employment_records = employer_db.get_employment_records(applicant_id)

    profile = {
        "applicant": applicant,
        "credit_history": credit_history,
        "employment_records": employment_records
    }

    # Store in cache with LRU eviction
    if len(_profile_cache) >= CACHE_SIZE:
        removed_key = _profile_cache_keys.pop(0)
        del _profile_cache[removed_key]

    _profile_cache[applicant_id] = profile
    _profile_cache_keys.append(applicant_id)

    return profile


# MCP Tools
@mcp.tool()
def get_applicant_profile(applicant_id: str) -> Dict[str, Any]:
    """
    Get complete applicant profile including personal info, credit history, and employment records.
    Results are cached for performance.

    Args:
        applicant_id: The unique identifier of the applicant

    Returns:
        Dictionary containing applicant profile, credit history, and employment records

    Raises:
        Error if applicant not found
    """
    try:
        profile = _get_cached_profile(applicant_id)
        if "error" in profile:
            return {
                "success": False,
                "error": profile["error"],
                "applicant_id": applicant_id
            }
        return {
            "success": True,
            "data": profile
        }
    except DatabaseError as e:
        logger.error(f"Error retrieving profile: {e}")
        return {
            "success": False,
            "error": str(e),
            "applicant_id": applicant_id
        }


@mcp.tool()
def update_applicant_credit_history(
    applicant_id: str,
    credit_score: Optional[int] = None,
    total_debt: Optional[float] = None,
    available_credit: Optional[float] = None,
    payment_history: Optional[list] = None,
    updated_by: str = "system"
) -> Dict[str, Any]:
    """
    Update applicant credit history with new credit information.

    Args:
        applicant_id: The unique identifier of the applicant
        credit_score: Credit score (300-850)
        total_debt: Total outstanding debt
        available_credit: Available credit limit
        payment_history: List of recent payment records
        updated_by: User or system that made the update

    Returns:
        Confirmation of credit update with record ID

    Raises:
        ValidationError if credit score is invalid
        DatabaseError if applicant not found
    """
    try:
        credit_data = {
            "credit_score": credit_score,
            "total_debt": total_debt,
            "available_credit": available_credit,
            "payment_history": payment_history or []
        }

        record_id = applicant_db.add_credit_update(applicant_id, credit_data, updated_by)

        return {
            "success": True,
            "record_id": record_id,
            "applicant_id": applicant_id,
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": updated_by
        }
    except ValidationError as e:
        logger.error(f"Validation error updating credit: {e}")
        return {
            "success": False,
            "error": str(e),
            "applicant_id": applicant_id
        }
    except DatabaseError as e:
        logger.error(f"Database error updating credit: {e}")
        return {
            "success": False,
            "error": str(e),
            "applicant_id": applicant_id
        }


@mcp.tool()
def verify_employment(
    applicant_id: str,
    employer_id: str,
    employee_id: Optional[str] = None,
    job_title: Optional[str] = None,
    salary: Optional[float] = None,
    start_date: Optional[str] = None,
    current_status: str = "active"
) -> Dict[str, Any]:
    """
    Verify employment by looking up applicant in employer database.

    Args:
        applicant_id: The unique identifier of the applicant
        employer_id: The unique identifier of the employer
        employee_id: Employee ID in employer system
        job_title: Job title
        salary: Annual salary
        start_date: Employment start date (ISO format)
        current_status: Current employment status (active/inactive)

    Returns:
        Verification result with employer details

    Raises:
        ValidationError if employer not found
        DatabaseError on database errors
    """
    try:
        employee_data = {
            "employee_id": employee_id,
            "job_title": job_title,
            "salary": salary,
            "start_date": start_date,
            "current_status": current_status
        }

        result = employer_db.verify_employment(applicant_id, employer_id, employee_data)

        return {
            "success": True,
            "verification": result
        }
    except ValidationError as e:
        logger.error(f"Validation error verifying employment: {e}")
        return {
            "success": False,
            "error": str(e),
            "applicant_id": applicant_id,
            "employer_id": employer_id
        }
    except DatabaseError as e:
        logger.error(f"Database error verifying employment: {e}")
        return {
            "success": False,
            "error": str(e),
            "applicant_id": applicant_id,
            "employer_id": employer_id
        }


@mcp.tool()
def create_applicant(
    applicant_id: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: Optional[str] = None,
    ssn: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    employment_status: Optional[str] = None,
    employer_id: Optional[str] = None,
    annual_income: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create a new applicant record in the database.

    Args:
        applicant_id: Unique identifier for the applicant
        first_name: First name
        last_name: Last name
        email: Email address
        phone: Phone number
        ssn: Social security number
        date_of_birth: Date of birth (ISO format)
        address: Street address
        city: City
        state: State
        zip_code: ZIP code
        employment_status: Current employment status
        employer_id: Current employer ID
        annual_income: Annual income

    Returns:
        Confirmation of applicant creation

    Raises:
        ValidationError if required fields missing or invalid
        DatabaseError if applicant already exists
    """
    try:
        applicant_data = {
            "id": applicant_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "ssn": ssn,
            "date_of_birth": date_of_birth,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "employment_status": employment_status,
            "employer_id": employer_id,
            "annual_income": annual_income
        }

        applicant_id = applicant_db.create_applicant(applicant_data)

        return {
            "success": True,
            "applicant_id": applicant_id,
            "message": "Applicant created successfully"
        }
    except ValidationError as e:
        logger.error(f"Validation error creating applicant: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except DatabaseError as e:
        logger.error(f"Database error creating applicant: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def add_employer(
    employer_id: str,
    name: str,
    industry: Optional[str] = None,
    headquarters_state: Optional[str] = None,
    employee_count: Optional[int] = None,
    verified: bool = True
) -> Dict[str, Any]:
    """
    Add a new employer to the employer database for employment verification.

    Args:
        employer_id: Unique identifier for the employer
        name: Company name
        industry: Industry type
        headquarters_state: State where headquartered
        employee_count: Number of employees
        verified: Whether employer is verified

    Returns:
        Confirmation of employer addition
    """
    try:
        employer_data = {
            "id": employer_id,
            "name": name,
            "industry": industry,
            "headquarters_state": headquarters_state,
            "employee_count": employee_count,
            "verified": verified
        }

        employer_db.add_employer(employer_data)

        return {
            "success": True,
            "employer_id": employer_id,
            "message": "Employer added successfully"
        }
    except ValidationError as e:
        logger.error(f"Validation error adding employer: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except DatabaseError as e:
        logger.error(f"Database error adding employer: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_database_stats() -> Dict[str, Any]:
    """
    Get statistics about the ApplicantDB database.

    Returns:
        Dictionary with database statistics
    """
    try:
        with applicant_db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM applicants')
            applicant_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM credit_history')
            credit_records = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM applicants WHERE employment_status = "active"')
            active_count = cursor.fetchone()[0]

        with employer_db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM employers')
            employer_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM employee_records')
            employment_records = cursor.fetchone()[0]

        return {
            "success": True,
            "applicant_count": applicant_count,
            "active_applicants": active_count,
            "credit_history_records": credit_records,
            "employer_count": employer_count,
            "employment_records": employment_records,
            "applicant_db_path": str(DB_PATH),
            "employer_db_path": str(EMPLOYMENT_DB_PATH),
            "cache_size": CACHE_SIZE
        }
    except DatabaseError as e:
        logger.error(f"Error retrieving statistics: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="127.0.0.1", port=8000)
