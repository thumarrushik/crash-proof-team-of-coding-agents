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

## How to use this skill

1. Read this file before producing any review verdict or report.
2. Open the topic file for the step you are on (below) — the run that
   produces the evidence, then the claim that reports it.

## Topic map (load on demand)

| Task | File |
|---|---|
| When a run counts: freshness, staleness, the false-red trap | **[LAST-RUN-RULE.md](LAST-RUN-RULE.md)** |
| How to state it: evidence lines, the boolean, "not verified" | **[CLAIMS.md](CLAIMS.md)** |

## The rules in one breath

1. Run after the last workspace action — if anything ran after your test
   run, that result is stale; run again before reporting.
2. Cite command plus output tail beside every verdict; a verdict without its
   evidence line is an impression.
3. `tests_passed` is literal-green-only: true iff the final run exited 0 with
   zero failures and zero errors. Everything else is false, reason named.
4. Say "not verified" plainly for any suite you did not or could not run —
   never an inferred pass, never silence.
5. Distrust your certainty in both directions: the measured failure here was
   false-red. No run, no claim; last run, only claim.

**Blocked on sight:** `tests_passed` set either way with no command + output
tail beside it · a verdict citing a run that predates your last workspace
action · "tests pass" taken from the author's REPORT.md instead of your own
run · a hedged verdict ("likely green") — the field is boolean; nuance lives
in the report text.
