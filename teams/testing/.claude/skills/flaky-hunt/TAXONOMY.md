# TAXONOMY — name the cause before touching the test

No fix without a diagnosis. The six classes below, roughly by
prevalence (Luo et al., FSE 2014; Google's flaky-test posts), cover
nearly every flake. Match the symptoms from your conviction runs (rate,
conditions, failure mode) to a class — the class dictates the fix in
DEFLAKE.md.

## 1. Async wait — the single largest cause

~45% of fixed flakes in Luo et al.'s empirical study. Sleep-based
synchronization, missing `await`, asserting before the app/promise
settles. **Telltales:** fails more on slow CI than locally; failure is
"element not found" / "expected X got undefined" / empty result; a
longer sleep "helps"; stack shows the assertion racing the work.

## 2. Concurrency

Races between threads, workers, promises; unsynchronized access to
shared memory. **Telltales:** fails only with parallel workers; failure
mode varies run to run (different wrong values, occasional deadlock);
disappears under a debugger or with `--workers=1`.

## 3. Test-order dependence / shared state

DB rows, globals, files, static caches, environment variables leaking
between tests. **Telltales:** passes alone, fails in the suite (or the
reverse — passes only after a sibling seeded state); randomized order
changes which test fails; failure names data the test never created.

## 4. Time

`Date.now`/`time.time` in assertions, timezone and DST assumptions,
expiry math, midnight/month/year rollovers. **Telltales:** fails at
specific wall-clock times (the 23:59 build), in specific CI regions, or
on the first run of the month; diffs show timestamps one unit apart.

## 5. Randomness

Unseeded generators, random test data, iteration order of hash
maps/sets, UUID collisions in truncated form. **Telltales:** low,
steady failure rate with no environmental pattern; failing values
differ every time; rerunning the same seed (when you have one)
reproduces it exactly.

## 6. Environment / resources

Ports in use, disk/memory pressure, external services, container
cold-starts. Larger tests flake more — Google's 2017 analysis ties
flake probability to binary size and RAM/dependency count.
**Telltales:** fails only in CI or only on one runner class; failure is
a timeout/connection refused/OOM rather than a wrong value; rate
correlates with suite size or parallelism, not with the code under
test.

## Diagnosis discipline

- Use the conviction-run matrix as evidence: alone-vs-suite
  discriminates class 3; randomized order confirms it; parallel-vs-serial
  discriminates class 2; local-vs-CI points at 1 or 6.
- One flake can stack classes (async wait exposed by slow CI). Name the
  proximate cause you can make deterministic — then re-run; the second
  class shows up in the residue if it exists.
- Write the named cause into the report/commit before fixing. "Flaky,
  rerun" is not a diagnosis; it is the habit that produced the 84%.

## Grounding

- Luo, Hariri, Eloussi, Marinov — "An Empirical Analysis of Flaky
  Tests" (FSE 2014): async wait, concurrency, and test order top the
  causes.
- Google Testing Blog — "Flaky Tests at Google and How We Mitigate
  Them" (2016); "Where do our flaky tests come from?" (2017).
