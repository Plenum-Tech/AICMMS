"""Application-wide configuration via Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class AppConfig(BaseSettings):
    """Root configuration loaded from environment variables / .env file."""

    model_config = {"env_prefix": "CAFM_", "env_file": ".env", "extra": "ignore"}

    # Logging
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    log_format: str = Field(default="json", description="Log format: json or console")

    # Plugin discovery
    auto_discover_plugins: bool = Field(
        default=True,
        description="Auto-discover connector plugins via entry_points on startup",
    )

    # Schema discovery defaults
    schema_sample_size: int = Field(
        default=100,
        description="Number of rows to sample for type inference (CSV/Excel/MongoDB)",
    )

    # Connection defaults
    default_query_limit: int = Field(default=1000, description="Default row limit for queries")
    connection_timeout_seconds: int = Field(default=30, description="Connection timeout")
    health_check_interval_seconds: int = Field(
        default=60, description="Interval between health checks"
    )
