PYTHON ?= python3.12
BACKEND_VENV := backend/.venv
BACKEND_PYTHON := $(BACKEND_VENV)/bin/python
BACKEND_PIP := $(BACKEND_VENV)/bin/pip

.PHONY: bootstrap bootstrap-ml bootstrap-mlops embeddings check test test-e2e lint typecheck build compose-check verify-reports reports eval compare eval-ml compare-ml experiment mlflow-ui clean

bootstrap:
	$(PYTHON) -m venv $(BACKEND_VENV)
	$(BACKEND_PIP) install --upgrade pip
	$(BACKEND_PIP) install -r backend/requirements-dev.txt
	npm --prefix frontend ci

bootstrap-ml: bootstrap
	$(BACKEND_PIP) install -r backend/requirements-ml.txt

bootstrap-mlops: bootstrap-ml
	$(BACKEND_PIP) install -r backend/requirements-mlops.txt

embeddings:
	cd backend && .venv/bin/python -m rag.dense build

check: lint typecheck test build compose-check verify-reports

verify-reports:
	cd backend && .venv/bin/python -m tools.data_report --check --output /tmp/tasteiq-data-quality.json
	cd backend && .venv/bin/python -m tools.retrieval_baseline --repetitions 5 --output /tmp/tasteiq-retrieval-baseline.json
	cd backend && .venv/bin/python -m evaluation.run --output /tmp/tasteiq-evaluation.json
	cd backend && .venv/bin/python -m evaluation.compare --output /tmp/tasteiq-comparison.json

reports:
	cd backend && .venv/bin/python -m tools.data_report --check
	cd backend && .venv/bin/python -m tools.retrieval_baseline
	cd backend && .venv/bin/python -m evaluation.run --retriever token --report-only --output ../docs/reports/evaluation-token-overlap-v2.json
	$(MAKE) eval
	$(MAKE) compare

eval:
	cd backend && .venv/bin/python -m evaluation.run

compare:
	cd backend && .venv/bin/python -m evaluation.compare

eval-ml:
	cd backend && .venv/bin/python -m evaluation.run --retriever dense --report-only --output ../docs/reports/evaluation-dense-v1.json
	cd backend && .venv/bin/python -m evaluation.run --retriever hybrid --report-only --output ../docs/reports/evaluation-hybrid-v1.json

compare-ml:
	cd backend && .venv/bin/python -m evaluation.compare_hybrid

experiment:
	cd backend && .venv/bin/python -m evaluation.track_experiment

mlflow-ui:
	cd backend && .venv/bin/mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 127.0.0.1 --port 5000

test:
	cd backend && .venv/bin/pytest

test-e2e:
	npm --prefix frontend run test:e2e

lint:
	cd backend && .venv/bin/ruff check .
	cd backend && .venv/bin/ruff format --check .
	npm --prefix frontend run lint

typecheck:
	cd backend && .venv/bin/pyright

build:
	npm --prefix frontend run build

compose-check:
	docker compose config --quiet

clean:
	rm -rf frontend/dist
	find backend -type d -name __pycache__ -prune -exec rm -rf {} +
