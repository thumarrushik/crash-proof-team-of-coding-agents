---
name: adr
description: Capture architecturally significant decisions as short, immutable, numbered Nygard-format records that are superseded rather than edited; use when a choice is costly to reverse, constrains future work, or will need its "why" explained later.
---

# adr

Undocumented decisions decay into folklore, then get re-litigated or
accidentally reversed. The record is cheap; the archaeology is not.

## How to use this skill

1. Read this file when a design fork appears. Apply the significance test
   (rule 1); when it says write, open **[FORMAT.md](FORMAT.md)** and write
   the record before moving on.
2. For status changes, superseding, or wiring ADRs into blueprints and
   PRs, open **[LIFECYCLE.md](LIFECYCLE.md)**.

## Topic map (load on demand)

| Task | File |
|---|---|
| Decide if it deserves one; write it — Nygard sections, worked example | **[FORMAT.md](FORMAT.md)** |
| Statuses, the supersede flow, linking ADRs into blueprints and PRs | **[LIFECYCLE.md](LIFECYCLE.md)** |

## The rules in one breath

1. Significant means at least one of: costly to reverse, constrains future
   designs, or someone will ask "why is it like this?" in six months. When
   a blueprint hits a fork and you hesitate: write the ADR.
2. One decision, one short file: `docs/adr/NNNN-<kebab-title>.md`,
   sequential, a page or two at most.
3. Nygard's sections: Status, Context (value-neutral forces, true as of
   the decision date), Decision ("We will ..."), Consequences — what
   becomes easier AND what becomes harder. Add rejected alternatives, one
   line each, with the reason each lost.
4. A consequences section with no downsides means you haven't found them
   yet — every real decision has costs.
5. Immutable once accepted: new information produces a new ADR that
   supersedes; touch the old file only to flip its Status and link
   forward. The log's value is that it never rewrites history.
6. Link it into the work: the blueprint cites ADR numbers at decision
   points, the implementing PR references the ADR, and downstream
   challenges are answered with the number and its context.

**Blocked on sight:** editing the Decision or Context of an accepted ADR ·
an ADR written after implementation to bless what was already built ·
"Consequences: none", or consequences listing only upsides · one ADR
bundling several decisions; decisions living only in chat threads.
