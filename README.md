# TasteIQ

TasteIQ is a full-stack meal-discovery application that ranks grounded recommendations from real menu data. Users can describe a craving, cuisine, or nutrition goal and receive matching menu items with available restaurant and nutrition information.

The current release is a local MVP. TasteIQ is being developed into an evaluated recommendation platform with hybrid retrieval, personalization, reproducible data pipelines, observability, and measurable latency targets.

## Current features

- Responsive React search experience
- FastAPI recommendation API with request validation
- Local retrieval over 448 deduplicated menu records
- Ingestion-time and response-level deduplication
- Optional calorie and protein constraints with strict unknown-value handling
- SQLite enrichment for available restaurant and nutrition details
- Docker and Docker Compose support
- Backend API tests and frontend lint/build checks

The current runtime uses deterministic token-overlap ranking. Hybrid vector retrieval, reranking, personalization, PostgreSQL, Redis, and the proposed Rust retrieval service are planned work—not current functionality.

## Architecture

```text
React client → FastAPI → local retriever → JSONL menu catalog
                                  └──────→ SQLite enrichment
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
query outputs, known retrieval defects, and local latency methodology. They are measurements of the
current snapshot, not production performance claims.

Run the versioned offline relevance evaluation independently:

```bash
make eval
```

The first judgment set contains 34 reviewed queries and reports Precision@5, Recall@10, MRR@10,
nDCG@10, constraint violations, duplicate results, no-result accuracy, empty-result rate, and
per-query rankings.

## Project status

TasteIQ is in the baseline phase. Near-term work focuses on repository cleanup, data quality, retrieval evaluation, PostgreSQL persistence, structured filters, CI, and runtime instrumentation. Advanced retrieval and systems optimization will be added against measured baselines.

See [docs/architecture-plan.md](docs/architecture-plan.md) for the internal system design and phased delivery plan.

## License

See [LICENSE](LICENSE).
