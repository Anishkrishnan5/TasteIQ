# TasteIQ

TasteIQ is a full-stack meal-discovery application that ranks grounded recommendations from real menu data. Users can describe a craving, cuisine, or nutrition goal and receive matching menu items with available restaurant and nutrition information.

The current release is a local MVP. TasteIQ is being developed into an evaluated recommendation platform with hybrid retrieval, personalization, reproducible data pipelines, observability, and measurable latency targets.

## Current features

- Responsive React search experience
- FastAPI recommendation API with request validation
- Local retrieval over 448 deduplicated menu records
- Ingestion-time and response-level deduplication
- Optional calorie and protein constraints with strict unknown-value handling
- Deterministic BM25 ranking with conservative, corpus-aware spelling correction
- A versioned 34-query evaluation suite with checked-in comparison reports
- Optional pinned dense retrieval and RRF hybrid search with BM25 outage fallback
- Request IDs, stage timings, and catalog/retriever version metadata
- SQLite enrichment for available restaurant and nutrition details
- Docker and Docker Compose support
- Backend API tests and frontend lint/build checks

The default runtime uses the measured BM25 winner. Dense vector retrieval and reciprocal-rank fusion
are implemented as an opt-in experiment, but are not the default because the current hybrid benchmark
underperforms BM25. Reranking, personalization, PostgreSQL, Redis, and the proposed Rust retrieval
service remain planned work.

## Architecture

```text
React client → FastAPI → BM25 retriever ─────────→ JSONL menu catalog
                         └→ optional dense + RRF ─┘
                                      └──────────→ SQLite enrichment
```

The proposed production architecture and implementation sequence are documented in [docs/architecture-plan.md](docs/architecture-plan.md).

## Run locally

Requirements:

- Python 3.12
- Node.js 20+

Bootstrap both applications and all development checks from the repository root:

```bash
make bootstrap
make check
```

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
