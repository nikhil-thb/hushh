"""
Stats API.

GET /api/stats — aggregate server and tunnel statistics (admin only).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from server.api.auth import get_current_admin
from server.core.tunnel_manager import TunnelManager
from server.models.user import User

router = APIRouter(prefix="/api/stats", tags=["stats"])


class ServerStats(BaseModel):
    active_tunnels: int
    total_requests: int | None = None  # populated from Prometheus if available


@router.get("", response_model=ServerStats, summary="Server statistics (admin)")
async def get_stats(
    _admin: Annotated[User, Depends(get_current_admin)],
    request: Request,
) -> ServerStats:
    manager: TunnelManager = request.app.state.tunnel_manager
    return ServerStats(active_tunnels=manager.count())
