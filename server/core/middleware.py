"""
ASGI middleware for Hushh Tunnel.

``TunnelRoutingMiddleware``
    Intercepts requests where the ``Host`` header matches ``*.hushh.online``
    and routes them through the TunnelManager.  All other requests fall
    through to the normal FastAPI router (health, API, metrics, etc.).

``RequestSizeLimitMiddleware``
    Rejects bodies that exceed the configured maximum size.
"""

from __future__ import annotations

import re

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from server.config import Settings
from server.core.metrics import HTTP_TUNNEL_NOT_FOUND_TOTAL
from server.core.proxy import route_request
from server.core.tunnel_manager import TunnelManager

logger = structlog.get_logger(__name__)

# Matches "<subdomain>.<domain>" e.g. "abc123.hushh.online"
_SUBDOMAIN_RE = re.compile(r"^(?P<subdomain>[a-z0-9][a-z0-9\-]+)\.")


class TunnelRoutingMiddleware(BaseHTTPMiddleware):
    """
    Route tunnel traffic to the appropriate WebSocket-connected client.

    The middleware inspects the ``Host`` header on every incoming request.
    If it matches ``<anything>.<domain>``, the request is routed through the
    corresponding tunnel.  Otherwise it passes to the next handler.
    """

    def __init__(self, app: object, settings: Settings, manager: TunnelManager) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._settings = settings
        self._manager = manager
        self._domain = settings.domain

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        host = request.headers.get("host", "").split(":")[0].lower()

        # Skip if this is the bare domain (API / health endpoints)
        if not host.endswith(f".{self._domain}"):
            return await call_next(request)

        # Extract subdomain
        m = _SUBDOMAIN_RE.match(host)
        if not m:
            return JSONResponse({"error": "invalid_host"}, status_code=400)

        subdomain = m.group("subdomain")
        tunnel = self._manager.lookup(subdomain)

        if tunnel is None:
            HTTP_TUNNEL_NOT_FOUND_TOTAL.inc()
            logger.warning("routing.tunnel_not_found", subdomain=subdomain, host=host)
            return JSONResponse(
                {
                    "error": "tunnel_not_found",
                    "detail": f"No active tunnel for subdomain '{subdomain}'. "
                    "Make sure your Hushh client is running.",
                },
                status_code=502,
            )

        return await route_request(tunnel, request, self._settings)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose body exceeds the configured limit."""

    def __init__(self, app: object, max_bytes: int) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > self._max_bytes:
            return JSONResponse(
                {
                    "error": "request_too_large",
                    "detail": f"Request body exceeds {self._max_bytes // (1024 * 1024)} MB limit.",
                },
                status_code=413,
            )
        return await call_next(request)
