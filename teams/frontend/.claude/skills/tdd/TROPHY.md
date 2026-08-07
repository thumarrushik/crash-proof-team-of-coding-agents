# TROPHY — pick the test's altitude before writing it

"Write tests. Not too many. Mostly integration." (Kent C. Dodds). The
Testing Trophy is the frontend's answer to the pyramid: integration tests
carry the most confidence per line of test code, because they exercise the
component the way the app actually uses it.

## The four layers, bottom to top

1. **Static (base):** TypeScript and lint catch typos, wrong props, and
   unreachable branches at zero test cost. The base layer, not a
   substitute for any layer above it.
2. **Unit:** pure logic *extracted from* components — formatting,
   validation, reducers, date math. If a function needs a DOM to test, it
   is not a unit test candidate; if a component's logic is hard to test,
   extract the logic and unit-test the extraction.
3. **Integration (the bulk — the trophy's cup):** render the component
   with its real children and hooks; mock the network at the HTTP
   boundary (MSW-style request handlers), not at the module boundary.
   Interact via userEvent, assert visible outcomes. This is the default
   altitude — when in doubt, write this test.
4. **E2E (the small top):** one per changed user story, in a real
   browser — hand these to the browser-e2e skill. Not one per component;
   e2e duplicating integration coverage is pure run-time cost.

## Why mock at HTTP, not at modules

Mocking `useQuery` or the api module tests your mock's shape, not the
component's wiring — the test keeps passing after the real hook's
contract changes. An MSW-style handler intercepts the actual request, so
the component's full data path (hook, cache, serialization, error
branch) runs for real. It also makes driving error and empty responses a
one-line handler override (see RENDER-STATES.md).

## Altitude smells and their fixes

- A test that breaks when you rename a CSS class or reshuffle divs —
  asserted markup accidents; re-aim at role/label/text the user sees.
- A test full of `mockReturnValue` chains for internal hooks — dropped
  below the component's public surface; move up to integration.
- An e2e asserting a pure formatting rule — two layers too high; extract
  and unit-test it, keep e2e for the journey.
- Snapshot tests as behavior verification — a snapshot asserts
  "something changed", never "the behavior is right"; replace with
  explicit assertions on what the user sees ("Common Mistakes with React
  Testing Library").

## TDD at each altitude

Red/green/refactor applies at every layer (Kent Beck): the failing test
comes first and must fail *for the right reason* — an assertion miss on
the behavior, not a missing import or a wrong query. Watch it fail before
making it pass; a test you never saw red proves nothing about itself.

## Grounding

- Kent C. Dodds — "Write tests. Not too many. Mostly integration." and
  the Testing Trophy.
- Kent C. Dodds, "Common Mistakes with React Testing Library".
- Testing Library Guiding Principles — query priority, role first.
- Kent Beck, Test-Driven Development: By Example — red/green/refactor.
