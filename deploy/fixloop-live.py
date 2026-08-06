"""Live review-driven fix-loop demo against a REAL Temporal server. Real
RunClaudeTask workflows drive the whole loop; the leaves that would spend
tokens or touch GitHub are stubbed, and the two escalation activities are
stubbed to start the *real* sibling workflow on the same server (minus the
GitHub reads/comments), so the cross-workflow chain is real:

  review r0 (red suite)  --escalate_fix-->  fix job r1  --push + escalate_review-->
  review r1 (green)  --human gate-->  operator approves via approvals.py  -->  merge

Plus a cap scenario: a red review already at max_fix_rounds starts no fix and
awaits a human. Run via deploy/fixloop-live.sh. Evidence -> fixloop-live-results.md
"""
import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from temporalio import activity
from temporalio.api.enums.v1 import EventType
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.worker import Worker

from shared import (
    ChunkInput, ChunkResult, FixEscalationInput, FixEscalationResult,
    HumanReviewState, MergeInput, MergeResult, PostReviewInput, PostReviewResult,
    PushBranchInput, PushBranchResult, ReviewEscalationInput, ReviewEscalationResult,
    TaskInput, TranscriptExportInput, TranscriptExportResult,
    TEMPORAL_ADDRESS, task_queue_for_team,
)
from workflows import RunClaudeTask

NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
TQ = task_queue_for_team("review")   # one queue/worker handles every lane here

MERGES: list[str] = []
STARTED_FIX: list[dict] = []
STARTED_REVIEW: list[dict] = []
PUSHES: list[str] = []
RUN = ""   # per-scenario id prefix, set before starting


def _log(m): print(m, flush=True)


# ---- leaf stubs (agent + GitHub) ----
@activity.defn
async def run_claude_chunk(input: ChunkInput) -> ChunkResult:
    # Red on the initial review, green once a fix has happened. The task text
    # carries the marker (the orchestrator/escalations set it).
    passed = ("expect-green" in input.prompt) or (input.team != "review")
    return ChunkResult(
        session_id="sid", subtype="success", text="done", cost_usd=0.0, num_turns=2,
        work_dir="/tmp/fixloop",
        structured={"summary": "the flag was not renamed", "files_created": [], "tests_passed": passed},
    )


@activity.defn
async def export_claude_session_transcript(input: TranscriptExportInput) -> TranscriptExportResult:
    return TranscriptExportResult(markdown_path="", source_jsonl_path="", event_count=0)


@activity.defn
async def read_pr_review_state(repo: str, pr_number: int) -> HumanReviewState:
    return HumanReviewState()   # no GitHub human review in this demo; the human acts at the gate


@activity.defn
async def post_pr_review(input: PostReviewInput) -> PostReviewResult:
    return PostReviewResult(number=input.number, posted=True, event="COMMENT")


@activity.defn
async def merge_pull_request(input: MergeInput) -> MergeResult:
    MERGES.append(f"pr-{input.number}")
    return MergeResult(number=input.number, merged=True, sha="feed")


@activity.defn
async def push_branch(input: PushBranchInput) -> PushBranchResult:
    PUSHES.append(input.branch)
    return PushBranchResult(pushed=True)


async def _start(client, source, team, task, *, fix_round, require_approval):
    wid = f"{RUN}-{team}-{source}"
    await client.start_workflow(
        RunClaudeTask.run,
        TaskInput(task=task, team=team, source=source, pr_number=4, repo="o/r",
                  branch="claude/issue-1", enable_fix_loop=True, max_fix_rounds=3,
                  fix_round=fix_round, require_approval=require_approval, approval_timeout_h=300.0 / 3600.0),
        id=wid, task_queue=TQ, id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
    )
    return wid


# ---- escalation stubs: real sibling-workflow starts, no GitHub ----
@activity.defn
async def escalate_fix(input: FixEscalationInput) -> FixEscalationResult:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=NAMESPACE)
    source = f"fix-pr-{input.pr_number}-r{input.fix_round}"
    wid = await _start(client, source, "backend",
                       f"Fix PR #{input.pr_number}: {input.feedback}",
                       fix_round=input.fix_round, require_approval=input.require_approval)
    STARTED_FIX.append({"wid": wid, "round": input.fix_round, "feedback": input.feedback})
    _log(f"    escalate_fix -> started {wid} (round {input.fix_round})")
    return FixEscalationResult(started=True, workflow_id=wid, team="backend",
                               fix_round=input.fix_round, message="started")


@activity.defn
async def escalate_review(input: ReviewEscalationInput) -> ReviewEscalationResult:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=NAMESPACE)
    source = f"pr-{input.pr_number}-r{input.fix_round}"
    wid = await _start(client, source, "review",
                       f"Re-review PR #{input.pr_number} after fix round {input.fix_round}. expect-green",
                       fix_round=input.fix_round, require_approval=input.require_approval)
    STARTED_REVIEW.append({"wid": wid, "round": input.fix_round})
    _log(f"    escalate_review -> started {wid} (round {input.fix_round})")
    return ReviewEscalationResult(started=True, workflow_id=wid, fix_round=input.fix_round, message="started")


_ACT = [run_claude_chunk, export_claude_session_transcript, read_pr_review_state,
        post_pr_review, merge_pull_request, push_branch, escalate_fix, escalate_review]


async def cli(*args):
    # Off the event loop: the in-process worker shares it, and a blocking
    # subprocess.run would freeze the worker while the CLI delivers the update.
    proc = await asyncio.to_thread(
        subprocess.run, [sys.executable, "approvals.py", "--namespace", NAMESPACE, *args],
        cwd=str(SRC), capture_output=True, text=True)
    return (proc.stdout + proc.stderr).strip()


