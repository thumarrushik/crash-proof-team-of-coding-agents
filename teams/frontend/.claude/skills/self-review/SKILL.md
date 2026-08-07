---
name: self-review
description: Review your own UI diff as the user and the reviewer will — all four render states present, accessibility verified, state classified correctly, no silent failures, last run cited. Use before declaring any frontend task done.
---

# self-review

Re-read the entire diff cold, then walk the actual rendered surface. These
hunts target the bug classes a green component suite passes right over.

1. **Walk the four render states on every touched surface.** Loading (no
   layout jump), empty (says why, offers the next action), error (what
   happened + a way out, per NN/g), success. A state you cannot reach in the
   UI or a test is a missing state, not a done one.
2. **Run the accessibility pass on every new or changed element.** Real
   `button`/`a`/`label` semantics, not divs with handlers; every input
   labeled; keyboard path complete and focus visible; contrast and target
   size at the WCAG 2.2 AA bar (design-ui carries the numbers); state never
   conveyed by color alone. If getByRole cannot find your element, ship the
   markup fix, not a test-id.
3. **Audit the state classification.** Nothing fetched got mirrored into a
   client store; no hand-rolled isLoading/isError beside a query cache; one
   source of truth per fact; every optimistic update carries its rollback
   (state-and-errors is the checklist).
4. **Hunt silent failures.** Empty catches, console-only errors, spinners
   with no error exit, mutations whose failure the user never sees. Every
   failure path must reach the screen.
5. **Grep the callers.** Renamed props, changed component signatures,
   moved files: find every usage — an updated component with one stale
   call site is a white screen in production.
6. **Sweep leftovers, then re-run everything as your final action.** No
   debug logging, dead styles, commented-out JSX, or skipped tests. Run the
   full suite (and the browser tests when they exist) after your last edit,
   and carry that literal result into `tests_passed` — a remembered green
   is the failure this house measured at 3 wrong in 10.

## Blocked on sight

- A touched surface missing any of the four render states.
- A clickable div, an unlabeled input, or a removed focus outline.
- Server data copied into a client store "for convenience".
- Declaring done from a remembered or assumed test run.

## Grounding

- WCAG 2.2 AA and the First Rule of ARIA (via design-ui) — w3.org.
- Nielsen Norman Group, "Error-Message Guidelines".
- Kent C. Dodds, "Application State Management with React".
- This repo's measured tests_passed experiment: the final-action run rule
  is the countermeasure to stale verdicts.
