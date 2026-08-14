# Phase 0B: Reproducible Tooling

**Status:** Complete  
**Date:** 2026-08-13  
**Related phase:** Phase 0 — Protect the baseline

## Outcome

TasteIQ now has a single bootstrap command, a single local quality gate, pinned backend development
tools, aligned Python configuration, and GitHub Actions checks for the supported application path.

From a clean clone with Python 3.12, Node.js 20+, npm, Make, and Docker installed:

```bash
make bootstrap
make check
```

## Starting state

Runtime dependencies were pinned in `requirements.txt`, and the frontend had a lock file, lint script,
and build script. However, the backend development environment was not reproducible in the current
checkout: `pytest` was unavailable, Python configuration targeted 3.14 while the container used 3.12,
there was no Python linter in the workflow, and there was no CI or repository-level command interface.

## Changes made

- Added pinned Ruff and Pyright development dependencies.
- Added central Ruff and pytest configuration in `backend/pyproject.toml`.
- Aligned local tooling, type checking, CI, Docker, and documentation on Python 3.12.
- Added `make bootstrap` for backend and frontend installation.
- Added `make check` for formatting, linting, type checking, tests, frontend build, and Compose validation.
- Added least-privilege GitHub Actions jobs for backend, frontend, and Compose checks.
- Formatted the active backend and modernized type annotations to satisfy the new baseline.
- Fixed the standalone Spoonacular client example, which called `fetch_menu_items` without its required
  query argument.
- Narrowed the retriever enrichment lookup to integer Spoonacular IDs for type-safe database access.

## System-design impact

This part does not intentionally change recommendation ranking. It creates the automated safety net
needed for subsequent data and retrieval changes and ensures that local and CI checks execute the same
commands.

## Decisions and reasoning

Ruff provides a fast formatter and broad static lint coverage through one pinned tool. Pyright was
retained because the repository already contained its configuration. Make supplies a small,
tool-agnostic command interface without introducing an application runtime dependency.

CI uses separate backend, frontend, and Compose jobs so failures remain attributable and independent.
Workflow permissions are read-only.

## Alternatives considered

- Pre-commit hooks were deferred because CI and explicit commands establish the first enforceable gate.
- Poetry, PDM, and uv were not introduced yet; the existing requirements files remain compatible with
  Docker and require less migration work.
- A monolithic CI job was rejected because it would reduce feedback clarity and parallelism.

## Tradeoffs and consequences

Direct dependencies are pinned, but transitive Python dependencies do not yet have a hash-locked file.
Developers must have Python 3.12 available as `python3.12`. The formatter caused mechanical changes in
older ingestion and preprocessing modules, without intended behavior changes.

## Security, reliability, data, and performance

The GitHub workflow has read-only repository permissions. Docker configuration is validated but images
are not yet built, scanned, or hardened in CI. `npm ci` reported 12 dependency advisories in the current
frontend dependency tree; dependency remediation remains follow-up work and should be evaluated without
blind major-version upgrades.

No data files or ranking scores were changed. Quality checks add development and CI time but no runtime
latency.

## Verification

Verification was performed locally on 2026-08-13 with Python 3.12.12 and Node.js 22.16.0:

| Check | Result |
|---|---|
| Ruff lint | Passed |
| Ruff formatting check | Passed; 20 files checked |
| Pyright | Passed; 0 errors and 0 warnings |
| Backend pytest | Passed; 5 tests in 0.61 seconds |
| Frontend ESLint | Passed |
| Frontend production build | Passed |
| Docker Compose configuration | Passed |
| Combined `make check` | Passed |

## Known limitations and risks

- CI has been defined locally but cannot be considered green until pushed and executed by GitHub.
- Python transitive dependencies are not hash-locked.
- Backend coverage remains limited to five API tests.
- There are no frontend unit or end-to-end tests.
- Container builds and security scans are not part of CI yet.
- The existing frontend audit reports 12 dependency advisories.

## Follow-up work

Phase 0C should add an automated catalog/database validator, data coverage and duplicate reports,
representative retrieval regression cases, and measured relevance and latency baselines.

## Affected files

- `.github/workflows/ci.yml`
- `Makefile`
- `README.md`
- `backend/pyproject.toml`
- `backend/pyrightconfig.json`
- `backend/requirements-dev.txt`
- Active backend Python modules formatted by Ruff
- `docs/implementation/README.md`
- `docs/implementation/01-reproducible-tooling.md`
