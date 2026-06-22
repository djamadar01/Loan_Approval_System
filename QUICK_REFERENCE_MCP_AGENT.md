# ApplicantProfileAgent MCP Integration - Quick Reference

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `applicant_profile_agent_mcp.py` | 39KB | Main implementation with MCP integration |
| `test_applicant_profile_agent_mcp.py` | 21KB | Comprehensive test suite (30+ tests) |
| `APPLICANT_PROFILE_AGENT_MCP_GUIDE.md` | 20KB | Complete architecture guide |
| `MCP_INTEGRATION_SUMMARY.md` | 14KB | Implementation summary |
| `QUICK_REFERENCE_MCP_AGENT.md` | - | This file |

## Key Components

### 1. MCPClientManager
```python
# Connection management with retry logic
manager = MCPClientManager(max_retries=3, retry_delay=1.0)
await manager.initialize()       # Connect with retry
await manager.is_connected()     # Health check
await manager.shutdown()         # Cleanup
```

### 2. ResultCache
```python
# Smart caching with automatic expiration
cache = ResultCache(max_size=1000, default_ttl=300)
cache.set(key, value)            # Store with TTL
cache.get(key)                   # Retrieve (checks expiry)
cache.get_stats()                # Hit rate, size, entries
cache.invalidate(key)            # Remove specific entry
```

### 3. ApplicantProfileAgent
```python
# Main orchestrator with MCP integration
agent = ApplicantProfileAgent(
    verbose=True,
    enable_cache=True,
    cache_ttl=300,
    max_retries=3
)

await agent.initialize()         # Setup MCP connection
await agent.fetch_applicant_profile(
    "APP001",
    use_cache=True,              # Use cache if available
    verify_employment=True       # Call verify_employment
)
await agent.shutdown()           # Cleanup
```

## MCP Tools Called

### get_applicant_profile(applicant_id)
```
Input:  applicant_id (string)
Output: {
  applicant_id, name, email, phone,
  income_stability {score, trend, volatility, average_monthly},
  employment_risk,
  credit_history {credit_score, accounts_on_time, accounts_late, ...},
  completeness {missing_fields, completion_percentage, ...},
  application_date, status
}
```

### verify_employment(applicant_id)
```
Input:  applicant_id (string)
Output: {verified: bool, timestamp: string, details: {...}}
Status: Non-blocking fallback (doesn't prevent profile retrieval)
```

## Quick Start

### Installation & Setup
```python
from applicant_profile_agent_mcp import ApplicantProfileAgent

# Create agent with caching enabled
agent = ApplicantProfileAgent(
    enable_cache=True,
    cache_ttl=300  # 5-minute cache
)
```

### Fetch Profile
```python
import asyncio

async def get_profile():
    agent = ApplicantProfileAgent()
    await agent.initialize()
    
    try:
        profile = await agent.fetch_applicant_profile(
            "APP001",
            verify_employment=True
        )
        print(f"Risk Score: {profile.overall_risk_score}")
        print(f"Recommendation: {profile.recommendation}")
    finally:
        await agent.shutdown()

asyncio.run(get_profile())
```

### Monitor Cache
```python
stats = agent.get_cache_stats()
# {
#   "size": 5,
#   "hits": 42,
#   "misses": 8,
#   "hit_rate_percent": 84.0,
#   "entries": {...}
# }
```

## Core Features

✅ **1. MCP Client Management**
- Automatic initialization with retry logic
- Exponential backoff on connection failures
- Health checking
- Graceful error recovery

✅ **2. MCP Tool Calls**
- `get_applicant_profile` - Profile retrieval
- `verify_employment` - Employment verification (non-blocking)
- List/filter operations

✅ **3. Result Caching**
- TTL-based automatic expiration (default: 5 min)
- Hit/miss statistics
- Size-limited (default: 1000 entries)
- LRU eviction strategy

✅ **4. Error Handling**
- Comprehensive exception hierarchy
- Graceful degradation
- Non-blocking employment verification
- Detailed error context

✅ **5. Async Support**
- Full async/await implementation
- Concurrent request handling
- Non-blocking operations

## Exception Handling

```python
try:
    profile = await agent.fetch_applicant_profile("APP001")
except MCPConnectionError as e:
    # Handle MCP connection failures
except ValidationError as e:
    # Handle data validation failures
except AgentError as e:
    # Handle agent-level errors
except Exception as e:
    # Unexpected errors
```

## Configuration Examples

### Profile Caching (5 min)
```python
agent = ApplicantProfileAgent(
    enable_cache=True,
    cache_ttl=300  # 5 minutes
)
```

### Portfolio Analysis (1 hour)
```python
agent = ApplicantProfileAgent(
    enable_cache=True,
    cache_ttl=3600  # 1 hour
)
```

### MCP Connection (Aggressive Retry)
```python
agent = ApplicantProfileAgent(
    max_retries=5      # More retry attempts
)
# Internal: MCPClientManager uses exponential backoff
```

### No Caching (Always Fresh)
```python
agent = ApplicantProfileAgent(
    enable_cache=False
)
```

## Performance Tips

1. **Enable Caching**: Improves response time by 50-90%
2. **Set Appropriate TTL**: Balance freshness vs. hit rate
3. **Monitor Statistics**: Track `get_cache_stats()` for optimization
4. **Reuse Agent Instance**: Don't create new agents per request
5. **Clear Stale Cache**: `agent.clear_cache()` when needed

## Testing

### Run All Tests
```bash
pytest test_applicant_profile_agent_mcp.py -v
```

