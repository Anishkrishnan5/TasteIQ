from fastapi import APIRouter, Request

from api.schemas import ErrorResponse, RecommendationRequest, RecommendationResponse
from core.config import settings
from rag.pipeline import recommend

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}


@router.post(
    "/api/recommendations",
    response_model=RecommendationResponse,
    responses={422: {"model": ErrorResponse}},
)
def recommendations(payload: RecommendationRequest, request: Request):
    return recommend(**payload.model_dump(), request_id=request.state.request_id)
