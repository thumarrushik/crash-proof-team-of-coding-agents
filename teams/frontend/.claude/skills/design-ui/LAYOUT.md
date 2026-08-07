# LAYOUT.md — inventory the system, then set hierarchy

New UI must look like it was always there. Two moves, in order, before a
single style is written.

## 1. Inventory (never fork a second style)

Find, and commit to reusing:
- the component library (buttons, inputs, cards, modals) — reuse the
  existing component before authoring a new one;
- the design tokens: the color palette, the spacing scale, the type scale
  (sizes and weights). Every value you set comes from these, not from a
  hand-picked pixel;
- a reference page in the same app, as the concrete template for how a
  surface of this kind is built here.

If the repo has a component or token that fits, using it is not optional —
a parallel button styled by hand is a second styling system, and that is
blocked on sight.

## 2. Hierarchy

- **One primary action per view.** Exactly one element carries the primary
  emphasis; everything else is secondary or tertiary. Two primaries is no
  primary.
- **Size, weight, and spacing come from the scale.** Emphasis is built from
  the existing type and spacing steps, never a one-off `font-size: 17px` or
  `margin: 13px`.
- **Group and align.** Related controls sit together; everything aligns to
  the grid the reference page already uses. Proximity and alignment do the
  work that boxes and lines otherwise would.

The test: drop your surface beside the reference page. If a reader can tell
which one is new, the inventory step was skipped.

## Grounding

- Refactoring UI (Wathan & Schoger): hierarchy by weight and color, spacing
  from a scale, one primary action.
- The repo's own component library and tokens are the authority; this file
  is how to find and honor them.
