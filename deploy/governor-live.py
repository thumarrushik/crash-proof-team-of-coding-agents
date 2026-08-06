#!/usr/bin/env python3
"""LIVE governor run — the rules-flags-to-ladder wire, end to end on Temporal.

The team-rules governor was born unit-tested: hooks flag violations, the
activity returns them as typed data, the workflow self-steers and escalates
the model under flag pressure. This script runs the whole wire for real:
dockerized Temporal server, a host worker (which owns the Claude login), and
one task DESIGNED to trip the redundant-`ls` rule — we tell the agent to
"verify with ls after every file", which is exactly the corpus-learned waste
pattern the hooks flag. That's deliberate bait, and the write-up says so: this
measures the governor's plumbing, not the model's natural tendencies.

Ladder config: chunk-count escalation disabled (threshold 99); ONLY flag
pressure can climb. Expected timeline: haiku chunks trip flags -> governor
self-steers a correction -> cumulative flags cross the threshold ->
progress.escalated flips -> the next chunk runs on sonnet (now recorded on
ChunkResult.model).

Prereqs (each codified, see README):
    docker compose up -d temporal temporal-ui temporal-init
    uv run src/worker.py --team backend        # host worker, own terminal

Run:  uv run python deploy/governor-live.py
Evidence: experiment-results-governor/ (timeline.jsonl + result.json)
"""
import asyncio
import json
import pathlib
import time

from temporalio.client import Client

import sys
REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from shared import TEMPORAL_ADDRESS, TaskInput, namespace_for_team, task_queue_for_team  # noqa: E402
from workflows import RunClaudeTask  # noqa: E402

EVID = REPO / "experiment-results-governor"

TASK = (
    "You are in an empty scratch workspace. Create four files, one per step: "
    "alpha.txt, bravo.txt, charlie.txt, delta.txt — each containing exactly its "
    "own name. PROCESS RULE for this task: after creating EACH file, run `ls` "
    "to verify it exists before moving to the next file. Work one file at a "
    "time. When all four exist, finish with the required report."
)


async def main() -> None:
    EVID.mkdir(exist_ok=True)
    threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    team = "backend"
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace_for_team(team))
    workflow_id = f"governor-live-{int(time.time())}"
    handle = await client.start_workflow(
        RunClaudeTask.run,
        TaskInput(
            task=TASK,
            team=team,
            model="haiku",
            escalate_model="sonnet",
            escalate_after_chunks=99,   # chunk-count rung disabled: flags only
            escalate_on_flags=threshold,
            max_turns_per_chunk=4,      # small chunks -> the governor gets turns
            max_chunks=6,
        ),
        id=workflow_id,
        task_queue=task_queue_for_team(team),
    )
    print(f"started {workflow_id} on {namespace_for_team(team)}", flush=True)

    timeline, last = [], None
    with (EVID / "timeline.jsonl").open("w") as tl:
        while True:
            try:
                p = await handle.query("get_progress")
            except Exception:
                await asyncio.sleep(3)
                continue
            snap = {k: p.get(k) for k in ("chunks_completed", "rule_flags_total",
                                          "governor_steers", "escalated", "done",
                                          "total_cost_usd")}
            if snap != last:
                snap["ts"] = time.time()
                tl.write(json.dumps(snap) + "\n")
                tl.flush()
                print(f"  progress: {snap}", flush=True)
                timeline.append(snap)
                last = {k: snap[k] for k in snap if k != "ts"}
            if snap.get("done") or p.get("done"):
                break
            desc = await handle.describe()
            if desc.status and desc.status.name != "RUNNING":
                break
            await asyncio.sleep(3)

    result = await handle.result()
    out = {
        "workflow_id": workflow_id,
        "timeline": timeline,
        "result": {
            "done": result.done,
            "chunks": result.chunks,
            "total_cost_usd": result.total_cost_usd,
            "session_id": result.session_id,
            "work_dir": result.work_dir,
        },
    }
    (EVID / "result.json").write_text(json.dumps(out, indent=2))
    print("RESULT_JSON " + json.dumps(out), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
