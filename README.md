# TasteIQ

TasteIQ is a full-stack meal-discovery application that ranks grounded recommendations from real menu data. Users can describe a craving, cuisine, or nutrition goal and receive matching menu items with available restaurant and nutrition information.

The current release is a local MVP. TasteIQ is being developed into an evaluated recommendation platform with hybrid retrieval, personalization, reproducible data pipelines, observability, and measurable latency targets.

## Current features

- Responsive React search experience
- FastAPI recommendation API with request validation
- Local retrieval over 448 deduplicated menu records
- Ingestion-time and response-level deduplication
- Optional calorie and protein constraints with strict unknown-value handling
- PostgreSQL-backed profiles, preferences, saved meals, and search history
- Explainable preference-aware reranking with disliked-ingredient exclusion
- Grounded conversational answers with validated menu-item citations
- Optional Gemini generation with a deterministic no-key/provider-outage fallback
- Deterministic BM25 ranking with conservative, corpus-aware spelling correction
- A versioned 34-query evaluation suite with checked-in comparison reports
- Optional pinned dense retrieval and RRF hybrid search with BM25 outage fallback
- Request IDs, stage timings, and catalog/retriever version metadata
- SQLite enrichment for available restaurant and nutrition details
- Docker and Docker Compose support
- Non-root API and web containers with health checks
- Backend API tests, frontend checks, and a real Playwright browser journey

The default runtime uses the measured BM25 winner. Dense vector retrieval and reciprocal-rank fusion
are implemented as an opt-in experiment, but are not the default because the current hybrid benchmark
underperforms BM25. Reranking, personalization, PostgreSQL, Redis, and the proposed Rust retrieval
service remain planned work.

Chat retrieval is always local and grounded in the same catalog. Gemini is optional: when configured,
it explains the retrieved records conversationally; when absent, unavailable, malformed, or missing
valid citations, TasteIQ returns a deterministic answer over those same records.

## Architecture

```text
React client → FastAPI → BM25 retriever ─────────→ JSONL menu catalog
                         └→ optional dense + RRF ─┘
                                      ├──────────→ SQLite catalog enrichment
                                      └──────────→ PostgreSQL personalization
```

The proposed production architecture and implementation sequence are documented in [docs/architecture-plan.md](docs/architecture-plan.md).

## Run locally

Requirements:

- Python 3.12
- Node.js 20+

Bootstrap both applications and all development checks from the repository root:

```bash
make bootstrap
make db-up
make db-migrate
make check
make test-e2e
```

The browser test starts the real FastAPI and React applications, submits a misspelled query with
nutrition filters, and verifies correction metadata, constraint-safe API results, and rendered cards.

Start the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Interactive API documentation is available at <http://localhost:8000/docs>.

The profile panel creates a local demo identity without authentication. Preferences are normalized and
stored in PostgreSQL. Personalized searches retrieve a wider grounded candidate set, exclude known
disliked ingredients, and apply small documented boosts for favorite cuisines, supported dietary
goals, and saved items. Every personalized search is recorded in the profile history.

To run both services with Docker:

```bash
docker compose up --build
```

### Optional semantic retrieval experiment

The larger ML dependency set and generated vector index are intentionally separate from the default
bootstrap. To reproduce the experiment:

```bash
make bootstrap-ml
make embeddings
make eval-ml
make compare-ml
```

Start the API with `RETRIEVAL_MODE=hybrid` to opt in. If the pinned model or validated index is
unavailable, the request automatically falls back to BM25 and reports the degraded mode in response
metadata. Generated vectors are not committed; the manifest pins the model revision and catalog hash.

### Track the experiment lifecycle

MLflow is an optional layer over the same checked-in evaluator. It records a parent champion-selection
run, child BM25/dense/hybrid runs, exact code and data lineage, retrieval parameters, metrics, and the
full comparison artifact:

```bash
make bootstrap-mlops
make embeddings
make experiment
make mlflow-ui
```

Open <http://127.0.0.1:5000> to inspect the runs. Local MLflow database and artifact files are ignored;
the portable experiment receipt under `docs/reports/` records the verified decision and run lineage.

## API

### Health

```http
GET /health
```

### Recommendations

```http
POST /api/recommendations
Content-Type: application/json
```

Example request:

```json
{
  "query": "high-protein chicken",
  "limit": 6,
  "max_calories": 650,
  "min_protein": 20
}
```

Only `query` is required. When a nutrition constraint is supplied, records with unknown values are
excluded so every returned item is known to satisfy the constraint. Dietary filters are not exposed
until the dataset contains trustworthy dietary metadata.

Pass a profile UUID as `profile_id` to enable preference-aware reranking and record the search in that
profile's history. Demo profile endpoints are intentionally unauthenticated for this personal MVP:

```text
POST   /api/profiles
GET    /api/profiles/{profile_id}
PUT    /api/profiles/{profile_id}
GET    /api/profiles/{profile_id}/saved
POST   /api/profiles/{profile_id}/saved
DELETE /api/profiles/{profile_id}/saved/{spoonacular_id}
GET    /api/profiles/{profile_id}/history
```

This is not an account system. Add authentication and ownership checks before accepting data from
multiple real users.

### Grounded chat

```http
POST /api/chat
Content-Type: application/json
```

```json
{
  "message": "What is a high-protein chicken option?",
  "history": [],
  "profile_id": null,
  "min_protein": 20
}
```

The response includes the answer, validated menu citations, provider/model metadata, retrieval
lineage, and an explicit degraded reason when the local fallback is used. Recent user turns are folded
into retrieval for conversational follow-ups, but only retrieved catalog records may be cited.

To enable Gemini when running Docker, copy `.env.example` to `.env`, add a Google AI Studio key, and
restart Compose. For direct backend development, use `backend/.env.example` instead. Both real `.env`
files are ignored by Git. Do not use sensitive personal information with the Gemini free tier.

## Tests and checks

```bash
make check
```

## Data pipeline

The checked-in `backend/database/rag_items.jsonl` file is the current runtime catalog. Maintenance scripts ingest, normalize, and enrich menu data using the Spoonacular API; the current application runtime does not require an external API credential.

Regenerate the checked-in data-quality and retrieval-baseline reports:

```bash
make reports
```

The reports under `docs/reports/` record artifact hashes, duplicate and metadata coverage, baseline
query outputs, formal retrieval metrics, BM25 and hybrid comparison results, and local latency
methodology. They are measurements of the current snapshot, not production performance claims.

Run the versioned offline relevance evaluation independently:

```bash
make eval
```

The first judgment set contains 34 reviewed queries and reports Precision@5, Recall@10, MRR@10,
nDCG@10, constraint violations, duplicate results, no-result accuracy, empty-result rate, and
per-query rankings.

## Project status

TasteIQ now has a reproducible retrieval-evaluation foundation, an improved lexical default, and a
rejected-but-reproducible semantic experiment. Near-term work should broaden the catalog and judgments,
improve semantic relevance before enabling hybrid search, and add deployment and observability.

See [docs/architecture-plan.md](docs/architecture-plan.md) for the internal system design and phased delivery plan.
The bounded [`v1.0.0` portfolio release scope](docs/portfolio-release-scope.md) is the authoritative
definition of completion; the broader architecture plan remains a source of optional future ideas.

## License

See [LICENSE](LICENSE).
