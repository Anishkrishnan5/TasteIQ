# TasteIQ Internal Architecture and Delivery Plan

**Status:** Working design  
**Audience:** Project contributors  
**Last updated:** 2026-08-14

This document defines the intended end-to-end architecture for TasteIQ and the order in which it should be built. It is an internal implementation plan, not a statement that every component already exists.

Completed work is recorded separately in the [implementation log](implementation/README.md). Every delivery part must add or update an implementation record describing what changed, why it changed, its effect on the end-to-end system, alternatives considered, tradeoffs, verification, risks, and follow-up work. This architecture document remains the forward-looking design; implementation records are the historical evidence of how that design evolves.

## 1. Objective

TasteIQ should become an explainable, personalized meal-ranking platform that converts natural-language intent and explicit constraints into grounded recommendations from real menu data.

The system should demonstrate two complementary areas of engineering:

1. **Retrieval and recommendation engineering:** query understanding, lexical and semantic retrieval, reranking, personalization, diversity, grounded explanations, and offline evaluation.
2. **Software and systems engineering:** durable data modeling, asynchronous ingestion, caching, reliability, service contracts, performance measurement, observability, security, CI/CD, and benchmark-driven optimization.

The project must not add infrastructure solely to increase the number of technologies used. Each component must improve relevance, reliability, operability, or measured performance.

## 2. Product scope

### 2.1 Primary user journey

1. A user enters a request such as “spicy vegetarian dinner under 700 calories.”
2. TasteIQ extracts semantic intent and structured constraints.
3. Hard dietary and nutrition constraints are enforced.
4. Multiple retrievers generate candidates.
5. Candidates are fused, reranked, personalized, and diversified.
6. The API returns menu items with explanations supported by known metadata.
7. The user can save, like, dislike, or skip results.
8. Interaction events improve later rankings without silently changing hard constraints.

### 2.2 Initial non-goals

- Restaurant ordering and payment
- Delivery logistics
- Medical or clinical nutrition advice
- Automatically claiming an item is allergen-safe when source data is incomplete
- Kubernetes before operational requirements justify it
- A large microservice topology
- A Rust or Go rewrite without measured need

## 3. System invariants

These rules should guide every design and implementation decision:

1. Hard exclusions must never be relaxed by a learned model.
2. Unknown nutrition or ingredient data must remain unknown.
3. Every returned explanation must be supported by source metadata or an explicit ranking feature.
4. Duplicate menu items must not appear in a result set.
5. A failed index build must never replace the active index.
6. Search should degrade safely when caches or optional model stages fail.
7. Dataset, index, model, feature, and ranker versions must be traceable.
8. Every optimization must be evaluated against a reproducible baseline.
9. User feedback must be recorded as immutable events before being transformed into preference features.
10. Personally sensitive preferences must not be unnecessarily included in logs.

## 4. Current system

### 4.1 Runtime flow

```text
Browser
  │
  ▼
React application
  │ POST /api/recommendations
  ▼
FastAPI
  │
  ▼
BM25 lexical retriever
  ├── JSONL catalog
  └── SQLite enrichment
  │
  ▼
JSON response
```

### 4.2 Current strengths

- Complete local request path
- Grounded menu records
- Deterministic behavior
- Input validation
- Simple Docker setup
- Presentable user interface
- A baseline that future rankers can be compared against

### 4.3 Current gaps

- The runtime catalog is deduplicated, but metadata coverage remains low.
- Runtime retrieval is BM25 lexical search rather than vector or hybrid search.
- Natural-language constraints are not parsed into structured filters.
- Calorie and protein filters are exposed; dietary metadata is not yet trustworthy enough to filter.
- A first 34-query relevance benchmark exists; it remains small and single-reviewer.
- There are no user accounts, profiles, or interaction events.
- SQLite and JSONL are acting as runtime stores without migrations or provenance.
- There is no cache, job queue, tracing, production deployment, or CI pipeline.
- There is not yet a supported vector-index build or query path.

## 5. Target system context

