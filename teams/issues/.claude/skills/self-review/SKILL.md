---
name: self-review
description: Review your own diff as the reviewer who gates your merge will — scope traced to the issue, callers checked, error paths loud, leftovers gone, last run cited. Use before writing REPORT.md on any issue.
---

# self-review

Your diff goes straight to a review lane that greps for callers, hunts the
missing hunk, and re-runs the suite. Find what it will find, first.

1. **Trace every hunk to the issue.** Re-read the diff cold, top to bottom.
   Each hunk must be required by a sentence in the issue or by the fix
   itself; anything else is scope creep — revert it or move the idea to
   "Noticed, not changed" in the report (scope-control).
2. **Grep the callers.** For every function, signature, constant, or config
   key you changed: find every call site and importer, and check the change
   holds at each. N-1 updated callers is a broken build in hiding — the
   review lane will run this exact hunt.
3. **Walk the failure side.** Every new branch's error path must fail loud
   with the contracted outcome. Hunt your own broad excepts, swallowed
   errors, and silent defaults — the quiet fallback is the house's most
   flagged pattern.
4. **Probe the edges you claimed to fix.** Empty, missing, duplicate, zero,
   max, wrong type — run the sibling case of the bug you fixed; the same
   off-by-one usually lives next door.
5. **Sweep leftovers.** No debug prints, no scratch files, no commented-out
   code, no TODO stubs, no secrets or tokens, no test skipped to get green.
   Only intended files changed — `git status` and the diff stat are the
   checklist.
6. **Re-run the full suite as your final action** and carry that literal
   result into `tests_passed`. If any fix in steps 1-5 touched a file after
   your last run, run again — a verdict older than your last edit is the
   exact failure this repo measured at 3 wrong in 10.

## Blocked on sight

- Declaring done from a remembered or assumed test run.
- A changed signature with unvisited callers.
- A swallowed exception or silent default anywhere in the diff.
- Scratch files, debug output, or drive-by refactors riding along.

## Grounding

- Google eng-practices, "What to look for in a code review": the checks the
  gating reviewer runs — run them on yourself first.
- Martin Fowler, "Yagni": every hunk needs a requiring sentence.
- This repo's measured tests_passed experiment: the final-action run rule
  in step 6 is the countermeasure to stale verdicts.
