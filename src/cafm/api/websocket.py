"""WebSocket support for real-time Command Center updates."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from cafm.core.events import Event, EventBus, EventType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    Clients connect via /ws/dashboard and receive real-time events
    about connector changes, work order updates, alerts, etc.
    """

    def __init__(self) -> None:
        self._active_connections: list[WebSocket] = []
        self._subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channels: list[str] | None = None) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self._active_connections.append(websocket)

        # Subscribe to specific channels or all
        if channels:
            for ch in channels:
                self._subscriptions.setdefault(ch, set()).add(websocket)
        else:
            self._subscriptions.setdefault("*", set()).add(websocket)

        logger.info(
            "WebSocket connected. Total: %d, Channels: %s",
            len(self._active_connections),
            channels or ["*"],
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
        for channel_subs in self._subscriptions.values():
            channel_subs.discard(websocket)
        logger.info("WebSocket disconnected. Remaining: %d", len(self._active_connections))

    async def broadcast(self, message: dict[str, Any], channel: str = "*") -> None:
        """Send a message to all subscribers of a channel."""
        payload = json.dumps(message, default=str)

        # Send to specific channel subscribers
        targets = self._subscriptions.get(channel, set())
        # Also send to wildcard subscribers
        targets = targets | self._subscriptions.get("*", set())

        disconnected: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception:
            self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        return len(self._active_connections)


# Global connection manager instance
ws_manager = ConnectionManager()


def create_event_bridge(event_bus: EventBus, manager: ConnectionManager) -> None:
    """Wire the EventBus to the WebSocket manager.

    Subscribes to key event types and broadcasts them to connected clients.
    """
    event_channel_map: dict[EventType, str] = {
        EventType.CONNECTOR_CONNECTED: "connectors",
        EventType.CONNECTOR_DISCONNECTED: "connectors",
        EventType.CONNECTOR_ERROR: "connectors",
        EventType.SCHEMA_DISCOVERED: "schema",
        EventType.PIPELINE_STARTED: "pipelines",
        EventType.PIPELINE_COMPLETED: "pipelines",
        EventType.PIPELINE_FAILED: "pipelines",
        EventType.RECORD_CREATED: "records",
        EventType.RECORD_UPDATED: "records",
        EventType.RECORD_DELETED: "records",
    }

    async def _bridge_handler(event: Event) -> None:
        channel = event_channel_map.get(event.type, "general")
        await manager.broadcast(
            message={
                "event_type": event.type.value,
                "source": event.source,
                "payload": event.payload,
                "timestamp": event.timestamp,
            },
            channel=channel,
        )

    for event_type in event_channel_map:
        event_bus.subscribe(event_type, _bridge_handler)

    logger.info("EventBus → WebSocket bridge established for %d event types", len(event_channel_map))


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for real-time dashboard updates.

    Clients can send JSON messages to subscribe to channels:
        {"action": "subscribe", "channels": ["connectors", "records"]}
    """
    channels = websocket.query_params.get("channels", "").split(",")
    channels = [c.strip() for c in channels if c.strip()] or None

    await ws_manager.connect(websocket, channels)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "subscribe":
                    new_channels = msg.get("channels", [])
                    for ch in new_channels:
                        ws_manager._subscriptions.setdefault(ch, set()).add(websocket)
                    await ws_manager.send_personal(websocket, {
                        "type": "subscribed",
                        "channels": new_channels,
                    })
                elif msg.get("action") == "ping":
                    await ws_manager.send_personal(websocket, {"type": "pong"})
            except json.JSONDecodeError:
                await ws_manager.send_personal(websocket, {
                    "type": "error",
                    "message": "Invalid JSON",
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
