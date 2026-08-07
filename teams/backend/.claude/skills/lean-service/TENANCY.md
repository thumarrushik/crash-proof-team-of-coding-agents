# TENANCY

Tenant isolation by construction. Default to **store-per-tenant**; never let one tenant's request touch
another's data.

## Model

- **Store per client:** a database/schema/namespace per tenant (e.g. `<prefix>_<client>`). Strongest
  isolation; no cross-tenant query risk.
- **Sub-scope per org/workspace:** a schema inside the client store, selected per request (e.g.
  `SET search_path`). Use it when the domain has a second tenancy axis; otherwise keep it flat.
- **Encode the split in routes + IA:** resources that are client-only live at `/clients/:client/...`;
  resources scoped to a sub-org live at `/clients/:client/orgs/:org/...`. Don't expose a sub-scope selector
  on routes that don't have that axis (it would silently mislead).

## Decide the tenancy axes ONCE, then apply them to EVERY tenant resource

The axes (client, org, …) are a **platform-wide contract**, not a per-service choice. Pick them up front
and scope **every** tenant-owned table, route, and cross-service call by the **same** set. A service that
scopes by `client` only while its peers scope by `client + org` is a latent bug, not a simpler design:

- **The data layer carries every axis.** Each tenant row stores `client` + `org` (and the store/schema
  encodes them too); every read/write filters by all of them. A resource scoped to fewer axes than its
  siblings becomes silently *shared* across the missing axis (e.g. a client-only classifier leaks across
  all that client's orgs) — usually not what anyone intended.
- **Routes mirror the axes exactly** (`/clients/:client/orgs/:org/<resource>`). If peers nest under
  `/orgs/:org` and one service doesn't, the IA lies about the isolation model.
- **Cross-service calls must be able to thread every axis.** The caller already knows the full scope; the
  callee must accept it. Real failure mode seen in practice: a `run` service holds `(client, org)` and calls
  a `registry` that only understands `client` — so it *cannot* pass `org`, and runs in different orgs
  resolve the same shared definitions. The fix is to add the missing axis to the upstream service, not to
  drop it at the call site. When you add a service or endpoint, grep peer call-sites
  (`/v0/clients/{client}/...`) and confirm the scope path segments match before wiring it.
- **Retrofitting is a migration, not an edit:** add the column (`ALTER TABLE ... ADD COLUMN org`),
  backfill existing rows to a default org, move data into the per-org schema if that's the model, bump the
  route prefix, and update every peer caller + the frontend — all in one coordinated change. Cheap to get
  right on day one; expensive once data and clients exist. So default new tenant resources to the **full**
  axis set even if only one axis is exercised at first.

## Provisioning

- Create the store on demand: an explicit `POST /v0/clients` (and sub-scope create), or lazily on first use.
- Provisioning runs the migrations (incl. seeds) so a new tenant is fully formed + converged.
- Idempotent: a 409 ("already exists") on provision is benign — continue the chain across services.

## Identifier safety (do this every time)

Before interpolating a tenant/identifier into a store or schema name, validate it against a strict
allowlist, e.g. `^[a-z0-9][a-z0-9_-]{0,39}$`, and reject otherwise with a validation error. Never format an
unvalidated string into DDL or a `search_path`.

## Connections

Open a connection bound to the tenant store (and set the sub-scope) per request; the business-logic layer
receives a ready connection. Mind the driver's transaction semantics — be consistent (don't mix implicit
autocommit with explicit transactions on the same connection); open read paths in autocommit and bracket
writes/migrations explicitly so a SELECT-before-transaction quirk doesn't no-op your writes.
