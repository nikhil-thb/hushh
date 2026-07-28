"""
Hushh Tunnel Server — main FastAPI application.

Architecture
------------
                 ┌─────────────────────────────────────────────────┐
  Browser ──▶ Caddy (TLS) ──▶ FastAPI  ──▶ TunnelRoutingMiddleware │
                                │                                    │
                                ├──▶ /auth/*     (REST)             │
                                ├──▶ /api/*      (REST)             │
                                ├──▶ /health     (probe)            │
                                ├──▶ /metrics    (Prometheus)       │
                                └──▶ /tunnel/ws  (WebSocket)        │
                                                                     │
  Client CLI ──▶ WebSocket /tunnel/ws ──▶ TunnelManager             │
                                                                     └

WebSocket Protocol
------------------
1. Client connects to ``wss://hushh.online/tunnel/ws``
2. Client sends ``REGISTER`` with API key and desired subdomain
3. Server replies ``REGISTER_ACK`` with the public tunnel URL
4. Server receives HTTP requests, wraps as ``REQUEST``, sends to client
5. Client replies with ``RESPONSE``
6. Client sends periodic ``HEARTBEAT``; server replies ``HEARTBEAT_ACK``
7. Either side sends ``DISCONNECT`` to close
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import Response

from server.api import auth, health, stats, tunnels, users, dashboard
from server.api.auth import _decode_token
from server.config import Settings, get_settings
from server.core.metrics import AUTH_FAILURE_TOTAL, AUTH_SUCCESS_TOTAL
from server.core.middleware import RequestSizeLimitMiddleware, TunnelRoutingMiddleware
from server.core.tunnel_manager import (
    SubdomainConflictError,
    TunnelLimitExceededError,
    TunnelManager,
)
from server.db.database import close_db, get_session, init_db
from server.logging_config import configure_logging, get_logger
from server.models.user import User
from shared.protocol import (
    DisconnectMessage,
    ErrorMessage,
    HeartbeatAckMessage,
    HeartbeatMessage,
    MessageType,
    RegisterAckMessage,
    RegisterMessage,
    ResponseMessage,
    parse_client_message,
    serialize_message,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Admin seeding
# ---------------------------------------------------------------------------


async def _seed_admin(settings: Settings) -> None:
    """Create the admin user if no users exist in the database."""
    async for session in get_session():
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # already seeded

        admin, plain_key = User.create_with_key(
            email=settings.admin_email,
            password=settings.admin_password,
            is_admin=True,
            max_tunnels=100,
        )
        session.add(admin)
        await session.commit()
        logger.info(
            "startup.admin_seeded",
            email=settings.admin_email,
            api_key_preview=plain_key[:12] + "...",
        )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown lifecycle."""
    settings: Settings = app.state.settings

    configure_logging(log_level=settings.log_level, json_logs=settings.log_json)
    logger.info("startup.begin", domain=settings.domain, port=settings.port)

    await init_db()
    await _seed_admin(settings)

    manager = TunnelManager(settings)
    await manager.start()
    app.state.tunnel_manager = manager

    logger.info("startup.complete")
    yield

    logger.info("shutdown.begin")
    await manager.stop()
    await close_db()
    logger.info("shutdown.complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Hushh Tunnel",
        description=(
            "Production-ready reverse tunneling platform. "
            "Expose localhost services over HTTPS."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Store settings on app state for access in dependencies / middleware
    app.state.settings = settings

    # ── Middleware ──────────────────────────────────────────────────────────
    # Order matters: outermost is applied first
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in production via settings
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_bytes=settings.max_request_size_bytes,
    )
    # TunnelRoutingMiddleware is added after app.state.tunnel_manager is set in lifespan
    # We attach it here referencing the manager via app.state so it's always fresh
    app.add_middleware(
        _TunnelRoutingMiddlewareFactory,
        settings=settings,
    )

    # ── Routers ─────────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(tunnels.router)
    app.include_router(users.router)
    app.include_router(stats.router)
    app.include_router(health.router)
    app.include_router(dashboard.router)

    # ── Prometheus metrics ───────────────────────────────────────────────────
    if settings.metrics_enabled:

        @app.get("/metrics", include_in_schema=False)
        async def metrics() -> Response:
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST,
            )

    # ── WebSocket tunnel endpoint ────────────────────────────────────────────
    @app.websocket("/tunnel/ws")
    async def tunnel_websocket_endpoint(websocket: WebSocket) -> None:  # noqa: RUF029
        await _handle_tunnel_websocket(websocket, app.state)

    return app


