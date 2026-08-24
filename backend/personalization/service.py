from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from personalization.models import SavedMenuItem, SearchInteraction, UserProfile


@dataclass(frozen=True)
class PreferenceSnapshot:
    dietary_preferences: frozenset[str]
    disliked_ingredients: frozenset[str]
    favorite_cuisines: frozenset[str]
    saved_source_ids: frozenset[int]


def preference_snapshot(session: Session, profile_id: str) -> PreferenceSnapshot | None:
    profile = session.get(UserProfile, profile_id)
    if profile is None:
        return None
    saved_ids = session.scalars(
        select(SavedMenuItem.spoonacular_id).where(SavedMenuItem.profile_id == profile_id)
    )
    return PreferenceSnapshot(
        dietary_preferences=frozenset(profile.dietary_preferences),
        disliked_ingredients=frozenset(profile.disliked_ingredients),
        favorite_cuisines=frozenset(profile.favorite_cuisines),
        saved_source_ids=frozenset(saved_ids),
    )


def rerank_for_profile(
    items: list[dict[str, Any]], preferences: PreferenceSnapshot
) -> list[dict[str, Any]]:
    """Remove disliked ingredients and apply small, explainable preference boosts."""
    reranked = []
    for position, source in enumerate(items):
        item = dict(source)
        ingredients = {str(value).lower() for value in item.get("ingredients", [])}
        if any(
            disliked in ingredient
            for disliked in preferences.disliked_ingredients
            for ingredient in ingredients
        ):
            continue

        boosts: list[str] = []
        boost = 0.0
        cuisine = str(item.get("cuisine", "")).lower()
        tags = {str(value).lower() for value in item.get("diet_tags", [])}
        tags.update(str(value).lower() for value in item.get("derived_tags", []))
        if (item.get("protein_g") or 0) >= 25:
            tags.add("high_protein")
        if (item.get("carbs_g") or float("inf")) <= 20:
            tags.add("low_carb")
        if (item.get("fat_g") or float("inf")) <= 15:
            tags.add("low_fat")
        source_id = item.get("spoonacular_id")
        searchable_text = " ".join(
            [str(item.get("name", "")), str(item.get("restaurant", "")), cuisine, *ingredients]
        ).lower()
        matching_cuisines = {
            favorite for favorite in preferences.favorite_cuisines if favorite in searchable_text
        }
        if matching_cuisines:
            boost += 1.0
            boosts.append(f"favorite cuisine: {', '.join(sorted(matching_cuisines))}")
        matching_diets = tags & preferences.dietary_preferences
        if matching_diets:
            boost += 1.25
            boosts.append(f"diet preference: {', '.join(sorted(matching_diets))}")
        if source_id in preferences.saved_source_ids:
            boost += 0.5
            boosts.append("previously saved")

        item["personalization"] = {"boost": boost, "reasons": boosts}
        reranked.append((float(item.get("score", 0)) + boost, position, item))

    reranked.sort(key=lambda entry: (-entry[0], entry[1]))
    return [item for _score, _position, item in reranked]


def record_search(
    session: Session, profile_id: str, query: str, results: list[dict[str, Any]]
) -> None:
    session.add(
        SearchInteraction(
            profile_id=profile_id,
            query=query,
            result_ids=[item["spoonacular_id"] for item in results],
        )
    )
    session.commit()
