# DDL-SAFETY — locks, idempotence, and the hazard catalog

Two properties every migration must have: **idempotent** — a re-run is a
no-op, never an error — and **low-lock** — it cannot stall production
writers while it works. Postgres wording below; the hazards and recipes
transfer to any MVCC database.

## The lock trap (GoCardless's hard parts)

Most DDL takes ACCESS EXCLUSIVE on the table — blocking all reads and
writes. The trap is not the DDL's own duration: a "fast" ALTER queues
behind any long-running query already touching the table, and then *every*
other query queues behind the waiting ALTER. A one-millisecond migration
can take the service down for minutes. Two standing defenses:

- Set `lock_timeout` (and a `statement_timeout`) for every migration so a
  blocked one fails fast — then retry — instead of parking the whole write
  path behind it.
- Keep each migration's transaction tiny: one concern, no data movement,
  no waiting on anything slow.

## Hazard catalog — what you want vs the safe recipe

| You want | Naive hazard | Safe recipe |
|---|---|---|
| New index | `CREATE INDEX` blocks writes for the whole build | `CREATE INDEX CONCURRENTLY`, outside a transaction; on failure it leaves an INVALID index — drop it and retry |
| NOT NULL on existing column | Full-table scan under ACCESS EXCLUSIVE | Add `CHECK (col IS NOT NULL) NOT VALID`, then `VALIDATE CONSTRAINT` in a separate statement (SHARE UPDATE EXCLUSIVE only); then the NOT NULL itself is cheap |
| Foreign key | Validates every existing row, locking both tables | Add `NOT VALID`, then `VALIDATE CONSTRAINT` separately |
| New column with default | On old Postgres (<11) or with a volatile default: full table rewrite | Add nullable column, set the default, backfill (BACKFILLS.md), then tighten |
| Change a column's type | Table rewrite under ACCESS EXCLUSIVE | New column + dual-write + backfill + switch — expand-contract (EXPAND-CONTRACT.md) |
| Rename column/table | Breaks the running release instantly | Never in one step — expand-contract |
| Drop a column | Old release still selects it | Contract phase only, after a full deploy cycle with no readers |

This is the same hazard class the strong_migrations and safe-pg-migrations
catalogs enforce mechanically in Rails shops — when unsure whether an
operation is safe, check those catalogs before running it anywhere.

## Idempotence — guard every statement

A migration that dies halfway will be re-run; every statement must
tolerate that. `IF NOT EXISTS` / `IF EXISTS` where the dialect has it;
explicit existence checks (catalog queries) where it doesn't — including
for constraints, enum values, and seed rows. The test is mechanical: apply
the migration twice on real storage; the second run must be a clean no-op,
never an error (this is part of the standing verification bar in SKILL.md).

## One concern per migration

- DDL and data movement (DML) never share a migration or a transaction —
  a backfill inside a DDL transaction holds its locks for the whole crawl.
- Concurrent index builds get their own non-transactional migration file.
- Never edit an already-applied migration; append a new one. Never hand-run
  DDL — everything rides the rail ([[lean-service]] MIGRATIONS.md).

## Grounding

- "Zero-downtime Postgres migrations — the hard parts" — gocardless.com
- strong_migrations & safe-pg-migrations lock-hazard catalogs — github.com
