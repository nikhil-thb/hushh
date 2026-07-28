"""
Client configuration — reads and writes ``~/.hushh/config.json``.

The config file stores:
- ``server_url``: base URL of the Hushh server
- ``api_key``: the user's API key (returned at login)
- ``email``: the user's email

All fields are optional to support a partial / not-yet-logged-in state.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

_CONFIG_DIR = Path.home() / ".hushh"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

DEFAULT_SERVER_URL = os.environ.get("HUSHH_SERVER_URL", "https://hushh.online")


class ClientConfig(BaseModel):
    """Hushh client configuration stored on disk."""

    server_url: str = DEFAULT_SERVER_URL
    api_key: str | None = None
    email: str | None = None

    @property
    def ws_url(self) -> str:
        """Return the WebSocket URL, converting https:// → wss://"""
        return self.server_url.replace("https://", "wss://").replace("http://", "ws://")

    @property
    def tunnel_ws_url(self) -> str:
        return f"{self.ws_url}/tunnel/ws"

    @property
    def is_authenticated(self) -> bool:
        return self.api_key is not None


def load_config() -> ClientConfig:
    """Load config from disk.  Returns defaults if file doesn't exist."""
    if not _CONFIG_FILE.exists():
        return ClientConfig()
    with _CONFIG_FILE.open() as fh:
        data: dict[str, Any] = json.load(fh)
    return ClientConfig.model_validate(data)


def save_config(config: ClientConfig) -> None:
    """Persist config to disk."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if _CONFIG_FILE.exists():
        _CONFIG_FILE.chmod(0o700)
    with _CONFIG_FILE.open("w") as fh:
        json.dump(config.model_dump(), fh, indent=2)
    _CONFIG_FILE.chmod(0o600)


def clear_config() -> None:
    """Remove the config file (logout)."""
    if _CONFIG_FILE.exists():
        _CONFIG_FILE.unlink()