```text
                                      ┌────────────────────┐
                                      │   Web application  │
                                      │ React + TypeScript │
                                      └──────────┬─────────┘
                                                 │ HTTPS/JSON
                                      ┌──────────▼─────────┐
                                      │     API service    │
                                      │ Python + FastAPI   │
                                      └───┬────┬───────┬───┘
                                          │    │       │ gRPC
                                  ┌───────▼┐ ┌─▼────┐  ▼
                                  │Postgres│ │Redis │ ┌──────────────────┐
                                  │        │ │      │ │ Retrieval service│
                                  └────────┘ └──────┘ │ Python, then Rust│
                                                       └─────────┬────────┘
                                                                 │ candidates
                                                       ┌─────────▼────────┐
                                                       │ Model/rank layer │
                                                       │ Python inference│
                                                       └──────────────────┘

 External sources ──► durable queue ──► ingestion workers
                                            │
                                            ├──► PostgreSQL
                                            └──► object storage/index registry

 All services ──► OpenTelemetry ──► metrics, traces, and structured logs
```

### 5.1 Deployment units

The target has three application deployment units:

1. **API service:** HTTP boundary, identity, user state, request orchestration, and response construction.
2. **Worker service:** ingestion, enrichment, embeddings, evaluation jobs, and index construction.
3. **Retrieval service:** deterministic candidate generation and filtering; extracted from Python only when benchmarks justify it.

PostgreSQL, Redis, object storage, and the job queue should be managed infrastructure in production and containers or lightweight substitutes locally.

## 6. Online recommendation flow

### 6.1 Request contract

The future request should separate free text from explicit filters:

```json
{
  "query": "spicy vegetarian dinner with lots of protein",
  "limit": 10,
  "filters": {
    "max_calories": 700,
    "min_protein_g": 25,
    "diet": ["vegetarian"],
    "excluded_ingredients": ["peanut"]
  },
  "context": {
    "meal": "dinner"
  }
}
```

Explicit request fields take precedence over values inferred from text. A conflict should either use the stricter safe value or return a validation prompt; it must not be silently resolved in a less restrictive direction.

### 6.2 Request sequence

```text
Client       API       Postgres      Redis      Retriever      Reranker
  │           │            │           │             │             │
  │ request   │            │           │             │             │
  ├──────────►│ validate   │           │             │             │
  │           ├───────────►│ profile   │             │             │
  │           │◄───────────┤           │             │             │
  │           │ parse and merge constraints          │             │
  │           ├──────────────────────►│ cache lookup │             │
  │           │◄──────────────────────┤              │             │
  │           │ cache miss            │              │             │
  │           ├─────────────────────────────────────►│ candidates  │
  │           │◄─────────────────────────────────────┤             │
  │           ├───────────────────────────────────────────────────►│
  │           │◄───────────────────────────────────────────────────┤
  │           │ personalize, diversify, explain                    │
  │           ├───────────►│ record impression                     │
  │           ├──────────────────────►│ cache safe response        │
  │ response  ◄────────────┤           │                            │
```

### 6.3 Stage behavior

#### Stage A: validation and identity

- Validate payload size, field types, ranges, and supported enumerations.
- Resolve an authenticated user or anonymous session.
- Attach a request ID and trace context.
- Create an absolute request deadline.

#### Stage B: query understanding

- Normalize casing, units, punctuation, and common food aliases.
- Parse calories, macronutrients, meal type, cuisines, diets, exclusions, and qualitative intent.
- Preserve both the original query and normalized representation.
- Use deterministic parsing first.
- Add an LLM or classifier only as a measured fallback for ambiguous language.

Example intermediate representation:

```json
{
  "original_query": "spicy vegetarian dinner under 700 calories",
  "semantic_query": "spicy vegetarian dinner",
  "hard_filters": {
    "max_calories": 700,
    "diet": ["vegetarian"]
  },
  "soft_features": {
    "spicy": 1.0,
    "meal:dinner": 1.0
  },
  "parser_version": "rules-v1"
}
```

#### Stage C: cache lookup

Cache keys must include every input that can affect ranking:

```text
index_version + ranker_version + normalized_query + filters + preference_version + limit
```

Personalized and anonymous responses require different cache policies. A Redis failure must be treated as a cache miss.

#### Stage D: hard filtering

- Apply supported dietary and ingredient exclusions before learned reranking.
- Distinguish `known safe`, `known violation`, and `unknown`.
- Define product behavior for unknown values explicitly.
- Use restrictive database/index predicates to avoid retrieving obviously invalid candidates.

#### Stage E: candidate generation

Generate independent candidate lists:

- BM25 for exact and lexical relevance
- Dense vector retrieval for semantic recall
- Optional popularity or collaborative candidates after feedback volume exists

Retrieve more candidates than the final result count. An initial budget could be 50 lexical and 50 dense candidates, deduplicated before fusion.

#### Stage F: rank fusion

