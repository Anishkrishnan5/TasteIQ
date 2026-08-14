from rag.bm25 import BM25_VERSION, build_index, search_menu_bm25


def test_bm25_index_covers_the_deduplicated_catalog():
    index = build_index()

    assert BM25_VERSION == "bm25-v1-k1.2-b0.0-name3"
    assert len(index.documents) == 448
    assert index.average_length > 0
    assert index.document_frequencies["chicken"] > 0


def test_bm25_returns_no_zero_overlap_fallbacks():
    assert search_menu_bm25("zzzxxyy") == []


def test_bm25_preserves_strict_nutrition_filters():
    results = search_menu_bm25("chicken", 20, max_calories=500, min_protein=20)

    assert results
    assert all(
        result["calories"] is not None
        and result["calories"] <= 500
        and result["protein_g"] is not None
        and result["protein_g"] >= 20
        for result in results
    )


def test_bm25_results_are_deduplicated():
    results = search_menu_bm25("chicken", 20)
    source_ids = [result["spoonacular_id"] for result in results]

    assert len(source_ids) == len(set(source_ids))
