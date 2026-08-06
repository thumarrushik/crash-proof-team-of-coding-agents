---
name: testing-delivery
description: How the testing/QA team works a task in the multi-team delivery pipeline (service-design → backend → frontend → testing → review → issues) — turn the issue's acceptance criteria into a concrete executable cross-layer test matrix (backend API tests with happy + failure paths AND frontend Playwright e2e of the whole user flow against the running backend), run narrow-then-wide, re-run for flake stability, and report the exact command + pass/fail/skip counts for every run with evidence in REPORT.md. Use when working any testing/team-testing issue or acting as a quality gate on another team's deliverable.
---

# testing-delivery

The testing team owns the **full cross-layer proof**. A task is not done when the backend tests pass —
it's done when the backend **and** the integrated frontend flow are both verified green. This team is the
safety net for the seams the other teams can miss: the contract between layers, not just the layers.

## The steps

1. **Turn acceptance criteria into executable checks.** Read the issue + the upstream team's deliverable
   (design doc, PR, REPORT.md). Rewrite each acceptance criterion as a concrete, runnable assertion —
   "user can create a project" becomes a named test with a request/click sequence and an expected result.
   If a criterion can't be made executable, flag it back to the issues team before proceeding.
2. **Backend API tests — happy path AND failure paths.** For every touched endpoint: the success case,
   plus the fail-loud branches (422 bad input / 404 missing / 409 conflict / 503 unavailable dep) asserted
   on status **and** error envelope. Run against real infra (real DB, live containers) where possible;
   skip cleanly with a stated reason if unreachable — never fake the dependency.
3. **Frontend Playwright/browser e2e of the whole user flow against the running backend.** Not component
   stubs — the real UI driving the real API. Cover the end-to-end journey the issue describes (navigate →
   act → verify persisted state), asserting URLs + structured elements, `workers: 1` when specs share one
   live backend.
4. **Run narrow first, then wide.** First the new/changed tests alone (fast signal), then the full suite +
   build gate (`pytest` whole service, `npx playwright test`, `npm run build` / typecheck) — the wide run
   is what catches integration breakage outside the diff.
5. **Re-run for stability.** Repeat the suites (aim 5×, minimum 3×) before declaring green. A test that
   fails once in five runs is a finding, not noise — isolate and report it as a flake; never mask with
   retries or deletions.
6. **Report the EXACT command + result for each run.** Every claim of green is backed by the literal
   command and its counts, e.g. `pytest tests/ -q → 47 passed, 2 skipped` and
   `npx playwright test → 12 passed (1.8m)`. No "tests pass" without the receipt.
7. **Write REPORT.md** with the evidence: matrix covered, commands + counts per run, failure paths
   asserted, flakes found (and their isolation), anything skipped and why. This is the artifact the
   review team gates on.

## The cross-layer matrix

What changed determines what must run — the testing team ensures the whole row is actually run and green:

| Change under test | Must run |
|---|---|
| Backend change (endpoint, service logic, migration) | Backend API tests **+** Playwright e2e of affected flows |
| Frontend change (component, page, routing) | Component/unit tests **+** Playwright e2e against the running backend |
| Contract change (API shape, error envelope, shared types) | **Both** full stacks — backend suite and e2e; this is the seam that breaks silently |

A green backend with an unexercised frontend (or vice versa) does not clear the gate.

## Definition of done

- [ ] Every acceptance criterion mapped to a named, executable check — none left interpretive.
- [ ] Backend API tests green: happy path + failure paths (422/404/409/503) asserted on real infra.
- [ ] Playwright e2e green: the full user flow driven through the real UI against the running backend.
- [ ] The full matrix row(s) for the change type were run — narrow first, then the wide suite + build gate.
- [ ] Suites re-run for stability; flakes isolated and reported, not masked or deleted.
- [ ] Exact command + pass/fail/skip counts reported for every run — no unreceipted "it passes".
- [ ] REPORT.md written with the evidence; skips and known gaps stated with reasons.
