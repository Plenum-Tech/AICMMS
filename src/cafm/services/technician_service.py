"""Service layer for technician / manpower management."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.technicians import Technician
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class TechnicianService:
    """Business logic for technician management and intelligent routing.

    Handles CRUD, availability tracking, gamification, and
    AI-based work order routing recommendations.
    """

    def __init__(
        self,
        repository: Repository[Technician],
        event_bus: EventBus,
    ) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def create_technician(
        self, data: dict[str, Any], created_by: str | None = None
    ) -> Technician:
        """Create a new technician record."""
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by

        tech = Technician(**data)
        created = await self._repo.create(tech)

        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED,
            source="technician_service",
            payload={"entity": "technician", "technician_id": created.technician_id},
        ))
        logger.info("Technician created: %s", created.technician_id)
        return created

    async def get_technician(self, technician_id: str) -> Technician | None:
        """Get a technician by ID."""
        return await self._repo.get_by_id(technician_id)

    async def list_technicians(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Technician], int]:
        """List technicians with filtering and pagination."""
        result_set = await self._repo.get_all(
            filters=filters, limit=limit, offset=offset,
        )
        total = await self._repo.count(filters=filters)
        technicians = []
        for record in result_set.records:
            if isinstance(record, Technician):
                technicians.append(record)
            else:
                technicians.append(Technician(**record.data if hasattr(record, "data") else {}))
        return technicians, total

    async def update_technician(
        self, technician_id: str, updates: dict[str, Any], updated_by: str | None = None
    ) -> Technician | None:
        """Update a technician record."""
        updates["updated_at"] = datetime.utcnow()
        if updated_by:
            updates["updated_by"] = updated_by
        updates = {k: v for k, v in updates.items() if v is not None}

        updated = await self._repo.update(technician_id, updates)
        if updated:
            await self._event_bus.publish(Event(
                type=EventType.RECORD_UPDATED,
                source="technician_service",
                payload={"entity": "technician", "technician_id": technician_id},
            ))
        return updated

    async def get_available_technicians(
        self, skill_codes: list[str] | None = None
    ) -> list[Technician]:
        """Get all available technicians, optionally filtered by skills."""
        techs, _ = await self.list_technicians(
            filters={"is_available": True}, limit=500,
        )
        if skill_codes:
            techs = [
                t for t in techs
                if any(s in t.skill_codes for s in skill_codes)
            ]
        return techs

    async def recommend_technician(
        self,
        required_skills: list[str],
        building_id: str | None = None,
        priority: str = "medium",
    ) -> list[dict[str, Any]]:
        """Recommend the best technician for a work order.

        Per AICMMS spec: auto-route work orders to the right technician
        based on availability, distance, expertise, and workload.
        """
        available = await self.get_available_technicians(skill_codes=required_skills)
        if not available:
            return []

        scored: list[tuple[Technician, float, list[str]]] = []
        for tech in available:
            score = 0.0
            reasons = []

            # Skill match (0-40 points)
            matched = sum(1 for s in required_skills if s in tech.skill_codes)
            skill_score = (matched / max(len(required_skills), 1)) * 40
            score += skill_score
            if matched == len(required_skills):
                reasons.append("Full skill match")

            # Workload (0-30 points): fewer current jobs = higher score
            workload_score = max(0, 30 - (tech.current_workload_count * 5))
            score += workload_score
            if tech.current_workload_count == 0:
                reasons.append("No current workload")

            # Performance (0-20 points)
            if tech.customer_satisfaction_avg:
                perf_score = (tech.customer_satisfaction_avg / 5.0) * 20
                score += perf_score
                if tech.customer_satisfaction_avg >= 4.0:
                    reasons.append("High satisfaction rating")

            # Experience (0-10 points)
            if tech.experience_years:
                exp_score = min(10, tech.experience_years)
                score += exp_score

            # Location match
            if building_id and tech.home_base_building_id == building_id:
                score += 5
                reasons.append("Same building")

            scored.append((tech, min(score / 100, 1.0), reasons))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return [
            {
                "technician_id": tech.technician_id,
                "technician_name": f"{tech.first_name} {tech.last_name}",
                "match_score": round(score, 2),
                "reasons": reasons,
                "estimated_response_hours": tech.avg_response_time_hours,
                "current_workload": tech.current_workload_count,
                "skill_match": any(s in tech.skill_codes for s in required_skills),
            }
            for tech, score, reasons in scored[:5]  # Top 5 recommendations
        ]

    async def award_points(
        self, technician_id: str, points: int, reason: str = "task_completion"
    ) -> Technician | None:
        """Award gamification points to a technician.

        Per AICMMS spec: gamified experience with points and levels.
        """
        tech = await self._repo.get_by_id(technician_id)
        if tech is None:
            return None

        new_points = tech.gamification_points + points
        new_level = 1 + (new_points // 100)  # Level up every 100 points

        return await self.update_technician(technician_id, {
            "gamification_points": new_points,
            "gamification_level": new_level,
        })
