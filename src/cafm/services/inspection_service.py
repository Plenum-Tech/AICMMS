"""Service layer for inspections with multimodal support (Stories 14, 15, 16)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.gamification import AssetInsight
from cafm.domain.inspections import InspectionReport
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class InspectionService:
    """Business logic for inspection reports, voice/photo input, AI classification.

    Covers:
    - Story 14: Inspection reports with voice notes and site pictures
    - Story 15: Gamified self-entry with pre-filled data and auto-classification
    - Story 16: QR code scan → add technical insights
    """

    def __init__(
        self,
        inspection_repo: Repository[InspectionReport],
        insight_repo: Repository[AssetInsight] | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._inspection_repo = inspection_repo
        self._insight_repo = insight_repo
        self._event_bus = event_bus or EventBus()

    async def create_inspection(
        self, data: dict[str, Any], inspector_id: str | None = None,
    ) -> InspectionReport:
        """Create an inspection report with multimodal inputs.

        Supports voice_note_urls, photo_urls, text_notes.
        Auto-generates prefilled data for 50% config pre-fill (Story 15a).
        """
        data["created_at"] = datetime.utcnow()
        data["inspection_date"] = data.get("inspection_date") or datetime.utcnow()
        data["status"] = data.get("status", "submitted")
        data.setdefault("inspector_id", inspector_id)

        report = InspectionReport(**data)
        created = await self._inspection_repo.create(report)

        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="inspection_service",
            payload={"entity": "inspection", "report_id": created.report_id},
        ))
        logger.info("Inspection report created: %s", created.report_id)
        return created

    async def get_inspection(self, report_id: str) -> InspectionReport | None:
        return await self._inspection_repo.get_by_id(report_id)

    async def list_inspections(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[InspectionReport], int]:
        result = await self._inspection_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._inspection_repo.count(filters=filters)
        reports = [InspectionReport(**r.data) for r in result.records]
        return reports, total

    async def update_inspection(
        self, report_id: str, updates: dict[str, Any],
    ) -> InspectionReport | None:
        updates["updated_at"] = datetime.utcnow()
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._inspection_repo.update(report_id, updates)

    async def classify_inspection(self, report_id: str) -> dict[str, Any]:
        """AI-classify an inspection report and trigger appropriate actions.

        Per AICMMS spec Story 15b: inspection report is entered and
        appropriate action is classified (PPM, future WO, tech insights).
        """
        report = await self._inspection_repo.get_by_id(report_id)
        if report is None:
            return {"error": "Report not found"}

        # AI classification placeholder — in production, this calls the AI engine
        classification = {
            "category": "maintenance_needed",
            "recommended_action": "schedule_ppm",
            "confidence": 0.85,
            "severity": "moderate",
        }

        await self._inspection_repo.update(report_id, {
            "ai_classified_category": classification["category"],
            "ai_recommended_action": classification["recommended_action"],
            "ai_confidence_score": classification["confidence"],
        })

        return {
            "report_id": report_id,
            "classification": classification,
            "action_taken": classification["recommended_action"],
        }

    async def get_prefilled_data(self, asset_id: str, inspector_id: str) -> dict[str, Any]:
        """Get pre-filled data for a new inspection (Story 15a: 50% pre-filled).

        Returns previous inspection data, asset info, and defaults.
        """
        recent_inspections, _ = await self.list_inspections(
            filters={"asset_id": asset_id}, limit=1,
        )
        prefilled: dict[str, Any] = {
            "asset_id": asset_id,
            "inspector_id": inspector_id,
            "inspection_type": "ppm",
        }
        if recent_inspections:
            last = recent_inspections[0]
            prefilled["previous_condition"] = last.overall_condition
            prefilled["previous_inspection_date"] = (
                last.inspection_date.isoformat() if last.inspection_date else None
            )
        return prefilled

    # ── Asset Insights (Story 16) ──────────────────────────────

    async def submit_asset_insight(
        self,
        technician_id: str,
        asset_id: str,
        insight_text: str,
        qr_code: str | None = None,
        voice_note_url: str | None = None,
        photo_urls: list[str] | None = None,
    ) -> AssetInsight | None:
        """Submit a technical insight after scanning an asset QR code (Story 16).

        The platform reads, classifies, and takes appropriate action.
        """
        if self._insight_repo is None:
            logger.warning("Insight repository not configured")
            return None

        insight = AssetInsight(
            insight_id=f"INS-{uuid.uuid4().hex[:8].upper()}",
            technician_id=technician_id,
            asset_id=asset_id,
            insight_text=insight_text,
            scanned_qr_code=qr_code,
            voice_note_url=voice_note_url,
            photo_urls=photo_urls or [],
            timestamp=datetime.utcnow(),
            # AI classification placeholder
            ai_category="maintenance_needed",
            ai_confidence=0.80,
            ai_action_taken="logged_for_review",
            points_earned=10,
        )
        created = await self._insight_repo.create(insight)

        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="inspection_service",
            payload={"entity": "asset_insight", "insight_id": created.insight_id},
        ))
        return created

    async def get_asset_insights(
        self, asset_id: str, limit: int = 50,
    ) -> tuple[list[AssetInsight], int]:
        """Get all technician insights for an asset."""
        if self._insight_repo is None:
            return [], 0
        result = await self._insight_repo.get_all(
            filters={"asset_id": asset_id}, limit=limit,
        )
        total = await self._insight_repo.count(filters={"asset_id": asset_id})
        insights = [AssetInsight(**r.data) for r in result.records]
        return insights, total
