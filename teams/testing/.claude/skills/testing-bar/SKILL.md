---
name: testing-bar
description: The bar every suite must clear — behavior coverage over line coverage, edge-case taxonomy, mutation-minded assertions. Use when writing, fixing, or reviewing tests and quality gates.
---

# testing-bar

Tests are executable evidence. A suite passes this bar when a reader can
trust green — not when a coverage number looks good.

## Phases — in order

1. **Enumerate promises, not lines.** List the behaviors the code claims
   (spec, docstrings, API contract) and write one test per promise —
   including every failure branch (422/404/409/503, timeouts, rejections)
   with its exact observable outcome. Line coverage only finds untested
   code; it never proves tested code is verified. Treat it as a floor
   detector, never a target.
2. **Run the edge-case taxonomy** against every input: empty/null/missing;
   boundaries (0, 1, max, max+1, off-by-one); duplicates and ordering;
   hostile strings (unicode, whitespace, injection-shaped); huge inputs;
   repeated and concurrent calls; wrong types. Then ask: "what input would
   embarrass us in production?" — that input is the missing test. Add it.
3. **Mutation-minded self-check.** For each assertion ask: what small code
   change would this fail to catch? Mentally flip a comparison, off-by-one
   a boundary, delete a guard — if no test would go red, the assertion is
   decoration. Run a mutation tool (Stryker, PIT, mutmut) when the repo has
   one; every survived mutant is a reproducible bug the suite would ship.
4. **Behavior over implementation.** Assert inputs -> observable outputs at
   the public boundary; a refactor that preserves behavior must not break
   the suite.
5. **Report evidence.** Run the narrow test first, then the wide suite or
   build gate that would catch integration breakage. State the exact
   command and result.

## Blocked on sight

- `is not None` / `toBeDefined` as the only assertion.
- Tests that still pass with the implementation gutted.
- Chasing a coverage percentage with assertion-free tests.
- Happy-path-only suites; sleeps added to "stabilize".

## Grounding

- Google Testing Blog, "Code Coverage Best Practices" (2020): high coverage
  does not guarantee effective tests.
- Stryker / PIT mutation-testing docs: killed vs. survived mutants as the
  honest measure of assertion strength.
- Martin Fowler, "TestCoverage" bliki: coverage finds untested code; as a
  target it is gameable.
