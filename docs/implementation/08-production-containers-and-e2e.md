# Portfolio Release: Production Containers and Browser Journey

**Status:** In progress — implementation verified except image execution

**Date:** 2026-08-18

**Related phase:** Portfolio release — quality and delivery

## Outcome

TasteIQ now defines least-privilege frontend and backend images with explicit health checks, and a
Playwright test exercises the principal journey through the real browser, frontend, API, retrieval
pipeline, and catalog. The browser journey passes locally. Docker Compose configuration validates,
but final image build and runtime inspection remain pending because the local Docker daemon was not
running during this delivery part.

## Starting state

Both services had minimal Dockerfiles that ran with image defaults, lacked health checks, and did not
encode production-oriented runtime settings. CI linted and built frontend assets but never exercised a
browser or the frontend/backend contract together.

## Changes made

- Backend image creates and runs as an unprivileged `tasteiq` user.
- Backend image disables bytecode writes, enables unbuffered logs, uses proxy headers, and exposes a
  Python-based health check without adding curl.
- Frontend image now uses the unprivileged Nginx distribution on port 8080.
- Nginx provides SPA fallback, a health endpoint, and basic response-security headers.
- Frontend builds accept `VITE_API_URL` as an explicit build argument.
- Compose waits for API health before starting the web service.
- Docker contexts exclude tests, local MLflow state, development dependencies, and generated vectors
  that the default BM25 runtime does not require.
- Added a pinned Playwright test runner and Chromium browser project.
- Added a real user-journey test covering typo correction, calorie and protein filters, API safety,
  and UI rendering.
- Added a dedicated CI browser-test job with both Python and Node dependencies.
- Updated Axios after the production dependency audit identified vulnerable locked dependencies; the
  production-only audit now reports zero known vulnerabilities and is a frontend CI gate.

## System-design impact

The browser gate now crosses the principal deployed boundary:

```text
Chromium → React → FastAPI → query correction → nutrition constraints → BM25 → catalog → UI cards
```

The images retain a single-process API and static frontend architecture suitable for ECS Fargate and
S3/CloudFront delivery. No service decomposition was introduced.

## Decisions and reasoning

A single Chromium journey is sufficient for the v1 architectural gate. It tests the riskiest contract
without creating a broad UI-test maintenance burden. It deliberately uses real services rather than a
mocked API.

The backend retains one Uvicorn process because ECS can scale tasks horizontally and the current load
does not justify an internal process manager. The frontend container remains useful for local and
portable deployments even though the final AWS architecture serves static assets from S3/CloudFront.

## Alternatives considered

- Mocking the recommendation response in Playwright was rejected because it would not validate the
  frontend/API contract or retrieval constraints.
- Running containers as root was rejected because neither application requires elevated privileges.
- Adding curl only for health checks was rejected in favor of Python and BusyBox tools already present.
- A large cross-browser suite was deferred because one principal Chromium journey closes the current
  architectural gap with much lower maintenance cost.

## Tradeoffs and consequences

Playwright adds a browser download to the E2E CI job, so that job is intentionally separate from fast
frontend lint/build checks. The test uses fixed local ports and must run outside restrictive sandboxes
that prohibit binding listeners.

An Nginx container and S3/CloudFront are two frontend delivery options, but they serve distinct needs:
portable/local container execution and the final low-operations AWS deployment.

## Security, reliability, data, and performance

- Both final image stages declare non-root users.
- Health checks cover both services and Compose startup ordering.
- Basic clickjacking, MIME-sniffing, and referrer headers are emitted by Nginx.
- The frontend production dependency audit reports zero known vulnerabilities after the Axios update.
- The browser test verifies every returned item has known nutrition and satisfies both submitted
  constraints.

## Verification

Verified:

- Python lint, formatting, type checking, and all backend tests
- Frontend lint and production build
- Docker Compose configuration parsing
- Production-only npm dependency audit with zero vulnerabilities
- Playwright against real FastAPI and Vite servers: one passing Chromium journey

Pending:

- `docker compose build`
- Container user inspection and health-state verification after startup

The pending checks require a running local Docker daemon. This record must change to `Complete` only
after those commands pass.

## Known limitations and risks

- Only Chromium is covered.
- The test validates the primary successful path, not every error or responsive-layout state.
- The production frontend URL is build-time configuration, so deployments must build per environment.
- Image base tags are pinned by runtime family rather than immutable digest; CI/CD should record image
  digests in the deployment revision.

## Follow-up work

Start Docker, build both images, inspect their configured users, start Compose, wait for healthy status,
and smoke-test the public endpoints. Then mark this record complete and begin Terraform-defined AWS
delivery.

## Affected files

- `backend/Dockerfile`, `backend/.dockerignore`
- `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/playwright.config.js`
- `frontend/tests/e2e/`, `frontend/package.json`, `frontend/package-lock.json`
- `docker-compose.yml`, `Makefile`, `.github/workflows/ci.yml`, `.gitignore`, `README.md`
