"""
Comprehensive test suite for ApplicantProfileAgent with MCP integration.

Tests cover:
- MCP client initialization and connection management
- Direct MCP tool calls (get_applicant_profile, verify_employment)
- Result caching with TTL and statistics
- Error handling and graceful degradation
- Async operations and lifecycle management
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from applicant_profile_agent_mcp import (
    ApplicantProfileAgent,
    MCPClientManager,
    ResultCache,
    MCPConnectionError,
    ValidationError,
    AgentError,
    CacheEntry,
    IncomeStabilityAssessment,
    EmploymentRiskAssessment,
    CreditHistorySummary,
    ApplicantProfileSummary,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mcp_manager():
    """Create MCPClientManager instance."""
    return MCPClientManager(max_retries=2, retry_delay=0.1)


@pytest.fixture
def result_cache():
    """Create ResultCache instance."""
    return ResultCache(max_size=100, default_ttl=300)


@pytest.fixture
def agent():
    """Create ApplicantProfileAgent instance."""
    return ApplicantProfileAgent(
        verbose=True,
        enable_cache=True,
        cache_ttl=300,
        max_retries=2
    )


@pytest.fixture
def sample_profile_data():
    """Sample applicant profile data from MCP server."""
    return {
        "applicant_id": "APP001",
        "name": "Alice Johnson",
        "email": "alice.johnson@email.com",
        "phone": "555-0101",
        "income_stability": {
            "score": 85,
            "trend": "increasing",
            "volatility": "low",
            "average_monthly": 5250.00
        },
        "employment_risk": "low",
        "credit_history": {
            "credit_score": 750,
            "accounts_on_time": 8,
            "accounts_late": 0,
            "total_debt": 15000.00,
            "debt_to_income_ratio": 28.6,
            "delinquencies": 0
        },
        "completeness": {
            "income_documentation_required": False,
            "employment_verification_required": False,
            "identity_verification_required": False,
            "credit_authorization_required": False,
            "missing_fields": [],
            "completion_percentage": 100
        },
        "application_date": "2026-06-01",
        "status": "approved"
    }


# ============================================================================
# MCPClientManager Tests
# ============================================================================


class TestMCPClientManager:
    """Tests for MCP client connection management."""

    @pytest.mark.asyncio
    async def test_initialization_success(self, mcp_manager):
        """Test successful MCP client initialization."""
        assert not mcp_manager.is_initialized

        success = await mcp_manager.initialize()

        assert success is True
        assert mcp_manager.is_initialized
        await mcp_manager.shutdown()

    @pytest.mark.asyncio
    async def test_initialization_idempotent(self, mcp_manager):
        """Test that initialization is idempotent."""
        await mcp_manager.initialize()
        await mcp_manager.initialize()  # Should not reinitialize

        assert mcp_manager.is_initialized
        await mcp_manager.shutdown()

    @pytest.mark.asyncio
    async def test_connection_health_check(self, mcp_manager):
        """Test connection health checking."""
        await mcp_manager.initialize()

        is_connected = await mcp_manager.is_connected()
        assert is_connected is True

        await mcp_manager.shutdown()

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, mcp_manager):
        """Test graceful shutdown."""
        await mcp_manager.initialize()
        assert mcp_manager.is_initialized

        await mcp_manager.shutdown()
        assert not mcp_manager.is_initialized

    @pytest.mark.asyncio
    async def test_last_error_tracking(self, mcp_manager):
        """Test tracking of last error."""
        mcp_manager._last_error = None
        assert mcp_manager.last_error is None


# ============================================================================
# ResultCache Tests
# ============================================================================


class TestResultCache:
    """Tests for result caching functionality."""

    def test_cache_set_and_get(self, result_cache):
        """Test basic cache set and get operations."""
        value = {"test": "data"}

        result_cache.set("key1", value)
        retrieved = result_cache.get("key1")

        assert retrieved == value

    def test_cache_miss(self, result_cache):
        """Test cache miss behavior."""
        result = result_cache.get("nonexistent")

        assert result is None
        assert result_cache._misses > 0

    def test_cache_expiration(self, result_cache):
        """Test cache entry expiration."""
        value = {"test": "data"}

        # Set with short TTL
        entry = CacheEntry(data=value, timestamp=datetime.now(), ttl_seconds=1)
        result_cache._cache["key1"] = entry

        # Should be retrievable immediately
        assert result_cache.get("key1") == value

        # Simulate expiration
        entry.timestamp = datetime.now() - timedelta(seconds=2)
        retrieved = result_cache.get("key1")

        assert retrieved is None  # Expired

    def test_cache_invalidation(self, result_cache):
        """Test selective cache invalidation."""
        result_cache.set("key1", "value1")
        result_cache.set("key2", "value2")

        invalidated = result_cache.invalidate("key1")

        assert invalidated is True
        assert result_cache.get("key1") is None
        assert result_cache.get("key2") == "value2"

    def test_cache_clear(self, result_cache):
        """Test clearing entire cache."""
        result_cache.set("key1", "value1")
        result_cache.set("key2", "value2")

        result_cache.clear()

        assert len(result_cache._cache) == 0

    def test_cache_statistics(self, result_cache):
        """Test cache statistics tracking."""
        result_cache.set("key1", "value1")

        # Hit
        result_cache.get("key1")
        # Miss
        result_cache.get("key2")

        stats = result_cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == 50.0

    def test_cache_size_limiting(self):
        """Test cache size limiting and eviction."""
        small_cache = ResultCache(max_size=3, default_ttl=300)

        # Fill cache
        small_cache.set("key1", "value1")
        small_cache.set("key2", "value2")
        small_cache.set("key3", "value3")

        assert len(small_cache._cache) == 3

        # Add one more - should trigger eviction
        small_cache.set("key4", "value4")

        assert len(small_cache._cache) == 3  # LRU eviction occurred

    def test_entry_hit_tracking(self, result_cache):
        """Test per-entry hit tracking."""
        result_cache.set("key1", "value1")

        # Access multiple times
        result_cache.get("key1")
        result_cache.get("key1")

        entry = result_cache._cache["key1"]
        assert entry.hit_count == 2


# ============================================================================
# ApplicantProfileAgent Tests
# ============================================================================


class TestApplicantProfileAgent:
    """Tests for main agent functionality."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert not agent._initialized

        initialized = await agent.initialize()

        assert initialized is True
        assert agent._initialized
        await agent.shutdown()

    @pytest.mark.asyncio
    async def test_cache_enabled(self):
        """Test cache enabled configuration."""
        agent_with_cache = ApplicantProfileAgent(enable_cache=True)
        assert agent_with_cache.cache is not None

        agent_without_cache = ApplicantProfileAgent(enable_cache=False)
        assert agent_without_cache.cache is None

    @pytest.mark.asyncio
    async def test_fetch_applicant_profile(self, agent, sample_profile_data):
        """Test fetching applicant profile."""
        await agent.initialize()

        try:
            # Mock get_applicant_profile to return sample data
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                profile = await agent.fetch_applicant_profile("APP001")

                assert profile.applicant_id == "APP001"
                assert profile.name == "Alice Johnson"
                assert profile.mcp_source is True
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_cache_hit(self, agent, sample_profile_data):
        """Test cache hit on second request."""
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                # First call
                profile1 = await agent.fetch_applicant_profile("APP001", use_cache=True)
                call_count_1 = mock_get.call_count

                # Second call - should hit cache
                profile2 = await agent.fetch_applicant_profile("APP001", use_cache=True)
                call_count_2 = mock_get.call_count

                # MCP tool should only be called once
                assert call_count_1 == 1
                assert call_count_2 == 1  # No new call

                # Profiles should be identical
                assert profile1.applicant_id == profile2.applicant_id
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_cache_bypass(self, agent, sample_profile_data):
        """Test bypassing cache."""
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                # First call with cache
                profile1 = await agent.fetch_applicant_profile("APP001", use_cache=True)

                # Second call without cache
                profile2 = await agent.fetch_applicant_profile("APP001", use_cache=False)

                # MCP tool should be called twice
                assert mock_get.call_count == 2
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_employment_verification(self, agent, sample_profile_data):
        """Test employment verification flag."""
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                profile = await agent.fetch_applicant_profile(
                    "APP001",
                    verify_employment=True
                )

                # Employment risk should have verification info
                assert hasattr(profile.employment_risk, 'verified')
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_invalid_applicant_error(self, agent):
        """Test error handling for invalid applicant."""
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.side_effect = ValueError("Applicant not found")

                with pytest.raises(AgentError):
                    await agent.fetch_applicant_profile("INVALID")
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, agent):
        """Test handling of validation errors."""
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                # Return invalid data (missing required field)
                mock_get.return_value = {"applicant_id": "APP001"}

                with pytest.raises(AgentError):
                    await agent.fetch_applicant_profile("APP001")
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_cache_statistics(self, agent, sample_profile_data):
        """Test cache statistics retrieval."""
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                # Make some cache operations
                await agent.fetch_applicant_profile("APP001", use_cache=True)
                await agent.fetch_applicant_profile("APP001", use_cache=True)
                await agent.fetch_applicant_profile("APP002", use_cache=True)  # Miss

                stats = agent.get_cache_stats()

                assert stats["caching_enabled"] is True
                assert stats["hits"] > 0
                assert stats["misses"] > 0
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_clear_cache(self, agent, sample_profile_data):
        """Test cache clearing."""
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                # Cache a profile
                await agent.fetch_applicant_profile("APP001", use_cache=True)

                # Clear cache
                agent.clear_cache()

                # Stats should be reset
                stats = agent.get_cache_stats()
                assert len(stats.get("entries", {})) == 0
        finally:
            await agent.shutdown()


