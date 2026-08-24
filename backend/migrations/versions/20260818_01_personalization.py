"""Create personalization tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("dietary_preferences", sa.JSON(), nullable=False),
        sa.Column("disliked_ingredients", sa.JSON(), nullable=False),
        sa.Column("favorite_cuisines", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "saved_menu_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("spoonacular_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=300), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["profile_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "spoonacular_id"),
    )
    op.create_index("ix_saved_menu_items_profile_id", "saved_menu_items", ["profile_id"])
    op.create_table(
        "search_interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("result_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["profile_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_interactions_profile_id", "search_interactions", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_search_interactions_profile_id", table_name="search_interactions")
    op.drop_table("search_interactions")
    op.drop_index("ix_saved_menu_items_profile_id", table_name="saved_menu_items")
    op.drop_table("saved_menu_items")
    op.drop_table("user_profiles")
