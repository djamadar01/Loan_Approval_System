"""Base agent classes."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature")
    max_tokens: int = Field(default=4096, description="Maximum tokens")
    system_prompt: Optional[str] = Field(None, description="System prompt")


class Agent:
    """Base agent class."""

    def __init__(self, config: AgentConfig):
        """Initialize agent.

        Args:
            config: Agent configuration
        """
        self.config = config

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent.

        Args:
            input_data: Input data

        Returns:
            Agent output
        """
        raise NotImplementedError("Subclasses must implement run()")
