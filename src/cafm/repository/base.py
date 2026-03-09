"""Abstract Repository — generic, source-agnostic data-access interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from cafm.models.base import CAFMBaseModel
from cafm.models.resultset import UnifiedResultSet

T = TypeVar("T", bound=CAFMBaseModel)


class Repository(ABC, Generic[T]):
    """Abstract repository defining CRUD + bulk operations for any entity.

    Type parameter *T* is a domain model that inherits from
    :class:`~cafm.models.base.CAFMBaseModel`.  Concrete subclasses
    (``SQLRepository``, ``MongoRepository``, ``FileRepository``) wire
    this interface to a specific :class:`~cafm.connectors.base.Connector`.
    """

    # ── Single-entity CRUD ────────────────────────────────────────

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> T | None:
        """Retrieve a single entity by its primary identifier.

        Returns ``None`` when no matching entity exists.
        """
        ...

    @abstractmethod
    async def get_all(
        self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
        order_by: str | None = None,
    ) -> UnifiedResultSet:
        """Retrieve a paginated, optionally filtered set of entities.

        Parameters
        ----------
        filters:
            Key/value pairs interpreted as equality predicates
            (e.g. ``{"status": "active"}``).
        limit:
            Maximum number of records to return.
        offset:
            Number of records to skip (for pagination).
        order_by:
            Field name optionally prefixed with ``-`` for descending order.
        """
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Persist a new entity and return it (potentially with generated fields)."""
        ...

    @abstractmethod
    async def update(self, entity_id: str, updates: dict[str, Any]) -> T | None:
        """Apply *updates* to the entity identified by *entity_id*.

        Returns the updated entity, or ``None`` if the entity was not found.
        """
        ...

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete the entity identified by *entity_id*.

        Returns ``True`` if a row was actually removed, ``False`` otherwise.
        """
        ...

    # ── Aggregate helpers ─────────────────────────────────────────

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Return the number of entities matching *filters*."""
        ...

    # ── Bulk operations ───────────────────────────────────────────

    @abstractmethod
    async def bulk_create(self, entities: list[T]) -> list[T]:
        """Persist multiple entities at once.

        Returns the list of created entities (order preserved).
        """
        ...

    @abstractmethod
    async def bulk_update(self, updates: list[tuple[str, dict[str, Any]]]) -> int:
        """Apply updates to multiple entities.

        Each element is a ``(entity_id, updates_dict)`` pair.
        Returns the total number of rows that were actually modified.
        """
        ...
