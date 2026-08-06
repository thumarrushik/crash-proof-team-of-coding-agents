# BACKEND

Service anatomy, the two-layer split, versioning, the error envelope, and the add-a-thing recipes.

## Service anatomy (folder layout)

Each service: a top-level **`database/`** folder (all data-layer items) + a **`src/`** folder whose API
lives under a **version** folder (`v0/`), inside which sit `endpoints/` and `services/`. Inside the logic
layer, **group by endpoint group → one light-wrapper file per endpoint → shared logic in that group's
`utils/` package**.

```
<service>/
  database/                          # ALL data-layer items live here
    migrations/
      0001_init.sql                  # versioned, idempotent DDL + seed data (see MIGRATIONS.md)
    connection.py                    # connect per tenant (+ sub-scope); identifier validation
    migrate.py                       # migration runner + admin-migrate logic
  src/
    main.py                          # builds the app; mounts the versioned routers
    settings.py
    v0/                              # API VERSION (bump to v1/ for a breaking contract; keep v0/ until migrated)
      endpoints/                     # thin HTTP transport
        errors.py                    #   the SINGLE place domain exceptions -> HTTP status + envelope
        <endpoint_group>.py          #   one router per endpoint group (e.g. classifiers.py, rules.py)
      services/                      # business logic (raises domain exceptions; NO web types)
        exceptions.py                #   shared domain exceptions
        <endpoint_group>/            #   a subfolder per endpoint group
          __init__.py
          <endpoint_a>.py            #   ONE light-wrapper file per endpoint (validate, call utils, raise, return)
          <endpoint_b>.py
          utils/                     #   a PACKAGE (not utils.py): NON-LLM shared logic split by concern
            __init__.py
            <concern_x>.py           #     e.g. queries.py, compile.py, evaluate.py
            <concern_y>.py
          llm/                       #   (LLM groups only) a SIBLING package of utils/ — ALL LLM code (see LLM.md)
            __init__.py
            agent.py                 #     core logic: generate→validate→refine orchestration; model injectable
            prompt.py                #     system prompts + builders
            model.py                 #     structured-output Pydantic models
      models.py                      # v0 request/response (Pydantic) models
  Dockerfile  pyproject.toml  README.md
```

- **`database/` = the data layer.** Migrations, the tenant-aware connection, and the migrate runner/admin
  logic all live here (see MIGRATIONS.md / TENANCY.md). Nothing else opens raw connections.
- **`src/<version>/`.** Every data route is served under its version; `endpoints/` and `services/` are
  **inside** the version folder, so a future `v1/` is a clean parallel tree.
- **Per-endpoint file = light wrapper.** Each `services/<group>/<endpoint>.py` is thin: parse/validate,
  orchestrate, raise domain exceptions, return plain data. It does NOT hold the bulk logic.
- **`utils/` per group = the NON-LLM shared logic, as a package.** A `utils/` **folder** split into multiple
  files by concern (`queries.py`, `compile.py`, `evaluate.py`) — never one catch-all `utils.py`. Wrappers
  import from it; promote anything used by ≥2 endpoints into it.
- **`llm/` per group (LLM groups only) = ALL LLM code, as a package — a SIBLING of `utils/` at the same
  depth** (not inside it): `agent.py` (core orchestration logic), `prompt.py` (system prompts + builders),
  `model.py` (structured-output Pydantic models). Keep non-LLM shared logic in `utils/`, everything LLM in
  `llm/` — see LLM.md.
- **Logic layer never imports the web framework or HTTP types.** Transport is one router per group, shapes
  the envelope, and is the only place exceptions become HTTP.

Why: data access has one home (`database/`); versions are isolated trees; testable logic with no web
mocks; one audited error-mapping site; each endpoint is a readable wrapper; shared behavior lives once.

## Versioning

Every data route under `/v0/...`. New breaking contracts bump to `/v1` and keep the old one until clients
migrate. Never expose an unversioned data route.

## Canonical error envelope

Response is `{data: …}` or `{error: {code, message, field, component}}`. Map domain exceptions centrally:

| Domain exception | code | HTTP |
|---|---|---|
| NotFound | `ERR_MISSING_FIELD` | 404 |
| Conflict (already exists / wrong state) | `ERR_SCHEMA_VALIDATION` | 409 |
| Validation (bad input) | `ERR_SCHEMA_VALIDATION` | 422 |
| MissingDependency (referenced entity absent) | `ERR_MISSING_FIELD` | 422 |
| DependencyUnavailable (key/lib/peer/infra down) | `ERR_DEPENDENCY_UNAVAILABLE` | 503 |

Register a global handler so an unhandled domain error AND a propagated peer error both render the envelope
with the right status. A framework body-validation error (missing/typed field) maps to 422 too.

## Cross-service calls (HTTP only)

Never query another service's store. Use a small client that:
- targets the peer's base URL (compose DNS / configured URL),
- unwraps the envelope (returns `data`),
- on `>=400` re-raises a domain/`NIEError` carrying the **upstream status** so a peer's 404/409/503 surfaces
  faithfully to your caller (and your envelope names the failing `component`).

Treat a 409 during provisioning as **benign/idempotent** ("already exists" — continue).

## Recipe: add a NEW service

Scaffold `database/{migrations/0001_init.sql, connection.py, migrate.py}`, `src/{main.py, settings.py}`,
`src/v0/services/exceptions.py`, a `src/v0/services/<group>/` package (a `utils/` folder + a file per
endpoint), `src/v0/endpoints/{errors.py, <group>.py}`, `src/v0/models.py`, `README.md`. Mirror the repo's
reference service. Wire `database/` (connect-per-tenant + migrate runner), then logic, then transport.
Containerize + compose + Makefile target (see DOCKER.md).

## Recipe: add an endpoint / feature

1. Schema needed? Add a migration in `database/migrations/` (see MIGRATIONS.md) — never inline DDL.
2. Logic: `src/v0/services/<group>/<endpoint>.py` — a **light wrapper** that validates, calls shared
   functions in the group's `src/v0/services/<group>/utils/` package, raises domain exceptions, returns
   data. Put any logic reused by another endpoint into a concern file under `utils/` (create the `<group>/`
   package + `utils/` folder if new).
3. Transport: add the route to `src/v0/endpoints/<group>.py` (Pydantic models in/out, envelope, delegate).
4. Mount under `/v0`. Register literal/collision-free routes **before** parameterized ones
   (`/x/test` before `/x/{id}`), or `{id}` will swallow the literal.
5. Tests (see TESTING.md): happy path + every fail-loud branch.
