"""Common API response schemas used across all endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = True
    data: T | None = None
    message: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with metadata."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[T]:
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str
    detail: str | None = None
    error_code: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    uptime_seconds: float = 0.0
    active_connectors: int = 0
    components: dict[str, str] = Field(default_factory=dict)


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""

    total_requested: int
    succeeded: int
    failed: int
    errors: list[dict[str, Any]] = Field(default_factory=list)
