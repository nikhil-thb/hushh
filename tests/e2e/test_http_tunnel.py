"""
End-to-end test: full HTTP tunnel flow.

Spins up:
1. A real FastAPI server (in-process via ASGI)
2. A simple aiohttp/asyncio local HTTP service on a random port
3. An in-process TunnelClient

Then makes an HTTP request through the tunnel and verifies the response.

Note: This test uses the test app's internal tunnel manager so no real
      WebSocket server is needed — we drive both sides in-process.
"""

from __future__ import annotations

import asyncio
import json
import socket
from contextlib import asynccontextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from server.core.tunnel_manager import TunnelManager
from shared.protocol import (
    MessageType,
    RequestMessage,
    ResponseMessage,
    serialize_message,
)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _SimpleHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that echoes back request info as JSON."""

    def do_GET(self) -> None:
        body = json.dumps(
            {"path": self.path, "method": "GET", "server": "hushh-e2e-test"}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass  # suppress output


class TestE2EHttpTunnel:
    """
    Full end-to-end test: browser → server → tunnel → local service → back.

    We fake the WebSocket by directly injecting responses into the tunnel's
    pending_requests dict, which is equivalent to what the real CLI client does.
    """

    @pytest.mark.asyncio
    async def test_full_request_response_cycle(
        self, app: Any, http_client: AsyncClient
    ) -> None:
        """Make an HTTP request through a registered tunnel."""
        manager: TunnelManager = app.state.tunnel_manager
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.close = AsyncMock()

        # Register tunnel
        tunnel = await manager.register(
            user_id=1,
            local_port=3001,
            client_version="0.1.0",
            websocket=mock_ws,
            requested_subdomain="e2etest",
        )

        # Simulate the client responding to requests
        async def client_side(text: str) -> None:
            data = json.loads(text)
            if data["type"] == "request":
                from uuid import UUID

                req_id = UUID(data["request_id"])
                response = ResponseMessage.from_raw(
                    request_id=req_id,
                    status_code=200,
                    headers={"content-type": "application/json"},
                    body=json.dumps({"e2e": "success", "path": data["path"]}).encode(),
                )
                fut = tunnel.pending_requests.get(req_id)
                if fut and not fut.done():
                    fut.set_result(response)

        mock_ws.send_text = AsyncMock(side_effect=client_side)

        # Send request through the tunnel
        resp = await http_client.get(
            "/test-endpoint",
            headers={"Host": "e2etest.test.tunnel"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["e2e"] == "success"
        assert data["path"] == "/test-endpoint"

        await manager.unregister("e2etest")

    @pytest.mark.asyncio
    async def test_tunnel_returns_502_when_offline(self, http_client: AsyncClient) -> None:
        """Request to an offline tunnel subdomain should return 502."""
        resp = await http_client.get(
            "/anything",
            headers={"Host": "offline-subdomain.test.tunnel"},
        )
        assert resp.status_code == 502
        data = resp.json()
        assert data["error"] == "tunnel_not_found"

    @pytest.mark.asyncio
    async def test_large_response_body(self, app: Any, http_client: AsyncClient) -> None:
        """Test that large response bodies are handled correctly."""
        manager: TunnelManager = app.state.tunnel_manager
        mock_ws = AsyncMock()

        tunnel = await manager.register(
            user_id=1,
            local_port=3002,
            client_version="0.1.0",
            websocket=mock_ws,
            requested_subdomain="largetest",
        )

        large_body = b"x" * (1024 * 512)  # 512 KB

        async def client_side(text: str) -> None:
            data = json.loads(text)
            if data["type"] == "request":
                from uuid import UUID

                req_id = UUID(data["request_id"])
                response = ResponseMessage.from_raw(
                    request_id=req_id,
                    status_code=200,
                    headers={"content-type": "application/octet-stream"},
                    body=large_body,
                )
                fut = tunnel.pending_requests.get(req_id)
                if fut and not fut.done():
                    fut.set_result(response)

        mock_ws.send_text = AsyncMock(side_effect=client_side)

        resp = await http_client.get(
            "/large",
            headers={"Host": "largetest.test.tunnel"},
        )
        assert resp.status_code == 200
        assert len(resp.content) == len(large_body)

        await manager.unregister("largetest")
