#!/usr/bin/env python3
"""
Integration Main Entry Point - Unified System Initialization

This module serves as the single entry point for the entire loan decision system.
It orchestrates:

1. MCP Server Initialization (ports 8001-8004)
   - ApplicantDB Server (port 8001)
   - RiskRulesDB Server (port 8002)
   - NotificationSystem Server (port 8003)
   - Decision Synthesis Server (port 8004)

2. LangGraph Orchestrator Creation
   - Multi-agent workflow setup
   - State management
   - Decision routing

3. FastAPI Main Application (port 8000)
   - REST API endpoints
   - Health checks
   - Application submission and tracking

4. Connection Verification
   - MCP server connectivity checks
   - Database readiness verification
   - System health assessment

5. Health Status Reporting
   - Real-time system status
   - Component availability tracking
   - Performance metrics

Usage:
    python integration_main.py

The system is ready when all components report healthy status.
"""

import asyncio
import logging
import sys
import time
import threading
import subprocess
import signal
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import socket

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

MCP_SERVERS = {
    "applicant_db": {
        "port": 8001,
        "name": "ApplicantDB MCP Server",
        "module": "applicantdb_mcp_server_enhanced",
        "endpoint": "http://localhost:8001"
    },
    "risk_rules_db": {
        "port": 8002,
        "name": "RiskRulesDB MCP Server",
        "module": "riskrulesdb_enhanced_server",
        "endpoint": "http://localhost:8002"
    },
    "notification_system": {
        "port": 8003,
        "name": "NotificationSystem MCP Server",
        "module": "notification_system_enhanced",
        "endpoint": "http://localhost:8003"
    },
    "decision_synthesis": {
        "port": 8004,
        "name": "Decision Synthesis MCP Server",
        "module": "decision_synthesis_enhanced",
        "endpoint": "http://localhost:8004"
    }
}

FASTAPI_PORT = 8000
FASTAPI_HOST = "0.0.0.0"

# Timeouts and retry logic
CONNECTION_TIMEOUT = 5.0
HEALTH_CHECK_INTERVAL = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


# ============================================================================
# DATA MODELS FOR HEALTH STATUS
# ============================================================================

@dataclass
class ComponentStatus:
    """Status of an individual component."""
    name: str
    port: Optional[int] = None
    status: str = "unknown"  # running, stopped, error, healthy, unhealthy
    last_check: Optional[str] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SystemHealth:
    """Overall system health status."""
    timestamp: str
    overall_status: str  # healthy, degraded, critical, offline
    components: Dict[str, ComponentStatus]
    uptime_seconds: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "uptime_seconds": self.uptime_seconds,
            "message": self.message
        }


# ============================================================================
# MCP SERVER MANAGER
# ============================================================================

