---
name: data-migrations
description: Change live storage without downtime or data loss — expand-contract for anything breaking, idempotent low-lock DDL, batched resumable backfills, roll-forward rollback, seeds on the migration rail, proven against real storage; use when changing any schema, backfilling data, or seeding reference data.
---

# data-migrations

The rail itself — numbered files, the migrate endpoint, seeds as migrations —
is defined in [[lean-service]] (MIGRATIONS.md). This skill governs changing
the *shape of live data* while the previous release is still running on it.

## How to use this skill

1. Read this file every time a schema, backfill, or seed changes. Classify
   the change first (rule 1 below) — the classification picks the topic file.
2. Open the topic file(s) for the task at hand. Don't read all of them —
   load what the change needs.

## Topic map (load on demand)

| Task | File |
|---|---|
| Anything that renames, retypes, tightens, moves, or drops in-use data — the three phases, rollback between releases | **[EXPAND-CONTRACT.md](EXPAND-CONTRACT.md)** |
| Writing any DDL: lock hazards, safe recipes per operation, idempotence | **[DDL-SAFETY.md](DDL-SAFETY.md)** |
| Moving data into a new shape: batching, resumability, verification | **[BACKFILLS.md](BACKFILLS.md)** |

## The rules in one breath

1. Classify first: purely additive (new nullable column, table, index) is
   one migration; rename, retype, tighten, move, or drop of data in use is
   expand-contract — never one shot.
2. One expand-contract phase per release; the release between phases IS the
   rollback path. Never collapse phases.
3. All DDL idempotent (guarded, re-run is a no-op) and low-lock: concurrent
   index builds, add-invalid-then-validate constraints, `lock_timeout` set.
4. Backfills are their own step — batched, idempotent per pass, resumable —
   never inside a DDL migration or its transaction.
5. Rollback stance is roll forward: redeploy previous code, no
   down-migration needed. Write a down only when it is real; a down that
   pretends to restore dropped data is a lie — mark contract migrations
   irreversible.
6. Prove on real storage with representative data: apply, apply again
   (idempotence), run the previous release's code on the new schema, then
   the full suite. Mock-only or empty-database runs are untested.

**Blocked on sight:** rename/retype/drop of an in-use column in a single
migration · a backfill UPDATE inside a DDL transaction, or unbatched on a
large table · editing an already-applied migration; hand-run DDL of any
kind · a down-migration that claims to restore destroyed data.