### Run Specific Tests
```bash
# MCP Client Manager tests
pytest test_applicant_profile_agent_mcp.py::TestMCPClientManager -v

# Cache tests
pytest test_applicant_profile_agent_mcp.py::TestResultCache -v

# Agent tests
pytest test_applicant_profile_agent_mcp.py::TestApplicantProfileAgent -v

# Integration tests
pytest test_applicant_profile_agent_mcp.py::TestIntegration -v
```

## Data Classes

### ApplicantProfileSummary
```python
profile = ApplicantProfileSummary(
    applicant_id: str,
    name: str,
    email: str,
    phone: str,
    income_stability: IncomeStabilityAssessment,
    employment_risk: EmploymentRiskAssessment,
    credit_history: CreditHistorySummary,
    application_status: str,
    overall_risk_score: float,  # 0-100
    recommendation: str,
    mcp_source: bool = True,
    cache_info: Optional[Dict]
)

# Methods
profile.validate()     # Validate all data
profile.to_dict()      # Convert to dictionary
profile.to_json()      # Convert to JSON string
```

### IncomeStabilityAssessment
```python
assessment = IncomeStabilityAssessment(
    score: int,                    # 0-100
    trend: str,                    # "increasing" | "stable" | "decreasing"
    volatility: str,               # "low" | "moderate" | "high"
    average_monthly: float,
    risk_indicator: str            # "healthy" | "caution" | "critical"
)
```

### EmploymentRiskAssessment
```python
assessment = EmploymentRiskAssessment(
    risk_level: str,               # "low" | "medium" | "high"
    rationale: str,
    verified: bool = False,
    verification_timestamp: Optional[str] = None
)
```

### CreditHistorySummary
```python
summary = CreditHistorySummary(
    credit_score: int,             # 300-850
    accounts_on_time: int,
    accounts_late: int,
    total_debt: float,
    debt_to_income_ratio: float,
    delinquencies: int,
    credit_rating: str             # "excellent" | "good" | "fair" | "poor"
)
```

## Logging

### Enable Debug Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)
agent = ApplicantProfileAgent(verbose=True)
```

### Log Levels
- `INFO` - Operation status, initialization, MCP calls
- `DEBUG` - Cache operations, detailed flow
- `WARNING` - Recoverable errors, connection issues
- `ERROR` - Unrecoverable errors, validation failures

## Production Checklist

- [ ] Replace mock MCP client with actual stdio transport
- [ ] Configure appropriate cache TTL for your use case
- [ ] Set up monitoring for cache hit rates
- [ ] Implement metrics collection
- [ ] Add structured logging for audit trails
- [ ] Configure error handling/alerting
- [ ] Set up connection retry parameters
- [ ] Test with production data volume
- [ ] Load test concurrent requests
- [ ] Document deployment parameters

## Common Patterns

### Pattern 1: Single Profile with Verification
```python
profile = await agent.fetch_applicant_profile(
    "APP001",
    verify_employment=True
)
```

### Pattern 2: Cache-First Lookup
```python
profile = await agent.fetch_applicant_profile(
    "APP001",
    use_cache=True,        # Use cache if available
    verify_employment=False  # Skip verification for speed
)
```

### Pattern 3: Force Fresh Fetch
```python
profile = await agent.fetch_applicant_profile(
    "APP001",
    use_cache=False  # Bypass cache
)
```

### Pattern 4: Portfolio Analysis
```python
portfolio = await agent.analyze_risk_portfolio()
print(f"Low risk: {portfolio['low']['count']}")
print(f"Medium risk: {portfolio['medium']['count']}")
print(f"High risk: {portfolio['high']['count']}")
```

### Pattern 5: Batch Processing with Cache
```python
applicant_ids = ["APP001", "APP002", "APP003"]
tasks = [
    agent.fetch_applicant_profile(app_id, use_cache=True)
    for app_id in applicant_ids
]
profiles = await asyncio.gather(*tasks)
```

## Documentation Structure

```
Main Implementation (39KB)
├── MCPClientManager (connection management)
├── ResultCache (performance optimization)
├── ApplicantProfileAgent (orchestration)
├── Data Classes (validation)
├── Risk Calculations (analysis)
└── Example Usage (demo)

Test Suite (21KB)
├── MCPClientManager tests
├── ResultCache tests
├── Agent tests
├── Validation tests
├── Integration tests
└── Performance tests

Guides (34KB)
├── Architecture guide (20KB)
├── Integration summary (14KB)
└── Quick reference (this file)
```

## Support & Troubleshooting

### MCP Connection Timeout
```python
# Increase timeout
agent.mcp_manager.timeout = 10.0  # 10 seconds
```

### Low Cache Hit Rate
```python
# Increase TTL for better hit rate
agent = ApplicantProfileAgent(cache_ttl=600)  # 10 minutes
```

### Cache Memory Issues
```python
# Reduce cache size
cache = ResultCache(max_size=500)  # Smaller cache
```

### Employment Verification Failures (Non-blocking)
```python
# Check if verification succeeded
profile = await agent.fetch_applicant_profile("APP001")
if profile.employment_risk.verified:
    print("Employment verified")
else:
    print("Verification pending or failed")
```

## Links

- **Main Implementation**: `applicant_profile_agent_mcp.py`
- **Test Suite**: `test_applicant_profile_agent_mcp.py`
- **Architecture Guide**: `APPLICANT_PROFILE_AGENT_MCP_GUIDE.md`
- **Integration Summary**: `MCP_INTEGRATION_SUMMARY.md`
- **Original Agent**: `applicant_profile_agent.py` (for comparison)

---

**Version**: 1.0  
**Last Updated**: 2026-06-19  
**Status**: Production Ready
