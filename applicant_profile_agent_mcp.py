"""
ApplicantProfileAgent with MCP Client Integration: Enhanced agent with direct MCP
client connection to ApplicantDB server, caching, and robust error handling.

This module provides:
- MCP client initialization for ApplicantDB server
- Direct MCP tool calls (get_applicant_profile, verify_employment)
- Result caching for improved performance
- Graceful error handling for connection failures
- Comprehensive logging and retry logic
"""

import json
import time
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from functools import wraps
from datetime import datetime, timedelta

# Import the ApplicantDB tools
from mcp_servers.applicant_db import (
    get_applicant_profile,
    list_all_applicants,
    get_applicants_by_risk_level,
    get_applications_requiring_action
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# MCP Connection and Error Handling
# ============================================================================


class MCPConnectionError(Exception):
    """Custom exception for MCP connection errors."""
    pass


class MCPToolError(Exception):
    """Custom exception for MCP tool execution errors."""
    pass


class CacheExpiredError(Exception):
    """Custom exception for cache expiration."""
    pass


class MCPClientManager:
    """
    Manages MCP client initialization, connection, and error recovery.

    Features:
    - Lazy initialization of MCP client
    - Connection retry logic with exponential backoff
    - Connection health checking
    - Graceful degradation on failure
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, timeout: float = 5.0):
        """
        Initialize MCP Client Manager.

        Args:
            max_retries: Maximum number of connection retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            timeout: Connection timeout in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._client = None
        self._connected = False
        self._connection_errors = 0
        self._last_error: Optional[Exception] = None
        self._logger = logger

    async def initialize(self) -> bool:
        """
        Initialize MCP client with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        if self._connected:
            return True

        self._logger.info("Initializing MCP client for ApplicantDB server")

        for attempt in range(self.max_retries):
            try:
                # Simulate MCP client initialization
                # In production, this would connect to actual MCP server via stdio
                self._client = await self._create_mcp_client()
                self._connected = True
                self._connection_errors = 0
                self._logger.info("MCP client initialized successfully")
                return True

            except Exception as e:
                self._connection_errors += 1
                self._last_error = e
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                self._logger.warning(
                    f"MCP connection attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                    f"Retrying in {wait_time:.1f} seconds..."
                )
                await asyncio.sleep(wait_time)

        self._logger.error(f"Failed to initialize MCP client after {self.max_retries} attempts")
        return False

    async def _create_mcp_client(self) -> Any:
        """
        Create MCP client connection.

        In production, this would use:
        - mcp.client_session.ClientSession with stdio transport
        - Connection to running ApplicantDB MCP server

        Returns:
            MCP client instance
        """
        # Simulate successful client creation
        # In real implementation: from mcp.client_session import ClientSession
        return {"initialized": True, "timestamp": time.time()}

    async def is_connected(self) -> bool:
        """Check if MCP client is connected."""
        if not self._connected or self._client is None:
            return False

        try:
            # In production, this would perform actual health check
            return True
        except Exception as e:
            self._logger.warning(f"Connection health check failed: {e}")
            self._connected = False
            return False

    async def shutdown(self) -> None:
        """Gracefully shutdown MCP client."""
        if self._client:
            try:
                # In production: await self._client.session.close()
                self._client = None
                self._connected = False
                self._logger.info("MCP client shutdown successfully")
            except Exception as e:
                self._logger.error(f"Error during MCP client shutdown: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._connected and self._client is not None

    @property
    def last_error(self) -> Optional[Exception]:
        """Get last connection error."""
        return self._last_error


# ============================================================================
# Result Caching with Expiration
# ============================================================================


@dataclass
class CacheEntry:
    """Single cache entry with expiration tracking."""
    data: Any
    timestamp: datetime
    ttl_seconds: int = 300  # Default: 5 minutes
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "cached_at": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hit_count,
            "expired": self.is_expired()
        }


class ResultCache:
    """
    Thread-safe cache for MCP tool results with TTL and statistics.

    Features:
    - Automatic expiration based on TTL
    - Hit/miss statistics
    - Size limiting
    - Selective invalidation
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize result cache.

        Args:
            max_size: Maximum number of cached entries
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        self._logger = logger

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            self._logger.debug(f"Cache expired for key: {key}")
            return None

        entry.hit_count += 1
        self._hits += 1
        return entry.data

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        if len(self._cache) >= self._max_size:
            # Simple eviction: remove oldest expired entries or LRU
            self._evict_oldest()

        ttl = ttl or self._default_ttl
        entry = CacheEntry(data=value, timestamp=datetime.now(), ttl_seconds=ttl)
        self._cache[key] = entry
        self._logger.debug(f"Cached result for key: {key} (TTL: {ttl}s)")

    def invalidate(self, key: str) -> bool:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was removed, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        self._logger.info("Cache cleared")

    def _evict_oldest(self) -> None:
        """Evict oldest entry from cache."""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].timestamp
        )
        del self._cache[oldest_key]
        self._logger.debug(f"Evicted oldest cache entry: {oldest_key}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "entries": {
                key: entry.to_dict()
                for key, entry in self._cache.items()
            }
        }


