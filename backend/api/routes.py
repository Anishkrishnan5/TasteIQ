from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from api.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from chat.service import answer_with_sources
from core.config import settings
from personalization.database import get_session
from personalization.service import preference_snapshot, record_search
from rag.pipeline import recommend

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}


@router.post(
    "/api/recommendations",
    response_model=RecommendationResponse,
    responses={422: {"model": ErrorResponse}},
)
def recommendations(
    payload: RecommendationRequest,
    request: Request,
    session: SessionDependency,
):
    values = payload.model_dump()
    profile_id = values.pop("profile_id")
    preferences = None
    if profile_id is not None:
        preferences = preference_snapshot(session, str(profile_id))
        if preferences is None:
            raise HTTPException(status_code=404, detail="Profile not found.")
    response = recommend(
        **values,
        request_id=request.state.request_id,
        profile_id=str(profile_id) if profile_id else None,
        preferences=preferences,
    )
    if profile_id is not None:
        record_search(session, str(profile_id), payload.query, response["results"])
    return response


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    responses={422: {"model": ErrorResponse}},
)
def chat(payload: ChatRequest, request: Request, session: SessionDependency):
    preferences = None
    if payload.profile_id is not None:
        preferences = preference_snapshot(session, str(payload.profile_id))
        if preferences is None:
            raise HTTPException(status_code=404, detail="Profile not found.")

    previous_user_messages = [turn.content for turn in payload.history if turn.role == "user"][-2:]
    retrieval_query = " ".join([*previous_user_messages, payload.message])
    retrieval = recommend(
        retrieval_query,
        limit=6,
        max_calories=payload.max_calories,
        min_protein=payload.min_protein,
        request_id=request.state.request_id,
        profile_id=str(payload.profile_id) if payload.profile_id else None,
        preferences=preferences,
    )
    history = [turn.model_dump() for turn in payload.history]
    generated = answer_with_sources(payload.message, history, retrieval["results"])
    if payload.profile_id is not None:
        record_search(
            session,
            str(payload.profile_id),
            retrieval_query,
            retrieval["results"],
        )
    return {
        "schema_version": "1.0",
        "answer": generated.answer,
        "citations": generated.cited_items,
        "meta": {
            "request_id": request.state.request_id,
            "provider": generated.provider,
            "model": generated.model,
            "grounded": True,
            "degraded": generated.degraded_reason is not None,
            "degraded_reason": generated.degraded_reason,
            "retrieval": retrieval["meta"],
        },
    }
