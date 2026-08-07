# The six audits — run in order, each with its method

Every audit below targets a way a green suite lies. The method column is
the point: search and run, don't skim and recall.

## 1. Seen-red proof

For each test in the diff, find the transcript moment it failed — before
the code existed, or via a deliberately broken expectation you then
restored. Method: list the new test names (`git diff --stat`, then grep
`def test_`/`it(`), and for each, locate the red run in your session
history. Not there: break the expectation now, run, watch red, restore,
run green. A test only ever seen green proves nothing about its power to
fail.

## 2. Mutation audit

Per assertion, name the small code change it would fail to catch: flip a
comparison, off-by-one a boundary, delete a guard, swap an early return —
in your head or in a scratch copy. If no test would go red, the assertion
is decoration; strengthen it (exact values over presence checks, full
shapes over single fields, error codes over "an exception happened").
When the repo carries a mutation tool (Stryker, PIT, mutmut), run it on
the touched modules; every survived mutant is a reproducible bug the
suite would ship.

## 3. Change-detector hunt

Hunt the three disguises of a test that asserts "whatever the code does":

- expected values computed by calling the code under test;
- a test body that restates the implementation line by line;
- assertions on private internals that break on harmless refactors.

Rewrite each against the promise (spec, contract, docstring) — otherwise
the next refactor breaks the test, someone deletes it, and the guardrail
is gone. (Google Testing on the Toilet: "Change-Detector Tests Considered
Harmful.")

## 4. Independence proof

New tests must pass alone, in random order, and twice in a row. Method:
run the single test file; run the suite with order randomization on (and
keep it on in config); run the new tests twice in one process. Failures
here mean leaked state — DB rows, globals, module caches, files — fix the
fixture, never the ordering.

## 5. Names as a spec

Read only the new test names, filed location included. A reader must
learn what the system guarantees: `rejects_expired_token_with_401`, filed
by feature — not `test_bug_1234`, not a chronicle-of-incidents bucket.
Rename and refile now; the suite is a living specification or it is a
junk drawer.

## 6. Leftovers, then the final run

No `.only`/focused tests, no skips without a reason and an owner, no
sleeps added to "stabilize", no debug output, only intended files changed.
Then run the FULL suite after your last edit and carry that literal result
into `tests_passed` — this house measured remembered verdicts wrong 3 in
10; the final-action run is the countermeasure.

## Grounding

- Google Testing Blog, "Code Coverage Best Practices": effectiveness lives
  in assertion strength, not counts.
- Stryker / PIT mutation-testing docs: the survived-mutant lens applied by
  hand in audit 2.
- Google Testing on the Toilet: "Change-Detector Tests Considered Harmful".
- This repo's measured tests_passed experiment
  (articles/final/the-agent-grades-its-own-homework.md): the final-action
  run rule.
