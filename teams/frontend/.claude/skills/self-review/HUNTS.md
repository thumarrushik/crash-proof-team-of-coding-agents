# HUNTS — six passes over your own diff, each with its check recipe

Run all six, in order, after the last edit. Each hunt names what it
catches and exactly how to check it — "I'm confident it's fine" is not
one of the recipes.

## 1. Walk the four render states on every touched surface

Catches: surfaces that only ever rendered the success path.

**How to check:** list every component the diff touched that renders
data. For each, reach all four states in the running app or a test:
success (real data), empty (a response with `[]`/zero total — assert the
designed message and next action, not a blank region), error (force it —
override the MSW handler or `page.route()` the call to 500 — and confirm
what happened + a way out, per NN/g), loading (throttle or delay the
response; watch for layout jump when content lands). A state you cannot
reach by any of these means is a missing state, not a done one — build
the path, then verify it.

## 2. Accessibility pass on every new or changed element

Catches: surfaces that work for a mouse user with good eyesight and
nobody else.

**How to check:** for each new/changed element in the diff — (a) is the
tag honest? `button`/`a`/`label`, not divs with handlers; grep the diff
for `onClick` on non-interactive tags. (b) Put the mouse down and drive
the whole flow by keyboard: every control reachable by Tab, operable by
Enter/Space, focus visibly outlined at each stop. (c) Every input
associated with a label — `getByLabel` finding it is the test. (d)
Contrast and target size at the WCAG 2.2 AA bar (design-ui carries the
numbers); state never conveyed by color alone. (e) If `getByRole` cannot
find the element in a test, ship the markup fix, not a test-id.

## 3. Audit the state classification

Catches: server state leaking into client stores, doubled sources of
truth (state-and-errors is the checklist).

**How to check:** grep the diff for store/context writes (`dispatch`,
`set`-prefixed store setters, context value changes) and confirm nothing
written there originated in an API response. Grep for `useState` holding
`isLoading`/`isError` next to a query hook — those flags come from the
cache. For each new piece of state, name its single owner; if a second
copy exists, one of them goes. For each optimistic update, point at its
onError rollback and its user-facing failure message — no rollback path,
no optimism.

## 4. Hunt silent failures

Catches: errors that die in the console while the screen stays pleasant.

**How to check:** grep the diff for `catch` — every catch block either
surfaces to the user, rethrows, or reports; an empty catch or a
console-only catch is blocked on sight. For every fetch and mutation
touched, name the pixel that changes when it fails. For every spinner,
name its error exit. Then run the app with the API forced to fail and
watch: if the UI's only reaction is a console line, the hunt found its
prey.

## 5. Grep the callers

Catches: renamed props, changed signatures, moved files with one stale
call site — a white screen in production that no component test sees.

**How to check:** for every export the diff renamed, re-typed, or moved,
grep the workspace for the old name and the current name; visit every
call site and confirm it compiles against the new shape. Do not trust
the editor's rename alone — string references, lazy imports, and
route-config lookups escape it. TypeScript helps only where types flow;
`grep -rn` is the floor.

## 6. Sweep leftovers, then re-run everything as your final action

Catches: debug residue shipping, and stale green verdicts.

**How to check:** grep the diff for `console.log`, `debugger`,
commented-out JSX, dead styles, `.only`/`.skip` on tests — remove them.
Then, after the sweep (which is itself an edit), run the full suite and
the browser tests when they exist, as the literal last action before
reporting. Carry that run's actual output into `tests_passed`. A
remembered green is the failure this house measured at 3 wrong in 10 —
if you edited anything after the last run, the last run is void.

## Grounding

- WCAG 2.2 AA and the First Rule of ARIA (via design-ui) — w3.org.
- Nielsen Norman Group, "Error-Message Guidelines".
- Kent C. Dodds, "Application State Management with React".
- This repo's measured tests_passed experiment — the final-action run
  rule is the countermeasure to stale verdicts.
