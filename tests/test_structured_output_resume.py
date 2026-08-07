import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from shared import (ChunkInput, ChunkResult, TaskInput,
                    TranscriptExportInput, TranscriptExportResult)
from workflows import RunClaudeTask

CALLS: list[str] = []


@activity.defn
async def run_claude_chunk(input: ChunkInput) -> ChunkResult:
    """First chunk exhausts structured-output attempts; the resumed chunk
    succeeds — exactly the shape the live fleet run produced (work complete
    in the session, only the report handshake failing)."""
    CALLS.append(input.session_id or "")
    if len(CALLS) == 1:
        return ChunkResult(
            session_id="sid-1", subtype="error_max_structured_output_retries",
            text="", errors=["Failed to provide valid structured output after 5 attempts"],
            cost_usd=0.01, num_turns=5, work_dir="/tmp/so-test",
        )
    return ChunkResult(
        session_id="sid-1", subtype="success", text="done",
        cost_usd=0.01, num_turns=2, work_dir="/tmp/so-test",
        structured={"summary": "resumed and reported", "files_created": [],
                    "tests_passed": True},
    )


@activity.defn
async def export_claude_session_transcript(input: TranscriptExportInput) -> TranscriptExportResult:
    return TranscriptExportResult(markdown_path="", source_jsonl_path="", event_count=0)


class StructuredOutputResumeTest(unittest.IsolatedAsyncioTestCase):
    async def test_structured_output_exhaustion_resumes_the_session(self) -> None:
        """The fleet run's dominant failure class must not be terminal: the
        workflow schedules another chunk that resumes the same session and
        re-asks for the report."""
        CALLS.clear()
        env = await WorkflowEnvironment.start_time_skipping()
        try:
            async with Worker(env.client, task_queue="so-test-queue",
                              workflows=[RunClaudeTask],
                              activities=[run_claude_chunk,
                                          export_claude_session_transcript]):
                result = await env.client.execute_workflow(
                    RunClaudeTask.run,
                    TaskInput(task="do a thing", team="backend", max_chunks=3),
                    id="so-resume-test", task_queue="so-test-queue",
                )
        finally:
            await env.shutdown()
        self.assertTrue(result.done)
        self.assertEqual(len(CALLS), 2, "expected a resume chunk")
        self.assertEqual(CALLS[1], "sid-1",
                         "second chunk must RESUME the first chunk's session")
        self.assertEqual(result.report["summary"], "resumed and reported")


if __name__ == "__main__":
    unittest.main()
