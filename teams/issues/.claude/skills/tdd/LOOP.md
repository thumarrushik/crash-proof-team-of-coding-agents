# LOOP — red, green, refactor, full suite

The loop is Beck's, run without shortcuts. Each phase has one job and one
proof; skipping a proof converts the loop into ordinary code-then-hope with
extra steps.

## Red

Write the test first. Run it. **Read the failure.**

The failure must be the behavior's absence: the right assertion failing, or
the contracted exception not raised. A test that fails on an import error, a
missing fixture, or a typo has proven only that it is broken — fix the test
until its red *is* the missing behavior.

A test never seen failing proves nothing: it may pass vacuously, assert the
wrong thing, or test code that isn't wired in. The watch-it-fail run is the
test's own test, and it happens exactly once — now, while the behavior
doesn't exist. Skipping it is blocked on sight.

## Green

Implement the **minimum** that passes. Not the elegant version, not the
general version, not the version with the parameter the next issue might
want — that is scope-control's line, and the review lane treats extras as
findings. Ugly-but-passing is a legitimate state of the loop; the next phase
exists precisely so you can afford it.

Run the test. Green means this test passes for the right reason — glance at
what it asserted, not just the exit code.

## Refactor — on green, tests untouched

With green as your safety net, improve the code: names, duplication,
structure. Two constraints:

- **Only on green.** Refactoring on red is changing two things at once with
  no net.
- **Tests untouched.** If a refactor forces test edits, the tests were
  pinned to implementation, not behavior. Stop, raise their altitude —
  assert observable outcomes at the boundary instead of internals — and
  then refactor. Tests that survive honest refactors are the only ones
  worth keeping.

## Choosing the boundary

Where the test lives is the lane's one real decision: **the boundary where
the behavior is observed.**

- **Bug fixes:** the regression test speaks the language the bug was
  observed in. Seen over HTTP, the test speaks HTTP; seen in a function's
  return value, the test calls the function. repro-first freezes this test
  before the fix exists — the loop's red phase is already done when the
  frozen test fails right.
- **Features:** test at the public boundary the issue names — endpoint,
  CLI, exported function — not at private helpers that refactors will
  rename. Helper-level tests calcify the current decomposition and die in
  the first cleanup.

## Full suite last

After your **final** edit, run every suite the repo ships, and report that
run's literal result. Green earlier does not count — this repo measured
remembered verdicts wrong 3 runs in 10, mostly stale reds from before the
fix landed. The final full-suite run must be your last workspace action;
the review lane checks transcript order for exactly this.

## Grounding

- Kent Beck, Test-Driven Development: By Example — red, green, refactor.
- This repo's measured experiment (the-agent-grades-its-own-homework): the
  final-run rule exists because remembered verdicts were wrong 3/10.
