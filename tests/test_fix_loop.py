"""Workflow-level tests for the review-driven fix loop, on Temporal's
time-skipping test server: a real RunClaudeTask runs against stub activities
and we assert what it hands off. The gate itself is covered by
test_human_gate.py; here we cover the loop *around* it — red suite or human
"Request Changes" starts a fix, a fix job re-reviews, and the cap holds.
"""
import asyncio
import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from shared import (
    ApprovalDecision,
    ChunkInput,
    ChunkResult,
    FixEscalationInput,
    FixEscalationResult,
    HumanReviewState,
    MergeInput,
    MergeResult,
    PostReviewInput,
    PostReviewResult,
    PushBranchInput,
    PushBranchResult,
    ReviewEscalationInput,
    ReviewEscalationResult,
    TaskInput,
    TranscriptExportInput,
    TranscriptExportResult,
)
from workflows import RunClaudeTask

# --- observable side effects the stubs record ---
MERGES: list[str] = []
STARTED_FIX: list[FixEscalationInput] = []
STARTED_REVIEW: list[ReviewEscalationInput] = []
PUSHES: list[str] = []
REVIEWS_POSTED: list[PostReviewInput] = []

# --- scenario knobs the stubs read ---
TESTS_PASSED = True
HUMAN_STATE = HumanReviewState()


@activity.defn
async def run_claude_chunk(input: ChunkInput) -> ChunkResult:
    return ChunkResult(
        session_id="sid-fix", subtype="success", text="done", cost_usd=0.01,
        num_turns=2, work_dir="/tmp/fix-test",
        structured={"summary": "did the work", "files_created": [], "tests_passed": TESTS_PASSED},
    )


@activity.defn
async def export_claude_session_transcript(input: TranscriptExportInput) -> TranscriptExportResult:
    return TranscriptExportResult(markdown_path="", source_jsonl_path="", event_count=0)


@activity.defn
async def read_pr_review_state(repo: str, pr_number: int) -> HumanReviewState:
    return HUMAN_STATE


@activity.defn
async def post_pr_review(input: PostReviewInput) -> PostReviewResult:
    REVIEWS_POSTED.append(input)
    return PostReviewResult(number=input.number, posted=True, event="COMMENT")


@activity.defn
async def merge_pull_request(input: MergeInput) -> MergeResult:
    MERGES.append(f"pr-{input.number}")
    return MergeResult(number=input.number, merged=True, sha="abc")


@activity.defn
async def push_branch(input: PushBranchInput) -> PushBranchResult:
    PUSHES.append(input.branch)
    return PushBranchResult(pushed=True)


@activity.defn
async def escalate_fix(input: FixEscalationInput) -> FixEscalationResult:
    STARTED_FIX.append(input)
    return FixEscalationResult(started=True, workflow_id=f"claude-x-fix-pr-{input.pr_number}-r{input.fix_round}",
                               team="backend", fix_round=input.fix_round, message="stub")


@activity.defn
async def escalate_review(input: ReviewEscalationInput) -> ReviewEscalationResult:
    STARTED_REVIEW.append(input)
    return ReviewEscalationResult(started=True, workflow_id=f"claude-review-pr-{input.pr_number}-r{input.fix_round}",
                                  fix_round=input.fix_round, message="stub")


_ACTIVITIES = [run_claude_chunk, export_claude_session_transcript, read_pr_review_state,
               post_pr_review, merge_pull_request, push_branch, escalate_fix, escalate_review]


def _review_input(*, tests_passed=True, human=None, fix_round=0, max_rounds=3,
                  require_approval=False, source="pr-4", team="review") -> TaskInput:
    global TESTS_PASSED, HUMAN_STATE
    TESTS_PASSED = tests_passed
    HUMAN_STATE = human or HumanReviewState()
    return TaskInput(
        task="review PR #4", team=team, source=source, pr_number=4, repo="o/r",
        branch="claude/issue-1", enable_fix_loop=True, max_fix_rounds=max_rounds,
        fix_round=fix_round, require_approval=require_approval, approval_timeout_h=24.0,
        max_chunks=2,
    )


