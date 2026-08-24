from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from personalization.database import Base

JSON_VALUE = JSON().with_variant(JSONB(), "postgresql")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    display_name: Mapped[str] = mapped_column(String(80))
    dietary_preferences: Mapped[list[str]] = mapped_column(JSON_VALUE, default=list)
    disliked_ingredients: Mapped[list[str]] = mapped_column(JSON_VALUE, default=list)
    favorite_cuisines: Mapped[list[str]] = mapped_column(JSON_VALUE, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    saved_items: Mapped[list["SavedMenuItem"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    interactions: Mapped[list["SearchInteraction"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class SavedMenuItem(Base):
    __tablename__ = "saved_menu_items"
    __table_args__ = (UniqueConstraint("profile_id", "spoonacular_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True
    )
    spoonacular_id: Mapped[int] = mapped_column(Integer)
    item_name: Mapped[str] = mapped_column(String(300))
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped[UserProfile] = relationship(back_populates="saved_items")


class SearchInteraction(Base):
    __tablename__ = "search_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True
    )
    query: Mapped[str] = mapped_column(Text)
    result_ids: Mapped[list[int]] = mapped_column(JSON_VALUE, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped[UserProfile] = relationship(back_populates="interactions")
