from time import perf_counter

from rag.bm25 import BM25_VERSION, search_menu_bm25
from rag.retriever import catalog_sha256


def recommend(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
    request_id: str = "",
) -> dict:
    started = perf_counter()
    items = search_menu_bm25(query, limit, max_calories, min_protein)
    retrieval_ms = (perf_counter() - started) * 1000
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
                "retrieval_ms": round(retrieval_ms, 3),
                "response_ms": round((perf_counter() - started) * 1000, 3),
            },
            "retriever_version": BM25_VERSION,
            "catalog_sha256": catalog_sha256(),
        },
    }
