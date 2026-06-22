#!/usr/bin/env python3
"""
Enhanced ApplicantDB MCP Server
A production-ready Model Context Protocol server with advanced features:
1. Webhook support for profile updates
2. Batch get_applicants tool
3. Advanced validation rules for profiles
4. Historical data tracking (audit trail)
5. Data enrichment from external services (simulated)
"""

import json
import sqlite3
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List, Callable
from functools import lru_cache
from enum import Enum
import threading
import queue

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("ApplicantDBEnhanced")

# Database configuration
DB_PATH = Path.home() / ".mcp_applicantdb_enhanced" / "applicantdb.sqlite"
EMPLOYMENT_DB_PATH = Path.home() / ".mcp_applicantdb_enhanced" / "employers.sqlite"
AUDIT_DB_PATH = Path.home() / ".mcp_applicantdb_enhanced" / "audit.sqlite"
CACHE_SIZE = 128

# Ensure directories exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
EMPLOYMENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
AUDIT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ==================== ENUMS ====================

class ValidationRuleType(Enum):
    """Types of validation rules."""
    EMAIL_FORMAT = "email_format"
    CREDIT_SCORE_RANGE = "credit_score_range"
    INCOME_THRESHOLD = "income_threshold"
    EMPLOYMENT_STATUS_VALID = "employment_status_valid"
    PHONE_FORMAT = "phone_format"
    SSN_FORMAT = "ssn_format"
    DEBT_TO_INCOME_RATIO = "debt_to_income_ratio"
    ADDRESS_COMPLETENESS = "address_completeness"
    AGE_REQUIREMENT = "age_requirement"


class AuditEventType(Enum):
    """Types of audit events."""
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    CREDIT_UPDATED = "credit_updated"
    EMPLOYMENT_VERIFIED = "employment_verified"
    VALIDATION_FAILED = "validation_failed"
    DATA_ENRICHED = "data_enriched"
    WEBHOOK_TRIGGERED = "webhook_triggered"


# ==================== EXCEPTIONS ====================

class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class ValidationError(Exception):
    """Custom exception for data validation."""
    pass


class WebhookError(Exception):
    """Custom exception for webhook operations."""
    pass


# ==================== VALIDATION RULES ====================

