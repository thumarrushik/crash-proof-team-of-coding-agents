---
name: backend-delivery
description: How the backend team works a task in the multi-team delivery pipeline (service-design → backend → frontend → testing → review → issues) — implement a service/API from an issue or a service-design contract, test-first (failing test before code), smallest change that satisfies the contract, then prove the change doesn't break the frontend by running the frontend build/tests and the e2e suite against your live backend before handing off with a REPORT.md. Use when working any backend or team-backend issue.
---

# backend-delivery

The backend team owns the API/service layer against the contract the service-design team published.
The contract is the spec; the issue is the scope. A backend change is **not done** when the backend
tests pass — it is done when it **proves the frontend still works against it**.

## The steps

Work every backend issue in this order. Don't reorder, don't skip.

1. **Read the issue and the service-design contract.** The issue defines scope; the contract
   (endpoints, request/response shapes, error envelope, status codes) defines correctness. If they
   conflict, or the contract is missing/ambiguous, stop and flag it back to service-design via an
   issue — don't invent a contract.
2. **TDD — write the failing test first.** Encode the contract behavior (happy path + the fail-loud
   branches: 4xx validation, 404, 409, 503) as a test, run it, watch it fail for the right reason.
   No production code before a red test.
3. **Implement the smallest change that satisfies the contract.** No drive-by refactors, no
   speculative parameters, no extra endpoints "while you're in there". Touch only the files the
   issue requires.
4. **Run the backend unit + integration tests.** The whole suite, not just your new test — against
   real infra where the repo supports it. All green before moving on.
5. **CROSS-TEAM: run the frontend + end-to-end tests too.** A backend/API change must not break the
   UI. If the repo has a frontend, run its build and its tests, then run the e2e/Playwright suite
   against your **running** backend (start it; don't test against a stale build). This step is the
   point of the pipeline — see the section below.
6. **Verify the contract and error envelope are honored.** Exercise the real HTTP surface (curl or
   the integration tests) and confirm: routes/versioning match the contract, response shapes match
   field-for-field, and error responses use the canonical envelope with the contracted status codes.
7. **Self-review the diff, write REPORT.md, hand off.** `git diff` the branch: only intended files,
   no debug prints, no scratch/temp files, no commented-out code. Write REPORT.md (what changed,
   why, test evidence including the cross-team runs, any risks). The harness opens the PR — your
   job ends at a clean branch plus the report.

## Cross-team testing (do not skip)

- **Backend change → backend tests AND frontend/e2e tests must be green.** Both. A green backend
  suite with an unexercised frontend is an unverified change, not a done one.
- Run the e2e suite against **your** modified backend, live — that's the only run that can catch a
  contract break the unit tests can't see.
- **If you cannot run the frontend or e2e suite** (missing toolchain, no browser, suite broken
  before your change), say so **explicitly** in REPORT.md: what you couldn't run, why, and what
  integration risk that leaves for the testing team. Silently skipping is the one failure mode this
  pipeline exists to prevent.
- If the frontend/e2e tests fail because of your change, that's your bug — fix the backend (or
  escalate a contract problem to service-design). Never "fix" the frontend tests to accept a
  contract break; the frontend team owns that code.

## Definition of done

- [ ] Contract honored: routes, shapes, status codes, and error envelope match service-design.
- [ ] Failing test was written first; it now passes for the contracted reason.
- [ ] Backend unit + integration tests green (full suite, real infra where supported).
- [ ] Frontend build/tests + e2e suite green against the running backend — **or** the gap and its
      integration risk are explicitly flagged in REPORT.md.
- [ ] Diff contains only intended files; no scratch files, debug output, or drive-by changes.
- [ ] REPORT.md written: what/why, test evidence (including cross-team runs), risks. Branch clean
      for the harness to open the PR.
