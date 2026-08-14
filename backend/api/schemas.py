from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

API_SCHEMA_VERSION = "1.0"


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=300)]
    limit: int = Field(default=6, ge=1, le=20)
    max_calories: float | None = Field(default=None, gt=0, le=5000)
    min_protein: float | None = Field(default=None, ge=0, le=500)


class MenuItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    spoonacular_id: int
    name: str
    restaurant: str = ""
    cuisine: str = ""
    ingredients: list[str] = Field(default_factory=list)
    diet_tags: list[str] = Field(default_factory=list)
    derived_tags: list[str] = Field(default_factory=list)
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    score: float


class AppliedFilters(BaseModel):
    max_calories: float | None
    min_protein: float | None
    unknown_nutrition_policy: Literal["exclude"] = "exclude"


class TimingMetadata(BaseModel):
    retrieval_ms: float
    response_ms: float


class ResponseMetadata(BaseModel):
    request_id: str
    result_count: int
    filters: AppliedFilters
    timings_ms: TimingMetadata
    retriever_version: str
    catalog_sha256: str


class RecommendationResponse(BaseModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    query: str
    message: str
    results: list[MenuItem]
    meta: ResponseMetadata


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    schema_version: Literal["1.0"] = API_SCHEMA_VERSION
    error: ErrorBody
    request_id: str
