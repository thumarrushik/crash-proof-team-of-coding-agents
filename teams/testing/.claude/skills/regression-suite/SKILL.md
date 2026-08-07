---
name: regression-suite
description: Bug-to-failing-test-first discipline that keeps the suite reading as a spec. Use when fixing any defect or auditing existing coverage.
---

# regression-suite

A fixed bug without a test is a bug on a return ticket.

## Phases — in order

1. **Reproduce as a failing test first.** Before touching the fix, write a
   test that fails on current code for the same reason the user saw. If you
   cannot make it fail, you have not found the bug — stop and diagnose.
2. **Name by behavior, not by ticket.** The name states the promise:
   `rejects_expired_token_with_401`, not `test_bug_1234` or `test_fix`.
   Someone reading names alone should learn what the system guarantees.
3. **Fix until green — and everything else stays green.** Run the narrow
   test, then the full suite.
4. **File by feature/module** so the suite reads as a living spec of the
   system, not a chronicle of incidents. No separate "old bugs" bucket
   that rots.
5. **Assert at the boundary.** Inputs -> observable outputs (responses,
   events, persisted state); the test must survive any refactor that
   preserves the behavior.
6. **Sweep the neighborhood.** Bugs cluster: apply the testing-bar
   edge-case taxonomy to the function that broke and add the sibling cases
   — the same off-by-one usually lives next door.

## Blocked on sight

- A fix merged with no reproducing test.
- Test names that cite tickets instead of behavior.
- Loosening or deleting a regression test to let a new change pass.
- Asserting private internals that break on harmless refactors.
- `skip` without a reason and an owner.

## Grounding

- Kent Beck, Test-Driven Development: By Example — a defect repair starts
  with a red test that reproduces it.
- Google Testing on the Toilet: "Test Behavior, Not Implementation".
- Martin Fowler, "Self-Testing Code": the suite as an executable
  specification you can trust after every change.
