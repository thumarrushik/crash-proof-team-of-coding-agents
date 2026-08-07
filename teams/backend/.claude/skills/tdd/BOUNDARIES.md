# BOUNDARIES — choose the altitude before the first red test

The boundary decides whether a green suite means "it works" or "the mocks
agree with each other". Choose it per behavior, before writing the test.

## Default altitude: the service contract

HTTP request in, envelope out, real storage underneath — the
[[lean-service]] real-infra bar. In a service, the service is the unit.
Contract-level tests are **behavior-sensitive and structure-insensitive**
(Beck's two load-bearing test desiderata): they fail when behavior breaks
and survive any refactor that preserves it. They are also the only tests
that catch the bug classes unit tests structurally miss — wiring and DI
mistakes, wrong SQL, serialization drift, middleware order, transaction
scope.

This is the microservice honeycomb (Spotify) rather than the classic
pyramid: the fat middle is service-level tests through the real API with
the service's own real storage, mocking only what lies *outside* the
service; implementation-detail tests are few; whole-system multi-service
tests fewest of all — slow, flaky, and owned elsewhere.

## When to drop to a pure unit test

Genuine logic only: parsers, calculators, validators, state machines —
branching code with no I/O. Test it through its public function, never its
internals; feed inputs, assert outputs. If setting up the unit test means
constructing fakes for your own collaborators, that is not genuine logic —
go back up to the contract.

## Know when a unit test lies

- A test that mocks your own repository or database passes while the actual
  query is wrong — the test asserts the mock's opinion, and the mock has
  your bug.
- A test asserting "method X was called with Y" (behavior verification on
  owned code) passes while observable behavior is broken, and shatters on
  any refactor — the mockist failure mode Fowler catalogs in "Mocks Aren't
  Stubs". Prefer sociable tests: real collaborators, state/output
  assertions.
- A green suite whose fixtures never touch the real schema will happily
  certify code the database rejects on first contact.

## The mocking rule

**Never mock what you own** — your database, your repositories, your
services, your own HTTP endpoints. Mock only true externals — third-party
APIs, LLM providers, payment gateways — and only at the injectable seam
the house style already provides ([[lean-service]] LLM.md). Then pin each
seam: at least one test runs against the real dependency's recorded
contract (recorded responses, sandbox, or provider contract) so the mock
cannot drift from reality unnoticed. An unpinned mock is a wish.

## Deciding in ten seconds

1. Does the behavior touch HTTP, storage, or wiring? → contract test.
2. Is it pure branching logic with no I/O? → unit test on the public
   function.
3. Does the test want a fake of something you own? → wrong altitude; go up.
4. Does it need a true external? → injectable seam + real-contract pin.

## Grounding

- Test-Driven Development: By Example (Kent Beck)
- "Test Desiderata" — behavior-sensitive, structure-insensitive (Kent Beck)
- "Testing of Microservices" — the honeycomb — engineering.atspotify.com
- Sociable vs solitary unit tests; "Mocks Aren't Stubs" — martinfowler.com