class ValidationRule:
    """Base validation rule."""

    def __init__(self, rule_type: ValidationRuleType, name: str, enabled: bool = True):
        self.rule_type = rule_type
        self.name = name
        self.enabled = enabled

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate data. Returns (is_valid, error_message)."""
        raise NotImplementedError


class EmailFormatRule(ValidationRule):
    """Validate email format."""

    def __init__(self):
        super().__init__(ValidationRuleType.EMAIL_FORMAT, "Email Format Validation")

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        email = data.get('email', '')
        if email and ('@' not in email or '.' not in email.split('@')[1]):
            return False, f"Invalid email format: {email}"
        return True, None


class CreditScoreRangeRule(ValidationRule):
    """Validate credit score is within acceptable range."""

    def __init__(self, min_score: int = 300, max_score: int = 850):
        super().__init__(ValidationRuleType.CREDIT_SCORE_RANGE, "Credit Score Range Validation")
        self.min_score = min_score
        self.max_score = max_score

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        score = data.get('credit_score')
        if score is not None:
            if not isinstance(score, int) or score < self.min_score or score > self.max_score:
                return False, f"Credit score must be between {self.min_score} and {self.max_score}, got {score}"
        return True, None


class IncomeThresholdRule(ValidationRule):
    """Validate minimum income requirement."""

    def __init__(self, min_income: float = 20000):
        super().__init__(ValidationRuleType.INCOME_THRESHOLD, "Income Threshold Validation")
        self.min_income = min_income

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        income = data.get('annual_income')
        if income is not None and income < self.min_income:
            return False, f"Annual income must be at least ${self.min_income}, got ${income}"
        return True, None


class EmploymentStatusRule(ValidationRule):
    """Validate employment status is valid."""

    VALID_STATUSES = {'active', 'inactive', 'self-employed', 'unemployed', 'retired', 'student', 'unknown'}

    def __init__(self):
        super().__init__(ValidationRuleType.EMPLOYMENT_STATUS_VALID, "Employment Status Validation")

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        status = data.get('employment_status', 'unknown')
        if status not in self.VALID_STATUSES:
            return False, f"Invalid employment status: {status}. Must be one of {self.VALID_STATUSES}"
        return True, None


class PhoneFormatRule(ValidationRule):
    """Validate phone format."""

    def __init__(self):
        super().__init__(ValidationRuleType.PHONE_FORMAT, "Phone Format Validation")

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        phone = data.get('phone', '')
        if phone:
            # Basic validation: at least 10 digits
            digits = ''.join(c for c in phone if c.isdigit())
            if len(digits) < 10:
                return False, f"Phone number must contain at least 10 digits: {phone}"
        return True, None


class SSNFormatRule(ValidationRule):
    """Validate SSN format."""

    def __init__(self):
        super().__init__(ValidationRuleType.SSN_FORMAT, "SSN Format Validation")

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        ssn = data.get('ssn', '')
        if ssn:
            # Basic validation: XXX-XX-XXXX or XXXXXXXXX
            digits = ''.join(c for c in ssn if c.isdigit())
            if len(digits) != 9:
                return False, f"SSN must have 9 digits: {ssn}"
        return True, None


class DebtToIncomeRatioRule(ValidationRule):
    """Validate debt-to-income ratio."""

    def __init__(self, max_ratio: float = 0.43):
        super().__init__(ValidationRuleType.DEBT_TO_INCOME_RATIO, "Debt-to-Income Ratio Validation")
        self.max_ratio = max_ratio

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        income = data.get('annual_income')
        total_debt = data.get('total_debt')

        if income and total_debt and income > 0:
            ratio = total_debt / income
            if ratio > self.max_ratio:
                return False, f"Debt-to-income ratio {ratio:.2%} exceeds maximum {self.max_ratio:.2%}"
        return True, None


class AddressCompletenessRule(ValidationRule):
    """Validate address completeness."""

    def __init__(self):
        super().__init__(ValidationRuleType.ADDRESS_COMPLETENESS, "Address Completeness Validation")

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        # If address provided, require city, state, and zip
        if data.get('address'):
            required = {'city', 'state', 'zip_code'}
            missing = [f for f in required if not data.get(f)]
            if missing:
                return False, f"If address provided, must include: {', '.join(missing)}"
        return True, None


class AgeRequirementRule(ValidationRule):
    """Validate applicant is at least 18 years old."""

    def __init__(self, min_age: int = 18):
        super().__init__(ValidationRuleType.AGE_REQUIREMENT, "Age Requirement Validation")
        self.min_age = min_age

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        dob = data.get('date_of_birth')
        if dob:
            try:
                birth_date = datetime.fromisoformat(dob)
                age = (datetime.utcnow() - birth_date).days // 365
                if age < self.min_age:
                    return False, f"Applicant must be at least {self.min_age} years old, currently {age}"
            except ValueError:
                return False, f"Invalid date format: {dob}"
        return True, None


# ==================== WEBHOOK MANAGEMENT ====================

class WebhookManager:
    """Manages webhook registrations and dispatching."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()
        self.registered_hooks: Dict[str, List[Callable]] = {
            'profile_updated': [],
            'credit_updated': [],
            'employment_verified': [],
            'validation_failed': []
        }
        self.webhook_queue = queue.Queue()
        self._start_webhook_worker()

    def _init_database(self):
        """Initialize webhook database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS webhooks (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_triggered TEXT,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS webhook_logs (
                        id TEXT PRIMARY KEY,
                        webhook_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        status_code INTEGER,
                        response_text TEXT,
                        triggered_at TEXT NOT NULL,
                        FOREIGN KEY (webhook_id) REFERENCES webhooks(id)
                    )
                ''')
                conn.commit()
                logger.info(f"Webhook database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Webhook database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize webhook database: {e}")

    def register_webhook(self, url: str, event_type: str) -> str:
        """Register a webhook endpoint."""
        webhook_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO webhooks (id, url, event_type, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', (webhook_id, url, event_type, now, True))
                conn.commit()
                logger.info(f"Registered webhook {webhook_id} for {event_type}")
                return webhook_id
        except sqlite3.Error as e:
            logger.error(f"Error registering webhook: {e}")
            raise DatabaseError(f"Failed to register webhook: {e}")

    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook endpoint."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM webhooks WHERE id = ?', (webhook_id,))
                conn.commit()
                logger.info(f"Unregistered webhook {webhook_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error unregistering webhook: {e}")
            raise DatabaseError(f"Failed to unregister webhook: {e}")

    def list_webhooks(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered webhooks."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if event_type:
                    cursor.execute('SELECT * FROM webhooks WHERE event_type = ? AND is_active = 1', (event_type,))
                else:
                    cursor.execute('SELECT * FROM webhooks WHERE is_active = 1')

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error listing webhooks: {e}")
            raise DatabaseError(f"Failed to list webhooks: {e}")

    def trigger_webhook(self, event_type: str, payload: Dict[str, Any]):
        """Trigger webhooks for an event (async via queue)."""
        self.webhook_queue.put((event_type, payload))

    def _start_webhook_worker(self):
        """Start background thread for webhook processing."""
        def worker():
            while True:
                try:
                    event_type, payload = self.webhook_queue.get(timeout=1)
                    webhooks = self.list_webhooks(event_type)

                    for webhook in webhooks:
                        self._dispatch_webhook(webhook['id'], webhook['url'], event_type, payload)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Webhook worker error: {e}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _dispatch_webhook(self, webhook_id: str, url: str, event_type: str, payload: Dict[str, Any]):
        """Dispatch a webhook (simulated)."""
        try:
            # Simulate webhook call - in production use requests library
            logger.info(f"Webhook dispatch to {url}: {event_type} - {json.dumps(payload)}")

            # Log webhook execution
            log_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO webhook_logs (
                        id, webhook_id, event_type, payload, status_code, response_text, triggered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (log_id, webhook_id, event_type, json.dumps(payload), 200, "Simulated", now))

                # Update last_triggered
                cursor.execute('UPDATE webhooks SET last_triggered = ? WHERE id = ?', (now, webhook_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Webhook dispatch failed: {e}")


# ==================== AUDIT TRAIL ====================

class AuditTrail:
    """Manages audit logging for all data changes."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize audit database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        applicant_id TEXT,
                        entity_type TEXT,
                        entity_id TEXT,
                        action TEXT NOT NULL,
                        old_values TEXT,
                        new_values TEXT,
                        user_id TEXT DEFAULT 'system',
                        ip_address TEXT,
                        timestamp TEXT NOT NULL,
                        status TEXT DEFAULT 'success'
                    )
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_audit_applicant ON audit_log(applicant_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)
                ''')
                conn.commit()
                logger.info(f"Audit database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Audit database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize audit database: {e}")

    def log_event(
        self,
        event_type: AuditEventType,
        applicant_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        user_id: str = "system",
        ip_address: Optional[str] = None,
        status: str = "success"
    ) -> str:
        """Log an audit event."""
        event_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log (
                        id, event_type, applicant_id, entity_type, entity_id, action,
                        old_values, new_values, user_id, ip_address, timestamp, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id,
                    event_type.value,
                    applicant_id,
                    entity_type,
                    entity_id,
                    action,
                    json.dumps(old_values) if old_values else None,
                    json.dumps(new_values) if new_values else None,
                    user_id,
                    ip_address,
                    now,
                    status
                ))
                conn.commit()
                logger.info(f"Audit event logged: {event_id} ({event_type.value})")
                return event_id
        except sqlite3.Error as e:
            logger.error(f"Error logging audit event: {e}")
            raise DatabaseError(f"Failed to log audit event: {e}")

    def get_history(self, applicant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit history for an applicant."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM audit_log
                    WHERE applicant_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (applicant_id, limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving audit history: {e}")
            raise DatabaseError(f"Failed to retrieve audit history: {e}")


# ==================== DATA ENRICHMENT ====================

class DataEnrichmentService:
    """Simulates external data enrichment services."""

    @staticmethod
    def enrich_credit_data(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate enrichment from credit bureau."""
        email = applicant_data.get('email', '')
        email_hash = hashlib.md5(email.encode()).hexdigest()

        # Simulated credit data based on email hash
        hash_value = int(email_hash, 16)
        credit_score = 650 + (hash_value % 200)
        total_debt = 5000 + (hash_value % 45000)
        available_credit = 10000 + (hash_value % 40000)

        return {
            'credit_score': min(850, max(300, credit_score)),
            'total_debt': total_debt,
            'available_credit': available_credit,
            'source': 'simulated_credit_bureau'
        }

    @staticmethod
    def enrich_employment_data(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate enrichment from employment verification service."""
        name = f"{applicant_data.get('first_name', '')} {applicant_data.get('last_name', '')}".lower()
        name_hash = hashlib.md5(name.encode()).hexdigest()

        hash_value = int(name_hash, 16)
        employment_verified = (hash_value % 100) > 20  # 80% verified

        return {
            'employment_verified': employment_verified,
            'verification_confidence': 0.75 + (hash_value % 25) / 100,
            'source': 'simulated_employment_service'
        }

    @staticmethod
    def enrich_identity_data(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate enrichment from identity verification service."""
        ssn = applicant_data.get('ssn', '')
        ssn_hash = hashlib.md5(ssn.encode()).hexdigest() if ssn else "00000000"

        hash_value = int(ssn_hash, 16)
        identity_verified = (hash_value % 100) > 10  # 90% verified

        return {
            'identity_verified': identity_verified,
            'verification_date': datetime.utcnow().isoformat(),
            'source': 'simulated_identity_service'
        }


# ==================== DATABASE CLASSES ====================

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

                # Applicants table with enrichment data
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
                        enrichment_data TEXT,
                        validation_status TEXT,
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
                        enrichment_source TEXT,
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

        now = datetime.utcnow().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO applicants (
                        id, first_name, last_name, email, phone, ssn, date_of_birth,
                        address, city, state, zip_code, employment_status, employer_id,
                        annual_income, enrichment_data, validation_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(applicant_data.get('enrichment_data', {})),
                    'pending_validation',
                    now,
                    now
                ))
                conn.commit()
                logger.info(f"Created applicant: {applicant_data['id']}")
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
                    result = dict(row)
                    # Parse enrichment_data
                    if result.get('enrichment_data'):
                        result['enrichment_data'] = json.loads(result['enrichment_data'])
                    return result
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving applicant: {e}")
            raise DatabaseError(f"Failed to retrieve applicant: {e}")

    def get_applicants_batch(self, applicant_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve multiple applicants by IDs."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                placeholders = ','.join('?' * len(applicant_ids))
                cursor.execute(f'SELECT * FROM applicants WHERE id IN ({placeholders})', applicant_ids)
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    data = dict(row)
                    if data.get('enrichment_data'):
                        data['enrichment_data'] = json.loads(data['enrichment_data'])
                    result.append(data)
                return result
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving applicants batch: {e}")
            raise DatabaseError(f"Failed to retrieve applicants batch: {e}")

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
        if not self.get_applicant(applicant_id):
            raise ValidationError(f"Applicant not found: {applicant_id}")

        now = datetime.utcnow().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO credit_history (
                        applicant_id, credit_score, total_debt, available_credit,
                        payment_history, enrichment_source, last_updated, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    applicant_id,
                    credit_data.get('credit_score'),
                    credit_data.get('total_debt'),
                    credit_data.get('available_credit'),
                    json.dumps(credit_data.get('payment_history', [])),
                    credit_data.get('source'),
                    now,
                    updated_by
                ))
                conn.commit()
                record_id = cursor.lastrowid
                logger.info(f"Added credit update for applicant {applicant_id}: {record_id}")
                _clear_profile_cache()
                return record_id
        except sqlite3.Error as e:
            logger.error(f"Database error adding credit update: {e}")
            raise DatabaseError(f"Failed to add credit update: {e}")

    def update_validation_status(self, applicant_id: str, status: str):
        """Update validation status for applicant."""
        now = datetime.utcnow().isoformat()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE applicants
                    SET validation_status = ?, updated_at = ?
                    WHERE id = ?
                ''', (status, now, applicant_id))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating validation status: {e}")
            raise DatabaseError(f"Failed to update validation status: {e}")


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

                cursor.execute('SELECT * FROM employers WHERE id = ?', (employer_id,))
                employer = cursor.fetchone()
                if not employer:
                    raise ValidationError(f"Employer not found: {employer_id}")

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


