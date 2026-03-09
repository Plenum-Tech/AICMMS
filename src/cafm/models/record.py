"""UnifiedRecord — source-agnostic data row wrapper."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from cafm.core.types import DataSourceType


class RecordMetadata(BaseModel):
    """Provenance metadata attached to every unified record."""

    source_name: str
    source_type: DataSourceType
    table_name: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    raw_types: dict[str, str] = Field(default_factory=dict)


class UnifiedRecord(BaseModel):
    """Source-agnostic data record.

    Every row from every source is wrapped in this envelope, preserving
    provenance while presenting a uniform interface.
    """

    data: dict[str, Any]
    metadata: RecordMetadata

    def get(self, field: str, default: Any = None) -> Any:
        """Get a field value with an optional default."""
        return self.data.get(field, default)

    def __getitem__(self, field: str) -> Any:
        return self.data[field]

    def __contains__(self, field: str) -> bool:
        return field in self.data

    def to_domain_model(self, model_cls: type[BaseModel]) -> BaseModel:
        """Convert to a typed Pydantic domain model."""
        return model_cls.model_validate(self.data)

    @property
    def field_names(self) -> list[str]:
        return list(self.data.keys())
