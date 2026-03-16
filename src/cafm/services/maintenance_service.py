"""Service layer for preventive maintenance (Story 3)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.enums import MaintenanceFrequency, WorkOrderType
from cafm.domain.maintenance import FailureMode, MaintenanceLog, MaintenanceSchedule
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)

FREQUENCY_DAYS: dict[MaintenanceFrequency, int] = {
    MaintenanceFrequency.DAILY: 1,
    MaintenanceFrequency.WEEKLY: 7,
    MaintenanceFrequency.BIWEEKLY: 14,
    MaintenanceFrequency.MONTHLY: 30,
    MaintenanceFrequency.QUARTERLY: 90,
    MaintenanceFrequency.SEMI_ANNUAL: 180,
    MaintenanceFrequency.ANNUAL: 365,
}


class MaintenanceService:
    """Business logic for preventive/predictive maintenance.

    Story 3: Receive PPM insights, auto-create work orders, intelligent routing.
    """

    def __init__(
        self,
        schedule_repo: Repository[MaintenanceSchedule],
        log_repo: Repository[MaintenanceLog],
        failure_mode_repo: Repository[FailureMode],
        event_bus: EventBus,
    ) -> None:
        self._schedule_repo = schedule_repo
        self._log_repo = log_repo
        self._failure_repo = failure_mode_repo
        self._event_bus = event_bus

    # ── Schedules ──────────────────────────────────────────────

    async def create_schedule(
        self, data: dict[str, Any], created_by: str | None = None,
    ) -> MaintenanceSchedule:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        if not data.get("next_due"):
            freq = data.get("frequency", MaintenanceFrequency.MONTHLY)
            days = data.get("custom_interval_days") or FREQUENCY_DAYS.get(freq, 30)
            data["next_due"] = datetime.utcnow() + timedelta(days=days)
        schedule = MaintenanceSchedule(**data)
        created = await self._schedule_repo.create(schedule)
        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="maintenance_service",
            payload={"entity": "schedule", "schedule_id": created.schedule_id},
        ))
        return created

    async def get_schedule(self, schedule_id: str) -> MaintenanceSchedule | None:
        return await self._schedule_repo.get_by_id(schedule_id)

    async def list_schedules(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[MaintenanceSchedule], int]:
        result = await self._schedule_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._schedule_repo.count(filters=filters)
        schedules = [MaintenanceSchedule(**r.data) for r in result.records]
        return schedules, total

    async def update_schedule(
        self, schedule_id: str, updates: dict[str, Any],
    ) -> MaintenanceSchedule | None:
        updates["updated_at"] = datetime.utcnow()
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._schedule_repo.update(schedule_id, updates)

    async def get_upcoming_ppm(self, days_ahead: int = 30) -> list[MaintenanceSchedule]:
        """Get PPM schedules due within the next N days."""
        schedules, _ = await self.list_schedules(
            filters={"is_active": True}, limit=500,
        )
        cutoff = datetime.utcnow() + timedelta(days=days_ahead)
        return [s for s in schedules if s.next_due and s.next_due <= cutoff]

    async def get_overdue_ppm(self) -> list[MaintenanceSchedule]:
        """Get PPM schedules that are past due."""
        schedules, _ = await self.list_schedules(
            filters={"is_active": True}, limit=500,
        )
        now = datetime.utcnow()
        return [s for s in schedules if s.next_due and s.next_due < now]

    async def generate_ppm_insights(self, asset_id: str) -> dict[str, Any]:
        """Generate PPM insights for an asset based on historical data.

        In production, this calls the AI predictive maintenance engine.
        Returns risk score and recommended actions.
        """
        # Get maintenance history
        logs, log_count = await self.list_maintenance_logs(
            filters={"asset_id": asset_id}, limit=100,
        )
        schedules, _ = await self.list_schedules(filters={"asset_id": asset_id})

        # Basic risk scoring (placeholder for AI engine)
        risk_score = 0.3  # default low risk
        if log_count == 0:
            risk_score = 0.7  # no history = higher risk
        overdue = [s for s in schedules if s.next_due and s.next_due < datetime.utcnow()]
        if overdue:
            risk_score = min(1.0, risk_score + 0.3)

        return {
            "asset_id": asset_id,
            "risk_score": round(risk_score, 2),
            "maintenance_history_count": log_count,
            "active_schedules": len(schedules),
            "overdue_schedules": len(overdue),
            "recommended_action": "schedule_ppm" if risk_score > 0.5 else "monitor",
            "confidence": 0.75,
            "factors": [
                f"{'No' if log_count == 0 else log_count} maintenance records",
                f"{len(overdue)} overdue schedule(s)",
            ],
        }

    # ── Maintenance Logs ───────────────────────────────────────

    async def create_maintenance_log(self, data: dict[str, Any]) -> MaintenanceLog:
        data["created_at"] = datetime.utcnow()
        log = MaintenanceLog(**data)
        return await self._log_repo.create(log)

    async def list_maintenance_logs(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[MaintenanceLog], int]:
        result = await self._log_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._log_repo.count(filters=filters)
        logs = [MaintenanceLog(**r.data) for r in result.records]
        return logs, total

    # ── Failure Modes ──────────────────────────────────────────

    async def list_failure_modes(
        self, asset_category: str | None = None,
    ) -> tuple[list[FailureMode], int]:
        filters = {"asset_category": asset_category} if asset_category else None
        result = await self._failure_repo.get_all(filters=filters)
        total = await self._failure_repo.count(filters=filters)
        modes = [FailureMode(**r.data) for r in result.records]
        return modes, total
