"""API-specific configuration extending the core AppConfig."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API server configuration loaded from environment variables."""

    model_config = {"env_prefix": "CAFM_API_", "env_file": ".env", "extra": "ignore"}

    # Server
    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, description="Bind port")
    debug: bool = Field(default=False, description="Enable debug mode")
    reload: bool = Field(default=False, description="Auto-reload on file changes")

    # CORS
    cors_origins: list[str] = Field(
        default=["*"], description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    # Auth
    secret_key: str = Field(
        default="change-me-in-production-use-a-real-secret-key",
        description="JWT signing secret",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=480, description="Access token TTL in minutes"
    )

    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=120, description="Max requests per minute per client"
    )

    # Pagination defaults
    default_page_size: int = Field(default=50, description="Default items per page")
    max_page_size: int = Field(default=500, description="Maximum items per page")
