"""
Tunnel client — WebSocket loop with auto-reconnect.

``TunnelClient`` manages the full lifecycle:
1. Connect to server WebSocket
2. Send REGISTER
3. Receive REGISTER_ACK → emit public URL via callback
4. Loop: receive REQUEST → forward to localhost → send RESPONSE
5. Send HEARTBEAT every ``heartbeat_interval`` seconds
6. On disconnect: exponential backoff reconnect (up to ``max_retries``)
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import structlog
import websockets
from shared.protocol import (
    DisconnectMessage,
    HeartbeatMessage,
    MessageType,
    RegisterMessage,
    RequestMessage,
    parse_server_message,
    serialize_message,
)
from websockets.exceptions import ConnectionClosed

from client.config import ClientConfig
from client.proxy import forward

logger = structlog.get_logger(__name__)

OnConnectedCallback = Callable[[str, str], None]  # (subdomain, tunnel_url)
OnRequestCallback = Callable[[str, str, int], None]  # (method, path, status)
OnDisconnectCallback = Callable[[str], None]  # (reason)


class TunnelClient:
    """
    Async tunnel client with reconnect support.

    Args:
        config: Loaded client configuration (server URL, API key, etc.).
        local_port: Port of the local service to tunnel.
        requested_subdomain: Optional custom subdomain.
        heartbeat_interval: Seconds between heartbeat messages.
        max_retries: Maximum reconnect attempts (0 = unlimited).
        on_connected: Callback invoked with (subdomain, tunnel_url) on each connect.
        on_request: Callback invoked with (method, path, status) after each proxy request.
        on_disconnect: Callback invoked with reason string on disconnect.
    """

    def __init__(
        self,
        config: ClientConfig,
        local_port: int,
        requested_subdomain: str | None = None,
        heartbeat_interval: int = 15,
        max_retries: int = 0,
        on_connected: OnConnectedCallback | None = None,
        on_request: OnRequestCallback | None = None,
        on_disconnect: OnDisconnectCallback | None = None,
    ) -> None:
        self._config = config
        self._local_port = local_port
        self._requested_subdomain = requested_subdomain
        self._heartbeat_interval = heartbeat_interval
        self._max_retries = max_retries
        self._on_connected = on_connected
        self._on_request = on_request
        self._on_disconnect = on_disconnect
        self._stop_event = asyncio.Event()
        self._current_subdomain: str | None = None

    async def run(self) -> None:
        """Main entry — connect and reconnect until stopped."""
        attempt = 0
        backoff = 1.0

        while not self._stop_event.is_set():
            try:
                await self._connect_and_run()
                # If we get here without exception, the server disconnected us gracefully
                attempt = 0
                backoff = 1.0
            except ConnectionClosed as exc:
                reason = f"Connection closed: code={exc.rcvd.code if exc.rcvd else '?'}"
                logger.warning("tunnel.disconnected", reason=reason)
                if self._on_disconnect:
                    self._on_disconnect(reason)
            except OSError as exc:
                logger.error("tunnel.connect_error", error=str(exc))
                if self._on_disconnect:
                    self._on_disconnect(f"Network error: {exc}")
            except Exception as exc:
                logger.error("tunnel.unexpected_error", error=str(exc))
                if self._on_disconnect:
                    self._on_disconnect(f"Error: {exc}")

            if self._stop_event.is_set():
                break

            attempt += 1
            if self._max_retries > 0 and attempt >= self._max_retries:
                logger.error("tunnel.max_retries_exceeded", attempt=attempt)
                break

            logger.info("tunnel.reconnecting", attempt=attempt, backoff_seconds=backoff)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=backoff)
            except TimeoutError:
                pass
            backoff = min(backoff * 2, 30.0)

    def stop(self) -> None:
        """Signal the client to stop reconnecting."""
        self._stop_event.set()

    async def _connect_and_run(self) -> None:
        ws_url = self._config.tunnel_ws_url
        logger.info("tunnel.connecting", url=ws_url)

        async with websockets.connect(  # type: ignore[attr-defined]
            ws_url,
            ping_interval=None,  # we manage heartbeats ourselves
            open_timeout=15,
            close_timeout=5,
        ) as ws:
            # ── Register ───────────────────────────────────────────────────────
            register_msg = RegisterMessage(
                api_key=self._config.api_key or "",
                requested_subdomain=self._requested_subdomain,
                local_port=self._local_port,
            )
            await ws.send(serialize_message(register_msg))

            raw = await ws.recv()
            data: dict[str, Any] = json.loads(raw)
            msg = parse_server_message(data)

            if msg.type == MessageType.ERROR:
                raise ConnectionError(f"Server error: {msg.code} — {msg.detail}")  # type: ignore[union-attr]

            if msg.type != MessageType.REGISTER_ACK:
                raise ConnectionError(f"Expected REGISTER_ACK, got {msg.type}")

            self._current_subdomain = msg.subdomain  # type: ignore[union-attr]
            tunnel_url: str = msg.tunnel_url  # type: ignore[union-attr]

            if self._on_connected:
                self._on_connected(self._current_subdomain, tunnel_url)

            logger.info("tunnel.connected", subdomain=self._current_subdomain, url=tunnel_url)

            # ── Start heartbeat task ───────────────────────────────────────────
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(ws), name="heartbeat"
            )

            try:
                await self._message_loop(ws)
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    async def _heartbeat_loop(self, ws: Any) -> None:
        """Send HEARTBEAT every ``heartbeat_interval`` seconds."""
        while True:
            await asyncio.sleep(self._heartbeat_interval)
            try:
                await ws.send(serialize_message(HeartbeatMessage()))
                logger.debug("tunnel.heartbeat_sent")
            except Exception as exc:
                logger.warning("tunnel.heartbeat_error", error=str(exc))
                break

    async def _message_loop(self, ws: Any) -> None:
        """Receive messages from the server and dispatch them."""
        async for raw in ws:
            if self._stop_event.is_set():
                await ws.send(serialize_message(DisconnectMessage(reason="client_stop")))
                break
            try:
                data: dict[str, Any] = json.loads(raw)
                msg = parse_server_message(data)
            except Exception as exc:
                logger.warning("tunnel.invalid_message", error=str(exc))
                continue

            match msg.type:
                case MessageType.REQUEST:
                    # Dispatch concurrently — don't block the loop
                    asyncio.create_task(
                        self._handle_request(ws, msg),  # type: ignore[arg-type]
                        name=f"req-{msg.message_id}",  # type: ignore[union-attr]
                    )
                case MessageType.HEARTBEAT_ACK:
                    logger.debug("tunnel.heartbeat_ack")
                case MessageType.DISCONNECT:
                    reason = getattr(msg, "reason", "")
                    logger.info("tunnel.server_disconnect", reason=reason)
                    if reason == "api_disconnect":
                        self.stop()
                    break
                case MessageType.ERROR:
                    logger.error("tunnel.server_error", code=getattr(msg, "code", "?"), detail=getattr(msg, "detail", ""))
                case _:
                    logger.warning("tunnel.unknown_message_type", type=msg.type)

    async def _handle_request(self, ws: Any, request_msg: RequestMessage) -> None:
        """Forward a single REQUEST to localhost and send the RESPONSE."""
        response_msg = await forward(request_msg, local_port=self._local_port)

        if self._on_request:
            self._on_request(request_msg.method, request_msg.path, response_msg.status_code)

        try:
            await ws.send(serialize_message(response_msg))
        except Exception as exc:
            logger.error(
                "tunnel.send_response_error",
                request_id=str(request_msg.request_id),
                error=str(exc),
            )
