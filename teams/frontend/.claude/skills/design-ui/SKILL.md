---
name: design-ui
description: Visual and UX discipline for user-facing surfaces — hierarchy, tokens, the four render states, WCAG 2.2 AA, responsive. Use when creating or changing anything a user sees.
---

# design-ui

Design the surface before styling it. Reuse before inventing. Make every
state of the data visible and every element reachable. This is the frontend
lane's house standard for anything a user sees; the [[state-and-errors]] and
[[browser-e2e]] skills carry the data-handling and proving halves.

## How to use this skill

1. Read this file before creating or changing any user-facing surface.
2. Open the topic file for the phase you are in (below): plan the layout,
   then the states, then accessibility, then responsiveness. Load what the
   surface needs, not all four.

## Topic map (load on demand)

| Task | File |
|---|---|
| Inventory the design system, set hierarchy, one primary action | **[LAYOUT.md](LAYOUT.md)** |
| Ship all four render states with NN/g-grade error messages | **[RENDER-STATES.md](RENDER-STATES.md)** |
| Meet WCAG 2.2 AA — semantics, focus, contrast, targets, color | **[ACCESSIBILITY.md](ACCESSIBILITY.md)** |
| Reflow to 320px, then prove the surface renders | **[RESPONSIVE-VERIFY.md](RESPONSIVE-VERIFY.md)** |

## The rules in one breath

1. Inventory first: extend the repo's components, tokens, and reference
   page — never fork a second styling system.
2. One primary action per view; size, weight, spacing come from the
   existing scale, never hand-picked one-offs.
3. Every data-driven surface ships all four render states — loading, empty,
   error, success — each with a real assertion.
4. Error messages say what happened, why, and the next action (NN/g);
   never a bare code, never blame the user; form errors inline, input kept.
5. WCAG 2.2 AA: semantic HTML first, ARIA only to fill gaps; labels;
   visible unobscured focus; contrast 4.5:1 / 3:1; targets >=24x24px;
   never color alone.
6. Reflow to 320px with no horizontal scroll or lost function; relative
   units; verify at phone width.
7. Prove it rendered — a browser test ([[browser-e2e]]) or at minimum a
   rendered assertion; markup alone is a claim, not proof.

**Blocked on sight:** a second styling system beside the existing one ·
"Something went wrong" with no cause and no next step · a `div`/`span` with
a click handler impersonating `button`/`a` · a focus outline removed
without an equal-or-better replacement · color as the only signal ·
desktop-only layouts · placeholder screens shipped as done.