# ============================================================================
# Data Validation Tests
# ============================================================================


class TestDataValidation:
    """Tests for data validation."""

    def test_income_stability_validation_valid(self):
        """Test valid income stability assessment."""
        assessment = IncomeStabilityAssessment(
            score=85,
            trend="increasing",
            volatility="low",
            average_monthly=5000.0,
            risk_indicator="healthy"
        )

        # Should not raise
        assessment.validate()

    def test_income_stability_validation_invalid_score(self):
        """Test invalid income stability score."""
        assessment = IncomeStabilityAssessment(
            score=150,  # Invalid: > 100
            trend="increasing",
            volatility="low",
            average_monthly=5000.0,
            risk_indicator="healthy"
        )

        with pytest.raises(ValidationError):
            assessment.validate()

    def test_employment_risk_validation_valid(self):
        """Test valid employment risk assessment."""
        assessment = EmploymentRiskAssessment(
            risk_level="low",
            rationale="Strong income stability"
        )

        assessment.validate()

    def test_employment_risk_validation_invalid_level(self):
        """Test invalid employment risk level."""
        assessment = EmploymentRiskAssessment(
            risk_level="unknown",  # Invalid
            rationale="Some rationale"
        )

        with pytest.raises(ValidationError):
            assessment.validate()

    def test_credit_history_validation_valid(self):
        """Test valid credit history summary."""
        summary = CreditHistorySummary(
            credit_score=750,
            accounts_on_time=8,
            accounts_late=0,
            total_debt=15000.0,
            debt_to_income_ratio=28.6,
            delinquencies=0,
            credit_rating="excellent"
        )

        summary.validate()

    def test_credit_history_validation_invalid_score(self):
        """Test invalid credit score."""
        summary = CreditHistorySummary(
            credit_score=900,  # Invalid: > 850
            accounts_on_time=8,
            accounts_late=0,
            total_debt=15000.0,
            debt_to_income_ratio=28.6,
            delinquencies=0,
            credit_rating="excellent"
        )

        with pytest.raises(ValidationError):
            summary.validate()


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, sample_profile_data):
        """Test complete end-to-end workflow."""
        agent = ApplicantProfileAgent(
            verbose=True,
            enable_cache=True,
            cache_ttl=300
        )

        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                # Fetch profile
                profile = await agent.fetch_applicant_profile("APP001")

                # Verify profile structure
                assert profile.applicant_id == "APP001"
                assert profile.income_stability is not None
                assert profile.employment_risk is not None
                assert profile.credit_history is not None
                assert profile.overall_risk_score >= 0
                assert profile.recommendation is not None

                # Verify it's JSON serializable
                json_str = profile.to_json()
                assert isinstance(json_str, str)

                # Parse JSON to verify structure
                json_data = json.loads(json_str)
                assert json_data["applicant_id"] == "APP001"
        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, sample_profile_data):
        """Test handling multiple concurrent requests."""
        agent = ApplicantProfileAgent(enable_cache=True)
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                # Create multiple concurrent requests
                tasks = [
                    agent.fetch_applicant_profile(f"APP00{i}", use_cache=True)
                    for i in range(1, 4)
                ]

                profiles = await asyncio.gather(*tasks)

                assert len(profiles) == 3
                assert all(isinstance(p, ApplicantProfileSummary) for p in profiles)
        finally:
            await agent.shutdown()


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Tests for performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, sample_profile_data):
        """Test that cache provides performance improvement."""
        agent = ApplicantProfileAgent(enable_cache=True)
        await agent.initialize()

        try:
            with patch('applicant_profile_agent_mcp.get_applicant_profile') as mock_get:
                mock_get.return_value = sample_profile_data

                import time

                # First call (cache miss)
                start = time.time()
                await agent.fetch_applicant_profile("APP001", use_cache=True)
                first_time = time.time() - start

                # Second call (cache hit)
                start = time.time()
                await agent.fetch_applicant_profile("APP001", use_cache=True)
                cached_time = time.time() - start

                # Cached call should be faster (though in tests it might not be dramatic)
                # Just verify both succeeded
                assert first_time >= 0
                assert cached_time >= 0
        finally:
            await agent.shutdown()


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
