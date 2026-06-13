"""Environment-based configuration for quickwit-mcp.

Settings are read from environment variables (or a local ``.env`` file). The
single required value is ``QW_BASE_URL``; everything else has a sensible default.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Transport(str, Enum):
    """Transports the MCP server can run on."""

    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


class Settings(BaseSettings):
    """quickwit-mcp runtime configuration.

    Field names map to upper-cased environment variables (case-insensitive),
    e.g. ``qw_base_url`` <- ``QW_BASE_URL``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    qw_base_url: str = Field(
        ...,
        description="Base URL of the Quickwit instance, e.g. http://localhost:7280",
    )
    qw_timeout: float = Field(
        30.0,
        gt=0,
        description="HTTP request timeout in seconds.",
    )
    qw_default_max_hits: int = Field(
        100,
        gt=0,
        description="Default number of hits when a search omits max_hits.",
    )
    qw_max_hits_ceiling: int = Field(
        500,
        gt=0,
        description="Hard upper bound on the hits any single search may return; "
        "page beyond it with start_offset.",
    )
    mcp_transport: Transport = Field(
        Transport.STDIO,
        description="Transport the MCP server runs on.",
    )

    @field_validator("qw_base_url")
    @classmethod
    def _normalize_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("QW_BASE_URL must start with http:// or https://")
        return value

    @model_validator(mode="after")
    def _check_hit_bounds(self) -> Settings:
        if self.qw_default_max_hits > self.qw_max_hits_ceiling:
            raise ValueError("QW_DEFAULT_MAX_HITS cannot exceed QW_MAX_HITS_CEILING")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance for app use."""
    return Settings()
