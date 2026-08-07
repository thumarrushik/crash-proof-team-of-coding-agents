# SUITE-AS-SPEC — the suite is the living specification

Someone reading test names alone should learn what the system
guarantees. That is the filing standard: every regression test lands
where a spec reader would look for the promise, named as the promise,
asserting only what the promise says.

## Name by behavior, not by ticket

- The name states the guarantee: `rejects_expired_token_with_401`,
  `pagination_returns_empty_page_beyond_last`, not `test_bug_1234`,
  `test_fix`, or `test_issue_regression_2`.
- The ticket reference goes in a comment or docstring if traceability
  matters — metadata, never identity. A ticket-named test is unreadable
  the day the tracker changes and unreviewable the day it fails.
- If you cannot name the behavior, you have not isolated it — go back
  to BUG-TO-TEST.md step 1.

## File by feature, not by incident

- The regression test lives with its feature's other tests: the expired
  token test goes in the auth suite, next to the other token promises.
- No separate `regression/` or "old bugs" bucket. An incident-ordered
  pile duplicates feature coverage, rots unowned, and reads as a
  chronicle — a spec organized by embarrassment date.
- If the feature has no test module yet, the bug just told you the spec
  has a missing chapter; create it and the test is its first page.

## Assert at the boundary, survive refactors

- Inputs -> observable outputs: responses, emitted events, persisted
  state. Test behavior, not implementation (Google Testing on the
  Toilet): a test pinned to private internals fails on harmless
  refactors and trains people to update tests reflexively — which is
  how real regressions sneak through a sea of "expected" red.
- The test must survive any refactor that preserves the behavior. If a
  rename inside the module breaks it, the test was asserting the diary,
  not the promise — fix the test's altitude.

## Audit passes (using this file on existing coverage)

When auditing a suite, sweep for the anti-spec patterns:

- Names citing tickets or "fix"/"bug" — rename to the behavior while
  you still know what it was.
- `skip`/`xfail` without a reason and an owner — each is a promise
  currently not being kept, invisible in green output; give it both or
  give it deletion with a stated rationale.
- Tests loosened over time (assertions commented out, tolerances
  widened) — each loosening reopened a return ticket; restore or
  justify.
- Duplicated incident tests that all pin one behavior — consolidate
  into the feature module's canonical promise test.

## Grounding

- Google Testing on the Toilet, "Test Behavior, Not Implementation".
- Martin Fowler, "Self-Testing Code" — the suite as an executable
  specification you can trust after every change.
