from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from rag.retriever import DEFAULT_DATA_PATH, catalog_sha256, load_details, load_items

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "ea78891063587eb050ed4166b20062eaf978037c"
DENSE_VERSION = f"minilm-l6-v2@{MODEL_REVISION[:8]}"
DEFAULT_INDEX_PATH = DEFAULT_DATA_PATH.with_name("vector_index.npz")
DEFAULT_MANIFEST_PATH = DEFAULT_DATA_PATH.with_name("vector_index.manifest.json")


class DenseUnavailableError(RuntimeError):
    """Raised when the optional dense model or a valid index is unavailable."""


@dataclass(frozen=True)
class DenseIndex:
    source_ids: Any
    vectors: Any
    manifest: dict[str, Any]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _document_text(item: dict[str, Any]) -> str:
    metadata = item.get("metadata", {})
    parts = [
        str(metadata.get("name", "")),
        f"Restaurant: {metadata.get('restaurant', '')}" if metadata.get("restaurant") else "",
        f"Cuisine: {metadata.get('cuisine', '')}" if metadata.get("cuisine") else "",
    ]
    ingredients = metadata.get("ingredients", [])
    if ingredients:
        parts.append(f"Ingredients: {', '.join(ingredients)}")
    tags = metadata.get("diet_tags", []) + metadata.get("derived_tags", [])
    if tags:
        parts.append(f"Tags: {', '.join(tags)}")
    return ". ".join(part for part in parts if part)


@lru_cache(maxsize=2)
def _load_model(local_files_only: bool = True):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise DenseUnavailableError(
            "Dense retrieval dependencies are not installed; run `make bootstrap-ml`."
        ) from exc
    try:
        return SentenceTransformer(
            MODEL_ID,
            revision=MODEL_REVISION,
            local_files_only=local_files_only,
            trust_remote_code=False,
        )
    except Exception as exc:
        raise DenseUnavailableError(
            "The pinned embedding model is unavailable locally; run `make embeddings`."
        ) from exc


def build_dense_index(
    index_path: Path = DEFAULT_INDEX_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    try:
        import numpy as np
    except ImportError as exc:
        raise DenseUnavailableError("NumPy is required to build the dense index.") from exc

    items = load_items()
    model = _load_model(local_files_only=False)
    texts = [_document_text(item) for item in items]
    vectors = model.encode(
        texts,
        batch_size=64,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype("float32")
    source_ids = np.asarray([item["spoonacular_id"] for item in items], dtype="int64")

    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_index = index_path.with_suffix(".npz.tmp")
    with temporary_index.open("wb") as handle:
        np.savez_compressed(handle, source_ids=source_ids, vectors=vectors)
    temporary_index.replace(index_path)

    manifest = {
        "manifest_version": 1,
        "dense_version": DENSE_VERSION,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "catalog_path": str(DEFAULT_DATA_PATH.name),
        "catalog_sha256": catalog_sha256(),
        "records": len(items),
        "dimensions": int(vectors.shape[1]),
        "normalized": True,
        "index_sha256": _sha256(index_path),
    }
    temporary_manifest = manifest_path.with_suffix(".json.tmp")
    temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(manifest_path)
    load_dense_index.cache_clear()
    return manifest


@lru_cache(maxsize=1)
def load_dense_index(
    index_path: Path = DEFAULT_INDEX_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> DenseIndex:
    if not index_path.exists() or not manifest_path.exists():
        raise DenseUnavailableError("Dense index artifacts are missing; run `make embeddings`.")
    try:
        import numpy as np
    except ImportError as exc:
        raise DenseUnavailableError("NumPy is required to query the dense index.") from exc

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("catalog_sha256") != catalog_sha256():
        raise DenseUnavailableError(
            "Dense index catalog version does not match the runtime catalog."
        )
    if manifest.get("model_revision") != MODEL_REVISION:
        raise DenseUnavailableError(
            "Dense index model revision does not match the configured model."
        )
    if manifest.get("index_sha256") != _sha256(index_path):
        raise DenseUnavailableError("Dense index checksum validation failed.")

    with np.load(index_path, allow_pickle=False) as artifact:
        source_ids = artifact["source_ids"].copy()
        vectors = artifact["vectors"].copy()
    if vectors.ndim != 2 or len(source_ids) != len(vectors):
        raise DenseUnavailableError("Dense index arrays have inconsistent shapes.")
    if len(source_ids) != manifest.get("records") or vectors.shape[1] != manifest.get("dimensions"):
        raise DenseUnavailableError("Dense index shape does not match its manifest.")
    return DenseIndex(source_ids=source_ids, vectors=vectors, manifest=manifest)


def search_menu_dense(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    index = load_dense_index()
    model = _load_model(local_files_only=True)
    query_vector = model.encode(
        [query], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
    )[0]
    similarities = index.vectors @ query_vector
    ranked_positions = similarities.argsort()[::-1]
    items_by_source_id = {item["spoonacular_id"]: item for item in load_items()}
    details = load_details()
    results = []
    seen = set()
    for position in ranked_positions:
        source_id = int(index.source_ids[position])
        if source_id in seen:
            continue
        item = items_by_source_id.get(source_id)
        if item is None:
            continue
        metadata = dict(item.get("metadata", {}))
        for key, value in details.get(source_id, {}).items():
            if value not in (None, "", []):
                metadata[key] = value
        calories = metadata.get("calories")
        protein = metadata.get("protein_g")
        if max_calories is not None and (calories is None or calories > max_calories):
            continue
        if min_protein is not None and (protein is None or protein < min_protein):
            continue
        seen.add(source_id)
        metadata.update(
            {
                "id": item.get("id"),
                "spoonacular_id": source_id,
                "score": round(float(similarities[position]), 4),
            }
        )
        results.append(metadata)
        if len(results) == limit:
            break
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or inspect TasteIQ dense index artifacts.")
    parser.add_argument("command", choices=("build", "inspect"))
    args = parser.parse_args()
    manifest = build_dense_index() if args.command == "build" else load_dense_index().manifest
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
