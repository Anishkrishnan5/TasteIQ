# Phase 0A: Repository Hygiene

**Status:** Complete  
**Date:** 2026-08-01  
**Related phase:** Phase 0 — Protect the baseline

## Outcome

The repository now has one clear active backend, one authoritative runtime database path, explicit separation between source code and generated retrieval artifacts, smaller Docker build contexts, and internal documentation separated from the public project introduction.

This part intentionally did not change recommendation behavior. Its purpose was to reduce ambiguity and protect the baseline before data, retrieval, persistence, or service architecture changes begin.

## Starting state

The application had a functional React-to-FastAPI request path, but the repository mixed active code with historical and generated material:

- `backend_backup/` contained an obsolete requirements file, empty tracked Python modules, an ignored environment file, and a 292 MB local virtual environment.
- Both `backend/tasteiq.db` and `backend/database/tasteiq.db` existed; the first was empty and the second was the actual runtime database.
- macOS `.DS_Store` files were tracked.
- Two incompatible FAISS build approaches and a generated index were present but disconnected from the runtime API.
- FAISS, NumPy, Sentence Transformers, and OpenAI dependencies required by those scripts were absent from the runtime requirements.
- Several packages contained empty placeholder modules that implied functionality that did not exist.
- Starter Vite assets remained despite not being used by the application.
- Docker build contexts did not explicitly exclude virtual environments, caches, tests, secrets, or generated artifacts.
- API exploration notes existed as an untracked root-level scratch file.
- The public README contained too much forward-looking architecture detail for a project introduction.

The repository also had an incomplete local backend virtual environment. The declared test dependency was not installed, which initially prevented the backend suite from running.

## Changes made

### Removed obsolete tracked content

The following categories were removed from the active tree:

- The tracked `backend_backup/` skeleton
- Root and backend `.DS_Store` files
- The empty duplicate `backend/tasteiq.db`
- Generated `faiss.index` and `faiss_meta.json`
- Disconnected OpenAI and local FAISS build/query scripts
- Empty fine-tuning, embedding, service, query, helper, and dependency placeholders
- Unused React and Vite starter assets

Git history still preserves the tracked material. Local copies of the backup directory and binary artifacts were moved to `/private/tmp` during cleanup rather than being irreversibly deleted.

### Added repository boundaries

The root `.gitignore` now excludes:

- Environment variants while allowing a future `.env.example`
- Operating-system and editor state
- Generated vector-index artifacts
- Local database journals and the obsolete root database path
- Frontend build output

Backend and frontend `.dockerignore` files now keep local dependencies, caches, credentials, test output, and generated artifacts out of their respective Docker build contexts.

### Reorganized documentation

- The root README was reduced to a conventional public introduction, current feature list, setup guide, API example, and honest project status.
- The end-to-end target design was retained in `docs/architecture-plan.md`.
- Historical Spoonacular exploration was converted from `api_notes.md` into `docs/data-source-notes.md`, with an explicit warning that API limits and behavior must be reverified.
- This implementation-log structure was introduced to preserve engineering reasoning for every future part.

### Restored the local test environment

The checked-in backend requirements were installed into the ignored local virtual environment. This added the missing `pytest` and `pydantic-settings` versions required to execute the current suite. No virtual-environment files are tracked.

## System-design impact

### Before

```text
Repository
├── active FastAPI backend
├── obsolete backend backup
├── two database paths
├── runtime-independent vector artifacts
├── empty future-facing modules
└── Docker contexts containing unnecessary local state
```

This structure made ownership ambiguous. A contributor could reasonably mistake the backup, empty database, or FAISS scripts for an active production path.

### After

```text
Repository
├── frontend/                 active React client
├── backend/                  active FastAPI application
│   └── database/
│       ├── rag_items.jsonl   runtime catalog
│       └── tasteiq.db        runtime enrichment database
├── docs/
│   ├── architecture-plan.md  target design
│   ├── data-source-notes.md  historical source observations
│   └── implementation/       completed engineering record
└── docker-compose.yml
```

The online pipeline itself remains:

```text
React → FastAPI → token-overlap retriever → JSONL + SQLite → results
```

Removing disconnected vector artifacts does not remove vector retrieval from the target architecture. It ensures that the future vector path is introduced as a supported, evaluated subsystem rather than as an unverified binary artifact.

## Decisions and reasoning

### Keep the simple retriever as the baseline

The token-overlap implementation remains even though it has known relevance problems. Replacing it during cleanup would combine structural and behavioral changes, making regressions harder to attribute. Phase 0C will measure it; later retrieval work must beat it.

### Remove generated indexes from Git

The checked-in FAISS index lacked a supported runtime path, reproducible dependency set, manifest, model contract, and evaluation report. Generated indexes belong in ignored local storage during development and versioned object storage in the target production architecture.

An index should eventually be identified by:

- Dataset version
- Embedding model and revision
- Dimensions
- Index configuration
- Document count
- Artifact checksums
- Validation report

The removed files did not provide this information reliably.

### Remove rather than preserve empty placeholders

Empty modules create false architectural signals. Python modules should appear when they own implemented behavior and tests. Future ranking, model, and persistence boundaries will be introduced when their contracts are defined.

