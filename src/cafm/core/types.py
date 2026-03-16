"""Shared type aliases and enumerations used across the platform."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class DataSourceType(StrEnum):
    """Supported data source types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"
    MONGODB = "mongodb"
    CSV = "csv"
    EXCEL = "excel"


class UnifiedDataType(StrEnum):
    """Source-agnostic type system.

    Every native column type from any connector is mapped to one of these.
    """

    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    BINARY = "binary"
    JSON = "json"
    ARRAY = "array"
    UUID = "uuid"
    UNKNOWN = "unknown"


class ConnectorState(StrEnum):
    """Lifecycle state of a connector instance."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


# Type alias for raw data from any source — a single row as a dict.
RawRow = dict[str, Any]
