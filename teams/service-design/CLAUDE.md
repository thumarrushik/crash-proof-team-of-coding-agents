# Service Design Team — Workspace Mandate

Team: `service-design`

This workspace is owned by a Temporal workflow. Work in bounded chunks, keep
side effects inside this workspace, and use the installed team skills when they
match the task.

## When the task arrives — the task list comes first

Before any other work, create this run's task list with TodoWrite: exactly
six tasks, one per phase, named Understand, Plan, Implement, Test,
Self-review, Report — in that order. Work them top to bottom, keep statuses
current, and mark each completed as you finish it. The `phase-gate` Stop hook
verifies the same list on every run: a run that skipped or renamed a phase
cannot finish. If anything is ambiguous, make the most reasonable assumption
and note it in REPORT.md — never stall waiting for a human.

## Every task follows these phases, in order — do not skip

1. **Understand.** Read the task and this file. Locate the relevant code with
   Glob/Grep before changing anything. Confirm the real requirement; don't
   pattern-match on the title.
2. **Plan.** Decide the smallest correct change that fully resolves the task.
   A new service, split, or major capability is designed as a
   [[service-blueprint]]; choices that are costly to reverse are recorded per
   [[adr]] — numbered, immutable, superseded rather than edited.
3. **Implement.** Match surrounding conventions. No placeholders: no TODO, no
   stubs, no commented-out "later".
4. **Test.** Design artifacts still get verified: apply the [[lean-service]]
   standard, run any checks or examples the design ships with, and show the
   output. If the task produced code, write the failing test first and run
   the suite until green.
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

Policy: this team's `.claude/` carries its full governance unit — `settings.json` (permissions plus the audit and rules hooks), `rules.json` (the lane's behavioral rules), the `flag-rules` hook script, and the `phase-gate` Stop hook (the run cannot finish until the mandated phase task list exists and every phase is completed) — all human-committed and stamped into the workspace before every chunk. The agent never edits them.

The harness owns git: never `git push` (it is denied). Leave changes in the
workspace; the harness commits, pushes, and opens PRs in its own recorded
steps. The worker exports the readable session transcript after the workflow
completes.
