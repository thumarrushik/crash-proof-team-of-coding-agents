"""Workflow-level tests for the human gate, on Temporal's time-skipping test
server: a real RunClaudeTask executes against stub activities, blocks on the
merge gate, and we play the human — or don't, and let the 24h deadline fire in
milliseconds of wall clock. This is the deep property the gate claims: the
WAIT itself is durable and the timeout is part of the contract.
"""
import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import asyncio

from temporalio import activity
from temporalio.client import WorkflowUpdateFailedError
from temporalio.testing import WorkflowEnvironment
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
)
from workflows import RunClaudeTask

MERGES: list[str] = []


@activity.defn
async def run_claude_chunk(input: ChunkInput) -> ChunkResult:
    return ChunkResult(
        session_id="sid-test", subtype="success", text="done", cost_usd=0.01,
        num_turns=2, work_dir="/tmp/gate-test",
        structured={"summary": "ok", "files_created": [], "tests_passed": True},
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
    return MergeResult(number=input.number, merged=True, sha="abc")


def _task_input() -> TaskInput:
    return TaskInput(
        task="review PR #4", team="review", source="pr-4", pr_number=4,
        repo="o/r", require_approval=True, approval_timeout_h=24.0,
        max_chunks=2,
    )


async def _run_env(scenario) -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        tq = f"gate-test-{uuid.uuid4()}"
        async with Worker(
            env.client, task_queue=tq, workflows=[RunClaudeTask],
            activities=[run_claude_chunk, export_claude_session_transcript,
                        post_pr_review, merge_pull_request],
        ):
            await scenario(env, tq)


class HumanGateTest(unittest.TestCase):
    def setUp(self):
        MERGES.clear()

    def test_approved_gate_merges(self):
        async def scenario(env, tq):
            handle = await env.client.start_workflow(
                RunClaudeTask.run, _task_input(),
                id=f"gate-approve-{uuid.uuid4()}", task_queue=tq,
            )
            # Wait (real time, not skipped) until the workflow blocks on the gate.
            for _ in range(100):
                gate = await handle.query("get_pending_approval")
                if gate:
                    self.assertEqual(gate["action"], "merge")
                    self.assertIn("PR #4", gate["detail"])
                    break
                await asyncio.sleep(0.1)
            else:
                self.fail("gate never opened")
            reply = await handle.execute_update(
                "decide",
                ApprovalDecision(approved=True, decided_by="tester", note="LGTM"),
            )
            self.assertIn("approved", reply)
            result = await handle.result()
            self.assertTrue(result.done)

        asyncio.run(_run_env(scenario))
        self.assertEqual(MERGES, ["pr-4"])

    def test_unanswered_gate_denies_on_deadline(self):
        async def scenario(env, tq):
            handle = await env.client.start_workflow(
                RunClaudeTask.run, _task_input(),
                id=f"gate-timeout-{uuid.uuid4()}", task_queue=tq,
            )
            # Nobody answers: awaiting the result lets the test server skip
            # 24 hours; the gate must close itself on the DENY side.
            result = await handle.result()
            self.assertTrue(result.done)
            progress = await handle.query("get_progress")
            self.assertFalse(progress["awaiting_approval"])
            self.assertIsNotNone(progress["approval"])
            self.assertFalse(progress["approval"]["approved"])
            self.assertEqual(progress["approval"]["decided_by"], "deadline")

        asyncio.run(_run_env(scenario))
        self.assertEqual(MERGES, [])

    def test_unsolicited_decision_is_rejected(self):
        async def scenario(env, tq):
            handle = await env.client.start_workflow(
                RunClaudeTask.run, _task_input(),
                id=f"gate-validate-{uuid.uuid4()}", task_queue=tq,
            )
            for _ in range(100):
                if await handle.query("get_pending_approval"):
                    break
                await asyncio.sleep(0.1)
            # A decision without attribution must be rejected by the validator
            # BEFORE it enters the workflow history.
            with self.assertRaises(WorkflowUpdateFailedError):
                await handle.execute_update(
                    "decide", ApprovalDecision(approved=True, decided_by="")
                )
            # The gate is still open; a proper decision still works.
            await handle.execute_update(
                "decide", ApprovalDecision(approved=False, decided_by="tester"),
            )
            result = await handle.result()
            self.assertTrue(result.done)

        asyncio.run(_run_env(scenario))
        self.assertEqual(MERGES, [])


if __name__ == "__main__":
    unittest.main()
