# FAILURE-PATHS — contracted failures are behavior; mocks are for externals

The happy path is the smaller half of a behavior's contract. What the code
does when input is bad, the entity is missing, or the dependency is down is
behavior users hit in production — so it gets the same red-first treatment,
with the same precision.

## Failure paths are first-class

Each behavior gets red tests for its **contracted failures**:

- **Bad input** — malformed, out-of-range, wrong type, empty where content
  is required.
- **Missing entity** — the ID that doesn't exist, the file that isn't
  there, the row already deleted.
- **Dependency down** — the store unreachable, the downstream call timing
  out, the queue refusing.

For each, assert the **exact observable outcome** the contract promises:
the specific status and error code, the specific exception type and its
message shape, the specific fallback value. "An exception happened" asserts
nothing — `pytest.raises(Exception)` passes on the typo in your test just
as happily as on the contracted error. Precision is the difference between
pinning a failure contract and merely observing chaos.

Failure tests go through the same loop as any behavior: red first, watch it
fail for the right reason, minimum code to green.

## Never mock what you own

Mock only **true externals** — the third-party API, the clock, the network
you don't control — and only at an **injectable seam** (a parameter, a
constructor argument, a fixture the design already exposes). Everything you
own runs real in the test.

Why the line is absolute: a mocked-out own-layer lets the actual wiring be
wrong while the suite stays green. The mock returns what you told it to,
the test asserts what the mock returned, and the two real components have
never met — a green suite over an integration that fails on first contact.
Fowler's terms: sociable tests by default; solitary tests only where the
collaborator is genuinely external.

Corollaries:

- Do not mock your own database layer to avoid a test database — the
  repo's test infrastructure exists for this; use it.
- Do not mock a function in the same module to "isolate" the one under
  test — their interaction is exactly what needs testing.
- Simulating a dependency-down failure path is the legitimate use of the
  seam: inject the external that raises, then assert your own real code's
  contracted response to it.

## Assert observable output, not mock choreography

Assertions on mock call counts and call arguments test the implementation's
current shape, not its behavior — they break under honest refactors and
pass under real bugs. Assert what a caller can observe: the return value,
the raised error, the state change, the emitted record. If the only thing a
test can assert is that a mock was called, the test is standing at the
wrong boundary — move it up until an observable outcome exists.

## Grounding

- Martin Fowler, "Self-Testing Code" and "Mocks Aren't Stubs": behavior
  over implementation; sociable tests by default.
- Kent Beck, Test-Driven Development: By Example — every contracted
  outcome, including failures, earns its red test.
