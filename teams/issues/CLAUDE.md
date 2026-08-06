# Issues Team — Workspace Mandate

Team: `issues`

This workspace is owned by a Temporal workflow. Work in bounded chunks, keep
side effects inside this workspace, and use the installed team skills when they
match the task.

## Every task follows these phases, in order — do not skip

1. **Understand.** Read the task and this file. Locate the relevant code with
   Glob/Grep before changing anything. Confirm the real requirement; don't
   pattern-match on the title.
2. **Plan.** Decide the smallest correct change that fully resolves the task.
   Prefer reusing existing functions over adding new ones.
3. **Implement.** Match surrounding conventions. No placeholders: no TODO, no
   stubs, no commented-out "later".
4. **Test.** Follow the [[tdd]] loop: add or update tests for the behavior you
   changed, then run the suite and show the output. Run every suite the repo
   ships when layers exist — a change in one layer has to prove it did not
   break the others. If a check fails, fix it and re-run until green.
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

Policy: this team's `.claude/` carries its full governance unit — `settings.json` (permissions plus the audit and rules hooks), `rules.json` (the lane's behavioral rules), and the `flag-rules` hook script — all human-committed and stamped into the workspace before every chunk. The agent never edits them.

The harness owns git: never `git push` (it is denied). Leave changes in the
workspace; the harness commits, pushes, and opens PRs in its own recorded
steps. The worker exports the readable session transcript after the workflow
completes.
