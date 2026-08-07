# CLAIMS — how a pass/fail statement must be written

The workflow reads your verdict as data and decides a merge with it. Every
claim therefore carries its evidence inline, uses the boolean literally, and
names uncertainty in plain words instead of hedging.

## Cite command plus output tail

Beside the verdict, paste:

1. The exact command you ran (`pytest -q`, `npm test`, the real invocation
   with its real flags — not a paraphrase).
2. The final summary lines of its output: passed / failed / errored /
   skipped counts, and the exit status if the summary doesn't imply it.

A verdict without its evidence line is an impression, and impressions are
what this lane exists to keep out of the workflow. The evidence line also
lets any auditor re-run the same command and check transcript order against
LAST-RUN-RULE.md.

## `tests_passed` is literal-green-only

Set true **iff** the final run exited 0 with zero failures and zero errors.
Every other condition reports false, with the reason named in the report
text:

- "Should pass" — false. A prediction is not a run.
- "Passed earlier" — false. That run predates your last workspace action.
- "Failed for environmental reasons" — false, with the environmental cause
  stated. The boolean records what happened, not what would have happened
  in a kinder environment; the nuance belongs in prose.
- Collection errors, import errors, timeouts — false. A suite that could
  not run did not pass.

**Skips:** skipped tests are not failures — a green run with routine skips
is still true. But a suite that skipped most of itself is not green
evidence: report the skip count and say plainly that the run proves less
than it appears to. Never let a mass-skip masquerade as a full pass.

## Say "not verified" plainly

Any suite you did not or could not run is reported in exactly those words —
"not verified" — with the reason: missing dependency, no database, out of
time, sandbox limits. Never an inferred pass, never silence, never a guess
dressed as a result.

An honest "not verified" is a **correct verdict**. A guessed green is the
failure this lane exists to prevent, and a guessed red spins the fix loop
just as hard. The workflow can handle "not verified"; it cannot handle
fiction in a boolean.

## No hedged verdicts

The field is boolean. "Likely green", "should be fine", "mostly passing" are
not values it can take. Commit the boolean to what the last run showed, and
put every nuance — flaky test suspicions, environmental caveats, skip
inflation — in the report text where prose belongs. A hedge in the boolean
position is a claim the workflow will round in whichever direction hurts
most.

## Never launder someone else's claim

"Tests pass" taken from the author's REPORT.md, a PR description, or a CI
badge is their claim, not your verdict. You may quote it — attributed — but
`tests_passed` reflects only your own last run. If you could not run the
suite yourself, that is a "not verified", whatever the author reports.

## Grounding

- Google eng-practices review standard: decisions rest on technical facts
  and evidence, not opinion.
- This repo's measured experiment (articles/final/the-agent-grades-its-own-
  homework.md): the boolean was wrong 3/10 precisely when stated without
  fresh evidence beside it.
