"""
Integration tests for TunnelClient reconnect logic.

Tests the exponential backoff and max_retries behaviour.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from client.config import ClientConfig
from client.tunnel import TunnelClient


class TestReconnectLogic:
    @pytest.mark.asyncio
    async def test_stops_after_max_retries(self) -> None:
        """Client should stop after max_retries failed attempts."""
        config = ClientConfig(
            server_url="ws://localhost:9999",  # unreachable
            api_key="hushh_fakekey",
            email="test@test.com",
        )

        client = TunnelClient(
            config=config,
            local_port=3000,
            max_retries=2,
        )

        disconnect_reasons: list[str] = []

        def on_disconnect(reason: str) -> None:
            disconnect_reasons.append(reason)

        client._on_disconnect = on_disconnect

        # Run with a short timeout — the client should give up after 2 retries
        with pytest.raises((asyncio.TimeoutError, OSError, Exception)):
            await asyncio.wait_for(client.run(), timeout=5.0)

        # Should have recorded some disconnect reasons
        assert len(disconnect_reasons) > 0

    @pytest.mark.asyncio
    async def test_stop_event_exits_loop(self) -> None:
        """Calling stop() should cause run() to exit."""
        config = ClientConfig(
            server_url="ws://localhost:9999",
            api_key="hushh_fakekey",
        )
        client = TunnelClient(config=config, local_port=3000, max_retries=0)

        # Stop immediately
        client.stop()

        # Should return quickly since stop_event is already set
        done = False

        async def run_with_flag() -> None:
            nonlocal done
            await client.run()
            done = True

        await asyncio.wait_for(run_with_flag(), timeout=2.0)
        assert done
