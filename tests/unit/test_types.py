"""Tests for core types and enums."""

from cafm.core.types import DataSourceType, UnifiedDataType, ConnectorState


def test_data_source_types():
    assert DataSourceType.POSTGRESQL == "postgresql"
    assert DataSourceType.MYSQL == "mysql"
    assert DataSourceType.MSSQL == "mssql"
    assert DataSourceType.MONGODB == "mongodb"
    assert DataSourceType.CSV == "csv"
    assert DataSourceType.EXCEL == "excel"
    assert len(DataSourceType) == 6


def test_unified_data_types():
    assert UnifiedDataType.STRING == "string"
    assert UnifiedDataType.INTEGER == "integer"
    assert UnifiedDataType.UNKNOWN == "unknown"
    assert len(UnifiedDataType) >= 13


def test_connector_states():
    assert ConnectorState.DISCONNECTED == "disconnected"
    assert ConnectorState.CONNECTED == "connected"
