# PROMISES — one test per behavior the code claims

A suite's table of contents is the code's list of promises, not its list
of functions. Before writing any test, write the promise list; the suite
is done when every promise has a test, not when a percentage is reached.

## Enumerate the promises

Harvest them from every place the code makes a claim:

- **The spec / ticket:** each acceptance criterion is a promise.
- **Docstrings and comments:** "returns the newest first" is a promise —
  and one that silently breaks if only length is asserted.
- **The API contract:** every documented field, enum value, status code,
  and error `code` (the backend team's api-contracts skill treats these
  as published promises; the suite is where they get enforced).
- **Types and signatures:** an `Optional` return promises a None branch;
  a raised exception in the signature promises a raising test.

Write the list down. A promise you cannot phrase as "given X, the caller
observes Y" is not yet understood well enough to implement, let alone
test.

## Failure branches are promises too

Every failure the code can hand a caller gets its own test with its
exact observable outcome — status + machine code + envelope shape for
HTTP (422/404/409/503), exception type + message contract for libraries,
rejection value for async. "It throws something" is not an outcome.
Include the unhappy infrastructure: timeouts, dependency down,
mid-operation cancellation — the branches that only ever run in
production are the ones most in need of a rehearsal.

## Coverage is a floor detector, never a target

- Use the coverage report exactly once per suite: to find code no test
  reaches. An unreached branch means a promise with no test — go add
  the test for the *promise*, not a test that merely executes the line.
- Never treat the percentage as the goal. High coverage does not
  guarantee effective tests (Google Testing Blog, "Code Coverage Best
  Practices"): an assertion-free test raises the number and verifies
  nothing. As a target, coverage is gameable and gets gamed (Fowler,
  "TestCoverage") — the number goes up while trust in green goes down.
- A diff that raises coverage while adding no assertions is blocked on
  sight; it converts the floor detector into a decoration dispenser.

## Assert at the public boundary

Each promise-test asserts inputs -> observable outputs at the boundary
callers actually use: the HTTP response, the return value, the emitted
event, the row that exists afterward. Not private helpers, not internal
call counts. A refactor that keeps every promise must keep the suite
green; a suite that breaks on behavior-preserving refactors is asserting
the implementation's diary, not its promises.

## Grounding

- Google Testing Blog, "Code Coverage Best Practices" (2020) — high
  coverage does not guarantee effective tests.
- Martin Fowler, "TestCoverage" bliki — coverage finds untested code; as
  a target it is gameable.
