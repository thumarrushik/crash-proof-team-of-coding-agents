# Worker affinity, run live — sticky queues under a kill and a restart

`deploy/affinity-live.sh`, 2026-08-18, model `haiku`, real `temporal server
start-dev`, real workers from `src/worker.py`, real agent chunks. One host,
**two worker identities** (`WORKER_ID=pod-A`, `WORKER_ID=pod-B`), affinity on
(`WORKER_AFFINITY=1`). Workflow `claude-testing-task-1787103189`; every check
read from the event history, not from logs. History saved by the runner
(`experiment-results/affinity-live/history.json`, regenerable).

## What happened

1. Both identities listened on the shared lane queue plus their own sticky
   queues. The task was submitted with deliberately tiny 2-turn chunks (cap 6)
   to force many pin-relevant boundaries.
2. **Chunk 1 was scheduled on the shared lane queue**
   (`claude-code-tasks-testing`). `pod-B` happened to take it and reported its
   sticky queue back on the typed result.
3. **All 5 later chunks were scheduled on that one sticky queue**
   (`claude-code-tasks-testing-w-pod-B`) — a single pin, never drifting.
4. **The pinned identity was SIGKILLed** (whole process tree) the moment the
   pin appeared in history. For a 45-second dead window only `pod-A` was
   alive. **Pinned activities started by the survivor: 0.** The pinned work
   waited; the wrong worker structurally could not steal it.
5. **A new process with `WORKER_ID=pod-B` was started.** The stable identity
   put it back on the same sticky queue; the workflow resumed and ran to
   completion as the **same session** (`b6d8050c-…`) across the kill.

## Verdict (from the event history)

| Check | Result |
|---|---|
| Chunk 1 on the shared lane queue | PASS |
| Later chunks pinned to exactly one sticky queue | PASS (5/5 on `…-w-pod-B`) |
| Survivor stole pinned work during the dead window | 0 (PASS) |
| Restarted same-ID process resumed and completed the workflow | PASS |
| Session continuity across the kill | same session ID throughout |

Total agent cost $0.1663 across 6 chunks.

## Two honest notes

- **The task itself hit its 6-chunk cap without finishing** (`done=False`,
  cleanly returned): the 2-turn cap sent the agent wandering, at $0.17 against
  the ~$0.11 continuous baseline — an accidental live re-confirmation of the
  family's fine-chunking law ("the mechanics cost cents; the behavior costs
  dollars"). Irrelevant to the affinity claims, which are about scheduling,
  identity, and resume; all held. Because the run did not reach success, the
  transcript-export pin was not exercised live here; it is covered by the
  offline routing test (`tests/test_worker_affinity.py`).
- **One host, one filesystem.** This run proves the routing guarantee live —
  pin, no-steal, restart-resume — but both identities shared a disk, so it
  cannot prove cross-machine file invisibility. The remaining receipt is the
  same run with the two identities on two machines (or the shared-storage
  variant); until then, permanent machine loss remains the stated gap.

Reproduce: `./deploy/affinity-live.sh` (needs `temporal`, `uv`, a logged-in
`claude`; bills a few cents; exits nonzero on any failed check).
