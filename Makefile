PYTHON ?= python3.12
BACKEND_VENV := backend/.venv
BACKEND_PYTHON := $(BACKEND_VENV)/bin/python
BACKEND_PIP := $(BACKEND_VENV)/bin/pip

.PHONY: bootstrap check test lint typecheck build compose-check verify-reports reports eval compare clean

bootstrap:
	$(PYTHON) -m venv $(BACKEND_VENV)
	$(BACKEND_PIP) install --upgrade pip
	$(BACKEND_PIP) install -r backend/requirements-dev.txt
	npm --prefix frontend ci

check: lint typecheck test build compose-check verify-reports

verify-reports:
	cd backend && .venv/bin/python -m tools.data_report --check --output /tmp/tasteiq-data-quality.json
	cd backend && .venv/bin/python -m tools.retrieval_baseline --repetitions 5 --output /tmp/tasteiq-retrieval-baseline.json
	cd backend && .venv/bin/python -m evaluation.run --output /tmp/tasteiq-evaluation.json
	cd backend && .venv/bin/python -m evaluation.compare --output /tmp/tasteiq-comparison.json

reports:
	cd backend && .venv/bin/python -m tools.data_report --check
	cd backend && .venv/bin/python -m tools.retrieval_baseline
	cd backend && .venv/bin/python -m evaluation.run --retriever token --output ../docs/reports/evaluation-token-overlap-v2.json
	$(MAKE) eval
	$(MAKE) compare

eval:
	cd backend && .venv/bin/python -m evaluation.run

compare:
	cd backend && .venv/bin/python -m evaluation.compare

test:
	cd backend && .venv/bin/pytest

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
