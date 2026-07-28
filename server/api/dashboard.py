"""
Dashboard API.

Endpoints
---------
GET /api/dashboard/stats — aggregate tunnel stats for the current user.
GET /api/dashboard/request-logs/{tunnel_id} — latest 100 requests for a tunnel.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.api.auth import get_current_user
from server.db.database import get_session
from server.models.request_log import RequestLog
from server.models.tunnel import TunnelRecord, TunnelStatus
from server.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    active_tunnels: int
    offline_tunnels: int
    total_requests: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DashboardStats:
    """Return dashboard statistics for the authenticated user."""
    # Active tunnels
    active = await session.execute(
        select(func.count(TunnelRecord.id)).where(
            TunnelRecord.user_id == user.id,
            TunnelRecord.status == TunnelStatus.ACTIVE,
        )
    )
    active_count = active.scalar() or 0

    # Offline tunnels
    offline = await session.execute(
        select(func.count(TunnelRecord.id)).where(
            TunnelRecord.user_id == user.id,
            TunnelRecord.status != TunnelStatus.ACTIVE,
        )
    )
    offline_count = offline.scalar() or 0

    # Total requests
    requests = await session.execute(
        select(func.sum(TunnelRecord.request_count)).where(
            TunnelRecord.user_id == user.id
        )
    )
    total_reqs = requests.scalar() or 0

    return DashboardStats(
        active_tunnels=active_count,
        offline_tunnels=offline_count,
        total_requests=total_reqs,
    )


class RequestLogOut(BaseModel):
    id: int
    method: str
    path: str
    status: int
    duration_ms: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/request-logs/{subdomain}", response_model=list[RequestLogOut])
async def get_request_logs(
    subdomain: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[RequestLogOut]:
    """Return the latest 100 requests for a specific tunnel by subdomain."""
    # Verify ownership
    tunnel_res = await session.execute(
        select(TunnelRecord).where(TunnelRecord.subdomain == subdomain)
    )
    tunnel = tunnel_res.scalar_one_or_none()

    if not tunnel:
        raise HTTPException(status_code=404, detail="Tunnel not found")
    if tunnel.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not your tunnel")

    # Fetch logs
    logs = await session.execute(
        select(RequestLog)
        .where(RequestLog.tunnel_id == tunnel.id)
        .order_by(RequestLog.created_at.desc())
        .limit(100)
    )

    return [
        RequestLogOut(
            id=l.id,
            method=l.method,
            path=l.path,
            status=l.status,
            duration_ms=l.duration_ms,
            created_at=l.created_at.isoformat(),
        )
        for l in logs.scalars().all()
    ]
