"""Worker affinity: sticky-session task queues.

The transcript and the workspace are local files on the worker that ran a
chunk, so a resume has to land on that worker. These tests cover the routing
guarantee end to end on Temporal's time-skipping server (the first chunk runs
on the shared lane queue; once a chunk reports its per-worker queue, every later
chunk and the transcript export pin there), plus the pure helpers the guarantee
rests on. The multi-*machine* proof is a live run; this pins the *logic*.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from shared import (
    ChunkInput,
    ChunkResult,
    TaskInput,
    TranscriptExportInput,
    TranscriptExportResult,
    pin_queue,
    stable_worker_id,
    task_queue_for_team,
    worker_queue_name,
)
from workflows import RunClaudeTask


class AffinityHelpersTest(unittest.TestCase):
    def test_pin_queue_prefers_the_pinned_queue(self) -> None:
        self.assertEqual(pin_queue("lane", "lane-w-host"), "lane-w-host")

    def test_pin_queue_falls_back_to_lane_when_unpinned(self) -> None:
        # "" is the affinity-off / first-chunk case: stay on the lane queue.
        self.assertEqual(pin_queue("lane", ""), "lane")

    def test_worker_queue_name_extends_the_lane_queue(self) -> None:
        lane = task_queue_for_team("backend")
        self.assertEqual(worker_queue_name("backend", "host-1"), f"{lane}-w-host-1")

    def test_stable_worker_id_honors_override_and_is_stable(self) -> None:
        prev = os.environ.get("WORKER_ID")
        try:
            os.environ["WORKER_ID"] = "pod-7"
            self.assertEqual(stable_worker_id(), "pod-7")
            self.assertEqual(stable_worker_id(), "pod-7")  # stable across calls
        finally:
            os.environ.pop("WORKER_ID", None)
            if prev is not None:
                os.environ["WORKER_ID"] = prev

    def test_stable_worker_id_sanitizes_hostnames(self) -> None:
        prev = os.environ.get("WORKER_ID")
        try:
            os.environ["WORKER_ID"] = "Weird Host/Name!!"
            wid = stable_worker_id()
            self.assertNotIn("/", wid)
            self.assertNotIn(" ", wid)
            self.assertTrue(wid)  # never empty
            # the id is queue-name safe (no chars task_queue_for_team wouldn't produce)
            self.assertRegex(wid, r"^[A-Za-z0-9._-]+$")
        finally:
            os.environ.pop("WORKER_ID", None)
            if prev is not None:
                os.environ["WORKER_ID"] = prev


LANE = "affinity-test-lane"
PINNED = f"{LANE}-w-hostX"
CHUNK_QUEUES: list[str] = []
EXPORT_QUEUES: list[str] = []


@activity.defn
async def run_claude_chunk(input: ChunkInput) -> ChunkResult:
    """Records the queue it ran on. Chunk 0 reports a per-worker queue and does
    not finish; the resumed chunk (which must land on that queue) succeeds."""
    CHUNK_QUEUES.append(activity.info().task_queue)
    if len(CHUNK_QUEUES) == 1:
        return ChunkResult(
            session_id="sid-1", subtype="error_max_turns", text="",
            cost_usd=0.01, num_turns=2, work_dir="/tmp/aff-test",
            worker_queue=PINNED,   # "I am the worker that holds the session"
        )
    return ChunkResult(
        session_id="sid-1", subtype="success", text="done",
        cost_usd=0.01, num_turns=2, work_dir="/tmp/aff-test",
        structured={"summary": "ok", "files_created": [], "tests_passed": True},
    )


@activity.defn
async def export_claude_session_transcript(
    input: TranscriptExportInput,
) -> TranscriptExportResult:
    EXPORT_QUEUES.append(activity.info().task_queue)
    return TranscriptExportResult(markdown_path="", source_jsonl_path="", event_count=0)


class AffinityRoutingTest(unittest.IsolatedAsyncioTestCase):
    async def test_resume_pins_to_the_reporting_worker(self) -> None:
        """First chunk on the lane queue; once it reports a per-worker queue,
        the resumed chunk AND the transcript export run on that queue."""
        CHUNK_QUEUES.clear()
        EXPORT_QUEUES.clear()
        env = await WorkflowEnvironment.start_time_skipping()
        try:
            acts = [run_claude_chunk, export_claude_session_transcript]
            # Two workers, as on a two-machine lane: the shared lane queue and
            # this "host"'s per-worker queue. Only the pinned worker can serve
            # the resumed chunk, so the run completing at all proves the route.
            async with Worker(env.client, task_queue=LANE,
                              workflows=[RunClaudeTask], activities=acts), \
                       Worker(env.client, task_queue=PINNED,
                              workflows=[RunClaudeTask], activities=acts):
                result = await env.client.execute_workflow(
                    RunClaudeTask.run,
                    TaskInput(task="do a thing", team="backend", max_chunks=3),
                    id="affinity-route-test", task_queue=LANE,
                )
        finally:
            await env.shutdown()

        self.assertTrue(result.done)
        self.assertEqual(CHUNK_QUEUES, [LANE, PINNED],
                         "first chunk on the lane queue, the resume pinned to the worker")
        self.assertEqual(EXPORT_QUEUES, [PINNED],
                         "the transcript export must run where the session's files live")

    async def test_no_reported_queue_stays_on_the_lane(self) -> None:
        """Affinity off (a chunk reports no worker_queue): nothing pins, every
        activity stays on the lane queue — the pre-affinity behavior, unchanged."""
        CHUNK_QUEUES.clear()
        EXPORT_QUEUES.clear()

        @activity.defn(name="run_claude_chunk")
        async def one_shot_chunk(input: ChunkInput) -> ChunkResult:
            CHUNK_QUEUES.append(activity.info().task_queue)
            return ChunkResult(
                session_id="sid-1", subtype="success", text="done",
                cost_usd=0.01, num_turns=2, work_dir="/tmp/aff-test",
                structured={"summary": "ok", "files_created": [], "tests_passed": True},
            )

        env = await WorkflowEnvironment.start_time_skipping()
        try:
            async with Worker(env.client, task_queue=LANE, workflows=[RunClaudeTask],
                              activities=[one_shot_chunk, export_claude_session_transcript]):
                result = await env.client.execute_workflow(
                    RunClaudeTask.run,
                    TaskInput(task="do a thing", team="backend", max_chunks=3),
                    id="affinity-off-test", task_queue=LANE,
                )
        finally:
            await env.shutdown()

        self.assertTrue(result.done)
        self.assertEqual(CHUNK_QUEUES, [LANE])
        self.assertEqual(EXPORT_QUEUES, [LANE])


if __name__ == "__main__":
    unittest.main()
