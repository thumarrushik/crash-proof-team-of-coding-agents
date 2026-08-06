# Team skills — the operating model

These are the built-in skills the workflow installs into each agent's workspace.
They model a small software org: every **team** has a **delivery playbook** (the
steps it runs to finish a task, plus its cross-team duty) and applies shared
**disciplines**.

The installer (`src/activities.py`) resolves each skill folder-first: the
operator's `~/.claude/skills/<name>` wins, then this `skills/<name>/`, else a
placeholder. So `lean-service` comes from the operator; the rest ship here.

## Team playbooks (how each team works a task)

| Team | Playbook | Cross-team duty |
|---|---|---|
| service-design | [`service-design`](service-design/SKILL.md) | writes the contract the others build against |
| backend | [`backend-delivery`](backend-delivery/SKILL.md) | backend change → run backend **and** frontend/e2e tests |
| frontend | [`frontend-delivery`](frontend-delivery/SKILL.md) | run a Playwright browser e2e of the integrated flow |
| testing | [`testing-delivery`](testing-delivery/SKILL.md) | owns the full cross-layer matrix (API + Playwright e2e) |
| review | [`pr-review`](pr-review/SKILL.md) | won't approve unless the cross-team test evidence is green |
| issues | [`issue-delivery`](issue-delivery/SKILL.md) | fallback lane for uncategorized work |

## Shared disciplines

- [`tdd`](tdd/SKILL.md) — test-first
- [`self-review`](self-review/SKILL.md) — review your own diff before declaring done
- [`final-report`](final-report/SKILL.md) — the required REPORT.md format
- [`frontend-ui`](frontend-ui/SKILL.md) — UI quality bar
- [`testing-bar`](testing-bar/SKILL.md) — verification standard
- `lean-service` — multi-tenant service standard (from `~/.claude/skills`)

## The cross-team testing principle

A change in one layer must prove it didn't break the others:

- **backend** change → backend tests **+** frontend/e2e
- **frontend** change → component tests **+** Playwright e2e
- **testing** owns running the whole matrix; **review** verifies it actually ran green

Each team lane also runs in its own **Temporal namespace** (`backend`, `frontend`,
…) — the per-team ownership/visibility boundary. A namespace has workflows only
once that team is assigned an issue or PR.
