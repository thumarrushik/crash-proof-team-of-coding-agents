---
name: flaky-hunt
description: Diagnose-before-fix workflow for nondeterministic tests, grounded in Google's flaky-test research. Use whenever a test passes sometimes or fails only in CI.
---

# flaky-hunt

Google measured ~1.5% of all test runs flaky, ~16% of tests affected, and 84%
of pass->fail transitions caused by flakes rather than real breakage. Every
tolerated flake trains the team to ignore red.

## Phases — in order

1. **Convict with data.** Rerun the suspect at least 10x — alone, inside
   the full suite, and in randomized order. Record the failure rate and
   conditions before touching anything.
2. **Diagnose to a named cause.** No fix without a diagnosis. The taxonomy,
   roughly by prevalence:
   - **Async wait** — sleep-based sync, missing await (the single largest
     cause; ~45% of fixed flakes in Luo et al.'s empirical study).
   - **Concurrency** — races between threads, workers, promises.
   - **Test-order dependence / shared state** — DB rows, globals, files,
     static caches leaking between tests.
   - **Time** — Date.now, timezones, DST, midnight rollovers.
   - **Randomness** — unseeded generators, random data, map/set ordering.
   - **Environment** — resources; larger tests flake more (Google, 2017).
3. **Deflake by cause, never by assertion.**
   - Async: wait on conditions (web-first assertions, polling on state);
     never widen a sleep.
   - Time: inject a fake or controlled clock.
   - Randomness: seed it and print the seed on failure.
   - Order/shared state: fresh fixtures per test; keep random-order runs
     on to prove independence.
   - Concurrency: synchronize on the real completion signal or make the
     schedule deterministic.
4. **Prove the fix.** Rerun the same 10x-or-more battery; record zero
   failures in the report alongside the diagnosis.
5. **Quarantine with an owner.** If it cannot be fixed now: skip with the
   diagnosis, an owner, and a link — visible and tracked. A silent skip or
   a deleted test is a deleted guardrail.

## Blocked on sight

- Widening timeouts or tolerances to turn red green.
- Auto-retries presented as a fix.
- Weakening or removing the assertion that flaked.
- `sleep(n)` as synchronization; "fixed" without recorded reruns.

## Grounding

- Google Testing Blog: "Flaky Tests at Google and How We Mitigate Them"
  (2016); "Where do our flaky tests come from?" (2017); "Test Flakiness —
  One of the Main Challenges of Automated Testing" (2020).
- Luo, Hariri, Eloussi, Marinov: "An Empirical Analysis of Flaky Tests"
  (FSE 2014) — async wait, concurrency, and test order top the causes.
