# TasteIQ

TasteIQ is a full-stack meal discovery app that grounds its recommendations in a local menu dataset. Describe a craving, cuisine, or nutrition goal and the API ranks matching menu items without requiring an API key.

## What works

- Responsive React search experience
- FastAPI recommendation endpoint with input validation
- Local retrieval over 900+ prepared menu items
- Optional calorie, protein, and diet constraints at the API layer
- CORS configuration, API tests, and Docker setup

## Run locally

Requirements: Python 3.11+ and Node 20+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. API documentation is available at <http://localhost:8000/docs>.

You can also run both services with `docker compose up --build`.

## API

`POST /api/recommendations`

```json
{
  "query": "high-protein chicken",
  "limit": 6,
  "max_calories": 650,
  "min_protein": 20,
  "diet": "low-carb"
}
```

Only `query` is required. Nutrition constraints are applied when an item has that data; items with unknown nutrition remain discoverable rather than being misrepresented.

## Tests and checks

```bash
cd backend && pytest
cd frontend && npm run lint && npm run build
```

## Data pipeline

The checked-in `backend/database/rag_items.jsonl` file is the runtime source. Scripts under `backend/database/` can ingest Spoonacular data, normalize it, and build an optional FAISS index. Those maintenance steps require their respective API key or machine-learning dependencies; the application itself does not.
