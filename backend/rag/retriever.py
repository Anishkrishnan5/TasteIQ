from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from core.config import settings

DEFAULT_DATA_PATH = Path(__file__).parents[1] / "database" / "rag_items.jsonl"
WORD_RE = re.compile(r"[a-z0-9]+")


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


def search_menu(query: str, limit: int = 6, max_calories: float | None = None,
                min_protein: float | None = None, diet: str | None = None) -> list[dict]:
    query_tokens = _tokens(" ".join(filter(None, [query, diet or ""])))
    ranked = []
    for item in load_items():
        metadata = item.get("metadata", {})
        calories = metadata.get("calories")
        protein = metadata.get("protein_g")
        if max_calories is not None and calories is not None and calories > max_calories:
            continue
        if min_protein is not None and protein is not None and protein < min_protein:
            continue
        searchable = item.get("embedding_text", "") + " " + " ".join(metadata.get("derived_tags", []))
        overlap = len(query_tokens & _tokens(searchable))
        name_overlap = len(query_tokens & _tokens(metadata.get("name", "")))
        score = overlap + name_overlap * 1.5
        if diet and diet.replace("-", "_").lower() in metadata.get("diet_tags", []) + metadata.get("derived_tags", []):
            score += 3
        if query_tokens and score == 0:
            continue
        ranked.append((score, item))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].get("metadata", {}).get("name", "")))
    results = []
    for score, item in ranked[:limit]:
        metadata = dict(item.get("metadata", {}))
        metadata.update({"id": item.get("id"), "score": round(score, 2)})
        results.append(metadata)
    return results
