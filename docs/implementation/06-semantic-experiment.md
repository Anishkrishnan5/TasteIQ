# Phase 3C: Semantic Experiment and Query Correction

**Status:** Complete

**Date:** 2026-08-14

**Related phase:** Phase 3 — Evaluation-first hybrid retrieval

## Outcome

TasteIQ can build and validate a pinned dense index, run dense retrieval, and fuse BM25 and dense
candidates with reciprocal-rank fusion (RRF). The hybrid implementation is available behind
`RETRIEVAL_MODE=hybrid` and falls back cleanly to BM25. It is not the default: the controlled benchmark
showed that equal-weight fusion reduced relevance on this small, lexically narrow catalog.

The same work identified a smaller improvement that did pass the adoption rule. Conservative
corpus-aware spelling correction now improves the default BM25 retriever and exposes every correction
in API metadata.

## Starting state

The API used BM25 over 448 deduplicated records. It had no embedding build, vector validation, semantic
search, fusion, or misspelling recovery. The evaluation set contained semantic and spelling challenges,
but its candidate pool had not been expanded with dense results.

## Changes made

- Added an optional `sentence-transformers` dependency set and a pinned
  `sentence-transformers/all-MiniLM-L6-v2` model revision.
- Added deterministic embedding generation for 384-dimensional normalized vectors.
- Added a manifest containing the model revision, catalog hash, record count, dimensions, normalization
  policy, and vector-file checksum.
- Added cosine-similarity dense search with the same strict nutrition constraints as BM25.
- Added equal-weight RRF over 50 BM25 and 50 dense candidates with `k=60`.
- Added BM25 fallback when the model, index, or dependency set is unavailable or invalid.
- Added dense, hybrid, and three-way comparison reports using expanded pooled judgments.
- Added conservative spelling correction for out-of-vocabulary tokens only. Candidates must exceed a
  similarity cutoff and share the first and last character, limiting surprising substitutions.
- Added response metadata for normalized queries, corrections, active retrieval mode, and degradation.

## System-design impact

The default request path remains lightweight:

```text
request → spelling normalization → BM25 → enrichment → response
```

The opt-in path is:

```text
request → BM25 candidates + dense candidates → RRF → enrichment → response
                         └─ failure ───────────→ BM25 fallback
```

Vector artifacts are generated locally and ignored by Git. The checked-in code, manifest schema,
model revision, and commands make the experiment repeatable without making large ML packages part of
the base application.

## Decisions and reasoning

The dense model was pinned by immutable revision rather than floating on a model name. Runtime loading
uses local files only, so an API request never triggers an unexpected network download. Artifact
validation fails closed on catalog drift, shape mismatch, or checksum mismatch.

Equal-weight RRF was chosen as a transparent first fusion baseline. The comparison rejected it for the
live default. Retaining BM25 is an evidence-based decision, not an unfinished integration: semantic
retrieval remains opt-in so future changes can be compared without destabilizing normal requests.

Spelling correction was adopted because it improved aggregate quality without a per-query regression.
It is deliberately corpus-aware and narrower than general autocorrect.

## Alternatives considered

- Committing vector artifacts was rejected because they are generated, catalog-specific binaries.
- Making Torch and sentence-transformers base dependencies was rejected because the default runtime
  does not need them.
- Enabling hybrid unconditionally was rejected by the offline relevance comparison.
- Approximate-nearest-neighbor infrastructure was deferred; exhaustive cosine scoring is simpler and
  fast enough for 448 records.
- An unconstrained edit-distance corrector was rejected after it changed valid food terms.

## Tradeoffs and consequences

The optional ML environment is substantially larger than the base backend. Dense and hybrid requests
also have higher warm latency than BM25 on this corpus. In exchange, the repository now demonstrates a
complete semantic-retrieval experiment, reproducible artifact lineage, failure handling, and an honest
adoption decision.

## Security, reliability, data, and performance

- Runtime model loading is local-only.
- The vector manifest binds the artifact to the exact model revision and catalog contents.
- Invalid or missing vectors cannot silently affect rankings; hybrid mode reports BM25 degradation.
- Dense and hybrid searches enforce the same known-value nutrition constraints as BM25.
- Unsupported lexical queries still return no results instead of receiving arbitrary semantic matches.

## Verification

The full base workflow passes Python formatting/linting, static typing, backend tests, frontend lint and
build, Docker Compose validation, report reproducibility, and evaluation thresholds. Dedicated tests
cover artifact failure, RRF behavior, safe fallback, unsupported-query handling, spelling correction,
and API diagnostics.

The checked-in reports record the exact aggregate metrics and per-query rankings. Corrected BM25 is the
default because it outperforms both dense retrieval and equal-weight hybrid fusion on the current
judgments. These local measurements are regression evidence, not production claims.

## Known limitations and risks

- The 34-query, single-reviewer judgment set is small and corpus-specific.
- Pooling candidates from evaluated systems can still miss unseen relevant records.
- The catalog is strongly chicken-oriented, limiting what semantic retrieval can demonstrate.
- RRF weights and candidate depths have not been tuned on a separate validation set.
- Exhaustive vector scoring will not scale to a large catalog.
- Spelling correction handles token typos, not paraphrases or multi-token intent.

## Follow-up work

Broaden the catalog and obtain a second judgment pass before tuning fusion. Evaluate semantic query
rewriting or a stronger embedding model on a held-out set, add diversity and reranking only when they
improve measured quality, and deploy the default BM25 service with observability before adding vector
infrastructure.

## Affected files

- `backend/rag/bm25.py`, `backend/rag/dense.py`, `backend/rag/hybrid.py`, `backend/rag/pipeline.py`
- `backend/evaluation/`, `backend/tests/`, `backend/requirements-ml.txt`
- `Makefile`, `.gitignore`, `README.md`, `docs/evaluation.md`, `docs/reports/`