Use Reciprocal Rank Fusion as the first hybrid algorithm:

```text
RRF(document) = Σ 1 / (k + rank_in_source)
```

RRF is preferred initially because lexical and vector raw scores are not directly comparable. The constant and candidate counts must be configuration values included in the ranker version.

#### Stage G: cross-encoder reranking

- Rerank only the top fused candidates.
- Batch query-document pairs.
- Enforce a short deadline.
- Record inference duration, batch size, model version, and timeout status.
- Fall back to fused ranking on timeout or service failure.

#### Stage H: personalization

Initial personalization should use interpretable features:

- Cuisine affinity
- Ingredient affinity or aversion
- Restaurant affinity
- Nutrition-goal compatibility
- Prior likes, dislikes, saves, and skips
- Repetition penalty
- Novelty preference

Begin with a weighted scoring layer. Only introduce learning-to-rank after enough high-quality interaction data or a defensible simulated dataset exists.

#### Stage I: diversity

Apply explicit restaurant, cuisine, or near-duplicate caps, or use Maximal Marginal Relevance. Diversity must not reintroduce candidates that violate hard constraints.

#### Stage J: explanations

Construct an evidence object before natural-language wording:

```json
{
  "menu_item_id": "item_123",
  "reasons": [
    {"type": "protein", "value": 32, "unit": "g"},
    {"type": "calorie_limit", "value": 540, "limit": 600},
    {"type": "preference", "feature": "spicy_chicken"}
  ]
}
```

The client-facing explanation must be derived only from this evidence. If a generative model is used for wording, its output must be validated against the evidence object.

#### Stage K: impression recording

Record what the user was shown, not just what they clicked. Each impression should include:

- Request/session/user identifiers
- Ordered result IDs
- Dataset, index, and ranker versions
- Parsed constraints
- Whether fallback paths were used
- Timestamp

The response should not fail merely because analytics event persistence fails. Delivery can be asynchronous after durable local acceptance.

## 7. Feedback flow

Supported events:

- `result_clicked`
- `result_saved`
- `result_liked`
- `result_disliked`
- `result_skipped`
- `search_reformulated`

Every event must reference the impression that produced it. Events are append-only facts; derived preference aggregates can be rebuilt.

```text
Client event → API validation → interaction_events table/queue
                                      │
                                      ▼
                              preference aggregation
                                      │
                                      ▼
                              versioned user features
```

Do not infer strong negative preference from a single non-click. Explicit dislikes should carry more weight than passive skips.

## 8. Data model

The initial PostgreSQL schema should favor clarity and provenance over premature abstraction.

### 8.1 Core entities

#### `users`

- `id`
- `external_identity_id`
- `created_at`
- `updated_at`

#### `user_preferences`

- `user_id`
- `preference_type`
- `preference_key`
- `weight`
- `source` (`explicit`, `inferred`)
- `version`
- timestamps

#### `dietary_restrictions`

- `user_id`
- `restriction_type`
- `restriction_value`
- `severity`
- timestamps

#### `restaurants`

- `id`
- `source`
- `source_restaurant_id`
- normalized name and location fields
- timestamps

#### `menu_items`

- `id`
- `restaurant_id`
- `source`
- `source_item_id`
- `name`
- `description`
- `price`
- `currency`
- `active`
- `source_updated_at`
- timestamps

Use a unique constraint on `(source, source_item_id)`.

#### `ingredients`

- `id`
- normalized name
- allergen categories

#### `menu_item_ingredients`

- `menu_item_id`
- `ingredient_id`
- source confidence
- provenance

#### `nutrition_facts`

- `menu_item_id`
- calories, protein, carbohydrates, and fat
- serving size and unit
- source and confidence
- source timestamp

#### `interaction_events`

- `id`
- `user_id` or anonymous session ID
- `impression_id`
- `menu_item_id`
- event type
- event metadata
- timestamp

#### `search_impressions`

- `id`
- user/session ID
- original and normalized query
- parsed filters
- ordered results
- dataset/index/model/ranker versions
- latency and fallback summary
- timestamp

#### `ingestion_jobs`

- `id`
- source
- job type and status
- attempt count
- cursor/checkpoint
- failure summary
- timestamps

#### `index_versions`

- `id`
- dataset version
- artifact URI and checksum
- document count and vector dimensions
- embedding model version
- validation report
- status (`building`, `validated`, `active`, `failed`, `retired`)
- timestamps

### 8.2 Migration rules

