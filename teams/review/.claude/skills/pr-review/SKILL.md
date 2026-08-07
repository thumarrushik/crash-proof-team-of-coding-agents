---
name: pr-review
description: Review-lane standard for inspecting a PR diff — what to look for, when to block, how to label findings. Use when reviewing any pull request in this workspace.
---

# pr-review

You are the last gate before merge, and this lane cannot edit code — Write/Edit
are flagged. Findings and the verdict are your only levers; make both precise.
The bar is Google's standard: approve when the change **definitely improves
the overall code health of the system, even if it isn't perfect**. There is no
perfect code, only better code.

## How to use this skill

1. Read this file at the start of every PR review, before opening the diff.
2. Open the topic file for the step you are on (below). Don't read all of
   them — load what the review needs.

## Topic map (load on demand)

| Task | File |
|---|---|
| Inspect the diff: the six concerns, in order, with the merge bar | **[INSPECTION.md](INSPECTION.md)** |
| Calibrate to diff size — 200-400 LOC passes, oversized-diff finding | **[SIZE-AND-PASSES.md](SIZE-AND-PASSES.md)** |
| Label every finding: Conventional Comments, escalation rules | **[LABELS.md](LABELS.md)** |

## The rules in one breath

1. Approve on definite improvement to system code health, not on perfection —
   and never approve a diff that degrades it because "it works".
2. Inspect in order: design, functionality, complexity, tests, naming and
   comments, consistency. Design findings outrank everything below them.
3. Read every line you were assigned; never scan a human-written hunk and
   assume it is fine.
4. Review in 200-400 line passes — defect discovery collapses past ~400
   changed lines. An oversized, unfocused diff is itself a finding.
5. Every finding carries a Conventional Comments label and decoration,
   blockers first, each with file:line and a stated consequence.
6. Nitpicks never block and never pad a verdict; unanswered questions on
   correctness-relevant code escalate to issues.

**Blocked on sight:** a verdict written before every file of
`git diff main...HEAD` was read · a "blocking" finding with no file:line or no
stated consequence · blocking on nitpicks — or taste laundered under the
`issue` label · approving a diff that degrades system code health because "it
works".
