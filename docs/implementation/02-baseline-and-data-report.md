# Phase 0C: Baseline and Data Report

**Status:** Complete  
**Date:** 2026-08-14  
**Related phase:** Phase 0 — Protect the baseline

## Outcome

TasteIQ now measures the integrity and coverage of its checked-in data, preserves representative
token-overlap results as regression fixtures, and records a reproducible warm-cache latency baseline.
The combined quality gate executes these tools on every local `make check` and in CI.

## Starting state

The repository described duplicate records, low metadata coverage, and a zero-overlap ranking defect,
but those claims depended on manual inspection. Retrieval behavior had only broad API assertions, and
there was no recorded corpus hash, query snapshot, measurement environment, or latency methodology.

## Changes made

- Added a standard-library catalog and SQLite inspection tool.
- Added tracked JSON reports for data quality and retrieval baseline results.
- Added SHA-256 identities for the catalog, database, and baseline fixture.
- Added six representative retrieval cases with expected top results and result counts.
- Explicitly recorded the known zero-overlap nutrition-bonus defect.
- Added warm-cache median, p95, and maximum latency measurement per query.
- Added eight tests covering current data integrity and deterministic retrieval snapshots.
- Added report verification to `make check` and GitHub Actions.
- Documented `make reports` as the command for regenerating published measurements.

## System-design impact

This phase establishes the evidence layer against which Phase 1 correctness changes and later BM25 or
hybrid retrieval changes can be compared. It intentionally does not change ranking behavior or rewrite
the dataset.

## Decisions and reasoning

Reports are JSON so both humans and CI can inspect them without another dependency. Artifact hashes
make it clear which dataset and fixture each result describes. The local baseline times only the
in-process `search_menu` call after warming cached catalog and SQLite data; it does not claim HTTP or
production latency.

The regression fixture includes the undesirable unknown-query result because Phase 0 records reality.
Phase 1 must deliberately replace that expectation when it removes the underlying ranking bonus.

## Alternatives considered

- A notebook was rejected because it is harder to enforce in CI and review as deterministic source.
- A full relevance judgment set was deferred to the dedicated evaluation phase; Phase 0C snapshots
  behavior rather than claiming relevance quality.
- Third-party benchmarking and data-frame libraries were unnecessary for the current corpus size.

## Tradeoffs and consequences

Latency values vary by machine, so regenerated tracked reports will contain measurement differences.
CI verifies report generation with five repetitions but does not compare latency thresholds. Exact
top-result snapshots are intentionally sensitive to ranking changes and must be reviewed when changed.

## Security, reliability, data, and performance

The tools access only checked-in local files and make no network requests. SQLite connections are
closed deterministically. Report verification fails on malformed JSON or missing record IDs/names.

Measured dataset facts:

| Metric | Value |
|---|---:|
| Catalog rows | 920 |
| Valid JSON records | 920 |
| Unique Spoonacular IDs | 460 |
| Duplicate source-ID rows | 460 |
| Unique normalized names | 430 |
| SQLite detail records | 51 |
| Unique source IDs with details | 51 of 460 (11.09%) |
| Catalog nutrition coverage before enrichment | 0% |

The initial six-query warm-cache run on macOS ARM with Python 3.12.12 produced a median query p95 of
approximately 2 ms. This is a local algorithm baseline, not an API SLO.

## Verification

Verification was performed on 2026-08-14:

| Check | Result |
|---|---|
| Data integrity gate | Passed |
| Catalog report generation | Passed |
| Retrieval snapshot matches | 6 of 6 |
| Backend pytest | Passed; 13 tests |
| Ruff | Passed |
| Pyright | Passed; 0 errors and 0 warnings |
| Frontend lint and build | Passed |
| Docker Compose validation | Passed |

## Known limitations and risks

- Half of catalog rows duplicate a source ID, and name-level duplication is greater still.
- Catalog metadata other than names is empty before optional SQLite enrichment.
- Only 11.09% of unique catalog source IDs have detail payloads.
- Original per-record fetch timestamps, request modes, and source manifests are unavailable.
- The current nutrition-presence bonus returns unrelated enriched items for zero-overlap queries.
- Six queries are a regression snapshot, not a relevance evaluation dataset.
- Latency measurement excludes HTTP, serialization, cold startup, and concurrency.

## Follow-up work

Phase 1 should remove the zero-overlap relevance bonus, define unknown-value filter semantics,
deduplicate the catalog at generation time, expose matching structured UI filters, and version the API
response. The later evaluation phase should introduce reviewed judgments and formal ranking metrics.

## Affected files

- `.github/workflows/ci.yml`
- `Makefile`
- `README.md`
- `backend/tools/data_report.py`
- `backend/tools/retrieval_baseline.py`
- `backend/tests/fixtures/retrieval_baseline.json`
- `backend/tests/test_data_report.py`
- `backend/tests/test_retrieval_baseline.py`
- `docs/reports/data-quality.json`
- `docs/reports/retrieval-baseline.json`
- `docs/implementation/README.md`
- `docs/implementation/02-baseline-and-data-report.md`
