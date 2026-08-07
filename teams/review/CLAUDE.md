# Review Team — Workspace Mandate

Team: `review`

This workspace is owned by a Temporal workflow. You are reviewing a pull
request whose branch is already checked out here. Your verdict decides a
merge, so accuracy matters more than a green answer.

## When the review arrives — the task list comes first

Before any other work, create this run's task list with TodoWrite: exactly
five tasks, one per phase, named Understand, Inspect, Run, Self-review,
Report — in that order. Work them top to bottom, keep statuses current, and
mark each completed as you finish it. The `phase-gate` Stop hook verifies the
same list on every run: a run that skipped or renamed a phase cannot finish.
If anything is ambiguous, make the most reasonable assumption and note it in
REPORT.md — never stall waiting for a human.

## Every review follows these phases, in order — do not skip

1. **Understand.** Read the PR's diff (`git diff main...HEAD`) and the code
   around it. Read this file. Confirm what the change claims to do.
2. **Inspect.** Apply the [[pr-review]] skill: the review bar, what to inspect,
   how to label findings — including whether the change carries the tests it
   needs. Then apply [[diff-forensics]]: callers of every changed symbol, the
   behavior deltas the description never claimed, the hunk that should exist
   but doesn't.
3. **Run.** Run the project's test suites yourself — all layers that exist,
   not only the one the diff touches. Show the output. You review code; you
   do not fix it: do not Write or Edit source files (the workspace flags it).
4. **Self-review.** Run the [[self-review]] checklist against your own findings:
   is every blocking claim concrete, with a file and line? Would you stake a
   merge on it?
5. **Report.** Write REPORT.md ([[final-report]]) and return the structured
   output. Set `tests_passed` per [[verdict-discipline]]: the latest actual
   run, cited with its command and output tail — never your impression from
   earlier in the review. Only set false for a real blocking problem, and
   name it first.

## Workspace efficiency rules (learned from a review of prior runs)

- Trust tool responses. Do NOT run `ls` to confirm files you already listed.
- Run the suites once, after reading the diff; do not re-run green tests
  before finishing.

## Harness contract

Policy: this team's `.claude/` carries its full governance unit — `settings.json` (permissions plus the audit and rules hooks), `rules.json` (the lane's behavioral rules), the `flag-rules` hook script, and the `phase-gate` Stop hook (the run cannot finish until the mandated phase task list exists and every phase is completed) — all human-committed and stamped into the workspace before every chunk. The agent never edits them.

The harness owns git: never `git push` (it is denied). Your verdict is data
the workflow reads; the harness posts the review and performs any merge in
its own recorded steps. The worker exports the readable session transcript
after the workflow completes.
