"""
Client authentication helpers.

Calls the server's ``/auth/*`` endpoints and manages local credentials.
"""

from __future__ import annotations

import httpx

from client.config import ClientConfig, load_config, save_config


class AuthError(Exception):
    """Raised when authentication fails."""


async def login(email: str, password: str, server_url: str | None = None) -> tuple[str, str]:
    """
    Authenticate with the server and persist credentials.

    Returns:
        (email, api_key) on success.

    Raises:
        AuthError: on invalid credentials or network failure.
    """
    config = load_config()
    base_url = server_url or config.server_url

    async with httpx.AsyncClient(base_url=base_url, timeout=15) as client:
        try:
            resp = await client.post("/auth/login", json={"email": email, "password": password})
        except httpx.RequestError as exc:
            raise AuthError(f"Network error: {exc}") from exc

    if resp.status_code == 401:
        raise AuthError("Invalid email or password.")
    if not resp.is_success:
        raise AuthError(f"Server error {resp.status_code}: {resp.text}")

    data = resp.json()
    api_key: str = data["api_key"]

    # Persist
    config = ClientConfig(server_url=base_url, api_key=api_key, email=email)
    save_config(config)

    return email, api_key


async def whoami() -> dict[str, object]:
    """
    Fetch current user info from the server using the stored JWT (via login).

    Since we store the API key (not JWT), we authenticate via a fresh login
    is not needed — we call /auth/whoami with a bearer token obtained at login.

    For simplicity, the config stores the api_key; the server's /auth/whoami
    requires a JWT.  We call /auth/login with stored credentials to get a
    fresh token, then /auth/whoami.

    Future: store JWT alongside api_key to avoid this round-trip.
    """
    config = load_config()
    if not config.is_authenticated:
        raise AuthError("Not logged in. Run `hushh login` first.")

    # Since we only store the api_key, hit a dedicated endpoint that accepts it.
    # The tunnel WebSocket authenticates with api_key directly.
    # For REST calls we use Basic auth workaround: X-API-Key header.
    async with httpx.AsyncClient(base_url=config.server_url, timeout=15) as client:
        try:
            resp = await client.get(
                "/auth/whoami",
                headers={"X-API-Key": config.api_key or ""},
            )
        except httpx.RequestError as exc:
            raise AuthError(f"Network error: {exc}") from exc

    if resp.status_code == 401:
        raise AuthError("Not authenticated. Run `hushh login` again.")
    resp.raise_for_status()
    return resp.json()  # type: ignore[return-value]
