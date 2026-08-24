import json
from pathlib import Path
from typing import Any

from database.db import connection
from utils.preprocess import preprocess_menu_items

OUT_PATH = Path(__file__).parent / "rag_items.jsonl"


def load_raw_items() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT spoonacular_id, payload FROM raw_menu_items").fetchall()

    raw_items: list[dict[str, Any]] = []
    bad = 0

    for r in rows:
        payload_txt = r["payload"]
        try:
            payload = json.loads(payload_txt) if payload_txt else {}
        except (TypeError, json.JSONDecodeError):
            bad += 1
            payload = {}

        # ensure dict
        if not isinstance(payload, dict):
            payload = {"payload": payload}

        payload["spoonacular_id"] = r["spoonacular_id"]
        raw_items.append(payload)

    if bad:
        print(f"Warning: {bad} payload rows failed json.loads()")
    return raw_items


def main() -> None:
    raw_items = load_raw_items()
    cleaned, stats = preprocess_menu_items(raw_items)
    print("Preprocess stats:", stats)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for item in cleaned:
            rec = {
                "id": item.item_id,
                "spoonacular_id": item.raw_source.get("spoonacular_id"),
                "embedding_text": item.embedding_text,
                "metadata": {
                    "name": item.name,
                    "restaurant": item.restaurant,
                    "cuisine": item.cuisine,
                    "ingredients": item.ingredients,
                    "diet_tags": item.diet_tags,
                    "derived_tags": item.derived_tags,
                    "calories": item.calories,
                    "protein_g": item.protein_g,
                    "carbs_g": item.carbs_g,
                    "fat_g": item.fat_g,
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(cleaned)} cleaned items to {OUT_PATH}")


if __name__ == "__main__":
    main()
