"""Gamification domain models.

Supports the AICMMS spec for rewarding technicians with points and levels
based on their inputs (inspection reports, technical insights, knowledge sharing).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from cafm.models.base import CAFMBaseModel


class GamificationProfile(CAFMBaseModel):
    """Gamification profile for a technician or user."""

    profile_id: str
    technician_id: str
    total_points: int = 0
    impact_points: int = 0
    current_level: int = 1
    level_name: str = "Rookie"
    points_to_next_level: int = 100
    badges: list[str] = Field(default_factory=list)
    streak_days: int = 0
    longest_streak: int = 0
    total_inspections: int = 0
    total_insights_shared: int = 0
    insights_that_led_to_action: int = 0
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class PointTransaction(CAFMBaseModel):
    """Record of points earned or deducted."""

    transaction_id: str
    technician_id: str
    points: int
    point_type: str  # "inspection", "insight", "impact", "streak", "badge"
    reason: str
    reference_type: str | None = None  # e.g., "inspection_report", "asset_insight"
    reference_id: str | None = None
    earned_at: datetime | None = None


class LevelDefinition(CAFMBaseModel):
    """Definition of gamification levels."""

    level: int
    name: str  # e.g., "Rookie", "Specialist", "Expert", "Master", "Legend"
    min_points: int
    max_points: int | None = None
    badge_icon: str | None = None
    perks: list[str] = Field(default_factory=list)
    description: str | None = None


class Badge(CAFMBaseModel):
    """Achievement badge that can be earned."""

    badge_id: str
    name: str
    description: str
    icon_url: str | None = None
    criteria: str  # e.g., "complete_50_inspections", "share_10_insights"
    points_value: int = 0
    category: str | None = None  # "inspection", "knowledge", "responsiveness"


class AssetInsight(CAFMBaseModel):
    """Technical insight shared by a technician for an asset.

    Per spec: technicians scan QR code and add insights, which get
    classified by the platform and trigger appropriate actions.
    """

    insight_id: str
    technician_id: str
    asset_id: str
    insight_text: str
    voice_note_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)
    scanned_qr_code: str | None = None
    timestamp: datetime | None = None

    # AI classification
    ai_category: str | None = None  # e.g., "maintenance_needed", "safety_concern", "optimization"
    ai_action_taken: str | None = None  # e.g., "work_order_created", "pm_schedule_updated"
    ai_confidence: float | None = None
    related_work_order_id: str | None = None

    # Gamification
    points_earned: int = 0
    impact_points_earned: int = 0
    impact_description: str | None = None

    custom_attributes: dict[str, Any] = Field(default_factory=dict)
