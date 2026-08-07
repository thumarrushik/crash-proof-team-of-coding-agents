---
name: issue-delivery
description: The issues lane's end-to-end playbook from reading the issue to the structured report that ends the run. Use when working any issue in this workspace.
---

# issue-delivery

This workspace is owned by a Temporal workflow: the harness stamps governance,
owns git (never `git push` — it is denied), and reads your structured report
as data. Your run ends at a clean working tree plus REPORT.md; the harness
commits, opens the PR, and a review agent whose verdict gates the merge will
re-derive every claim you make. Deliver accordingly.

1. **Understand.** Read the issue in full, then locate the real code with
   Grep/Glob before editing anything. Establish what "done" observably means;
   do not pattern-match the title. Ambiguous or wrong-lane issue: flag it in
   the report rather than guessing.
2. **Reproduce or locate.** Bug-shaped: run the repro-first skill — exact
   reproduction, minimized, frozen as a failing test — before any fix.
   Feature-shaped: find the insertion point and the conventions around it;
   the surrounding code is the spec for how yours should look.
3. **Plan the smallest correct change** (scope-control skill): one-sentence
   scope with an acceptance line, nothing presumptive, drive-by temptations
   noted instead of done.
4. **Implement test-first** (tdd skill) wherever there is behavior: failing
   test, minimal code to green. No placeholders — no TODO, no stubs, no
   commented-out "later". Match surrounding conventions exactly.
5. **Test — all layers, once, at the end.** Run every suite the repo ships,
   not only the layer you touched: a change in shared code or config must
   prove it did not break the neighbors. Red: fix and re-run until green.
   Record the final command and its output tail; that run must be your last
   workspace action — the review lane checks exactly this.
6. **Self-review** (self-review skill) on the final diff: only intended
   files changed; edges probed; no scratch files, debug prints, or secrets;
   every stated requirement satisfied or explicitly flagged.
7. **Report, then stop.** Write REPORT.md (final-report skill): what changed
   and why, the acceptance line mapped to its shown check, exact test
   commands and results, the "Noticed, not changed" list, residual risk. Set
   `tests_passed` to the literal result of the step-5 final run. Return the
   structured output — that ends the run. No commits, no pushes, no PRs: the
   harness performs those in its own recorded steps.

## Blocked on sight

- Any `git push`, or manual commit/PR plumbing the harness owns.
- Editing before the issue's code was located and read.
- Declaring done with an unrun suite, or `tests_passed` set from memory.
- Work continuing after REPORT.md, or a report the harness cannot parse.

## Grounding

- Google eng-practices, "Small CLs" and the review standard: your diff is
  judged as a CL — small, focused, carrying its own evidence.
- Stack Overflow MRE guidance (via repro-first): reproduce before fixing.
- Martin Fowler, "Yagni": smallest correct change, nothing presumptive.
- This repo's 3/10 tests_passed misreport finding: the last-run rule in
  step 5 exists because stale verdicts measurably lie.
