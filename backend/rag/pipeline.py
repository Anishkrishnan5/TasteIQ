from time import perf_counter

from core.config import settings
from rag.bm25 import BM25_VERSION, build_index, normalize_query, search_menu_bm25
from rag.hybrid import search_hybrid_with_diagnostics
from rag.retriever import catalog_sha256


def recommend(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
    request_id: str = "",
) -> dict:
    started = perf_counter()
    normalized_query, corrections = normalize_query(query, build_index())
    query_understanding_ms = (perf_counter() - started) * 1000
    retrieval_started = perf_counter()
    if settings.retrieval_mode == "hybrid":
        retrieval = search_hybrid_with_diagnostics(query, limit, max_calories, min_protein)
        items = retrieval.results
        retriever_version = retrieval.retriever_version
        retrieval_mode = retrieval.mode
        degraded_reason = retrieval.degraded_reason
    else:
        items = search_menu_bm25(query, limit, max_calories, min_protein)
        retriever_version = BM25_VERSION
        retrieval_mode = "bm25"
        degraded_reason = None
    retrieval_ms = (perf_counter() - retrieval_started) * 1000
    if items:
        names = ", ".join(item["name"].title() for item in items[:3])
        message = f"I found {len(items)} grounded matches. Top picks: {names}."
    else:
        message = "No menu items matched those constraints. Try a broader food or cuisine."
    return {
        "schema_version": "1.0",
        "query": query,
        "message": message,
        "results": items,
        "meta": {
            "request_id": request_id,
            "result_count": len(items),
            "filters": {
                "max_calories": max_calories,
                "min_protein": min_protein,
                "unknown_nutrition_policy": "exclude",
            },
            "timings_ms": {
                "query_understanding_ms": round(query_understanding_ms, 3),
                "retrieval_ms": round(retrieval_ms, 3),
                "response_ms": round((perf_counter() - started) * 1000, 3),
            },
            "retriever_version": retriever_version,
            "catalog_sha256": catalog_sha256(),
            "normalized_query": normalized_query,
            "query_corrections": corrections,
            "retrieval_mode": retrieval_mode,
            "degraded": degraded_reason is not None,
            "degraded_reason": degraded_reason,
        },
    }
