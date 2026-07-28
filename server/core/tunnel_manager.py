"""
TunnelManager — in-memory registry of live tunnel connections.

Design
------
- ``TunnelManager`` is instantiated once and shared via FastAPI's ``app.state``.
- Each live tunnel is represented by a :class:`Tunnel` dataclass that holds
  the WebSocket connection and a dictionary of pending HTTP request futures.
- A background sweep task runs every ``heartbeat_timeout / 2`` seconds and
  evicts tunnels that have not sent a heartbeat within the timeout window.
- All operations are protected by per-tunnel asyncio locks where necessary.
- The manager is *not* a global singleton; callers receive it from the request
  state to allow multiple instances in tests.
"""

from __future__ import annotations

import asyncio
import random
import re
import string
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import structlog
from fastapi import WebSocket

from server.config import Settings
from server.core.metrics import (
    TUNNEL_ACTIVE_GAUGE,
    TUNNEL_CONNECTED_TOTAL,
    TUNNEL_DISCONNECTED_TOTAL,
    TUNNEL_IDLE_EVICTIONS_TOTAL,
)

logger = structlog.get_logger(__name__)

_SUBDOMAIN_ALPHABET = string.ascii_lowercase + string.digits
_SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$")


@dataclass
class Tunnel:
    """Represents a single live tunnel connection."""

    subdomain: str
    user_id: int
    local_port: int
    client_version: str
    websocket: WebSocket
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # request_id → asyncio.Future[ResponseMessage]
    pending_requests: dict[UUID, asyncio.Future] = field(default_factory=dict)  # type: ignore[type-arg]

    # Serialization lock — ensures only one goroutine writes to WS at a time
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def touch(self) -> None:
        """Update last_seen_at to now."""
        self.last_seen_at = datetime.now(UTC)

    def seconds_since_last_seen(self) -> float:
        return (datetime.now(UTC) - self.last_seen_at).total_seconds()

    def is_idle(self, idle_timeout: int) -> bool:
        return self.seconds_since_last_seen() > idle_timeout

    def __repr__(self) -> str:
        return f"<Tunnel subdomain={self.subdomain!r} user_id={self.user_id}>"


class SubdomainConflictError(Exception):
    """Raised when a requested subdomain is already taken."""


class TunnelLimitExceededError(Exception):
    """Raised when a user would exceed their tunnel limit."""


