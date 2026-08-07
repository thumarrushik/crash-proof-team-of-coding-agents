# BLACK-BOX — derive from the promise, verify red, then attack

You are testing someone else's code. The order protects you from the
central hazard of that position: reading the implementation first
anchors you to what the code *does*, and you will faithfully re-encode
its bugs as expectations.

## Derive tests from the promise — before reading the code

Sources, in order of authority: the spec/task description, the API
contract (documented fields, status codes, error codes), the public
signatures and types, the docstrings. From these alone, write the
promise list (the testing-bar PROMISES.md discipline) and the expected
outcome for each — including every failure branch.

- **Expected values come from the promise or an independent
  computation** — worked by hand, from the spec's examples, or from a
  reference implementation. Never by running the code under test and
  pasting its output into the assertion: that produces a test that
  certifies the code agrees with itself, bug for bug.
- If the promise is ambiguous ("returns the results sorted" — by
  what?), the ambiguity is a finding to raise, not a blank to fill by
  peeking at the implementation.

Only after the black-box suite exists, open the source — for exactly
one purpose: hunting branches your suite does not exercise (the guard
you didn't know existed, the cache path, the retry loop). Each found
branch becomes a new promise-derived test, not a transcription of the
branch's current behavior.

## See every test fail

- **New behavior:** run the test red before the code exists (Kent Beck:
  red before green). The failure message must be the behavior missing,
  not an import error.
- **Existing code:** the code may already pass your test — so prove the
  test CAN fail. Break the expectation or the input once (flip the
  expected value, drop a required field), watch red, restore green.
  Thirty seconds that convert the test from decoration to evidence.
- A test that cannot be made to fail is asserting nothing — the
  change-detector failure mode inverted.

## Attack, don't confirm

Your job is to break the code, and a suite you never tried to make fail
is a rubber stamp:

- Feed the testing-bar embarrass-us inputs and the full edge taxonomy:
  empty, boundary, duplicate, hostile strings, huge, wrong types.
- Drive every failure branch to its exact designed outcome — not "it
  errors" but "422 with code `validation_failed`".
- Abuse the protocol: double-submit the same request, reorder the call
  sequence, overflow the pagination, cancel mid-operation.
- When an attack succeeds, that is the job working: file the failing
  test as the reproduction (regression-suite BUG-TO-TEST.md) — do not
  soften the test to match the broken behavior.

## Change-detector tests are the anti-pattern

A test that asserts whatever the implementation currently returns —
snapshotting its output, mirroring its internal call sequence — fails
on every innocent change and never on a real bug that preserves the
mirrored shape (Google Testing on the Toilet, "Change-Detector Tests
Considered Harmful"). If you cannot say which *promise* an assertion
enforces, delete or re-derive it.

## Grounding

- Kent Beck, Test-Driven Development: By Example — red before green.
- Google Testing on the Toilet — "Change-Detector Tests Considered
  Harmful".
