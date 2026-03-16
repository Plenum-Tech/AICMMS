"""Tests for WebSocket connection manager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cafm.api.websocket import ConnectionManager


class TestConnectionManager:
    """Tests for the WebSocket connection manager."""

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    def _mock_websocket(self) -> MagicMock:
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.receive_text = AsyncMock()
        return ws

    async def test_connect(self, manager):
        ws = self._mock_websocket()
        await manager.connect(ws)
        assert manager.connection_count == 1
        ws.accept.assert_called_once()

    async def test_connect_with_channels(self, manager):
        ws = self._mock_websocket()
        await manager.connect(ws, channels=["connectors", "records"])
        assert manager.connection_count == 1
        assert ws in manager._subscriptions.get("connectors", set())
        assert ws in manager._subscriptions.get("records", set())

    async def test_disconnect(self, manager):
        ws = self._mock_websocket()
        await manager.connect(ws)
        assert manager.connection_count == 1
        manager.disconnect(ws)
        assert manager.connection_count == 0

    async def test_broadcast(self, manager):
        ws1 = self._mock_websocket()
        ws2 = self._mock_websocket()
        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.broadcast({"type": "test", "data": "hello"})
        assert ws1.send_text.called
        assert ws2.send_text.called

    async def test_broadcast_to_channel(self, manager):
        ws1 = self._mock_websocket()
        ws2 = self._mock_websocket()
        await manager.connect(ws1, channels=["connectors"])
        await manager.connect(ws2, channels=["records"])

        await manager.broadcast({"type": "test"}, channel="connectors")
        assert ws1.send_text.called
        # ws2 is not subscribed to "connectors" and not to wildcard
        assert not ws2.send_text.called

    async def test_send_personal(self, manager):
        ws = self._mock_websocket()
        await manager.connect(ws)
        await manager.send_personal(ws, {"type": "personal", "msg": "hi"})
        ws.send_text.assert_called()

    async def test_broadcast_handles_disconnect(self, manager):
        ws = self._mock_websocket()
        ws.send_text = AsyncMock(side_effect=Exception("connection closed"))
        await manager.connect(ws)
        assert manager.connection_count == 1

        # Should not raise, and should disconnect the bad client
        await manager.broadcast({"type": "test"})
        assert manager.connection_count == 0
