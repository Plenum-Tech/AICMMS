"""Base model with audit fields and soft-delete support."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CAFMBaseModel(BaseModel):
    """Base model for all CAFM domain entities.

    Provides:
      - Audit fields (created_at, updated_at, created_by, updated_by)
      - Soft-delete support (is_deleted, deleted_at)
      - Custom attributes dict for extensibility
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    is_deleted: bool = False
    deleted_at: datetime | None = None

    def soft_delete(self, deleted_by: str | None = None) -> None:
        """Mark this entity as deleted without removing it."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if deleted_by:
            self.updated_by = deleted_by
