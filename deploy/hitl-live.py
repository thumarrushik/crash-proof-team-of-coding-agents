"""Live human-gate demo against a REAL Temporal server (not the time-skipping
test env). A real in-process worker runs the real RunClaudeTask workflow; the
two leaf activities that would cost tokens or touch GitHub (the agent chunk and
the merge) are stubbed, so the demo isolates the gate mechanics exactly the way
the other chapters isolate a mechanism. Everything else is real: the query
inbox, the validated update, the durable wait + deadline timer, the operator
CLI (src/approvals.py, invoked as a subprocess), and the event history.

Three scenarios, all on the real server:
  A. approve via the CLI            -> merge runs, decision in history
  B. reject via the CLI             -> no merge, decision in history
  C. nobody answers (5s deadline)   -> auto-deny attributed to "deadline", no merge

Run it via deploy/hitl-live.sh (which starts an ephemeral dev server first).
Writes evidence to deploy/hitl-live-results.md.
"""
import asyncio
import logging
import os
import subprocess
import sys
import uuid
from pathlib import Path

logging.basicConfig(level=logging.WARNING,
                    format="%(levelname)s %(name)s: %(message)s")

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from temporalio import activity
from temporalio.api.enums.v1 import EventType
from temporalio.client import Client
from temporalio.worker import Worker

from shared import (
    ApprovalDecision,
    ChunkInput,
    ChunkResult,
    MergeInput,
    MergeResult,
    PostReviewInput,
    PostReviewResult,
    TaskInput,
    TranscriptExportInput,
    TranscriptExportResult,
    TEMPORAL_ADDRESS,
    task_queue_for_team,
)
from workflows import RunClaudeTask

NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
MERGES: list[str] = []


# ---- stub leaf activities (agent + GitHub), identical shape to tests ----
@activity.defn
async def run_claude_chunk(input: ChunkInput) -> ChunkResult:
    return ChunkResult(
        session_id="sid-live", subtype="success", text="done", cost_usd=0.0,
        num_turns=2, work_dir="/tmp/hitl-live",
        structured={"summary": "green suite", "files_created": [], "tests_passed": True},
    )


@activity.defn
async def export_claude_session_transcript(input: TranscriptExportInput) -> TranscriptExportResult:
    return TranscriptExportResult(markdown_path="", source_jsonl_path="", event_count=0)


@activity.defn
async def post_pr_review(input: PostReviewInput) -> PostReviewResult:
    return PostReviewResult(number=input.number, posted=True, event="APPROVE")


@activity.defn
async def merge_pull_request(input: MergeInput) -> MergeResult:
    MERGES.append(f"pr-{input.number}")
    return MergeResult(number=input.number, merged=True, sha="deadbeef")


def _task_input(timeout_h: float) -> TaskInput:
    return TaskInput(
        task="review PR #4", team="review", source="pr-4", pr_number=4,
        repo="o/r", require_approval=True, approval_timeout_h=timeout_h,
        max_chunks=2,
    )


async def cli(*args: str) -> str:
    """Invoke the real operator CLI (src/approvals.py) as a subprocess.

    Run it OFF the event loop: the in-process Worker shares this loop, and a
    blocking subprocess.run would freeze the Worker so it could never process
    the very update the CLI is sending — deadlocking the decision against the
    workflow task that must apply it."""
    proc = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "approvals.py", "--namespace", NAMESPACE, *args],
        cwd=str(SRC), capture_output=True, text=True,
    )
    return (proc.stdout + proc.stderr).strip()


async def _wait_gate(handle) -> dict:
    # Poll gently: aggressive query polling races the workflow task and the
    # decision update against each other on a busy dev server.
    for _ in range(60):
        gate = await handle.query("get_pending_approval")
        if gate:
            await asyncio.sleep(0.5)  # let the workflow task settle before deciding
            return gate
        await asyncio.sleep(0.5)
    raise RuntimeError("gate never opened")


