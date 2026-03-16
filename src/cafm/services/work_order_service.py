"""Service layer for work order management."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.enums import WorkOrderPriority, WorkOrderStatus, WorkOrderType
from cafm.domain.work_orders import WorkOrder
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class WorkOrderService:
    """Business logic for work order management.

    Handles CRUD, status transitions, ad-hoc creation from text/voice,
    and intelligent routing to technicians.
    """

    def __init__(
        self,
        repository: Repository[WorkOrder],
        event_bus: EventBus,
    ) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def create_work_order(
        self, data: dict[str, Any], created_by: str | None = None
    ) -> WorkOrder:
        """Create a new work order."""
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        data["requested_date"] = data.get("requested_date") or datetime.utcnow()
        data.setdefault("status", WorkOrderStatus.SUBMITTED)

        wo = WorkOrder(**data)
        created = await self._repo.create(wo)

        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED,
            source="work_order_service",
            payload={"entity": "work_order", "work_order_id": created.work_order_id},
        ))

        logger.info("Work order created: %s", created.work_order_id)
        return created

    async def create_adhoc_work_order(
        self,
        text: str,
        building_id: str | None = None,
        asset_id: str | None = None,
        priority: WorkOrderPriority = WorkOrderPriority.MEDIUM,
        requested_by: str | None = None,
    ) -> WorkOrder:
        """Create an ad-hoc work order from text/voice input.

        Per AICMMS spec: users can create work orders via text or voice notes
        through the query interface on mobile.
        """
        wo_id = f"WO-{uuid.uuid4().hex[:8].upper()}"
        # In a full implementation, AI would parse the text to extract:
        # - title, description, asset identification, priority
        title = text[:100] if len(text) > 100 else text
        data = {
            "work_order_id": wo_id,
            "title": title,
            "description": text,
            "work_order_type": WorkOrderType.CORRECTIVE,
            "priority": priority,
            "building_id": building_id,
            "asset_id": asset_id,
            "requested_by": requested_by,
            "custom_attributes": {"source": "adhoc", "original_text": text},
        }
        return await self.create_work_order(data, created_by=requested_by)

    async def get_work_order(self, work_order_id: str) -> WorkOrder | None:
        """Get a work order by ID."""
        return await self._repo.get_by_id(work_order_id)

    async def list_work_orders(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str | None = None,
    ) -> tuple[list[WorkOrder], int]:
        """List work orders with filtering and pagination."""
        result_set = await self._repo.get_all(
            filters=filters, limit=limit, offset=offset, order_by=order_by,
        )
        total = await self._repo.count(filters=filters)
        work_orders = []
        for record in result_set.records:
            if isinstance(record, WorkOrder):
                work_orders.append(record)
            else:
                work_orders.append(WorkOrder(**record.data if hasattr(record, "data") else {}))
        return work_orders, total

    async def update_work_order(
        self, work_order_id: str, updates: dict[str, Any], updated_by: str | None = None
    ) -> WorkOrder | None:
        """Update a work order."""
        updates["updated_at"] = datetime.utcnow()
        if updated_by:
            updates["updated_by"] = updated_by
        updates = {k: v for k, v in updates.items() if v is not None}

        updated = await self._repo.update(work_order_id, updates)
        if updated:
            await self._event_bus.publish(Event(
                type=EventType.RECORD_UPDATED,
                source="work_order_service",
                payload={"entity": "work_order", "work_order_id": work_order_id},
            ))
        return updated

    async def transition_status(
        self, work_order_id: str, new_status: WorkOrderStatus, by: str | None = None
    ) -> WorkOrder | None:
        """Transition a work order to a new status with validation."""
        wo = await self._repo.get_by_id(work_order_id)
        if wo is None:
            return None

        # Basic status transition validation
        valid_transitions: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
            WorkOrderStatus.DRAFT: {WorkOrderStatus.SUBMITTED, WorkOrderStatus.CANCELLED},
            WorkOrderStatus.SUBMITTED: {
                WorkOrderStatus.APPROVED, WorkOrderStatus.CANCELLED,
            },
            WorkOrderStatus.APPROVED: {
                WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.ON_HOLD,
                WorkOrderStatus.CANCELLED,
            },
            WorkOrderStatus.IN_PROGRESS: {
                WorkOrderStatus.ON_HOLD, WorkOrderStatus.COMPLETED,
                WorkOrderStatus.CANCELLED,
            },
            WorkOrderStatus.ON_HOLD: {
                WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED,
            },
            WorkOrderStatus.COMPLETED: {WorkOrderStatus.CLOSED},
            WorkOrderStatus.CANCELLED: set(),
            WorkOrderStatus.CLOSED: set(),
        }

        allowed = valid_transitions.get(wo.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {wo.status} to {new_status}. "
                f"Allowed: {', '.join(sorted(allowed)) or 'none'}"
            )

        updates: dict[str, Any] = {"status": new_status}
        if new_status == WorkOrderStatus.IN_PROGRESS and wo.actual_start is None:
            updates["actual_start"] = datetime.utcnow()
        if new_status == WorkOrderStatus.COMPLETED:
            updates["actual_end"] = datetime.utcnow()

        return await self.update_work_order(work_order_id, updates, updated_by=by)

    async def assign_work_order(
        self, work_order_id: str, technician_id: str, by: str | None = None
    ) -> WorkOrder | None:
        """Assign a work order to a technician."""
        return await self.update_work_order(
            work_order_id, {"assigned_to": technician_id}, updated_by=by,
        )

    async def get_overdue_work_orders(self) -> tuple[list[WorkOrder], int]:
        """Get work orders past their due date."""
        # In production, this would use a date-based query
        return await self.list_work_orders(
            filters={"status": WorkOrderStatus.IN_PROGRESS}
        )

    async def get_work_order_count(self, filters: dict[str, Any] | None = None) -> int:
        """Count work orders matching filters."""
        return await self._repo.count(filters=filters)