async def _await_gate(client, wid):
    handle = client.get_workflow_handle(wid)
    for _ in range(120):
        try:
            if await handle.query("get_pending_approval"):
                await asyncio.sleep(0.5)
                return handle
        except Exception:
            pass
        await asyncio.sleep(0.5)
    raise RuntimeError(f"gate never opened on {wid}")


async def _history_updates(handle):
    n = 0
    async for ev in handle.fetch_history_events():
        if EventType.Name(ev.event_type) == "EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED":
            n += 1
    return n


async def scenario_full_chain(client) -> dict:
    global RUN
    RUN = f"fl-{uuid.uuid4().hex[:6]}"
    MERGES.clear(); STARTED_FIX.clear(); STARTED_REVIEW.clear(); PUSHES.clear()
    _log(f"[chain] {RUN}: starting red initial review ...")
    r0 = await _start(client, "pr-4", "review", "Review PR #4 (initial).",
                      fix_round=0, require_approval=True)
    # The red review escalates a fix; the fix pushes and re-reviews; the re-review
    # (round 1) opens the human gate. Wait for that gate, then approve via the CLI.
    for _ in range(240):
        if STARTED_REVIEW:
            break
        await asyncio.sleep(0.5)
    if not STARTED_REVIEW:
        raise RuntimeError("re-review never started")
    rr = STARTED_REVIEW[-1]["wid"]
    handle = await _await_gate(client, rr)
    _log(f"[chain] gate open on {rr}; operator approves via CLI ...")
    reply = await cli("--approve", rr, "--by", "rushik", "--note", "fix looks good")
    _log(f"[chain] approve -> {reply!r}")
    await handle.result()
    updates = await _history_updates(handle)
    return {"name": "chain: red -> fix -> green -> approve -> merge", "run": RUN,
            "started_fix": list(STARTED_FIX), "pushes": list(PUSHES),
            "started_review": list(STARTED_REVIEW), "merges": list(MERGES),
            "gate_updates": updates, "cli_reply": reply}


async def scenario_cap(client) -> dict:
    global RUN
    RUN = f"cap-{uuid.uuid4().hex[:6]}"
    MERGES.clear(); STARTED_FIX.clear(); STARTED_REVIEW.clear(); PUSHES.clear()
    _log(f"[cap] {RUN}: red review already at round 3 (=max) ...")
    wid = await _start(client, "pr-4", "review", "Review PR #4 (initial).",
                       fix_round=3, require_approval=True)
    await client.get_workflow_handle(wid).result()
    await asyncio.sleep(1.0)   # let any (unexpected) escalation surface
    return {"name": "cap: red at max rounds -> no fix, await human", "run": RUN,
            "started_fix": list(STARTED_FIX), "merges": list(MERGES)}


def _fmt(r):
    out = [f"### {r['name']}", "", f"- run: `{r['run']}`"]
    if "started_fix" in r:
        out.append(f"- fix jobs started: {[f['wid'] for f in r['started_fix']]}")
    if "pushes" in r:
        out.append(f"- fix pushes: `{r['pushes']}`")
    if "started_review" in r:
        out.append(f"- re-review jobs started: {[x['wid'] for x in r['started_review']]}")
    out.append(f"- merges: `{r['merges']}`")
    if "gate_updates" in r:
        out.append(f"- human-gate updates in history: {r['gate_updates']}")
    if "cli_reply" in r:
        out.append(f"- operator reply: `{r['cli_reply']}`")
    return "\n".join(out) + "\n"


async def main() -> int:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=NAMESPACE)
    async with Worker(client, task_queue=TQ, workflows=[RunClaudeTask], activities=_ACT):
        chain = await scenario_full_chain(client)
        cap = await scenario_cap(client)

    checks = [
        ("chain: red suite started exactly one fix (round 1)",
         [f["round"] for f in chain["started_fix"]] == [1]),
        ("chain: the fix pushed the branch", chain["pushes"] == ["claude/issue-1"]),
        ("chain: a re-review (round 1) started", [x["round"] for x in chain["started_review"]] == [1]),
        ("chain: the re-review reached the human gate", chain["gate_updates"] == 1),
        ("chain: operator approval merged PR #4", chain["merges"] == ["pr-4"]),
        ("cap: red at max rounds started NO fix", cap["started_fix"] == []),
        ("cap: nothing merged", cap["merges"] == []),
    ]
    print("\n=== live fix-loop demo — real Temporal server ===\n")
    ok = True
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
        ok = ok and passed

    out = Path(__file__).resolve().parent / "fixloop-live-results.md"
    out.write_text(
        "# Review-Driven Fix Loop — Live Run on a Real Temporal Server\n\n"
        "Reproduce: `deploy/fixloop-live.sh`. Real `RunClaudeTask` workflows drive "
        "the loop on a real `temporal server start-dev`; the agent chunk, the "
        "transcript export, the review post, the merge, the push, and the human-"
        "review read are stubbed, and the two escalation activities are stubbed to "
        "start the *real* sibling workflow (minus GitHub), so the cross-workflow "
        "chain, the human gate, and the operator CLI (`src/approvals.py`) are real.\n\n"
        + _fmt(chain) + "\n" + _fmt(cap)
        + "\n## Checks\n\n"
        + "\n".join(f"- {'PASS' if p else 'FAIL'} — {l}" for l, p in checks)
        + f"\n\n**{'ALL PASS' if ok else 'FAILURES PRESENT'}** "
          f"({sum(p for _, p in checks)}/{len(checks)}).\n"
    )
    print(f"\n  evidence -> {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
