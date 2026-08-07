#!/usr/bin/env python3
"""Phase gate (Stop hook) — service-design lane.

Studied from the work-issue skill: when a task event arrives, the SAME ordered
phase list is worked every time, no skips. This gate enforces it mechanically:
the run cannot finish until a TodoWrite task list carrying every mandated
phase exists and every phase task is completed. Human-committed in the team
folder; stamped into the workspace before every chunk. The agent never edits it.
"""
import json
import os
import sys

PHASES = ['Understand', 'Blueprint', 'Decide', 'Verify', 'Self-review', 'Report']
LOG = ".claude/hook-log.jsonl"
STATE = ".claude/phase-gate-blocks"
MAX_BLOCKS = 3  # deadlock guard: past this, allow and leave the trail in the log


def _blocks() -> int:
    try:
        return int(open(STATE).read().strip())
    except Exception:
        return 0


def block(reason: str) -> None:
    n = _blocks()
    if n >= MAX_BLOCKS:  # never wedge a run — the audit log still shows the miss
        sys.exit(0)
    with open(STATE, "w") as f:
        f.write(str(n + 1))
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def main() -> None:
    try:
        json.load(sys.stdin)  # hook input; presence is all we need
    except Exception:
        pass
    todo_calls = []
    if os.path.exists(LOG):
        with open(LOG) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("tool_name") == "TodoWrite":
                    todo_calls.append(entry.get("tool_input", {}).get("todos", []))
    order = ", ".join(PHASES)
    if not todo_calls:
        block(
            "This lane works a fixed phase list on every run. Before finishing, "
            f"create the task list with TodoWrite — one task per phase, named for "
            f"the phases, in this order: {order}. Then work them to completed."
        )
    last = todo_calls[-1]
    names = [t.get("content", "").strip().lower() for t in last]
    missing = [p for p in PHASES
               if not any(n.startswith(p.lower()) for n in names)]
    if len(last) < len(PHASES) or missing:
        block(
            f"The task list must carry all {len(PHASES)} phases every run "
            f"({order}). Missing: {', '.join(missing) or 'tasks'}. Update the "
            "TodoWrite list to include every phase, then complete them."
        )
    not_done = [t.get("content", "") for t in last if t.get("status") != "completed"]
    if not_done:
        block(
            "Finish every phase before stopping. Not completed: "
            f"{'; '.join(not_done)}. Work each remaining phase and mark it "
            "completed (or complete it now if the work is already done)."
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
