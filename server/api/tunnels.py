"""
Tunnels REST API.

Endpoints
---------
GET  /api/tunnels              — list active tunnels for authenticated user
GET  /api/tunnels/{subdomain}  — get details of a specific active tunnel
DELETE /api/tunnels/{subdomain} — disconnect a tunnel
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from server.api.auth import get_current_user
from server.core.tunnel_manager import TunnelManager
from server.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/tunnels", tags=["tunnels"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TunnelInfo(BaseModel):
    subdomain: str
    tunnel_url: str
    user_id: int
    local_port: int
    client_version: str
    created_at: datetime
    last_seen_at: datetime
    pending_requests: int


# ---------------------------------------------------------------------------
# Helper to extract TunnelManager from app state
# ---------------------------------------------------------------------------


def _get_manager(request: Request) -> TunnelManager:
    return request.app.state.tunnel_manager  # type: ignore[return-value]


def _get_domain(request: Request) -> str:
    return request.app.state.settings.domain  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[TunnelInfo], summary="List active tunnels")
async def list_tunnels(
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> list[TunnelInfo]:
    """Return all active tunnels belonging to the authenticated user."""
    manager: TunnelManager = _get_manager(request)
    domain = _get_domain(request)
    tunnels = manager.list_tunnels(user_id=user.id)
    return [
        TunnelInfo(
            subdomain=t.subdomain,
            tunnel_url=f"https://{t.subdomain}.{domain}",
            user_id=t.user_id,
            local_port=t.local_port,
            client_version=t.client_version,
            created_at=t.created_at,
            last_seen_at=t.last_seen_at,
            pending_requests=len(t.pending_requests),
        )
        for t in tunnels
    ]


@router.get("/{subdomain}", response_model=TunnelInfo, summary="Get tunnel details")
async def get_tunnel(
    subdomain: str,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> TunnelInfo:
    """Return details of a specific active tunnel."""
    manager: TunnelManager = _get_manager(request)
    domain = _get_domain(request)
    tunnel = manager.lookup(subdomain)

    if tunnel is None:
        raise HTTPException(status_code=404, detail=f"Tunnel '{subdomain}' not found.")
    if tunnel.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not your tunnel.")

    return TunnelInfo(
        subdomain=tunnel.subdomain,
        tunnel_url=f"https://{tunnel.subdomain}.{domain}",
        user_id=tunnel.user_id,
        local_port=tunnel.local_port,
        client_version=tunnel.client_version,
        created_at=tunnel.created_at,
        last_seen_at=tunnel.last_seen_at,
        pending_requests=len(tunnel.pending_requests),
    )


@router.delete("/{subdomain}", status_code=status.HTTP_204_NO_CONTENT, summary="Disconnect tunnel")
async def disconnect_tunnel(
    subdomain: str,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> None:
    """Forcibly disconnect an active tunnel."""
    manager: TunnelManager = _get_manager(request)
    tunnel = manager.lookup(subdomain)

    if tunnel is None:
        raise HTTPException(status_code=404, detail=f"Tunnel '{subdomain}' not found.")
    if tunnel.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not your tunnel.")

    await manager.unregister(subdomain, reason="api_disconnect")
    logger.info("api.tunnel_disconnected", subdomain=subdomain, by_user=user.id)
