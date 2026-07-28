"""
Health check endpoints.

GET /health  — liveness probe (always 200 if process is running)
GET /readyz  — readiness probe (checks DB connectivity)
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Request
from sqlalchemy import text

from server.db.database import get_session

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return 200 OK when the server process is alive."""
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness probe")
async def readyz(request: Request) -> dict[str, Any]:
    """
    Return 200 OK when the server is ready to serve traffic.

    Checks:
    - Database connectivity
    - TunnelManager is started
    """
    checks: dict[str, str] = {}

    # DB check
    try:
        async for session in get_session():
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.error("health.db_check_failed", error=str(exc))
        checks["database"] = f"error: {exc}"

    # TunnelManager check
    try:
        manager = request.app.state.tunnel_manager
        checks["tunnel_manager"] = "ok" if manager is not None else "not_started"
    except AttributeError:
        checks["tunnel_manager"] = "not_started"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
