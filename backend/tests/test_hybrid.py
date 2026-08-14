import rag.hybrid as hybrid
from rag.dense import DenseUnavailableError
from rag.hybrid import reciprocal_rank_fusion, search_hybrid_with_diagnostics


def item(source_id: int, name: str) -> dict:
    return {"spoonacular_id": source_id, "name": name, "score": 1.0}


def test_rrf_rewards_candidates_returned_by_both_retrievers():
    lexical = [item(1, "one"), item(2, "two")]
    dense = [item(2, "two"), item(3, "three")]

    fused = reciprocal_rank_fusion([lexical, dense])

    assert [result["spoonacular_id"] for result in fused] == [2, 1, 3]
    assert fused[0]["source_ranks"] == [2, 1]


def test_hybrid_falls_back_to_bm25_when_dense_is_unavailable(monkeypatch):
    lexical = [item(1, "one"), item(2, "two")]
    monkeypatch.setattr(hybrid, "search_menu_bm25", lambda *args, **kwargs: lexical)

    def unavailable(*args, **kwargs):
        raise DenseUnavailableError("model missing")

    monkeypatch.setattr(hybrid, "search_menu_dense", unavailable)

    response = search_hybrid_with_diagnostics("chicken", limit=1)

    assert response.results == lexical[:1]
    assert response.mode == "bm25_fallback"
    assert response.degraded_reason == "model missing"


def test_hybrid_does_not_use_dense_when_lexical_has_no_grounded_candidates(monkeypatch):
    monkeypatch.setattr(hybrid, "search_menu_bm25", lambda *args, **kwargs: [])

    def should_not_run(*args, **kwargs):
        raise AssertionError("dense retrieval should not run for out-of-corpus queries")

    monkeypatch.setattr(hybrid, "search_menu_dense", should_not_run)

    response = search_hybrid_with_diagnostics("shrimp")

    assert response.results == []
    assert response.mode == "bm25_no_candidates"
