from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import Any

from evaluation.metrics import (
    constraint_violations,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank_at_k,
)
from rag.retriever import DEFAULT_DATA_PATH, RETRIEVER_VERSION, load_items, search_menu

BACKEND_ROOT = Path(__file__).parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_JUDGMENTS = Path(__file__).with_name("judgments-v1.json")
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reports" / "evaluation-token-overlap-v2.json"
SearchFunction = Callable[..., list[dict[str, Any]]]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round(value: float) -> float:
    return round(value, 4)


def validate_dataset(dataset: dict[str, Any]) -> None:
    cases = dataset.get("cases", [])
    case_ids = [case.get("id") for case in cases]
    if len(cases) < 30:
        raise ValueError("Evaluation dataset must contain at least 30 cases.")
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Evaluation case IDs must be unique.")

    corpus_ids = {item.get("spoonacular_id") for item in load_items()}
    for case in cases:
        if not str(case.get("query", "")).strip():
            raise ValueError(f"Case {case.get('id')} has an empty query.")
        judgments = {int(item_id): grade for item_id, grade in case.get("judgments", {}).items()}
        missing_ids = judgments.keys() - corpus_ids
        if missing_ids:
            raise ValueError(f"Case {case['id']} references unknown IDs: {sorted(missing_ids)}")
        if case.get("expected_no_results") and judgments:
            raise ValueError(f"No-result case {case['id']} cannot contain relevant judgments.")
        if not case.get("expected_no_results") and not judgments:
            raise ValueError(f"Relevance case {case['id']} requires judgments.")
        if any(not isinstance(grade, int) or not 0 <= grade <= 3 for grade in judgments.values()):
            raise ValueError(f"Case {case['id']} has a grade outside 0..3.")


def evaluate(
    dataset: dict[str, Any],
    search: SearchFunction = search_menu,
    *,
    k: int = 10,
    retriever_version: str = RETRIEVER_VERSION,
) -> dict[str, Any]:
    validate_dataset(dataset)
    case_reports = []
    relevance_reports = []
    no_result_reports = []
    total_results = 0
    total_duplicates = 0
    total_constraint_violations = 0

    for case in dataset["cases"]:
        filters = case.get("filters", {})
        started = perf_counter()
        results = search(case["query"], k, **filters)
        latency_ms = (perf_counter() - started) * 1000
        result_ids = [result["spoonacular_id"] for result in results]
        judgments = {int(item_id): grade for item_id, grade in case["judgments"].items()}
        duplicate_count = len(result_ids) - len(set(result_ids))
        violation_count = constraint_violations(results, filters)
        report = {
            "id": case["id"],
            "query": case["query"],
            "filters": filters,
            "expected_no_results": case.get("expected_no_results", False),
            "result_ids": result_ids,
            "relevance_grades": [judgments.get(item_id, 0) for item_id in result_ids],
            "result_count": len(results),
            "duplicate_count": duplicate_count,
            "constraint_violations": violation_count,
            "latency_ms": round(latency_ms, 3),
        }
        if report["expected_no_results"]:
            report["no_result_correct"] = not results
            no_result_reports.append(report)
        else:
            report.update(
                {
                    "precision_at_5": _round(precision_at_k(result_ids, judgments, 5)),
                    "recall_at_10": _round(recall_at_k(result_ids, judgments, k)),
                    "reciprocal_rank_at_10": _round(reciprocal_rank_at_k(result_ids, judgments, k)),
                    "ndcg_at_10": _round(ndcg_at_k(result_ids, judgments, k)),
                }
            )
            relevance_reports.append(report)
        case_reports.append(report)
        total_results += len(results)
        total_duplicates += duplicate_count
        total_constraint_violations += violation_count

    def mean(metric: str) -> float:
        return _round(statistics.mean(report[metric] for report in relevance_reports))

    summary = {
        "cases": len(case_reports),
        "relevance_cases": len(relevance_reports),
        "no_result_cases": len(no_result_reports),
        "precision_at_5": mean("precision_at_5"),
        "recall_at_10": mean("recall_at_10"),
        "mrr_at_10": mean("reciprocal_rank_at_10"),
        "ndcg_at_10": mean("ndcg_at_10"),
        "constraint_violation_rate": _round(
            total_constraint_violations / total_results if total_results else 0
        ),
        "duplicate_result_rate": _round(total_duplicates / total_results if total_results else 0),
        "no_result_accuracy": _round(
            statistics.mean(report["no_result_correct"] for report in no_result_reports)
        ),
        "empty_result_rate": _round(
            statistics.mean(not report["result_ids"] for report in case_reports)
        ),
        "median_latency_ms": round(
            statistics.median(report["latency_ms"] for report in case_reports), 3
        ),
    }
    minimum_metrics = dataset.get("minimum_metrics", {})
    quality_gate = {
        metric: summary[metric] >= minimum
        if metric not in {"constraint_violation_rate", "duplicate_result_rate"}
        else summary[metric] <= minimum
        for metric, minimum in minimum_metrics.items()
    }
    return {
        "report_version": 1,
        "dataset_version": dataset["dataset_version"],
        "retriever_version": retriever_version,
        "k": k,
        "summary": summary,
        "minimum_metrics": minimum_metrics,
        "quality_gate": quality_gate,
        "cases": case_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a TasteIQ retriever.")
    parser.add_argument("--judgments", type=Path, default=DEFAULT_JUDGMENTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()
    if args.k < 1:
        parser.error("--k must be at least 1")

    judgments_path = args.judgments.resolve()
    dataset = json.loads(judgments_path.read_text(encoding="utf-8"))
    report = evaluate(dataset, k=args.k)
    report["artifacts"] = {
        "judgments": str(judgments_path.relative_to(PROJECT_ROOT)),
        "judgments_sha256": _sha256(judgments_path),
        "catalog": str(DEFAULT_DATA_PATH.relative_to(PROJECT_ROOT)),
        "catalog_sha256": _sha256(DEFAULT_DATA_PATH),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote evaluation report to {args.output}")
    print(json.dumps(report["summary"], sort_keys=True))
    return int(not all(report["quality_gate"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
