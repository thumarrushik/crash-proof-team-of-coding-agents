---
name: tdd
description: Test-driven UI development — failing behavior test first, Testing Library queries by role, trophy-shaped coverage. Use when implementing or fixing any component, hook, or user-visible behavior.
---

# tdd (frontend lane)

Red, green, refactor — where "red" is a user-shaped behavior test, not a
snapshot. Write the behavior test first, watch it fail for the right
reason, implement the minimum to pass, then refactor with the suite green.

## How to use this skill

1. Read this file before implementing or fixing any component, hook, or
   user-visible behavior — the failing test comes before the code, and a
   bug fix starts with a failing test that reproduces it.
2. Open TROPHY.md when deciding what kind of test to write and at what
   altitude; open RENDER-STATES.md when writing the tests for a component
   that fetches or can fail.

## Topic map (load on demand)

| Task | File |
|---|---|
| Choose test altitude — trophy shape, integration default, what to unit-test, when e2e | **[TROPHY.md](TROPHY.md)** |
| Cover loading/empty/error/success — driving and asserting each render state | **[RENDER-STATES.md](RENDER-STATES.md)** |

## The rules in one breath

1. Red: write the behavior test first and run it to watch it fail for the
   right reason — render, query like a user (getByRole with name,
   getByLabel), interact via userEvent, assert the visible outcome.
2. Green: minimum implementation to pass. Nothing speculative.
3. Refactor with confidence: good UI tests survive markup and styling
   refactors — if reshuffling divs breaks a test, fix the test's altitude.
4. Pick altitude by the trophy — mostly component integration tests, with
   network mocked at the HTTP boundary; unit-test extracted pure logic;
   one e2e per changed user story (hand that to browser-e2e).
5. Cover all four render states: loading, empty, error, success each get
   a behavior assertion — error paths are not optional.
6. Suite green before the next behavior: run the whole suite and show the
   output; never report done on an unrun or red suite.

**Blocked on sight:** snapshot tests standing in as behavior
verification · querying by class or test-id when a role or label exists ·
asserting component internals (state, props, instance methods) · tests
written after the code just to raise coverage · skipping the
watch-it-fail run.
