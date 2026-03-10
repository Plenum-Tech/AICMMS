"""Multi-modal query interface API routes (Story 4)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from cafm.api.dependencies import CurrentUser, require_permission
from cafm.api.schemas.common import APIResponse
from cafm.api.schemas.gamification import QueryInterfaceRequest, QueryInterfaceResponse

router = APIRouter(prefix="/query", tags=["Query Interface"])

_query_service = None


def get_query_service():
    if _query_service is None:
        raise HTTPException(status_code=503, detail="Query service not initialized")
    return _query_service


def set_query_service(svc) -> None:
    global _query_service
    _query_service = svc


@router.post("/", response_model=APIResponse)
async def submit_query(
    request: QueryInterfaceRequest,
    user: CurrentUser = Depends(require_permission("query:read")),
    svc=Depends(get_query_service),
):
    """Submit a natural-language or multi-modal query (Story 4).

    Accepts text, voice, and image queries. The AI engine interprets the
    query and returns structured results with suggested actions.
    """
    result = await svc.process_query(
        query_text=request.query_text,
        query_type=request.query_type,
        context=request.context,
        voice_note_url=request.voice_note_url,
        image_urls=request.image_urls,
        user_id=user.user_id,
    )
    return APIResponse(data=result, message="Query processed")


@router.get("/history", response_model=APIResponse)
async def get_query_history(
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    svc=Depends(get_query_service),
):
    """Get the user's recent query history."""
    history = await svc.get_query_history(user.user_id, limit=limit)
    return APIResponse(data=history)


@router.get("/suggestions", response_model=APIResponse)
async def get_query_suggestions(
    user: CurrentUser,
    context: str | None = Query(None, description="Current page or context for suggestions"),
    svc=Depends(get_query_service),
):
    """Get contextual query suggestions based on user role and location."""
    suggestions = await svc.get_suggestions(user.user_id, context=context)
    return APIResponse(data=suggestions)
