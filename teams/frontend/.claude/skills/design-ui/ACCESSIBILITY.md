# ACCESSIBILITY.md — WCAG 2.2 AA, with the numbers

Accessibility is a build requirement, not a polish pass. The success
criteria below are the AA bar; each carries its SC number so a reviewer can
check it.

## Semantics first

- **Semantic HTML before ARIA.** A `<button>` is a button; a `<div
  onclick>` is a bug that assistive tech cannot see. The First Rule of ARIA:
  do not use ARIA if a native element with the semantics you need exists.
- **ARIA only to fill real gaps** — a custom widget with no native
  equivalent — and then following the ARIA Authoring Practices Guide (APG)
  pattern for that widget exactly.

## Keyboard and focus

- Every action is reachable by keyboard, in a logical tab order.
- Every input has a programmatic label (`<label for>` or `aria-label`).
- **Focus is visible (SC 2.4.7) and not obscured (SC 2.4.11).** If you
  restyle the focus outline, the replacement is at least as visible as the
  default — removing it outright is blocked on sight.

## Contrast, targets, color

- **Contrast (SC 1.4.3, 1.4.11):** >=4.5:1 for body text; >=3:1 for large
  text, UI component boundaries, and meaningful graphics.
- **Target size (SC 2.5.8):** pointer targets >=24x24 CSS px; prefer 44px
  for primary touch actions.
- **Never color alone (SC 1.4.1):** state conveyed by color also carries an
  icon, text, or shape; images and icons carry text alternatives.

## The pass

Run this list against every new or changed element before declaring the
surface done. If `getByRole` (from [[browser-e2e]]) cannot find an element
by its accessible name, that is an accessibility defect in the markup —
fix the markup, not the test.

## Grounding

- WCAG 2.2 (W3C Recommendation, 2023): SC 1.4.1, 1.4.3, 1.4.10, 1.4.11,
  2.4.7, 2.4.11, 2.5.8.
- W3C "Using ARIA" (First Rule of ARIA); the ARIA Authoring Practices Guide.
