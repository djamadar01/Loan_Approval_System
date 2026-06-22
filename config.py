"""Configuration management."""
from typing import Optional

from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """API configuration."""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    reload: bool = Field(default=True, description="Enable auto-reload")
    workers: int = Field(default=1, description="Number of workers")


class StreamlitConfig(BaseModel):
    """Streamlit configuration."""

    host: str = Field(default="localhost", description="Streamlit host")
    port: int = Field(default=8501, description="Streamlit port")
    theme: str = Field(default="light", description="UI theme")


class AppConfig(BaseModel):
    """Application configuration."""

    debug: bool = Field(default=False, description="Debug mode")
    api: APIConfig = Field(default_factory=APIConfig, description="API config")
    streamlit: StreamlitConfig = Field(default_factory=StreamlitConfig, description="Streamlit config")
    log_level: str = Field(default="INFO", description="Logging level")


def get_config() -> AppConfig:
    """Get application configuration."""
    return AppConfig()
