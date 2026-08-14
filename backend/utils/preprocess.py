# backend/utils/preprocess.py
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

# ---------------------------
# Canonicalization helpers
# ---------------------------

_WORD_RE = re.compile(r"[^a-z0-9\s,./+-]")  # keep basic separators
_WS_RE = re.compile(r"\s+")

FILLER_WORDS = {
    "fresh",
    "organic",
    "homemade",
    "house",
    "housemade",
    "signature",
    "classic",
    "delicious",
    "tasty",
    "served",
    "with",
    "and",
    "style",
    "chef",
    "choice",
}

# Lightweight synonym map you can grow over time
INGREDIENT_SYNONYMS = {
    "chilli": "chili",
    "garbanzo bean": "chickpea",
    "garbanzo beans": "chickpea",
    "scallion": "green onion",
    "spring onion": "green onion",
    "bell peppers": "bell pepper",
    "tomatoes": "tomato",
    "potatoes": "potato",
}

CUISINE_MAP = {
    "mexican": "mexican",
    "tex mex": "mexican",
    "italian": "italian",
    "american": "american",
    "chinese": "chinese",
    "thai": "thai",
    "indian": "indian",
    "japanese": "japanese",
    "mediterranean": "mediterranean",
    "middle eastern": "middle eastern",
    "korean": "korean",
    "vietnamese": "vietnamese",
    "french": "french",
    "greek": "greek",
    "spanish": "spanish",
    "fusion": "fusion",
}

DIET_TAG_CANON = {
    "vegetarian": "vegetarian",
    "vegan": "vegan",
    "gluten free": "gluten_free",
    "gluten-free": "gluten_free",
    "dairy free": "dairy_free",
    "dairy-free": "dairy_free",
    "keto": "keto",
    "paleo": "paleo",
    "low carb": "low_carb",
    "low-carb": "low_carb",
    "high protein": "high_protein",
    "high-protein": "high_protein",
}


def clean_text(s: str | None) -> str:
    """Lowercase + strip + remove weird chars + normalize whitespace."""
    if not s:
        return ""
    s = s.lower().strip()
    s = _WORD_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def to_float(x: Any) -> float | None:
    """Parse numbers robustly; returns None if missing/unparseable."""
    if x is None:
        return None
    if isinstance(x, int | float):
        # guard against NaN
        try:
            if x != x:  # NaN
                return None
        except Exception:
            pass
        return float(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"", "na", "n/a", "none", "null"}:
            return None
        # pull first number from string like "350 kcal" or "12g"
        m = re.search(r"-?\d+(\.\d+)?", s)
        return float(m.group(0)) if m else None
    return None


def clamp_nonneg(x: float | None) -> float | None:
    if x is None:
        return None
    return max(0.0, x)


def normalize_cuisine(c: str | None) -> str:
    c = clean_text(c)
    if not c:
        return ""
    return CUISINE_MAP.get(c, c)


def normalize_diet_tags(tags: Any) -> list[str]:
    """
    Accepts list/str/None.
    Outputs stable snake_case tags like ['vegan','gluten_free'].
    """
    if tags is None:
        return []
    if isinstance(tags, str):
        raw = [t.strip() for t in re.split(r"[;,/|]+", tags) if t.strip()]
    elif isinstance(tags, list | tuple):
        raw = [str(t) for t in tags if t is not None]
    else:
        raw = [str(tags)]

    out: list[str] = []
    for t in raw:
        t2 = clean_text(t)
        if not t2:
            continue
        t2 = DIET_TAG_CANON.get(t2, t2.replace(" ", "_"))
        out.append(t2)

    # de-dupe, stable
    return sorted(set(out))


def normalize_ingredient(i: str) -> str:
    i = clean_text(i)
    if not i:
        return ""

    # remove filler words
    parts = [p for p in i.split() if p not in FILLER_WORDS]
    i = " ".join(parts).strip()

    # normalize some common punctuation patterns
    i = i.replace("&", "and")
    i = _WS_RE.sub(" ", i).strip()

    # apply synonym replacements (exact match + simple plural)
    if i in INGREDIENT_SYNONYMS:
        i = INGREDIENT_SYNONYMS[i]
    else:
        # naive singularization (helps embeddings; keep conservative)
        if i.endswith("es") and len(i) > 4:
            cand = i[:-2]
            if cand in INGREDIENT_SYNONYMS:
                i = INGREDIENT_SYNONYMS[cand]
        elif i.endswith("s") and len(i) > 3 and not i.endswith("ss"):
            cand = i[:-1]
            if cand in INGREDIENT_SYNONYMS:
                i = INGREDIENT_SYNONYMS[cand]

    return i


def normalize_ingredients(ingredients: Any) -> list[str]:
    """
    Accepts list/str/None.
    Spoonacular sometimes returns free text; we try to split safely.
    """
    if ingredients is None:
        return []
    if isinstance(ingredients, str):
        raw = [t.strip() for t in re.split(r"[;,/|]+", ingredients) if t.strip()]
    elif isinstance(ingredients, list | tuple):
        raw = [str(t) for t in ingredients if t is not None]
    else:
        raw = [str(ingredients)]

    out = [normalize_ingredient(x) for x in raw]
    out = [x for x in out if x]
    return sorted(set(out))


def compute_derived_tags(
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
) -> list[str]:
    """
    Cheap heuristics to help retrieval.
    These are not medical rules—just retrieval cues.
    """
    tags: list[str] = []
    if calories is not None:
        if calories <= 500:
            tags.append("under_500_cal")
        elif calories <= 700:
            tags.append("under_700_cal")

    if protein_g is not None and protein_g >= 25:
        tags.append("high_protein")

    if carbs_g is not None and carbs_g <= 20:
        tags.append("low_carb")

    if fat_g is not None and fat_g <= 15:
        tags.append("low_fat")

    return tags


