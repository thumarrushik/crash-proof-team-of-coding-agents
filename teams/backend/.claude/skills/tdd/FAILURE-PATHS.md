# FAILURE-PATHS — the error side is first-class behavior

The happy path is half the contract. Each behavior gets red tests for its
contracted failures, written in the same red-green loop as the feature —
failure handling that was never tested red is failure handling that has
never been seen working.

## Enumerate, then test each

For every behavior, list its contracted failures before implementing:

- **Bad input** — malformed body, out-of-range value, missing required
  field, invalid enum member.
- **Missing entity** — the ID that isn't there, the tenant that doesn't own
  it (reads as not-found, never as someone else's row).
- **Conflict** — duplicate create, stale update, state-machine violation.
- **Dependency down** — the external seam fails or times out.

One red test per failure, asserting **status + machine `code` from the
canonical envelope** — not merely "an exception happened", and never a
pattern-match on `message` prose. The envelope is contract
([[api-contracts]]); its tests live at contract altitude, over real HTTP.

## Simulating the failure honestly

- Bad input, missing entity, conflict: real requests against real storage —
  no simulation needed; construct the state and send the request.
- Dependency down: configure the *injectable seam* (BOUNDARIES.md) to fail
  or time out — allowed because the dependency is a true external. Assert
  the mapped envelope (e.g. 503 + `code`), and that nothing was silently
  swallowed or defaulted: no fabricated fallback body, no 200-with-error.

## Bug fixes: regression test first, always

1. **Reproduce at the boundary where the bug was observed.** Seen over
   HTTP → the regression test speaks HTTP. Seen in a calculation → a unit
   test on that function. Never translate downward for convenience; a unit
   test can pass while the HTTP-visible bug lives on in the wiring.
2. **Watch it fail for the bug's reason.** The failure message must exhibit
   the reported symptom — wrong value, wrong status, wrong `code`. A test
   failing for a setup error reproduces nothing.
3. **Fix minimally, go green,** full suite green, and the test stays in the
   suite forever — named after the behavior (or issue) so its future
   failure reads as "this bug is back".

Fix-then-test is blocked: a test written after the fix has never been seen
failing on the bug, so it proves nothing about it (the red-first discipline
is the point of Beck's loop, and bug fixes are its purest case).

## Blocked on sight

- A failure path asserted as "raises an exception" with no status + `code`.
- A dependency-down case handled by returning fake data (silent fallback).
- A bug fix merged without a regression test that failed first.
- Skipped or xfail tests parked on the failure side to reach green.

## Grounding

- Test-Driven Development: By Example (Kent Beck) — red first, smallest step
