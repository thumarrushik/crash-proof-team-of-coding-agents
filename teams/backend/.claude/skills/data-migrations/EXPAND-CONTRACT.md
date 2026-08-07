# EXPAND-CONTRACT — breaking shape changes across releases

Fowler's ParallelChange: never force every user of an interface to move in
one atomic step. Applied to storage, the "users" are your own releases — the
previous release is still running on the schema you are changing, and it
must keep working until it is gone.

## Classify first

Purely additive — new nullable column, new table, new index: one migration,
done (write it to the DDL-SAFETY.md recipes). Anything that renames,
retypes, tightens (NOT NULL, constraint, narrower enum), moves, or drops
data in use: the three phases below, one phase per release, never one shot.

## The three phases

1. **Expand.** Add the new shape beside the old — purely additive DDL. Old
   code runs untouched; nothing reads or writes the new shape yet.
2. **Migrate.** Ship code that writes both shapes and still reads the old.
   Backfill history (BACKFILLS.md). Verify new vs old — counts, spot
   checksums — then ship the read-switch to the new shape. Each of these
   (dual-write, backfill, read-switch) can be its own release; they never
   share one with expand or contract.
3. **Contract.** Only after every reader is on the new shape and a full
   deploy cycle has passed: stop writing the old shape, then drop it in its
   own migration.

## Worked example — renaming `full_name` to `display_name`

- **R1 (expand):** migration adds nullable `display_name`.
- **R2 (migrate, write):** code writes both columns, reads `full_name`.
  Backfill copies `full_name` → `display_name` where NULL; verify counts
  and spot-check values match.
- **R3 (migrate, read):** code reads `display_name`, still writes both.
- **R4 (contract):** code stops writing `full_name`; a later migration
  drops the column, guarded and irreversible.

Four small releases instead of one clever migration — that is the trade,
and it is the cheap side of it.

## Why phases never collapse — the release between phases IS the rollback

The invariant: every release's code must run correctly on both its own
schema and its neighbors'. R2's code works on R1's schema (column just
unused for reads) and R3 deploys with no schema change at all. So "rollback"
at any point means redeploying the previous release's code — no
down-migration, no data surgery, no coordination window. Collapse two
phases into one release and that invariant breaks: the moment the deploy
misbehaves, there is no release you can safely return to, and the incident
becomes a schema-repair project.

## Rollback stance: roll forward

Because the phase gap is the rollback path, a down-migration is usually
unnecessary. Write one only when it is real — dropping exactly what expand
added, nothing else. A down that pretends to restore dropped or destroyed
data is a lie that will be believed during an incident: mark contract-phase
migrations explicitly irreversible and rely on the phase gap and backups.

## Prove the phase compatibility

Before shipping each phase, on real storage with representative data: apply
the migration, then run the *previous* release's code and test suite
against the new schema. That is the direct test of the invariant above —
and the step mock-based suites structurally cannot perform.

## Grounding

- ParallelChange / expand-contract (Fowler bliki) — martinfowler.com
- "Zero-downtime Postgres migrations — the hard parts" — gocardless.com
