---
name: frontend-delivery
description: How the frontend team works a task in the multi-team delivery pipeline (service-design → backend → frontend → testing → review → issues) — build a UI surface against the service-design contract/API, match the repo's existing design system, wire real data with loading/error/empty/permission states, cover it with component tests, and prove the integrated flow with a Playwright (or the repo's) browser end-to-end suite against the running backend before handing off. Use when working any frontend/team-frontend issue.
---

# frontend-delivery

The frontend team turns a service-design contract into a usable UI surface. The contract is fixed by
the time an issue reaches this team — build to it, don't renegotiate it in component code. A frontend
task is **not done** until the integrated flow works in a real browser against the real backend.

## The steps

1. **Read the issue, the contract, and the room.** Load the issue plus the service-design contract it
   references (endpoints, payload shapes, error envelope, tenancy axes). Then find the repo's existing
   design system — component library, tokens, layout patterns, an adjacent screen to crib from. Match
   what exists; don't import a new UI kit or invent a parallel style for one screen.
2. **Build the smallest usable UI surface.** One route/view that completes the user flow in the issue —
   no speculative tabs, settings, or "while I'm here" screens. List-first for CRUD; overlays from the
   repo's primitives, never hand-rolled.
3. **Wire it to the REAL API.** Same client/proxy pattern the repo already uses; thread every tenancy
   axis the backend scopes by. Handle **loading / error / empty / permission** explicitly — a failed
   fetch is an inline error + retry surfacing the backend's `code`/`message`, never a silently empty
   table; a 403 is a visible denied state, not a blank page. No mocked fetches left in shipped code.
4. **Write component/unit tests.** Render each state (loading, error, empty, populated, denied), assert
   the API client sends the right path + params, and cover the interaction logic (form validation,
   optimistic updates, disabled-until-valid submits) in the repo's test runner.
5. **CROSS-TEAM (mandatory): run a Playwright — or the repo's — browser end-to-end test of the whole
   flow against the running backend.** Start the real stack, drive the browser through the issue's flow
   end to end, and watch data round-trip through the actual API. This is the step that proves frontend
   and backend integrate — component tests passing against mocks proves nothing about the seam. Add or
   extend a spec for this flow; if the suite doesn't exist yet, this issue creates it.
6. **Inspect the changed view in a real browser.** Look for clipping, overlap, controls hidden under
   sticky headers, broken focus/tab order, and an empty console + network panel (no 4xx/5xx, no React
   warnings). A screenshot-worthy view with a red console is not done.
7. **Self-review the diff, write REPORT.md, hand off.** Re-read your own diff for debug logs, dead
   code, and scratch files. REPORT.md states what was built, how it maps to the contract, what the e2e
   proves, and anything the testing/review teams should probe. Then hand off to testing.

## Cross-team testing (do not skip)

- A frontend change ships with **both** component tests **and** a Playwright/browser e2e of the
  integrated flow. One without the other is half-verified.
- The e2e drives the **real** backend — real containers, real DB, real proxy. If a backend route was
  added for this issue, rebuild/restart the backend and `curl` the route before trusting the UI; a
  dev proxy pointed at a stale container will 404 and some flows read that as success.
- Run e2e specs **serial** when they share one backend — concurrent setup/teardown against shared
  state flakes, and a flaky suite gets ignored.
- Assert on **URLs and structured elements** (roles, headings, table cells, badges) — not on log
  output or JSON substrings. If the assertion would survive a copy edit, it's asserting the wrong thing.
- Overlay-hosted form fields aren't in the DOM until opened: the spec clicks the trigger first, fills,
  then closes. Moving a form into a drawer means updating the spec in the same change.

## Definition of done

- [ ] UI matches the repo's existing design system — no one-off styles or new UI kits.
- [ ] Loading / error / empty / permission states all handled and visible; backend errors surfaced verbatim.
- [ ] Component/unit tests green; Playwright (or repo) browser e2e of the integrated flow green against the real backend.
- [ ] Changed view inspected in a browser: no clipping/overlap/broken controls, clean console + network panel.
- [ ] No scratch files, debug logs, or mocked fetches left in the diff.
- [ ] REPORT.md written; issue handed off to the testing team.
