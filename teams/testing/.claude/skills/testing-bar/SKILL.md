---
name: testing-bar
description: The bar every suite must clear — behavior coverage over line coverage, edge-case taxonomy, mutation-minded assertions. Use when writing, fixing, or reviewing tests and quality gates.
---

# testing-bar

Tests are executable evidence. A suite passes this bar when a reader can
trust green — not when a coverage number looks good. Coverage finds
untested code; it never proves tested code is verified.

## How to use this skill

1. Read this file when writing, fixing, or reviewing tests or quality
   gates — before trusting any green, yours or anyone's.
2. Open the topic file for the step you are on: enumerating what to
   test, stress-testing the inputs, or stress-testing the assertions.

## Topic map (load on demand)

| Task | File |
|---|---|
| Decide what to test — one test per promise, failure branches, coverage as floor detector | **[PROMISES.md](PROMISES.md)** |
| Generate the inputs that break code — the edge-case taxonomy, checklist form | **[EDGE-TAXONOMY.md](EDGE-TAXONOMY.md)** |
| Prove assertions bite — mutation-minded self-check, mutation tools | **[MUTATION.md](MUTATION.md)** |

## The rules in one breath

1. Enumerate promises, not lines: one test per behavior the code claims,
   including every failure branch with its exact observable outcome.
2. Line coverage is a floor detector, never a target.
3. Run the edge-case taxonomy against every input; then ask "what input
   would embarrass us in production?" — that input is the missing test.
4. Mutation-minded self-check: for each assertion, name the small code
   change it would fail to catch; if none would go red, the assertion is
   decoration. Run the repo's mutation tool when it has one.
5. Behavior over implementation: assert inputs -> observable outputs at
   the public boundary; a behavior-preserving refactor must not break
   the suite.
6. Report evidence: narrow test first, then the wide suite or build gate;
   state the exact command and result.

**Blocked on sight:** `is not None` / `toBeDefined` as the only
assertion · tests that still pass with the implementation gutted ·
chasing a coverage percentage with assertion-free tests ·
happy-path-only suites; sleeps added to "stabilize".