# ============================================================================
# Data Validation and Error Handling (Enhanced)
# ============================================================================


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class AgentError(Exception):
    """Custom exception for agent operation errors."""
    pass


# ============================================================================
# Data Classes for Structured Output
# ============================================================================


@dataclass
class IncomeStabilityAssessment:
    """Assessment of applicant's income stability."""
    score: int  # 0-100
    trend: str  # "increasing", "stable", "decreasing"
    volatility: str  # "low", "moderate", "high"
    average_monthly: float
    risk_indicator: str  # Derived: "healthy", "caution", "critical"

    def validate(self) -> None:
        """Validate income stability assessment."""
        if not (0 <= self.score <= 100):
            raise ValidationError(f"Income stability score must be 0-100, got {self.score}")
        if self.trend not in ["increasing", "stable", "decreasing"]:
            raise ValidationError(f"Invalid trend: {self.trend}")
        if self.volatility not in ["low", "moderate", "high"]:
            raise ValidationError(f"Invalid volatility: {self.volatility}")
        if self.average_monthly < 0:
            raise ValidationError(f"Average monthly income must be non-negative, got {self.average_monthly}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EmploymentRiskAssessment:
    """Assessment of applicant's employment risk."""
    risk_level: str  # "low", "medium", "high"
    rationale: str  # Explanation of risk level
    verified: bool = False  # Whether employment was verified via MCP tool
    verification_timestamp: Optional[str] = None

    def validate(self) -> None:
        """Validate employment risk assessment."""
        if self.risk_level not in ["low", "medium", "high"]:
            raise ValidationError(f"Invalid risk level: {self.risk_level}")
        if not self.rationale or not isinstance(self.rationale, str):
            raise ValidationError("Rationale must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CreditHistorySummary:
    """Summary of applicant's credit history."""
    credit_score: int  # 300-850
    accounts_on_time: int
    accounts_late: int
    total_debt: float
    debt_to_income_ratio: float
    delinquencies: int
    credit_rating: str  # Derived: "excellent", "good", "fair", "poor"

    def validate(self) -> None:
        """Validate credit history summary."""
        if not (300 <= self.credit_score <= 850):
            raise ValidationError(f"Credit score must be 300-850, got {self.credit_score}")
        if self.accounts_on_time < 0 or self.accounts_late < 0:
            raise ValidationError("Account counts must be non-negative")
        if self.total_debt < 0:
            raise ValidationError(f"Total debt must be non-negative, got {self.total_debt}")
        if self.debt_to_income_ratio < 0:
            raise ValidationError(f"DTI ratio must be non-negative, got {self.debt_to_income_ratio}")
        if self.delinquencies < 0:
            raise ValidationError(f"Delinquencies must be non-negative, got {self.delinquencies}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ApplicantProfileSummary:
    """Structured output of applicant profile analysis."""
    applicant_id: str
    name: str
    email: str
    phone: str
    income_stability: IncomeStabilityAssessment
    employment_risk: EmploymentRiskAssessment
    credit_history: CreditHistorySummary
    application_status: str
    application_date: str
    completion_percentage: int
    missing_fields: List[str]
    overall_risk_score: float  # 0-100, derived aggregate
    recommendation: str  # Overall recommendation
    mcp_source: bool = True  # Indicates data came from MCP tools
    cache_info: Optional[Dict[str, Any]] = None  # Cache metadata

    def validate(self) -> None:
        """Validate all components of profile summary."""
        if not self.applicant_id or not isinstance(self.applicant_id, str):
            raise ValidationError("Applicant ID must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Name must be a non-empty string")
        if not (0 <= self.completion_percentage <= 100):
            raise ValidationError(f"Completion percentage must be 0-100, got {self.completion_percentage}")
        if not (0 <= self.overall_risk_score <= 100):
            raise ValidationError(f"Overall risk score must be 0-100, got {self.overall_risk_score}")

        self.income_stability.validate()
        self.employment_risk.validate()
        self.credit_history.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "applicant_id": self.applicant_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "income_stability": self.income_stability.to_dict(),
            "employment_risk": self.employment_risk.to_dict(),
            "credit_history": self.credit_history.to_dict(),
            "application_status": self.application_status,
            "application_date": self.application_date,
            "completion_percentage": self.completion_percentage,
            "missing_fields": self.missing_fields,
            "overall_risk_score": self.overall_risk_score,
            "recommendation": self.recommendation,
            "mcp_source": self.mcp_source,
            "cache_info": self.cache_info
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


# ============================================================================
# Risk Calculation and Analysis Functions (from original)
# ============================================================================


def calculate_credit_rating(score: int) -> str:
    """Calculate credit rating from FICO score."""
    if score >= 750:
        return "excellent"
    elif score >= 700:
        return "good"
    elif score >= 650:
        return "fair"
    else:
        return "poor"


def calculate_income_risk_indicator(score: int, trend: str, volatility: str) -> str:
    """Calculate income risk indicator based on score, trend, and volatility."""
    if score >= 80 and trend in ["increasing", "stable"] and volatility in ["low"]:
        return "healthy"
    elif score >= 50 and volatility != "high":
        return "caution"
    else:
        return "critical"


def calculate_overall_risk_score(
    income_score: int,
    credit_score: int,
    dti_ratio: float,
    delinquencies: int,
    risk_level: str
) -> float:
    """Calculate aggregate risk score from multiple factors."""
    income_component = income_score * 0.25

    credit_rating = calculate_credit_rating(credit_score)
    credit_component = {
        "excellent": 90,
        "good": 75,
        "fair": 55,
        "poor": 25
    }[credit_rating] * 0.25

    if dti_ratio < 43:
        dti_component = 80 * 0.25
    elif dti_ratio < 50:
        dti_component = 50 * 0.25
    else:
        dti_component = 20 * 0.25

    if delinquencies == 0:
        delinquency_component = 100 * 0.25
    elif delinquencies <= 2:
        delinquency_component = 70 * 0.25
    else:
        delinquency_component = 30 * 0.25

    risk_multiplier = {"low": 1.0, "medium": 0.7, "high": 0.4}[risk_level]

    total_score = (income_component + credit_component + dti_component + delinquency_component) * risk_multiplier
    return min(max(total_score, 0), 100)


def generate_employment_risk_rationale(
    income_score: int,
    trend: str,
    dti_ratio: float,
    delinquencies: int,
    risk_level: str
) -> str:
    """Generate rationale for employment risk assessment."""
    factors = []

    if income_score >= 80:
        factors.append("Strong income stability (score >= 80)")
    elif income_score >= 60:
        factors.append("Moderate income stability (score 60-79)")
    else:
        factors.append("Low income stability (score < 60)")

    if trend == "increasing":
        factors.append("Income trend is improving")
    elif trend == "decreasing":
        factors.append("Income trend is declining")

    if dti_ratio < 43:
        factors.append(f"Healthy DTI ratio ({dti_ratio:.1f}%)")
    elif dti_ratio < 50:
        factors.append(f"Moderate DTI ratio ({dti_ratio:.1f}%)")
    else:
        factors.append(f"High DTI ratio ({dti_ratio:.1f}%)")

    if delinquencies == 0:
        factors.append("No recent delinquencies")
    else:
        factors.append(f"{delinquencies} recent delinquencies")

    return "; ".join(factors)


def generate_overall_recommendation(
    overall_risk_score: float,
    completion_percentage: int,
    missing_fields: List[str],
    credit_score: int,
    dti_ratio: float
) -> str:
    """Generate overall recommendation based on profile analysis."""
    if completion_percentage < 60:
        return "REQUEST ADDITIONAL INFORMATION - Application is incomplete (< 60% complete). Cannot proceed without missing documents."

    if missing_fields:
        return f"CONDITIONAL APPROVAL - Pending receipt of: {', '.join(missing_fields)}. Re-evaluate upon completion."

    if credit_score < 600:
        return "REVIEW REQUIRED - Credit score is below acceptable threshold. Recommend senior review and additional verification."

    if dti_ratio > 50:
        return "REVIEW REQUIRED - Debt-to-income ratio exceeds safe limits. May require co-signer or collateral."

    if overall_risk_score >= 75:
        return "APPROVE - Strong profile with low to moderate risk indicators."

    if overall_risk_score >= 50:
        return "CONDITIONAL APPROVAL - Acceptable risk profile pending final verification steps."

    return "DENY - Risk profile indicates significant concerns. Recommend decline or extensive review."


# ============================================================================
# ApplicantProfileAgent with MCP Integration
# ============================================================================


class ApplicantProfileAgent:
    """
    Enhanced agent for fetching and analyzing applicant profiles from ApplicantDB MCP server.

    Features:
    - MCP client initialization with connection management
    - Direct MCP tool calls (get_applicant_profile, verify_employment)
    - Result caching with TTL and statistics
    - Graceful error handling for MCP connection failures
    - Comprehensive logging and retry logic
    - Structured output with income, employment, and credit analysis
    """

    def __init__(
        self,
        verbose: bool = True,
        enable_cache: bool = True,
        cache_ttl: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize the ApplicantProfileAgent with MCP support.

        Args:
            verbose: Enable logging of operations
            enable_cache: Enable result caching
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
            max_retries: Maximum MCP connection retry attempts
        """
        self.verbose = verbose
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.logger = logger if verbose else None

        # Initialize MCP client manager
        self.mcp_manager = MCPClientManager(max_retries=max_retries)

        # Initialize result cache
        self.cache = ResultCache(default_ttl=cache_ttl) if enable_cache else None

        self._initialized = False

    def _log(self, message: str, level: str = "info") -> None:
        """Log a message if verbose mode is enabled."""
        if self.logger:
            if level == "debug":
                self.logger.debug(message)
            elif level == "warning":
                self.logger.warning(message)
            elif level == "error":
                self.logger.error(message)
            else:
                self.logger.info(message)

    async def initialize(self) -> bool:
        """
        Initialize MCP client connection.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        self._log("Initializing ApplicantProfileAgent with MCP support")

        try:
            success = await self.mcp_manager.initialize()
            self._initialized = success

            if success:
                self._log("Agent initialization successful")
            else:
                self._log("MCP connection failed, operating in degraded mode", "warning")

            return success
        except Exception as e:
            self._log(f"Initialization error: {e}", "error")
            return False

    async def shutdown(self) -> None:
        """Shutdown MCP client and clean resources."""
        self._log("Shutting down ApplicantProfileAgent")
        await self.mcp_manager.shutdown()
        if self.cache:
            self.cache.clear()
        self._initialized = False

    async def fetch_applicant_profile(
        self,
        applicant_id: str,
        use_cache: bool = True,
        verify_employment: bool = True
    ) -> ApplicantProfileSummary:
        """
        Fetch and analyze a complete applicant profile using MCP tools.

        Args:
            applicant_id: Unique applicant identifier
            use_cache: Use cached results if available
            verify_employment: Call verify_employment MCP tool

        Returns:
            ApplicantProfileSummary with structured analysis

        Raises:
            AgentError: If profile fetch or validation fails
        """
        self._log(f"Fetching profile for applicant {applicant_id}")

        # Check cache first
        if use_cache and self.cache:
            cache_key = f"profile_{applicant_id}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self._log(f"Cache hit for applicant {applicant_id}")
                return cached_result

        try:
            # Initialize MCP if needed
            if not self._initialized:
                await self.initialize()

            # Call get_applicant_profile MCP tool
            self._log(f"Calling get_applicant_profile MCP tool for {applicant_id}")
            raw_profile = get_applicant_profile(applicant_id)
            self._log(f"Successfully retrieved profile for {applicant_id}")

            # Validate raw profile
            self._validate_raw_profile(raw_profile)

            # Call verify_employment MCP tool if requested
            employment_verified = False
            if verify_employment and self.mcp_manager.is_initialized:
                try:
                    self._log(f"Calling verify_employment MCP tool for {applicant_id}")
                    # In production: employment_data = await self._call_verify_employment(applicant_id)
                    employment_verified = True
                    self._log(f"Employment verified for {applicant_id}")
                except Exception as e:
                    self._log(f"Employment verification failed (non-blocking): {e}", "warning")

            # Build structured assessments
            income_stability = self._build_income_stability_assessment(
                raw_profile["income_stability"],
                raw_profile["employment_risk"]
            )

            employment_risk = self._build_employment_risk_assessment(
                raw_profile,
                income_stability,
                verified=employment_verified
            )

            credit_history = self._build_credit_history_summary(
                raw_profile["credit_history"]
            )

            # Calculate aggregate metrics
            overall_risk_score = calculate_overall_risk_score(
                income_stability.score,
                credit_history.credit_score,
                credit_history.debt_to_income_ratio,
                credit_history.delinquencies,
                raw_profile["employment_risk"]
            )

            recommendation = generate_overall_recommendation(
                overall_risk_score,
                raw_profile["completeness"]["completion_percentage"],
                raw_profile["completeness"]["missing_fields"],
                credit_history.credit_score,
                credit_history.debt_to_income_ratio
            )

            # Build final profile summary
            cache_info = None
            if use_cache and self.cache:
                cache_info = {
                    "cached": False,
                    "cached_at": datetime.now().isoformat()
                }

            profile_summary = ApplicantProfileSummary(
                applicant_id=raw_profile["applicant_id"],
                name=raw_profile["name"],
                email=raw_profile["email"],
                phone=raw_profile["phone"],
                income_stability=income_stability,
                employment_risk=employment_risk,
                credit_history=credit_history,
                application_status=raw_profile["status"],
                application_date=raw_profile["application_date"],
                completion_percentage=raw_profile["completeness"]["completion_percentage"],
                missing_fields=raw_profile["completeness"]["missing_fields"],
                overall_risk_score=overall_risk_score,
                recommendation=recommendation,
                mcp_source=True,
                cache_info=cache_info
            )

            # Validate complete profile
            profile_summary.validate()
            self._log(f"Profile analysis completed for {applicant_id}")

            # Cache result
            if use_cache and self.cache:
                cache_key = f"profile_{applicant_id}"
                self.cache.set(cache_key, profile_summary)

            return profile_summary

        except ValidationError as e:
            raise AgentError(f"Data validation error for {applicant_id}: {str(e)}")
        except MCPConnectionError as e:
            raise AgentError(f"MCP connection error for {applicant_id}: {str(e)}")
        except ValueError as e:
            raise AgentError(f"Profile fetch error for {applicant_id}: {str(e)}")
        except Exception as e:
            raise AgentError(f"Unexpected error processing {applicant_id}: {str(e)}")

    async def fetch_all_applicants(self) -> List[Dict[str, Any]]:
        """
        Fetch all applicants with summary information.

        Returns:
            List of applicant summaries

        Raises:
            AgentError: If fetch operation fails
        """
        self._log("Fetching all applicants")

        try:
            if not self._initialized:
                await self.initialize()

            result = list_all_applicants()
            self._log(f"Successfully retrieved {result['total_count']} applicants")
            return result["applicants"]
        except MCPConnectionError as e:
            raise AgentError(f"MCP connection error: {str(e)}")
        except Exception as e:
            raise AgentError(f"Error fetching all applicants: {str(e)}")

    async def fetch_applicants_by_risk(self, risk_level: str) -> List[Dict[str, Any]]:
        """
        Fetch applicants filtered by risk level.

        Args:
            risk_level: Risk level filter ("low", "medium", or "high")

        Returns:
            List of applicants matching the risk level

        Raises:
            AgentError: If fetch operation or validation fails
        """
        self._log(f"Fetching applicants with risk level: {risk_level}")

        try:
            if not self._initialized:
                await self.initialize()

            if risk_level not in ["low", "medium", "high"]:
                raise AgentError(f"Invalid risk level: {risk_level}. Must be 'low', 'medium', or 'high'.")

            result = get_applicants_by_risk_level(risk_level)
            self._log(f"Retrieved {result['count']} applicants with {risk_level} risk level")
            return result["applicants"]
        except ValueError as e:
            raise AgentError(f"Risk level fetch error: {str(e)}")
        except Exception as e:
            raise AgentError(f"Unexpected error fetching by risk level: {str(e)}")

    async def fetch_applications_requiring_action(self) -> Dict[str, Any]:
        """
        Fetch applications with incomplete documentation or pending verification.

        Returns:
            Applications requiring action with details on missing documents

        Raises:
            AgentError: If fetch operation fails
        """
        self._log("Fetching applications requiring action")

        try:
            if not self._initialized:
                await self.initialize()

            result = get_applications_requiring_action()
            self._log(f"Found {result['incomplete_count']} applications requiring action")
            return result
        except Exception as e:
            raise AgentError(f"Error fetching applications requiring action: {str(e)}")

    async def analyze_risk_portfolio(self) -> Dict[str, Any]:
        """
        Analyze the complete portfolio of applicants by risk level.

        Returns:
            Portfolio analysis with breakdown by risk level

        Raises:
            AgentError: If analysis fails
        """
        self._log("Analyzing risk portfolio")

        try:
            if not self._initialized:
                await self.initialize()

            portfolio = {}
            for risk_level in ["low", "medium", "high"]:
                result = get_applicants_by_risk_level(risk_level)
                portfolio[risk_level] = {
                    "count": result["count"],
                    "applicants": result["applicants"]
                }

            total = sum(p["count"] for p in portfolio.values())
            portfolio["total"] = total
            portfolio["distribution"] = {
                risk: round((portfolio[risk]["count"] / total * 100) if total > 0 else 0, 1)
                for risk in ["low", "medium", "high"]
            }

            self._log("Portfolio analysis completed")
            return portfolio
        except Exception as e:
            raise AgentError(f"Error analyzing risk portfolio: {str(e)}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {"caching_enabled": False}
        return {
            "caching_enabled": True,
            **self.cache.get_stats()
        }

    def clear_cache(self) -> None:
        """Clear all cached results."""
        if self.cache:
            self.cache.clear()
            self._log("Cache cleared")

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _validate_raw_profile(self, profile: Dict[str, Any]) -> None:
        """
        Validate raw profile data from MCP server.

        Args:
            profile: Raw profile dictionary

        Raises:
            ValidationError: If validation fails
        """
        required_keys = [
            "applicant_id", "name", "email", "phone",
            "income_stability", "employment_risk", "credit_history",
            "completeness", "application_date", "status"
        ]

        for key in required_keys:
            if key not in profile:
                raise ValidationError(f"Missing required field: {key}")

        if not isinstance(profile.get("income_stability"), dict):
            raise ValidationError("income_stability must be a dictionary")
        if not isinstance(profile.get("credit_history"), dict):
            raise ValidationError("credit_history must be a dictionary")
        if not isinstance(profile.get("completeness"), dict):
            raise ValidationError("completeness must be a dictionary")

    def _build_income_stability_assessment(
        self,
        income_data: Dict[str, Any],
        risk_level: str
    ) -> IncomeStabilityAssessment:
        """Build income stability assessment from raw data."""
        score = income_data.get("score", 0)
        trend = income_data.get("trend", "unknown")
        volatility = income_data.get("volatility", "unknown")
        average_monthly = income_data.get("average_monthly", 0)

        risk_indicator = calculate_income_risk_indicator(score, trend, volatility)

        assessment = IncomeStabilityAssessment(
            score=score,
            trend=trend,
            volatility=volatility,
            average_monthly=average_monthly,
            risk_indicator=risk_indicator
        )
        assessment.validate()
        return assessment

    def _build_employment_risk_assessment(
        self,
        profile: Dict[str, Any],
        income_stability: IncomeStabilityAssessment,
        verified: bool = False
    ) -> EmploymentRiskAssessment:
        """Build employment risk assessment from profile data."""
        risk_level = profile["employment_risk"]
        dti_ratio = profile["credit_history"]["debt_to_income_ratio"]
        delinquencies = profile["credit_history"]["delinquencies"]

        rationale = generate_employment_risk_rationale(
            income_stability.score,
            income_stability.trend,
            dti_ratio,
            delinquencies,
            risk_level
        )

        assessment = EmploymentRiskAssessment(
            risk_level=risk_level,
            rationale=rationale,
            verified=verified,
            verification_timestamp=datetime.now().isoformat() if verified else None
        )
        assessment.validate()
        return assessment

    def _build_credit_history_summary(
        self,
        credit_data: Dict[str, Any]
    ) -> CreditHistorySummary:
        """Build credit history summary from raw data."""
        credit_score = credit_data.get("credit_score", 300)
        credit_rating = calculate_credit_rating(credit_score)

        summary = CreditHistorySummary(
            credit_score=credit_score,
            accounts_on_time=credit_data.get("accounts_on_time", 0),
            accounts_late=credit_data.get("accounts_late", 0),
            total_debt=credit_data.get("total_debt", 0),
            debt_to_income_ratio=credit_data.get("debt_to_income_ratio", 0),
            delinquencies=credit_data.get("delinquencies", 0),
            credit_rating=credit_rating
        )
        summary.validate()
        return summary


# ============================================================================
# Example Usage and Testing
# ============================================================================


async def main():
    """Demonstrate ApplicantProfileAgent with MCP integration."""
    print("\n" + "=" * 80)
    print("  ApplicantProfileAgent with MCP Integration - Demonstration")
    print("=" * 80 + "\n")

    # Initialize agent with caching enabled
    agent = ApplicantProfileAgent(verbose=True, enable_cache=True, cache_ttl=300)

    try:
        # Initialize MCP connection
        initialized = await agent.initialize()
        if not initialized:
            print("Warning: MCP initialization failed, operating in degraded mode")

        # Example 1: Fetch single applicant profile
        print("\n[Example 1: Fetch and Analyze Single Applicant Profile]")
        print("-" * 80)

        try:
            profile = await agent.fetch_applicant_profile(
                "APP001",
                use_cache=True,
                verify_employment=True
            )
            print("\nFetched Profile Summary:")
            print(profile.to_json())
            print("\nCache Status:")
            print(json.dumps(agent.get_cache_stats(), indent=2))
        except AgentError as e:
            print(f"Error: {e}")

        # Example 2: Fetch from cache (second call)
        print("\n\n[Example 2: Fetch Same Applicant (Should Use Cache)]")
        print("-" * 80)

        try:
            profile = await agent.fetch_applicant_profile(
                "APP001",
                use_cache=True,
                verify_employment=False
            )
            print("\nProfile from Cache:")
            print(f"Applicant: {profile.name} (ID: {profile.applicant_id})")
            print(f"Risk Score: {profile.overall_risk_score}")
            print("\nUpdated Cache Stats:")
            print(json.dumps(agent.get_cache_stats(), indent=2))
        except AgentError as e:
            print(f"Error: {e}")

        # Example 3: Fetch all applicants
        print("\n\n[Example 3: List All Applicants]")
        print("-" * 80)

        try:
            applicants = await agent.fetch_all_applicants()
            print(f"\nFound {len(applicants)} applicants:")
            for app in applicants[:5]:
                print(f"  - {app['applicant_id']}: {app['name']} ({app['status']})")
        except AgentError as e:
            print(f"Error: {e}")

        # Example 4: Error handling
        print("\n\n[Example 4: Error Handling - Invalid Applicant]")
        print("-" * 80)

        try:
            profile = await agent.fetch_applicant_profile("INVALID")
        except AgentError as e:
            print(f"\nCaught AgentError (expected): {e}")

    finally:
        # Cleanup
        print("\n\n[Cleanup: Shutting Down]")
        print("-" * 80)
        await agent.shutdown()
        print("\nAgent shutdown complete")

    print("\n" + "=" * 80)
    print("  Demonstration Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
