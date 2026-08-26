# Machine loss, not process loss: the two-filesystem resume

Reproduce: `deploy/machine-loss-live.sh` (starts an ephemeral `temporal server
start-dev` if :7233 is down; bills a small TDD task on `haiku`). **Date:**
2026-08-20. **Result: 7 checks, all passing.**

## The claim being paid

The sticky-queue live run (`experiment-results/affinity-live/`) proved worker
affinity but its two identities shared one filesystem, so the articles carried
an honest edge: true machine loss, the local files gone with the machine, was
"the receipt still owed." This run pays it.

## Method

Two "machines" are two disjoint workspace roots on one box (per-worker
`TMPDIR`, which the harness's workspace derivation honors; the CLI's
transcript store keys projects by workspace path, so each machine's transcript
lives in its own project directory). Auth is shared: a real machine B is
provisioned with its own login, so credentials are not part of the claim.

1. Worker A runs the chunk; the audit hook's `usage-log.jsonl` (a tool-call
   count, agent-behavior-proof) signals mid-work; A's whole process tree is
   SIGKILLed and never restarted.
2. Shared storage is a one-shot staging copy: A's workspace and A's transcript
   project directory are copied out.
3. Machine A's disk is deleted: the workspace root and the transcript project
   directory, both gone before B exists.
4. The staged copies are restored at machine B's paths (the transcript project
   renamed to B's cwd slug, as a shared mount at B's path would present it).
5. Worker B starts. Temporal retries after the two-minute heartbeat timeout.
   The retry reads the session ID from the dead attempt's last heartbeat and
   resumes it against the restored transcript.

## The confirmed run

`done=True chunks=1 cost=$0.0809`, session `43b0d9ae`, workspace on machine B.
`recovery-log.jsonl` on B: `resume_session_from_heartbeat, attempt 2,
input_session_id: null, heartbeat_session_id: 43b0d9ae-…`. Checks: task
completed; completed on B's workspace; A's transcript project gone; recovery
log exists on B; resumed from heartbeat id; input session id null; same
session finished. Evidence copy: `experiment-results/machine-loss/`.

## Three lessons the failed attempts taught

- **Isolated `CLAUDE_CONFIG_DIR` cannot authenticate** (the keychain credential
  is namespaced to the config dir): the first attempt failed on both machines
  with "Not logged in." Auth is machine provisioning, not shared-storage
  payload; the design was corrected to per-machine workspace roots only.
- **Behavior can blind detection**: in the second attempt the agent chose to
  write its files to literal `/tmp` instead of its workspace, the `*.py` poll
  never fired, and attempt 1 completed before the kill. The fix polls the
  harness-owned audit log (`usage-log.jsonl` tool-call count), which records
  every tool call no matter where the agent wanders.
- **A dying orphan can flush one last file**: moments after `rm -rf`, a
  straggler of the killed tree recreated A's workspace path with a single
  `REPORT.md`. B never reads it (the staged copy predates it), and the checks
  assert B's provenance rather than A's emptiness: the same masking effect the
  flagship's caveats describe, observed live one more time.

## What this does and does not prove

Proved: with the workspace and transcript reachable through shared storage
under the same key, heartbeat resume works across machine loss: the surviving
machine needs nothing from the dead one. Not built: the harness still does not
ship the sync itself; the staging copy stands in for the shared mount or
object-store replication a production deployment would run.