async def _cli_list_until_seen(wid: str) -> str:
    # Visibility (list_workflows) lags a freshly started workflow on the dev
    # server by up to a second or two; retry so the inbox reflects reality.
    out = ""
    for _ in range(10):
        out = await cli("--list")
        if wid in out:
            return out
        await asyncio.sleep(0.6)
    return out


async def _history_summary(handle) -> dict:
    """Real event-history evidence: did a validated update land, and did the
    merge activity run?"""
    names: list[str] = []
    async for ev in handle.fetch_history_events():
        names.append(EventType.Name(ev.event_type))
    return {
        "total_events": len(names),
        "update_accepted": names.count("EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED"),
        "update_completed": names.count("EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_COMPLETED"),
        "activity_completed": names.count("EVENT_TYPE_ACTIVITY_TASK_COMPLETED"),
        "timer_started": names.count("EVENT_TYPE_TIMER_STARTED"),
        "timer_fired": names.count("EVENT_TYPE_TIMER_FIRED"),
    }


# Bounded real deadlines (hours). A/B are long enough that the CLI decision
# always lands first, but bounded so a misconfigured server can never hang 24h.
_LONG_H = 300.0 / 3600.0   # 5 minutes
_SHORT_H = 5.0 / 3600.0    # 5 seconds


def _log(msg: str) -> None:
    print(msg, flush=True)


async def scenario_approve(client) -> dict:
    MERGES.clear()
    wid = f"hitl-approve-{uuid.uuid4().hex[:8]}"
    _log(f"[A] starting {wid} (require_approval, 5-min deadline) ...")
    handle = await client.start_workflow(
        RunClaudeTask.run, _task_input(_LONG_H), id=wid,
        task_queue=task_queue_for_team("review"),
    )
    gate = await _wait_gate(handle)
    _log(f"[A] gate open: {gate}")
    inbox = await _cli_list_until_seen(wid)                      # the real inbox
    _log(f"[A] operator --list -> {inbox!r}")
    reply = await cli("--approve", wid, "--by", "rushik", "--note", "LGTM")  # real decision
    _log(f"[A] operator --approve -> {reply!r}")
    result = await handle.result()
    _log(f"[A] workflow complete; merges={MERGES}")
    progress = await handle.query("get_progress")
    return {
        "name": "A. approve via CLI", "wid": wid, "gate": gate,
        "cli_list": inbox, "cli_reply": reply,
        "merges": list(MERGES), "approval": progress["approval"],
        "history": await _history_summary(handle), "done": result.done,
    }


async def scenario_reject(client) -> dict:
    MERGES.clear()
    wid = f"hitl-reject-{uuid.uuid4().hex[:8]}"
    _log(f"[B] starting {wid} ...")
    handle = await client.start_workflow(
        RunClaudeTask.run, _task_input(_LONG_H), id=wid,
        task_queue=task_queue_for_team("review"),
    )
    await _wait_gate(handle)
    reply = await cli("--reject", wid, "--by", "rushik", "--note", "hold for security review")
    _log(f"[B] operator --reject -> {reply!r}")
    result = await handle.result()
    _log(f"[B] workflow complete; merges={MERGES}")
    progress = await handle.query("get_progress")
    return {
        "name": "B. reject via CLI", "wid": wid, "cli_reply": reply,
        "merges": list(MERGES), "approval": progress["approval"],
        "history": await _history_summary(handle), "done": result.done,
    }


async def scenario_deadline(client) -> dict:
    MERGES.clear()
    wid = f"hitl-deadline-{uuid.uuid4().hex[:8]}"
    _log(f"[C] starting {wid} (5-second real deadline, nobody answers) ...")
    handle = await client.start_workflow(
        RunClaudeTask.run, _task_input(_SHORT_H), id=wid,  # 5-second real deadline
        task_queue=task_queue_for_team("review"),
    )
    result = await handle.result()  # nobody answers; the real timer fires
    _log(f"[C] workflow complete; merges={MERGES}")
    progress = await handle.query("get_progress")
    return {
        "name": "C. nobody answers (5s deadline)", "wid": wid,
        "merges": list(MERGES), "approval": progress["approval"],
        "history": await _history_summary(handle), "done": result.done,
    }


