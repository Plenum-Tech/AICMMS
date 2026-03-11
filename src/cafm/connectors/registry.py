"""Plugin registry with auto-discovery via entry_points.

Third-party connectors register themselves by adding an entry point
in the ``cafm.connectors`` group of their ``pyproject.toml``.
"""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import ClassVar

from cafm.connectors.base import Connector, ConnectorConfig
from cafm.core.exceptions import ConnectorAlreadyRegisteredError, ConnectorNotFoundError
from cafm.core.types import DataSourceType

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Singleton registry that maps DataSourceType -> Connector class.

    Discovery order:
      1. Explicit registration via ``register()``.
      2. Auto-discovery via ``cafm.connectors`` entry_points group.
    """

    _instance: ClassVar[ConnectorRegistry | None] = None
    _plugins: dict[DataSourceType, type[Connector]]

    def __new__(cls) -> ConnectorRegistry:
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._plugins = {}
            cls._instance = inst
        return cls._instance

    # ── Registration ──────────────────────────────────────────────

    def register(
        self, connector_cls: type[Connector], *, allow_override: bool = False
    ) -> None:
        """Register a connector class for its ``source_type``."""
        source_type = connector_cls.source_type
        if source_type in self._plugins and not allow_override:
            raise ConnectorAlreadyRegisteredError(
                f"Connector for {source_type} is already registered"
            )
        self._plugins[source_type] = connector_cls
        logger.info("Registered connector: %s -> %s", source_type, connector_cls.__name__)

    def discover_plugins(self) -> None:
        """Auto-discover connector plugins via setuptools entry_points."""
        eps = entry_points(group="cafm.connectors")
        for ep in eps:
            try:
                connector_cls = ep.load()
                if isinstance(connector_cls, type) and issubclass(connector_cls, Connector):
                    self.register(connector_cls, allow_override=True)
                else:
                    logger.warning("Entry point %s did not resolve to a Connector subclass", ep.name)
            except Exception:
                logger.exception("Failed to load connector plugin: %s", ep.name)

    # ── Lookup ────────────────────────────────────────────────────

    def get(self, source_type: DataSourceType) -> type[Connector]:
        """Get the connector class for a source type. Raises if not found."""
        try:
            return self._plugins[source_type]
        except KeyError:
            raise ConnectorNotFoundError(
                f"No connector registered for {source_type}. "
                f"Available: {list(self._plugins.keys())}"
            )

    def create(self, config: ConnectorConfig) -> Connector:
        """Factory: instantiate a connector from a config dict."""
        cls = self.get(config.source_type)
        return cls(config)

    def list_registered(self) -> list[DataSourceType]:
        """List all registered source types."""
        return list(self._plugins.keys())

    def is_registered(self, source_type: DataSourceType) -> bool:
        return source_type in self._plugins

    # ── Testing ───────────────────────────────────────────────────

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing only)."""
        cls._instance = None
