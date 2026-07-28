"""
Pytest configuration and shared fixtures.

Fixtures:
    settings        — test Settings instance (in-memory SQLite)
    app             — FastAPI test application
    client          — HTTPX async test client
    db_session      — async database session
    tunnel_manager  — TunnelManager instance
    mock_websocket  — Mock WebSocket for unit tests
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import WebSocket
from httpx import ASGITransport, AsyncClient
from server.config import Settings
from server.core.tunnel_manager import Tunnel, TunnelManager
from server.db.database import Base, get_session
from server.main import create_app
from server.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        domain="test.tunnel",
        host="127.0.0.1",
        port=8001,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test_secret_key_at_least_32_chars_long",
        admin_email="admin@test.com",
        admin_password="testpassword",
        log_json=False,
        log_level="DEBUG",
        max_tunnels_per_user=3,
        max_concurrent_tunnels=100,
        heartbeat_timeout=60,
        heartbeat_interval=10,
        idle_timeout=3600,
        request_timeout=5,
    )


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def engine(settings: Settings):
    _engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# TunnelManager
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def tunnel_manager(settings: Settings) -> AsyncGenerator[TunnelManager, None]:
    manager = TunnelManager(settings)
    await manager.start()
    yield manager
    await manager.stop()


# ---------------------------------------------------------------------------
# Mock WebSocket
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_websocket() -> MagicMock:
    ws = AsyncMock(spec=WebSocket)
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


# ---------------------------------------------------------------------------
# FastAPI app + HTTPX client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def app(settings: Settings, engine):
    """Create a FastAPI test application with in-memory DB."""
    # Override the database session to use the test engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    _app = create_app(settings)

    # Override the get_session dependency
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    _app.dependency_overrides[get_session] = override_get_session

    # Seed admin user
    async with factory() as session:
        admin, _ = User.create_with_key(
            email=settings.admin_email,
            password=settings.admin_password,
            is_admin=True,
        )
        session.add(admin)
        await session.commit()

    yield _app


@pytest_asyncio.fixture(scope="function")
async def http_client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def admin_token(http_client: AsyncClient, settings: Settings) -> str:
    """Login as admin and return the access token."""
    resp = await http_client.post(
        "/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def admin_api_key(http_client: AsyncClient, settings: Settings) -> str:
    resp = await http_client.post(
        "/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert resp.status_code == 200
    return resp.json()["api_key"]


# ---------------------------------------------------------------------------
# Tunnel fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_tunnel(tunnel_manager: TunnelManager, mock_websocket: MagicMock) -> Tunnel:
    """Register a mock tunnel and return it."""
    user = MagicMock()
    user.id = 1
    tunnel = await tunnel_manager.register(
        user_id=1,
        local_port=3000,
        client_version="0.1.0",
        websocket=mock_websocket,
        requested_subdomain="testsubdomain",
    )
    return tunnel
