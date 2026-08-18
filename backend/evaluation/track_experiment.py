from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from evaluation.compare_hybrid import DEFAULT_OUTPUT, compare_hybrid
from evaluation.run import DEFAULT_JUDGMENTS, PROJECT_ROOT
from rag.bm25 import BM25_VERSION
from rag.dense import DENSE_VERSION, MODEL_ID, MODEL_REVISION
from rag.hybrid import DENSE_CANDIDATES, HYBRID_VERSION, LEXICAL_CANDIDATES, RRF_K
from rag.retriever import DEFAULT_DATA_PATH

DEFAULT_TRACKING_URI = "sqlite:///mlflow.db"
DEFAULT_EXPERIMENT = "tasteiq-retrieval"
DEFAULT_RECEIPT = PROJECT_ROOT / "docs" / "reports" / "mlflow-experiment-receipt.json"
SUMMARY_METRICS = (
    "precision_at_5",
    "recall_at_10",
    "mrr_at_10",
    "ndcg_at_10",
    "constraint_violation_rate",
    "duplicate_result_rate",
    "no_result_accuracy",
    "empty_result_rate",
    "median_latency_ms",
)


class TrackingUnavailableError(RuntimeError):
    """Raised when the optional experiment-tracking dependency is unavailable."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_revision() -> str:
    if revision := os.getenv("GITHUB_SHA"):
        return revision
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _load_mlflow():
    try:
        import mlflow
    except ImportError as exc:
        raise TrackingUnavailableError(
            "MLflow is not installed; run `make bootstrap-mlops`."
        ) from exc
    return mlflow


def _log_retriever_run(
    mlflow: Any,
    *,
    name: str,
    report: dict[str, Any],
    version: str,
    role: str,
    parent_run_id: str,
    shared_tags: dict[str, str],
) -> str:
    with mlflow.start_run(run_name=name, nested=True, parent_run_id=parent_run_id) as run:
        mlflow.log_param("retriever", name)
        mlflow.log_param("retriever_version", version)
        mlflow.log_param("evaluation_k", report["k"])
        if name in {"dense", "hybrid"}:
            mlflow.log_param("embedding_model", MODEL_ID)
            mlflow.log_param("embedding_revision", MODEL_REVISION)
        if name == "hybrid":
            mlflow.log_param("rrf_k", RRF_K)
            mlflow.log_param("lexical_candidates", LEXICAL_CANDIDATES)
            mlflow.log_param("dense_candidates", DENSE_CANDIDATES)
        mlflow.log_metrics({metric: float(report["summary"][metric]) for metric in SUMMARY_METRICS})
        mlflow.set_tags({**shared_tags, "tasteiq.run_role": role})
        return run.info.run_id


def track_comparison(
    report: dict[str, Any],
    report_path: Path,
    *,
    tracking_uri: str = DEFAULT_TRACKING_URI,
    experiment_name: str = DEFAULT_EXPERIMENT,
    judgments_path: Path = DEFAULT_JUDGMENTS,
    catalog_path: Path = DEFAULT_DATA_PATH,
    mlflow_module: Any | None = None,
) -> dict[str, Any]:
    mlflow = mlflow_module or _load_mlflow()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    comparison = report["comparison"]
    decision = comparison["decision"]
    shared_tags = {
        "tasteiq.git_revision": _git_revision(),
        "tasteiq.dataset_version": report["dataset_version"],
        "tasteiq.judgments_sha256": _sha256(judgments_path),
        "tasteiq.catalog_sha256": _sha256(catalog_path),
        "tasteiq.model_revision": MODEL_REVISION,
    }
    run_ids: dict[str, str] = {}
    with mlflow.start_run(run_name=f"champion-selection-{decision}") as parent:
        parent_run_id = parent.info.run_id
        mlflow.log_params(
            {
                "champion_before": BM25_VERSION,
                "candidate": HYBRID_VERSION,
                "decision": decision,
                "judgment_cases": report["bm25"]["summary"]["cases"],
            }
        )
        mlflow.log_metrics(
            {
                "query_wins": float(comparison["query_wins"]),
                "query_ties": float(comparison["query_ties"]),
                "query_losses": float(comparison["query_losses"]),
                **{
                    f"hybrid_delta_{metric}": float(value)
                    for metric, value in comparison["aggregate_deltas"].items()
                },
            }
        )
        mlflow.set_tags(
            {
                **shared_tags,
                "tasteiq.run_role": "champion_selection",
                "tasteiq.decision": decision,
                "tasteiq.champion_after": BM25_VERSION
                if decision == "retain_bm25"
                else HYBRID_VERSION,
            }
        )
        retrievers = {
            "bm25": (report["bm25"], BM25_VERSION, "champion"),
            "dense": (report["dense"], DENSE_VERSION, "challenger"),
            "hybrid": (report["hybrid"], HYBRID_VERSION, "challenger"),
        }
        for name, (retriever_report, version, role) in retrievers.items():
            run_ids[name] = _log_retriever_run(
                mlflow,
                name=name,
                report=retriever_report,
                version=version,
                role=role,
                parent_run_id=parent_run_id,
                shared_tags=shared_tags,
            )
        mlflow.log_artifact(str(report_path), artifact_path="evaluation")
    return {
        "experiment": experiment_name,
        "tracking_uri": tracking_uri,
        "parent_run_id": parent_run_id,
        "retriever_run_ids": run_ids,
        "decision": decision,
        "lineage": shared_tags,
        "metrics": {
            name: {metric: retriever["summary"][metric] for metric in SUMMARY_METRICS}
            for name, retriever in {
                "bm25": report["bm25"],
                "dense": report["dense"],
                "hybrid": report["hybrid"],
            }.items()
        },
        "comparison": comparison,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate and track TasteIQ retrieval experiments."
    )
    parser.add_argument("--judgments", type=Path, default=DEFAULT_JUDGMENTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI),
    )
    parser.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()

    judgments_path = args.judgments.resolve()
    dataset = json.loads(judgments_path.read_text(encoding="utf-8"))
    report = compare_hybrid(dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    result = track_comparison(
        report,
        args.output,
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment,
        judgments_path=judgments_path,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote MLflow experiment receipt to {args.receipt}")
    print(json.dumps(result, sort_keys=True))
    return int(not report["comparison"]["safety_preserved"])


if __name__ == "__main__":
    raise SystemExit(main())
