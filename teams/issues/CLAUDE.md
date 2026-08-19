# Issues Team — Workspace Mandate

Team: `issues`

This workspace is owned by a Temporal workflow. Work in bounded chunks, keep
side effects inside this workspace, and use the installed team skills when they
match the task.

## When the task arrives — the task list comes first

Before any other work, create this run's task list: exactly
seven tasks, one per phase, named Understand, Reproduce, Plan, Implement,
Test, Self-review, Report — in that order. Work them top to bottom, keep statuses
current, and mark each completed as you finish it. The `phase-gate` Stop hook
verifies the same list on every run: a run that skipped or renamed a phase
cannot finish. If anything is ambiguous, make the most reasonable assumption
and note it in REPORT.md — never stall waiting for a human.

## Every task follows these phases, in order — do not skip

1. **Understand.** Read the task and this file. Locate the relevant code with
   Glob/Grep before changing anything. Confirm the real requirement; don't
   pattern-match on the title. The [[issue-delivery]] skill is this lane's
   end-to-end playbook — follow it.
2. **Reproduce.** This lane's own step — the issue is either bug-shaped or
   feature-shaped, and each needs different work. Bug-shaped: [[repro-first]]
   — reproduce exactly, minimize, freeze as a failing test, before any fix.
   Feature-shaped: locate the insertion point and the conventions around it;
   the surrounding code is the spec for how yours should look.
3. **Plan.** Decide the smallest correct change that fully resolves the task
   per [[scope-control]]: one-sentence scope with an acceptance line, nothing
   presumptive, drive-by temptations noted instead of done. Prefer reusing
   existing functions over adding new ones.
4. **Implement.** Match surrounding conventions. No placeholders: no TODO, no
   stubs, no commented-out "later".
5. **Test.** Follow the [[tdd]] loop: add or update tests for the behavior you
   changed, then run the suite and show the output. Run every suite the repo
   ships when layers exist — a change in one layer has to prove it did not
   break the others. If a check fails, fix it and re-run until green.
6. **Self-review.** Run the [[self-review]] checklist on your own diff:
   correctness, edge cases, security, leftovers, conventions. Fix anything
   you'd flag.
7. **Report.** Write REPORT.md ([[final-report]]) and return the structured
   output the harness requires. Set `tests_passed` to the actual result of the
   last suite run you performed — run it after your final edit, not before.

## Workspace efficiency rules (learned from a review of prior runs)

- Trust tool responses. A successful Write/Edit already proves the file exists
  at the returned path — do NOT run `ls` to confirm a file you just created.
- Run the test suite once after implementing; if it passes, go straight to the
  report. Do not re-run green tests or re-list the directory before finishing.

## Harness contract

Policy: this team's `.claude/` carries its full governance unit — `settings.json` (permissions plus the audit and rules hooks), `rules.json` (the lane's behavioral rules), the `flag-rules` hook script, and the `phase-gate` Stop hook (the run cannot finish until the mandated phase task list exists and every phase is completed) — all human-committed and stamped into the workspace before every chunk. The agent never edits them.

The harness owns the remote: never `git push` (it is denied). Commit as you
work — small commits at meaningful checkpoints (a phase completed, a suite
green), each with a message that says why — and leave anything uncommitted at
the end; the harness sweeps leftovers into a final commit, pushes your full
commit history, and opens the PR in its own recorded steps. The worker exports
the readable session transcript after the workflow completes.
