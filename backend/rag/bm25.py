from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from rag.retriever import _tokens, load_details, load_items

BM25_VERSION = "bm25-v1-k1.2-b0.0-name3"
K1 = 1.2
B = 0.0
NAME_WEIGHT = 3


@dataclass(frozen=True)
class IndexedDocument:
    item: dict[str, Any]
    term_frequencies: Counter[str]
    length: int


@dataclass(frozen=True)
class BM25Index:
    documents: list[IndexedDocument]
    document_frequencies: Counter[str]
    average_length: float


def _document_tokens(item: dict[str, Any]) -> list[str]:
    metadata = item.get("metadata", {})
    name_tokens = list(_tokens(str(metadata.get("name", ""))))
    body_tokens = list(_tokens(str(item.get("embedding_text", ""))))
    return body_tokens + name_tokens * (NAME_WEIGHT - 1)


@lru_cache(maxsize=4)
def build_index(path: str | None = None) -> BM25Index:
    documents = []
    document_frequencies: Counter[str] = Counter()
    for item in load_items(path):
        tokens = _document_tokens(item)
        frequencies = Counter(tokens)
        documents.append(
            IndexedDocument(item=item, term_frequencies=frequencies, length=len(tokens))
        )
        document_frequencies.update(frequencies.keys())
    average_length = (
        sum(document.length for document in documents) / len(documents) if documents else 0.0
    )
    return BM25Index(documents, document_frequencies, average_length)


def _inverse_document_frequency(document_count: int, document_frequency: int) -> float:
    return math.log(1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5))


def _score(index: BM25Index, document: IndexedDocument, query_terms: set[str]) -> float:
    score = 0.0
    for term in query_terms:
        frequency = document.term_frequencies.get(term, 0)
        if not frequency:
            continue
        inverse_frequency = _inverse_document_frequency(
            len(index.documents), index.document_frequencies[term]
        )
        length_normalization = 1 - B + B * document.length / index.average_length
        score += (
            inverse_frequency * (frequency * (K1 + 1)) / (frequency + K1 * length_normalization)
        )
    return score


def search_menu_bm25(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
) -> list[dict[str, Any]]:
    query_terms = _tokens(query)
    if not query_terms:
        return []

    index = build_index()
    details = load_details()
    ranked = []
    for document in index.documents:
        score = _score(index, document, query_terms)
        if score <= 0:
            continue
        item = document.item
        metadata = dict(item.get("metadata", {}))
        source_id = item.get("spoonacular_id")
        detail = details.get(source_id, {}) if isinstance(source_id, int) else {}
        for key, value in detail.items():
            if value not in (None, "", []):
                metadata[key] = value

        calories = metadata.get("calories")
        protein = metadata.get("protein_g")
        if max_calories is not None and (calories is None or calories > max_calories):
            continue
        if min_protein is not None and (protein is None or protein < min_protein):
            continue
        ranked.append((score, item, metadata))

    ranked.sort(
        key=lambda candidate: (
            -candidate[0],
            candidate[2].get("name", ""),
            candidate[1].get("spoonacular_id", 0),
        )
    )
    results = []
    seen = set()
    for score, item, metadata in ranked:
        source_id = item.get("spoonacular_id")
        if source_id in seen:
            continue
        seen.add(source_id)
        metadata.update(
            {
                "id": item.get("id"),
                "spoonacular_id": source_id,
                "score": round(score, 4),
            }
        )
        results.append(metadata)
        if len(results) == limit:
            break
    return results
