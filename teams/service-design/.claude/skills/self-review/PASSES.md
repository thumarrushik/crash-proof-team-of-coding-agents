# PASSES — hostile reads over the finished artifact

Run in order over the finished blueprint, CONTRACT.md, or ADR. Each pass is
a *search*, not a skim — the grep-for lists are literal: search the doc for
those strings. Surfacing gaps while change is still cheap is the entire
function of a design doc (Google's design-doc practice).

## 1. Unstated failure modes

Kill each dependency in your head — down, slow, wrong — and find the
sentence that says what happens. No sentence means the doc is incomplete,
not that the failure is unlikely. Then hunt the quiet ones, which no
dependency list surfaces:

- Duplicate submission (same request twice — is the operation idempotent,
  and does the doc say so?)
- Concurrent writers to one entity (last-write-wins? reject? merge?)
- Partial success — step two of three fails; what state is the world in,
  and who cleans it up?
- Replayed or out-of-order events, for anything event-consuming.

**Grep for:** "gracefully", "handle errors", "as appropriate", "if
possible", "best effort", "robust", and "retry" (a retry without a budget
and a give-up behavior is not a response). Every hit is a failure mode
without its contracted response — replace it with the exact behavior:
status + `code`, degraded shape, or queue bound.

## 2. Capacity hand-waves

**Grep for:** "fast", "slow", "large", "small", "scales", "should
handle", "high volume", "low latency", "efficiently", "significant",
"plenty", "easily". Each hit is an adjective standing where a number
belongs. Replace it with the estimate, the arithmetic behind it, and the
metric that would verify it in production (the NALSD bar — a design
review without arithmetic is an opinion exchange). If the math cannot be
done yet, write that down as a **named unknown** with a measurement plan
— an admitted gap is a design input; a hidden one is a landmine.

## 3. Boundary leaks

- Any fact with two writers? (Check the ownership table against every
  sequence/flow in the doc — the second writer usually hides in a flow
  diagram, not the table.)
- Any read reaching into a peer's tables instead of its API or events?
- Any operation quietly requiring knowledge only a peer owns — a join
  across the boundary in disguise? ("Enrich with X from Y" phrasing is
  the tell.)
- Any contract shape exposing internal storage structure — column names,
  storage enums, autoincrement IDs leaking through — welding consumers to
  the schema you wanted freedom to change?

**Grep for:** your own table and column names appearing inside contract
shapes; "directly from", "reads the", "joins".

## 4. The two-engineer test

Would two engineers, reading the artifact independently, build identical
behavior? **Grep for:** "TBD", "probably", "etc.", "and so on", "roughly",
"or similar", "as needed", "we can decide later". Then the structural
checks: every enum lists all its values; every operation lists its error
cases; every failure carries status + `code`; every limit has a number.
Every ambiguity a downstream team finds later is a design bug you chose
not to find now — and it ships as three teams' divergent guesses.

## 5. Downstream dry-run

Open **DRY-RUN.md** and walk the artifact once per consuming team. Not
optional, and not foldable into a general re-read — the seat change is
what finds the gaps.

## 6. Record residual unknowns

In the doc and REPORT.md: unverified load assumptions, unconfirmed
dependency behavior, decisions deferred with the trigger condition that
will force them. A recorded unknown is scheduled work; an unrecorded one
is an incident with a date to be named later.

## Grounding

- "Design Docs at Google" (review is the doc's function) — industrialempathy.com
- NALSD iterative design review — sre.google/workbook
