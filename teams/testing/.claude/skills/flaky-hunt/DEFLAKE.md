# DEFLAKE — fix by cause, prove with reruns, quarantine with an owner

The fix must attack the named cause from TAXONOMY.md — never the
assertion that caught it. Widening a timeout, adding a retry, or
loosening a tolerance converts a visible flake into an invisible one
and spends the team's trust in green either way.

## The fix, by cause

- **Async wait:** wait on conditions, never clocks — web-first
  auto-retrying assertions, polling on observable state
  (`expect.poll`, `waitFor` on a condition), awaiting the actual
  promise. Delete the sleep; do not widen it. A sleep that "works now"
  is the same race with a longer fuse.
- **Concurrency:** synchronize on the real completion signal — join the
  thread, await the task set, subscribe to the done event — or make the
  schedule deterministic (single-flight executor, injected queue). Do
  not "fix" by serializing the whole suite; that hides the race the
  production code still has.
- **Test-order / shared state:** fresh fixtures per test — new DB
  rows/schema per test, reset globals and static caches in setup, not
  teardown (a crashed test skips its own teardown). Keep randomized
  order ON permanently to prove independence stays proven.
- **Time:** inject a fake or controlled clock (freezegun, fake timers,
  a Clock dependency) and pin the scenario times — including the
  boundary times (DST shift, midnight, month end) as explicit cases.
- **Randomness:** seed every generator and print the seed on failure so
  any run is reproducible; replace "any random data" with representative
  fixed data unless randomness IS the point (then it is a seeded
  property test).
- **Environment:** give the test what it actually needs — unique ports,
  isolated temp dirs, containerized dependencies — or shrink the test's
  size; Google's data says the bigger the test, the more it flakes.
  Move assertions that don't need the big harness down a level.

## Prove the fix

Rerun the **same conviction battery** that established the flake — at
least 10x, alone, in the full suite, and in randomized order (parallel
too, if concurrency was the class). Record zero failures in the report
alongside the diagnosis: cause, fix, battery, result. "Fixed" without
recorded reruns is a mood, not a state — the original conviction rate
tells you how many clean runs mean anything.

## Quarantine with an owner — the honest fallback

If the fix cannot land now, quarantine — visibly:

- Skip with three things attached: the **diagnosis** (named cause), an
  **owner**, and a **link** to the tracking issue. All three in the
  skip reason string, greppable.
- Quarantine removes the test from the merge-blocking signal while
  keeping it running where its failures are recorded — it is a
  holding cell, not a shredder.
- A silent skip or a deleted test is a deleted guardrail: whatever
  promise it asserted is now unwatched. Deleting is only legitimate
  when the promise itself is gone, stated as such.
- Quarantine has a clock: an unfixed quarantined test at its review
  date escalates to its owner; the bucket must never become the "old
  bugs" pile the regression-suite skill forbids.

## Grounding

- Google Testing Blog — "Flaky Tests at Google and How We Mitigate
  Them" (2016): quarantine-and-track over delete; "Test Flakiness — One
  of the Main Challenges of Automated Testing" (2020): fix by cause.
- Luo et al. (FSE 2014) — most async-wait flakes were fixed with
  condition-based waiting, not longer sleeps.
