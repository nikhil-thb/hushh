"""Unit tests for TunnelManager."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from server.config import Settings
from server.core.tunnel_manager import (
    SubdomainConflictError,
    TunnelLimitExceededError,
    TunnelManager,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        domain="test.tunnel",
        host="127.0.0.1",
        port=8001,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test_secret_key_at_least_32_chars_long",
        admin_email="admin@test.com",
        admin_password="testpassword",
        max_tunnels_per_user=2,
        max_concurrent_tunnels=5,
        heartbeat_timeout=60,
        heartbeat_interval=10,
        idle_timeout=3600,
        request_timeout=5,
        log_json=False,
    )


@pytest.fixture
def mock_ws() -> MagicMock:
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    return ws



class TestTunnelManagerRegistration:
    @pytest.mark.asyncio
    async def test_register_generates_subdomain(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            tunnel = await manager.register(
                user_id=1,
                local_port=3000,
                client_version="0.1.0",
                websocket=mock_ws,
            )
            assert tunnel.subdomain
            assert len(tunnel.subdomain) == 8
            assert manager.lookup(tunnel.subdomain) is tunnel
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_register_custom_subdomain(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            tunnel = await manager.register(
                user_id=1,
                local_port=3000,
                client_version="0.1.0",
                websocket=mock_ws,
                requested_subdomain="myapi",
            )
            assert tunnel.subdomain == "myapi"
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_subdomain_conflict(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            await manager.register(
                user_id=1,
                local_port=3000,
                client_version="0.1.0",
                websocket=mock_ws,
                requested_subdomain="taken",
            )
            with pytest.raises(SubdomainConflictError):
                await manager.register(
                    user_id=2,
                    local_port=4000,
                    client_version="0.1.0",
                    websocket=AsyncMock(),
                    requested_subdomain="taken",
                )
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_user_tunnel_limit(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            for i in range(settings.max_tunnels_per_user):
                await manager.register(
                    user_id=99,
                    local_port=3000 + i,
                    client_version="0.1.0",
                    websocket=AsyncMock(),
                )
            with pytest.raises(TunnelLimitExceededError):
                await manager.register(
                    user_id=99,
                    local_port=9000,
                    client_version="0.1.0",
                    websocket=AsyncMock(),
                )
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_invalid_subdomain(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            with pytest.raises(ValueError):
                await manager.register(
                    user_id=1,
                    local_port=3000,
                    client_version="0.1.0",
                    websocket=mock_ws,
                    requested_subdomain="UPPERCASE",
                )
        finally:
            await manager.stop()


class TestTunnelManagerHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_updates_last_seen(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            tunnel = await manager.register(
                user_id=1,
                local_port=3000,
                client_version="0.1.0",
                websocket=mock_ws,
            )
            before = tunnel.last_seen_at
            await asyncio.sleep(0.01)
            result = manager.heartbeat(tunnel.subdomain)
            assert result is True
            assert tunnel.last_seen_at > before
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_heartbeat_unknown_subdomain(self, settings: Settings) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            result = manager.heartbeat("nonexistent")
            assert result is False
        finally:
            await manager.stop()


class TestTunnelManagerUnregister:
    @pytest.mark.asyncio
    async def test_unregister_removes_tunnel(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            tunnel = await manager.register(
                user_id=1,
                local_port=3000,
                client_version="0.1.0",
                websocket=mock_ws,
            )
            subdomain = tunnel.subdomain
            await manager.unregister(subdomain)
            assert manager.lookup(subdomain) is None
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_unregister_cancels_pending_futures(self, settings: Settings, mock_ws: MagicMock) -> None:
        manager = TunnelManager(settings)
        await manager.start()
        try:
            tunnel = await manager.register(
                user_id=1,
                local_port=3000,
                client_version="0.1.0",
                websocket=mock_ws,
            )
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            from uuid import uuid4
            req_id = uuid4()
            tunnel.pending_requests[req_id] = fut

            await manager.unregister(tunnel.subdomain)
            assert fut.cancelled()
        finally:
            await manager.stop()
