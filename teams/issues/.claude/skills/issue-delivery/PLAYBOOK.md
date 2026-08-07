# PLAYBOOK — the seven steps, in order, every issue

Work every issue through these steps in sequence. Each step names the skill
that governs it in depth; this file is the spine that keeps them in order.

## 1. Understand

Read the issue in full, then locate the real code with Grep/Glob before
editing anything. Establish what "done" observably means — a test that
greens, an output that changes — before forming a theory of the fix. Do not
pattern-match the title: the issue text, not its headline, defines the work.

If the issue is ambiguous, contradicts the code it points at, or belongs to
another lane: flag that in the report as the deliverable rather than
guessing. A well-evidenced "this issue is ambiguous because X" is a
completed run.

## 2. Reproduce or locate

- **Bug-shaped:** run the repro-first skill — exact reproduction, minimized,
  frozen as a failing test — before any fix. No observed failure, no fix.
- **Feature-shaped:** find the insertion point and read the conventions
  around it — naming, error handling, test structure, layering. The
  surrounding code is the spec for how yours should look; a feature that
  imports its own style arrives pre-loaded with review findings.

## 3. Plan the smallest correct change

Apply the scope-control skill: a one-sentence scope statement ending in an
acceptance line, nothing presumptive, drive-by temptations noted for the
report instead of done. The plan should name the files you expect to touch —
a self-review anchor for step 6.

## 4. Implement test-first

Wherever there is behavior, apply the tdd skill: failing test, then minimal
code to green. Absolutely no placeholders — no TODO comments, no stub
functions, no commented-out "later" blocks. The diff ships production-ready
or it doesn't ship. Match surrounding conventions exactly, down to how
errors are raised and how tests are named.

## 5. Test — all layers, once, at the end

Run **every suite the repo ships**, not only the layer you touched. A change
in shared code or config must prove it did not break the neighbors; "my
layer is green" is not that proof.

Red: fix and re-run until green. Then record the final command and its
output tail — and make that run your **last workspace action**. Anything
executed after it stales the result (this repo measured `tests_passed`
wrong 3/10 from exactly such stale verdicts), and the review lane checks
transcript order for precisely this.

## 6. Self-review

Apply the self-review skill to the final diff:

- Only intended files changed — diff stat against the step-3 plan.
- Edges probed: empty, missing, duplicate, concurrent, dependency-down.
- No scratch files, debug prints, or secrets anywhere in the tree.
- Every stated requirement satisfied or explicitly flagged as not done.

## 7. Report, then stop

Write REPORT.md (final-report skill): what changed and why, the acceptance
line mapped to its shown check, exact test commands and results, the
"Noticed, not changed" list, residual risk. Set `tests_passed` to the
literal result of the step-5 final run — green means exit 0, zero failures,
zero errors; anything else is false with the reason named.

Return the structured output — that **ends the run**. No commits, no
pushes, no PRs, no "one more improvement" after the report: the harness
performs git in its own recorded steps (see HARNESS-CONTRACT.md).

## Grounding

- Google eng-practices, "Small CLs" and the review standard: your diff is
  judged as a CL — small, focused, carrying its own evidence.
- Stack Overflow MRE guidance (via repro-first): reproduce before fixing.
- Martin Fowler, "Yagni": smallest correct change, nothing presumptive.
- This repo's 3/10 tests_passed misreport finding: the last-run rule in
  step 5 exists because stale verdicts measurably lie.
