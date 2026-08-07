# BACKFILLS — moving data without taking the table down

A backfill is its own step — its own migration or task — never inside the
DDL migration or its transaction. One giant `UPDATE` locks every touched
row for its whole run, bloats the table, starves replication, and if it
dies at row 4M it rolls back to zero. Every rule here exists to prevent one
of those.

## Batch it

- Bounded rows per pass (start ~1k–10k; tune against production impact).
- Walk the table by primary-key range (keyset: `WHERE id > :last ORDER BY
  id LIMIT :n`), never `OFFSET` — offset re-scans everything it skips.
- Each batch is its own transaction: locks are held for one batch, not one
  table.
- Pause between batches, and watch the followers: replication lag and lock
  waits are the throttle signals. A backfill is a background tenant of the
  database, not a priority customer.

## Make each pass idempotent

The batch predicate selects only unmigrated rows — `WHERE new_col IS NULL`
(or an equivalent marker) — so re-running any batch, or the whole job, is a
no-op on completed work. Never "copy everything again"; never arithmetic
that double-applies (`SET x = x + ...` without a guard).

## Make it resumable

A backfill that dies at row 4M must pick up at row 4M — not restart from
zero, not double-write. Persist progress (last key processed, or rely on
the idempotent predicate to skip completed rows), and log it per batch:
rows done, last key, elapsed. Silence for an hour on a 50M-row job is
indistinguishable from a hang.

## Dual-write first, backfill second

Inside expand-contract (EXPAND-CONTRACT.md), the dual-write code ships
*before* the backfill runs. Otherwise rows written during the crawl are
missed and the backfill never converges. Order: expand DDL → dual-write
release → backfill history → verify → read-switch.

## Verify before anyone reads it

Before the read-switch, prove new equals old on real data: row counts of
migrated vs eligible, spot checksums or field-compare on a sample, and a
zero-count query for stragglers (`WHERE new_col IS NULL AND <eligible>`).
A backfill without a verification query is a rumor that the data moved.

## Prove the mechanics like any migration

On real storage with representative volume: run it, kill it mid-flight,
re-run it — completed rows untouched, remainder finished, totals correct.
A backfill tested only on ten rows has tested the happy path of a loop.

## Grounding

- "Zero-downtime Postgres migrations — the hard parts" — gocardless.com
- strong_migrations (backfilling outside DDL, in batches) — github.com
