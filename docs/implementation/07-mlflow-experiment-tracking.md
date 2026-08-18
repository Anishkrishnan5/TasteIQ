# Phase 3D: MLflow Experiment Tracking

**Status:** Complete

**Date:** 2026-08-17

**Related phase:** Portfolio release — experiment lifecycle

## Outcome

TasteIQ's retrieval benchmark now produces a navigable MLflow experiment in addition to checked-in
JSON reports. A parent run records the promotion decision, while BM25, dense, and hybrid child runs
record their parameters and metrics. The current tracked decision retains corrected BM25 as champion.

## Starting state

The evaluator already produced detailed, reproducible reports, but experiments could only be compared
by reading JSON. There was no experiment UI or run hierarchy, and no single record joined the Git
revision, catalog, judgment set, model revision, parameters, metrics, artifact, and decision.

## Changes made

- Added a pinned, optional MLflow dependency layer that remains separate from application runtime and
  base CI dependencies.
- Added `make experiment` for the full BM25/dense/hybrid comparison and `make mlflow-ui` for inspection.
- Logged a parent champion-selection run and three retriever child runs.
- Logged code, data, judgment, and model lineage as searchable tags.
- Logged retriever parameters, ranking and safety metrics, query wins/ties/losses, aggregate deltas,
  and the explicit retain/promote decision.
- Attached the complete comparison report and generated a portable checked-in experiment receipt.
- Added tests using an in-memory fake tracking adapter so base CI verifies behavior without installing
  or contacting MLflow.

## System-design impact

MLflow belongs only to the offline experiment path:

```text
catalog + judgments + retrievers → evaluator → MLflow runs and comparison artifact
                                                  │
                                                  └→ explicit champion decision
```

The recommendation API does not import MLflow, query the tracking server, or depend on tracking
availability.

## Decisions and reasoning

Experiment Tracking is used now because TasteIQ has several real retriever configurations and a
promotion decision to preserve. Model Registry is deferred because the current champion is a retrieval
pipeline around data and configuration, not a custom-trained model package.

Local SQLite tracking is the default for reproducibility and low operating cost. The same command
accepts `MLFLOW_TRACKING_URI` for a later remote backend. Local tracking state is ignored by Git; the
portable receipt and source reports preserve reviewable evidence.

## Alternatives considered

- Replacing the JSON reports with MLflow was rejected because checked-in reports remain easier to
  review in CI and Git history.
- Adding MLflow to runtime requirements was rejected because inference does not need it.
- Introducing Model Registry merely for a resume keyword was rejected until there is a naturally
  packageable model lifecycle.
- Requiring a hosted tracking server was rejected for the local-first workflow.

## Tradeoffs and consequences

The optional MLOps environment is large and takes longer to install. In return, experiment lineage and
selection evidence are inspectable in a standard UI. Maintaining both JSON and MLflow outputs adds a
small amount of integration code but prevents dependence on a single tool.

## Security, reliability, data, and performance

- No credentials are required for local tracking.
- The tracking command records hashes rather than raw evaluation queries as tags.
- MLflow failures cannot affect online recommendations.
- The command logs artifacts only after evaluation completes.
- Runtime latency and image size are unchanged because MLflow is optional.

## Verification

- The base workflow passes without requiring MLflow.
- Unit tests verify the parent/child hierarchy, champion label, lineage, metrics, and artifact logging.
- A real local SQLite-backed experiment was executed with BM25, dense, and hybrid child runs.
- The resulting run data was queried through the MLflow client to verify run roles and nDCG values.

## Known limitations and risks

- Local MLflow state is not shareable until a remote tracking backend is deployed.
- Run identifiers in the checked-in receipt identify the recorded local execution, not a public server.
- The judgment set remains small and single-reviewer.
- MLflow records the selection process but does not eliminate the need for human judgment review.

## Follow-up work

Use an S3 artifact store and an appropriately secured remote tracking backend during AWS delivery. Add
a README screenshot once the final presentation pass begins. Consider Model Registry only if the
retrieval pipeline is packaged as a deployable model abstraction.

## Affected files

- `backend/evaluation/track_experiment.py`
- `backend/requirements-mlops.txt`
- `backend/tests/test_experiment_tracking.py`
- `Makefile`, `.gitignore`, `README.md`, `docs/evaluation.md`, `docs/reports/`
