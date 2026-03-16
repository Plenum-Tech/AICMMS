"""Unit of Work — transactional boundary across multiple repositories."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

from cafm.connectors.base import Connector
from cafm.core.exceptions import DataError

logger = structlog.get_logger(__name__)


# ── Change tracking ──────────────────────────────────────────────


class ChangeType(StrEnum):
    """Kind of mutation tracked by the Unit of Work."""

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class TrackedChange:
    """A single pending change waiting to be committed."""

    change_type: ChangeType
    table: str
    data: dict[str, Any]
    filters: dict[str, Any] | None = None


# ── Unit of Work ─────────────────────────────────────────────────


class UnitOfWork:
    """Group multiple repository operations into a transactional unit.

    Usage::

        async with UnitOfWork(connector) as uow:
            uow.register_insert("assets", {"asset_id": "A-1", ...})
            uow.register_update("work_orders", {"status": "closed"},
                                filters={"wo_id": "WO-42"})
            # all changes are flushed on successful exit of the context

    If an exception occurs inside the context block, all pending changes
    are discarded and (where the connector supports it) a rollback is
    issued.

    The class deliberately keeps its scope narrow: it tracks changes as
    simple dicts rather than domain models, because it sits below the
    Repository layer and operates at the connector level.
    """

    def __init__(self, connector: Connector) -> None:
        self._connector = connector
        self._changes: list[TrackedChange] = []
        self._committed = False

    # ── Context manager ───────────────────────────────────────────

    async def __aenter__(self) -> UnitOfWork:
        self._changes.clear()
        self._committed = False
        logger.debug("uow_started", connector=self._connector.name)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
            logger.warning(
                "uow_rolled_back",
                connector=self._connector.name,
                error=str(exc_val),
                pending_changes=len(self._changes),
            )
            return  # propagate the exception

        if not self._committed:
            await self.commit()

    # ── Change registration ───────────────────────────────────────

    def register_insert(self, table: str, data: dict[str, Any]) -> None:
        """Stage an insert operation."""
        self._changes.append(
            TrackedChange(change_type=ChangeType.INSERT, table=table, data=data)
        )

    def register_update(
        self,
        table: str,
        data: dict[str, Any],
        *,
        filters: dict[str, Any],
    ) -> None:
        """Stage an update operation."""
        self._changes.append(
            TrackedChange(
                change_type=ChangeType.UPDATE,
                table=table,
                data=data,
                filters=filters,
            )
        )

    def register_delete(
        self,
        table: str,
        *,
        filters: dict[str, Any],
    ) -> None:
        """Stage a delete operation."""
        self._changes.append(
            TrackedChange(
                change_type=ChangeType.DELETE,
                table=table,
                data={},
                filters=filters,
            )
        )

    # ── Commit / Rollback ─────────────────────────────────────────

    async def commit(self) -> None:
        """Flush all pending changes to the connector.

        Changes are applied in registration order.  If any individual
        operation fails the remaining changes are **not** applied and a
        :class:`~cafm.core.exceptions.DataError` is raised (the caller
        should handle cleanup or rely on the database's own transaction
        semantics if the connector wraps one).
        """
        if self._committed:
            return

        # Group inserts by table to allow batch insertion.
        inserts_by_table: dict[str, list[dict[str, Any]]] = {}
        ordered_ops: list[TrackedChange] = []

        for change in self._changes:
            if change.change_type is ChangeType.INSERT:
                inserts_by_table.setdefault(change.table, []).append(change.data)
            else:
                # Flush any queued inserts for tables that appeared
                # before this non-insert operation to preserve order.
                if inserts_by_table:
                    for table, rows in inserts_by_table.items():
                        ordered_ops.append(
                            TrackedChange(
                                change_type=ChangeType.INSERT,
                                table=table,
                                data={"__batch__": rows},
                            )
                        )
                    inserts_by_table.clear()
                ordered_ops.append(change)

        # Flush remaining inserts.
        for table, rows in inserts_by_table.items():
            ordered_ops.append(
                TrackedChange(
                    change_type=ChangeType.INSERT,
                    table=table,
                    data={"__batch__": rows},
                )
            )

        applied = 0
        try:
            for op in ordered_ops:
                if op.change_type is ChangeType.INSERT:
                    batch = op.data.get("__batch__")
                    if batch:
                        await self._connector.insert_rows(op.table, batch)
                    else:
                        await self._connector.insert_rows(op.table, [op.data])
                elif op.change_type is ChangeType.UPDATE:
                    assert op.filters is not None
                    await self._connector.update_rows(
                        op.table, filters=op.filters, updates=op.data
                    )
                elif op.change_type is ChangeType.DELETE:
                    assert op.filters is not None
                    await self._connector.delete_rows(op.table, filters=op.filters)
                applied += 1
        except Exception as exc:
            raise DataError(
                f"UnitOfWork commit failed after {applied}/{len(ordered_ops)} "
                f"operations on connector {self._connector.name!r}: {exc}"
            ) from exc

        self._committed = True
        logger.info(
            "uow_committed",
            connector=self._connector.name,
            operations=applied,
        )
        self._changes.clear()

    async def rollback(self) -> None:
        """Discard all pending changes.

        If the underlying connector exposes a ``rollback`` method (e.g.
        a SQL connector with an open transaction) it is called;
        otherwise the in-memory change list is simply cleared.
        """
        self._changes.clear()
        self._committed = False

        rollback_fn = getattr(self._connector, "rollback", None)
        if callable(rollback_fn):
            try:
                await rollback_fn()
            except Exception:
                logger.warning(
                    "uow_rollback_connector_error",
                    connector=self._connector.name,
                    exc_info=True,
                )

        logger.debug("uow_rolled_back", connector=self._connector.name)

    # ── Introspection ─────────────────────────────────────────────

    @property
    def pending_changes(self) -> list[TrackedChange]:
        """Return a snapshot of the uncommitted changes."""
        return list(self._changes)

    @property
    def is_committed(self) -> bool:
        return self._committed

    @property
    def has_pending_changes(self) -> bool:
        return bool(self._changes)