- Use Alembic and commit every migration.
- Test upgrades from the last released schema.
- Prefer backward-compatible expand/migrate/contract changes for deployed services.
- Do not combine irreversible data destruction with an application rollout.
- Backfills must be restartable and observable.

## 9. Offline ingestion and index lifecycle

### 9.1 Ingestion stages

1. Fetch a page or batch from a source.
2. Store raw source payload and provenance.
3. Validate its schema.
4. Normalize units, names, and categories.
5. Deduplicate by source ID and conservative entity matching.
6. Enrich nutrition, ingredients, and restaurant metadata.
7. Upsert normalized entities in one bounded transaction.
8. Emit quality metrics and advance the durable checkpoint.

### 9.2 Job semantics

- Jobs must be idempotent.
- Queue delivery may be at least once.
- External calls use bounded concurrency and exponential backoff with jitter.
- Retry only transient failures.
- Invalid records go to quarantine with a reason.
- Workers acknowledge jobs only after durable completion.
- A job stores enough checkpoint state to resume after restart.

### 9.3 Index build

1. Select a consistent dataset version.
2. Export canonical retrieval documents.
3. Generate embeddings in deterministic batches.
4. Build lexical and vector indexes.
5. Write artifacts to a temporary versioned location.
6. Compute checksums and a manifest.
7. Run structural and retrieval quality checks.
8. Mark the version `validated`.
9. Activate through one atomic registry update.
10. Notify retrieval instances to load the version.
11. Keep the previous known-good version available for rollback.

### 9.4 Index manifest

```json
{
  "index_version": "idx_2026_08_01_001",
  "dataset_version": "data_2026_08_01_001",
  "document_count": 500000,
  "embedding_model": "model-name-and-revision",
  "dimensions": 768,
  "bm25_config": {"k1": 1.2, "b": 0.75},
  "artifacts": [
    {"path": "bm25.bin", "sha256": "..."},
    {"path": "vectors.bin", "sha256": "..."},
    {"path": "metadata.bin", "sha256": "..."}
  ]
}
```

## 10. Retrieval service boundary

### 10.1 Start in Python

The first hybrid retriever should be a typed Python module behind an interface such as:

```python
class Retriever:
    def search(self, request: RetrievalRequest) -> RetrievalResponse:
        ...
```

This keeps algorithm development fast and creates the functional contract for future implementations.

### 10.2 Extraction criteria

Extract retrieval into a separate process only when at least one is true:

- Candidate generation consumes a material portion of the p95 latency budget.
- Index memory pressure interferes with API/model processes.
- Retrieval needs to scale independently.
- Atomic index loading is operationally safer in a separate process.
- Failure isolation provides measurable availability value.

### 10.3 Rust decision gate

Implement a Rust prototype only after the Python baseline has:

- A stable contract
- A representative corpus
- A reproducible load generator
- CPU and memory profiles
- p50, p95, and p99 measurements
- Defined correctness and ranking-equivalence tests

Keep Rust if it demonstrates a meaningful improvement in tail latency, throughput, memory, or operational isolation after including serialization and network overhead.

Go is not currently planned. Adding Python, Rust, and Go would increase operational and cognitive cost without a distinct third responsibility.

### 10.4 Proposed gRPC contract

```protobuf
service RetrievalService {
  rpc Search(SearchRequest) returns (SearchResponse);
  rpc GetIndexStatus(IndexStatusRequest) returns (IndexStatusResponse);
}

message SearchRequest {
  string request_id = 1;
  string semantic_query = 2;
  Filters filters = 3;
  uint32 lexical_candidates = 4;
  uint32 vector_candidates = 5;
  uint32 result_limit = 6;
  string required_index_version = 7;
}

message Candidate {
  string menu_item_id = 1;
  float fused_score = 2;
  uint32 lexical_rank = 3;
  uint32 vector_rank = 4;
}
```

Deadlines and trace context must propagate across the gRPC boundary. The API must reject responses from an unexpected index version when strict reproducibility is requested.

## 11. Caching

### 11.1 Candidate caches

- Normalized query embedding cache
- Anonymous fused-candidate cache
- Menu-item projection cache
- User preference snapshot cache

### 11.2 Invalidation

Prefer versioned keys over broad deletion:

```text
recommendation:{index_version}:{ranker_version}:{query_hash}:{filter_hash}
```

Activating a new index naturally changes the namespace. Old entries expire through bounded TTLs.

### 11.3 Cache safety

