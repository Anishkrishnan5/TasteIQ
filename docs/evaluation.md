# Retrieval Evaluation

TasteIQ uses a versioned offline judgment set to compare retrieval changes before they reach the API.
Run it from the repository root:

```bash
make eval
```

The command evaluates the active retriever against
`backend/evaluation/judgments-v1.json` and writes a detailed report under `docs/reports/`. `make check`
also runs the evaluation against minimum quality and safety thresholds.

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
and a depth-20 pool from the baseline retriever.

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
scope. The first judgments have only one reviewer and are partially pooled from the token-overlap
baseline, which favors lexical candidates and can miss relevant items neither system retrieves. The
dataset is appropriate for regression and initial comparisons, but not for broad claims about meal
recommendation quality. Future versions should add independent reviewers, inter-rater agreement,
broader cuisine coverage, adversarial constraints, and deeper pooled judgments.
