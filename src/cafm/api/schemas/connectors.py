"""Request/response schemas for the data connectors API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cafm.core.types import ConnectorState, DataSourceType


class ConnectorCreateRequest(BaseModel):
    """Request to register a new data source connector."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique source name")
    source_type: DataSourceType = Field(..., description="Type of data source")
    connection_params: dict[str, Any] = Field(
        ..., description="Connection parameters (e.g., url, host, port, database)"
    )
    description: str | None = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list)


class ConnectorUpdateRequest(BaseModel):
    """Request to update connector configuration."""

    connection_params: dict[str, Any] | None = None
    description: str | None = None
    tags: list[str] | None = None


class ConnectorResponse(BaseModel):
    """Connector information returned by the API."""

    name: str
    source_type: DataSourceType
    state: ConnectorState
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    tables_count: int | None = None


class ConnectorTestResult(BaseModel):
    """Result of a connection test."""

    name: str
    healthy: bool
    latency_ms: float | None = None
    error: str | None = None


class SchemaResponse(BaseModel):
    """Schema information for a data source."""

    source_name: str
    source_type: str
    tables_count: int
    tables: list[TableSummary]


class TableSummary(BaseModel):
    """Summary of a table's schema."""

    name: str
    columns_count: int
    row_count: int | None = None
    columns: list[ColumnSummary]


class ColumnSummary(BaseModel):
    """Summary of a column."""

    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False


# Fix forward reference
SchemaResponse.model_rebuild()


class QueryRequest(BaseModel):
    """Request to query a data source."""

    source_name: str
    table: str
    columns: list[str] | None = None
    filters: dict[str, Any] | None = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class QueryResponse(BaseModel):
    """Response from a data source query."""

    source_name: str
    table: str
    rows: list[dict[str, Any]]
    total_count: int
    offset: int
    limit: int
    has_more: bool