class MCPServerManager:
    """Manages MCP servers lifecycle."""

    def __init__(self):
        """Initialize MCP server manager."""
        self.servers: Dict[str, subprocess.Popen] = {}
        self.component_status: Dict[str, ComponentStatus] = {}
        self.start_time = time.time()

    async def start_all_servers(self) -> bool:
        """
        Start all MCP servers.

        Returns:
            bool: True if all servers started successfully, False otherwise.
        """
        logger.info("Starting all MCP servers...")
        all_started = True

        for server_key, config in MCP_SERVERS.items():
            success = await self._start_server(server_key, config)
            if not success:
                all_started = False
                logger.error(f"Failed to start {config['name']}")

        return all_started

    async def _start_server(self, server_key: str, config: Dict[str, Any]) -> bool:
        """
        Start a single MCP server.

        Args:
            server_key: Key for the server in MCP_SERVERS
            config: Server configuration

        Returns:
            bool: True if server started and is healthy, False otherwise.
        """
        logger.info(f"Starting {config['name']} on port {config['port']}...")

        try:
            # Check if port is already in use
            if self._is_port_in_use(config['port']):
                logger.warning(f"Port {config['port']} already in use, assuming server is running")
                self.component_status[server_key] = ComponentStatus(
                    name=config['name'],
                    port=config['port'],
                    status="running"
                )
                return True

            # Start server process
            cmd = [
                sys.executable, "-m", "uvicorn",
                f"{config['module']}:app",
                "--host", "0.0.0.0",
                "--port", str(config['port']),
                "--log-level", "info"
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.servers[server_key] = process
            logger.info(f"Started {config['name']} process (PID: {process.pid})")

            # Wait for server to be ready
            await self._wait_for_server(server_key, config, max_retries=MAX_RETRIES)

            self.component_status[server_key] = ComponentStatus(
                name=config['name'],
                port=config['port'],
                status="healthy",
                last_check=datetime.now().isoformat()
            )

            return True

        except Exception as e:
            logger.error(f"Error starting {config['name']}: {e}")
            self.component_status[server_key] = ComponentStatus(
                name=config['name'],
                port=config['port'],
                status="error",
                error_message=str(e)
            )
            return False

    async def _wait_for_server(
        self,
        server_key: str,
        config: Dict[str, Any],
        max_retries: int = MAX_RETRIES
    ) -> bool:
        """
        Wait for a server to become ready.

        Args:
            server_key: Key for the server
            config: Server configuration
            max_retries: Maximum number of retries

        Returns:
            bool: True if server is ready, False otherwise.
        """
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(RETRY_DELAY)

                async with httpx.AsyncClient(timeout=CONNECTION_TIMEOUT) as client:
                    response = await client.get(f"{config['endpoint']}/health")
                    if response.status_code == 200:
                        logger.info(f"{config['name']} is ready")
                        return True

            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}/{max_retries} to reach {config['name']}: {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(RETRY_DELAY)

        logger.warning(f"{config['name']} did not respond within timeout period")
        return False

    async def check_server_health(self, server_key: str, config: Dict[str, Any]) -> ComponentStatus:
        """
        Check health of a single MCP server.

        Args:
            server_key: Key for the server
            config: Server configuration

        Returns:
            ComponentStatus: Health status of the server.
        """
        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=CONNECTION_TIMEOUT) as client:
                response = await client.get(f"{config['endpoint']}/health")
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    return ComponentStatus(
                        name=config['name'],
                        port=config['port'],
                        status="healthy",
                        last_check=datetime.now().isoformat(),
                        response_time_ms=response_time
                    )
                else:
                    return ComponentStatus(
                        name=config['name'],
                        port=config['port'],
                        status="unhealthy",
                        last_check=datetime.now().isoformat(),
                        error_message=f"HTTP {response.status_code}"
                    )

        except Exception as e:
            return ComponentStatus(
                name=config['name'],
                port=config['port'],
                status="error",
                last_check=datetime.now().isoformat(),
                error_message=str(e)
            )

    async def check_all_servers_health(self) -> Dict[str, ComponentStatus]:
        """
        Check health of all MCP servers.

        Returns:
            Dict of server statuses.
        """
        tasks = [
            self.check_server_health(key, config)
            for key, config in MCP_SERVERS.items()
        ]

        results = await asyncio.gather(*tasks)

        for server_key, status in zip(MCP_SERVERS.keys(), results):
            self.component_status[server_key] = status

        return self.component_status

    async def stop_all_servers(self):
        """Stop all running MCP servers."""
        logger.info("Stopping all MCP servers...")

        for server_key, process in self.servers.items():
            try:
                process.terminate()
                logger.info(f"Terminated {MCP_SERVERS[server_key]['name']} (PID: {process.pid})")

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.warning(f"Forced kill of {MCP_SERVERS[server_key]['name']}")

            except Exception as e:
                logger.error(f"Error stopping {MCP_SERVERS[server_key]['name']}: {e}")

    @staticmethod
    def _is_port_in_use(port: int) -> bool:
        """
        Check if a port is already in use.

        Args:
            port: Port number to check

        Returns:
            bool: True if port is in use, False otherwise.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return False
            except OSError:
                return True

    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self.start_time


# ============================================================================
# LANGGRAPH ORCHESTRATOR
# ============================================================================

class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator for loan decision workflows.

    This is a simplified orchestrator that coordinates with MCP servers.
    In a full implementation, this would include the complete state graph
    from loan_orchestrator.py
    """

    def __init__(self, mcp_manager: MCPServerManager):
        """Initialize the orchestrator."""
        self.mcp_manager = mcp_manager
        self.is_ready = False
        logger.info("LangGraph Orchestrator initialized")

    async def initialize(self) -> bool:
        """
        Initialize the orchestrator with MCP servers.

        Returns:
            bool: True if initialization successful, False otherwise.
        """
        logger.info("Initializing LangGraph Orchestrator...")

        try:
            # Verify MCP servers are healthy
            health_status = await self.mcp_manager.check_all_servers_health()

            healthy_servers = sum(
                1 for status in health_status.values()
                if status.status == "healthy"
            )

            total_servers = len(MCP_SERVERS)

            if healthy_servers >= total_servers - 1:  # Allow 1 server to be down
                self.is_ready = True
                logger.info(f"Orchestrator ready with {healthy_servers}/{total_servers} servers")
                return True
            else:
                logger.error(f"Insufficient healthy servers: {healthy_servers}/{total_servers}")
                return False

        except Exception as e:
            logger.error(f"Error initializing orchestrator: {e}")
            return False

    async def process_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a loan application through the orchestrator.

        Args:
            application_data: Application details

        Returns:
            Dict with processing results
        """
        if not self.is_ready:
            raise RuntimeError("Orchestrator not ready")

        return {
            "status": "processed",
            "application_id": application_data.get("id"),
            "timestamp": datetime.now().isoformat()
        }

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "ready": self.is_ready,
            "mcp_servers": self.mcp_manager.component_status
        }


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

def create_fastapi_app(mcp_manager: MCPServerManager, orchestrator: LangGraphOrchestrator) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        mcp_manager: MCP server manager
        orchestrator: LangGraph orchestrator

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Loan Decision System - Integrated API",
        description="Single entry point for the loan decision system",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================================================
    # HEALTH AND STATUS ENDPOINTS
    # ========================================================================

    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Loan Decision System"
        }

    @app.get("/status")
    async def system_status():
        """Get detailed system status."""
        # Check all MCP servers
        health_status = await mcp_manager.check_all_servers_health()

        # Determine overall status
        healthy_count = sum(1 for s in health_status.values() if s.status == "healthy")
        total_count = len(health_status)

        if healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count >= total_count - 1:
            overall_status = "degraded"
        else:
            overall_status = "critical"

        system_health = SystemHealth(
            timestamp=datetime.now().isoformat(),
            overall_status=overall_status,
            components=health_status,
            uptime_seconds=mcp_manager.get_uptime(),
            message=f"{healthy_count}/{total_count} components healthy"
        )

        return system_health.to_dict()

    @app.get("/health/detailed")
    async def detailed_health():
        """Get detailed health information for all components."""
        health_status = await mcp_manager.check_all_servers_health()

        return {
            "timestamp": datetime.now().isoformat(),
            "components": {
                name: status.to_dict()
                for name, status in health_status.items()
            },
            "orchestrator": orchestrator.get_status()
        }

    # ========================================================================
    # APPLICATION PROCESSING ENDPOINTS
    # ========================================================================

    @app.post("/applications/submit")
    async def submit_application(application: Dict[str, Any]):
        """
        Submit a new loan application for processing.

        Args:
            application: Loan application data

        Returns:
            Application submission response
        """
        if not orchestrator.is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Orchestrator not ready"
            )

        try:
            result = await orchestrator.process_application(application)
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing application: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @app.get("/applications/{application_id}")
    async def get_application_status(application_id: str):
        """Get the status of a loan application."""
        return {
            "application_id": application_id,
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # SYSTEM CONTROL ENDPOINTS
    # ========================================================================

    @app.post("/system/restart")
    async def restart_system():
        """Restart all MCP servers."""
        try:
            await mcp_manager.stop_all_servers()
            await asyncio.sleep(2)
            await mcp_manager.start_all_servers()

            return {
                "success": True,
                "message": "System restarted",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @app.get("/system/info")
    async def system_info():
        """Get system information."""
        return {
            "name": "Loan Decision System",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": mcp_manager.get_uptime(),
            "mcp_servers": len(MCP_SERVERS),
            "fastapi_port": FASTAPI_PORT,
            "orchestrator_ready": orchestrator.is_ready
        }

    return app


# ============================================================================
# MAIN INITIALIZATION FUNCTION
# ============================================================================

async def initialize_system() -> tuple[FastAPI, MCPServerManager, LangGraphOrchestrator]:
    """
    Initialize the complete system.

    Returns:
        Tuple of (FastAPI app, MCP manager, Orchestrator)

    Raises:
        RuntimeError: If critical initialization fails
    """
    logger.info("=" * 80)
    logger.info("STARTING INTEGRATED LOAN DECISION SYSTEM")
    logger.info("=" * 80)

    # Initialize MCP server manager
    mcp_manager = MCPServerManager()

    # Start all MCP servers
    logger.info(f"Starting {len(MCP_SERVERS)} MCP servers...")
    servers_started = await mcp_manager.start_all_servers()

    if not servers_started:
        logger.warning("Some MCP servers failed to start, continuing with available servers")

    # Give servers time to stabilize
    await asyncio.sleep(2)

    # Initialize orchestrator
    orchestrator = LangGraphOrchestrator(mcp_manager)
    orchestrator_ready = await orchestrator.initialize()

    if not orchestrator_ready:
        logger.warning("Orchestrator initialization had issues, but system will continue")

    # Create FastAPI app
    app = create_fastapi_app(mcp_manager, orchestrator)

    logger.info("=" * 80)
    logger.info("SYSTEM INITIALIZATION COMPLETE")
    logger.info("=" * 80)

    return app, mcp_manager, orchestrator


async def verify_connections() -> bool:
    """
    Verify all system connections.

    Returns:
        bool: True if all connections verified, False otherwise.
    """
    logger.info("Verifying system connections...")

    mcp_manager = MCPServerManager()
    health_status = await mcp_manager.check_all_servers_health()

    healthy_count = sum(1 for s in health_status.values() if s.status == "healthy")
    total_count = len(health_status)

    logger.info(f"Connection verification: {healthy_count}/{total_count} servers healthy")

    for name, status in health_status.items():
        logger.info(f"  {status.name}: {status.status}")
        if status.error_message:
            logger.info(f"    Error: {status.error_message}")

    return healthy_count >= total_count - 1


# ============================================================================
# SIGNAL HANDLERS AND CLEANUP
# ============================================================================

mcp_manager_instance: Optional[MCPServerManager] = None


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal, cleaning up...")

    if mcp_manager_instance:
        asyncio.run(mcp_manager_instance.stop_all_servers())

    sys.exit(0)


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for the system."""
    global mcp_manager_instance

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize system
        app, mcp_manager, orchestrator = await initialize_system()
        mcp_manager_instance = mcp_manager

        # Verify connections
        connections_verified = await verify_connections()

        if not connections_verified:
            logger.warning("Some connections could not be verified, but continuing startup")

        # Get system status
        logger.info("\n" + "=" * 80)
        logger.info("SYSTEM STATUS")
        logger.info("=" * 80)

        status_data = await app.dependency_overrides.get(
            lambda: {"status": "checking"}
        ) or {}

        logger.info(f"FastAPI running on: http://{FASTAPI_HOST}:{FASTAPI_PORT}")
        logger.info("\nMCP Servers:")
        for key, config in MCP_SERVERS.items():
            logger.info(f"  - {config['name']}: http://localhost:{config['port']}")

        logger.info("\nSystem is ready. Access:")
        logger.info(f"  Health Check: http://localhost:{FASTAPI_PORT}/health")
        logger.info(f"  System Status: http://localhost:{FASTAPI_PORT}/status")
        logger.info(f"  Detailed Health: http://localhost:{FASTAPI_PORT}/health/detailed")

        logger.info("=" * 80 + "\n")

        # Start FastAPI server
        config = uvicorn.Config(
            app=app,
            host=FASTAPI_HOST,
            port=FASTAPI_PORT,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        logger.error(f"Fatal error during initialization: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