def _fmt(r: dict) -> str:
    a = r.get("approval") or {}
    lines = [f"### {r['name']}", "",
             f"- workflow id: `{r['wid']}`",
             f"- merges performed: `{r['merges']}`",
             f"- decision: approved=`{a.get('approved')}` by=`{a.get('decided_by')}` "
             f"note=`{a.get('note')}`"]
    if r.get("gate"):
        lines.append(f"- gate seen by query: `{r['gate']}`")
    if r.get("cli_list"):
        lines.append(f"- operator `--list` inbox:\n\n```\n{r['cli_list']}\n```")
    if r.get("cli_reply"):
        lines.append(f"- operator decision reply: `{r['cli_reply']}`")
    h = r["history"]
    lines.append(
        f"- event history: {h['total_events']} events — "
        f"update-accepted×{h['update_accepted']}, update-completed×{h['update_completed']}, "
        f"activity-completed×{h['activity_completed']}, "
        f"timer started×{h['timer_started']}/fired×{h['timer_fired']}")
    lines.append("")
    return "\n".join(lines)


async def main() -> int:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=NAMESPACE)
    async with Worker(
        client, task_queue=task_queue_for_team("review"),
        workflows=[RunClaudeTask],
        activities=[run_claude_chunk, export_claude_session_transcript,
                    post_pr_review, merge_pull_request],
    ):
        results = [await scenario_approve(client),
                   await scenario_reject(client),
                   await scenario_deadline(client)]

    # ---- assertions: the gate must behave exactly as claimed ----
    ok = True
    checks = [
        ("A merged exactly PR #4", results[0]["merges"] == ["pr-4"]),
        ("A decider is the human", (results[0]["approval"] or {}).get("decided_by") == "rushik"),
        ("A update entered history", results[0]["history"]["update_accepted"] == 1),
        ("B did not merge", results[1]["merges"] == []),
        ("B decision recorded, not approved", (results[1]["approval"] or {}).get("approved") is False),
        ("B update entered history", results[1]["history"]["update_accepted"] == 1),
        ("C did not merge", results[2]["merges"] == []),
        ("C denied by deadline", (results[2]["approval"] or {}).get("decided_by") == "deadline"),
        ("C recorded NO human update", results[2]["history"]["update_accepted"] == 0),
        ("C timer fired", results[2]["history"]["timer_fired"] == 1),
    ]
    print("\n=== live human-gate demo — real Temporal server ===\n")
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
        ok = ok and passed

    out = Path(__file__).resolve().parent / "hitl-live-results.md"
    out.write_text(
        "# Human Gate — Live Run on a Real Temporal Server\n\n"
        "Reproduce: `deploy/hitl-live.sh` (starts an ephemeral `temporal server "
        "start-dev`, runs `deploy/hitl-live.py`). The RunClaudeTask workflow, the "
        "query inbox, the validated `decide` update, the durable wait + deadline "
        "timer, the operator CLI (`src/approvals.py`), and the event history below "
        "are all real. Four activities are stubbed (the agent chunk, the transcript "
        "export, the review post, and the merge) so the run needs no tokens and no "
        "live repo; the gate machinery itself is untouched.\n\n"
        + "\n".join(_fmt(r) for r in results)
        + "\n## Checks\n\n"
        + "\n".join(f"- {'PASS' if p else 'FAIL'} — {l}" for l, p in checks)
        + f"\n\n**{'ALL PASS' if ok else 'FAILURES PRESENT'}** "
          f"({sum(p for _, p in checks)}/{len(checks)}).\n"
    )
    print(f"\n  evidence -> {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
