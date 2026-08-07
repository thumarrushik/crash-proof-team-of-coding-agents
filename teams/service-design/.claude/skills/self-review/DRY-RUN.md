# DRY-RUN — read the artifact once per consuming team

The method behind consumer-driven contracts, applied to the whole design:
the artifact is correct only from the seats of the people who must build
against it (pact.io's stance, at doc altitude). One full re-read per
consuming team — backend, frontend, testing — asking a single question:
**can they start without asking me anything?**

## The method

1. Pick one team. Re-read the artifact top to bottom *in that team's
   seat*, doing their first day's work in your head against only what the
   doc says.
2. Write down, verbatim, every question they would have to ask you. Do
   not answer inline, do not mentally patch the doc — collect first;
   answering as you go hides how many gaps there are.
3. Answer every question **in the doc, not in a reply**. A reply reaches
   one asker once; the doc reaches every reader forever — and the next
   asker is an agent that cannot ask.
4. Repeat for the next team. Re-run any team's pass after edits for it;
   a pass counts only when it yields zero questions.

## Per-team question checklists

**Backend** — could they write the first migration and endpoint today?

- Storage implied by each entity clear — and whose service owns each?
- Every operation's semantics: idempotency, ordering, transactionality?
- Every failure response specified with status + `code`?
- Anything needed from a peer available through a stated API/event — no
  hidden join across the boundary?

**Frontend** — could they build the first screen against a stub today?

- Every user-visible state renderable from stated responses: loading,
  empty, error, degraded — per operation?
- Pagination, sorting, filtering shapes stated where lists exist?
- Every enum's full value list known (something must render each)?
- Error `code` → user-facing treatment mappable without guessing?

**Testing** — could they write the acceptance suite today?

- Is every behavioral claim falsifiable as written — a test either
  passes or fails, no judgment calls?
- Seed/fixture requirements derivable from the doc?
- Every failure mode *injectable* (a way exists to force down/slow/wrong
  in a test environment)?
- The capacity section's metric observable, so its claim is checkable?

## What a found question means

Each question is a design gap, not a nuisance: classify it (missing
failure response → PASSES.md pass 1; missing number → pass 2; ambiguity →
pass 4), fix the doc, and note the class — a team whose pass produced five
questions of one class tells you which pass you under-ran.

## Grounding

- Consumer-driven contracts (design read from the consumer's seat) — pact.io
