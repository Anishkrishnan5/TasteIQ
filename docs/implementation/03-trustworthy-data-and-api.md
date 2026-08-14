# Phase 1: Trustworthy Data and API

**Status:** Complete  
**Date:** 2026-08-14  
**Related phase:** Phase 1 — Trustworthy data and API

## Outcome

TasteIQ now returns only lexically grounded results, treats explicit nutrition limits as strict
constraints, uses a deduplicated and reproducibly generated runtime catalog, exposes matching calorie
and protein filters in the web interface, and returns a documented versioned API response with request
and timing metadata.

## Starting state

The Phase 0 baseline proved several correctness gaps:

- A nutrition-presence score bonus admitted unrelated items for zero-overlap queries.
- Nutrition filters allowed unknown values through, making limits ambiguous.
- The 920-row runtime catalog contained duplicate source IDs and omitted available restaurant names.
- The API accepted a dietary field that the data could not evaluate reliably.
- The frontend exposed none of the API's structured filters and implied natural-language parsing.
- Responses had no schema, artifact version, request ID, or timing information.
- A development-only error route and hard-coded route version remained.

## Changes made

### Retrieval correctness

- Removed the nutrition-presence relevance bonus.
- Zero-overlap queries now return an empty result set.
- Calorie and protein filters exclude both known violations and unknown values.
- Bumped the deterministic retriever identifier to `token-overlap-v2`.

### Data generation

- Added Spoonacular's `restaurantChain` to normalization.
- Deduplicated by source ID and conservative restaurant/name identity during preprocessing.
- Regenerated the runtime catalog from SQLite: 920 raw rows became 448 distinct runtime records.
- Added duplicate removal to the automated data-quality gate.
- Added preprocessing tests for restaurant preservation and idempotent entity deduplication.

### API contract and diagnostics

- Added Pydantic request, menu-item, response metadata, success, and error models.
- Published schema version `1.0` and application version `0.2.0`.
- Rejected unknown request fields instead of silently ignoring unsupported filters.
- Removed the development-only `/test-error` route.
- Added safe request-ID generation/propagation through response bodies and `X-Request-ID`.
- Added `Server-Timing` and response metadata for retrieval and response construction.
- Added retriever version and catalog SHA-256 to each recommendation response.
- Added a structured validation-error envelope and documented it in OpenAPI.

### Product interface

- Added maximum-calorie and minimum-protein controls to the search form.
- Added a clear-filter action and a visible explanation of strict unknown-value behavior.
- Replaced copy that implied unsupported natural-language nutrition parsing.
- Improved frontend handling of structured server errors.
- Removed dietary filtering from the public request contract until trustworthy dietary metadata exists.

## System-design impact

The runtime path remains a modular monolith, but it now exposes the minimum traceability required for
measured ranking work:

```text
React query + explicit filters
        │
        ▼
versioned FastAPI contract + request ID
        │
        ▼
strict known-value filtering → token-overlap-v2 → deduplicated catalog
        │                                      └→ SQLite detail enrichment
        ▼
versioned response + artifact hash + stage timings
```

The changed snapshot is intentional and recorded in the retrieval baseline fixture and report.

## Decisions and reasoning

Unknown nutrition is excluded whenever the user supplies a nutrition constraint. This is the only
behavior that makes “maximum” and “minimum” truthful without presenting an unknown value as safe.
Unfiltered searches continue to include items with unknown nutrition.

Dietary filtering was removed from the request rather than pretending empty tags are evidence. It can
return after a future ingestion pipeline supplies source-backed or explicitly inferred dietary fields.

Request IDs accept a caller value only when it contains a bounded safe character set; otherwise the API
generates a UUID. Catalog hashes and retriever versions make a response attributable to concrete inputs.

## Alternatives considered

- Keeping unknown nutrition in filtered results was rejected because it weakens a hard constraint.
- Returning no results for every diet filter was rejected as technically strict but unusable and
  misleading given 0% dietary metadata coverage.
- Natural-language calorie parsing was deferred; explicit UI inputs are deterministic and unambiguous.
- Deduplicating only at response time was insufficient because it wastes ranking work and leaves the
  runtime dataset itself misleading.

## Tradeoffs and consequences

Strict filtering reduces recall to the 51 records with nutrition enrichment. The catalog shrank to 448
records because 472 raw rows represented duplicate source IDs or conservative duplicate entities.
Restaurant names improve grounding but can cause a query to match a restaurant name even when the item
name lacks that token; later evaluation and BM25 field weighting should measure this behavior.

The API contract changed by removing `diet` and adding response metadata. This is recorded as application
version `0.2.0`; no deployed compatibility obligation exists for the local MVP.

## Security, reliability, data, and performance

- Request IDs are bounded to 128 safe characters before being copied to response headers.
- Unknown request fields are forbidden.
- Numeric filters have upper and lower bounds.
- Whitespace-only queries are rejected after trimming.
- Error responses do not include stack traces or internal paths.
- Runtime catalog generation is deterministic and idempotent.
- The deduplicated catalog reduced the measured warm-cache median query p95 from roughly 2 ms to roughly
  1.25 ms on the same local class of environment; this is not a production SLO claim.

## Verification

Verification was performed locally on 2026-08-14:

| Check | Result |
|---|---|
| Catalog export | 920 seen, 448 kept, 472 duplicates removed |
| Export idempotency | Identical SHA-256 before and after regeneration |
| Data-quality gate | Passed, including zero duplicate source IDs |
| Retrieval snapshots | 6 of 6 top results and counts matched |
| Unknown query | Returned zero results |
| Strict calorie/protein request | Every returned value known and within bounds |
| Request ID propagation | Passed in header and response body |
| Versioned OpenAPI success/error schemas | Passed |
| Backend pytest | 20 tests passed |
| Ruff and Pyright | Passed; 0 type errors or warnings |
| Frontend ESLint and production build | Passed |
| Docker Compose validation | Passed |

## Known limitations and risks

- Nutrition coverage remains limited to 51 of 448 runtime items.
- Diet, allergen, ingredient-exclusion, and cuisine filters remain unavailable.
- Timings cover in-process stages and total server handling, not browser/network latency.
- The frontend has lint/build coverage but no component or browser tests.
- Token overlap lacks term-frequency, inverse-document-frequency, phrase, and field-weight modeling.
- The raw SQLite table retains duplicate historical fetch rows; the generated runtime catalog is clean.

## Follow-up work

The next delivery should create the first reviewed relevance judgment set and formal metric runner.
After the evaluation baseline is fixed, implement BM25 and compare its quality and latency against
`token-overlap-v2` without weakening strict filters or deduplication.

## Affected files

- `README.md`
- `backend/api/routes.py`
- `backend/api/schemas.py`
- `backend/app.py`
- `backend/core/config.py`
- `backend/core/errors.py` (removed)
- `backend/database/rag_items.jsonl`
- `backend/pyproject.toml`
- `backend/rag/pipeline.py`
- `backend/rag/retriever.py`
- `backend/utils/preprocess.py`
- `backend/tests/`
- `backend/tools/data_report.py`
- `backend/tools/retrieval_baseline.py`
- `frontend/src/App.jsx`
- `frontend/src/App.css`
- `docs/architecture-plan.md`
- `docs/reports/`