class TunnelManager:
    """
    Registry and lifecycle manager for all active tunnel connections.

    Intended to be created once and stored on ``app.state.tunnel_manager``.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._tunnels: dict[str, Tunnel] = {}  # subdomain → Tunnel
        self._user_tunnel_count: dict[int, int] = {}  # user_id → count
        self._sweep_task: asyncio.Task | None = None  # type: ignore[type-arg]

    # ── Lifecycle ─────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background sweep task."""
        self._sweep_task = asyncio.create_task(self._sweep_loop(), name="tunnel-sweeper")
        logger.info("tunnel_manager.started")

    async def stop(self) -> None:
        """Cancel sweep task and close all tunnels."""
        if self._sweep_task is not None:
            self._sweep_task.cancel()
            try:
                await self._sweep_task
            except asyncio.CancelledError:
                pass

        subdomains = list(self._tunnels.keys())
        for subdomain in subdomains:
            await self._close_tunnel(subdomain, reason="server_shutdown")

        logger.info("tunnel_manager.stopped", tunnels_closed=len(subdomains))

    # ── Registration ──────────────────────────────────────────────────────

    async def register(
        self,
        *,
        user_id: int,
        local_port: int,
        client_version: str,
        websocket: WebSocket,
        requested_subdomain: str | None = None,
    ) -> Tunnel:
        """
        Register a new tunnel.

        Raises:
            SubdomainConflictError: if requested subdomain is already in use.
            TunnelLimitExceededError: if the user has hit their tunnel limit.
            ValueError: if the requested subdomain is invalid.
        """
        current_count = self._user_tunnel_count.get(user_id, 0)
        if current_count >= self._settings.max_tunnels_per_user:
            raise TunnelLimitExceededError(
                f"User {user_id} already has {current_count} tunnels (max {self._settings.max_tunnels_per_user})"
            )

        if len(self._tunnels) >= self._settings.max_concurrent_tunnels:
            raise TunnelLimitExceededError("Server tunnel capacity reached.")

        subdomain = self._resolve_subdomain(requested_subdomain)

        tunnel = Tunnel(
            subdomain=subdomain,
            user_id=user_id,
            local_port=local_port,
            client_version=client_version,
            websocket=websocket,
        )
        self._tunnels[subdomain] = tunnel
        self._user_tunnel_count[user_id] = current_count + 1

        TUNNEL_CONNECTED_TOTAL.inc()
        TUNNEL_ACTIVE_GAUGE.inc()

        logger.info(
            "tunnel.registered",
            subdomain=subdomain,
            user_id=user_id,
            local_port=local_port,
        )
        return tunnel

    async def unregister(self, subdomain: str, *, reason: str = "client_disconnect") -> None:
        """Remove a tunnel and cancel all pending requests."""
        await self._close_tunnel(subdomain, reason=reason)

    def lookup(self, subdomain: str) -> Tunnel | None:
        """Return the live Tunnel for a subdomain, or None."""
        return self._tunnels.get(subdomain)

    def heartbeat(self, subdomain: str) -> bool:
        """
        Update last_seen_at for a tunnel.

        Returns:
            True if the tunnel was found and updated, False otherwise.
        """
        tunnel = self._tunnels.get(subdomain)
        if tunnel is None:
            return False
        tunnel.touch()
        return True

    # ── Queries ───────────────────────────────────────────────────────────

    def list_tunnels(self, *, user_id: int | None = None) -> list[Tunnel]:
        """Return all (or filtered) active tunnels."""
        tunnels = list(self._tunnels.values())
        if user_id is not None:
            tunnels = [t for t in tunnels if t.user_id == user_id]
        return tunnels

    def count(self) -> int:
        return len(self._tunnels)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _resolve_subdomain(self, requested: str | None) -> str:
        if requested is not None:
            requested = requested.lower().strip()
            if not _SUBDOMAIN_PATTERN.match(requested):
                raise ValueError(
                    f"Invalid subdomain {requested!r}. "
                    "Must be 3-63 chars, lowercase alphanumeric and hyphens."
                )
            if requested in self._tunnels:
                raise SubdomainConflictError(f"Subdomain {requested!r} is already in use.")
            return requested

        # Generate a random 8-char subdomain, retry on collision
        for _ in range(10):
            candidate = "".join(random.choices(_SUBDOMAIN_ALPHABET, k=8))
            if candidate not in self._tunnels:
                return candidate
        raise RuntimeError("Failed to generate a unique subdomain after 10 attempts.")

    async def _close_tunnel(self, subdomain: str, *, reason: str) -> None:
        tunnel = self._tunnels.pop(subdomain, None)
        if tunnel is None:
            return

        # Cancel all pending request futures
        for fut in tunnel.pending_requests.values():
            if not fut.done():
                fut.cancel()
        tunnel.pending_requests.clear()

        # Close WebSocket gracefully
        try:
            from shared.protocol import DisconnectMessage, serialize_message
            await tunnel.websocket.send_text(serialize_message(DisconnectMessage(reason=reason)))
            await tunnel.websocket.close()
        except Exception:
            pass

        user_count = self._user_tunnel_count.get(tunnel.user_id, 1)
        self._user_tunnel_count[tunnel.user_id] = max(0, user_count - 1)

        TUNNEL_DISCONNECTED_TOTAL.inc()
        TUNNEL_ACTIVE_GAUGE.dec()

        logger.info("tunnel.closed", subdomain=subdomain, reason=reason, user_id=tunnel.user_id)

    async def _sweep_loop(self) -> None:
        """Periodically evict dead / idle tunnels."""
        interval = max(10, self._settings.heartbeat_timeout // 2)
        while True:
            await asyncio.sleep(interval)
            await self._sweep()

    async def _sweep(self) -> None:
        now = datetime.now(UTC)
        dead: list[str] = []
        for subdomain, tunnel in list(self._tunnels.items()):
            since = (now - tunnel.last_seen_at).total_seconds()
            if since > self._settings.heartbeat_timeout:
                dead.append(subdomain)
                TUNNEL_IDLE_EVICTIONS_TOTAL.inc()
                logger.warning(
                    "tunnel.evicted",
                    subdomain=subdomain,
                    idle_seconds=since,
                )

        for subdomain in dead:
            await self._close_tunnel(subdomain, reason="heartbeat_timeout")
