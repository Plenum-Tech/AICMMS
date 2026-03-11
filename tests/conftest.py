"""Shared test fixtures."""

from __future__ import annotations

import pytest

from cafm.connectors.registry import ConnectorRegistry
from cafm.core.config import AppConfig
from cafm.core.events import EventBus


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig()


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure each test gets a fresh ConnectorRegistry."""
    yield
    ConnectorRegistry.reset()
