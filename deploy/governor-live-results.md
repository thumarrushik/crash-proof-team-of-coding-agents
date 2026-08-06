# Governor live run — the flags-to-ladder wire, end to end on Temporal

**Runner:** `deploy/governor-live.py` (Temporal dev server via `temporal server
start-dev`, host worker `src/worker.py --team backend`, real `RunClaudeTask`).
**Evidence:** `experiment-results-governor/` (per-run timeline JSONL, result
JSON, and activity-input model extraction from `temporal workflow show`).
**Date:** 2026-07-29.

## What was tested

The team-rules governor had only ever been unit-tested. This runs the whole
wire live: a PostToolUse hook flags rule violations into the workspace → the
activity tallies them into typed `ChunkResult.rule_flags` → the workflow
self-steers a correction into the next chunk and, under flag pressure
(`escalate_on_flags`), climbs the model ladder — same session, stronger model.

**Deliberate bait, disclosed:** the task instructs the agent to run `ls` after
every file it creates — exactly the corpus-learned redundant-orientation
pattern the default rule flags. This measures the governor's *plumbing*, not
the model's natural tendencies. Chunk-count escalation was disabled
(threshold 99) so only flag pressure could climb.

## Run 1 — threshold 2 (`run1-threshold2.*`)

| After chunk | Model | Flags total | Steers | Escalated |
|---|---|---|---|---|
| 1 | haiku | 1 | 1 | no |
| 2 | haiku | 1 | 1 | no |
| 3 | haiku | 2 | 1 | **yes** (task finished same chunk) |

The detail worth noticing: **chunk 2 produced zero new flags** — the
governor's corrective steer visibly changed the agent's behavior mid-run
(it stopped ls-verifying after being told once). The flag that crossed the
threshold came on the final chunk, so the ladder armed but the run ended
before a stronger-model chunk was needed. Total $0.0798.

## Run 2 — threshold 1 (`run2-threshold1.*`)

| Chunk | Model (from workflow history) | Resumed session |
|---|---|---|
| 1 | haiku | (fresh) |
| 2 | **sonnet** | `6a01eed8…` |
| 3 | **sonnet** | `6a01eed8…` |

Chunk 1 tripped the rule twice → steer + escalate in one shot; chunks 2–3 ran
on sonnet **resuming the same session** — the mid-conversation brain
transplant, triggered by enforced-hook evidence rather than a human or a
timer, recorded per-chunk in the durable history (`ChunkInput.model` in the
activity inputs; also now returned on `ChunkResult.model`). Cost timeline
shows the rate change: $0.022 after the haiku chunk, $0.266 after the first
sonnet chunk, $0.316 total.

## Conclusions

1. The full wire works live: hook → flag log → typed chunk result → governor
   steer → prompt injection → behavior change → flag pressure → ladder climb
   → stronger model inherits the conversation.
2. The self-steer alone measurably corrected behavior (run 1, chunk 2 clean)
   — before any escalation was needed.
3. Governor state (`rule_flags_total`, `governor_steers`, `escalated`) was
   queryable live throughout, and the model per chunk is auditable from the
   event history afterwards.

## Caveats

- n=2 runs, bait task, tiny workloads: this validates mechanism, not
  effect sizes.
- Escalation cost is visible and real (run 2 cost 4× run 1) — flag-pressure
  thresholds are a budget decision, not just a quality one.
