from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.bm25 import BM25_VERSION, search_menu_bm25
from rag.dense import DENSE_VERSION, DenseUnavailableError, search_menu_dense

RRF_K = 60
LEXICAL_CANDIDATES = 50
DENSE_CANDIDATES = 50
HYBRID_VERSION = (
    f"hybrid-rrf-v1-k{RRF_K}-l{LEXICAL_CANDIDATES}-d{DENSE_CANDIDATES}"
    f"+{BM25_VERSION}+{DENSE_VERSION}"
)


@dataclass(frozen=True)
class HybridSearchResult:
    results: list[dict[str, Any]]
    retriever_version: str
    mode: str
    degraded_reason: str | None = None


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict[str, Any]]], *, rrf_k: int = RRF_K
) -> list[dict[str, Any]]:
    scores: dict[int, float] = {}
    documents: dict[int, dict[str, Any]] = {}
    source_ranks: dict[int, list[int | None]] = {}
    for source_index, ranked_list in enumerate(ranked_lists):
        for rank, document in enumerate(ranked_list, start=1):
            source_id = document.get("spoonacular_id")
            if not isinstance(source_id, int):
                continue
            scores[source_id] = scores.get(source_id, 0.0) + 1 / (rrf_k + rank)
            documents.setdefault(source_id, document)
            source_ranks.setdefault(source_id, [None] * len(ranked_lists))[source_index] = rank

    ordered_ids = sorted(
        scores,
        key=lambda source_id: (
            -scores[source_id],
            str(documents[source_id].get("name", "")),
            source_id,
        ),
    )
    fused = []
    for source_id in ordered_ids:
        document = dict(documents[source_id])
        document["score"] = round(scores[source_id], 6)
        document["source_ranks"] = source_ranks[source_id]
        fused.append(document)
    return fused


def search_hybrid_with_diagnostics(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
) -> HybridSearchResult:
    lexical = search_menu_bm25(
        query,
        LEXICAL_CANDIDATES,
        max_calories=max_calories,
        min_protein=min_protein,
    )
    if not lexical:
        return HybridSearchResult(
            results=[],
            retriever_version=BM25_VERSION,
            mode="bm25_no_candidates",
        )
    try:
        dense = search_menu_dense(
            query,
            DENSE_CANDIDATES,
            max_calories=max_calories,
            min_protein=min_protein,
        )
    except DenseUnavailableError as exc:
        return HybridSearchResult(
            results=lexical[:limit],
            retriever_version=BM25_VERSION,
            mode="bm25_fallback",
            degraded_reason=str(exc),
        )
    fused = reciprocal_rank_fusion([lexical, dense])
    return HybridSearchResult(
        results=fused[:limit],
        retriever_version=HYBRID_VERSION,
        mode="hybrid",
    )


def search_menu_hybrid(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
) -> list[dict[str, Any]]:
    return search_hybrid_with_diagnostics(query, limit, max_calories, min_protein).results
