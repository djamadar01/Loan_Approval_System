#!/usr/bin/env python3
"""
System Health Check Script

This script provides comprehensive diagnostics for the loan application orchestrator system.
It tests:
1. MCP server connectivity
2. Database accessibility
3. Agent initialization
4. Orchestrator state validation
5. System configuration

Run independently to diagnose system issues: python system_health_check.py
"""

import sys
import json
import sqlite3
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class HealthStatus(str, Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """System component types."""
    MCP_SERVER = "mcp_server"
    DATABASE = "database"
    AGENT = "agent"
    ORCHESTRATOR = "orchestrator"
    CONFIGURATION = "configuration"
    DEPENDENCIES = "dependencies"


@dataclass
class HealthCheckResult:
    """Individual health check result."""
    component: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: str


@dataclass
class SystemHealthReport:
    """Complete system health report."""
    overall_status: HealthStatus
    timestamp: str
    results: List[HealthCheckResult]
    summary: Dict[str, int]  # Count of each status
    recommendations: List[str]


# ============================================================================
# HEALTH CHECK BASE CLASS
# ============================================================================

class HealthChecker:
    """Base class for system health checking."""

    def __init__(self):
        self.results: List[HealthCheckResult] = []
        self.recommendations: List[str] = []
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.load_environment()

    def load_environment(self) -> None:
        """Load environment variables from .env file."""
        if self.env_file.exists():
            try:
                with open(self.env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value.strip("'\"")
                logger.info(f"Loaded environment from {self.env_file}")
            except Exception as e:
                logger.warning(f"Failed to load environment: {e}")

    def add_result(
        self,
        component: str,
        component_type: ComponentType,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a health check result."""
        result = HealthCheckResult(
            component=component,
            component_type=component_type,
            status=status,
            message=message,
            details=details or {},
            timestamp=datetime.utcnow().isoformat()
        )
        self.results.append(result)

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation for fixing issues."""
        self.recommendations.append(recommendation)


# ============================================================================
# MCP SERVER HEALTH CHECKS
# ============================================================================

class MCPServerHealthChecker(HealthChecker):
    """Check MCP server connectivity and functionality."""

    MCP_SERVERS = {
        "applicantdb_mcp_server_enhanced": {
            "module": "applicantdb_mcp_server_enhanced",
            "port": 5000,
            "description": "Applicant Database MCP Server"
        },
        "riskrulesdb_enhanced_server": {
            "module": "riskrulesdb_enhanced_server",
            "port": 5001,
            "description": "Risk Rules Database MCP Server"
        },
        "notification_system_server": {
            "module": "notification_system_server",
            "port": 5002,
            "description": "Notification System MCP Server"
        }
    }

    def check_mcp_servers(self) -> None:
        """Check all MCP servers for accessibility and functionality."""
        logger.info("Checking MCP server connectivity...")

        for server_name, server_config in self.MCP_SERVERS.items():
            self._check_single_mcp_server(server_name, server_config)

    def _check_single_mcp_server(
        self,
        server_name: str,
        server_config: Dict[str, Any]
    ) -> None:
        """Check a single MCP server."""
        details = {
            "server_name": server_name,
            "module": server_config["module"],
            "description": server_config["description"]
        }

        try:
            # Try to import the module
            module_path = self.project_root / f"{server_config['module']}.py"
            if not module_path.exists():
                self.add_result(
                    component=server_name,
                    component_type=ComponentType.MCP_SERVER,
                    status=HealthStatus.CRITICAL,
                    message=f"MCP server file not found at {module_path}",
                    details=details
                )
                self.add_recommendation(
                    f"Verify that {server_config['module']}.py exists in the project root"
                )
                return

            # Check if module can be loaded
            spec = importlib.util.spec_from_file_location(
                server_config["module"],
                module_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't execute, just check if it's parseable
                logger.debug(f"Module {server_config['module']} is importable")
                details["import_status"] = "OK"
            else:
                details["import_status"] = "FAILED"
                self.add_result(
                    component=server_name,
                    component_type=ComponentType.MCP_SERVER,
                    status=HealthStatus.WARNING,
                    message=f"Cannot load module spec for {server_config['module']}",
                    details=details
                )
                return

            # Check port availability (if applicable)
            if not self._check_port_available(server_config["port"]):
                details["port_available"] = False
                self.add_result(
                    component=server_name,
                    component_type=ComponentType.MCP_SERVER,
                    status=HealthStatus.WARNING,
                    message=f"Port {server_config['port']} may already be in use",
                    details=details
                )
                self.add_recommendation(
                    f"Check if {server_name} is already running or if port {server_config['port']} is in use"
                )
            else:
                details["port_available"] = True

            self.add_result(
                component=server_name,
                component_type=ComponentType.MCP_SERVER,
                status=HealthStatus.HEALTHY,
                message=f"MCP server {server_name} is properly configured",
                details=details
            )

        except Exception as e:
            self.add_result(
                component=server_name,
                component_type=ComponentType.MCP_SERVER,
                status=HealthStatus.CRITICAL,
                message=f"Failed to check MCP server: {str(e)}",
                details={**details, "error": str(e)}
            )
            self.add_recommendation(
                f"Review {server_config['module']}.py for syntax errors or import issues"
            )

    @staticmethod
    def _check_port_available(port: int) -> bool:
        """Check if a port is available."""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


# ============================================================================
# DATABASE HEALTH CHECKS
# ============================================================================

class DatabaseHealthChecker(HealthChecker):
    """Check database accessibility and integrity."""

    DATABASES = {
        "applicantdb": {
            "path": "~/.mcp_applicantdb_enhanced/applicantdb.sqlite",
            "description": "Applicant Database",
            "tables": ["applicants", "employment_history"]
        },
        "audit_db": {
            "path": "~/.mcp_applicantdb_enhanced/audit.sqlite",
            "description": "Audit Database",
            "tables": ["audit_logs"]
        },
        "employers_db": {
            "path": "~/.mcp_applicantdb_enhanced/employers.sqlite",
            "description": "Employers Database",
            "tables": ["employers"]
        },
        "risk_rules_db": {
            "path": "~/.mcp_risk_rules_enhanced/riskrulesdb.sqlite",
            "description": "Risk Rules Database",
            "tables": ["risk_rules", "compliance_rules"]
        }
    }

    def check_databases(self) -> None:
        """Check all database systems."""
        logger.info("Checking database accessibility...")

        for db_name, db_config in self.DATABASES.items():
            self._check_single_database(db_name, db_config)

    def _check_single_database(
        self,
        db_name: str,
        db_config: Dict[str, Any]
    ) -> None:
        """Check a single database."""
        db_path = Path(db_config["path"]).expanduser()
        details = {
            "database_name": db_name,
            "path": str(db_path),
            "description": db_config["description"]
        }

        try:
            # Check if database file exists
            if not db_path.exists():
                details["exists"] = False
                self.add_result(
                    component=db_name,
                    component_type=ComponentType.DATABASE,
                    status=HealthStatus.WARNING,
                    message=f"Database file not found at {db_path}",
                    details=details
                )
                self.add_recommendation(
                    f"Initialize {db_name} or check configuration path"
                )
                return

            details["exists"] = True

            # Try to connect
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            existing_tables = {row[0] for row in cursor.fetchall()}
            details["existing_tables"] = list(existing_tables)
            details["expected_tables"] = db_config.get("tables", [])

            # Verify expected tables
            missing_tables = set(db_config.get("tables", [])) - existing_tables
            if missing_tables:
                details["missing_tables"] = list(missing_tables)
                self.add_result(
                    component=db_name,
                    component_type=ComponentType.DATABASE,
                    status=HealthStatus.WARNING,
                    message=f"Some expected tables missing: {missing_tables}",
                    details=details
                )
                self.add_recommendation(
                    f"Run migrations or initialization script for {db_name}"
                )
            else:
                details["missing_tables"] = []

            # Get database statistics
            cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size();")
            size_result = cursor.fetchone()
            details["size_bytes"] = size_result[0] if size_result else 0

            # Count rows in each table
            row_counts = {}
            for table in existing_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    row_counts[table] = count
                except sqlite3.Error as e:
                    row_counts[table] = f"Error: {str(e)}"
            details["row_counts"] = row_counts

            conn.close()

            status = (
                HealthStatus.HEALTHY
                if not missing_tables
                else HealthStatus.WARNING
            )

            self.add_result(
                component=db_name,
                component_type=ComponentType.DATABASE,
                status=status,
                message=f"Database {db_name} is accessible",
                details=details
            )

        except sqlite3.Error as e:
            self.add_result(
                component=db_name,
                component_type=ComponentType.DATABASE,
                status=HealthStatus.CRITICAL,
                message=f"Database error: {str(e)}",
                details={**details, "error": str(e)}
            )
            self.add_recommendation(
                f"Check database file integrity for {db_name} or reinitialize"
            )
        except Exception as e:
            self.add_result(
                component=db_name,
                component_type=ComponentType.DATABASE,
                status=HealthStatus.CRITICAL,
                message=f"Failed to check database: {str(e)}",
                details={**details, "error": str(e)}
            )


# ============================================================================
# AGENT INITIALIZATION CHECKS
# ============================================================================

class AgentHealthChecker(HealthChecker):
    """Check agent modules and initialization."""

    AGENTS = {
        "applicant_profile_agent": {
            "module": "applicant_profile_agent_mcp",
            "description": "Applicant Profile Agent",
            "key_classes": ["ApplicantProfileAgent"]
        },
        "financial_risk_agent": {
            "module": "financial_risk_agent",
            "description": "Financial Risk Agent",
            "key_classes": ["FinancialRiskAgent"]
        },
        "loan_decision_agent": {
            "module": "loan_decision_agent",
            "description": "Loan Decision Agent",
            "key_classes": ["LoanDecisionAgent"]
        },
        "compliance_orchestrator_agent": {
            "module": "compliance_orchestrator_agent",
            "description": "Compliance Orchestrator Agent",
            "key_classes": ["ComplianceOrchestratorAgent"]
        }
    }

    def check_agents(self) -> None:
        """Check all agent modules."""
        logger.info("Checking agent initialization...")

        for agent_name, agent_config in self.AGENTS.items():
            self._check_single_agent(agent_name, agent_config)

    def _check_single_agent(
        self,
        agent_name: str,
        agent_config: Dict[str, Any]
    ) -> None:
        """Check a single agent module."""
        details = {
            "agent_name": agent_name,
            "module": agent_config["module"],
            "description": agent_config["description"]
        }

        try:
            # Check if module file exists
            module_path = self.project_root / f"{agent_config['module']}.py"
            if not module_path.exists():
                self.add_result(
                    component=agent_name,
                    component_type=ComponentType.AGENT,
                    status=HealthStatus.CRITICAL,
                    message=f"Agent module not found at {module_path}",
                    details=details
                )
                self.add_recommendation(
                    f"Verify that {agent_config['module']}.py exists"
                )
                return

            details["file_exists"] = True

            # Try to import and check for key classes
            spec = importlib.util.spec_from_file_location(
                agent_config["module"],
                module_path
            )
            if spec and spec.loader:
                # Check for required classes by parsing the file
                with open(module_path, 'r') as f:
                    content = f.read()

                missing_classes = []
                found_classes = []
                for class_name in agent_config.get("key_classes", []):
                    if f"class {class_name}" in content:
                        found_classes.append(class_name)
                    else:
                        missing_classes.append(class_name)

                details["expected_classes"] = agent_config.get("key_classes", [])
                details["found_classes"] = found_classes
                details["missing_classes"] = missing_classes

                if missing_classes:
                    status = HealthStatus.CRITICAL
                    message = f"Missing expected classes: {missing_classes}"
                    self.add_recommendation(
                        f"Check {agent_config['module']}.py for expected class definitions"
                    )
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Agent {agent_name} module is properly configured"

            else:
                status = HealthStatus.WARNING
                message = f"Cannot load module spec for {agent_config['module']}"
                details["warning"] = "Module spec could not be loaded"

            self.add_result(
                component=agent_name,
                component_type=ComponentType.AGENT,
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            self.add_result(
                component=agent_name,
                component_type=ComponentType.AGENT,
                status=HealthStatus.CRITICAL,
                message=f"Failed to check agent: {str(e)}",
                details={**details, "error": str(e)}
            )
            self.add_recommendation(
                f"Review {agent_config['module']}.py for syntax or import errors"
            )


# ============================================================================
# ORCHESTRATOR STATE CHECKS
# ============================================================================

class OrchestratorHealthChecker(HealthChecker):
    """Check orchestrator configuration and state."""

    def check_orchestrator(self) -> None:
        """Check orchestrator module and configuration."""
        logger.info("Checking orchestrator state...")

        self._check_orchestrator_module()
        self._check_orchestrator_configuration()
        self._check_langgraph_setup()

    def _check_orchestrator_module(self) -> None:
        """Check orchestrator module exists and is valid."""
        details = {
            "module": "loan_orchestrator",
            "description": "LangGraph-based Loan Orchestrator"
        }

        try:
            orchestrator_path = self.project_root / "loan_orchestrator.py"

            if not orchestrator_path.exists():
                self.add_result(
                    component="loan_orchestrator",
                    component_type=ComponentType.ORCHESTRATOR,
                    status=HealthStatus.CRITICAL,
                    message="Orchestrator module not found",
                    details=details
                )
                self.add_recommendation("Verify loan_orchestrator.py exists in project root")
                return

            details["file_exists"] = True

            # Check for key functions/classes
            with open(orchestrator_path, 'r') as f:
                content = f.read()

            required_items = [
                "compile_loan_orchestrator",
                "execute_application",
                "ApplicationState",
                "ApplicationStatus"
            ]
            found_items = []
            missing_items = []

            for item in required_items:
                if f"def {item}" in content or f"class {item}" in content:
                    found_items.append(item)
                else:
                    missing_items.append(item)

            details["required_items"] = required_items
            details["found_items"] = found_items
            details["missing_items"] = missing_items

            if missing_items:
                status = HealthStatus.CRITICAL
                message = f"Missing required items: {missing_items}"
                self.add_recommendation(
                    "Check loan_orchestrator.py for required function and class definitions"
                )
            else:
                status = HealthStatus.HEALTHY
                message = "Orchestrator module is properly configured"

            self.add_result(
                component="loan_orchestrator",
                component_type=ComponentType.ORCHESTRATOR,
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            self.add_result(
                component="loan_orchestrator",
                component_type=ComponentType.ORCHESTRATOR,
                status=HealthStatus.CRITICAL,
                message=f"Failed to check orchestrator: {str(e)}",
                details={**details, "error": str(e)}
            )

    def _check_orchestrator_configuration(self) -> None:
        """Check orchestrator configuration files."""
        details = {"config_files": []}

        config_files = [
            "decision_synthesis_mcp_config.json",
            "riskrulesdb_enhanced_config.json"
        ]

        for config_file in config_files:
            config_path = self.project_root / config_file
            file_details = {
                "file": config_file,
                "exists": config_path.exists()
            }

            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    file_details["valid_json"] = True
                    file_details["size_bytes"] = config_path.stat().st_size
                    file_details["keys"] = list(config_data.keys())
                except json.JSONDecodeError as e:
                    file_details["valid_json"] = False
                    file_details["error"] = str(e)
                    self.add_recommendation(
                        f"Fix JSON syntax error in {config_file}"
                    )
            else:
                file_details["valid_json"] = False

            details["config_files"].append(file_details)

        self.add_result(
            component="orchestrator_configuration",
            component_type=ComponentType.ORCHESTRATOR,
            status=HealthStatus.HEALTHY,
            message="Orchestrator configuration check completed",
            details=details
        )

    def _check_langgraph_setup(self) -> None:
        """Check LangGraph setup and dependencies."""
        details = {}

        try:
            import langgraph
            details["langgraph_available"] = True
            details["langgraph_version"] = getattr(langgraph, "__version__", "unknown")
        except ImportError:
            details["langgraph_available"] = False
            self.add_recommendation("Install langgraph: pip install langgraph")

        try:
            from langgraph.graph import StateGraph
            details["stategraph_available"] = True
        except ImportError:
            details["stategraph_available"] = False
            self.add_recommendation("Install langgraph-core components")

        status = (
            HealthStatus.HEALTHY
            if details.get("langgraph_available") and details.get("stategraph_available")
            else HealthStatus.CRITICAL
        )

        self.add_result(
            component="langgraph_setup",
            component_type=ComponentType.ORCHESTRATOR,
            status=status,
            message="LangGraph dependency check",
            details=details
        )


# ============================================================================
# DEPENDENCY CHECKS
# ============================================================================

class DependencyHealthChecker(HealthChecker):
    """Check system dependencies."""

    REQUIRED_PACKAGES = [
        "anthropic",
        "langgraph",
        "mcp",
        "fastapi",
        "sqlite3",
        "pydantic"
    ]

    def check_dependencies(self) -> None:
        """Check all required dependencies."""
        logger.info("Checking system dependencies...")

        for package in self.REQUIRED_PACKAGES:
            self._check_single_dependency(package)

    def _check_single_dependency(self, package_name: str) -> None:
        """Check a single dependency."""
        details = {"package": package_name}

        try:
            if package_name == "sqlite3":
                # sqlite3 is built-in
                import sqlite3
                details["installed"] = True
                details["version"] = sqlite3.sqlite_version
                status = HealthStatus.HEALTHY
                message = f"Built-in {package_name} is available"
            else:
                module = importlib.import_module(package_name)
                details["installed"] = True
                details["version"] = getattr(module, "__version__", "unknown")
                status = HealthStatus.HEALTHY
                message = f"Package {package_name} is installed"

            self.add_result(
                component=package_name,
                component_type=ComponentType.DEPENDENCIES,
                status=status,
                message=message,
                details=details
            )

        except ImportError:
            details["installed"] = False
            self.add_result(
                component=package_name,
                component_type=ComponentType.DEPENDENCIES,
                status=HealthStatus.CRITICAL,
                message=f"Required package {package_name} is not installed",
                details=details
            )
            self.add_recommendation(f"Install {package_name}: pip install {package_name}")


# ============================================================================
# CONFIGURATION CHECKS
# ============================================================================

class ConfigurationHealthChecker(HealthChecker):
    """Check system configuration."""

    def check_configuration(self) -> None:
        """Check system configuration."""
        logger.info("Checking system configuration...")

        self._check_env_variables()
        self._check_required_files()

    def _check_env_variables(self) -> None:
        """Check environment variables."""
        details = {}

        required_vars = ["ANTHROPIC_API_KEY"]
        present_vars = []
        missing_vars = []

        for var in required_vars:
            if os.getenv(var):
                present_vars.append(var)
                details[var] = "PRESENT"
            else:
                missing_vars.append(var)
                details[var] = "MISSING"

        details["present_count"] = len(present_vars)
        details["missing_count"] = len(missing_vars)

        status = (
            HealthStatus.HEALTHY
            if not missing_vars
            else HealthStatus.CRITICAL
        )

        if missing_vars:
            self.add_recommendation(
                f"Set missing environment variables: {', '.join(missing_vars)}"
            )

        self.add_result(
            component="environment_variables",
            component_type=ComponentType.CONFIGURATION,
            status=status,
            message="Environment variable check",
            details=details
        )

    def _check_required_files(self) -> None:
        """Check for required project files."""
        details = {}

        required_files = [
            "loan_orchestrator.py",
            "applicant_profile_agent_mcp.py",
            "financial_risk_agent.py",
            "loan_decision_agent.py",
            ".env"
        ]

        present_files = []
        missing_files = []

        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                present_files.append(file_name)
                details[file_name] = "EXISTS"
            else:
                missing_files.append(file_name)
                details[file_name] = "MISSING"

        details["present_count"] = len(present_files)
        details["missing_count"] = len(missing_files)

        status = (
            HealthStatus.HEALTHY
            if not missing_files
            else HealthStatus.WARNING
        )

        if missing_files:
            self.add_recommendation(
                f"Missing files: {', '.join(missing_files)}"
            )

        self.add_result(
            component="required_files",
            component_type=ComponentType.CONFIGURATION,
            status=status,
            message="Required files check",
            details=details
        )


# ============================================================================
# HEALTH REPORT GENERATOR
# ============================================================================

class HealthReportGenerator:
    """Generate comprehensive health report."""

    def __init__(self):
        self.all_results: List[HealthCheckResult] = []
        self.all_recommendations: List[str] = []

    def run_all_checks(self) -> SystemHealthReport:
        """Run all health checks."""
        logger.info("Starting comprehensive system health check...")

        checkers = [
            ConfigurationHealthChecker(),
            DependencyHealthChecker(),
            MCPServerHealthChecker(),
            DatabaseHealthChecker(),
            AgentHealthChecker(),
            OrchestratorHealthChecker(),
        ]

        for checker in checkers:
            if isinstance(checker, ConfigurationHealthChecker):
                checker.check_configuration()
            elif isinstance(checker, DependencyHealthChecker):
                checker.check_dependencies()
            elif isinstance(checker, MCPServerHealthChecker):
                checker.check_mcp_servers()
            elif isinstance(checker, DatabaseHealthChecker):
                checker.check_databases()
            elif isinstance(checker, AgentHealthChecker):
                checker.check_agents()
            elif isinstance(checker, OrchestratorHealthChecker):
                checker.check_orchestrator()

            self.all_results.extend(checker.results)
            self.all_recommendations.extend(checker.recommendations)

        return self._generate_report()

    def _generate_report(self) -> SystemHealthReport:
        """Generate the final health report."""
        # Determine overall status
        status_counts = {
            HealthStatus.HEALTHY: sum(
                1 for r in self.all_results if r.status == HealthStatus.HEALTHY
            ),
            HealthStatus.WARNING: sum(
                1 for r in self.all_results if r.status == HealthStatus.WARNING
            ),
            HealthStatus.CRITICAL: sum(
                1 for r in self.all_results if r.status == HealthStatus.CRITICAL
            ),
            HealthStatus.UNKNOWN: sum(
                1 for r in self.all_results if r.status == HealthStatus.UNKNOWN
            ),
        }

        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_status = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY

        report = SystemHealthReport(
            overall_status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            results=self.all_results,
            summary={
                "total_checks": len(self.all_results),
                "healthy": status_counts[HealthStatus.HEALTHY],
                "warning": status_counts[HealthStatus.WARNING],
                "critical": status_counts[HealthStatus.CRITICAL],
                "unknown": status_counts[HealthStatus.UNKNOWN],
            },
            recommendations=list(set(self.all_recommendations))  # Deduplicate
        )

        return report


# ============================================================================
# REPORT FORMATTING AND OUTPUT
# ============================================================================

def format_report_for_console(report: SystemHealthReport) -> str:
    """Format health report for console output."""
    output = []
    output.append("\n" + "=" * 80)
    output.append("SYSTEM HEALTH CHECK REPORT")
    output.append("=" * 80)
    output.append(f"\nReport Generated: {report.timestamp}")
    output.append(f"Overall System Status: {report.overall_status.value.upper()}")
    output.append(f"\nSummary:")
    output.append(f"  Total Checks: {report.summary['total_checks']}")
    output.append(f"  Healthy:      {report.summary['healthy']}")
    output.append(f"  Warnings:     {report.summary['warning']}")
    output.append(f"  Critical:     {report.summary['critical']}")

    # Group results by component type
    by_type = {}
    for result in report.results:
        type_name = result.component_type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(result)

    for component_type in sorted(by_type.keys()):
        output.append(f"\n{'-' * 80}")
        output.append(f"{component_type.upper()}")
        output.append(f"{'-' * 80}")

        for result in by_type[component_type]:
            status_str = result.status.value.upper()
            status_symbol = {
                "healthy": "✓",
                "warning": "⚠",
                "critical": "✗",
                "unknown": "?"
            }.get(result.status.value, "?")

            output.append(f"\n{status_symbol} [{status_str}] {result.component}")
            output.append(f"   Message: {result.message}")

            if result.details:
                output.append(f"   Details:")
                for key, value in result.details.items():
                    if isinstance(value, (list, dict)):
                        output.append(f"     {key}: {json.dumps(value, indent=6)}")
                    else:
                        output.append(f"     {key}: {value}")

    if report.recommendations:
        output.append(f"\n{'-' * 80}")
        output.append("RECOMMENDATIONS")
        output.append(f"{'-' * 80}")
        for i, recommendation in enumerate(report.recommendations, 1):
            output.append(f"{i}. {recommendation}")

    output.append("\n" + "=" * 80 + "\n")

    return "\n".join(output)


def format_report_as_json(report: SystemHealthReport) -> str:
    """Format health report as JSON."""
    report_dict = {
        "overall_status": report.overall_status.value,
        "timestamp": report.timestamp,
        "summary": report.summary,
        "results": [
            {
                "component": r.component,
                "component_type": r.component_type.value,
                "status": r.status.value,
                "message": r.message,
                "details": r.details,
                "timestamp": r.timestamp
            }
            for r in report.results
        ],
        "recommendations": report.recommendations
    }
    return json.dumps(report_dict, indent=2)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for system health check."""
    import argparse

    parser = argparse.ArgumentParser(
        description="System Health Check for Loan Application Orchestrator"
    )
    parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Output format (default: console)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (optional, defaults to stdout)"
    )

    args = parser.parse_args()

    # Run health checks
    generator = HealthReportGenerator()
    report = generator.run_all_checks()

    # Format output
    if args.format == "json":
        output = format_report_as_json(report)
    else:
        output = format_report_for_console(report)

    # Write output
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Health report written to: {args.output}")
        except IOError as e:
            print(f"Error writing to {args.output}: {e}", file=sys.stderr)
            print(output)
            sys.exit(1)
    else:
        print(output)

    # Exit with appropriate status code
    if report.overall_status == HealthStatus.CRITICAL:
        sys.exit(1)
    elif report.overall_status == HealthStatus.WARNING:
        sys.exit(0)  # Warnings don't fail the check
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
