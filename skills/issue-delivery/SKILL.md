---
name: issue-delivery
description: How the general/issues team — the fallback lane for uncategorized or unlabeled work — delivers an issue end to end in the multi-team pipeline (service-design → backend → frontend → testing → review → issues) — understand the issue and its dependencies, plan the smallest correct change, implement test-first where there's behavior, run the relevant checks (including backend/frontend suites when the change touches their behavior — don't break neighbors), self-review, and hand off with a REPORT.md. Use for any team-issues or unlabeled issue.
---

# issue-delivery

The issues team is the catch-all lane: work that doesn't map cleanly to service-design, backend,
frontend, or testing lands here — maintenance, docs, config, small fixes, tooling, cross-cutting
changes. "Uncategorized" does not mean "lower standard": the same bar applies as in any lane, and
because this work often cuts across team boundaries, the burden of not breaking neighbors is
*higher* here, not lower.

## The steps

Work every issue in this order. Don't reorder, don't skip.

1. **Understand the issue and its dependencies.** Read the issue in full, then read the code and
   docs it touches. Establish what "done" means for this issue and which teams' territory the
   change crosses. If the issue is ambiguous or actually belongs to a specific team, flag it —
   don't guess scope and don't quietly do another team's job.
2. **Plan the smallest correct change.** The catch-all lane attracts scope creep; resist it.
   Identify the minimal set of files that must change and the minimal change to each. No drive-by
   refactors, no "while I'm here" cleanups — a maintenance issue fixes what it names.
3. **Implement test-first where there's behavior.** If the change alters behavior, write the
   failing test first, watch it fail for the right reason, then make it pass. If the change has no
   testable behavior (docs, comments, config text), say so in REPORT.md rather than inventing a
   hollow test.
4. **Run the relevant checks — and your neighbors'.** Run whatever the change directly touches
   (linters, builds, the local suite). Then the cross-cutting rule: **if the change touches
   backend or frontend behavior — even indirectly, via config, shared code, or tooling — run those
   teams' test suites too.** A green local check with an unexercised neighbor is an unverified
   change. If you can't run a neighboring suite, flag the gap explicitly in REPORT.md instead of
   skipping silently.
5. **Self-review.** Run the full [self-review](../self-review/SKILL.md) pass: re-read the diff as
   a skeptical stranger, confirm only intended files changed (no scratch files, debug prints, or
   secrets), re-run the tests and read the results, probe the edge paths, check the issue's
   definition of done.
6. **Write REPORT.md and hand off.** What changed and why, test evidence (including neighboring
   suites you ran or couldn't), residual risk. The harness opens the PR — your job ends at a clean
   branch plus the report.

## Definition of done

- [ ] Issue fully understood; dependencies and crossed team boundaries identified up front.
- [ ] Change is the smallest correct one — only the files the issue requires, no drive-bys.
- [ ] Behavioral changes were test-first; non-testable changes are declared as such in REPORT.md.
- [ ] Relevant checks green — plus backend/frontend suites when their behavior was touched, or the
      gap explicitly flagged.
- [ ] Self-review pass completed on the final branch state.
- [ ] REPORT.md written: what/why, test evidence, residual risk. Branch clean for the harness to
      open the PR.
