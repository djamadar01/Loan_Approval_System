"""Base classes for MCP servers."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class MCPServer(ABC):
    """Abstract base class for MCP servers."""

    def __init__(self, name: str, version: str = "0.1.0"):
        """Initialize MCP server.

        Args:
            name: Server name
            version: Server version
        """
        self.name = name
        self.version = version

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the server."""
        pass

    @abstractmethod
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming request.

        Args:
            request: Request dictionary

        Returns:
            Response dictionary
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the server."""
        pass
