# Phase 3A: Evaluation Foundation

**Status:** Complete  
**Date:** 2026-08-14  
**Related phase:** Phase 3 — Evaluation-first hybrid retrieval

## Outcome

TasteIQ now has a versioned 34-case relevance dataset, independently testable ranking metrics,
per-query reports, artifact hashes, and enforced quality and safety thresholds. Retrieval changes can
now be compared with evidence instead of selected screenshots or anecdotal queries.

## Starting state

Phase 0 preserved six exact behavioral snapshots, but they answered only whether output changed. They
did not determine whether a result was relevant, assign graded judgments, measure recall or ordering,
or reveal aggregate quality changes. Phase 1 corrected known safety issues without a formal relevance
gate for subsequent ranking algorithms.

## Changes made

- Added `judgments-v1`, containing 30 relevance cases and four expected no-result cases.
- Covered item attributes, exact items, restaurants, structured nutrition filters, misspellings,
  semantic challenges, and unsupported-corpus requests.
- Added binary Precision@5, Recall@10, MRR@10, and graded nDCG@10 implementations.
- Added constraint-violation, duplicate-result, no-result accuracy, empty-result, and latency metrics.
- Added per-query result IDs, relevance grades, filters, latency, and safety counts.
- Added dataset validation for case uniqueness, corpus IDs, grade ranges, and no-result consistency.
- Added minimum metric thresholds and made failures block `make check` and CI.
- Added unit tests for metric calculations, unknown-value violations, dataset validation, and the full
  current evaluation.
- Added public evaluation methodology and review guidance.

## System-design impact

The evaluator accepts a search function separately from metric calculation. The next BM25 retriever can
therefore use the identical dataset and metrics, producing directly comparable reports while retaining
the current token-overlap baseline.

## Decisions and reasoning

Relevance uses grades 0–3 so nDCG can distinguish a direct item match from a partial match. Precision
uses a fixed denominator of five to penalize result lists that cannot fill useful positions. Safety
metrics treat unknown constrained nutrition as a violation, matching the API's strict filter policy.

No-result cases are assessed separately from relevance cases. Treating an expected empty query as
perfect precision would inflate ranking quality and obscure corpus coverage.

## Alternatives considered

- Reusing the six regression snapshots was rejected because expected rank identity is not relevance.
- Fully synthetic judgments were rejected because they would not reflect the actual catalog.
- External evaluation libraries were unnecessary for the initial metric set and would add dependency
  weight without improving transparency.

## Tradeoffs and consequences

The first judgments are single-reviewer and partially pooled from the baseline's top 20, which can bias
the set toward lexical retrieval. The corpus itself is chicken-oriented. Metrics are therefore valid for
regression and controlled comparison on this snapshot, not broad market-quality claims.

Thresholds intentionally sit just below the recorded baseline. They detect regressions but do not prove
that a new algorithm is meaningfully better; the BM25 comparison must report metric deltas and per-query
changes.

## Security, reliability, data, and performance

Evaluation is offline, deterministic apart from recorded local latency, and makes no network calls.
Every judged ID is verified against the checked-in catalog. Explicit filter cases produced zero unknown
or violating results, and every evaluated result set contained unique source IDs.

## Verification

The token-overlap-v2 report recorded:

| Metric | Result |
|---|---:|
| Cases | 34 |
| Precision@5 | 0.7267 |
| Recall@10 | 0.9418 |
| MRR@10 | 0.9667 |
| nDCG@10 | 0.9558 |
| Constraint-violation rate | 0.0000 |
| Duplicate-result rate | 0.0000 |
| No-result accuracy | 1.0000 |
| Empty-result rate | 0.1471 |

The complete project gate passed with 25 backend tests, Ruff, Pyright, frontend lint/build, Compose
validation, data validation, retrieval snapshots, and evaluation thresholds.

## Known limitations and risks

- Only one reviewer assigned judgments.
- Pool depth is limited and baseline-dependent.
- The test corpus is narrow and historically sourced.
- No inter-rater agreement is available.
- Latency measures an in-process local call without concurrency.
- Explanations and diversity cannot yet be evaluated because they are not implemented.

## Follow-up work

Implement a proper BM25 retriever behind the same callable boundary, evaluate token overlap and BM25
with identical judgments, publish aggregate and per-query deltas, and adopt BM25 only if it improves or
preserves agreed metrics without safety violations.

## Affected files

- `.github/workflows/ci.yml`
- `Makefile`
- `README.md`
- `backend/evaluation/`
- `backend/tests/test_evaluation.py`
- `docs/evaluation.md`
- `docs/reports/evaluation-token-overlap-v2.json`
- `docs/implementation/README.md`
- `docs/implementation/04-evaluation-foundation.md`
