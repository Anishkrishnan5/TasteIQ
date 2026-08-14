import json
from pathlib import Path

import pytest

from rag.retriever import search_menu

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "retrieval_baseline.json"
BASELINE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", BASELINE["cases"], ids=lambda case: case["query"])
def test_token_overlap_baseline(case):
    results = search_menu(case["query"], case["limit"])

    assert len(results) == case["expected_result_count"]
    assert results[0]["spoonacular_id"] == case["expected_top_spoonacular_id"]
    assert len({result["spoonacular_id"] for result in results}) == len(results)
