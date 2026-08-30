# Kill only the child → same heartbeat resume, faster — measured

Fresh run of `deploy/child-kill-recovery.sh`. Date: 2026-08-30. Agent model:
`haiku`. Lane: `testing` (isolated). Companion contrast to
`heartbeat-recovery.sh`, which kills the worker's **whole** process tree. Here
we kill **only the Claude child** and leave the worker alive.

The question: when the agent subprocess dies but its worker does not, does the
run recover, and where does the resumed session id come from? A tempting answer
is "the worker is alive, so it recovers from memory, ordinary error handling."
This run shows that answer is **wrong**.

## What ran

1. A worker (`uv run src/worker.py`, pid 14802 → python 14804) picks up one
   `mathkit` TDD chunk (40-turn budget). The Claude CLI runs as a grandchild
   (pid 14846).
2. The moment the agent starts writing files (session live and heartbeated), an
   8s flush margin, then **only pid 14846 (the Claude child) is `SIGKILL`ed**.
   The worker (14802/14804) is left running and is never restarted.

## Result

- **The worker survived**: pid 14802 unchanged, never restarted.
- **The SDK saw the CLI die immediately** and failed the activity, from
  `worker.log`:
  ```
  ERROR:claude_agent_sdk._internal.query:Fatal error in message reader:
    Command failed with exit code -9
  WARNING:temporalio.activity:Completing activity as failed (... attempt 1 ...)
  ```
- **Attempt 2 resumed from the heartbeat**, from `recovery-log.jsonl`:
  ```json
  {"event": "resume_session_from_heartbeat", "attempt": 2, "activity_id": "1",
   "input_session_id": null,
   "heartbeat_session_id": "50e526b8-3ba9-4a2e-9e99-6ddff27bccf1"}
  ```
  `input_session_id: null` (no completed chunk to fall back on) and the
  workflow's final `session_id` equals the `heartbeat_session_id`: the **same**
  session finished, resumed from heartbeat details.
- **Fast, not slow.** The recovery-log appeared **5s** after the kill (the
  retry policy's 5s initial backoff), not after the ~2-minute heartbeat timeout.
  The task completed as **1 chunk, $0.1362**, 76s after the kill.

## The finding

Killing the child is **not** a weaker or different recovery. It is the **same**
resume-from-heartbeat path as a worker crash, and it comes from the same place:
the session id lives in Temporal **heartbeat details on the server**, not in the
worker's memory. Mid-chunk, that id was never returned to the workflow, so even
a live worker's retry must read it back from the heartbeat. The recovery-log is
byte-for-byte the same shape as the worker-kill run's (`input_session_id: null`,
`attempt 2`).

The only two differences from a whole-worker crash:

| | Kill the **whole worker tree** | Kill **only the child** |
|---|---|---|
| What detects the failure | heartbeat timeout (server-side) | the activity raises (SDK sees the dead CLI) |
| Time to retry | ~2 minutes | ~5 seconds (retry backoff) |
| Worker + sibling jobs | die too, all recover | untouched |
| Where the session id comes from | heartbeat details | heartbeat details (same) |
| Recovery-log | `resume_session_from_heartbeat`, null input | identical |

So a dead agent subprocess is caught **faster** than a dead worker (a raised
error beats a liveness timeout), and it disturbs nothing else on the box. But it
is the same mechanism underneath.

## Caveats (all real)

- **The alternative outcome did not happen.** If the SDK had *hung* instead of
  raising, the dumb 30s timer heartbeat would have kept reporting "alive," the
  2-minute heartbeat timeout would never fire, and only the 15-minute chunk
  ceiling would catch it. It did not: the SDK surfaced the dead CLI on the spot
  (`exit code -9`). Worth re-checking if the SDK's process handling changes.
- **Timing still matters**, same as the worker-kill: the session id must already
  be persisted in heartbeat details when the kill lands (throttle 3s + 8s flush
  margin here). Kill before that and attempt 2 finds `input_session_id: null`
  with no heartbeat id either, and starts a fresh session (a re-run, never
  wedged).
- **Sibling-safety is inferred, not separately demonstrated here.** This run had
  one job. That the worker process survived means any *other* activity in that
  same worker would keep running; a concurrent-sibling run was not part of this
  measurement.

## Reproduce

```bash
# needs a logged-in `claude` CLI; starts its own ephemeral Temporal dev server
HEARTBEAT_THROTTLE_SECONDS=3 FLUSH_MARGIN=8 MODEL=haiku TEAM=testing \
  ./deploy/child-kill-recovery.sh
# → recovery-log.jsonl: resume_session_from_heartbeat, attempt 2, ~5s after the kill,
#   worker pid unchanged
```