- Never share personalized responses between users.
- Do not cache authorization failures.
- Cache negative results briefly to prevent repeated expensive misses.
- Record hit, miss, bypass, and error separately.
- Redis unavailability must not make search unavailable.

## 12. Reliability model

### 12.1 Time budget

An initial 500 ms request deadline can be divided approximately as follows:

| Stage | Budget |
|---|---:|
| Validation and identity | 15 ms |
| Profile and metadata lookup | 30 ms |
| Query understanding | 35 ms |
| Candidate retrieval | 100 ms |
| Cross-encoder reranking | 180 ms |
| Personalization/diversity/explanation | 60 ms |
| Serialization and network reserve | 80 ms |

Budgets are provisional until measured. Downstream stages must receive the remaining deadline rather than independent full timeouts.

### 12.2 Degradation matrix

| Failure | Behavior | User impact |
|---|---|---|
| Redis unavailable | Bypass cache | Higher latency |
| Vector index unavailable | BM25 only | Lower semantic recall |
| Retrieval service unavailable | Local fallback during migration, otherwise controlled 503 | Possible reduced availability |
| Reranker timeout | Use fused candidates | Lower precision |
| Explanation model unavailable | Deterministic explanations | Less natural wording |
| Analytics unavailable | Buffer or drop noncritical event with metric | No search impact |
| New index validation failure | Retain active index | Stale but valid results |
| PostgreSQL unavailable | Serve safe anonymous/cache path if possible | No profile updates |

### 12.3 Retry rules

- Never automatically retry non-idempotent writes without an idempotency key.
- Do not retry validation or authorization failures.
- Limit retries by the request deadline.
- Use exponential backoff with jitter for asynchronous work.
- Track retry count and final outcome.

### 12.4 Backpressure

- Bound worker and inference concurrency.
- Use finite queues.
- Reject excess work quickly instead of allowing unbounded latency.
- Decrease reranker candidate count under controlled load shedding if quality tests support it.
- Export saturation metrics for connection pools, worker pools, and inference batches.

## 13. Performance and capacity plan

### 13.1 Initial SLO candidates

- Cached request p50 below 75 ms
- Normal recommendation p95 below 250 ms
- Recommendation p99 below 500 ms
- Availability of 99.9% after production hardening
- Zero known hard-constraint violations

These are objectives, not current claims.

### 13.2 Benchmark methodology

Every published benchmark must record:

- Git revision
- Dataset and index versions
- Corpus size
- Hardware and operating environment
- Warm-up procedure
- Concurrency and request distribution
- Cache state
- Duration and sample count
- p50, p95, p99, throughput, and error rate
- CPU, memory, and downstream saturation

### 13.3 Workloads

- Exact lexical searches
- Semantic searches
- Multi-filter requests
- Personalized requests
- Cache-heavy traffic
- Cold-cache traffic
- Index reload during traffic
- Reranker slowdown and outage
- Burst traffic above steady-state capacity

### 13.4 Profiling order

1. Measure end-to-end latency.
2. Use traces to identify the dominant stage.
3. Profile that stage for CPU, allocation, I/O, and lock contention.
4. Make one controlled change.
5. Repeat the identical workload.
6. Record quality regressions as well as speed improvements.

## 14. Retrieval evaluation plan

### 14.1 Evaluation dataset

Create a versioned benchmark containing queries, hard constraints, relevance judgments, and expected failure behavior. Include:

- Exact item names
- Restaurant and cuisine requests
- Ingredients and exclusions
- Nutrition goals
- Dietary restrictions
- Vague semantic cravings
- Multi-intent requests
- Misspellings and synonyms
- No-result cases
- Adversarial constraint combinations

### 14.2 Metrics

- Recall@K
- Precision@K
- Mean Reciprocal Rank
- nDCG@K
- Constraint-violation rate
- Duplicate-result rate
- Diversity by restaurant/cuisine/item similarity
- Empty-result rate
- Coverage of explanation evidence

### 14.3 Experiment record

Each experiment should save:

- Baseline and candidate configurations
- Dataset and judgment versions
- Aggregate metrics
- Per-query differences
- Latency and compute cost
- Decision and rationale

No new ranker should ship solely because aggregate relevance improves if it introduces hard-constraint regressions or violates the latency budget.

## 15. Observability

### 15.1 Tracing

Use OpenTelemetry from the browser-visible request through:

- API middleware
- Database calls
- Redis calls
- Retrieval RPC
- Lexical/vector stages
- Reranker inference
- Event publication

