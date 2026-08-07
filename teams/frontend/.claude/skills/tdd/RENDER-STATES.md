# RENDER-STATES — loading, empty, error, success all get asserted

Any component that fetches has four faces: loading, empty, error,
success. Users meet all four; most suites test one. Each state gets its
own behavior assertion — error paths are not optional, and empty is not
"success with less data" (the four states are the same quartet design-ui
requires you to design).

## Drive each state deterministically

With the network mocked at the HTTP boundary (MSW-style, per TROPHY.md),
each state is a handler away:

- **Success:** default handler returns representative data — including
  the awkward-but-legal shapes (long names, zero counts, missing optional
  fields), not only the demo-pretty payload.
- **Empty:** handler returns the well-formed empty response (`[]`, zero
  total). Assert the *designed* empty state — its message and its
  call-to-action — not just "the list didn't render".
- **Error:** override the handler to return 500 (and, where the contract
  distinguishes them, 4xx variants). Assert the user-facing message and
  the way out — the retry control is visible and, when clicked with the
  handler restored, recovers to success. That recovery test is the whole
  point of the error state.
- **Loading:** assert it via the transition, not a frozen mock: on
  render, the loading indicator (role `progressbar`/`status` or its
  accessible text) is visible; after the response resolves, use
  `findBy*` to await the settled content and assert loading is gone.

## Assert like a user in every state

- Query by role/label/text in all four branches — the error message and
  the empty-state copy are user-visible text; assert that text, not an
  `ErrorBox` component's presence.
- Use `findBy*` (retrying) for content that appears after async work and
  `queryBy*` for asserting absence; `getBy*` for content that must be
  there now. Wrong query family here is the classic flake source
  ("Common Mistakes with React Testing Library").
- Never assert internals — that a state flag is `"error"` — the flag can
  be right while the screen shows nothing.

## TDD order for a fetching component

1. Red: success-path behavior test against the default handler.
2. Green, then add empty, error, and loading tests one at a time — each
   watched failing first. Writing all four before any implementation
   invites four tests that fail for the same missing-import reason.
3. A bug report in any state becomes a failing test in that state before
   the fix (the regression-suite discipline, one level down).

## Grounding

- Kent C. Dodds, "Common Mistakes with React Testing Library" — query
  families, async queries, asserting like a user.
- Testing Library Guiding Principles and query priority.
- MSW docs — HTTP-boundary request handlers and per-test overrides.
- Nielsen Norman Group, "Error-Message Guidelines" — what the error
  state must show (the text your test asserts).
