"""Connector factory — creates connector instances from configuration dicts."""

from __future__ import annotations

from typing import Any

from cafm.connectors.base import Connector, ConnectorConfig
from cafm.connectors.registry import ConnectorRegistry
from cafm.core.types import DataSourceType


def create_connector(
    name: str,
    source_type: str | DataSourceType,
    connection_params: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> Connector:
    """Create a connector instance from plain parameters.

    This is the recommended way for external code to instantiate connectors.

    Args:
        name: Human-readable name for this data source.
        source_type: One of the DataSourceType values (string or enum).
        connection_params: Source-specific connection parameters.
        options: Optional tuning parameters.

    Returns:
        An un-connected Connector instance. Call ``connect()`` or use
        ``session()`` to establish the connection.
    """
    config = ConnectorConfig(
        name=name,
        source_type=DataSourceType(source_type),
        connection_params=connection_params,
        options=options or {},
    )
    registry = ConnectorRegistry()
    return registry.create(config)
