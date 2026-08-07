---
name: tdd
description: Red-green-refactor for the generalist lane — failing test first at the boundary where the behavior is observed, failure paths included, full suite last. Use when implementing or fixing any behavior.
---

# tdd (issues lane)

You fix and build across the whole repo, so the loop is Beck's, and the only
lane-specific decision is *where* the test lives: at the boundary where the
behavior is observed.

## How to use this skill

1. Read this file before implementing or fixing any behavior.
2. Open the topic file for what you are writing (below): the loop and its
   boundary, or the failure-path and mocking rules.

## Topic map (load on demand)

| Task | File |
|---|---|
| Run red-green-refactor and pick the test's boundary | **[LOOP.md](LOOP.md)** |
| Test contracted failures; mock only true externals | **[FAILURE-PATHS.md](FAILURE-PATHS.md)** |

## The rules in one breath

1. Red first: write the test, run it, read the failure — it must fail for
   the behavior's absence, not an import or setup error.
2. Green with the minimum that passes; nothing speculative — the review lane
   treats extras as findings.
3. Refactor on green with tests untouched; tests that break under refactor
   were pinned to implementation — raise their altitude first.
4. Test at the boundary where the behavior is observed: bugs in the language
   they were seen in, features at the public surface the issue names.
5. Failure paths are first-class: red tests for bad input, missing entity,
   dependency down — exact observable outcome asserted.
6. Never mock what you own; mock only true externals at an injectable seam.
7. Full suite after your final edit, and report that run's literal result —
   green earlier does not count; stale verdicts measured wrong 3 in 10 here.

**Blocked on sight:** tests written after the code "for coverage" · the
watch-it-fail run skipped, or a red test whose failure reason was never
read · assertions on mock call counts instead of observable output · skipped
or xfail tests used to reach green.
