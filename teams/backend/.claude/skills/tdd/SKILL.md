---
name: tdd
description: Red-green-refactor for backend work with the test boundary chosen so tests cannot lie — contract-level tests over real HTTP and storage by default, pure unit tests only for genuine logic, mocks only at owned seams for true externals; use when implementing or fixing any backend behavior.
---

# tdd

Red-green-refactor, with the backend twist that decides whether the tests
mean anything: choose the test boundary *before* writing the test, so the
suite cannot pass while the service is broken.

## How to use this skill

1. Read this file every time you implement or fix backend behavior — the
   loop below runs for every behavior, no exceptions.
2. Before the first red test, open **[BOUNDARIES.md](BOUNDARIES.md)** to
   choose the altitude. For failure cases and bug fixes, open
   **[FAILURE-PATHS.md](FAILURE-PATHS.md)**.

## Topic map (load on demand)

| Task | File |
|---|---|
| Choose the test altitude; what may be mocked and what never | **[BOUNDARIES.md](BOUNDARIES.md)** |
| Test the failure side; write a bug-fix regression test | **[FAILURE-PATHS.md](FAILURE-PATHS.md)** |

## The loop + rules in one breath

1. **Red.** Write the test first, run it, read the failure — it must fail
   for the behavior's absence, not an import error. A test never seen
   failing proves nothing.
2. **Green.** Implement the minimum that passes. No speculative branches.
3. **Refactor on green, tests untouched.** If a refactor forces test edits,
   the tests were pinned to implementation — raise their altitude first.
4. Full suite green before the next behavior; run once more after the final
   edit and report that number.
5. Default altitude is the service contract: HTTP in, envelope out, real
   storage underneath. Drop to a pure unit test only for genuine logic.
6. Never mock what you own; mock true externals only, at the injectable
   seam, pinned by a real-contract test.
7. Failure paths get red tests asserting status + error `code`; bug fixes
   start from a failing test at the boundary where the bug was observed.

**Blocked on sight:** tests written after the code "for coverage" ·
assertions on mock call counts or call order instead of observable output ·
a mocked own-database or own-repository layer anywhere · an endpoint marked
tested with no test that speaks HTTP to it · skipped or xfail tests used to
reach green.
