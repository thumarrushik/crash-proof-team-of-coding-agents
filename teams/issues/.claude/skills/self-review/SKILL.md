---
name: self-review
description: Review your own diff as the reviewer who gates your merge will — scope traced to the issue, callers checked, error paths loud, leftovers gone, last run cited. Use before writing REPORT.md on any issue.
---

# self-review (issues lane)

Your diff goes straight to a review lane that greps for callers, hunts the
missing hunk, and re-runs the suite. Find what it will find, first.

## How to use this skill

1. Read this file when the implementation feels done, before writing
   REPORT.md.
2. Load the topic file (below) and run its six hunts in order over the final
   diff — they mirror the gating reviewer's own passes.

## Topic map (load on demand)

| Task | File |
|---|---|
| Run the six pre-report hunts over the final diff | **[HUNTS.md](HUNTS.md)** |

## The rules in one breath

1. Trace every hunk to a requiring sentence in the issue — anything else is
   scope creep: revert it or move it to "Noticed, not changed".
2. Grep every changed symbol's callers and check the change holds at each;
   N-1 updated callers is a broken build in hiding.
3. Walk the failure side: every new branch fails loud with the contracted
   outcome — hunt your own broad excepts and silent defaults.
4. Probe the edges you claimed to fix — run the sibling case of the bug; the
   same off-by-one usually lives next door.
5. Sweep leftovers: no debug prints, scratch files, commented-out code, TODO
   stubs, secrets, or skipped tests; only intended files changed.
6. Re-run the full suite as your final action and carry that literal result
   into `tests_passed` — a verdict older than your last edit is the exact
   failure this repo measured at 3 wrong in 10.

**Blocked on sight:** declaring done from a remembered or assumed test run ·
a changed signature with unvisited callers · a swallowed exception or silent
default anywhere in the diff · scratch files, debug output, or drive-by
refactors riding along.
