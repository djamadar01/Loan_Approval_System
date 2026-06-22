# Integration Main - System Entry Point Guide

## Overview

`integration_main.py` is the single entry point for the entire loan decision system. It orchestrates:

1. **MCP Server Initialization** (Ports 8001-8004)
2. **LangGraph Orchestrator** Setup
3. **FastAPI Application** (Port 8000)
4. **Connection Verification**
5. **Health Status Reporting**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         FastAPI Main Application (Port 8000)             │
│  - REST API endpoints                                    │
│  - Health checks                                         │
│  - Application submission                               │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Orchestrator │ │ MCP Manager  │ │ Health Mgr   │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │
        └──────┬───────┴────────────┬───────┐
               ▼                    ▼       ▼
        ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
        │ Applicant  │ │ RiskRules  │ │Notification│ │ Decision   │
        │ DB Server  │ │ DB Server  │ │   Server   │ │ Synthesis  │
        │ (8001)     │ │ (8002)     │ │   (8003)   │ │   (8004)   │
        └────────────┘ └────────────┘ └────────────┘ └────────────┘
```

## MCP Servers Configuration

| Server | Port | Module | Purpose |
|--------|------|--------|---------|
| ApplicantDB | 8001 | `applicantdb_mcp_server_enhanced` | Applicant profile management |
| RiskRulesDB | 8002 | `riskrulesdb_enhanced_server` | Risk assessment rules |
| NotificationSystem | 8003 | `notification_system_enhanced` | Notification & audit tracking |
| DecisionSynthesis | 8004 | `decision_synthesis_enhanced` | Decision synthesis engine |

## Starting the System

### Basic Usage

```bash
cd /home/ubuntu/Desktop/demo
python3 integration_main.py
```

### Expected Startup Sequence

```
================================================================================
STARTING INTEGRATED LOAN DECISION SYSTEM
================================================================================
Starting all MCP servers...
Starting ApplicantDB MCP Server on port 8001...
Started ApplicantDB MCP Server process (PID: 12345)
ApplicantDB MCP Server is ready
...
[repeat for other servers]

Initializing LangGraph Orchestrator...
Orchestrator ready with 4/4 servers

================================================================================
SYSTEM STATUS
================================================================================
FastAPI running on: http://0.0.0.0:8000

MCP Servers:
  - ApplicantDB MCP Server: http://localhost:8001
  - RiskRulesDB MCP Server: http://localhost:8002
  - NotificationSystem MCP Server: http://localhost:8003
  - Decision Synthesis MCP Server: http://localhost:8004

System is ready. Access:
  Health Check: http://localhost:8000/health
  System Status: http://localhost:8000/status
  Detailed Health: http://localhost:8000/health/detailed
================================================================================
```

## API Endpoints

### Health & Status

#### GET `/health`
Basic health check - confirms API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-20T15:30:45.123456",
  "service": "Loan Decision System"
}
```

#### GET `/status`
Detailed system status with component health.

#### GET `/health/detailed`
Comprehensive health details for all components.

### Application Processing

#### POST `/applications/submit`
Submit a new loan application for processing.

#### GET `/applications/{application_id}`
Get the status of a loan application.

### System Control

#### POST `/system/restart`
Restart all MCP servers (graceful restart).

#### GET `/system/info`
Get general system information.

## Component Status Levels

### Overall Status
- **healthy**: All components running and responsive
- **degraded**: 3/4 components healthy (1 allowed down)
- **critical**: 2 or fewer components healthy
- **offline**: No components responding

### Component Status
- **running**: Process is active
- **healthy**: Server is responding to health checks
- **unhealthy**: Server not responding correctly
- **error**: Server encountered an error
- **unknown**: Status could not be determined

## Configuration

### Constants (Adjustable)
Edit `integration_main.py` to modify:

```python
# MCP server ports
MCP_SERVERS = {
    "applicant_db": {"port": 8001, ...},
    "risk_rules_db": {"port": 8002, ...},
    "notification_system": {"port": 8003, ...},
    "decision_synthesis": {"port": 8004, ...}
}

# FastAPI configuration
FASTAPI_PORT = 8000
FASTAPI_HOST = "0.0.0.0"

# Timeouts and retry logic
CONNECTION_TIMEOUT = 5.0
HEALTH_CHECK_INTERVAL = 30
MAX_RETRIES = 3
RETRY_DELAY = 2
```

## Troubleshooting

### Port Already in Use
If a port is already in use, the system will:
1. Detect the port is in use
2. Assume the server is already running
3. Continue with system initialization

To free a port:
```bash
# Find process on port 8001
lsof -i :8001

# Kill the process
kill -9 <PID>
```

### MCP Server Won't Start
1. Check logs for specific error
2. Verify the module name is correct
3. Ensure dependencies are installed

### System Degraded
If system status shows "degraded":
1. Check individual server status with `/health/detailed`
2. Use `/system/restart` to restart all servers
3. Monitor logs for errors

## Performance Characteristics

### Startup Time
- **MCP Server initialization**: ~2-5 seconds per server
- **Total startup time**: ~10-15 seconds (parallel initialization)
- **Health check timeout**: 5 seconds per server attempt

### Health Check Performance
- **Individual server check**: ~50-100ms
- **Full system health check**: ~200-500ms (parallel)

## Dependencies

Required packages:
```
fastapi >= 0.104.0
uvicorn >= 0.24.0
httpx >= 0.25.0
```

## Next Steps

1. **Deploy**: Run `python3 integration_main.py` in production environment
2. **Monitor**: Use `/health/detailed` for continuous monitoring
3. **Scale**: Use `/system/restart` for zero-downtime updates
4. **Extend**: Add custom MCP servers by following the pattern
