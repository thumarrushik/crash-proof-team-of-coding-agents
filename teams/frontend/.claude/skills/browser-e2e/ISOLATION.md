# ISOLATION — every test passes alone, in parallel, in any order

A test that depends on another test's leftovers is a test of run order,
not of the app. Playwright's best-practices bar is explicit: each test
gets its own browser context, its own storage state, its own data —
and must pass alone, in parallel, and in any order.

## Own context, own storage

- One browser context per test (Playwright's default per-test fixture) —
  cookies, localStorage, and sessions never bleed between tests.
- Log in via a fixture or a saved `storageState` produced by a setup
  project — not by test #1 logging in so tests #2–#40 can ride the
  session. A shared live session is shared mutable state with extra steps.
- If two tests need different users, they get different storage states;
  they never take turns mutating one account.

## Own data — seeded, not inherited

- Each test creates the records it asserts on, via API call or fixture in
  its own setup — never via the UI of a previous test and never by
  assuming a database row exists because "it always has".
- Make data unique per run (suffix a timestamp/UUID) so parallel workers
  can't collide on names or unique constraints.
- Clean up in teardown — or better, write tests that don't care about
  leftover rows because every assertion is scoped to data the test itself
  created. Scoped assertions survive a dirty database; "expect 3 rows
  total" does not.

## The independence checklist

Before calling a test done, it must survive all three:

1. **Alone:** run just this test on a fresh environment. Passing only
   after the full suite has run = hidden dependency on leftovers.
2. **In parallel:** run the suite with parallel workers. Collisions on
   shared accounts or records surface here.
3. **In any order:** shuffle or run the file's tests in reverse. Order
   dependence means one test is another test's setup.

`test.describe.serial` is a declaration of dependence — allowed only when
the journey itself is genuinely one continuous story, never as a fix for
tests that trample each other's data.

## Why this is the crash-proof property

Isolated tests are what make retries, sharding, and parallel CI honest:
a failure means the app broke, not the choreography. Every exception to
isolation converts some future red build into an hour of archaeology —
and feeds the flake taxonomy (test-order dependence) that the testing
team's flaky-hunt skill exists to hunt.

## Grounding

- Playwright docs, "Best Practices" — test isolation; contexts and
  storage state; parallelism.
- Google Testing Blog flaky-test analyses — test-order dependence and
  shared state among the recurring flake causes.
