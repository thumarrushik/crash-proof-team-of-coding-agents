---
name: tdd
description: Test-driven UI development — failing behavior test first, Testing Library queries by role, trophy-shaped coverage. Use when implementing or fixing any component, hook, or user-visible behavior.
---

# tdd (frontend lane)

Red, green, refactor — where "red" is a user-shaped behavior test, not a
snapshot.

## Phases — in order

1. **Red.** Write the behavior test first and run it to watch it fail for
   the right reason. Render the component, find elements the way a user
   would (getByRole with name, getByLabel), interact via userEvent, assert
   the visible outcome. A bug fix starts the same way: a failing test that
   reproduces it.
2. **Green.** Minimum implementation to pass. Nothing speculative.
3. **Refactor with confidence.** Good UI tests survive markup and styling
   refactors; if renaming a class or reshuffling divs breaks a test, the
   test asserted the wrong thing — fix the test's altitude.
4. **Pick altitude by the trophy — mostly integration.** Default: component
   integration tests (component + children + hooks, network mocked at the
   HTTP boundary, MSW-style handlers). Unit-test pure logic extracted from
   components (formatting, validation, reducers). One e2e per changed user
   story — hand that to browser-e2e. Static analysis (types, lint) is the
   base layer, not a substitute for any of the above.
5. **Cover all four render states.** Loading, empty, error, success each
   get a behavior assertion (see design-ui) — error paths are not optional.
6. **Suite green before the next behavior.** Run the whole suite and show
   the output; never report done on an unrun or red suite.

## Blocked on sight

- Snapshot tests standing in as behavior verification.
- Querying by class or test-id when a role or label exists.
- Asserting component internals (state, props, instance methods).
- Tests written after the code just to raise coverage.
- Skipping the watch-it-fail run.

## Grounding

- Kent C. Dodds: "Write tests. Not too many. Mostly integration." and the
  Testing Trophy.
- Testing Library Guiding Principles and query priority (role first).
- Kent C. Dodds, "Common Mistakes with React Testing Library".
- Kent Beck, Test-Driven Development: By Example (red/green/refactor).
