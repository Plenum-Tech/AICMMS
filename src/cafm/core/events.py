"""Publish-subscribe event bus for decoupled communication between components."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """Well-known event types emitted by the platform."""

    # Connector lifecycle
    CONNECTOR_REGISTERED = "connector.registered"
    CONNECTOR_CONNECTED = "connector.connected"
    CONNECTOR_DISCONNECTED = "connector.disconnected"
    CONNECTOR_ERROR = "connector.error"

    # Schema
    SCHEMA_DISCOVERED = "schema.discovered"
    SCHEMA_CHANGED = "schema.changed"

    # Pipeline
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_STEP_COMPLETED = "pipeline.step_completed"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"

    # Data
    RECORD_CREATED = "record.created"
    RECORD_UPDATED = "record.updated"
    RECORD_DELETED = "record.deleted"


@dataclass(frozen=True)
class Event:
    """An immutable event that flows through the event bus."""

    type: EventType
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


# Handlers can be sync or async callables.
EventHandler = Callable[[Event], None] | Callable[[Event], Awaitable[None]]


class EventBus:
    """Simple in-process pub/sub event bus with async support."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event, invoking all registered handlers."""
        for handler in self._handlers.get(event.type, []):
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Event handler failed for %s", event.type)

    def publish_sync(self, event: Event) -> None:
        """Synchronous convenience — runs handlers that are sync, skips async ones."""
        for handler in self._handlers.get(event.type, []):
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    result.close()  # prevent RuntimeWarning
                    logger.warning(
                        "Async handler skipped in publish_sync for %s", event.type
                    )
            except Exception:
                logger.exception("Event handler failed for %s", event.type)
