from __future__ import annotations

import json
import re
import sqlite3
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from core.config import settings

DEFAULT_DATA_PATH = Path(__file__).parents[1] / "database" / "rag_items.jsonl"
DEFAULT_DB_PATH = Path(__file__).parents[1] / "database" / "tasteiq.db"
WORD_RE = re.compile(r"[a-z0-9]+")
RETRIEVER_VERSION = "token-overlap-v2"


def _tokens(value: str) -> set[str]:
    return set(WORD_RE.findall(value.lower()))


@lru_cache(maxsize=4)
def load_items(path: str | None = None) -> list[dict]:
    source = Path(path or settings.rag_data_path or DEFAULT_DATA_PATH)
    if not source.exists():
        return []
    items = []
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                items.append(json.loads(line))
            except (TypeError, json.JSONDecodeError):
                continue
    return items


@lru_cache(maxsize=4)
def catalog_sha256(path: str | None = None) -> str:
    source = Path(path or settings.rag_data_path or DEFAULT_DATA_PATH)
    if not source.exists():
        return sha256(b"").hexdigest()
    return sha256(source.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def load_details() -> dict[int, dict]:
    """Load the hydrated Spoonacular fields available for a subset of items."""
    if not DEFAULT_DB_PATH.exists():
        return {}
    details = {}
    try:
        connection = sqlite3.connect(DEFAULT_DB_PATH)
        rows = connection.execute(
            "SELECT spoonacular_id, payload FROM menu_item_details"
        ).fetchall()
        connection.close()
    except sqlite3.Error:
        return {}
    for spoonacular_id, payload in rows:
        try:
            record = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            continue
        nutrients = {
            nutrient.get("name", "").lower(): nutrient.get("amount")
            for nutrient in record.get("nutrition", {}).get("nutrients", [])
        }
        details[spoonacular_id] = {
            "restaurant": record.get("restaurantChain") or "",
            "ingredients": record.get("ingredients") or [],
            "calories": nutrients.get("calories"),
            "protein_g": nutrients.get("protein"),
            "carbs_g": nutrients.get("carbohydrates"),
            "fat_g": nutrients.get("fat"),
        }
    return details


def search_menu(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
) -> list[dict]:
    query_tokens = _tokens(query)
    ranked = []
    for item in load_items():
        metadata = dict(item.get("metadata", {}))
        spoonacular_id = item.get("spoonacular_id")
        detail = load_details().get(spoonacular_id, {}) if isinstance(spoonacular_id, int) else {}
        for key, value in detail.items():
            if value not in (None, "", []):
                metadata[key] = value
        calories = metadata.get("calories")
        protein = metadata.get("protein_g")
        if max_calories is not None and (calories is None or calories > max_calories):
            continue
        if min_protein is not None and (protein is None or protein < min_protein):
            continue
        searchable = (
            item.get("embedding_text", "") + " " + " ".join(metadata.get("derived_tags", []))
        )
        overlap = len(query_tokens & _tokens(searchable))
        name_overlap = len(query_tokens & _tokens(metadata.get("name", "")))
        score = overlap + name_overlap * 1.5
        if query_tokens and score == 0:
            continue
        ranked.append((score, item, metadata))
    ranked.sort(key=lambda pair: (-pair[0], pair[2].get("name", "")))
    results = []
    seen = set()
    for score, item, metadata in ranked:
        unique_id = item.get("spoonacular_id") or item.get("id")
        if unique_id in seen:
            continue
        seen.add(unique_id)
        metadata.update(
            {
                "id": item.get("id"),
                "spoonacular_id": item.get("spoonacular_id"),
                "score": round(score, 2),
            }
        )
        results.append(metadata)
        if len(results) == limit:
            break
    return results
