# HARD-RULES

The non-negotiables, the anti-patterns, and the bugs learned the hard way. Read this every time.

## Non-negotiable rules

1. **Fail loud, never fake.** Unimplemented/unavailable → a structured error with a stable code (and a
   tracking ref if one exists), never a silent skip, empty result, or canned/fake value. A path you
   can't verify is not done. "I can't without X" is usually a failure to find the legitimate X, not a wall.
2. **Schema + reference-data changes go through versioned migrations + a migrate endpoint — never ad-hoc
   DDL from request code.** See MIGRATIONS.md.
3. **Version every data route** (`/v0/...`); unversioned data routes never ship.
4. **Two layers:** pure business logic (raises domain exceptions, no web types) + a thin transport layer
   (the single place exceptions map to HTTP + the envelope). The logic layer is grouped by **endpoint
   group** (a subfolder each), with **one light-wrapper file per endpoint** and shared logic in that
   group's **`utils/` package** (multiple files by concern, never one `utils.py`). See BACKEND.md.
5. **Tenant isolation by construction** (store-per-tenant; validate identifiers). See TENANCY.md.
6. **Cross-service over HTTP only — no shared store.** Preserve the upstream status when re-raising.
7. **Optional/heavy deps fail loud** (lazy-import; missing lib/key → 503) and are **injectable** for mocks.
8. **Validate generated/runnable artifacts before persisting** (compile + satisfy examples; refine ≤2×;
   drop + report the rest). See LLM.md.
9. **Parse user expressions with a safe-AST allowlist — never `eval`.**
10. **Small scoped commits at every edit.** Secrets only via env + a committed `.env.example`.

## Anti-patterns (never do)

- `CREATE`/`ALTER` from request handlers; editing a `CREATE ... IF NOT EXISTS` and expecting existing
  stores to change (they won't — add an `ALTER ... IF NOT EXISTS` migration).
- Business logic in the transport layer, or web/HTTP types leaking into the logic layer.
- One service reading another service's database.
- `eval()` / `exec()` on user-supplied input.
- Faked/canned results, silent fallbacks, swallowing an error into an empty list.
- Committing a real secret (use env; document keys in `.env.example`).
- Declaring done from a green unit run alone — without a live, real-infra, end-to-end check.

## Bugs learned the hard way (check these proactively)

- **Don't trust assumed response field names.** A list endpoint may return `client_id` where you assumed
  `client`; the UI rendered `undefined` keys until verified against the real response. Inspect the real payload.
- **Presigned object-store uploads:** create the upload **without** a content-type and PUT raw bytes. Signing
  with a content-type the client then omits causes a SigV4 signature mismatch and the upload 403s.
- **A checkbox wrapped inside its own `<label>` double-toggles** when clicked (label re-fires the control) →
  net no-op. Use a clickable element with `role=checkbox` + a pointer-inert indicator, or click the label, not
  the inner input.
- **A `position: sticky` header intercepts clicks** on buttons that scroll-into-view tucks beneath it — the
  click lands on the bar, the handler never fires, no error. Don't overlay interactive content; reserve scroll
  padding or drop sticky.
- **A submit clicked right after a checkbox toggle** can miss in browser automation (lingering pointer state);
  dispatch a `click` event for deterministic activation.
- **Calling a state-setter during render** (e.g. lazy-loading inside a component body) causes re-render churn /
  flaky interactions — do it in an effect.
- **Migrate-idempotency tests must assert on a SECOND migrate run**, not the first — pre-existing stores from
  earlier work may be a version behind, so the first run legitimately applies something.
- **Seeding common entities collides with tests/users** that create same-named entities — use deterministic,
  namespaced seed ids and expect names not to be unique.
- **Containers don't pick up new code/migrations until rebuilt.** After editing migrations or a baked shared
  lib, rebuild the image (and overlay the shared-lib source if its wheel build is flaky) before the live check.
- **A fresh interpreter cold-starts slowly on heavy images**, so a 5s container healthcheck flaps — run the
  probe interpreter with site-init skipped and give a generous timeout + start_period.
- **Browser e2e sharing one live backend must run serially** — concurrent tenant creation (`CREATE DATABASE`)
  contends and flakes.
- **A group `__init__.py` that re-exports a function whose name equals a submodule filename SHADOWS the
  submodule.** After `from .build import build`, `from pkg import build` returns the *function*, not the
  module — so tests/importers that wanted the module get a callable and `module.other_symbol` fails. Never let
  a re-exported name equal a sibling submodule name (name the `/build` endpoint wrapper `builder.py`, not
  `build.py`). Smoke-test `from pkg import <submodule>` after wiring re-exports.
- **A `src/`-rooted layout isn't importable until you tell the tools where root is.** With the app under
  `src/` + a sibling `database/` (both top-level import roots named in `uvicorn src.main:app`), set
  `[tool.pytest.ini_options] pythonpath = ["."]` so tests resolve them without an install, point the wheel
  `packages = ["src", "database"]`, and in the image run from the copied source (`WORKDIR` + `PYTHONPATH`,
  `CMD uvicorn src.main:app`) — don't rely on the project being pip-installed as an importable package.
- **Real-infra DB tests need the password wired in, or they silently skip.** A reachability-gated suite that
  reads `*_POSTGRES_PASSWORD` from env will skip every DB test if you only pass host/port — source the
  project's `.env` (mapping its `POSTGRES_PASSWORD` to the service's `NIE_`-prefixed var) before the run, and
  treat a big skip count as a red flag, not a pass.