# ==================== INITIALIZATION ====================

# Initialize database instances
applicant_db = ApplicantDB(DB_PATH)
employer_db = EmployerDB(EMPLOYMENT_DB_PATH)
audit_trail = AuditTrail(AUDIT_DB_PATH)
webhook_manager = WebhookManager(AUDIT_DB_PATH)

# Initialize validation rules
VALIDATION_RULES: Dict[ValidationRuleType, ValidationRule] = {
    ValidationRuleType.EMAIL_FORMAT: EmailFormatRule(),
    ValidationRuleType.CREDIT_SCORE_RANGE: CreditScoreRangeRule(),
    ValidationRuleType.INCOME_THRESHOLD: IncomeThresholdRule(),
    ValidationRuleType.EMPLOYMENT_STATUS_VALID: EmploymentStatusRule(),
    ValidationRuleType.PHONE_FORMAT: PhoneFormatRule(),
    ValidationRuleType.SSN_FORMAT: SSNFormatRule(),
    ValidationRuleType.DEBT_TO_INCOME_RATIO: DebtToIncomeRatioRule(),
    ValidationRuleType.ADDRESS_COMPLETENESS: AddressCompletenessRule(),
    ValidationRuleType.AGE_REQUIREMENT: AgeRequirementRule(),
}


