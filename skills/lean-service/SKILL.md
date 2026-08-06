---
name: lean-service
description: Build or extend a multi-tenant backend microservice (FastAPI/Python by default; the principles transfer to any HTTP service stack) and its optional React/TS frontend, to a battle-tested standard — tenant-isolated storage, versioned migrations applied via a migrate endpoint (never ad-hoc DDL), versioned APIs, two-layer service/endpoint code with a canonical fail-loud error envelope, cross-service over HTTP only, optional heavy deps lazy-imported + fail loud, generated artifacts validated before persist, safe-AST (never eval), dockerized & self-contained, tested against real infra (nothing faked). Use whenever adding/extending a service, endpoint, migration, seed, cross-service integration, LLM feature, or frontend surface.
---

# lean-service

A portable playbook for multi-tenant backend platforms + their UIs, forged on a FastAPI + Postgres +
object-store + React/Vite/TS stack. Every rule states a **principle** — apply the principle, adapt the
syntax. **If the repo has a reference service or a `CLAUDE.md`/ADR with conventions, those win over this
skill.** First action in a repo: detect the stack + any reference service, then follow these rules.

## How to use this skill

1. Read **[HARD-RULES.md](HARD-RULES.md)** every time — the non-negotiables + the bugs learned the hard way.
2. Open the topic file(s) for the task at hand (below). Don't read all of them — load what you need.
3. Build to the rules, then clear the **[TESTING.md](TESTING.md)** verification bar before declaring done.

## Topic map (load on demand)

| Task | File |
|---|---|
| The non-negotiable rules + anti-patterns + hard-won bug lessons | **[HARD-RULES.md](HARD-RULES.md)** |
| Service anatomy, two-layer split, `/v0`, error envelope, add a service/endpoint, cross-service calls | **[BACKEND.md](BACKEND.md)** |
| Versioned migrations, idempotent DDL, the migrate endpoint, seeding reference data | **[MIGRATIONS.md](MIGRATIONS.md)** |
| Store-per-tenant, schema/namespace per sub-scope, identifier validation, provisioning | **[TENANCY.md](TENANCY.md)** |
| Optional/heavy deps (LLM etc.): lazy-import + fail-loud + injectable; validate generated artifacts; safe-AST | **[LLM.md](LLM.md)** |
| Self-contained image, shared-lib overlay, healthcheck, compose, Makefile, README | **[DOCKER.md](DOCKER.md)** |
| Same-origin proxy, URL-tenancy + guards, component library, fail-loud UI, uploads | **[FRONTEND.md](FRONTEND.md)** |
| Verification bar: real infra, 5×, live containers, fail-loud asserted, browser-e2e pitfalls | **[TESTING.md](TESTING.md)** |
| Design-first for big features (multi-lens design doc → fixed-contract build) | **[DESIGN-FIRST.md](DESIGN-FIRST.md)** |

## The 10 rules in one breath (details in HARD-RULES.md)

1. Fail loud, never fake. 2. Schema/seed changes only via versioned migrations + a migrate endpoint.
3. Version every data route (`/v0`). 4. Two layers: pure logic (domain exceptions) + thin transport
(HTTP + envelope mapping). 5. Tenant isolation by construction. 6. Cross-service over HTTP only — no
shared store. 7. Optional/heavy deps lazy-import + fail loud (503) + injectable for mocks. 8. Validate
generated/runnable artifacts before persisting. 9. Safe-AST allowlist, never `eval`. 10. Small commits
at every edit; secrets only via env.
