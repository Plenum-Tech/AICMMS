"""Service layer for gamification — profiles, badges, leaderboard (Story 15)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.gamification import Badge, GamificationProfile, PointTransaction
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class GamificationService:
    """Business logic for technician gamification and recognition.

    Story 15: Points, levels, badges, streaks, leaderboard, and
    impact tracking for self-entered inspection data.
    """

    def __init__(
        self,
        profile_repo: Repository[GamificationProfile],
        transaction_repo: Repository[PointTransaction],
        badge_repo: Repository[Badge],
        event_bus: EventBus,
    ) -> None:
        self._profile_repo = profile_repo
        self._transaction_repo = transaction_repo
        self._badge_repo = badge_repo
        self._event_bus = event_bus

    # ── Profiles ──────────────────────────────────────────────

    async def get_profile(self, technician_id: str) -> GamificationProfile | None:
        profiles, _ = await self._list_profiles(filters={"technician_id": technician_id})
        return profiles[0] if profiles else None

    async def _list_profiles(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[GamificationProfile], int]:
        result = await self._profile_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._profile_repo.count(filters=filters)
        profiles = [GamificationProfile(**r.data) for r in result.records]
        return profiles, total

    async def get_or_create_profile(self, technician_id: str) -> GamificationProfile:
        profile = await self.get_profile(technician_id)
        if profile:
            return profile
        new_profile = GamificationProfile(
            profile_id=f"GP-{uuid.uuid4().hex[:8].upper()}",
            technician_id=technician_id,
            created_at=datetime.utcnow(),
        )
        return await self._profile_repo.create(new_profile)

    # ── Points ────────────────────────────────────────────────

    async def award_points(
        self,
        technician_id: str,
        points: int,
        point_type: str,
        reason: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> PointTransaction:
        """Award points and update profile."""
        profile = await self.get_or_create_profile(technician_id)

        tx = PointTransaction(
            transaction_id=f"PT-{uuid.uuid4().hex[:8].upper()}",
            technician_id=technician_id,
            points=points,
            point_type=point_type,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            earned_at=datetime.utcnow(),
        )
        created = await self._transaction_repo.create(tx)

        # Update profile totals
        new_total = profile.total_points + points
        updates: dict[str, Any] = {"total_points": new_total}
        if point_type == "impact":
            updates["impact_points"] = profile.impact_points + points

        # Level calculation
        level, level_name = self._calculate_level(new_total)
        updates["current_level"] = level
        updates["level_name"] = level_name
        updates["points_to_next_level"] = self._points_for_next_level(level) - new_total

        await self._profile_repo.update(profile.profile_id, updates)

        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="gamification_service",
            payload={
                "entity": "point_transaction",
                "technician_id": technician_id,
                "points": points,
                "point_type": point_type,
            },
        ))
        return created

    async def get_point_history(
        self, technician_id: str, limit: int = 50,
    ) -> list[PointTransaction]:
        result = await self._transaction_repo.get_all(
            filters={"technician_id": technician_id}, limit=limit,
        )
        return [PointTransaction(**r.data) for r in result.records]

    # ── Leaderboard ───────────────────────────────────────────

    async def get_leaderboard(
        self, period: str = "all_time", top_n: int = 20,
    ) -> list[dict[str, Any]]:
        """Get ranked leaderboard entries."""
        profiles, _ = await self._list_profiles(limit=500)
        # Sort by total_points descending
        sorted_profiles = sorted(profiles, key=lambda p: p.total_points, reverse=True)[:top_n]
        entries = []
        for rank, p in enumerate(sorted_profiles, 1):
            entries.append({
                "rank": rank,
                "technician_id": p.technician_id,
                "technician_name": p.technician_id,  # In production, look up name
                "total_points": p.total_points,
                "impact_points": p.impact_points,
                "level": p.current_level,
                "level_name": p.level_name,
                "badges_count": len(p.badges),
            })
        return entries

    # ── Badges ────────────────────────────────────────────────

    async def list_badges(self, category: str | None = None) -> list[Badge]:
        filters = {"category": category} if category else None
        result = await self._badge_repo.get_all(filters=filters)
        return [Badge(**r.data) for r in result.records]

    async def get_badge(self, badge_id: str) -> Badge | None:
        return await self._badge_repo.get_by_id(badge_id)

    # ── Level Calculations ────────────────────────────────────

    @staticmethod
    def _calculate_level(total_points: int) -> tuple[int, str]:
        levels = [
            (0, "Rookie"), (100, "Apprentice"), (500, "Specialist"),
            (1500, "Expert"), (5000, "Master"), (15000, "Legend"),
        ]
        level = 1
        name = "Rookie"
        for i, (threshold, label) in enumerate(levels):
            if total_points >= threshold:
                level = i + 1
                name = label
        return level, name

    @staticmethod
    def _points_for_next_level(current_level: int) -> int:
        thresholds = [0, 100, 500, 1500, 5000, 15000, 50000]
        if current_level < len(thresholds):
            return thresholds[current_level]
        return thresholds[-1]
