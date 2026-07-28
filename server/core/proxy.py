"""
HTTP → Tunnel proxy logic.

``route_request`` translates an incoming FastAPI ``Request`` into a
:class:`~shared.protocol.RequestMessage`, sends it over the tunnel's
WebSocket, waits for the matching :class:`~shared.protocol.ResponseMessage`,
and returns a FastAPI ``Response``.

The tunnel WebSocket is shared between this function and the WS handler
(:func:`server.main.tunnel_websocket_endpoint`).  Concurrent sends are
serialized with the tunnel's ``send_lock``.
"""

from __future__ import annotations

import asyncio
import time
from uuid import UUID, uuid4

import structlog
from fastapi import Request, Response
from shared.protocol import RequestMessage, ResponseMessage, serialize_message

from server.config import Settings
from server.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUEST_SIZE_BYTES,
    HTTP_REQUEST_TIMEOUT_TOTAL,
    HTTP_REQUESTS_TOTAL,
    HTTP_RESPONSE_SIZE_BYTES,
)
from server.core.tunnel_manager import Tunnel

logger = structlog.get_logger(__name__)

# Headers that should not be forwarded to the local service
_HOP_BY_HOP_HEADERS = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "host",  # we'll rewrite host to localhost
    }
)


async def route_request(
    tunnel: Tunnel,
    request: Request,
    settings: Settings,
) -> Response:
    """
    Forward an HTTP request through the tunnel and return the response.

    Args:
        tunnel: The live tunnel to send the request through.
        request: The incoming FastAPI Request.
        settings: Application settings (for timeout).

    Returns:
        A :class:`fastapi.Response` built from the tunnel's reply.

    Raises:
        asyncio.TimeoutError: propagated to the caller if the tunnel doesn't respond.
    """
    start = time.monotonic()
    request_id: UUID = uuid4()

    # ── Build request body ─────────────────────────────────────────────────
    body = await request.body()
    HTTP_REQUEST_SIZE_BYTES.observe(len(body))

    # ── Sanitize headers ───────────────────────────────────────────────────
    headers: dict[str, str] = {
        k.lower(): v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS
    }
    headers["x-forwarded-for"] = request.client.host if request.client else "unknown"
    headers["x-forwarded-proto"] = "https"

    query = str(request.url.query)
    path = request.url.path

    msg = RequestMessage.from_raw(
        method=request.method,
        path=path,
        query=query,
        headers=headers,
        body=body,
        request_id=request_id,
    )

    # ── Register future for response ───────────────────────────────────────
    loop = asyncio.get_running_loop()
    fut: asyncio.Future[ResponseMessage] = loop.create_future()
    tunnel.pending_requests[request_id] = fut

    # ── Send request over WebSocket ────────────────────────────────────────
    try:
        async with tunnel.send_lock:
            await tunnel.websocket.send_text(serialize_message(msg))
    except Exception as exc:
        tunnel.pending_requests.pop(request_id, None)
        logger.error("proxy.send_error", subdomain=tunnel.subdomain, error=str(exc))
        return Response(status_code=502, content="Tunnel send error.")

    # ── Await response ─────────────────────────────────────────────────────
    try:
        resp_msg: ResponseMessage = await asyncio.wait_for(fut, timeout=settings.request_timeout)
    except TimeoutError:
        tunnel.pending_requests.pop(request_id, None)
        HTTP_REQUEST_TIMEOUT_TOTAL.inc()
        logger.warning("proxy.timeout", subdomain=tunnel.subdomain, path=path, method=request.method)
        return Response(status_code=504, content="Tunnel timed out.")
    except asyncio.CancelledError:
        tunnel.pending_requests.pop(request_id, None)
        return Response(status_code=503, content="Tunnel disconnected.")
    finally:
        tunnel.pending_requests.pop(request_id, None)

    # ── Record metrics ─────────────────────────────────────────────────────
    elapsed = time.monotonic() - start
    HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method).observe(elapsed)
    HTTP_REQUESTS_TOTAL.labels(method=request.method, status=str(resp_msg.status_code)).inc()
    HTTP_RESPONSE_SIZE_BYTES.observe(len(resp_msg.body))

    # ── Build response ─────────────────────────────────────────────────────
    resp_body = resp_msg.decode_body()

    # Filter hop-by-hop from response headers too
    resp_headers: dict[str, str] = {
        k.lower(): v
        for k, v in resp_msg.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS
    }

    logger.info(
        "proxy.request",
        subdomain=tunnel.subdomain,
        method=request.method,
        path=path,
        status=resp_msg.status_code,
        duration_ms=round(elapsed * 1000, 1),
    )

    # ── Database metrics ───────────────────────────────────────────────────
    from sqlalchemy import select, update

    from server.db.database import get_session
    from server.models.request_log import RequestLog
    from server.models.tunnel import TunnelRecord

    async def _log_request() -> None:
        try:
            async for session in get_session():
                # Get the tunnel record ID
                res = await session.execute(select(TunnelRecord.id).where(TunnelRecord.subdomain == tunnel.subdomain))
                tunnel_id = res.scalar_one_or_none()
                if tunnel_id:
                    # Add request log
                    log = RequestLog(
                        tunnel_id=tunnel_id,
                        method=request.method,
                        path=path,
                        status=resp_msg.status_code,
                        duration_ms=int(elapsed * 1000)
                    )
                    session.add(log)

                    # Update metrics
                    await session.execute(
                        update(TunnelRecord)
                        .where(TunnelRecord.id == tunnel_id)
                        .values(
                            request_count=TunnelRecord.request_count + 1,
                            bytes_uploaded=TunnelRecord.bytes_uploaded + len(body),
                            bytes_downloaded=TunnelRecord.bytes_downloaded + len(resp_msg.body)
                        )
                    )
                    await session.commit()
                break
        except Exception as e:
            logger.error("proxy.log_request_failed", error=str(e), exc_info=True)

    # Fire and forget database update
    asyncio.create_task(_log_request())

    return Response(
        content=resp_body,
        status_code=resp_msg.status_code,
        headers=resp_headers,
        media_type=resp_headers.get("content-type"),
    )
