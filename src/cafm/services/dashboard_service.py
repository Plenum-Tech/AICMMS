"""Service layer for the Command Center dashboard."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from cafm.core.events import EventBus
from cafm.domain.enums import (
    AssetCondition,
    AssetCriticality,
    AssetStatus,
    WorkOrderPriority,
    WorkOrderStatus,
)
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class DashboardService:
    """Business logic for the Command Center dashboard.

    Aggregates metrics from multiple repositories to provide a single-view
    dashboard as specified by AICMMS Command Center requirements.
    """

    def __init__(
        self,
        asset_repo: Repository | None = None,
        work_order_repo: Repository | None = None,
        technician_repo: Repository | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._asset_repo = asset_repo
        self._wo_repo = work_order_repo
        self._tech_repo = technician_repo
        self._event_bus = event_bus

    async def get_summary(self) -> dict[str, Any]:
        """Build the dashboard summary with all KPIs.

        Returns a dictionary matching the DashboardSummary schema.
        """
        summary: dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Asset metrics
        if self._asset_repo:
            summary["total_assets"] = await self._asset_repo.count()
            summary["active_assets"] = await self._asset_repo.count(
                filters={"status": AssetStatus.ACTIVE}
            )
            summary["critical_assets"] = await self._asset_repo.count(
                filters={"criticality": AssetCriticality.CRITICAL}
            )
            summary["assets_under_maintenance"] = await self._asset_repo.count(
                filters={"status": AssetStatus.UNDER_MAINTENANCE}
            )
        else:
            summary.update({
                "total_assets": 0, "active_assets": 0,
                "critical_assets": 0, "assets_under_maintenance": 0,
            })

        # Work order metrics
        if self._wo_repo:
            open_statuses = [
                WorkOrderStatus.SUBMITTED, WorkOrderStatus.APPROVED,
                WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.ON_HOLD,
            ]
            open_count = 0
            for s in open_statuses:
                open_count += await self._wo_repo.count(filters={"status": s})
            summary["open_work_orders"] = open_count
            summary["completed_this_month"] = await self._wo_repo.count(
                filters={"status": WorkOrderStatus.COMPLETED}
            )
        else:
            summary.update({
                "open_work_orders": 0, "overdue_work_orders": 0,
                "completed_this_month": 0,
            })

        # Technician metrics
        if self._tech_repo:
            summary["total_technicians"] = await self._tech_repo.count()
            summary["available_technicians"] = await self._tech_repo.count(
                filters={"is_available": True}
            )
        else:
            summary.update({"total_technicians": 0, "available_technicians": 0})

        return summary

    async def get_asset_breakdown(self) -> dict[str, Any]:
        """Get asset breakdown by status and condition."""
        if not self._asset_repo:
            return {"by_status": {}, "by_condition": {}, "by_criticality": {}}

        by_status = {}
        for s in AssetStatus:
            by_status[s.value] = await self._asset_repo.count(filters={"status": s})

        by_condition = {}
        for c in AssetCondition:
            by_condition[c.value] = await self._asset_repo.count(filters={"condition": c})

        by_criticality = {}
        for cr in AssetCriticality:
            by_criticality[cr.value] = await self._asset_repo.count(filters={"criticality": cr})

        return {
            "by_status": by_status,
            "by_condition": by_condition,
            "by_criticality": by_criticality,
        }

    async def get_work_order_breakdown(self) -> dict[str, Any]:
        """Get work order breakdown by status and priority."""
        if not self._wo_repo:
            return {"by_status": {}, "by_priority": {}}

        by_status = {}
        for s in WorkOrderStatus:
            by_status[s.value] = await self._wo_repo.count(filters={"status": s})

        by_priority = {}
        for p in WorkOrderPriority:
            by_priority[p.value] = await self._wo_repo.count(filters={"priority": p})

        return {"by_status": by_status, "by_priority": by_priority}

    async def get_alerts(self) -> list[dict[str, Any]]:
        """Generate alerts based on current system state.

        In production, this would check SLA breaches, overdue work orders,
        critical asset conditions, sensor thresholds, etc.
        """
        alerts: list[dict[str, Any]] = []

        # Check for critical assets
        if self._asset_repo:
            critical_count = await self._asset_repo.count(
                filters={"condition": AssetCondition.CRITICAL}
            )
            if critical_count > 0:
                alerts.append({
                    "alert_id": "alert-critical-assets",
                    "severity": "critical",
                    "category": "asset",
                    "title": "Critical Asset Condition",
                    "message": f"{critical_count} asset(s) in critical condition",
                    "created_at": datetime.utcnow().isoformat(),
                    "acknowledged": False,
                })

        # Check for high-priority unassigned work orders
        if self._wo_repo:
            # This is a simplified check
            emergency_count = await self._wo_repo.count(
                filters={"priority": WorkOrderPriority.EMERGENCY}
            )
            if emergency_count > 0:
                alerts.append({
                    "alert_id": "alert-emergency-wo",
                    "severity": "critical",
                    "category": "work_order",
                    "title": "Emergency Work Orders",
                    "message": f"{emergency_count} emergency work order(s) active",
                    "created_at": datetime.utcnow().isoformat(),
                    "acknowledged": False,
                })

        return alerts
