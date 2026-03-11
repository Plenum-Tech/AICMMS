"""UnifiedResultSet — paginated query results."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from cafm.models.record import UnifiedRecord


class UnifiedResultSet(BaseModel):
    """Paginated result from any data source query."""

    records: list[UnifiedRecord]
    total_count: int | None = None
    offset: int = 0
    limit: int | None = None
    has_more: bool = False

    def as_dicts(self) -> list[dict[str, Any]]:
        """Extract raw data dicts from all records."""
        return [r.data for r in self.records]

    def as_dataframe(self) -> Any:
        """Convert to a pandas DataFrame. Requires pandas installed."""
        import pandas as pd

        return pd.DataFrame(self.as_dicts())

    def as_domain_models(self, model_cls: type[BaseModel]) -> list[BaseModel]:
        """Convert all records to typed domain models."""
        return [r.to_domain_model(model_cls) for r in self.records]

    @property
    def count(self) -> int:
        """Number of records in this page."""
        return len(self.records)

    @property
    def is_empty(self) -> bool:
        return len(self.records) == 0
