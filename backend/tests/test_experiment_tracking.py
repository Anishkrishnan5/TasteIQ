from __future__ import annotations

import builtins
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from evaluation.track_experiment import TrackingUnavailableError, track_comparison


class FakeRun:
    def __init__(self, run_id: str) -> None:
        self.info = SimpleNamespace(run_id=run_id)

    def __enter__(self):
        return self

    def __exit__(self, *_args: Any) -> None:
        return None


class FakeMlflow:
    def __init__(self) -> None:
        self.runs: list[dict[str, Any]] = []
        self.params: list[dict[str, Any]] = []
        self.metrics: list[dict[str, float]] = []
        self.tags: list[dict[str, str]] = []
        self.artifacts: list[tuple[str, str]] = []

    def set_tracking_uri(self, tracking_uri: str) -> None:
        self.tracking_uri = tracking_uri

    def set_experiment(self, experiment_name: str) -> None:
        self.experiment_name = experiment_name

    def start_run(self, **kwargs: Any) -> FakeRun:
        run_id = f"run-{len(self.runs) + 1}"
        self.runs.append({"run_id": run_id, **kwargs})
        return FakeRun(run_id)

    def log_param(self, key: str, value: Any) -> None:
        self.params.append({key: value})

    def log_params(self, params: dict[str, Any]) -> None:
        self.params.append(params)

    def log_metrics(self, metrics: dict[str, float]) -> None:
        self.metrics.append(metrics)

    def set_tags(self, tags: dict[str, str]) -> None:
        self.tags.append(tags)

    def log_artifact(self, path: str, artifact_path: str) -> None:
        self.artifacts.append((path, artifact_path))


def _report() -> dict[str, Any]:
    summary = {
        "cases": 34,
        "precision_at_5": 0.7,
        "recall_at_10": 0.8,
        "mrr_at_10": 0.9,
        "ndcg_at_10": 0.85,
        "constraint_violation_rate": 0,
        "duplicate_result_rate": 0,
        "no_result_accuracy": 1,
        "empty_result_rate": 0.1,
        "median_latency_ms": 1.2,
    }
    retriever = {"k": 10, "summary": summary}
    return {
        "dataset_version": "judgments-v1",
        "bm25": retriever,
        "dense": retriever,
        "hybrid": retriever,
        "comparison": {
            "decision": "retain_bm25",
            "query_wins": 0,
            "query_ties": 21,
            "query_losses": 13,
            "aggregate_deltas": {"ndcg_at_10": -0.05, "median_latency_ms": 4.0},
        },
    }


def test_tracking_logs_parent_children_lineage_metrics_and_artifact(tmp_path: Path) -> None:
    fake = FakeMlflow()
    report_path = tmp_path / "report.json"
    judgments_path = tmp_path / "judgments.json"
    catalog_path = tmp_path / "catalog.jsonl"
    report_path.write_text("{}", encoding="utf-8")
    judgments_path.write_text("{}", encoding="utf-8")
    catalog_path.write_text("{}", encoding="utf-8")

    result = track_comparison(
        _report(),
        report_path,
        tracking_uri="sqlite:///test.db",
        experiment_name="test-experiment",
        judgments_path=judgments_path,
        catalog_path=catalog_path,
        mlflow_module=fake,
    )

    assert result["decision"] == "retain_bm25"
    assert result["parent_run_id"] == "run-1"
    assert set(result["retriever_run_ids"]) == {"bm25", "dense", "hybrid"}
    assert fake.tracking_uri == "sqlite:///test.db"
    assert fake.experiment_name == "test-experiment"
    assert len(fake.runs) == 4
    assert all(run["parent_run_id"] == "run-1" for run in fake.runs[1:])
    assert any(metrics.get("query_losses") == 13 for metrics in fake.metrics)
    assert any(tags.get("tasteiq.catalog_sha256") for tags in fake.tags)
    assert any(tags.get("tasteiq.run_role") == "champion" for tags in fake.tags)
    assert fake.artifacts == [(str(report_path), "evaluation")]


def test_tracking_dependency_has_an_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import evaluation.track_experiment as tracking

    original_import = builtins.__import__

    def reject_mlflow(name: str, *args: Any, **kwargs: Any):
        if name == "mlflow":
            raise ImportError
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_mlflow)
    with pytest.raises(TrackingUnavailableError, match="bootstrap-mlops"):
        tracking._load_mlflow()
