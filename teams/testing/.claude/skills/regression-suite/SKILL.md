---
name: regression-suite
description: Bug-to-failing-test-first discipline that keeps the suite reading as a spec. Use when fixing any defect or auditing existing coverage.
---

# regression-suite

A fixed bug without a test is a bug on a return ticket. Every defect
becomes a failing test before it becomes a fix, and every test lands
where it keeps the suite reading as a living specification — not a
chronicle of incidents.

## How to use this skill

1. Read this file when fixing any defect or auditing existing coverage —
   before touching the fix, not after.
2. Open BUG-TO-TEST.md for the repair procedure itself; open
   SUITE-AS-SPEC.md when naming, filing, or auditing tests so the suite
   stays a spec.

## Topic map (load on demand)

| Task | File |
|---|---|
| Repair a defect — reproduce as a red test, fix to green, sweep the neighborhood | **[BUG-TO-TEST.md](BUG-TO-TEST.md)** |
| Name, file, and assert so the suite reads as a living spec — and audit it | **[SUITE-AS-SPEC.md](SUITE-AS-SPEC.md)** |

## The rules in one breath

1. Reproduce as a failing test first — it must fail on current code for
   the same reason the user saw; if you cannot make it fail, you have
   not found the bug. Stop and diagnose.
2. Name by behavior, not by ticket: `rejects_expired_token_with_401`,
   never `test_bug_1234`.
3. Fix until green — and everything else stays green: narrow test, then
   the full suite.
4. File by feature/module so the suite reads as a spec; no "old bugs"
   bucket that rots.
5. Assert at the boundary — inputs -> observable outputs; the test must
   survive any refactor that preserves the behavior.
6. Sweep the neighborhood: bugs cluster — apply the testing-bar edge
   taxonomy to the function that broke and add the sibling cases.

**Blocked on sight:** a fix merged with no reproducing test · test names
that cite tickets instead of behavior · loosening or deleting a
regression test to let a new change pass · asserting private internals
that break on harmless refactors · `skip` without a reason and an owner.
