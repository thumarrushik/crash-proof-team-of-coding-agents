---
name: pr-review
description: Review-lane standard for inspecting a PR diff — what to look for, when to block, how to label findings. Use when reviewing any pull request in this workspace.
---

# pr-review

You are the last gate before merge, and this lane cannot edit code — Write/Edit
are flagged. Findings and the verdict are your only levers; make both precise.

## The bar

Approve when the change **definitely improves the overall code health of the
system, even if it isn't perfect** (Google's standard). There is no perfect
code, only better code — never block on polish you would not stake a merge on.

## What to inspect, in order

1. **Design** — does this change belong here, and does it integrate with the
   system or fight it? A CL that degrades code health is not accepted.
2. **Functionality** — does the code do what the PR claims, for its users and
   its edges (empty, missing, duplicate, concurrent, unavailable dependency)?
3. **Complexity** — could it be simpler? Would the next reader understand it
   without archaeology? Speculative generality is a complexity finding.
4. **Tests** — correct, behavioral (they would fail if the change were
   reverted), covering failure branches, not only the happy path.
5. **Naming and comments** — names say what a thing is; comments say *why*,
   not what. A comment the diff just made stale is a finding.
6. **Consistency** — matches surrounding conventions; a diff importing its
   own style is a design finding, not taste.

Read every line you were assigned; never scan a human-written hunk and assume
it is fine. Calibrate to size: defect discovery collapses past ~400 changed
lines (SmartBear/Cisco: a 200-400 LOC pass over 60-90 minutes finds 70-90% of
defects). Review large diffs in 200-400 line passes, and record that an
oversized, unfocused diff resisted review — that is itself a finding.

## Labeling findings (Conventional Comments)

Every finding carries a label and decoration, blockers listed first:
- `issue (blocking): file:line — what breaks and why` — must be fixed to merge.
- `suggestion (non-blocking): ...` — improvement with reasoning, author's call.
- `nitpick (non-blocking): ...` — polish; never blocks, never pads a verdict.
- `question: ...` — intent you could not determine; unanswered questions on
  correctness-relevant code escalate to issues.

## Blocked on sight

- A verdict written before every file of `git diff main...HEAD` was read.
- A "blocking" finding with no file:line or no stated consequence.
- Blocking on nitpicks — or taste laundered under the `issue` label.
- Approving a diff that degrades system code health because "it works".

## Grounding

- Google eng-practices: "What to look for in a code review" and "The Standard
  of Code Review" (google.github.io/eng-practices).
- SmartBear/Cisco study (2,500 reviews, 3.2M LOC): 200-400 LOC per pass,
  defect density drops past ~500 LOC/hour.
- Conventional Comments (conventionalcomments.org): label + decoration format.
