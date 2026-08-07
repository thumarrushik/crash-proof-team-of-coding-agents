# MUTATION — prove the assertions bite

A test that cannot fail is decoration. Mutation thinking asks, of every
assertion: **what small code change would this fail to catch?** If the
answer is "most of them", the test verifies the code ran, not that it
worked.

## The mental mutation pass

For each test you write or review, mentally apply the classic mutants to
the code under test and check that at least one test goes red:

- **Flip a comparison:** `<` -> `<=`, `==` -> `!=`. Survives? Your test
  never sat on the boundary — add the boundary input (EDGE-TAXONOMY.md).
- **Off-by-one a constant:** `limit` -> `limit + 1`, `0` -> `1`.
  Survives? You asserted "some items", not "exactly these".
- **Delete a guard:** remove the `if not valid: raise`. Survives? The
  failure branch has no test — the promise list is short (PROMISES.md).
- **Gut a statement:** replace the function body's effect with a no-op,
  return a constant. Survives? The assertion is `is not None` /
  `toBeDefined`-grade — it accepts anything truthy.
- **Swap boolean connectives:** `and` -> `or`, negate a condition.
  Survives? The test data satisfies both branches at once — pick inputs
  that distinguish them.

The whole-suite version of the gut check: if the implementation were
replaced with the simplest thing that type-checks, which tests still
pass? Those tests are the ones to strengthen first.

## Run the tool when the repo has one

Stryker (JS/TS), PIT (JVM), mutmut/cosmic-ray (Python) automate the
pass: they generate mutants, run the suite, and report **killed vs
survived**. That ratio — not line coverage — is the honest measure of
assertion strength, because a survived mutant is a concrete, reproducible
bug the suite would have shipped.

- Treat every survived mutant as a finding: write the test that kills
  it, or record explicitly why it is equivalent (behavior-identical)
  noise.
- Scope runs to the changed files; whole-repo mutation is a nightly job,
  not a pre-merge gate.
- Never "fix" a survived mutant by weakening the code to match the test.

## What this bar rules out

- Assertion-free tests added to move a coverage number — they kill zero
  mutants and exist only to defeat the floor detector.
- Snapshot-or-nothing suites — a snapshot kills "something changed"
  mutants but survives most logic flips inside unchanged markup.
- Over-mocked tests where the mutant lives in mocked-out code — the
  mutant survives because the real code never ran; drop the mock a
  level.

## Grounding

- Stryker Mutator docs / PIT (pitest.org) — killed vs. survived mutants
  as the honest measure of assertion strength.
- Google Testing Blog, "Code Coverage Best Practices" — coverage cannot
  measure assertion quality; mutation testing can.
