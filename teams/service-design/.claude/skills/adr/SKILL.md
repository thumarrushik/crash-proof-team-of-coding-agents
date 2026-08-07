---
name: adr
description: Capture architecturally significant decisions as short, immutable, numbered Nygard-format records that are superseded rather than edited; use when a choice is costly to reverse, constrains future work, or will need its "why" explained later.
---

# adr

Undocumented decisions decay into folklore, then get re-litigated or
accidentally reversed. The record is cheap; the archaeology is not.

## 1. Decide whether it deserves one

Architecturally significant means at least one of: costly to reverse,
constrains future designs, or someone will ask "why is it like this?" in six
months. Storage engine, sync-vs-events between two services, a boundary
split, a versioning policy, build-vs-buy — yes. Naming, formatting, anything
swappable in a day — no. When a blueprint hits a fork and you hesitate:
write the ADR; twenty minutes now beats an excavation later.

## 2. One decision, one short file

`docs/adr/NNNN-<kebab-title>.md`, sequential, a page or two at most, in
Nygard's format:

- **Status** — Proposed, then Accepted; later Deprecated or "Superseded by
  ADR-NNNN" with a link.
- **Context** — the forces at play (technical, team, deadline), written
  value-neutrally, true as of the decision date.
- **Decision** — one active-voice statement: "We will ...".
- **Consequences** — what becomes easier AND what becomes harder, including
  the new problems this decision creates. Every real decision has costs; a
  consequences section with no downsides means you haven't found them yet.

Add the rejected alternatives, one line each, with the reason each lost.

## 3. Immutable once accepted

New information never edits an accepted ADR — it produces a new ADR that
supersedes it. Touch the old file only to flip its Status and link forward.
The log's entire value is that it never rewrites history: a reader can
replay why each decision made sense with what was known at the time.

## 4. Link it into the work

The blueprint cites ADR numbers at each decision point; the implementing PR
references the ADR; when a downstream team challenges a choice, answer with
the number and its context, not a from-scratch debate.

## Blocked on sight

- Editing the Decision or Context of an accepted ADR.
- An ADR written after implementation to bless what was already built.
- "Consequences: none", or consequences listing only upsides.
- One ADR bundling several decisions; decisions living only in chat threads.

## Grounding

- "Documenting Architecture Decisions" (Michael Nygard) — cognitect.com
- ADR templates and organization — adr.github.io
- ArchitectureDecisionRecord bliki — martinfowler.com
