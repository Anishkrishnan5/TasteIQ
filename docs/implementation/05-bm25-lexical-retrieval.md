# Phase 3B: BM25 Lexical Retrieval

**Status:** Complete  
**Date:** 2026-08-14  
**Related phase:** Phase 3 — Evaluation-first hybrid retrieval

## Outcome

TasteIQ now serves recommendations through a cached BM25 lexical index. A controlled comparison against
`token-overlap-v2` found exact parity on all measured relevance and safety metrics, with approximately
74% lower warm-cache median retrieval latency. The API adopted BM25 based on that evidence and exposes
its full configuration version in every response.

## Starting state

Token overlap recomputed document tokens for every request and did not account for corpus-wide term
frequency. The new evaluation suite made a controlled algorithm comparison possible, but it initially
contained judgments pooled only from token overlap and therefore missed relevant BM25 candidates.

## Changes made

- Added an in-memory BM25 index with document frequency, term frequency, and configurable `k1`, `b`,
  and name weighting.
- Cached index construction for reuse across requests.
- Preserved strict calorie/protein filtering, SQLite enrichment, stable ordering, and deduplication.
- Added a comparison runner with aggregate deltas and per-query wins, ties, losses, and result IDs.
- Added cold index-build time and incremental/peak index-memory measurement.
- Reviewed previously unjudged BM25 candidates and expanded the pooled judgments before deciding.
- Evaluated a small `b`/`k1` parameter grid.
- Selected `bm25-v1-k1.2-b0.0-name3` and connected it to the API.
- Retained token overlap as an explicit baseline rather than deleting the comparison target.
- Added active-BM25 and baseline-token reports plus the combined decision report.
- Added BM25 index, zero-overlap, filtering, deduplication, and comparison tests.
- Added `make compare` and CI comparison verification.

## System-design impact

```text
Request → strict filters → cached BM25 index → ranked candidates → SQLite enrichment → response
                           │
                           └── version: bm25-v1-k1.2-b0.0-name3
```

This remains local lexical retrieval within the FastAPI process. It supplies a faster lexical baseline
for later dense retrieval and Reciprocal Rank Fusion without prematurely extracting a service.

## Decisions and reasoning

The first BM25 configuration (`b=0.75`) appeared worse on seven cases. Candidate review showed that
several losses were direct relevant matches missing from the token-pooled judgments. The pool was
expanded before tuning or adoption, avoiding a decision biased toward the incumbent.

After pooled review, normal length normalization still slightly reduced quality on this short,
repetitive menu corpus. A parameter grid showed that `b=0` preserved every baseline metric and all 34
query-level scores. This valid BM25 configuration disables document-length normalization, which fits
records whose short metadata length should not imply lower relevance.

The candidate was adopted for measured performance rather than a relevance claim. The decision rule
required no quality regression, perfect safety/no-result parity, and either a positive quality delta or
at least a 20% median latency improvement.

## Alternatives considered

- `b=0.75` was rejected because it reduced Precision, Recall, MRR, and nDCG.
- Keeping token overlap was defensible on quality but retained repeat tokenization on every request.
- A custom coordination bonus was deferred until plain BM25 had an established baseline.
- Dense embeddings and fusion remain separate work and must be evaluated against BM25.

## Tradeoffs and consequences

BM25 adds an in-memory index and cold-build step. On the 448-record corpus, the representative run added
about 1.13 MB of traced allocations and built in about 11 ms. Warm-cache median search fell from roughly
1.08 ms to 0.28 ms. These local measurements vary by machine and are not production SLOs.

No measured relevance improvement occurred: all aggregate deltas were zero and all 34 cases tied. The
supported claim is equivalent measured quality with lower local retrieval latency, not improved semantic
recommendation quality.

## Security, reliability, data, and performance

- The index reads only the checked-in catalog and makes no network calls.
- Filtered results retain zero unknown or violating nutrition values.
- Duplicate-result and no-result behavior remain unchanged.
- Deterministic secondary ordering prevents unstable equal-score results.
- Responses include the exact BM25 configuration and catalog SHA-256.
- The index is cached and rebuilt from the immutable catalog per process.

## Verification

| Metric | Token overlap | BM25 | Delta |
|---|---:|---:|---:|
| Precision@5 | 0.7267 | 0.7267 | 0.0000 |
| Recall@10 | 0.9019 | 0.9019 | 0.0000 |
| MRR@10 | 0.9667 | 0.9667 | 0.0000 |
| nDCG@10 | 0.9558 | 0.9558 | 0.0000 |
| Constraint violations | 0 | 0 | 0 |
| Duplicate-result rate | 0 | 0 | 0 |
| No-result accuracy | 1.0000 | 1.0000 | 0.0000 |

All 34 queries tied. The representative comparison measured about 74% lower warm-cache median latency,
an approximately 11 ms cold build, and approximately 1.13 MB of incremental traced index memory.

The complete gate passed with 30 backend tests, Ruff, Pyright, frontend lint/build, Compose validation,
data validation, retrieval snapshots, active evaluation, and algorithm comparison.

## Known limitations and risks

- The evaluation set and corpus remain small, narrow, and single-reviewer.
- `b=0` may not remain optimal as richer ingredient and description fields increase document lengths.
- Index memory uses Python `tracemalloc`, not process RSS.
- Median latency is warm-cache, single-threaded, and in-process.
- The index has no versioned on-disk artifact or atomic reload yet.
- BM25 cannot recover synonyms, conceptual cravings, or misspellings without normalization or semantic
  retrieval.

## Follow-up work

Add local dense embeddings and vector candidates, then use RRF to compare BM25, dense, and hybrid results
on an expanded independently pooled judgment set. BM25 should remain the safe vector-outage fallback.

## Affected files

- `.github/workflows/ci.yml`
- `Makefile`
- `README.md`
- `backend/rag/bm25.py`
- `backend/rag/pipeline.py`
- `backend/evaluation/compare.py`
- `backend/evaluation/run.py`
- `backend/evaluation/judgments-v1.json`
- `backend/tests/test_bm25.py`
- `backend/tests/test_evaluation.py`
- `docs/evaluation.md`
- `docs/reports/evaluation-bm25-v1.json`
- `docs/reports/evaluation-token-overlap-v2.json`
- `docs/reports/retrieval-comparison.json`
