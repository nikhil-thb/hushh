"""
Server configuration via Pydantic Settings.

Settings are loaded from environment variables and/or a ``config.yaml`` file.
Environment variables take precedence over the YAML file.

Usage::

    from server.config import get_settings
    settings = get_settings()
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / config.yaml."""

    model_config = SettingsConfigDict(
        env_prefix="HUSHH_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ────────────────────────────────────────────────────────────
    domain: str = Field("hushh.online", description="Base domain for tunnel subdomains.")
    host: str = Field("0.0.0.0", description="Bind host.")
    port: int = Field(8000, ge=1, le=65535, description="Bind port.")

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = Field(
        "sqlite+aiosqlite:///./hushh.db",
        description="SQLAlchemy async database URL.",
    )

    # ── Security ──────────────────────────────────────────────────────────
    secret_key: str = Field(..., description="Secret key for signing JWT tokens.")
    jwt_algorithm: str = Field("HS256")
    access_token_expire_minutes: int = Field(10080)  # 7 days

    # ── Tunnel limits ─────────────────────────────────────────────────────
    max_tunnels_per_user: int = Field(5, ge=1)
    max_concurrent_tunnels: int = Field(500, ge=1)
    max_request_size_mb: int = Field(50, ge=1)

    # ── Timeouts ──────────────────────────────────────────────────────────
    heartbeat_interval: int = Field(15, description="Expected heartbeat interval from client (seconds).")
    heartbeat_timeout: int = Field(45, description="Seconds before a tunnel is considered dead.")
    idle_timeout: int = Field(28800, description="Max tunnel lifetime with no traffic (seconds).")
    request_timeout: int = Field(30, description="Seconds to wait for a tunnel response.")

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = Field("INFO")
    log_json: bool = Field(True, description="Emit structured JSON logs.")

    # ── Metrics ───────────────────────────────────────────────────────────
    metrics_enabled: bool = Field(True)

    # ── Seeded admin ──────────────────────────────────────────────────────
    admin_email: str = Field("admin@hushh.online")
    admin_password: str = Field("changeme_admin_password")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @model_validator(mode="before")
    @classmethod
    def _load_yaml(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Merge values from config.yaml (lower priority than env vars)."""
        config_path = Path(os.getenv("HUSHH_CONFIG_FILE", "config.yaml"))
        if config_path.exists():
            with config_path.open() as fh:
                yaml_data: dict[str, Any] = yaml.safe_load(fh) or {}
            # env vars already in `values` take precedence
            for key, val in yaml_data.items():
                env_key = key.lower()
                if env_key not in values or values[env_key] is None:
                    values[env_key] = val
        return values

    @property
    def tunnel_base_url(self) -> str:
        """Return the HTTPS base URL for tunnels."""
        return f"https://{self.domain}"

    @property
    def tunnel_ws_url(self) -> str:
        """Return the WebSocket URL clients connect to."""
        return f"wss://{self.domain}/tunnel/ws"

    @property
    def max_request_size_bytes(self) -> int:
        return self.max_request_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()  # type: ignore[call-arg]
