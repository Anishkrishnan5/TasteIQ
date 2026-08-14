from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.errors import BadRequestError
from rag.pipeline import recommend

router = APIRouter()


def get_app_version():
    return "0.1.0"


@router.get("/health")
def health(version: str = Depends(get_app_version)):
    return {"status": "ok", "version": version}


class RecommendationRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    limit: int = Field(default=6, ge=1, le=20)
    max_calories: float | None = Field(default=None, gt=0)
    min_protein: float | None = Field(default=None, ge=0)
    diet: str | None = Field(default=None, max_length=40)


@router.post("/api/recommendations")
def recommendations(request: RecommendationRequest):
    return recommend(**request.model_dump())


@router.get("/test-error")
def test_error(q: int):
    if q < 0:
        raise BadRequestError("q must be non-negative")
    return {"q": q}
