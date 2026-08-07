---
name: tdd
description: Red-green-refactor for the generalist lane — failing test first at the boundary where the behavior is observed, failure paths included, full suite last. Use when implementing or fixing any behavior.
---

# tdd (issues lane)

You fix and build across the whole repo, so the loop is Beck's, and the only
lane-specific decision is *where* the test lives: at the boundary where the
behavior is observed.

## The loop

1. **Red.** Write the test first, run it, and read the failure — it must
   fail for the behavior's absence (the right assertion or exception), not
   an import or setup error. A test never seen failing proves nothing.
2. **Green.** Implement the minimum that passes. Nothing speculative — that
   is scope-control's line, and the review lane treats extras as findings.
3. **Refactor on green, tests untouched.** If a refactor forces test edits,
   the tests were pinned to implementation, not behavior — raise their
   altitude first, then refactor.
4. **Full suite last.** Run every suite the repo ships after your final
   edit, and report that run's literal result. Green earlier does not count;
   this repo measured stale verdicts wrong 3 runs in 10.

## Choosing the boundary

- **Bug fixes**: the regression test speaks the language the bug was
  observed in — seen over HTTP, the test speaks HTTP; seen in a function's
  return value, the test calls the function. repro-first freezes this test
  before the fix exists.
- **Features**: test at the public boundary the issue names (endpoint, CLI,
  exported function), not at private helpers that refactors will rename.
- **Failure paths are first-class.** Each behavior gets red tests for its
  contracted failures — bad input, missing entity, dependency down — with
  the exact observable outcome asserted, not merely "an exception happened".
- **Never mock what you own.** Mock only true externals at an injectable
  seam; a mocked-out own-layer lets the actual wiring be wrong while the
  suite stays green.

## Blocked on sight

- Tests written after the code "for coverage".
- The watch-it-fail run skipped, or a red test whose failure reason was
  never read.
- Assertions on mock call counts instead of observable output.
- Skipped or xfail tests used to reach green.

## Grounding

- Kent Beck, Test-Driven Development: By Example — red, green, refactor.
- Martin Fowler, "Self-Testing Code" and "Mocks Aren't Stubs": behavior
  over implementation; sociable tests by default.
- This repo's measured experiment (the-agent-grades-its-own-homework):
  the final-run rule exists because remembered verdicts were wrong 3/10.