async def _run_env(scenario) -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        tq = f"fix-test-{uuid.uuid4()}"
        async with Worker(env.client, task_queue=tq, workflows=[RunClaudeTask],
                          activities=_ACTIVITIES):
            await scenario(env, tq)


class FixLoopTest(unittest.TestCase):
    def setUp(self):
        MERGES.clear(); STARTED_FIX.clear(); STARTED_REVIEW.clear()
        PUSHES.clear(); REVIEWS_POSTED.clear()

    def _run(self, task_input, drive=None):
        async def scenario(env, tq):
            handle = await env.client.start_workflow(
                RunClaudeTask.run, task_input,
                id=f"fix-{uuid.uuid4()}", task_queue=tq,
            )
            if drive is not None:
                await drive(handle)
            await handle.result()
        asyncio.run(_run_env(scenario))

    # --- red suite / human changes start a fix ---
    def test_red_suite_starts_fix(self):
        self._run(_review_input(tests_passed=False, fix_round=0))
        self.assertEqual(MERGES, [])
        self.assertEqual(len(STARTED_FIX), 1)
        self.assertEqual(STARTED_FIX[0].fix_round, 1)          # round advances
        self.assertIn("did the work", STARTED_FIX[0].feedback)  # feedback carried

    def test_human_request_changes_starts_fix_even_if_tests_pass(self):
        human = HumanReviewState(state="CHANGES_REQUESTED", body="rename the flag", reviewer="rushik")
        self._run(_review_input(tests_passed=True, human=human, fix_round=0))
        self.assertEqual(MERGES, [])
        self.assertEqual(len(STARTED_FIX), 1)
        self.assertIn("rename the flag", STARTED_FIX[0].feedback)

    # --- the cap holds ---
    def test_cap_reached_stops_and_awaits_human(self):
        self._run(_review_input(tests_passed=False, fix_round=3, max_rounds=3))
        self.assertEqual(MERGES, [])
        self.assertEqual(STARTED_FIX, [])                      # no more fix rounds
        self.assertTrue(any("Handing off to a human" in (r.body or "") for r in REVIEWS_POSTED))

    # --- a fix job re-reviews (pushes + escalate_review) ---
    def test_fix_job_pushes_and_re_reviews(self):
        self._run(_review_input(tests_passed=True, fix_round=1, source="fix-pr-4-r1", team="backend"))
        self.assertEqual(MERGES, [])                           # fix job never merges
        self.assertEqual(PUSHES, ["claude/issue-1"])          # it pushes the fix
        self.assertEqual(len(STARTED_REVIEW), 1)
        self.assertEqual(STARTED_REVIEW[0].fix_round, 1)

    # --- approved + gate approve merges (no fix) ---
    def test_approved_and_gate_approves_merges(self):
        async def drive(handle):
            for _ in range(100):
                if await handle.query("get_pending_approval"):
                    break
                await asyncio.sleep(0.1)
            await handle.execute_update(
                "decide", ApprovalDecision(approved=True, decided_by="rushik", note="LGTM"))
        self._run(_review_input(tests_passed=True, require_approval=True, fix_round=0), drive)
        self.assertEqual(MERGES, ["pr-4"])
        self.assertEqual(STARTED_FIX, [])

    # --- gate deny WITH a note starts a fix; a deadline deny does NOT ---
    def test_gate_deny_with_note_starts_fix(self):
        async def drive(handle):
            for _ in range(100):
                if await handle.query("get_pending_approval"):
                    break
                await asyncio.sleep(0.1)
            await handle.execute_update(
                "decide", ApprovalDecision(approved=False, decided_by="rushik",
                                           note="please add a test for the empty case"))
        self._run(_review_input(tests_passed=True, require_approval=True, fix_round=0), drive)
        self.assertEqual(MERGES, [])
        self.assertEqual(len(STARTED_FIX), 1)
        self.assertIn("empty case", STARTED_FIX[0].feedback)

    def test_gate_deadline_deny_does_not_start_fix(self):
        # Nobody answers; the deadline denies. A timeout is a safe stop, not a
        # change request — it must not spin up another fix round.
        self._run(_review_input(tests_passed=True, require_approval=True, fix_round=0))
        self.assertEqual(MERGES, [])
        self.assertEqual(STARTED_FIX, [])


if __name__ == "__main__":
    unittest.main()
