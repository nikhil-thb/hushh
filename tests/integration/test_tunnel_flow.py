"""
Integration tests for the full tunnel request/response flow.

Uses an in-process FastAPI app, async HTTP test client, and a mock
WebSocket to simulate a connected tunnel client.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from server.core.tunnel_manager import TunnelManager
from shared.protocol import (
    ResponseMessage,
)


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health(self, http_client: AsyncClient) -> None:
        resp = await http_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_readyz(self, http_client: AsyncClient) -> None:
        resp = await http_client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "checks" in data


class TestTunnelAPI:
    @pytest.mark.asyncio
    async def test_list_tunnels_authenticated(
        self, http_client: AsyncClient, admin_token: str
    ) -> None:
        resp = await http_client.get(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_list_tunnels_unauthenticated(self, http_client: AsyncClient) -> None:
        resp = await http_client.get("/api/tunnels")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_unknown_tunnel(
        self, http_client: AsyncClient, admin_token: str
    ) -> None:
        resp = await http_client.get(
            "/api/tunnels/nosuchsubdomain",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestProxyFlow:
    """
    Test the HTTP → tunnel → response round-trip using mock futures.
    """

    @pytest.mark.asyncio
    async def test_tunnel_not_found_returns_502(self, http_client: AsyncClient) -> None:
        # Request to a tunnel subdomain that doesn't exist
        resp = await http_client.get(
            "/some-path",
            headers={"Host": "nonexistent.test.tunnel"},
        )
        assert resp.status_code == 502

    @pytest.mark.asyncio
    async def test_proxy_resolves_response(
        self, app: Any, http_client: AsyncClient, admin_api_key: str
    ) -> None:
        """Register a mock tunnel and simulate the client responding to a request."""
        manager: TunnelManager = app.state.tunnel_manager
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.close = AsyncMock()

        # Register a fake tunnel
        tunnel = await manager.register(
            user_id=1,
            local_port=3000,
            client_version="0.1.0",
            websocket=mock_ws,
            requested_subdomain="proxytest",
        )

        # Intercept the send_text call and inject a response
        async def fake_send(text: str) -> None:
            data = json.loads(text)
            if data["type"] == "request":
                req_id_str = data["request_id"]
                from uuid import UUID

                req_id = UUID(req_id_str)
                response = ResponseMessage.from_raw(
                    request_id=req_id,
                    status_code=200,
                    headers={"content-type": "application/json"},
                    body=b'{"tunnel": "works"}',
                )
                fut = tunnel.pending_requests.get(req_id)
                if fut is not None and not fut.done():
                    fut.set_result(response)

        mock_ws.send_text = AsyncMock(side_effect=fake_send)

        resp = await http_client.get(
            "/api-path",
            headers={"Host": "proxytest.test.tunnel"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"tunnel": "works"}

        # Cleanup
        await manager.unregister("proxytest")
