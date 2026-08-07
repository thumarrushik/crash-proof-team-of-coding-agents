# Autonomous merge-conflict resolution — the live run's receipt

Transcribed from the lab repository's live-run table
(`temporal-claude-demo/README.md`, run of 2026-07-14 on `snippets-service`,
GCP-hosted Temporal); the original artifacts (event histories, session
transcripts) live in that repository. This file exists so the flagship's
centerpiece claim has a named receipt in the shipping repo.

## What ran

Two backend PRs edited the same regions of `backend/app.py` plus the API
contract — one added search, one added `DELETE /api/snippets/{id}`. The
search PR merged first, so the delete PR (#4) went `CONFLICTING`/`DIRTY`.

The chain, with no human input:

1. Review approved PR #4 → merge attempt returned HTTP 405.
2. Base-merge hit a real content conflict (not a stale branch).
3. `escalate_conflict` read the issue's `team/backend` label and started
   `claude-backend-resolve-pr-4` in the backend namespace (deterministic
   ID, duplicate-safe).
4. The backend agent merged `main`, kept both features, and the suite went
   green on the merged tree — **10/10, independently re-run**.
5. The harness pushed the resolved branch and re-merged:
   *"Merge PR #4 (conflict auto-resolved)."*
6. Issue #1 auto-closed; the frontend issue (`Blocked by: #1`) unblocked
   and shipped a delete button plus a Playwright create+delete test
   (PR #6, merged).

## The asterisk, stated plainly

**Staged, disclosed:** PR #4 predated the escalation feature, so its review
was re-triggered against the new code, and the polls were hand-kicked
instead of waiting on the schedule. The resolution chain itself — detect →
escalate → resolve → test → push → re-merge → downstream unblock — ran with
no human decision in it.

A later fleet run reproduced the chain end-to-end on scheduled polls with
no hand-kicks, across three simultaneous real conflicts
(`deploy/fleet-run-results.md`).
