from __future__ import annotations

import argparse
import json
import tracemalloc
from pathlib import Path
from time import perf_counter
from typing import Any

from evaluation.run import DEFAULT_JUDGMENTS, PROJECT_ROOT, evaluate
from rag.bm25 import BM25_VERSION, build_index, search_menu_bm25
from rag.retriever import RETRIEVER_VERSION, search_menu

DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reports" / "retrieval-comparison.json"
QUALITY_METRICS = ("precision_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10")
SAFETY_METRICS = ("constraint_violation_rate", "duplicate_result_rate")


def _round(value: float) -> float:
    return round(value, 4)


def compare(dataset: dict[str, Any]) -> dict[str, Any]:
    baseline = evaluate(dataset, search_menu, retriever_version=RETRIEVER_VERSION)
    build_index.cache_clear()
    tracemalloc.start()
    memory_before, _ = tracemalloc.get_traced_memory()
    build_started = perf_counter()
    build_index()
    index_build_ms = (perf_counter() - build_started) * 1000
    memory_after, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    candidate = evaluate(dataset, search_menu_bm25, retriever_version=BM25_VERSION)
    baseline_cases = {case["id"]: case for case in baseline["cases"]}
    candidate_cases = {case["id"]: case for case in candidate["cases"]}
    per_query = []
    wins = ties = losses = 0
    for case_id, baseline_case in baseline_cases.items():
        candidate_case = candidate_cases[case_id]
        if baseline_case["expected_no_results"]:
            baseline_score = float(baseline_case["no_result_correct"])
            candidate_score = float(candidate_case["no_result_correct"])
            comparison_metric = "no_result_correct"
        else:
            baseline_score = baseline_case["ndcg_at_10"]
            candidate_score = candidate_case["ndcg_at_10"]
            comparison_metric = "ndcg_at_10"
        delta = _round(candidate_score - baseline_score)
        if delta > 0:
            wins += 1
        elif delta < 0:
            losses += 1
        else:
            ties += 1
        per_query.append(
            {
                "id": case_id,
                "query": baseline_case["query"],
                "metric": comparison_metric,
                "baseline": baseline_score,
                "candidate": candidate_score,
                "delta": delta,
                "baseline_result_ids": baseline_case["result_ids"],
                "candidate_result_ids": candidate_case["result_ids"],
            }
        )

    deltas = {
        metric: _round(candidate["summary"][metric] - baseline["summary"][metric])
        for metric in (*QUALITY_METRICS, *SAFETY_METRICS, "no_result_accuracy", "median_latency_ms")
    }
    quality_not_worse = all(deltas[metric] >= 0 for metric in QUALITY_METRICS)
    safety_preserved = all(candidate["summary"][metric] == 0 for metric in SAFETY_METRICS)
    no_result_preserved = (
        candidate["summary"]["no_result_accuracy"] >= baseline["summary"]["no_result_accuracy"]
    )
    meaningful_quality_gain = any(deltas[metric] > 0 for metric in QUALITY_METRICS)
    performance_gain_percent = _round(
        (baseline["summary"]["median_latency_ms"] - candidate["summary"]["median_latency_ms"])
        / baseline["summary"]["median_latency_ms"]
        * 100
    )
    meaningful_performance_gain = performance_gain_percent >= 20
    adopt_candidate = (
        quality_not_worse
        and safety_preserved
        and no_result_preserved
        and (meaningful_quality_gain or meaningful_performance_gain)
    )

    return {
        "report_version": 1,
        "dataset_version": dataset["dataset_version"],
        "baseline": baseline,
        "candidate": candidate,
        "comparison": {
            "aggregate_deltas": deltas,
            "query_wins": wins,
            "query_ties": ties,
            "query_losses": losses,
            "quality_not_worse": quality_not_worse,
            "safety_preserved": safety_preserved,
            "no_result_preserved": no_result_preserved,
            "meaningful_quality_gain": meaningful_quality_gain,
            "performance_gain_percent": performance_gain_percent,
            "meaningful_performance_gain": meaningful_performance_gain,
            "adopt_candidate": adopt_candidate,
            "candidate_index": {
                "cold_build_ms": round(index_build_ms, 3),
                "incremental_memory_bytes": memory_after - memory_before,
                "peak_memory_bytes": peak_memory - memory_before,
                "measurement": "tracemalloc allocations while building after catalog warm-up",
            },
        },
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare token overlap with BM25.")
    parser.add_argument("--judgments", type=Path, default=DEFAULT_JUDGMENTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    dataset = json.loads(args.judgments.read_text(encoding="utf-8"))
    report = compare(dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote retrieval comparison to {args.output}")
    print(json.dumps(report["comparison"], sort_keys=True))
    return int(not report["comparison"]["safety_preserved"])


if __name__ == "__main__":
    raise SystemExit(main())
