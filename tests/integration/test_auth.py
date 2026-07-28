"""
Integration tests for the authentication API.

Tests login, logout, whoami, and unauthorized access.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from server.config import Settings


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, http_client: AsyncClient, settings: Settings) -> None:
        resp = await http_client.post(
            "/auth/login",
            json={"email": settings.admin_email, "password": settings.admin_password},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "api_key" in data
        assert data["api_key"].startswith("hushh_")
        assert data["email"] == settings.admin_email

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, http_client: AsyncClient, settings: Settings) -> None:
        resp = await http_client.post(
            "/auth/login",
            json={"email": settings.admin_email, "password": "wrong_password"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_email(self, http_client: AsyncClient) -> None:
        resp = await http_client.post(
            "/auth/login",
            json={"email": "nobody@test.com", "password": "whatever"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, http_client: AsyncClient) -> None:
        resp = await http_client.post(
            "/auth/login",
            json={"email": "not-an-email", "password": "password"},
        )
        assert resp.status_code == 422  # validation error


class TestWhoAmI:
    @pytest.mark.asyncio
    async def test_whoami_with_valid_token(self, http_client: AsyncClient, admin_token: str, settings: Settings) -> None:
        resp = await http_client.get(
            "/auth/whoami",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == settings.admin_email
        assert data["is_admin"] is True

    @pytest.mark.asyncio
    async def test_whoami_no_token(self, http_client: AsyncClient) -> None:
        resp = await http_client.get("/auth/whoami")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_whoami_invalid_token(self, http_client: AsyncClient) -> None:
        resp = await http_client.get(
            "/auth/whoami",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401


class TestRotateKey:
    @pytest.mark.asyncio
    async def test_rotate_returns_new_key(self, http_client: AsyncClient, admin_token: str) -> None:
        resp = await http_client.post(
            "/auth/rotate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "api_key" in data
        assert data["api_key"].startswith("hushh_")
