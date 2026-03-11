"""Gamification API routes — profiles, leaderboard, badges (Story 15)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse
from cafm.api.schemas.gamification import (
    BadgeResponse, GamificationProfileResponse,
    LeaderboardEntry, PointTransactionResponse,
)

router = APIRouter(prefix="/gamification", tags=["Gamification"])

_gamification_service = None


def get_gamification_service():
    if _gamification_service is None:
        raise HTTPException(status_code=503, detail="Gamification service not initialized")
    return _gamification_service


def set_gamification_service(svc) -> None:
    global _gamification_service
    _gamification_service = svc


# ── Profiles ──────────────────────────────────────────────────


@router.get("/profile/{technician_id}", response_model=APIResponse)
async def get_gamification_profile(
    technician_id: str, user: CurrentUser,
    svc=Depends(get_gamification_service),
):
    """Get gamification profile for a technician (Story 15)."""
    profile = await svc.get_profile(technician_id)
    if not profile: raise HTTPException(status_code=404, detail=f"Profile for '{technician_id}' not found")
    return APIResponse(data=GamificationProfileResponse(**profile.model_dump()))


@router.get("/profile/me", response_model=APIResponse)
async def get_my_profile(
    user: CurrentUser,
    svc=Depends(get_gamification_service),
):
    """Get the current user's gamification profile."""
    profile = await svc.get_profile(user.user_id)
    if not profile: raise HTTPException(status_code=404, detail="Profile not found")
    return APIResponse(data=GamificationProfileResponse(**profile.model_dump()))


# ── Leaderboard ───────────────────────────────────────────────


@router.get("/leaderboard", response_model=APIResponse)
async def get_leaderboard(
    user: CurrentUser,
    period: str = Query("all_time", description="Period: all_time, monthly, weekly"),
    top_n: int = Query(20, ge=1, le=100),
    svc=Depends(get_gamification_service),
):
    """Get gamification leaderboard (Story 15)."""
    entries = await svc.get_leaderboard(period=period, top_n=top_n)
    return APIResponse(data=entries, message=f"Top {top_n} for {period}")


# ── Badges ────────────────────────────────────────────────────


@router.get("/badges", response_model=APIResponse)
async def list_badges(
    user: CurrentUser,
    category: str | None = Query(None),
    svc=Depends(get_gamification_service),
):
    badges = await svc.list_badges(category=category)
    items = [BadgeResponse(**b.model_dump()) for b in badges]
    return APIResponse(data=items)


@router.get("/badges/{badge_id}", response_model=APIResponse)
async def get_badge(badge_id: str, user: CurrentUser, svc=Depends(get_gamification_service)):
    badge = await svc.get_badge(badge_id)
    if not badge: raise HTTPException(status_code=404, detail=f"Badge '{badge_id}' not found")
    return APIResponse(data=BadgeResponse(**badge.model_dump()))


# ── Point Transactions ────────────────────────────────────────


@router.get("/points/{technician_id}", response_model=APIResponse)
async def get_point_history(
    technician_id: str, user: CurrentUser,
    svc=Depends(get_gamification_service),
):
    """Get point transaction history for a technician."""
    transactions = await svc.get_point_history(technician_id)
    items = [PointTransactionResponse(**t.model_dump()) for t in transactions]
    return APIResponse(data=items)
