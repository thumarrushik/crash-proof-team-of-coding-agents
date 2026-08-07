# MIGRATIONS

Schema **and** reference data change only through versioned, idempotent migrations applied by a migrate
endpoint to every tenant store. Never run DDL ad-hoc from request code.

## The mechanism

- Files: `database/migrations/NNNN_<description>.sql`, next sequential number, tracked in git. The runner +
  the tenant-aware connection live in `database/` too (see BACKEND.md anatomy).
- Each tenant store carries a `schema_migrations(version, applied_at)` table.
- A runner applies only **unrecorded** versions, in order, each committed as its own unit; on a DB error
  it rolls back that migration and re-raises (loud, never half-applied silently).
- An **admin migrate endpoint** (`POST /v0/admin/migrate`) applies pending migrations to **every** tenant
  store — idempotent, safe to re-run. New tenants get all migrations at provision time.

## Idempotent DDL (required)

Use `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`.
Index soft-state columns (`deprecated`, `deleted`). **Editing a `CREATE TABLE IF NOT EXISTS` does nothing on
existing stores** — to add a column you MUST add a new `ALTER ... IF NOT EXISTS` migration and run the endpoint.

## Soft state, not destruction

`deprecate` and `delete` are soft (boolean + timestamp columns, indexed). Hidden from default reads; revealed
with `?include_deprecated` / `?include_deleted`. Foreign keys: reference with `ON DELETE RESTRICT` so a
referenced row can't be hard-removed out from under a dependent; membership tables `ON DELETE CASCADE`.

## Seeding reference data (same channel)

Seed common/default rows via a migration too — **deterministic ids** (`<kind>_seed_<name>`) + `ON CONFLICT
(id) DO NOTHING` so it's idempotent and every tenant converges. Insert parents before children (e.g.
classifiers before pipeline membership). Validate any embedded patterns/expressions compile before shipping
the seed (the migration bypasses the app's create-time validation). They're ordinary rows — editable and
soft-deletable like any other.

## Rollout checklist

1. Write `migrations/NNNN_*.sql` (idempotent).
2. Rebuild the service image so the file is baked into `/app/migrations` (the runner reads it there).
3. `POST /v0/admin/migrate` → applies to all existing tenants; new tenants get it on provision.
4. If a test asserts idempotency, assert on a **second** migrate run (pre-existing stores may be a version
   behind, so the first run legitimately applies the new version).