Trace attributes should include safe version and operational fields, not raw sensitive preferences.

### 15.2 Metrics

#### API

- Request count, latency, and status
- Active requests
- Validation failures
- Rate-limit decisions
- Degraded-mode responses

#### Retrieval

- Lexical/vector/fusion latency
- Candidate counts
- Empty results
- Active index version
- Index load duration and failures

#### Models

- Inference latency
- Batch size
- Queue time
- Timeout and fallback rates
- Model version

#### Data pipeline

- Records fetched, accepted, deduplicated, and quarantined
- Job duration and retries
- Enrichment coverage
- Index build and validation outcomes

#### Infrastructure

- CPU and memory
- Database connections and query latency
- Redis hit rate and errors
- Queue depth and oldest-message age

### 15.3 Logging

- Emit structured JSON in deployed environments.
- Include timestamp, severity, service, environment, request ID, trace ID, and version fields.
- Redact authorization data and avoid raw health or allergy preferences.
- Log one clear terminal event per request rather than many redundant messages.

## 16. Security and privacy

- Use OIDC for identity rather than storing passwords directly.
- Enforce authorization server-side.
- Keep secrets in a managed secret store and out of images, logs, and Git.
- Use parameterized SQL and strict request schemas.
- Limit request sizes and apply rate limits.
- Run containers as non-root with minimal images.
- Scan dependencies and container images in CI.
- Encrypt production traffic and managed data stores.
- Define retention periods for queries and interaction events.
- Allow users to delete stored preferences and interaction history.
- Treat allergy information as sensitive and never infer safety from missing data.

## 17. Testing plan

### 17.1 Unit tests

- Query normalization and parsing
- Filter semantics, including unknown metadata
- Deduplication
- BM25/vector fusion
- Personalization features
- Diversity rules
- Explanation evidence validation
- Cache-key construction

### 17.2 Property-based tests

- Adding a hard restriction never increases violating results.
- Deduplication always produces unique result IDs.
- RRF output contains only source candidates.
- Cache keys differ when any ranking-relevant input differs.
- Results are deterministic for a fixed version and configuration.

### 17.3 Integration tests

- API with PostgreSQL and Redis
- Migration upgrade path
- Worker idempotency and resume behavior
- Index build, validation, activation, and rollback
- API/retrieval protobuf compatibility
- Timeouts and fallback behavior

### 17.4 End-to-end tests

- Anonymous search
- Filtered search
- Account preference update
- Feedback event recording
- Degraded search without Redis
- Reranker timeout fallback

### 17.5 Load and failure tests

- SLO checks at target concurrency
- Soak test for leaks or degradation
- Index hot-swap during traffic
- Database/Redis/model latency injection
- Worker retry and dead-letter behavior

## 18. Local development environment

Docker Compose should eventually provide:

- Web application
- API service
- Worker
- Retrieval service when extracted
- PostgreSQL
- Redis
- Queue emulator or broker
- OpenTelemetry collector
- Prometheus and Grafana

Local development must retain a fast path. Contributors should not need the full observability stack to change UI copy or a ranking function.

Recommended commands should converge on:

```text
make bootstrap
make dev
make test
make lint
make eval
make load-test
```

## 19. CI/CD and environments

### 19.1 Environments

- **Local:** Docker Compose and seeded fixtures
- **CI:** ephemeral dependencies and deterministic tests
- **Staging:** production-like contracts with smaller capacity
- **Production:** managed data services, controlled rollout, and alerts

### 19.2 Pull-request pipeline

1. Formatting and linting
2. Type checking
3. Unit tests
4. Integration tests
5. Retrieval regression suite
6. Frontend build and end-to-end smoke test
7. Container build
8. Dependency, secret, and image scanning
9. Migration compatibility checks

### 19.3 Deployment pipeline

1. Build immutable images tagged with the Git revision.
2. Publish signed artifacts.
3. Apply reviewed Terraform changes.
4. Deploy database-compatible application changes to staging.
5. Run smoke and contract tests.
6. Roll out production with readiness gates.
7. Monitor SLO and error signals.
8. Automatically or manually roll back on defined thresholds.

Indexes are deployed separately from application code and must follow their own validation and activation process.

## 20. Cloud topology

Use a managed container platform initially rather than Kubernetes. A representative AWS mapping is:

