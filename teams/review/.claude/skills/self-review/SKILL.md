---
name: self-review
description: Final audit of your own review before submitting — findings, labels, and claims held to the bar you held the diff to. Use immediately before writing REPORT.md in the review lane.
---

# self-review

Your product is not code — it is findings plus a verdict that triggers or
blocks a merge. This lane cannot edit source, so a sloppy review is your only
way to ship a defect. Audit the review the way you audited the diff.

1. **Re-read every blocking finding as the author will.** Each blocker must
   carry file:line, what is wrong, why it blocks (the consequence), and where
   possible what fixed looks like. A blocker the author cannot act on without
   asking you a question is not finished.
2. **Audit your severity labels.** For each `issue (blocking)`: would you
   stake the merge on it — a real correctness, security, or data problem, not
   a preference in costume? For each nitpick and suggestion: genuinely
   ignorable? Relabel now, not after pushback.
3. **Verify you ran what you claim.** For every "I ran X" in the draft
   report, find the actual command in your transcript. Not there: run it now
   or rewrite the claim as "not verified". Then confirm the run backing
   `tests_passed` is your LAST workspace action (verdict-discipline) — if
   anything came after it, run again.
4. **Check coverage of the whole diff.** Compare `git diff main...HEAD
   --stat` against the files your review discusses or consciously cleared. A
   file you never opened is an unreviewed file — open it or disclose it.
5. **Check the review's own scope.** Findings are about this diff, not a
   wishlist for the codebase. Pre-existing problems you noticed go in a
   clearly separated non-blocking note, never in the blocker list.
6. **Read the report as the workflow will.** Structured output parses;
   `tests_passed` matches the cited run; blockers first; the verdict sentence
   is unambiguous — approve or block, with the deciding reason named.

## Blocked on sight

- A blocker without file:line, or whose "why" amounts to "I don't like it".
- Any claimed run with no matching command in the transcript.
- `tests_passed` backed by a run that is not your final workspace action.
- Diff files neither reviewed nor disclosed as unreviewed.

## Grounding

- Google eng-practices, "The Standard of Code Review": comments grounded in
  technical facts; Nit-labeled polish never blocks a change.
- Conventional Comments: labeled severity is the reviewer's contract with
  the author — mislabeling breaks it.
- This repo's 3/10 tests_passed misreport finding: the claim audit in step 3
  is the countermeasure.
