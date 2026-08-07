---
name: design-ui
description: Visual and UX discipline for user-facing surfaces — hierarchy, tokens, the four render states, WCAG 2.2 AA. Use when creating or changing anything a user sees.
---

# design-ui

Design the surface before styling it. Reuse before inventing. Make every state
of the data visible and every element reachable.

## Phases — in order

1. **Inventory.** Find the repo's components, tokens (color, spacing, type
   scale), and a reference page. Extend them; never fork a second style. New
   UI must look like it was always there.
2. **Hierarchy.** One primary action per view. Size, weight, and spacing come
   from the existing scale — no hand-picked one-off values. Group related
   controls; align to the grid already in use.
3. **The four render states.** Every data-driven surface ships loading (space
   reserved, no layout jump), empty (say why it is empty and offer the next
   action), error, and success. Error messages follow NN/g: say what happened
   in plain language, why (when known), and what the user can do next —
   polite, precise, constructive; never a bare error code, never blame the
   user. Form errors appear inline beside the field and preserve the user's
   input.
4. **Accessibility (WCAG 2.2 AA).**
   - Semantic HTML first; ARIA only to fill real gaps (First Rule of ARIA).
   - Every input labeled; every action keyboard-reachable in a logical order.
   - Focus visible (SC 2.4.7) and not obscured (SC 2.4.11); if you restyle
     the outline, the replacement must be at least as visible.
   - Contrast: >=4.5:1 body text; >=3:1 large text, UI components, and
     meaningful graphics (SC 1.4.3, 1.4.11).
   - Pointer targets >=24x24 CSS px (SC 2.5.8); prefer 44px for primary
     touch actions.
   - Never color alone to convey state (SC 1.4.1); icons and images carry
     text alternatives.
5. **Responsive.** Content-first layout that reflows to 320px width without
   horizontal scrolling or loss of function (SC 1.4.10); relative units;
   verify at phone width, not just desktop.
6. **Verify rendered.** User-visible behavior gets a browser test (see
   browser-e2e) or at minimum a rendered assertion — markup alone is a
   claim, not proof.

## Blocked on sight

- A second styling system beside the existing one.
- "Something went wrong" with no cause and no next step.
- `div`/`span` with click handlers impersonating `button`/`a`.
- Focus outline removed without an equal-or-better replacement.
- Color as the only signal; desktop-only layouts; placeholder screens
  shipped as done.

## Grounding

- WCAG 2.2 (W3C Recommendation, 2023): SC 1.4.1, 1.4.3, 1.4.10, 1.4.11,
  2.4.7, 2.4.11, 2.5.8.
- W3C "Using ARIA" (First Rule of ARIA) and the ARIA Authoring Practices
  Guide (APG) interaction patterns.
- Nielsen Norman Group: "Error-Message Guidelines" and "10 Design Guidelines
  for Reporting Errors in Forms".
- NN/g 10 Usability Heuristics, #9: help users recognize, diagnose, and
  recover from errors.