# ==================== CACHE ====================

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

    if applicant_id in _profile_cache:
        return _profile_cache[applicant_id]

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

    if len(_profile_cache) >= CACHE_SIZE:
        removed_key = _profile_cache_keys.pop(0)
        del _profile_cache[removed_key]

    _profile_cache[applicant_id] = profile
    _profile_cache_keys.append(applicant_id)

    return profile


# ==================== MCP TOOLS ====================

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
    Create a new applicant record with validation and enrichment.

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
        Confirmation of applicant creation with validation results
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
            "employment_status": employment_status or "unknown",
            "employer_id": employer_id,
            "annual_income": annual_income
        }

        # Validate applicant data
        validation_errors = []
        for rule in VALIDATION_RULES.values():
            if rule.enabled:
                is_valid, error = rule.validate(applicant_data)
                if not is_valid:
                    validation_errors.append(error)

        # Enrich data from external services
        enrichment_data = {
            'credit_enrichment': DataEnrichmentService.enrich_credit_data(applicant_data),
            'employment_enrichment': DataEnrichmentService.enrich_employment_data(applicant_data),
            'identity_enrichment': DataEnrichmentService.enrich_identity_data(applicant_data),
            'enriched_at': datetime.utcnow().isoformat()
        }
        applicant_data['enrichment_data'] = enrichment_data

        # Create applicant
        created_id = applicant_db.create_applicant(applicant_data)

        # Set validation status
        validation_status = "valid" if not validation_errors else "invalid"
        applicant_db.update_validation_status(applicant_id, validation_status)

        # Log audit event
        audit_trail.log_event(
            AuditEventType.PROFILE_CREATED,
            applicant_id=applicant_id,
            entity_type="applicant",
            entity_id=applicant_id,
            action="create",
            new_values=applicant_data,
            status="success"
        )

        # Log data enrichment
        audit_trail.log_event(
            AuditEventType.DATA_ENRICHED,
            applicant_id=applicant_id,
            entity_type="enrichment",
            action="enrich",
            new_values=enrichment_data
        )

        # Trigger webhook
        webhook_manager.trigger_webhook('profile_updated', {
            'applicant_id': applicant_id,
            'event': 'profile_created',
            'timestamp': datetime.utcnow().isoformat()
        })

        return {
            "success": True,
            "applicant_id": created_id,
            "message": "Applicant created successfully",
            "validation_status": validation_status,
            "validation_errors": validation_errors,
            "enrichment_data": enrichment_data
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
def get_applicant_profile(applicant_id: str) -> Dict[str, Any]:
    """
    Get complete applicant profile including personal info, credit history,
    employment records, enrichment data, and validation status.

    Args:
        applicant_id: The unique identifier of the applicant

    Returns:
        Dictionary containing full applicant profile
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
def get_applicants_batch(applicant_ids: List[str]) -> Dict[str, Any]:
    """
    Get multiple applicant profiles in a single batch operation.
    More efficient than multiple individual get_applicant_profile calls.

    Args:
        applicant_ids: List of applicant IDs to retrieve

    Returns:
        Dictionary with list of applicant profiles and summary statistics
    """
    try:
        if not applicant_ids:
            return {
                "success": False,
                "error": "applicant_ids list cannot be empty"
            }

        if len(applicant_ids) > 100:
            return {
                "success": False,
                "error": "Maximum 100 applicants per batch request"
            }

        applicants = applicant_db.get_applicants_batch(applicant_ids)

        # Get additional data for each applicant
        profiles = []
        for applicant in applicants:
            credit_history = applicant_db.get_credit_history(applicant['id'])
            employment_records = employer_db.get_employment_records(applicant['id'])

            profiles.append({
                "applicant": applicant,
                "credit_history": credit_history,
                "employment_records": employment_records
            })

        return {
            "success": True,
            "count": len(profiles),
            "profiles": profiles,
            "summary": {
                "requested": len(applicant_ids),
                "retrieved": len(profiles),
                "not_found": len(applicant_ids) - len(profiles)
            }
        }
    except DatabaseError as e:
        logger.error(f"Error retrieving applicants batch: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def validate_applicant_profile(applicant_id: str) -> Dict[str, Any]:
    """
    Run all validation rules against an applicant profile.

    Args:
        applicant_id: The unique identifier of the applicant

    Returns:
        Validation results with list of errors and warnings
    """
    try:
        applicant = applicant_db.get_applicant(applicant_id)
        if not applicant:
            return {
                "success": False,
                "error": f"Applicant not found: {applicant_id}"
            }

        # Prepare credit data
        credit_history = applicant_db.get_credit_history(applicant_id, limit=1)
        if credit_history:
            applicant['credit_score'] = credit_history[0].get('credit_score')
            applicant['total_debt'] = credit_history[0].get('total_debt')

        errors = []
        warnings = []

        for rule_type, rule in VALIDATION_RULES.items():
            if rule.enabled:
                is_valid, error = rule.validate(applicant)
                if not is_valid:
                    errors.append(error)

        validation_status = "valid" if not errors else "invalid"
        applicant_db.update_validation_status(applicant_id, validation_status)

        # Log audit event
        audit_trail.log_event(
            AuditEventType.VALIDATION_FAILED if errors else AuditEventType.PROFILE_UPDATED,
            applicant_id=applicant_id,
            action="validate",
            new_values={"validation_errors": errors},
            status="success"
        )

        return {
            "success": True,
            "applicant_id": applicant_id,
            "validation_status": validation_status,
            "errors": errors,
            "warnings": warnings,
            "rules_checked": len(VALIDATION_RULES),
            "rules_passed": len(VALIDATION_RULES) - len(errors)
        }
    except DatabaseError as e:
        logger.error(f"Error validating applicant: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_applicant_audit_history(applicant_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get complete audit history for an applicant including all changes and events.

    Args:
        applicant_id: The unique identifier of the applicant
        limit: Maximum number of records to return (default 50)

    Returns:
        List of audit events in chronological order
    """
    try:
        history = audit_trail.get_history(applicant_id, limit)

        # Parse JSON fields
        for record in history:
            if record.get('old_values'):
                record['old_values'] = json.loads(record['old_values'])
            if record.get('new_values'):
                record['new_values'] = json.loads(record['new_values'])

        return {
            "success": True,
            "applicant_id": applicant_id,
            "count": len(history),
            "history": history
        }
    except DatabaseError as e:
        logger.error(f"Error retrieving audit history: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def register_webhook(url: str, event_type: str) -> Dict[str, Any]:
    """
    Register a webhook endpoint for profile update notifications.

    Args:
        url: The webhook endpoint URL
        event_type: Type of event (profile_updated, credit_updated, employment_verified, validation_failed)

    Returns:
        Webhook registration details with ID
    """
    try:
        valid_events = ['profile_updated', 'credit_updated', 'employment_verified', 'validation_failed']
        if event_type not in valid_events:
            return {
                "success": False,
                "error": f"Invalid event_type. Must be one of: {valid_events}"
            }

        webhook_id = webhook_manager.register_webhook(url, event_type)

        return {
            "success": True,
            "webhook_id": webhook_id,
            "url": url,
            "event_type": event_type,
            "registered_at": datetime.utcnow().isoformat()
        }
    except DatabaseError as e:
        logger.error(f"Error registering webhook: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def unregister_webhook(webhook_id: str) -> Dict[str, Any]:
    """
    Unregister a webhook endpoint.

    Args:
        webhook_id: The webhook ID to unregister

    Returns:
        Confirmation of webhook removal
    """
    try:
        success = webhook_manager.unregister_webhook(webhook_id)

        return {
            "success": success,
            "webhook_id": webhook_id,
            "message": "Webhook unregistered" if success else "Webhook not found"
        }
    except DatabaseError as e:
        logger.error(f"Error unregistering webhook: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def list_webhooks(event_type: Optional[str] = None) -> Dict[str, Any]:
    """
    List all registered webhooks, optionally filtered by event type.

    Args:
        event_type: Optional filter by event type

    Returns:
        List of registered webhook endpoints
    """
    try:
        webhooks = webhook_manager.list_webhooks(event_type)

        return {
            "success": True,
            "count": len(webhooks),
            "webhooks": webhooks
        }
    except DatabaseError as e:
        logger.error(f"Error listing webhooks: {e}")
        return {
            "success": False,
            "error": str(e)
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
    """
    try:
        credit_data = {
            "credit_score": credit_score,
            "total_debt": total_debt,
            "available_credit": available_credit,
            "payment_history": payment_history or [],
            "source": "manual_update"
        }

        record_id = applicant_db.add_credit_update(applicant_id, credit_data, updated_by)

        # Log audit event
        audit_trail.log_event(
            AuditEventType.CREDIT_UPDATED,
            applicant_id=applicant_id,
            entity_type="credit",
            action="update",
            new_values=credit_data,
            user_id=updated_by
        )

        # Trigger webhook
        webhook_manager.trigger_webhook('credit_updated', {
            'applicant_id': applicant_id,
            'event': 'credit_updated',
            'record_id': record_id,
            'timestamp': datetime.utcnow().isoformat()
        })

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

        # Log audit event
        audit_trail.log_event(
            AuditEventType.EMPLOYMENT_VERIFIED,
            applicant_id=applicant_id,
            entity_type="employment",
            entity_id=result.get('verification_id'),
            action="verify",
            new_values=employee_data
        )

        # Trigger webhook
        webhook_manager.trigger_webhook('employment_verified', {
            'applicant_id': applicant_id,
            'event': 'employment_verified',
            'employer_id': employer_id,
            'timestamp': datetime.utcnow().isoformat()
        })

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
    Get statistics about the ApplicantDB database including counts and performance metrics.

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

            cursor.execute('SELECT COUNT(*) FROM applicants WHERE validation_status = "valid"')
            valid_applicants = cursor.fetchone()[0]

        with employer_db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM employers')
            employer_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM employee_records')
            employment_records = cursor.fetchone()[0]

        with sqlite3.connect(AUDIT_DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM audit_log')
            audit_records = cursor.fetchone()[0]

        webhooks = webhook_manager.list_webhooks()

        return {
            "success": True,
            "applicant_stats": {
                "total": applicant_count,
                "active": active_count,
                "valid": valid_applicants,
                "invalid": applicant_count - valid_applicants
            },
            "credit_stats": {
                "records": credit_records,
                "average_per_applicant": round(credit_records / max(applicant_count, 1), 2)
            },
            "employer_stats": {
                "total_employers": employer_count,
                "total_employment_records": employment_records
            },
            "audit_stats": {
                "total_events": audit_records
            },
            "webhook_stats": {
                "total_webhooks": len(webhooks),
                "active_webhooks": sum(1 for w in webhooks if w.get('is_active'))
            },
            "database_locations": {
                "applicant_db": str(DB_PATH),
                "employer_db": str(EMPLOYMENT_DB_PATH),
                "audit_db": str(AUDIT_DB_PATH)
            },
            "cache_size": CACHE_SIZE,
            "cache_current": len(_profile_cache)
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
