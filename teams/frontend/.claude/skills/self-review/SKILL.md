---
name: self-review
description: Review your own UI diff as the user and the reviewer will — all four render states present, accessibility verified, state classified correctly, no silent failures, last run cited. Use before declaring any frontend task done.
---

# self-review

Re-read the entire diff cold, then walk the actual rendered surface.
These hunts target the bug classes a green component suite passes right
over — the states nobody reached, the div nobody could tab to, the
failure nobody saw.

## How to use this skill

1. Read this file before declaring any frontend task done — after the
   last edit, not as a formality during it.
2. Open HUNTS.md and run all six hunts in order, each with its concrete
   check recipe. This skill has one topic file because the review is one
   sweep; do not sample hunts.

## Topic map (load on demand)

| Task | File |
|---|---|
| Run the six hunts with concrete check recipes — states, a11y, state audit, silent failures, callers, leftovers + final run | **[HUNTS.md](HUNTS.md)** |

## The rules in one breath

1. Walk the four render states on every touched surface — loading, empty,
   error, success; a state you cannot reach is missing, not done.
2. Run the accessibility pass on every new or changed element — real
   semantics, labels, keyboard path, visible focus, WCAG 2.2 AA.
3. Audit the state classification — nothing fetched mirrored into a
   client store; every optimistic update carries its rollback.
4. Hunt silent failures — every failure path must reach the screen.
5. Grep the callers — one stale call site is a white screen in
   production.
6. Sweep leftovers, then re-run everything as your final action and carry
   that literal result into `tests_passed` — a remembered green is the
   failure this house measured at 3 wrong in 10.

**Blocked on sight:** a touched surface missing any of the four render
states · a clickable div, an unlabeled input, or a removed focus
outline · server data copied into a client store "for convenience" ·
declaring done from a remembered or assumed test run.
