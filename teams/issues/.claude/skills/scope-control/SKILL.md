---
name: scope-control
description: Deliver the smallest correct change that fully resolves the issue and nothing else. Use when planning an issue's change and again when self-reviewing the diff.
---

# scope-control

Small diffs are not a style preference: they are reviewed faster, more
thoroughly, and carry fewer bugs — and this lane's diffs face a review gate
that treats out-of-scope changes as findings. The issue defines the blast
radius; stay inside it.

1. **Restate the issue in one sentence before editing**, ending with its
   acceptance line: "done when <observable check> passes". That sentence is
   your scope contract. If you cannot write it, the issue is ambiguous —
   flag that in the report instead of guessing.
2. **Choose the smallest correct change — correct first, small second.**
   Smallest means fewest files, existing functions edited over parallel ones
   added, existing abstractions reused over new ones invented. It never means
   half a fix: handling the reported case while leaving its obvious sibling
   broken is small and wrong.
3. **Build nothing presumptive (YAGNI).** No parameter "for later", no
   extension point with one caller, no generalization the issue does not
   require. Speculative code costs even when it turns out right: it is carry
   cost — every future change in this file now reads, reviews, and tests
   around it.
4. **No drive-by refactors — note them instead.** Renames, cleanups,
   dependency upgrades, and formatting churn you were tempted by go in
   REPORT.md under "Noticed, not changed". That converts scope creep into
   triage input and keeps every diff line explainable. Sole exception: fix
   what your change itself makes wrong — a now-lying comment, a now-dead
   branch.
5. **Close the loop: acceptance line to shown check.** The sentence from
   step 1 must map to a test or command output that appears in your report.
   An acceptance line with no check beside it means the issue is not
   resolved — merely edited.

## Blocked on sight

- Diff hunks no sentence in the issue requires.
- A new abstraction, parameter, or config key with exactly one user and a
  "we might need it" justification.
- Formatting or rename churn mixed into a functional fix.
- A report whose acceptance line points at no shown check.

## Grounding

- Martin Fowler, "Yagni" (martinfowler.com/bliki/Yagni.html): presumptive
  features cost build, carry, and delay — even when built right.
- Google eng-practices, "Small CLs": small changes review faster, more
  thoroughly, and breed fewer bugs.
- SmartBear/Cisco: defect discovery collapses beyond ~400 changed lines —
  scope creep literally makes your bugs harder to catch.
