# VERDICT.md — the boolean that decides the merge

`tests_passed` is not a summary of your impression. It is data the workflow
reads to merge or block, and this repo measured it wrong 3 runs in 10 —
every miss a stale verdict formed before the last edit
(articles/final/the-agent-grades-its-own-homework.md). These rules are the
countermeasure; [[verdict-discipline]] is the full treatment.

## The last-run rule

The result behind `tests_passed` comes from a suite run performed AFTER
every other action in your workspace. If anything ran after your test run,
that result is stale — run again before reporting. Transcript order is the
proof, and it is exactly what the next reviewer (or the harness) checks.

## Literal-green-only

`tests_passed` is true iff that final run exited 0 with zero failures and
zero errors. "Should pass", "passes except for", "failed for environmental
reasons" all report **false**, with the reason named in the Verdict. Skips
are not failures, but a suite that skipped most of itself is not green
evidence — say so.

## The two directions, equally

- A **false green** merges a red suite — the catastrophic direction.
- A **false red** bounces good work and spins the fix loop for nothing —
  the expensive direction, and the one this repo actually measured.

Distrust your certainty both ways. The cure for both is one mechanical rule:
no run, no claim; last run, only claim.

## Not verified is a correct answer

A suite you could not run is reported in those words, with the reason —
never an inferred pass, never silence. An honest "not verified" is a valid
verdict; a guessed green is the failure this lane exists to prevent.

## The structured output

The harness requires the schema'd report; `summary` opens with the verdict
sentence, `tests_passed` obeys the rules above. Returning it ends the run —
the phase gate treats the returned report as the Report phase's completion.
