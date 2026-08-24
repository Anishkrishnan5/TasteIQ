from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from personalization.database import get_session
from personalization.models import SavedMenuItem, SearchInteraction, UserProfile
from personalization.schemas import (
    InteractionResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
    SavedItemResponse,
    SaveItemRequest,
)

router = APIRouter(prefix="/api/profiles", tags=["personalization"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _profile_or_404(session: Session, profile_id: UUID) -> UserProfile:
    profile = session.get(UserProfile, str(profile_id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, session: SessionDependency):
    profile = UserProfile(**payload.model_dump())
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: UUID, session: SessionDependency):
    return _profile_or_404(session, profile_id)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: UUID, payload: ProfileUpdate, session: SessionDependency):
    profile = _profile_or_404(session, profile_id)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/{profile_id}/saved", response_model=list[SavedItemResponse])
def list_saved_items(profile_id: UUID, session: SessionDependency):
    _profile_or_404(session, profile_id)
    return session.scalars(
        select(SavedMenuItem)
        .where(SavedMenuItem.profile_id == str(profile_id))
        .order_by(desc(SavedMenuItem.saved_at))
    ).all()


@router.post(
    "/{profile_id}/saved",
    response_model=SavedItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_item(profile_id: UUID, payload: SaveItemRequest, session: SessionDependency):
    _profile_or_404(session, profile_id)
    saved = SavedMenuItem(profile_id=str(profile_id), **payload.model_dump())
    session.add(saved)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        saved = session.scalar(
            select(SavedMenuItem).where(
                SavedMenuItem.profile_id == str(profile_id),
                SavedMenuItem.spoonacular_id == payload.spoonacular_id,
            )
        )
    return saved


@router.delete("/{profile_id}/saved/{spoonacular_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_item(profile_id: UUID, spoonacular_id: int, session: SessionDependency):
    _profile_or_404(session, profile_id)
    saved = session.scalar(
        select(SavedMenuItem).where(
            SavedMenuItem.profile_id == str(profile_id),
            SavedMenuItem.spoonacular_id == spoonacular_id,
        )
    )
    if saved is not None:
        session.delete(saved)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{profile_id}/history", response_model=list[InteractionResponse])
def search_history(profile_id: UUID, session: SessionDependency, limit: int = 20):
    _profile_or_404(session, profile_id)
    return session.scalars(
        select(SearchInteraction)
        .where(SearchInteraction.profile_id == str(profile_id))
        .order_by(desc(SearchInteraction.created_at))
        .limit(min(max(limit, 1), 100))
    ).all()
