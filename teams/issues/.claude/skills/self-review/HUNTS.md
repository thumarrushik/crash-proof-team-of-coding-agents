# HUNTS — six passes over your own final diff, in order

These are the passes the gating reviewer runs; run them on yourself first.
Order matters: scope first (no point polishing hunks you are about to
revert), the suite last (so every fix the hunts trigger is inside the final
run).

## 1. Trace every hunk to the issue

Re-read the diff cold, top to bottom, as if someone else wrote it. Each
hunk must be required by a sentence in the issue or by the fix itself —
including collateral the fix caused, like a comment it made stale. Anything
else is scope creep: revert it, or move the idea to "Noticed, not changed"
in the report (scope-control's mechanism). Yagni's test applies hunk by
hunk: every hunk needs a requiring sentence.

## 2. Grep the callers

For every function, signature, constant, or config key you changed: find
every call site and importer — including string references for config keys
and routes — and check the change holds at each. N-1 updated callers is a
broken build in hiding, and the review lane runs this exact hunt with your
name on the result. A changed signature with unvisited callers is blocked
on sight.

## 3. Walk the failure side

Every new or changed branch's error path must fail loud with the contracted
outcome. Hunt your own:

- broad excepts that catch more than the contract names;
- swallowed errors — caught, logged (or not), and dropped;
- silent defaults that turn a failure into a plausible-looking value.

The quiet fallback is the house's most flagged pattern. If a failure path
exists and no test pins its outcome, add the test now (tdd's
failure-paths rule) — the reviewer will otherwise add the finding.

## 4. Probe the edges you claimed to fix

Empty, missing, duplicate, zero, max, wrong type — and above all, **run the
sibling case of the bug you fixed**: the same off-by-one usually lives next
door. Fixed the last-page case? Run the empty-page case. Fixed `None`? Try
`""`. Siblings of the reported bug are in scope (scope-control); finding
one now costs a minute, finding it in review costs a cycle.

## 5. Sweep leftovers

`git status` and the diff stat are the checklist:

- No debug prints or verbose logging you added while investigating.
- No scratch files, fixtures, or notes outside the deliverable.
- No commented-out code or TODO stubs — the diff ships finished.
- No secrets or tokens anywhere, including test data.
- No test skipped, xfailed, or loosened to reach green.
- Only intended files changed — every name in the stat is one you meant.

## 6. Re-run the full suite as your final action

Every fix the hunts above triggered touched the tree — so the suite run
that backs `tests_passed` must come after all of them. Run every suite the
repo ships, as your last workspace action, and carry that run's literal
result into the report with its command and output tail.

A verdict older than your last edit is the exact failure this repo measured
at 3 wrong in 10 — including false-reds on genuinely fixed code. If
anything touches a file after this run, run again. Then write REPORT.md and
stop.

## Grounding

- Google eng-practices, "What to look for in a code review": the checks the
  gating reviewer runs — run them on yourself first.
- Martin Fowler, "Yagni": every hunk needs a requiring sentence.
- This repo's measured tests_passed experiment: the final-action run rule
  in hunt 6 is the countermeasure to stale verdicts.
