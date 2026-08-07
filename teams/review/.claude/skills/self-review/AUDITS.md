# AUDITS — hold your review to the bar you held the diff to

Run these five audits in order over the draft review. Each one has caught
real defects in this workflow; none is optional because none overlaps the
others.

## 1. Re-read every blocking finding as the author will

The author receives your blocker with none of your context. Each one must
carry, on its own:

- **file:line** — where to look.
- **What is wrong** — the defect, concretely.
- **Why it blocks** — the consequence: what breaks, leaks, or decays.
- **Where possible, what fixed looks like** — enough direction that the fix
  loop converges in one pass instead of three.

A blocker the author cannot act on without asking you a question is not
finished — and in an async workflow, that question costs a full round trip.

## 2. Audit your severity labels

Walk the labels in both directions:

- For each `issue (blocking)`: would you stake the merge on it? It must be a
  real correctness, security, or data problem — not a preference in costume.
  Google's standard is explicit that comments rest on technical facts, and
  Nit-labeled polish never blocks a change.
- For each `nitpick` and `suggestion`: genuinely ignorable? If ignoring it
  would leave a defect, it is mislabeled in the dangerous direction.

Relabel now, not after pushback. Labeled severity is your contract with the
author (Conventional Comments) — mislabeling breaks it, and a reviewer who
inflates severity trains authors to discount every future blocker.

## 3. Verify you ran what you claim

For every "I ran X" in the draft report, find the actual command in your
transcript. If it is not there, you have exactly two honest moves: run it
now, or rewrite the claim as "not verified". There is no third option where
the claim stays because it is probably true.

Then confirm the run backing `tests_passed` is your **last** workspace
action (verdict-discipline's rule). If anything ran after it — anything —
run the suite again before the report. This audit is the direct
countermeasure to this repo's measured 3/10 tests_passed misreport rate.

## 4. Check coverage of the whole diff

Compare `git diff main...HEAD --stat` against the files your review
discusses or consciously cleared. Every file in the stat is in one of three
states: reviewed with findings, reviewed and clean, or **disclosed as
unreviewed** with the reason. A file you never opened is an unreviewed file
— silence about it converts your partial review into a claimed full one.

## 5. Check the review's own scope

Findings are about this diff. Pre-existing problems you noticed while
reading go in a clearly separated non-blocking note — useful signal, honestly
labeled — never in the blocker list. Blocking an author for code they did
not write is scope creep wearing a reviewer's badge, and it poisons the
merge signal for everyone reading the verdict.

## Grounding

- Google eng-practices, "The Standard of Code Review": comments grounded in
  technical facts; Nit-labeled polish never blocks a change.
- Conventional Comments: labeled severity is the reviewer's contract with
  the author — mislabeling breaks it.
- This repo's 3/10 tests_passed misreport finding: the claim audit in
  step 3 is the countermeasure.
