---
name: self-review
description: Audit the suite you just wrote as the deliverable it is — every test seen red, assertions that would catch mutants, independence proven, names that read as spec. Use before declaring any testing task done.
---

# self-review

Your diff IS tests, so this review audits evidence quality: a weak suite
ships silent permission for other people's bugs.

1. **Prove every new test was seen red.** For each test in the diff, find
   the transcript moment it failed — before the code existed, or via a
   deliberately broken expectation that you then restored. A test only ever
   seen green is unverified evidence; go make it fail once.
2. **Mutation-audit your assertions.** Per assertion: what small code change
   would slip past it? Flip a comparison, off-by-one a boundary, delete a
   guard in your head — if nothing would go red, the assertion is
   decoration (testing-bar step 3). Strengthen it now.
3. **Hunt your own change-detectors.** Any expected value computed by
   calling the code under test, any test restating the implementation, any
   assertion on private internals: rewrite against the promise, or the
   suite breaks on the next harmless refactor and someone deletes it.
4. **Prove independence.** New tests pass alone, in random order, and
   twice in a row (no leaked rows, globals, files, or module caches). If
   the runner supports order randomization, run it once and keep it on.
5. **Read the names as a spec.** Names state the promise
   (`rejects_expired_token_with_401`), filed by feature — a reader who sees
   only names must learn what the system guarantees.
6. **Sweep leftovers, then run the full suite as your final action.** No
   focused/only tests, no skips without a reason and owner, no sleeps added
   to stabilize, no debug output. Then run everything after your last edit
   and carry that literal result into `tests_passed` — this house measured
   remembered verdicts wrong 3 in 10.

## Blocked on sight

- A test in the diff that was never observed failing.
- A `.only`/focused test or an unexplained skip left in.
- Expected values derived from the implementation under test.
- Declaring done from a remembered or assumed run.

## Grounding

- Google Testing Blog, "Code Coverage Best Practices": effectiveness lives
  in assertion strength, not counts.
- Stryker / PIT mutation-testing docs: the survived-mutant lens applied by
  hand in step 2.
- Google Testing on the Toilet: "Change-Detector Tests Considered Harmful".
- This repo's measured tests_passed experiment: the final-action run rule.
