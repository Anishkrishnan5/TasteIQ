import copy
import json

import pytest

from evaluation.compare import compare
from evaluation.metrics import (
    constraint_violations,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank_at_k,
)
from evaluation.run import DEFAULT_JUDGMENTS, evaluate, validate_dataset
from rag.bm25 import search_menu_bm25


def load_dataset():
    return json.loads(DEFAULT_JUDGMENTS.read_text(encoding="utf-8"))


def test_ranking_metrics_use_binary_and_graded_relevance():
    results = [30, 10, 20, 40]
    judgments = {10: 3, 20: 2, 50: 1}

    assert precision_at_k(results, judgments, 4) == 0.5
    assert recall_at_k(results, judgments, 4) == pytest.approx(2 / 3)
    assert reciprocal_rank_at_k(results, judgments, 4) == 0.5
    assert ndcg_at_k(results, judgments, 4) == pytest.approx(0.6299, abs=0.0001)


def test_constraint_metric_treats_unknown_as_violation():
    results = [
        {"calories": 400, "protein_g": 30},
        {"calories": None, "protein_g": 30},
        {"calories": 700, "protein_g": 30},
        {"calories": 400, "protein_g": None},
    ]

    assert constraint_violations(results, {"max_calories": 500, "min_protein": 20}) == 3


def test_judgment_dataset_is_valid_and_versioned():
    dataset = load_dataset()

    validate_dataset(dataset)
    assert dataset["dataset_version"] == "judgments-v1"
    assert len(dataset["cases"]) == 34


def test_dataset_validation_rejects_duplicate_case_ids():
    dataset = copy.deepcopy(load_dataset())
    dataset["cases"][1]["id"] = dataset["cases"][0]["id"]

    with pytest.raises(ValueError, match="unique"):
        validate_dataset(dataset)


def test_current_retriever_evaluation_has_zero_safety_regressions():
    report = evaluate(load_dataset(), search_menu_bm25)

    assert report["summary"]["cases"] == 34
    assert report["summary"]["constraint_violation_rate"] == 0
    assert report["summary"]["duplicate_result_rate"] == 0
    assert report["summary"]["no_result_accuracy"] == 1
    assert report["summary"]["precision_at_5"] > 0
    assert report["summary"]["recall_at_10"] > 0
    assert report["summary"]["mrr_at_10"] > 0
    assert report["summary"]["ndcg_at_10"] > 0
    assert all(report["quality_gate"].values())


def test_bm25_comparison_preserves_quality_and_safety():
    report = compare(load_dataset())

    assert report["comparison"]["quality_not_worse"]
    assert report["comparison"]["safety_preserved"]
    assert report["comparison"]["no_result_preserved"]
    assert report["comparison"]["query_losses"] == 0
