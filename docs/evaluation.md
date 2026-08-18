# Retrieval Evaluation

TasteIQ uses a versioned offline judgment set to compare retrieval changes before they reach the API.
Run it from the repository root:

```bash
make eval
```

The command evaluates the active BM25 retriever against
`backend/evaluation/judgments-v1.json` and writes a detailed report under `docs/reports/`. `make check`
also runs the evaluation against minimum quality and safety thresholds.

`make compare` regenerates the controlled BM25-versus-token-overlap comparison, including aggregate
deltas, per-query wins/losses, warm-cache latency, cold index-build time, and incremental index memory.

The optional ML workflow builds a pinned MiniLM index and compares dense and equal-weight reciprocal
rank fusion against the same BM25 baseline:

```bash
make bootstrap-ml
make embeddings
make eval-ml
make compare-ml
```

ML dependencies and generated vectors are separate from `make bootstrap` and `make check`. This keeps
the default development and CI path small while preserving a reproducible semantic experiment.

## MLflow tracking

Run the full champion/challenger workflow locally with:

```bash
make bootstrap-mlops
make embeddings
make experiment
make mlflow-ui
```

`make experiment` creates a parent selection run and BM25, dense, and hybrid child runs. It logs:

- Git revision, catalog hash, judgment hash, dataset version, and embedding-model revision
- Retriever and fusion parameters
- Precision@5, Recall@10, MRR@10, nDCG@10, latency, no-result behavior, and safety metrics
- Query-level wins, ties, losses, aggregate deltas, and the promotion decision
- The complete comparison report as an artifact

The default tracking URI is a local SQLite database. Set `MLFLOW_TRACKING_URI` to use a remote tracking
server. MLflow is not a runtime API dependency and the application continues to work without it.

## Current dataset

The first version contains 34 cases:

- Exact and broad menu-item requests
- Multi-term food requests
- Restaurant requests
- Explicit calorie and protein constraints
- Expected no-result requests
- Misspelling and semantic-recall challenges

Judgments use a four-point scale: 0 is irrelevant, 1 is partially relevant, 2 is relevant, and 3 is
highly relevant. The set was manually reviewed against menu names, restaurant fields, known nutrition,
and candidate pools from token overlap, BM25, and dense retrieval.

## Metrics

- **Precision@5:** proportion of the first five ranks that are judged relevant
- **Recall@10:** proportion of known relevant judgments retrieved in the first ten ranks
- **MRR@10:** reciprocal rank of the first relevant result
- **nDCG@10:** graded ranking quality with more credit for highly relevant early results
- **Constraint-violation rate:** returned results with unknown or violating explicit nutrition fields
- **Duplicate-result rate:** repeated source IDs in result lists
- **No-result accuracy:** expected-empty cases that return no results
- **Empty-result rate:** share of all queries returning nothing

Precision uses a fixed denominator of five. A retriever returning fewer than five relevant results is
therefore penalized for unused result positions.

## Review workflow

When changing judgments:

1. Give every case a stable, unique ID.
2. Keep explicit filters separate from the query text.
3. Verify every judged source ID exists in the active catalog.
4. Review at least the top 20 candidates from both the baseline and proposed retriever to reduce pooling
   bias.
5. Record relevance independently of the ranker's score.
6. Regenerate the report and inspect per-query changes, not only aggregates.
7. Update minimum thresholds only with a documented reason.

## Limitations

The current corpus is a chicken-oriented historical snapshot, so benchmark coverage reflects that
scope. The first judgments have only one reviewer and are pooled from the systems being compared,
which can miss relevant items none of those systems retrieves. The
dataset is appropriate for regression and initial comparisons, but not for broad claims about meal
recommendation quality. Future versions should add independent reviewers, inter-rater agreement,
broader cuisine coverage, adversarial constraints, and deeper pooled judgments.
