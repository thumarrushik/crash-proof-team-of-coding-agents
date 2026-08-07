# FREEZE — the repro becomes a failing test before any fix

A reproduction that lives in your transcript dies with your session. Freeze
it into the repo's suite as a failing test, and it becomes three permanent
things: the issue's acceptance line, the fix loop's target, and a regression
guard that outlives everyone involved.

## Translate the MRE into a test

1. Put it in the repo's suite, in the conventional place for the code under
   test, named for the behavior (and the issue, if the repo's convention
   includes issue IDs) — not `test_bug.py`.
2. Carry the MRE over whole: its inlined data, its minimal steps, its exact
   assertion on the wrong behavior. The test asserts what *correct* looks
   like, so today it fails by showing the reported wrongness.
3. Keep it as readable as the MRE was — this test will be the first thing
   the next investigator of a recurrence reads.

## Watch it fail — for the right reason

Run the test now, before any fix, and inspect the failure:

- It must fail on the **right assertion or the reported exception** — the
  same wrongness you recorded in Phase 1 of MRE.md.
- A test that fails on an import error, a missing fixture, a typo, or a
  wrong path is a broken test, not a frozen bug. Fix the test until its
  failure *is* the bug.
- A test that **passes** before the fix proves it does not capture the bug —
  back to MRE.md; some necessary ingredient got lost in translation.

Record the failing run: command and output tail, same discipline as any
verdict. This is the "before" photograph the fix will be judged against.

## The test is the acceptance line

From this point the issue has a mechanical definition of done:

- The fix greens this test.
- The full suite stays green around it.
- The test remains in the suite forever, pinning the bug against
  regression. Deleting or weakening it later reopens the bug's front door.

## Only now open the fix loop

With the frozen test failing for the right reason, hand off to the tdd
skill: the smallest change that greens the frozen test, then the full suite.
Not before — a fix written ahead of the frozen test has no proof it fixes
the reported bug rather than a neighboring one, and nothing stops the bug
from returning next quarter.

## Grounding

- TDD bug-fix practice: regression test first, watch it fail for the right
  reason, then fix.
- Stack Overflow MRE guidance: verify the repro actually fails — the
  frozen-test failure run is that verification, made permanent.
