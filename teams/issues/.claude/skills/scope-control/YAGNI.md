# YAGNI — nothing presumptive, no drive-bys

Two temptations inflate every issue's diff: building for imagined futures,
and fixing the unrelated things you noticed on the way. Both feel like
diligence. Both are scope creep, and the review gate treats both as
findings.

## Build nothing presumptive

No parameter "for later". No extension point with one caller. No
generalization the issue does not require. No config key for a behavior
nobody asked to vary.

Fowler's argument is the one to internalize: **speculative code costs even
when it turns out right.** The costs stack:

- **Build cost** — the time spent now on capability nobody scheduled.
- **Carry cost** — the permanent tax: every future change in this file now
  reads, reviews, and tests around the speculative part. Carry cost is paid
  by everyone, forever, whether or not the future arrives.
- **Delay cost** — the actual issue ships later than it had to.

And when the imagined future does arrive, it rarely matches the guess —
so the presumptive design gets rebuilt anyway, now with migration on top.
The cheap time to build a capability is when its real requirements exist.

The test for any hunk: does a sentence in the issue require it? "We might
need it" is the exact justification the blocked-on-sight list names.

## No drive-by refactors — note them instead

While fixing, you will notice things: a misleading name, a duplicated
helper, an outdated dependency, formatting the linter would change. The
discipline is one move: **note, don't touch.**

Renames, cleanups, dependency upgrades, and formatting churn you were
tempted by go in REPORT.md under **"Noticed, not changed"**. That single
habit does three jobs:

- Converts scope creep into triage input — the team can now schedule the
  cleanup as its own issue with its own review.
- Keeps every diff line explainable — the reviewer never has to separate
  your fix from your housekeeping, and mixed churn is blocked on sight.
- Loses nothing — the observation is captured, just not smuggled.

Formatting churn is the sneakiest offender: it buries the three lines that
matter under three hundred that don't, and defect discovery in review
collapses with diff size.

## The sole exception: damage your own change causes

Fix what your change itself makes wrong, in the same diff:

- A comment your change just made into a lie.
- A branch your change just made dead.
- A docstring describing the behavior you just corrected.

This is not a drive-by — leaving it would ship a diff that actively
misleads. The boundary is causal: your change created the wrongness, so
your change cleans it up. Wrongness that predates your diff goes under
"Noticed, not changed", however small the fix would be.

## Grounding

- Martin Fowler, "Yagni" (martinfowler.com/bliki/Yagni.html): presumptive
  features cost build, carry, and delay — even when built right.
- Google eng-practices, "Small CLs": keep refactors and formatting in their
  own changes; small focused diffs review faster and breed fewer bugs.