- Frontend: S3 and CloudFront
- API, worker, retrieval: ECS Fargate
- Database: RDS PostgreSQL
- Cache: ElastiCache Redis
- Queue: SQS
- Index artifacts: S3
- Secrets: Secrets Manager
- Telemetry: OpenTelemetry collector plus a compatible backend
- Infrastructure: Terraform

Equivalent GCP or Azure services are acceptable. Provider selection should be documented in an architecture decision record based on cost, operational complexity, and learning goals.

## 21. Repository organization

The target structure can evolve toward:

```text
TasteIQ/
├── frontend/                 # React + TypeScript client
├── backend/
│   ├── api/                  # HTTP routes and schemas
│   ├── application/          # use cases and orchestration
│   ├── domain/               # ranking and preference concepts
│   ├── infrastructure/       # database, cache, queues, clients
│   ├── retrieval/            # Python baseline and interfaces
│   ├── workers/              # ingestion and index jobs
│   ├── migrations/
│   └── tests/
├── retrieval-rs/            # optional benchmark-justified Rust service
├── contracts/               # protobuf/OpenAPI artifacts
├── evaluation/              # judgments, runner, reports
├── load-tests/
├── infrastructure/          # Terraform and deployment config
├── observability/            # dashboards and collector config
├── docs/
│   ├── architecture-plan.md
│   └── adr/
└── docker-compose.yml
```

Do not reorganize everything in one commit. Move code as each boundary receives tests and a clear owner.

## 22. Delivery plan

Each phase should end in a demonstrable, tested state. Advanced work must not block improvements to the existing MVP.

### Phase 0: protect the baseline

**Goal:** make the current state reproducible before architectural changes.

Tasks:

1. Remove or archive duplicate backup code and generated OS files.
2. Keep the current runtime dataset in Git while excluding generated vector-index artifacts.
3. Pin all runtime and development dependencies.
4. Add a single documented bootstrap command.
5. Add GitHub Actions for current backend and frontend checks.
6. Add representative retrieval fixtures and snapshot current behavior.
7. Record current data coverage and duplicate counts.

Exit criteria:

- A clean clone can build and test without undocumented steps.
- CI is green.
- The current ranking baseline is reproducible.
- No unowned duplicate runtime paths remain.

### Phase 1: trustworthy data and API

**Goal:** fix correctness and data quality before adding models.

Tasks:

1. Remove the nutrition-presence relevance bonus that admits unrelated results.
2. Define exact semantics for unknown nutrition under filters.
3. Deduplicate the catalog at ingestion rather than only at response time.
4. Add data validation and a coverage report.
5. Expose filters in the UI.
6. Replace development-only endpoints and hard-coded version values.
7. Add structured errors, request IDs, and per-stage timers.
8. Define versioned API response schemas.

Exit criteria:

- Irrelevant zero-overlap results no longer appear.
- Duplicate-result and constraint tests pass.
- Data quality is reported automatically.
- UI and API support the same filter model.

### Phase 2: PostgreSQL and event foundation

**Goal:** introduce durable product state and migrations.

Tasks:

1. Implement the core PostgreSQL schema.
2. Add Alembic migrations.
3. Import the cleaned dataset idempotently.
4. Add repository interfaces so ranking logic is storage-independent.
5. Record anonymous search impressions.
6. Add interaction event endpoints.
7. Add integration tests with ephemeral PostgreSQL.

Exit criteria:

- Menu and interaction data survive restarts.
- Migrations work from a clean database and the prior schema.
- Re-running ingestion does not create duplicates.
- Every feedback event can be tied to an impression.

### Phase 3: evaluation-first hybrid retrieval

**Goal:** improve relevance with measurable evidence.

Tasks:

1. Create and review the first labeled query set.
2. Implement metric calculation and per-query reports.
3. Add a proper BM25 baseline.
4. Add local dense embeddings and vector retrieval.
5. Add RRF and configurable candidate budgets.
6. Connect the hybrid retriever to the API behind a feature flag.
7. Compare quality, latency, and memory against token overlap.

Exit criteria:

- Evaluation can be run with one command.
- Hybrid search beats the baseline on agreed relevance metrics.
- Hard-constraint violations remain zero.
- Index/model/config versions appear in results and telemetry.

### Phase 4: reranking, explanations, and graceful degradation

**Goal:** improve top-result precision without making models a single point of failure.

Tasks:

1. Select and evaluate a cross-encoder.
2. Batch the top candidate pairs.
3. Add deadlines, cancellation, and fused-ranking fallback.
4. Implement diversity rules.
5. Create structured explanation evidence.
6. Add deterministic explanations.
7. Add failure-injection and latency regression tests.