### Preserve historical data-source findings

The Spoonacular notes contain useful observations about missing metadata, serving inconsistency, enrichment cost, and provenance. They were kept internally but marked historical because third-party API limits and pricing are temporally unstable.

### Preserve local backup material recoverably

The backup contained an ignored environment file that may hold credentials. It was not printed, committed, or destroyed. Moving it outside the active project removed ambiguity while preserving recovery options.

## Alternatives considered

### Keep `backend_backup/` in the repository

Rejected because Git already preserves history, nearly all tracked files were empty, and its obsolete dependencies suggested a second supported backend.

### Move the FAISS experiment to an active `experiments/` directory

Deferred. The two implementations used incompatible embedding providers and lacked a shared contract or dependencies. A future experiment should begin from the Phase 3 retrieval interface and evaluation harness.

### Commit the generated FAISS index

Rejected for the current design. Committing a small index can simplify a demo, but it creates unclear provenance and does not scale to versioned production artifacts. The current token retriever keeps local startup credential-free while the supported index lifecycle is designed.

### Delete all local backup contents permanently

Rejected as unnecessarily destructive. Recoverable moves provide the same repository cleanup without risking credentials or work that had not been independently reviewed.

### Replace SQLite immediately

Rejected for Phase 0A. PostgreSQL is planned, but SQLite is part of the functioning baseline. Persistence migration belongs in a separately tested delivery part.

## Tradeoffs and consequences

### Benefits

- Contributors can identify the active runtime path quickly.
- Docker contexts are smaller and less likely to include credentials or local dependencies.
- Future indexes cannot be mistaken for automatically reproducible artifacts.
- Repository claims more closely match implemented behavior.
- Baseline tests can run in the repaired local environment.
- Historical reasoning remains available without cluttering the public README.

### Costs

- The old FAISS demo can no longer be run directly from the active tree.
- Reintroducing vector retrieval requires a supported dependency and artifact design.
- The cleanup creates many deletion entries in one change.
- Local recoverable copies under `/private/tmp` are temporary and should not be treated as permanent backups.

### Accepted risk

The current token retriever still has known relevance defects. They are intentionally retained until baseline tests and evaluation cases are added, so the behavioral fix is independently reviewable.

## Security, reliability, data, and performance

### Security

- Environment-file patterns are ignored.
- A future `.env.example` remains committable.
- Docker contexts exclude environment files.
- The ignored historical environment file was preserved outside the repository without exposing its values.

If the historical OpenAI or Pinecone keys were ever shared or committed elsewhere, they should be rotated independently of this cleanup.

### Reliability

Runtime code and data were preserved. Backend API tests and frontend build checks verify that removal of disconnected files did not affect the supported path.

### Data

The authoritative current data files remain:

- `backend/database/rag_items.jsonl`
- `backend/database/tasteiq.db`

No menu or nutrition records were rewritten during this part.

### Performance

There is no intended request-latency change. Docker build contexts should transfer less irrelevant data because local virtual environments, frontend dependencies, and caches are excluded.

## Verification

Verification was performed on 2026-08-01 in the local development workspace.

| Check | Result |
|---|---|
| Backend API tests | 5 passed in 0.34 seconds |
| Frontend ESLint | Passed |
| Frontend production build | Passed |
| Docker Compose configuration validation | Passed |
| Git whitespace validation | Passed |
| Runtime JSONL present | Passed |
| Runtime SQLite database present | Passed |
| Active retriever present | Passed |

The first backend test attempt failed because the ignored virtual environment did not contain `pytest`. Installing the declared requirements corrected the environment; the subsequent suite passed.

## Known limitations and risks

- The backend dependency format is still a flat `requirements.txt`.
- There is no lock file or automated CI yet.
- Only five backend tests exist.
- There are no frontend component or end-to-end tests.
- The current retrieval bug can return unrelated enriched items for zero-overlap queries.
- Dataset duplication and metadata coverage remain unresolved.
- Docker images are not yet non-root or health-gated.
- The cleanup is currently uncommitted and should be reviewed as a coherent checkpoint.
- `/private/tmp` recovery copies may be removed by the operating system.

## Follow-up work

### Phase 0B: reproducible tooling

1. Introduce `pyproject.toml` with runtime and development configuration.
2. Add formatting, linting, type checking, and pytest configuration.
3. Add a consistent command interface.
4. Add GitHub Actions for backend and frontend verification.
5. Align documented, CI, Docker, and local Python versions.

### Phase 0C: baseline and data report

1. Replace the broken validation scratch script with a real JSONL/SQLite validator.
2. Quantify duplicates and metadata coverage.
3. Add representative retrieval regression cases.
4. Record current relevance and latency baselines.

## Affected files

Important additions and modifications:

- `.gitignore`
- `README.md`
- `backend/.dockerignore`
- `frontend/.dockerignore`
- `frontend/index.html`
- `docs/architecture-plan.md`
- `docs/data-source-notes.md`
- `docs/implementation/README.md`
- `docs/implementation/00-repository-hygiene.md`

Removed categories:

- `backend_backup/`
- Generated FAISS artifacts and disconnected scripts
- Empty placeholder modules
- Duplicate empty database
- OS metadata and unused starter assets
