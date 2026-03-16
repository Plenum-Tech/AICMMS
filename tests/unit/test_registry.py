"""Tests for connector registry."""

import pytest

from cafm.connectors.base import Connector, ConnectorConfig, SchemaInspector
from cafm.connectors.registry import ConnectorRegistry
from cafm.core.exceptions import ConnectorAlreadyRegisteredError, ConnectorNotFoundError
from cafm.core.types import DataSourceType, RawRow


class DummyInspector(SchemaInspector):
    async def list_tables(self): return []
    async def discover_table(self, name): ...
    async def discover_schema(self): ...


class DummyConnector(Connector):
    source_type = DataSourceType.CSV

    async def connect(self): ...
    async def disconnect(self): ...
    async def health_check(self): return True
    def get_schema_inspector(self): return DummyInspector()
    async def fetch_rows(self, table, **kw): return []
    async def count_rows(self, table, **kw): return 0


def test_register_and_get():
    reg = ConnectorRegistry()
    reg.register(DummyConnector)
    assert reg.is_registered(DataSourceType.CSV)
    assert reg.get(DataSourceType.CSV) is DummyConnector


def test_register_duplicate_raises():
    reg = ConnectorRegistry()
    reg.register(DummyConnector)
    with pytest.raises(ConnectorAlreadyRegisteredError):
        reg.register(DummyConnector)


def test_get_missing_raises():
    reg = ConnectorRegistry()
    with pytest.raises(ConnectorNotFoundError):
        reg.get(DataSourceType.MSSQL)


def test_create_instance():
    reg = ConnectorRegistry()
    reg.register(DummyConnector)
    config = ConnectorConfig(
        name="test",
        source_type=DataSourceType.CSV,
        connection_params={},
    )
    conn = reg.create(config)
    assert isinstance(conn, DummyConnector)
    assert conn.name == "test"


def test_list_registered():
    reg = ConnectorRegistry()
    reg.register(DummyConnector)
    types = reg.list_registered()
    assert DataSourceType.CSV in types