Exit criteria:

- Reranking improves nDCG/MRR by an agreed threshold.
- p95 remains within the provisional budget.
- Reranker failure produces valid degraded results.
- Explanation validation prevents unsupported claims.

### Phase 5: personalization

**Goal:** use explicit and observed preferences responsibly.

Tasks:

1. Add OIDC authentication.
2. Add explicit taste preferences and restrictions.
3. Build versioned preference aggregates from events.
4. Add interpretable personalization features.
5. Add repetition penalties and novelty controls.
6. Evaluate personalized ranking using offline replay or a documented simulation.
7. Provide preference/history deletion.

Exit criteria:

- User-specific results are isolated and reproducible.
- Explicit restrictions override inferred preferences.
- Preference features have explainable weights and versions.
- Personalization can be disabled independently.

### Phase 6: caching, jobs, and index operations

**Goal:** establish scalable operational behavior.

Tasks:

1. Add Redis with versioned keys and bypass fallback.
2. Add the durable job queue and workers.
3. Move ingestion and index building behind job contracts.
4. Store versioned index artifacts and manifests.
5. Implement validation, atomic activation, hot loading, and rollback.
6. Add queue, cache, and index operational metrics.

Exit criteria:

- Redis outage does not cause search outage.
- Jobs resume safely after worker termination.
- An invalid index cannot become active.
- A previous index can be restored without rebuilding.

### Phase 7: performance and Rust decision

**Goal:** profile the mature path and optimize the demonstrated bottleneck.

Tasks:

1. Build representative load and corpus scaling tools.
2. Establish end-to-end and per-stage baselines.
3. Profile CPU, allocations, I/O, and memory.
4. Optimize Python and configuration first.
5. Freeze the retrieval contract and correctness suite.
6. Build a Rust retrieval prototype if extraction criteria are met.
7. Benchmark Python and Rust including RPC overhead.
8. Document the keep/reject decision in an ADR.

Exit criteria:

- Benchmarks are reproducible from the repository.
- SLOs reflect actual measurements.
- Rust exists in the production architecture only if evidence supports it.
- Ranking equivalence or intentional differences are documented.

### Phase 8: observability and cloud deployment

**Goal:** operate the system safely in a production-like environment.

Tasks:

1. Complete OpenTelemetry instrumentation.
2. Add dashboards and alerts tied to SLO symptoms.
3. Container-harden every service.
4. Provision staging infrastructure with Terraform.
5. Add CI/CD, smoke tests, and rollback.
6. Run load, soak, and failure tests in staging.
7. Deploy a cost-bounded production environment.
8. Publish an architecture diagram, benchmark report, and operational demo.

Exit criteria:

- Infrastructure can be recreated from code.
- A trace explains a recommendation request end to end.
- Alerts detect injected latency and error failures.
- Deployment and rollback are documented and tested.

## 23. Architecture decision records

Create short ADRs under `docs/adr/` as decisions are made. Initial candidates:

1. PostgreSQL as the source of truth
2. Modular monolith before service extraction
3. BM25 plus dense retrieval with RRF
4. Hard constraints outside learned ranking
5. Versioned immutable index artifacts
6. Redis as optional acceleration
7. Managed containers before Kubernetes
8. Rust retrieval extraction decision
9. Cloud provider and deployment topology
10. Interaction event and retention model

Each ADR should contain context, decision, alternatives, consequences, and evidence.

## 24. Open decisions

The following should be resolved during their relevant phase rather than guessed now:

- Exact policy for missing allergen and nutrition data
- Authentication provider
- Job queue implementation
- Vector index implementation and embedding model
- Cross-encoder model and serving approach
- Anonymous-event retention period
- Cloud provider and monthly cost ceiling
- Minimum benchmark improvement required to keep Rust
- Whether impression events require a queue at initial traffic levels

## 25. Definition of project success

TasteIQ is successful when the repository demonstrates, with evidence, that:

- Recommendations improve over a documented baseline.
- Hard constraints are enforced reliably.
- Data and index builds are reproducible and reversible.
- The system remains useful during optional-component failures.
- Latency and capacity are measured under realistic load.
- Production behavior can be diagnosed through traces and metrics.
- Infrastructure and deployments are reproducible.
- Every major architectural choice has a clear tradeoff and justification.

That combination—not the number of models, languages, or cloud services—is the intended SWE signal.
