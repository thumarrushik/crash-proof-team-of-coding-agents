---
name: pr-review
description: How the review team reviews a PR in the multi-team delivery pipeline (service-design → backend → frontend → testing → review → issues) — review as a skeptical maintainer, not a rubber stamp; read the linked issue's intent, inspect the WHOLE diff, VERIFY the required cross-team tests actually ran on this commit and are green (backend PR needs backend + frontend/e2e evidence, frontend PR needs Playwright e2e), check correctness/tests/security/blast-radius, confirm only the intended change is in the diff, then decide approve or block with concrete file:line findings. Use when reviewing any PR or working a team-review job.
---

# pr-review

The review team is the **last gate before merge**. Review as a skeptical maintainer who will be paged
when this breaks: assume nothing, verify everything, and never rubber-stamp. An approval is not a
comment — it is a **decision that triggers a merge**, so grant it only on evidence.

## The steps

Work every review in this order. Don't reorder, don't skip.

1. **Read the linked issue for intent.** What was this PR supposed to do, and for which lane
   (service-design / backend / frontend / testing)? The issue defines scope; anything in the diff
   beyond that scope is a finding. If there is no linked issue or the intent is unclear, that alone
   is a blocking finding.
2. **Inspect the WHOLE diff** — `git diff main...HEAD`, every file, top to bottom. Not the PR
   summary, not the first three files, not the author's description of the change. A reviewer who
   hasn't read the whole diff has no basis for an approval.
3. **VERIFY the required cross-team tests actually ran on this commit and passed.** Don't trust
   "tests pass" in REPORT.md — check the evidence: which suites, which commit, real output. A
   backend PR must show backend unit/integration tests **and** the frontend/e2e suite green against
   the modified backend. A frontend PR must show the Playwright e2e run. Evidence from a stale
   commit, an unnamed suite, or a run with a large skip count (real-infra tests silently skipping is
   a red flag, not a pass) does not count. Missing or unverifiable → block.
4. **Check the four dimensions**, in order:
   - **Correctness** — edge cases (empty, missing, duplicate, concurrent), error handling that fails
     loud with the canonical envelope (no silent skips, no faked/canned results, no error swallowed
     into an empty list), off-by-one and null paths.
   - **Tests** — do they assert *behavior*, not just status 200? Do they cover the failure branches
     (422/404/409/503), not only the happy path? Would they fail if the change were reverted?
   - **Security** — input validation at the boundary, authz/tenant isolation on every new route, no
     secrets in the diff (env only), no injection paths (SQL string-building, `eval`/`exec` on user
     input), identifiers validated before use in queries or paths.
   - **Operational blast radius** — migrations versioned + idempotent (never ad-hoc DDL from request
     code), backward compatibility of API shapes (versioned routes, no field renames under callers),
     performance on hot paths, and a plausible rollback story.
5. **Check the PR contains ONLY the intended change.** No scratch/workspace files, logs, `.env`
   files, debug prints, commented-out code, drive-by refactors, or unrelated formatting churn swept
   into the diff. Every touched file must be explainable by the issue.
6. **Write findings with concrete `file:line` references, blocking items first.** "Error handling is
   weak" is not a finding; "`src/api/orders.py:142` returns 200 with an empty list when the store is
   unreachable — must be a 503 envelope" is. Separate **blocking** from **non-blocking** explicitly.
7. **Decide.** Approve **only if** the change is correct, safe, and the required cross-team test
   evidence is present and green. Anything less → block, with the specific findings that must be
   resolved. "Probably fine" is a block, not an approve.

## Lane-aware focus

- **Backend PR** — contract adherence field-for-field (routes, shapes, status codes), canonical
  error envelope on every failure path, migration safety (versioned, idempotent, via the migrate
  endpoint), integration tests against real infra, and the frontend/e2e evidence from step 3.
- **Frontend PR** — all UI states handled (loading / empty / error / success — errors surfaced, not
  swallowed), accessibility (labels, roles, keyboard paths), and Playwright e2e coverage of the
  changed flows against a live backend.
- **Service-design PR** — is the contract implementable and unambiguous? Every endpoint has request/
  response shapes, status codes, and error-envelope cases defined; no field left for the backend and
  frontend teams to guess differently.

## Definition of done

- [ ] Whole diff read (`git diff main...HEAD`), every file.
- [ ] Cross-team test evidence verified green **on this commit** (backend → backend + frontend/e2e;
      frontend → Playwright e2e) — evidence checked, not claims trusted.
- [ ] All four dimensions checked: correctness, tests, security, operational blast radius.
- [ ] Only-intended-change confirmed — no scratch files or drive-by edits in the diff.
- [ ] Findings written with concrete `file:line` refs, blocking listed first.
- [ ] Decisive verdict (approve / block) recorded in REPORT.md with the reasoning and evidence.
