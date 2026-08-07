# Fleet run — 13 issues through the live system (2026-08-06)

One evening, one app repo (`thumarrushik/linkbox`), 13 labeled issues, the
full stack from this repo: dev server, six lane workers, the poller worker,
and the `github-poller` Schedule sweeping every 60 s. No human wrote a line
of app code. This file records what the run taught and what changed because
of it — every fix below landed as a commit the same evening.

## What the run delivered

- Pilot (issue #1): build -> PR #15 -> review APPROVE -> merge, $1.32 total
  ($0.84 build + $0.48 review). The review cited its final suite run with
  command + output tail (verdict-discipline live) and labeled findings
  Conventional-Comments style (pr-review live).
- Fleet: every open issue routed to its lane and built. Snapshot near the
  end: 12 workflow completions, 3 transient failures (all later recovered by
  automatic retry), 8 PRs open with reviews draining, 3 merged + the pilot's.
- The backend pilot agent created EXACTLY its six mandated phases as tasks —
  Understand, Contract, Implement, Test, Self-review, Report — and completed
  every one, unprompted, from the mandate alone.

## Five failures found live, five fixes landed

1. **The poller worker died at startup** — canary.py imported `shared` bare;
   the workflow sandbox re-imported it and tripped on an import-time
   `Path.resolve()`. The schedule fired with no executor. Fix: the same
   `imports_passed_through()` guard workflows.py already used.
2. **The pilot's cleanup trap killed the shared server**, taking 11 running
   workflows down with the in-memory history. Recovery was automatic by
   design (GitHub is the state of record; the next sweep resubmitted all 11,
   including newly-unblocked #2). Fix: pilot borrows a running server without
   owning it; stack server is file-backed; teardown lives only in
   stack-down.sh.
3. **The phase gate spoke the wrong dialect.** Agents build their task list
   with TaskCreate/TaskUpdate, not TodoWrite — the gate blocked runs whose
   task boards were perfect. Gate v2 reads both dialects from the audit log.
4. **One transient failure deadlocked an issue forever.** Three builds failed
   on "structured output after 5 attempts"; REJECT_DUPLICATE then refused
   every retry of those workflow ids. Fix: ALLOW_DUPLICATE_FAILED_ONLY at
   every submit site. All three failures then retried and delivered their
   PRs with no human action — fail, sweep, resubmit, deliver.
5. **Undeclared blockers let an agent invent a feature.** Issue #7 (a bug in
   the not-yet-built export) was worked before its prerequisite existed; the
   agent BUILT the export to have something to fix, racing issue #2's real
   implementation into a merge conflict. Fix: dependencies declared on the
   app repo in the planner's own `Blocked by: #N` syntax, and repro-first
   gained a blocked-on-sight clause for exactly this trap.

## What the conflicts exercised

PRs #18, #20, #21 arrived CONFLICTING (the #7-vs-#2 race plus ordinary
cross-PR drift). That is the review lane's self-heal chain — verdict, merge
attempt, 405, API branch-update, escalate-to-owning-lane — running unattended
on real conflicts. (Outcome tracked in the PR history of the app repo.)

## The meta-lesson

The failures were not noise; they were the product. Every one was caught by
the always-on monitor, diagnosed from the audit trail the hooks write, fixed
in the governance-or-code layer it belonged to, verified by the suite, and
pushed — while the fleet kept running. The system's job is not to avoid
failure; it is to convert failure into a commit.
