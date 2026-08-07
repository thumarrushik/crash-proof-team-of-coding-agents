---
name: self-review
description: Review your own backend diff like the on-call engineer who will be paged for it — hunt broken callers, swallowed error paths, N+1 and unbounded-query edges, untrusted inputs, and missing migration pairing; use before declaring any backend task done.
---

# self-review

Re-read the entire diff cold, top to bottom, as a hostile reviewer — the
on-call engineer who will be paged for it. Then run the hunts: each targets
a bug class a green unit suite passes right over.

## How to use this skill

1. Run **[HUNTS.md](HUNTS.md)** every time, in order, on the final diff —
   each hunt comes with grep recipes; run them, don't recall them.
2. Run **[SECURITY-PASS.md](SECURITY-PASS.md)** whenever the diff touches
   boundary input, a query, authz, files, or configuration — in practice,
   nearly every diff; when in doubt, run it.

## Topic map (load on demand)

| Task | File |
|---|---|
| The ordered hunts: callers, error paths, query/perf edges, tenant scope, migration pairing, leftovers — with grep recipes | **[HUNTS.md](HUNTS.md)** |
| OWASP-grounded pass: input validation, injection, authz, secrets | **[SECURITY-PASS.md](SECURITY-PASS.md)** |

## The rules in one breath

1. Every changed signature or shape: grep every caller — this service,
   siblings over HTTP, the frontend — or reclassify via [[api-contracts]].
2. Every new branch's failure side lands in the canonical envelope with a
   real `code`; the silent fallback is the house's number-one blocked
   pattern, and diffs are where it sneaks in.
3. No query or HTTP call in a loop; no unbounded list reads; walk new paths
   at 0 rows, 1 row, and a million rows.
4. Every boundary value validated before use; every new query
   tenant-scoped — a bare-ID fetch is a cross-tenant read; no string-built
   SQL or shell, no eval, no secrets in code or logs.
5. Schema-touching code ships its migration in the same diff, on the rail;
   both deploy orders (old code/new schema, new code/old schema) survive.
6. Only intended files changed; no debug prints, scratch files, or "while I
   was here" refactors.
7. Full suite on the final state, output actually read — a skip spike is a
   red flag, not a pass. Unverified items go to REPORT.md as residual risk.

**Blocked on sight:** declaring done from a remembered or assumed test run ·
a swallowed exception or silent default anywhere in the diff · a new query
without tenant scope · schema-touching code whose migration is not in the
same diff.
