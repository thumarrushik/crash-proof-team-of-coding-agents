---
name: design-ui
description: Design and build user interface surfaces to a consistent, accessible, fail-loud standard — visual hierarchy, a spacing/type scale, explicit loading/empty/error states, responsive layout, and reuse of the repo's existing components and tokens. Use when creating or changing anything a user sees.
---

# design-ui

Design the surface before styling it, reuse before inventing, and make every
state visible. If the repo has an existing component library, design tokens, or
a reference page, those win — extend them, never fork a second style.

## The pass, in order — do not skip

1. **Inventory.** Find the existing components, tokens (colors, spacing, type),
   and a reference page. New UI must look like it was always there.
2. **Hierarchy.** One primary action per view. Size, weight, and spacing follow
   the scale already in use; do not hand-pick one-off values.
3. **States.** Every surface ships all of: loading, empty (with a next step for
   the user), error (fail-loud: show the real message, never a silent blank),
   and success. A UI that hides failure is a broken UI.
4. **Accessibility.** Semantic elements, labeled inputs, keyboard reachable,
   visible focus, contrast that passes; images and icons carry alt text.
5. **Responsive.** Content-first layout that holds at phone width; no
   horizontal scroll for primary content; tap targets comfortably sized.
6. **Verify visibly.** User-visible behavior gets a browser/e2e test (or at
   minimum a rendered check) — markup alone does not prove a UI works.

## Anti-patterns (blocked on sight)

- A second styling system beside the existing one.
- Silent catch-and-continue around fetch/render errors.
- Placeholder screens ("TODO", lorem ipsum) shipped as done.
- Desktop-only layouts.