# ---------------------------------------------------------------------------
# Middleware factory shim
# ---------------------------------------------------------------------------


class _TunnelRoutingMiddlewareFactory(TunnelRoutingMiddleware):
    """
    Thin subclass that defers reading ``tunnel_manager`` from ``app.state``
    at *request time* rather than at construction time (before lifespan runs).
    """

    def __init__(self, app: Any, settings: Settings) -> None:
        # We cannot call super().__init__ with manager here because the manager
        # doesn't exist yet.  Store settings and override dispatch.
        from starlette.middleware.base import BaseHTTPMiddleware

        BaseHTTPMiddleware.__init__(self, app)
        self._settings = settings
        self._domain = settings.domain

    async def dispatch(self, request: Request, call_next: Any) -> Any:  # type: ignore[override]
        # Lazily resolve the tunnel manager from app state
        try:
            self._manager = request.app.state.tunnel_manager
        except AttributeError:
            # Manager not ready yet (startup request)
            return await call_next(request)
        return await super().dispatch(request, call_next)


# ---------------------------------------------------------------------------
# WebSocket handler
# ---------------------------------------------------------------------------


async def _handle_tunnel_websocket(websocket: WebSocket, state: Any) -> None:
    """
    Handle the full lifecycle of a tunnel client WebSocket connection.

    Phase 1 — Handshake: authenticate and register.
    Phase 2 — Loop: receive HEARTBEAT / RESPONSE from client.
    """
    await websocket.accept()
    manager: TunnelManager = state.tunnel_manager
    settings: Settings = state.settings
    subdomain: str | None = None

    log = get_logger("tunnel_ws")

    try:
        # ── Phase 1: Handshake ───────────────────────────────────────────────
        raw = await websocket.receive_text()
        data: dict[str, Any] = json.loads(raw)

        if data.get("type") != MessageType.REGISTER:
            await websocket.send_text(
                serialize_message(
                    ErrorMessage(code="PROTOCOL_ERROR", detail="Expected REGISTER as first message.")
                )
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            register_msg = RegisterMessage.model_validate(data)
        except Exception as exc:
            await websocket.send_text(
                serialize_message(ErrorMessage(code="INVALID_MESSAGE", detail=str(exc)))
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # ── Authenticate ─────────────────────────────────────────────────────
        user = await _authenticate_api_key(register_msg.api_key, settings)
        if user is None:
            AUTH_FAILURE_TOTAL.labels(method="api_key").inc()
            await websocket.send_text(
                serialize_message(ErrorMessage(code="AUTH_FAILED", detail="Invalid API key."))
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        AUTH_SUCCESS_TOTAL.labels(method="api_key").inc()

        # ── Register tunnel ───────────────────────────────────────────────────
        try:
            tunnel = await manager.register(
                user_id=user.id,
                local_port=register_msg.local_port,
                client_version=register_msg.client_version,
                websocket=websocket,
                requested_subdomain=register_msg.requested_subdomain,
            )
        except SubdomainConflictError as exc:
            await websocket.send_text(
                serialize_message(ErrorMessage(code="SUBDOMAIN_CONFLICT", detail=str(exc)))
            )
            await websocket.close()
            return
        except TunnelLimitExceededError as exc:
            await websocket.send_text(
                serialize_message(ErrorMessage(code="TUNNEL_LIMIT_EXCEEDED", detail=str(exc)))
            )
            await websocket.close()
            return

        subdomain = tunnel.subdomain
        tunnel_url = f"https://{subdomain}.{settings.domain}"

        await websocket.send_text(
            serialize_message(
                RegisterAckMessage(
                    subdomain=subdomain,
                    tunnel_url=tunnel_url,
                )
            )
        )

        log.info("ws.registered", subdomain=subdomain, user_id=user.id)

        # ── Update Database ──────────────────────────────────────────────────
        from server.db.database import get_session
        from server.models.tunnel import TunnelRecord, TunnelStatus
        from datetime import datetime, UTC
        
        async for session in get_session():
            record = TunnelRecord(
                subdomain=subdomain,
                user_id=user.id,
                local_port=register_msg.local_port,
                client_version=register_msg.client_version,
                target=f"localhost:{register_msg.local_port}",
                status=TunnelStatus.ACTIVE,
                connected_at=datetime.now(UTC),
            )
            session.add(record)
            await session.commit()
            break

        # ── Phase 2: Message loop ─────────────────────────────────────────────
        while True:
            raw = await websocket.receive_text()
            await _handle_client_message(raw, tunnel, manager, log)

    except WebSocketDisconnect:
        log.info("ws.client_disconnected", subdomain=subdomain)
    except Exception as exc:
        log.error("ws.error", subdomain=subdomain, error=str(exc))
    finally:
        if subdomain is not None:
            await manager.unregister(subdomain, reason="websocket_closed")
            
            # Update database status
            from server.db.database import get_session
            from server.models.tunnel import TunnelRecord, TunnelStatus
            from sqlalchemy import update
            from datetime import datetime, UTC
            
            async for session in get_session():
                await session.execute(
                    update(TunnelRecord)
                    .where(TunnelRecord.subdomain == subdomain)
                    .values(
                        status=TunnelStatus.CLOSED, 
                        closed_at=datetime.now(UTC),
                        disconnected_at=datetime.now(UTC)
                    )
                )
                await session.commit()
                break


async def _handle_client_message(
    raw: str,
    tunnel: Any,
    manager: TunnelManager,
    log: Any,
) -> None:
    """Dispatch a raw JSON string from the client to the correct handler."""
    try:
        data: dict[str, Any] = json.loads(raw)
        msg = parse_client_message(data)
    except Exception as exc:
        log.warning("ws.invalid_message", error=str(exc))
        return

    match msg.type:
        case MessageType.HEARTBEAT:
            manager.heartbeat(tunnel.subdomain)
            async with tunnel.send_lock:
                await tunnel.websocket.send_text(serialize_message(HeartbeatAckMessage()))

        case MessageType.RESPONSE:
            resp_msg: ResponseMessage = msg  # type: ignore[assignment]
            fut = tunnel.pending_requests.get(resp_msg.request_id)
            if fut is not None and not fut.done():
                fut.set_result(resp_msg)
            else:
                log.warning(
                    "ws.orphan_response",
                    subdomain=tunnel.subdomain,
                    request_id=str(resp_msg.request_id),
                )

        case MessageType.DISCONNECT:
            disc: DisconnectMessage = msg  # type: ignore[assignment]
            log.info("ws.client_disconnect_msg", subdomain=tunnel.subdomain, reason=disc.reason)
            # The finally block in _handle_tunnel_websocket will clean up

        case _:
            log.warning("ws.unexpected_message_type", type=msg.type)


async def _authenticate_api_key(api_key: str, settings: Settings) -> User | None:
    """Look up a user by their plaintext API key."""
    async for session in get_session():
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.is_active == True))  # noqa: E712
        users = result.scalars().all()
        for user in users:
            if user.verify_api_key(api_key):
                return user
    return None


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def run() -> None:
    """CLI entrypoint — ``hushh-server``."""
    settings = get_settings()
    configure_logging(log_level=settings.log_level, json_logs=settings.log_json)
    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        log_config=None,  # use structlog
        access_log=False,
    )


app = create_app()

if __name__ == "__main__":
    run()
