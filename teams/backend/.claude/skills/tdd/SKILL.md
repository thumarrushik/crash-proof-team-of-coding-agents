---
name: tdd
description: Red-green-refactor for backend work with the test boundary chosen so tests cannot lie — contract-level tests over real HTTP and storage by default, pure unit tests only for genuine logic, mocks only at owned seams for true externals; use when implementing or fixing any backend behavior.
---

# tdd

## The loop

1. **Red.** Write the test first, run it, read the failure — it must fail for
   the behavior's absence, not an import error. A test never seen failing
   proves nothing.
2. **Green.** Implement the minimum that passes. No speculative branches.
3. **Refactor on green, tests untouched.** If a refactor forces test edits,
   the tests were pinned to implementation, not behavior — raise their
   altitude first, then refactor.
4. Full suite green before the next behavior; run once more after the final
   edit and report that number.

## The backend twist: choose the boundary before writing the test

- **Default altitude is the service contract:** HTTP request in, envelope
  out, real storage underneath (the [[lean-service]] real-infra bar). In a
  service, the service is the unit — contract-level tests survive refactors
  and catch the wiring, query, and serialization bugs unit tests
  structurally miss.
- **Drop to a pure unit test only for genuine logic:** parsers, calculators,
  validators — branching code with no I/O, tested through its public
  function, never its internals.
- **Know when a unit test lies.** A test that mocks your own repository or
  database passes while the actual query is wrong; a test asserting "method
  X was called" passes while behavior is broken. Never mock what you own.
  Mock only true externals (third-party APIs, LLM providers) at the
  injectable seam, and pin each seam with at least one test against the real
  dependency's recorded contract so the mock cannot drift.

## Failure paths are first-class

Each behavior gets red tests for its contracted failures — bad input, missing
entity, dependency down — asserting status + error `code` from the envelope,
not merely "an exception happened".

## Bug fixes

Start from a failing test at the boundary where the bug was observed: seen
over HTTP means the regression test speaks HTTP. Then fix, then green.

## Blocked on sight

- Tests written after the code "for coverage".
- Assertions on mock call counts or call order instead of observable output.
- A mocked own-database or own-repository layer anywhere.
- An endpoint marked tested with no test that speaks HTTP to it.
- Skipped or xfail tests used to reach green.

## Grounding

- Test-Driven Development: By Example (Kent Beck)
- "Test Desiderata" — behavior-sensitive, structure-insensitive (Kent Beck)
- "Testing of Microservices" — the honeycomb — engineering.atspotify.com
- Sociable vs solitary unit tests; "Mocks Aren't Stubs" — martinfowler.com
