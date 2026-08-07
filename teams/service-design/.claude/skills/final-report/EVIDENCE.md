# EVIDENCE.md — what verification is allowed to claim

This repo measured what happens when the claim and the run drift: the
self-report boolean was wrong 3 in 10 against ground truth — every miss a
stale verdict, not a lie (articles/final/the-agent-grades-its-own-homework.md).
These rules are the countermeasure.

## The last-run rule

The result you report must come from a run performed AFTER your final
edit. If anything changed after your last run — even a comment — run
again before reporting. Transcript order is the proof; the review lane
checks exactly this.

## Cite command + tail

Beside every verification claim, paste the exact command and the final
summary lines (counts of passed/failed/errored/skipped). For this lane:
the checks or examples the design ships with. A claim without its command is an impression, and the reviewer
treats it as unverified.

## tests_passed is literal-green-only

True iff the final run exited 0 with zero failures and zero errors.
"Should pass", "passed earlier", "failed for environmental reasons" — all
false, with the reason named in the report. Skips are not failures, but a
suite that skipped most of itself is not green evidence; say so.

## "Not verified" is a correct answer

Any check you could not run is reported in those words, with the reason.
An honest not-verified is triage input; a guessed green is the one
failure this pipeline is built to prevent — and a guessed red spins the
fix loop on good work just as surely.

## The structured output

The harness requires the schema'd report (summary, files_created,
tests_passed). The summary opens with the outcome; files_created matches
the Files section; tests_passed obeys the rules above. Returning it ends
the run — the phase gate treats the returned report as the Report
phase's completion.
