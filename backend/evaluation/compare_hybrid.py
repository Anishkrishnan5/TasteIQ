from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluation.run import DEFAULT_JUDGMENTS, PROJECT_ROOT, evaluate
from rag.bm25 import BM25_VERSION, search_menu_bm25
from rag.dense import DENSE_VERSION, load_dense_index, search_menu_dense
from rag.hybrid import HYBRID_VERSION, search_menu_hybrid

DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reports" / "retrieval-hybrid-comparison.json"
QUALITY_METRICS = ("precision_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10")
SAFETY_METRICS = ("constraint_violation_rate", "duplicate_result_rate")


def _round(value: float) -> float:
    return round(value, 4)


def compare_hybrid(dataset: dict[str, Any]) -> dict[str, Any]:
    bm25 = evaluate(dataset, search_menu_bm25, retriever_version=BM25_VERSION)
    dense = evaluate(dataset, search_menu_dense, retriever_version=DENSE_VERSION)
    hybrid = evaluate(dataset, search_menu_hybrid, retriever_version=HYBRID_VERSION)
    deltas = {
        metric: _round(hybrid["summary"][metric] - bm25["summary"][metric])
        for metric in (*QUALITY_METRICS, *SAFETY_METRICS, "no_result_accuracy", "median_latency_ms")
    }
    quality_not_worse = all(deltas[metric] >= 0 for metric in QUALITY_METRICS)
    safety_preserved = all(hybrid["summary"][metric] == 0 for metric in SAFETY_METRICS)
    no_result_preserved = (
        hybrid["summary"]["no_result_accuracy"] >= bm25["summary"]["no_result_accuracy"]
    )
    bm25_cases = {case["id"]: case for case in bm25["cases"]}
    hybrid_cases = {case["id"]: case for case in hybrid["cases"]}
    per_query = []
    wins = ties = losses = 0
    for case_id, baseline in bm25_cases.items():
        candidate = hybrid_cases[case_id]
        metric = "no_result_correct" if baseline["expected_no_results"] else "ndcg_at_10"
        baseline_score = float(baseline[metric])
        candidate_score = float(candidate[metric])
        delta = _round(candidate_score - baseline_score)
        wins += delta > 0
        ties += delta == 0
        losses += delta < 0
        per_query.append(
            {
                "id": case_id,
                "query": baseline["query"],
                "metric": metric,
                "bm25": baseline_score,
                "hybrid": candidate_score,
                "delta": delta,
                "bm25_result_ids": baseline["result_ids"],
                "hybrid_result_ids": candidate["result_ids"],
            }
        )
    return {
        "report_version": 1,
        "dataset_version": dataset["dataset_version"],
        "index_manifest": load_dense_index().manifest,
        "bm25": bm25,
        "dense": dense,
        "hybrid": hybrid,
        "comparison": {
            "aggregate_deltas": deltas,
            "query_wins": wins,
            "query_ties": ties,
            "query_losses": losses,
            "quality_not_worse": quality_not_worse,
            "safety_preserved": safety_preserved,
            "no_result_preserved": no_result_preserved,
            "adopt_hybrid": quality_not_worse and safety_preserved and no_result_preserved,
            "decision": "retain_bm25" if not quality_not_worse else "adopt_hybrid",
        },
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare BM25, dense, and RRF hybrid retrieval.")
    parser.add_argument("--judgments", type=Path, default=DEFAULT_JUDGMENTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    dataset = json.loads(args.judgments.read_text(encoding="utf-8"))
    report = compare_hybrid(dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote hybrid comparison to {args.output}")
    print(json.dumps(report["comparison"], sort_keys=True))
    return int(not report["comparison"]["safety_preserved"])


if __name__ == "__main__":
    raise SystemExit(main())