def stable_item_id(restaurant: str, name: str) -> str:
    """
    Deterministic id helps de-duping and vector upserts.
    """
    base = f"{restaurant}::{name}"
    base = clean_text(base).replace(" ", "_")
    return base[:200]  # avoid silly-long ids


def build_embedding_text(record: dict[str, Any]) -> str:
    """
    This is what you embed.
    Keep it dense, factual, consistent.
    """
    name = record.get("name", "")
    restaurant = record.get("restaurant", "")
    cuisine = record.get("cuisine", "")
    ingredients = record.get("ingredients", [])
    diet_tags = record.get("diet_tags", [])
    derived_tags = record.get("derived_tags", [])

    calories = record.get("calories")
    protein = record.get("protein_g")
    carbs = record.get("carbs_g")
    fat = record.get("fat_g")

    ing_txt = ", ".join(ingredients) if ingredients else ""
    tag_txt = (
        ", ".join(sorted(set(diet_tags + derived_tags))) if (diet_tags or derived_tags) else ""
    )

    # Use short key:value lines. This embeds well and is easy to inspect.
    lines = [
        f"name: {name}",
        f"restaurant: {restaurant}",
        f"cuisine: {cuisine}" if cuisine else "",
        f"ingredients: {ing_txt}" if ing_txt else "",
        f"tags: {tag_txt}" if tag_txt else "",
        f"calories_kcal: {int(calories)}" if calories is not None else "",
        f"protein_g: {round(protein, 1)}" if protein is not None else "",
        f"carbs_g: {round(carbs, 1)}" if carbs is not None else "",
        f"fat_g: {round(fat, 1)}" if fat is not None else "",
    ]
    return "\n".join([ln for ln in lines if ln]).strip()


# ---------------------------
# Public pipeline
# ---------------------------


@dataclass
class CleanedMenuItem:
    item_id: str
    name: str
    restaurant: str
    cuisine: str
    ingredients: list[str]
    diet_tags: list[str]
    derived_tags: list[str]
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    embedding_text: str
    raw_source: dict[str, Any]  # keep for debugging


def clean_one_menu_item(raw: dict[str, Any]) -> CleanedMenuItem | None:
    """
    Map your raw Spoonacular-ish dict into a cleaned, RAG-ready record.
    Adjust field names here to match your ingested schema.
    """
    # ---- REQUIRED-ish fields ----
    name = clean_text(raw.get("name") or raw.get("title") or "")
    if not name:
        return None

    restaurant = clean_text(
        raw.get("restaurant")
        or raw.get("restaurant_name")
        or raw.get("restaurantChain")
        or raw.get("brand")
        or ""
    )
    cuisine = normalize_cuisine(raw.get("cuisine") or raw.get("cuisines") or "")

    ingredients = normalize_ingredients(
        raw.get("ingredients") or raw.get("ingredientList") or raw.get("ingredient_list")
    )
    diet_tags = normalize_diet_tags(raw.get("dietary_tags") or raw.get("diets") or raw.get("tags"))

    # ---- Nutrition fields (try common variants) ----
    calories = clamp_nonneg(to_float(raw.get("calories") or raw.get("kcal")))
    protein_g = clamp_nonneg(to_float(raw.get("protein") or raw.get("protein_g")))
    carbs_g = clamp_nonneg(
        to_float(raw.get("carbs") or raw.get("carbohydrates") or raw.get("carbs_g"))
    )
    fat_g = clamp_nonneg(to_float(raw.get("fat") or raw.get("fat_g")))

    derived_tags = compute_derived_tags(calories, protein_g, carbs_g, fat_g)

    # Basic de-dupe key
    item_id = stable_item_id(restaurant or "unknown_restaurant", name)

    record = {
        "name": name,
        "restaurant": restaurant,
        "cuisine": cuisine,
        "ingredients": ingredients,
        "diet_tags": diet_tags,
        "derived_tags": derived_tags,
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
    }
    embedding_text = build_embedding_text(record)

    return CleanedMenuItem(
        item_id=item_id,
        name=name,
        restaurant=restaurant,
        cuisine=cuisine,
        ingredients=ingredients,
        diet_tags=diet_tags,
        derived_tags=derived_tags,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        embedding_text=embedding_text,
        raw_source=raw,
    )


def preprocess_menu_items(
    raw_items: Iterable[dict[str, Any]],
) -> tuple[list[CleanedMenuItem], dict[str, int]]:
    """
    Cleans an iterable of raw items.
    Returns (clean_items, stats).
    """
    out: list[CleanedMenuItem] = []
    stats = {
        "seen": 0,
        "kept": 0,
        "dropped_missing_name": 0,
        "dropped_duplicate": 0,
    }
    seen_source_ids: set[int] = set()
    seen_item_ids: set[str] = set()

    for raw in raw_items:
        stats["seen"] += 1
        cleaned = clean_one_menu_item(raw)
        if cleaned is None:
            stats["dropped_missing_name"] += 1
            continue
        source_id = cleaned.raw_source.get("spoonacular_id")
        if (
            isinstance(source_id, int)
            and source_id in seen_source_ids
            or cleaned.item_id in seen_item_ids
        ):
            stats["dropped_duplicate"] += 1
            continue
        if isinstance(source_id, int):
            seen_source_ids.add(source_id)
        seen_item_ids.add(cleaned.item_id)
        out.append(cleaned)
        stats["kept"] += 1

    return out, stats
