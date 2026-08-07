# FORMAT — deciding, then writing, a Nygard record

## Does it deserve one?

Architecturally significant means at least one of: **costly to reverse**,
**constrains future designs**, or **someone will ask "why is it like
this?" in six months**.

- Yes: storage engine choice, sync-vs-events between two services, a
  boundary split, a versioning policy, build-vs-buy, an auth model.
- No: naming, formatting, library choices swappable in a day, anything a
  linter could arbitrate.
- The hesitation rule: when a blueprint hits a fork and you pause to
  weigh it, that pause *is* the signal — write the ADR. Twenty minutes
  now beats an excavation later.

## One decision, one short file

`docs/adr/NNNN-<kebab-title>.md` — sequential number, never reused, a page
or two at most, plain markdown in the repo next to the code it governs
(Nygard's format; template variants at adr.github.io). One decision per
file: a record bundling three choices can't be superseded when one of
them changes.

## The sections

- **Title** — `ADR-NNNN: <the decision as a phrase>`.
- **Status** — Proposed, then Accepted; later Deprecated or "Superseded
  by ADR-NNNN" with a link (flows in LIFECYCLE.md).
- **Context** — the forces at play: technical, team, deadline,
  political. Written **value-neutrally** — describing the situation, not
  selling the decision — and true as of the decision date; it is the
  section future readers need most.
- **Decision** — one active-voice statement: "We will ...". Stated as a
  response to the forces, not a specification dump.
- **Consequences** — what becomes easier AND what becomes harder,
  including the new problems this decision creates. Every real decision
  has costs; a consequences section with no downsides means you haven't
  found them yet.
- **Alternatives** — each rejected option, one line, with the reason it
  lost. One line is the discipline: if an alternative needs a page, it
  deserved its own design discussion first.

## Worked example — the shape and length to copy

    # ADR-0007: Billing consumes order events, not the orders API

    Status: Accepted (2026-08-06)

    Context: Invoices need order totals within a minute. Synchronous
    calls would couple checkout latency to billing availability;
    orders is on a weekly deploy cadence, billing daily. Both teams
    already run the shared event bus.

    Decision: We will publish OrderPlaced events; billing consumes
    them and materializes its own totals.

    Consequences: Checkout no longer blocks on billing (easier).
    Billing totals are eventually consistent — the UI must show
    invoice state as pending (harder). We now own replay and
    duplicate-delivery handling in billing (new problem).

    Alternatives: Sync REST call — rejected: couples checkout
    availability to billing. Shared table — rejected: two writers,
    violates one-writer-per-fact.

Everything load-bearing, nothing else. If your draft is three times this
length, it is probably a design doc wearing an ADR's filename — cut it or
promote it.

## Grounding

- "Documenting Architecture Decisions" (Michael Nygard) — cognitect.com
- ArchitectureDecisionRecord bliki — martinfowler.com
