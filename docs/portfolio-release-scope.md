# TasteIQ Portfolio Release Scope

**Target release:** `v1.0.0`

**Status:** Scope frozen

**Scope date:** 2026-08-17

## Product statement

TasteIQ is an end-to-end meal-retrieval system that turns natural-language requests and explicit
nutrition constraints into grounded menu recommendations. It demonstrates the complete applied-ML
lifecycle: trustworthy data, reproducible retrieval artifacts, offline evaluation, experiment
tracking, evidence-based promotion, containerized cloud inference, CI/CD, monitoring, and a user
feedback path.

The goal is a credible, operable personal project. It is not intended to imitate the infrastructure
of a large recommendation company.

## Definition of done

TasteIQ is portfolio-complete when all of the following are true.

### Product

- A public user can open the deployed frontend and receive grounded recommendations from the deployed
  API.
- Query correction and explicit calorie/protein filters behave consistently with the documented API.
- Loading, validation, unavailable-service, empty-result, and successful-result paths are usable.
- A lightweight relevance-feedback action is available without collecting unnecessary personal data.

### Data and retrieval

- The runtime catalog is deduplicated, validated, hashed, and covered by a generated quality report.
- BM25 remains the default champion unless a candidate passes the documented relevance and safety
  gates.
- Dense and hybrid retrieval remain reproducible challengers with pinned model and artifact lineage.
- Evaluation includes versioned judgments, per-query results, ranking metrics, constraint safety,
  duplicate rate, no-result behavior, and latency.

### Experiment lifecycle

- Evaluation runs can be logged to MLflow with the Git revision, catalog and judgment versions,
  retriever parameters, metrics, and detailed reports.
- Champion/challenger decisions are explicit and reproducible; an experiment does not deploy merely
  because it completed successfully.
- Local development works without a remote MLflow server or AWS account.

### Quality and delivery

- One command runs backend lint, formatting, type checks, tests, frontend checks, retrieval gates, and
  deployment-configuration validation.
- CI runs those checks on pull requests.
- At least one browser-level test covers the principal search-and-filter journey.
- Production containers run as non-root users and expose health checks.
- The main branch can build immutable images, publish them to Amazon ECR, deploy through Amazon ECS
  Fargate, and perform a post-deployment smoke test.
- AWS infrastructure is defined with Terraform and uses GitHub Actions OIDC rather than stored
  long-lived AWS credentials.

### Operations

- The deployed API emits structured logs with request ID, latency, status, retriever version, catalog
  version, result count, correction status, and fallback status.
- CloudWatch exposes a small dashboard and alarms for availability, server errors, and latency.
- Raw user queries are not included in routine operational logs.
- The project has a documented rollback and artifact-version recovery procedure.
- A small AWS budget alert is configured.

### Portfolio presentation

- The README leads with a screenshot or short demonstration, a live link, the system diagram, and the
  measured BM25-versus-hybrid decision.
- Setup, local evaluation, MLflow usage, deployment architecture, limitations, and operating cost are
  documented honestly.
- The repository has a clean `v1.0.0` release tag and all required checks pass from a clean checkout.

## Final v1 architecture

```text
GitHub Actions ──build/test/evaluate──→ Amazon ECR
       │                                    │
       └──Terraform plan/apply              ▼
                                      ECS Fargate API
React build ──→ S3 + CloudFront             │
                                             ├──→ versioned catalog/index artifacts
Offline evaluation ──→ MLflow Tracking      ├──→ feedback store
                                             └──→ CloudWatch logs, metrics, alarms
```

The default local application continues to use checked-in data and does not require AWS, MLflow, or
the optional embedding dependencies.

## Required tools and why they exist

| Tool | Required v1 responsibility |
|---|---|
| Docker | Reproducible frontend and API packaging |
| GitHub Actions | CI, image publishing, deployment, and smoke testing |
| MLflow | Experiment parameters, metrics, lineage, and comparison artifacts |
| Terraform | Reviewable, reproducible AWS infrastructure |
| Amazon ECR | Immutable container-image storage |
| Amazon ECS Fargate | Managed execution of the API container |
| Amazon S3 and CloudFront | Static frontend delivery and versioned artifacts |
| Amazon CloudWatch | Production logs, service metrics, dashboard, and alarms |

Every required tool owns a real lifecycle responsibility. No tool is included solely as a resume
keyword.

## Explicit v1 non-goals

The following are not required for portfolio completion:

- Kubernetes or Amazon EKS
- Airflow
- Kafka or another event-streaming platform
- Redis
- Spark
- Rust services
- Microservice decomposition
- Online model training
- Custom neural-model training
- Personalization or user accounts
- A feature store
- A vector database
- Multi-region or high-availability architecture
- Automated promotion based on noisy live feedback

They may be considered after `v1.0.0` only when a measured product or operational need justifies them.

## Current position

Already complete:

- Responsive React interface and versioned FastAPI contract
- Strict structured nutrition filters and conservative spelling correction
- Deduplicated 448-record catalog with data-quality reporting
- BM25, dense, and RRF hybrid retrieval implementations
- Pinned dense-model revision and validated vector-index lineage
- A 34-query relevance set and token/BM25/dense/hybrid comparison reports
- Evidence-based BM25 champion selection with safe hybrid fallback
- Backend tests, linting, formatting, typing, frontend checks, Docker Compose, and CI
- Request IDs, local stage timings, retriever versions, and catalog hashes

Still required:

1. MLflow experiment tracking and a documented champion/challenger run.
2. Production-container hardening and one end-to-end browser test.
3. Terraform-defined AWS deployment and GitHub Actions deployment workflow.
4. Structured production logging, CloudWatch dashboard/alarms, budget control, and rollback notes.
5. A minimal feedback path with privacy-aware storage.
6. Public demo evidence, final README polish, clean-checkout verification, and the `v1.0.0` release.

## Completion rule

After every item under “Still required” is complete and verified, TasteIQ is complete as a flagship
end-to-end MLE portfolio project. Broader data, additional judgments, retrieval tuning, interface
polish, and alternative infrastructure are post-release refinements rather than architectural
requirements.
