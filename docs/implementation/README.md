# TasteIQ Implementation Log

This directory is the internal engineering record for TasteIQ. The architecture plan describes the target system; these documents describe what was actually implemented, why it was implemented, and what evidence shows that it works.

## Rules

Every meaningful delivery part must have an implementation record. Update the record in the same change as the code.

Each record must explain:

1. Scope and intended outcome
2. Starting state
3. Changes made
4. Position in the end-to-end architecture
5. Important decisions and reasoning
6. Alternatives considered
7. Tradeoffs and consequences
8. Security, reliability, data, and performance impact
9. Verification performed and results
10. Known limitations and risks
11. Follow-up dependencies
12. Files and components affected

Do not claim planned functionality as implemented. Measurements must identify their environment and methodology. If a change supersedes an earlier decision, link the new record and retain the old record as history.

## Records

| Part | Status | Record |
|---|---|---|
| Phase 0A — Repository hygiene | Complete | [00-repository-hygiene.md](00-repository-hygiene.md) |
| Phase 0B — Reproducible tooling | Complete | [01-reproducible-tooling.md](01-reproducible-tooling.md) |
| Phase 0C — Baseline and data report | Complete | [02-baseline-and-data-report.md](02-baseline-and-data-report.md) |
| Phase 1 — Trustworthy data and API | Complete | [03-trustworthy-data-and-api.md](03-trustworthy-data-and-api.md) |
| Phase 3A — Evaluation foundation | Complete | [04-evaluation-foundation.md](04-evaluation-foundation.md) |

## Relationship to other documentation

- [Public README](../../README.md): concise project introduction and local usage
- [Architecture plan](../architecture-plan.md): target design and delivery sequence
- Implementation records: actual changes, evidence, and evolving decisions
- Future ADRs under `docs/adr/`: durable decisions that apply across multiple delivery parts

## Record template

Use this structure for future records:

```markdown
# Part title

**Status:** Planned | In progress | Complete
**Date:** YYYY-MM-DD
**Related phase:** Phase name

## Outcome
## Starting state
## Changes made
## System-design impact
## Decisions and reasoning
## Alternatives considered
## Tradeoffs and consequences
## Security, reliability, data, and performance
## Verification
## Known limitations and risks
## Follow-up work
## Affected files
```
