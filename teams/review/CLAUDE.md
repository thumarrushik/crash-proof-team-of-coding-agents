# Review Team — Workspace Mandate

Team: `review`

This workspace is owned by a Temporal workflow. You are reviewing a pull
request whose branch is already checked out here. Your verdict decides a
merge, so accuracy matters more than a green answer.

## Every review follows these phases, in order — do not skip

1. **Understand.** Read the PR's diff (`git diff main...HEAD`) and the code
   around it. Read this file. Confirm what the change claims to do.
2. **Inspect.** Apply the pr-review skill: correctness, security, operational
   risk. Apply the testing-bar skill: does the change carry the tests it
   needs?
3. **Run.** Run the project's test suites yourself — all layers that exist,
   not only the one the diff touches. Show the output. You review code; you
   do not fix it: do not Write or Edit source files (the workspace flags it).
4. **Self-review.** Run the self-review checklist against your own findings:
   is every blocking claim concrete, with a file and line? Would you stake a
   merge on it?
5. **Report.** Write REPORT.md (final-report skill) and return the structured
   output. Set `tests_passed` to the result of the suite run you performed in
   phase 3 — the latest actual run, not your impression from earlier in the
   review. Only set false for a real blocking problem, and name it first.

## Workspace efficiency rules (learned from a review of prior runs)

- Trust tool responses. Do NOT run `ls` to confirm files you already listed.
- Run the suites once, after reading the diff; do not re-run green tests
  before finishing.

## Harness contract

Policy: this team's `.claude/settings.json` (deny rules plus the audit and
rules hooks) is human-committed and stamped into the workspace before every
chunk. The agent never edits it.

The harness owns git: never `git push` (it is denied). Your verdict is data
the workflow reads; the harness posts the review and performs any merge in
its own recorded steps. The worker exports the readable session transcript
after the workflow completes.
