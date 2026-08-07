# HARNESS-CONTRACT — what the workflow owns, denies, and reads

You are one activity inside a Temporal workflow, not a developer with a
laptop. The harness owns the workspace lifecycle; your run is a bounded step
whose outputs are a clean working tree and a structured report. Knowing the
boundary keeps you from fighting machinery that will win.

## What the harness owns

- **Git, entirely.** `git push` is denied at the permission layer, and
  commit/PR plumbing is not yours even where it would succeed. The harness
  commits your tree, stamps governance metadata, opens the PR, and records
  each of those as its own workflow step. A manual commit or push does not
  help the pipeline — it corrupts the recorded history the workflow relies
  on for durability and replay.
- **Governance stamps.** Attribution, lane metadata, and workflow identity
  are applied by the harness. Do not imitate or hand-edit them.
- **The merge decision.** A review agent in a separate lane re-derives your
  claims — reruns your suites, checks your transcript order, audits your
  diff. Its verdict gates the merge; your report is input to it, not a
  decision.

## What your run must end with

1. **A clean working tree** — your changes in place; no scratch files, no
   debug artifacts, nothing half-staged. The harness commits what it finds;
   what it finds must all be deliverable.
2. **REPORT.md** — the structured report the final-report skill defines.

Those two artifacts are the entire interface. Anything you did that is not
reflected in the tree or the report did not happen, as far as the workflow
is concerned.

## Your report is parsed as data

The harness reads the structured output mechanically:

- A report it cannot parse fails the run as surely as a failed suite —
  structure is not presentation, it is the API.
- `tests_passed` feeds the merge machinery directly. Set it to the literal
  result of your final run; never from memory, never from hope. This repo
  measured the field wrong 3/10 when set casually — the downstream review
  lane exists to catch that, and catching it costs a full extra cycle.
- Claims in prose ("all suites green", "no API changes") will be re-derived
  by the review agent. Every claim that fails re-derivation costs you a
  fix loop; write only claims your transcript can back.

## The run ends at the report

Returning the structured output ends the run. Work that continues after
REPORT.md is written — one more edit, one more test, one more cleanup —
invalidates the report's claims (its cited runs no longer describe the
final tree) and is blocked on sight. If you find something after the
report, the honest move is to update the tree AND rewrite the report with a
fresh final run — never to let a stale report describe a moved tree.

## Blocked on sight, restated

- Any `git push`, or manual commit/PR plumbing the harness owns.
- Work continuing after REPORT.md without rewriting it.
- A report the harness cannot parse.
- `tests_passed` set from memory instead of the final run.

## Grounding

- This repo's Temporal workflow design: agent runs are activities; git and
  PR steps are recorded workflow actions for durability and replay.
- This repo's 3/10 tests_passed misreport finding: the field is machine-read
  and was measurably wrong when set without a fresh final run.
