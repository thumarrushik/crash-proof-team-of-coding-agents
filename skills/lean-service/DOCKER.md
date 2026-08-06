# DOCKER & compose

Each service is **self-contained**: one image, its migrations baked in, an entry in the compose file, a
tolerant healthcheck, a Makefile test target, and a README.

## Image (self-contained)

- `FROM` the shared base image (carries the shared lib + contracts).
- Install the service (and its optional extra if it has one, e.g. `[llm]`).
- **Overlay the current shared-lib source** if the base image's copy can lag or its wheel build is flaky
  (a plain file copy into site-packages — no network, no build backend). This guarantees the image has the
  latest shared lib without a slow/hanging rebuild.
- **Copy the `database/migrations/` dir** into the image and point the migrate runner at it (an env var
  like `MIGRATIONS_DIR`). The runner reads migrations from there — if you add a migration, **rebuild** or
  it won't be applied.
- **Run from the copied source, not a pip-installed package.** With a `src/` + sibling `database/` layout,
  set `WORKDIR` to the service dir and `ENV PYTHONPATH=<that dir>` so the local `src`/`database` packages
  resolve — don't depend on the project being importable as an installed wheel (a top-level `src` package is
  fragile). Mirror this in packaging: wheel `packages = ["src", "database"]` and tests use
  `[tool.pytest.ini_options] pythonpath = ["."]` (see HARD-RULES.md).
- `EXPOSE` the port; `CMD` runs the ASGI server (`uvicorn src.main:app --host 0.0.0.0 --port <port>`).

## compose

- One service entry; **host-port offset** (e.g. `18xxx:<port>`) to avoid clashing with other local stacks.
- Pass tenancy/infra env (DB host/credentials, object-store endpoints, optional `*_API_KEY` /
  `*_BASE_URL`). `depends_on` peers **with `condition: service_healthy`**.
- **Healthcheck must tolerate slow cold-starts.** A fresh interpreter on a heavy (e.g. LLM-extra) image can
  take seconds to start, so a default 5s probe flaps to "unhealthy" even though the app is fine. Run the
  probe interpreter with **site-init skipped** (`python -S -c "...urlopen('/health')..."`) and set a
  generous `timeout: 15s` + `start_period: 30s`. Don't make a header/element `position: sticky` etc. — that's
  a frontend note, but the principle is the same: don't let infra cosmetics cause false failures.

## Per-service extras

- A **Makefile** target (`<svc>-test`) that runs the suite against the local infra with the right env.
- A **README** documenting endpoints, tenancy, seeded defaults, and the fail-loud cases.
- A migrate rollout step: after adding a migration, rebuild the image, restart the container, and
  `POST /v0/admin/migrate` (see MIGRATIONS.md).

## Frontend image (if there's a UI)

Multi-stage: build the static bundle, then serve with a static server that **reverse-proxies `/api/<svc>`
to each backend** (same-origin, no CORS). SPA fallback to `index.html` so client-side routes resolve on
deep links / refresh. See FRONTEND.md.
