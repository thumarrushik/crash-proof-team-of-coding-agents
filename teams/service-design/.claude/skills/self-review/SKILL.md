---
name: self-review
description: Attack your own design artifact before downstream teams inherit its gaps — hunt unstated failure modes, capacity hand-waves, boundary leaks, and ambiguity, then dry-run the doc as each consuming team; use before declaring any blueprint, contract, or ADR done.
---

# self-review

A bug in a design ships as three teams' bugs, built confidently and in
parallel. The review team exists to catch what a careful author could not
see — not what you didn't look for. Run these hostile passes over the
finished artifact (blueprint, CONTRACT.md, ADR) before declaring done.

1. **Unstated failure modes.** Kill each dependency in your head — down,
   slow, wrong — and find the sentence that says what happens; no sentence
   means the doc is incomplete, not that the failure is unlikely. Then the
   quiet ones: duplicate submission, concurrent writers to one entity,
   partial success (step two of three fails), replayed or out-of-order
   events. Every named failure carries its exact contracted response.
2. **Capacity hand-waves.** Grep the doc for adjectives standing where
   numbers belong — "fast", "large", "scales", "should handle". Replace
   each with an estimate, the arithmetic behind it, and the metric that
   would verify it. If the math cannot be done yet, write that down as a
   named unknown — an admitted gap is a design input; a hidden one is a
   landmine.
3. **Boundary leaks.** Any fact with two writers? Any read reaching into a
   peer's tables instead of its API or events? Any operation quietly
   requiring knowledge only a peer owns — a join across the boundary in
   disguise? Any contract shape exposing internal storage structure,
   welding consumers to the schema?
4. **The two-engineer test.** Would two engineers, reading the artifact
   independently, build identical behavior? Hunt "TBD", "probably", "etc.",
   enums missing values, operations missing an error case, failures missing
   status + code. Every ambiguity a downstream team finds later is a design
   bug you chose not to find now.
5. **Downstream dry-run.** Re-read the artifact once per consuming team —
   backend, frontend, testing — asking only: can they start without asking
   me anything? Write down each question they would ask; answer it in the
   doc, not in a reply.
6. **Record residual unknowns** in the doc and REPORT.md: unverified load
   assumptions, unconfirmed dependency behavior, decisions deferred with
   the trigger condition that will force them.

## Blocked on sight

- "Will be defined during implementation" for behavior the contract owns.
- A capacity claim with no arithmetic behind it.
- A failure mode listed without its contracted response.
- Declaring done without the per-team dry-run.

## Grounding

- "Design Docs at Google" (review is the doc's function) — industrialempathy.com
- NALSD iterative design review — sre.google/workbook
- Consumer-driven contracts (design read from the consumer's seat) — pact.io
