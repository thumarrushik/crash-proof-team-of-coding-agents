---
name: self-review
description: Review your own backend diff like the on-call engineer who will be paged for it — hunt broken callers, swallowed error paths, N+1 and unbounded-query edges, untrusted inputs, and missing migration pairing; use before declaring any backend task done.
---

# self-review

Re-read the entire diff cold, top to bottom, as a hostile reviewer. Then run
these backend-specific hunts in order — each targets a bug class a green unit
suite passes right over.

1. **Callers.** For every function, endpoint, or shape whose signature or
   semantics changed: grep every call site — this service, sibling services
   over HTTP, the frontend. Each caller is updated, or the change is
   reclassified as a contract change and put through [[api-contracts]].
2. **Error paths.** Walk each new branch's failure side: every one must land
   in the canonical envelope with a real `code`. Hunt broad excepts/catches
   that swallow, return defaults, or log-and-continue — the silent fallback
   is the house's number-one blocked pattern, and diffs are where it sneaks
   in.
3. **Query and perf edges.** Any query or HTTP call inside a loop (N+1)? Any
   list read without pagination or bound? A new filter predicate with no
   index? Walk the new path at 0 rows, 1 row, and a million rows.
4. **Security inputs.** Every value crossing the boundary — body, path,
   query, header, upload — is validated before use. Every new query is
   tenant-scoped: fetching by bare ID is a cross-tenant read. No
   string-built SQL or shell, no eval, no secrets or tokens in code or logs.
5. **Migration pairing.** Code that reads a new column, table, or seed ships
   with its migration in the same diff — on the rail, idempotent, ordered
   after head, never ad-hoc DDL. Check both deploy orders: old code on the
   new schema, and new code before the migration runs, must both survive.
6. **Leftovers and scope.** Only intended files changed. No debug prints,
   commented-out code, scratch files, or "while I was here" refactors.

Then run the full suite on the final state of the branch and read the output —
counts, failures, and skips (a skip spike is a red flag, not a pass). Record
anything you could not verify in REPORT.md as residual risk.

## Blocked on sight

- Declaring done from a remembered or assumed test run.
- A swallowed exception or silent default anywhere in the diff.
- A new query without tenant scope.
- Schema-touching code whose migration is not in the same diff.

## Grounding

- Secure Code Review Cheat Sheet — cheatsheetseries.owasp.org
- OWASP API Security Top 10 (object-level authz, input validation) — owasp.org
- "What to look for in a code review" — google.github.io/eng-practices
