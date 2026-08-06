# Failure → heartbeat → resume — measured

Fresh run of `deploy/heartbeat-recovery.sh`. Date: 2026-07-15. Agent model:
`haiku`. Lane: `testing` (isolated). The claim: a mid-chunk worker crash resumes
the *same* Claude session from the id carried in Temporal heartbeat details — no
completed checkpoint required, and far cheaper than re-running from zero.

## What ran

1. A worker picks up one long chunk (a `mathkit` TDD task, 40-turn budget).
2. The moment the agent starts writing files (session live and heartbeated), a
   short flush margin, then the worker's **whole process tree** is `SIGKILL`ed —
   before any completed chunk result exists.
3. A restarted worker is polling. After the heartbeat timeout, Temporal retries
   the activity; **attempt 2** reads the session id out of the previous attempt's
   heartbeat details and relaunches Claude with `--resume`.

## Evidence (recovery-log.jsonl, attempt 2)

```json
{"event": "resume_session_from_heartbeat", "attempt": 2, "activity_id": "1",
 "input_session_id": null,
 "heartbeat_session_id": "698c432a-b6b5-4d0a-b636-4e385f8caf80"}
```

- `input_session_id: null` — the workflow had **no** completed-chunk session id to
  hand back; the id came *only* from heartbeat details.
- The workflow's final `session_id` equals the `heartbeat_session_id` — the **same**
  session was resumed, not a fresh one.
- Completed as **1 chunk, $0.0404** — a cheap resume (prefix re-read + the
  remaining work), not a re-run of the whole task.

## Three engineering details this surfaced (all real)

Reproducing this cleanly required fixing three things — each a genuine caveat:

1. **Heartbeat throttle.** Temporal throttles how often heartbeat *details* are
   persisted. With a 2-minute heartbeat timeout the default effective throttle is
   ~60s — too coarse to record the in-flight session id before a short crash.
   The worker now sets it via `HEARTBEAT_THROTTLE_SECONDS` (default 15s; the demo
   uses 3s). See `src/worker.py`.
2. **Process-group kill.** `kill -9` on the worker alone orphans the Claude child,
   which finishes the chunk and *masks* the recovery (attempt 2 finds the work
   already done). Killing the whole process tree is required to actually test
   recovery — and is why production workers belong in a process group/container.
3. **Timing.** The crash must land while the chunk is genuinely in flight; the
   demo waits for the agent's first file write rather than guessing a wall-clock.

## Reproduce

```bash
docker compose up -d
HEARTBEAT_THROTTLE_SECONDS=3 FLUSH_MARGIN=6 MODEL=haiku TEAM=testing \
  ./deploy/heartbeat-recovery.sh
# → recovery-log.jsonl with event=resume_session_from_heartbeat on attempt 2
```
