# LIFECYCLE — statuses, superseding, and linking into the work

## The statuses

**Proposed → Accepted → (Deprecated | Superseded by ADR-NNNN)**

- **Proposed** — written, under discussion. Don't let proposeds
  accumulate: decide or discard within the design cycle that raised them;
  a zombie proposed is a decision being made silently elsewhere.
- **Accepted** — the decision is in force. From this moment the file is
  immutable except for its Status line.
- **Deprecated** — no longer in force and *not replaced* (the capability
  went away, the constraint dissolved).
- **Superseded by ADR-NNNN** — replaced by a newer decision, with a link
  forward. Deprecated says "we stopped"; superseded says "we changed our
  minds, and here is the new reasoning".

## Immutable once accepted — the supersede flow

New information never edits an accepted ADR — it produces a new one:

1. Write the new ADR (FORMAT.md). Its Context opens with what changed
   since the old decision, citing it: "ADR-0007 chose events; the bus is
   being retired (see ...)". Yesterday's decision was right for
   yesterday's forces — supersession is not an accusation.
2. Accept the new ADR through the normal review.
3. Touch the old file exactly once: flip Status to "Superseded by
   ADR-NNNN" with a link. Its Context, Decision, and Consequences stay
   byte-for-byte.
4. Numbers are never reused; files are never deleted.

The log's entire value is that it never rewrites history: a reader can
replay why each decision made sense with what was known at the time. Edit
one accepted record once and every record becomes untrustworthy.

## Linking it into the work

An unlinked ADR is folklore with a filename. Wire each one in:

- **Blueprint** — cites the ADR number at the exact point the decision
  appears ("consumes events, not the API (ADR-0007)"), per
  [[service-blueprint]] section 7.
- **Implementing PR** — references the ADR in its description; a reviewer
  questioning the approach reads the record, not a rehash thread.
- **Downstream challenge** — answered with the number and its context,
  not a from-scratch debate. If the challenger brings a force the Context
  never considered, that is new information: the answer is a superseding
  ADR, not a quiet edit.

## Housekeeping

- One directory: `docs/adr/`, flat, `NNNN-<kebab-title>.md` (the
  adr.github.io convention; compatible with adr-tools).
- Next number = highest existing + 1, taken at write time.
- An index/README listing number, title, status is optional but cheap —
  generate it, never hand-maintain it into staleness.

## Grounding

- ADR templates and organization — adr.github.io
- "Documenting Architecture Decisions" (Michael Nygard) — cognitect.com
