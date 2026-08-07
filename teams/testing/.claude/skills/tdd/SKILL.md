---
name: tdd
description: Test-first workflow for the testing lane — black-box suites against others' code, adversarial by default, property-based where inputs are structured. Use when building or extending any test suite.
---

# tdd (testing lane)

You write suites for code you did not write. Test the contract, try to
break it, and never trust a test you have not seen fail — a test never
seen red is unverified evidence.

## How to use this skill

1. Read this file when building or extending any test suite — before
   reading the implementation you are about to test.
2. Open BLACK-BOX.md for deriving and verifying the suite from the
   promise; open PROPERTIES.md when the input domain is structured
   (parsers, serializers, validators, calculations, converters).

## Topic map (load on demand)

| Task | File |
|---|---|
| Derive tests from the promise, see every test fail, attack the code | **[BLACK-BOX.md](BLACK-BOX.md)** |
| Write property-based tests — roundtrips, invariants, oracles, shrinking, seeds | **[PROPERTIES.md](PROPERTIES.md)** |

## The rules in one breath

1. Black-box first: derive tests from the promise — spec, API contract,
   signatures — before reading the implementation; open the source only
   afterward, to hunt unexercised branches.
2. See every test fail: red before the code exists for new behavior;
   for existing code, break the expectation once, watch red, restore
   green.
3. Attack, don't confirm: feed the testing-bar embarrass-us inputs,
   drive every failure branch, double-submit, reorder, overflow. A
   suite you never tried to make fail is a rubber stamp.
4. Property-based where inputs are structured: roundtrips, invariants,
   or a reference oracle; let shrinking hand you the minimal
   counterexample and record the failing seed.
5. One behavior per test, then the wide gate: names state behavior; run
   the narrow test, then the full suite; report exact commands and
   results.

**Blocked on sight:** expected values computed by calling the code under
test · change-detector tests that assert whatever the implementation
currently returns · tests that have never been observed failing ·
example-only coverage of a structured input domain where a property is
natural.
