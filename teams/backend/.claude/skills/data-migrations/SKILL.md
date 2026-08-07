---
name: data-migrations
description: Change live storage without downtime or data loss — expand-contract for anything breaking, idempotent low-lock DDL, batched resumable backfills, roll-forward rollback, seeds on the migration rail, proven against real storage; use when changing any schema, backfilling data, or seeding reference data.
---

# data-migrations

The rail itself — numbered files, the migrate endpoint, seeds as migrations —
is defined in [[lean-service]] (MIGRATIONS.md). This skill governs changing
the *shape of live data* while the previous release is still running on it.

## 1. Classify the change

Purely additive (new nullable column, table, index): one migration, done.
Anything that renames, retypes, tightens (NOT NULL, constraint, narrower
enum), moves, or drops data in use: expand-contract, never one shot.

## 2. Expand-contract, one phase per release

- **Expand.** Add the new shape beside the old — purely additive DDL. Old
  code runs untouched.
- **Migrate.** Ship code that writes both shapes and still reads the old.
  Backfill history (below). Verify new vs old (counts, spot checksums), then
  ship the read-switch to the new shape.
- **Contract.** Only after every reader is on the new shape and a full deploy
  cycle has passed: drop the old shape in its own migration.

Never collapse phases into one release — the release between phases IS the
rollback path.

## 3. Idempotent, low-lock DDL

Guard every statement (`IF NOT EXISTS` / existence checks) so a re-run is a
no-op, never an error. Respect lock cost: build indexes concurrently (outside
a transaction); add NOT NULL and constraints as add-invalid-then-validate;
set a `lock_timeout` so a blocked migration fails fast instead of queueing
every writer behind it.

## 4. Backfill discipline

A backfill is its own step, never inside the DDL migration or its
transaction. Batch it (bounded rows per pass), make each pass idempotent
(`WHERE new_col IS NULL`), log progress, make it resumable — a backfill that
dies at row 4M must pick up, not restart from zero or double-write.

## 5. Rollback stance: roll forward

Each phase is compatible with the neighboring release, so "rollback" means
redeploying the previous code — no down-migration needed. Write a down only
when it is real (dropping what expand added). A down that pretends to restore
dropped data is a lie: mark contract migrations irreversible and rely on the
phase gap and backups.

## 6. Prove it on real storage

Against a real database with representative data: apply the migration, apply
it again (idempotence), run the previous release's code on the new schema
(expand compatibility), then the full suite. A migration that only ran
against a mock or an empty database is untested.

## Blocked on sight

- Rename/retype/drop of an in-use column in a single migration.
- A backfill UPDATE inside a DDL transaction, or unbatched on a large table.
- Editing an already-applied migration; hand-run DDL of any kind.
- A down-migration that claims to restore destroyed data.

## Grounding

- ParallelChange / expand-contract (Fowler bliki) — martinfowler.com
- "Zero-downtime Postgres migrations — the hard parts" — gocardless.com
- strong_migrations & safe-pg-migrations lock-hazard catalogs — github.com
