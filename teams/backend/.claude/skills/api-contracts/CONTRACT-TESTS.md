# CONTRACT-TESTS — prove the promise field by field

A contract without a test is an intention. Per operation, per version, a
suite asserts exactly what consumers see — over real HTTP, against the real
service ([[lean-service]] TESTING.md bar). A mock of your own service
verifies nothing.

## What one operation's suite asserts

- **Happy path:** status code, then every documented response field checked
  for presence and type (and value only where the value itself is contract:
  enum members, error `code` strings, pagination field names).
- **Every enumerated failure:** one test each — bad input, missing entity,
  conflict, dependency down — asserting status + machine `code` + the
  canonical envelope shape. "An error happened" is not an assertion.
- **Pagination and collection shape:** page fields present, bound
  respected, empty page well-formed.
- **Deprecation marking** where it applies: `Deprecation`/`Sunset` headers
  present on a deprecated version's responses (DEPRECATION.md).

## The sensitivity bar — calibrated in both directions

The suite must **fail** when a served field disappears or changes type, and
must **pass** when a field is added. That rules out both lazy extremes:

- Whole-body exact equality fails on additive changes — too tight; it turns
  every safe addition into a false alarm.
- Spot-checking two fields passes on removals — too loose; it certifies a
  promise it never inspected.

Assert field-by-field with type/shape matchers (pact-style matching: types
and structure, not incidental values). Unknown extra fields are tolerated by
the test exactly as the contract tells clients to tolerate them.

## Consumer-driven, pact-style

Write each test from the consumer's seat: one interaction = the request a
consumer actually sends plus the response shape it depends on. When several
consumers exist, each consumer's expectations form a suite the provider
runs — the provider is verified against what consumers actually use, not
against what the docs hope they use (consumer-driven contracts, pact.io).
Practical payoff: a field no consumer's suite touches is a field you can
deprecate; a field three suites assert is load-bearing.

## Wiring into the change flow

- **Additive change:** add new assertions; existing tests are untouched and
  stay green. If an existing contract test had to change, the change was
  not additive — reclassify via CLASSIFICATION.md.
- **Breaking change:** the new version gets its own suite; the old
  version's suite keeps running unmodified until the version is deleted
  (DEPRECATION.md). Deleting the old suite before the old version is the
  same crime as deleting the version early.
- A contract-test edit in any diff is a tripwire: the promise changed.
  Stop, classify, and route the change accordingly.

## Grounding

- Consumer-driven contract testing — pact.io / docs.pact.io
