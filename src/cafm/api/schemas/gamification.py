"""Request/response schemas for the gamification API (Story 15)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GamificationProfileResponse(BaseModel):
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


class LeaderboardEntry(BaseModel):
    rank: int
    technician_id: str
    technician_name: str
    total_points: int
    impact_points: int
    level: int
    level_name: str
    badges_count: int = 0


class BadgeResponse(BaseModel):
    badge_id: str
    name: str
    description: str
    icon_url: str | None = None
    criteria: str
    points_value: int = 0
    category: str | None = None


class PointTransactionResponse(BaseModel):
    transaction_id: str
    technician_id: str
    points: int
    point_type: str
    reason: str
    reference_type: str | None = None
    reference_id: str | None = None
    earned_at: datetime | None = None


class AssetInsightCreateRequest(BaseModel):
    """Submit a technical insight after QR scan (Story 16)."""
    asset_id: str
    insight_text: str = Field(..., min_length=1)
    qr_code: str | None = None
    voice_note_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)


class AssetInsightResponse(BaseModel):
    insight_id: str
    technician_id: str
    asset_id: str
    insight_text: str
    voice_note_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)
    scanned_qr_code: str | None = None
    timestamp: datetime | None = None
    ai_category: str | None = None
    ai_action_taken: str | None = None
    ai_confidence: float | None = None
    related_work_order_id: str | None = None
    points_earned: int = 0
    impact_points_earned: int = 0
    impact_description: str | None = None


class QueryInterfaceRequest(BaseModel):
    """Multi-modal query interface (Story 4)."""
    query_text: str = Field(..., min_length=1, description="Natural language query")
    query_type: str = "text"  # "text", "voice", "image"
    context: dict[str, Any] = Field(default_factory=dict)
    voice_note_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)


class QueryInterfaceResponse(BaseModel):
    query_id: str
    query_text: str
    response_text: str
    response_data: dict[str, Any] = Field(default_factory=dict)
    suggested_actions: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    confidence: float | None = None
    processing_time_ms: float | None = None


class OccupancyResponse(BaseModel):
    space_id: str
    building_id: str
    timestamp: datetime
    occupant_count: int
    capacity: int | None = None
    utilization_pct: float | None = None


class SpaceUtilizationResponse(BaseModel):
    space_id: str
    building_id: str
    period_start: datetime
    period_end: datetime
    avg_occupancy: float | None = None
    peak_occupancy: int | None = None
    avg_utilization_pct: float | None = None
    total_hours_occupied: float | None = None


class ReservationCreateRequest(BaseModel):
    reservation_id: str = Field(..., min_length=1, max_length=50)
    space_id: str
    building_id: str
    title: str | None = None
    reserved_by: str
    start_time: datetime
    end_time: datetime
    attendee_count: int | None = None


class ReservationResponse(BaseModel):
    reservation_id: str
    space_id: str
    building_id: str
    title: str | None = None
    reserved_by: str
    start_time: datetime
    end_time: datetime
    attendee_count: int | None = None
    status: str
    created_at: datetime | None = None
