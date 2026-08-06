---
name: frontend-ui
description: UI delivery discipline for frontend tasks. Use whenever building or changing user-facing screens, components, flows, or browser behavior.
---

Build usable UI, not a description of UI. Match the repo's design system first.
Keep screens dense enough for repeated work, responsive, and verified in a
browser. Before declaring done, run the available frontend checks and inspect
the changed view for layout clipping, overlapping text, broken controls, and
missing loading/error/empty states.

Watch the hard-won gotchas: a checkbox wrapped in its own `<label>`
double-toggles; a `position: sticky` header can intercept clicks; calling a
state-setter during render causes churn; dispatch a real `click` event after a
toggle so browser automation registers it.
