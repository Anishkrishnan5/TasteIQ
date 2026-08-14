PYTHON ?= python3.12
BACKEND_VENV := backend/.venv
BACKEND_PYTHON := $(BACKEND_VENV)/bin/python
BACKEND_PIP := $(BACKEND_VENV)/bin/pip

.PHONY: bootstrap check test lint typecheck build compose-check clean

bootstrap:
	$(PYTHON) -m venv $(BACKEND_VENV)
	$(BACKEND_PIP) install --upgrade pip
	$(BACKEND_PIP) install -r backend/requirements-dev.txt
	npm --prefix frontend ci

check: lint typecheck test build compose-check

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
