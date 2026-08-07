#!/usr/bin/env python3
"""Phase gate (Stop hook) — backend lane.

Studied from the work-issue skill: when a task event arrives, the SAME ordered
phase list is worked every time, no skips. This gate enforces it mechanically:
the run cannot finish until a task list carrying every mandated phase exists
and every phase task is completed. Speaks both task dialects — TodoWrite
(todos array) and TaskCreate/TaskUpdate (id-addressed tasks) — because live
runs showed agents using either. Human-committed in the team folder; stamped
into the workspace before every chunk. The agent never edits it.
"""
import json
import os
import sys

PHASES = ['Understand', 'Contract', 'Implement', 'Test', 'Self-review', 'Report']
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


def _collect():
    """Return (todo_lists, tasks) from the audit log: every TodoWrite call's
    todos, and an id->(name, completed) map built from TaskCreate/TaskUpdate."""
    todo_calls, tasks, saw_report = [], {}, False
    if not os.path.exists(LOG):
        return todo_calls, tasks, saw_report
    with open(LOG) as f:
        for line in f:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            tool = entry.get("tool_name")
            args = entry.get("tool_input", {}) or {}
            if tool == "TodoWrite":
                todo_calls.append(args.get("todos", []))
            elif tool == "TaskCreate":
                resp = entry.get("tool_response") or {}
                task = resp.get("task") if isinstance(resp, dict) else None
                tid = str((task or {}).get("id", "")) or str(len(tasks) + 1)
                tasks[tid] = {"name": args.get("subject", ""), "done": False}
            elif tool == "StructuredOutput":
                saw_report = True
            elif tool == "TaskUpdate":
                tid = str(args.get("taskId", ""))
                if tid in tasks and args.get("status"):
                    tasks[tid]["done"] = args["status"] == "completed"
    return todo_calls, tasks, saw_report


def main() -> None:
    try:
        json.load(sys.stdin)  # hook input; presence is all we need
    except Exception:
        pass
    todo_calls, tasks, saw_report = _collect()
    order = ", ".join(PHASES)
    if todo_calls:  # TodoWrite dialect: judge the latest full list
        last = todo_calls[-1]
        names = [t.get("content", "").strip().lower() for t in last]
        done = [t.get("content", "") for t in last if t.get("status") == "completed"]
        not_done = [t.get("content", "") for t in last if t.get("status") != "completed"]
    elif tasks:  # TaskCreate/TaskUpdate dialect: judge the task board
        names = [t["name"].strip().lower() for t in tasks.values()]
        done = [t["name"] for t in tasks.values() if t["done"]]
        not_done = [t["name"] for t in tasks.values() if not t["done"]]
    else:
        block(
            "This lane works a fixed phase list on every run. Before finishing, "
            f"create the task list — one task per phase, named for the phases, "
            f"in this order: {order}. Then work them to completed."
        )
        return
    missing = [p for p in PHASES
               if not any(n.startswith(p.lower()) for n in names)]
    if missing:
        block(
            f"The task list must carry all {len(PHASES)} phases every run "
            f"({order}). Missing: {', '.join(missing)}. Add the missing phase "
            "tasks, then complete them."
        )
    phase_not_done = [n for n in not_done
                      if any(n.strip().lower().startswith(p.lower()) for p in PHASES)]
    if saw_report:  # the returned structured report IS the Report phase's completion
        phase_not_done = [n for n in phase_not_done
                         if not n.strip().lower().startswith("report")]
    if phase_not_done:
        block(
            "Finish every phase before stopping. Not completed: "
            f"{'; '.join(phase_not_done)}. Work each remaining phase and mark "
            "it completed (or complete it now if the work is already done)."
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
