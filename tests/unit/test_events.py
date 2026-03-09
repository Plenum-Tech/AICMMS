"""Tests for the event bus."""

import pytest
from cafm.core.events import Event, EventBus, EventType


@pytest.mark.asyncio
async def test_publish_subscribe():
    bus = EventBus()
    received = []

    def handler(event: Event):
        received.append(event)

    bus.subscribe(EventType.CONNECTOR_CONNECTED, handler)
    event = Event(type=EventType.CONNECTOR_CONNECTED, source="test")
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].source == "test"


@pytest.mark.asyncio
async def test_async_handler():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe(EventType.SCHEMA_DISCOVERED, handler)
    await bus.publish(Event(type=EventType.SCHEMA_DISCOVERED, source="db"))

    assert len(received) == 1


def test_publish_sync():
    bus = EventBus()
    received = []

    def handler(event: Event):
        received.append(event)

    bus.subscribe(EventType.PIPELINE_COMPLETED, handler)
    bus.publish_sync(Event(type=EventType.PIPELINE_COMPLETED, source="pipe"))

    assert len(received) == 1


def test_unsubscribe():
    bus = EventBus()
    received = []

    def handler(event: Event):
        received.append(event)

    bus.subscribe(EventType.CONNECTOR_CONNECTED, handler)
    bus.unsubscribe(EventType.CONNECTOR_CONNECTED, handler)
    bus.publish_sync(Event(type=EventType.CONNECTOR_CONNECTED, source="x"))

    assert len(received) == 0
