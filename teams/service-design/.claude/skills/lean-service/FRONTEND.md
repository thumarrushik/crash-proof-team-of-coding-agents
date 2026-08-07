# FRONTEND (optional UI)

Forged on React + Vite + TypeScript + react-router. Principles transfer to any SPA.

## Wiring & tenancy

- Reach services **same-origin** via `/api/<service>/…` — a reverse-proxy in prod (nginx `proxy_pass`),
  the dev-server proxy in dev. No CORS, one origin. A thin API client unwraps the envelope and throws a
  typed error carrying `status/code/field/component`.
- **Tenancy lives in the URL** (`/clients/:client/...`, and a sub-scope axis as
  `/clients/:client/orgs/:org/...`). Route **guards** require a provisioned client/sub-scope and render a
  clear "not found / provision it" state — never a blank page. Persist last selection only as a fallback.
- **Carry EVERY axis the backend has — consistently** (see TENANCY.md). If services scope by
  `client + org`, then routes, the context switcher, and **every** fetch carry both — the path shape
  matches the API exactly (`/clients/:client/orgs/:org/X` ⇄ `GET /v0/clients/{client}/orgs/{org}/X`).
  Dropping an axis on one screen silently shows another scope's data. Read `(client, org)` from one place
  (route params + context/store) and thread it into each call; never hardcode or omit it. If a resource
  has fewer axes than its siblings, that's usually an upstream gap to fix, not a frontend special case.
- **No dead-end navigation.** Make the primary nav reflect the real flow; every nav target resolves to a
  working route or an explicit empty/provision state.

## Components & state

- A small **component library** (layout, primitives, data-display, feedback, a couple of composites).
  Each list distinguishes **loading / loaded-empty / error / populated** — a failed fetch is an
  `InlineError + retry`, never a silently empty table.
- **Surface backend errors verbatim** (`code` + `message` + `field` + `component`) as a toast or inline
  error. Never fake success; never swallow an error into an empty list. When combining several async
  actions on a page, show the **most recent** message (stamp + pick latest), not the first truthy one.
- Render results **structured** (tables/badges), with the raw payload behind a disclosure.

## Management pages: list-first, not a panel stack

A CRUD surface should be **list-first** — the table IS the page. Put create in a **slide-over drawer**
behind a `+ New` header button, and secondary tools (test/build/import) behind a **`Tools` dropdown**, each
in a **dialog**. Stacking *create + table + tools* panels on one page reads as a playground, not an
enterprise tool. Use Radix/shadcn **Sheet / Dialog / DropdownMenu** (+ `tailwindcss-animate`); never
hand-roll overlays. For destructive actions use a **type-to-confirm** dialog (disable the button until the
user types the exact id). Drive overlay open-state **controlled** so create-on-success closes it and
create-on-error keeps it open with the error inline.

## Uploads (direct to object store)

Presign **without** a content-type and PUT **raw bytes**; signing with a content-type the client then
omits causes a SigV4 mismatch (403). Verify response field names against the real payload — don't assume.

## Browser e2e (see TESTING.md for the bar)

- Drive the **real** stack; assert on **URLs + structured elements**, not JSON/log substrings. Run
  **serial** when specs share one backend (concurrent tenant creation flakes).
- Pitfalls that cost real debugging here:
  - A checkbox wrapped in its `<label>` **double-toggles** → net no-op. Use a clickable element with
    `role=checkbox` + a pointer-inert indicator; click the pill, not the inner input.
  - A `position: sticky` header **intercepts clicks** on controls that scroll beneath it (the click hits the
    bar, the handler never fires, no error). Don't overlay interactive content.
  - **Drawer/dialog form fields aren't in the DOM until opened** — fixtures must click `+ New` (or
    `Tools → X`) BEFORE filling, and `Escape` to close between steps. Moving a form into a drawer breaks any
    test that filled it directly; update the spec in the same change.
  - **A 404-tolerant delete chain fakes success against a stale container.** A 404 from an *unbuilt* route is
    indistinguishable from "already deleted", so the chain reports success and the UI shows a green toast
    while nothing happened. After adding a backend route, **rebuild the image and `curl` the route** before
    trusting the UI — the dev server proxies to the running container, not your edited source.
  - A submit clicked immediately after a checkbox toggle can miss — dispatch a `click` for determinism.
