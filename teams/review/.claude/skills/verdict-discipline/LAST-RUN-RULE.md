# LAST-RUN-RULE — the verdict is the last run, nothing earlier

A verdict is not a memory, an impression, or a first diagnosis that hardened.
It is the result of one specific run: the suite run performed after every
other command you executed in the workspace. Everything else is stale.

## The rule, mechanically

1. Finish all workspace actions — every edit, every install, every config
   touch, every "one last tweak".
2. Then run the suite.
3. Then report, from that run and no other.

If anything ran after your test run — even a command you believe could not
affect tests — the result is stale. Run again before reporting. The cost of
an extra run is seconds; the cost of a stale verdict is a wrong merge
decision or a wasted fix loop.

**Transcript order is the proof.** Anyone auditing the transcript must find
the cited run as the last workspace action before the verdict. If it isn't,
the verdict is invalid regardless of whether it happens to be correct.

## The false-red trap — what actually went wrong here

This repo's measured experiment found `tests_passed` wrong 3 runs in 10
against ground truth — and the dominant failure was not optimism. It was
**false-red**: 3 of 5 wrong verdicts were agents reporting *false* on their
own genuinely green code.

The mechanism: the agent met a red suite at first contact, formed the
verdict "failing", then fixed the code — and the verdict never updated,
because the agent trusted its earlier diagnosis over a fresh run. Stale
pessimism then spins the fix loop on good work exactly as surely as false
optimism merges bad work.

So distrust your certainty in **both** directions:

- Feeling sure it passes is not a run.
- Feeling sure it still fails is not a run either.

## Why a mechanical rule and not "be careful"

Automation bias research (Parasuraman & Manzey 2010) shows this class of
error — trusting a formed judgment over fresh evidence — produces both
omission and commission errors, affects experts as much as novices, and is
not trained away by awareness or motivation. Vigilance does not fix it;
procedure does. Hence one mechanical rule that requires no judgment to
apply:

**No run, no claim. Last run, only claim.**

## What counts as "the last run"

- Your own run, in this workspace, of the suite you are reporting on. The
  author's REPORT.md, CI badges from before your changes, or a teammate's
  transcript are testimony, not evidence.
- The whole suite you are making a claim about — a green single test file
  supports a claim about that file, not about "tests".
- A run whose output you actually captured; see CLAIMS.md for how it must
  be cited.

## Grounding

- This repo's measured experiment (articles/final/the-agent-grades-its-own-
  homework.md): tests_passed wrong 3/10 vs ground truth; 3/5 false-reds on
  genuinely green fixes, from stale first-contact verdicts.
- Parasuraman & Manzey 2010, Human Factors: automation bias yields omission
  and commission errors, affects experts, and is not trained away — hence a
  mechanical run-then-report rule instead of vigilance.
