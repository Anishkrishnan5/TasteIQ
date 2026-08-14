from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

from rag.retriever import DEFAULT_DATA_PATH, load_details, load_items, search_menu

BACKEND_ROOT = Path(__file__).parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_FIXTURE = BACKEND_ROOT / "tests" / "fixtures" / "retrieval_baseline.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reports" / "retrieval-baseline.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def measure_case(case: dict[str, Any], repetitions: int) -> dict[str, Any]:
    results = search_menu(case["query"], case["limit"])
    durations = []
    for _ in range(repetitions):
        started = perf_counter()
        search_menu(case["query"], case["limit"])
        durations.append((perf_counter() - started) * 1000)

    actual_top_id = results[0].get("spoonacular_id") if results else None
    return {
        "query": case["query"],
        "limit": case["limit"],
        "result_count": len(results),
        "top_spoonacular_id": actual_top_id,
        "expected_top_spoonacular_id": case["expected_top_spoonacular_id"],
        "top_result_matches_snapshot": actual_top_id == case["expected_top_spoonacular_id"],
        "known_defect": case.get("known_defect"),
        "latency_ms": {
            "median": round(statistics.median(durations), 3),
            "p95": round(percentile(durations, 0.95), 3),
            "max": round(max(durations), 3),
        },
    }


def build_baseline(fixture_path: Path, repetitions: int) -> dict[str, Any]:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    load_items()
    load_details()
    cases = [measure_case(case, repetitions) for case in fixture["cases"]]
    all_snapshot_matches = all(case["top_result_matches_snapshot"] for case in cases)
    return {
        "report_version": 1,
        "baseline": "deterministic token overlap with SQLite enrichment",
        "fixture_version": fixture["version"],
        "methodology": {
            "warm_cache": True,
            "repetitions_per_query": repetitions,
            "concurrency": 1,
            "timed_scope": "search_menu call only",
            "latency_warning": "Local development measurement; not a production SLO claim.",
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or "unknown",
        },
        "artifacts": {
            "fixture": str(fixture_path.relative_to(PROJECT_ROOT)),
            "fixture_sha256": _sha256(fixture_path),
            "catalog": str(DEFAULT_DATA_PATH.relative_to(BACKEND_ROOT)),
            "catalog_sha256": _sha256(DEFAULT_DATA_PATH),
            "catalog_records": len(load_items()),
        },
        "summary": {
            "cases": len(cases),
            "snapshot_top_result_matches": sum(
                case["top_result_matches_snapshot"] for case in cases
            ),
            "all_snapshot_matches": all_snapshot_matches,
            "median_query_p95_ms": round(
                statistics.median(case["latency_ms"]["p95"] for case in cases), 3
            ),
        },
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure the current TasteIQ retrieval baseline.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repetitions", type=int, default=100)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be at least 1")

    report = build_baseline(args.fixture.resolve(), args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote retrieval baseline to {args.output}")
    print(json.dumps(report["summary"], sort_keys=True))
    return int(not report["summary"]["all_snapshot_matches"])


if __name__ == "__main__":
    sys.exit(main())
