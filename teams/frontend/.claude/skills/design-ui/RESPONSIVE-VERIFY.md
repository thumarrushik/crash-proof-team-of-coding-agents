# RESPONSIVE-VERIFY.md — reflow to 320px, then prove it

## Responsive

- **Content-first layout that reflows to 320px width** with no horizontal
  scrolling and no loss of function (SC 1.4.10). A user at phone width can
  reach and use everything a desktop user can.
- **Relative units** (rem, %, fr, ch) over fixed pixels, so the layout
  responds to viewport and user zoom rather than fighting them.
- **Verify at phone width, not just desktop.** The desktop view passing is
  not evidence the phone view works; open the narrow breakpoint and check.

## Verify rendered — markup is a claim, not proof

A component that compiles is not a component that works. User-visible
behavior gets:
- a **browser test** ([[browser-e2e]]) driving the real surface — the
  strongest evidence; or, when no browser runner exists in the workspace,
- at minimum a **rendered assertion** (render the component, assert the
  user sees what you claim) — and say in the report that a browser test was
  not available.

This closes the loop the four render states opened: each state is not
"designed" until something renders it and asserts on it.

## Grounding

- WCAG 2.2 SC 1.4.10 Reflow (320px, no loss of function).
- The verify bar is shared with [[browser-e2e]] (role-first locators,
  web-first assertions) and [[tdd]] (behavior over markup).
