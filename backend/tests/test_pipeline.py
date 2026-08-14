import rag.pipeline as pipeline
from rag.bm25 import BM25_VERSION
from rag.hybrid import HybridSearchResult


def test_hybrid_mode_reports_bm25_degradation(monkeypatch):
    monkeypatch.setattr(pipeline.settings, "retrieval_mode", "hybrid")
    monkeypatch.setattr(
        pipeline,
        "search_hybrid_with_diagnostics",
        lambda *args, **kwargs: HybridSearchResult(
            results=[],
            retriever_version=BM25_VERSION,
            mode="bm25_fallback",
            degraded_reason="model missing",
        ),
    )

    response = pipeline.recommend("chicken", request_id="test")

    assert response["meta"]["retrieval_mode"] == "bm25_fallback"
    assert response["meta"]["degraded"] is True
    assert response["meta"]["degraded_reason"] == "model missing"
