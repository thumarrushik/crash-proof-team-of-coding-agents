---
name: verdict-discipline
description: Evidence-first rules for setting tests_passed and stating any pass/fail claim. Use whenever producing the review verdict or report.
---

# verdict-discipline

`tests_passed` is data the workflow reads to decide a merge. This repo
measured that boolean against ground truth and it was wrong 3 runs in 10 —
including agents reporting *false* on their own genuinely green code, because
the verdict formed at first contact with a red suite and never updated after
the last edit. A verdict is not a memory. It is the last run.

1. **Run after the last workspace action.** The result you report must come
   from a suite run performed AFTER every other command you executed. If
   anything ran after your test run, that result is stale — run again before
   reporting. Transcript order is the proof.
2. **Cite command plus output tail.** Beside the verdict, paste the exact
   command and the final summary lines (passed / failed / errored / skipped
   counts). A verdict without its evidence line is an impression.
3. **`tests_passed` is literal-green-only.** True iff that final run exited 0
   with zero failures and zero errors. "Should pass", "passed earlier",
   "failed for environmental reasons" — all report as false, with the reason
   named. Skips are not failures, but a suite that skipped most of itself is
   not green evidence — say so in the report.
4. **Say "not verified" plainly.** Any suite you did not or could not run is
   reported in exactly those words, with the reason — never an inferred pass,
   never silence. An honest "not verified" is a correct verdict; a guessed
   green is the failure this lane exists to prevent.
5. **Distrust your certainty in both directions.** The measured failure here
   was false-red: stale pessimism spins the fix loop on good work as surely
   as false optimism merges bad work. The cure for both is one mechanical
   rule — no run, no claim; last run, only claim.

## Blocked on sight

- `tests_passed` set either way with no command + output tail beside it.
- A verdict citing a run that predates your last workspace action.
- "Tests pass" taken from the author's REPORT.md instead of your own run.
- A hedged verdict ("likely green") — the field is boolean; nuance lives in
  the report text.

## Grounding

- This repo's measured experiment (articles/final/the-agent-grades-its-own-
  homework.md): tests_passed wrong 3/10 vs ground truth; 3/5 false-reds on
  genuinely green fixes, from stale first-contact verdicts.
- Parasuraman & Manzey 2010, Human Factors: automation bias yields omission
  and commission errors, affects experts, and is not trained away — hence a
  mechanical run-then-report rule instead of vigilance.
- Google eng-practices review standard: decisions rest on technical facts
  and evidence, not opinion.
