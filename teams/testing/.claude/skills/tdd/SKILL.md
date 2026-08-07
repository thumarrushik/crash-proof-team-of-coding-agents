---
name: tdd
description: Test-first workflow for the testing lane — black-box suites against others' code, adversarial by default, property-based where inputs are structured. Use when building or extending any test suite.
---

# tdd (testing lane)

You write suites for code you did not write. Test the contract, try to break
it, and never trust a test you have not seen fail.

## Phases — in order

1. **Black-box first.** Derive tests from the promise — spec, API contract,
   signatures, task description — before reading the implementation.
   Reading the code first anchors you to what it does, and you will
   faithfully re-encode its bugs as expectations. Open the source only
   afterward, to hunt unexercised branches.
2. **See every test fail.** New test for new behavior: run it red before
   the code exists. New test for existing code: prove it CAN fail — break
   the expectation or the input once, watch red, restore green. A test
   never seen red is unverified evidence.
3. **Attack, don't confirm.** Your job is to break the code. Feed the
   testing-bar embarrass-us inputs, drive every failure branch, double-
   submit, reorder, overflow. A suite you never tried to make fail is a
   rubber stamp.
4. **Property-based where inputs are structured.** Parsers, serializers,
   validators, calculations, converters: write properties (Hypothesis,
   fast-check) — roundtrip (decode(encode(x)) == x), invariants (length,
   ordering, conservation), or comparison against a reference oracle. Let
   shrinking hand you the minimal counterexample; record the failing seed
   so the repro is deterministic.
5. **One behavior per test, then the wide gate.** Names state behavior;
   run the narrow test, then the full suite; report exact commands and
   results.

## Blocked on sight

- Expected values computed by calling the code under test.
- Change-detector tests that assert whatever the implementation currently
  returns.
- Tests that have never been observed failing.
- Example-only coverage of a structured input domain where a property is
  natural.

## Grounding

- Kent Beck, Test-Driven Development: By Example — red before green.
- Hypothesis documentation: @given strategies, invariant and roundtrip
  properties, shrinking to minimal counterexamples.
- Google Testing on the Toilet: "Change-Detector Tests Considered Harmful".
