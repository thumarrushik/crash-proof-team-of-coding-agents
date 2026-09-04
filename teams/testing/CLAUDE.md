# Testing Team — Workspace Mandate

Team: `testing`

This workspace is owned by a Temporal workflow. Work in bounded chunks, keep
side effects inside this workspace, and use the installed team skills when they
match the task.

## When the task arrives — the task list comes first

Before any other work, create this run's task list: exactly
six tasks, one per phase, named Understand, Plan, Author, Run,
Self-review, Report — in that order. Work them top to bottom, keep statuses
current, and mark each completed as you finish it. The `phase-gate` Stop hook
verifies the same list on every run: a run that skipped or renamed a phase
cannot finish. If anything is ambiguous, make the most reasonable assumption
and note it in REPORT.md — never stall waiting for a human.

## Every task follows these phases, in order — do not skip

1. **Understand.** Read the task and this file. Locate the relevant code with
   Glob/Grep before changing anything. Confirm the real requirement; don't
   pattern-match on the title.
2. **Plan.** Enumerate the promises to cover per [[testing-bar]] — behaviors,
   failure branches, the edge-case taxonomy — and pick the boundary each test
   speaks at. Bug-shaped work plans a failing reproduction first per
   [[regression-suite]].
3. **Author.** Your deliverable IS the tests — this is the testing lane's own
   step. Write them black-box and test-first per [[tdd]]: every new test seen
   red once; names state behavior; no change-detectors. A sometimes-failing
   test goes through [[flaky-hunt]], never a retry.
4. **Run.** Run everything you wrote, show the output, and run the full
   cross-layer suites when they exist. If a check fails, fix it and re-run
   until green.
5. **Self-review.** Run the [[self-review]] checklist on your own diff:
   correctness, edge cases, security, leftovers, conventions. Fix anything
   you'd flag.
6. **Report.** Write REPORT.md ([[final-report]]) and return the structured
   output the harness requires. Set `tests_passed` to the actual result of the
   last suite run you performed — run it after your final edit, not before.

## Workspace efficiency rules (learned from a review of prior runs)

- Trust tool responses. A successful Write/Edit already proves the file exists
  at the returned path — do NOT run `ls` to confirm a file you just created.
- Run the test suite once after implementing; if it passes, go straight to the
  report. Do not re-run green tests or re-list the directory before finishing.

## Harness contract

Policy: this team's `.claude/` carries its full governance unit — `settings.json` (permissions plus the audit and rules hooks), `rules.json` (the lane's behavioral rules), the `flag-rules` hook script, the `mirror-signal` hook (every `git commit` leaves a marker the harness reads to mirror the work branch to the remote), and the `phase-gate` Stop hook (the run cannot finish until the mandated phase task list exists and every phase is completed) — all human-committed and stamped into the workspace before every chunk. The agent never edits them.

The harness owns the remote: never `git push` (it is denied). Commit as you
work — end every phase with a commit, plus small commits at meaningful
checkpoints (a suite green, a decision made), each with a message that says
why. Every commit is mirrored as it lands: a hook leaves a marker and the
harness pushes the work branch to the remote in its own step, with its own
credential, so finished work is never only on this machine. Leave anything
uncommitted at the end; the harness sweeps leftovers into a final commit and
opens the PR in its own recorded steps. The worker exports
the readable session transcript after the workflow completes.
