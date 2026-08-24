from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Preference = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class ProfileFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]
    dietary_preferences: list[Preference] = Field(default_factory=list, max_length=20)
    disliked_ingredients: list[Preference] = Field(default_factory=list, max_length=50)
    favorite_cuisines: list[Preference] = Field(default_factory=list, max_length=20)

    @field_validator("dietary_preferences", "disliked_ingredients", "favorite_cuisines")
    @classmethod
    def normalize_preferences(cls, values: list[str]) -> list[str]:
        return sorted({value.lower() for value in values})


class ProfileCreate(ProfileFields):
    pass


class ProfileUpdate(ProfileFields):
    pass


class ProfileResponse(ProfileFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class SaveItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spoonacular_id: int = Field(gt=0)
    item_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
    ]


class SavedItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    spoonacular_id: int
    item_name: str
    saved_at: datetime


class InteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    result_ids: list[int]
    created_at: datetime
