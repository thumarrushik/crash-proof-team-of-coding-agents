import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest
from unittest import mock

from temporalio.exceptions import WorkflowAlreadyStartedError

import poller
from shared import (
    ConflictEscalationInput,
    FixEscalationInput,
    MergeInput,
    PostReviewInput,
    ReviewEscalationInput,
    namespace_for_team,
)
from team_service import GitHubIssue, PullRequestEvent, plan_issue_activities, plan_pr_review_activity


class FakeClient:
    """Records start_workflow calls; can simulate a duplicate rejection."""

    def __init__(self, raise_duplicate: bool = False) -> None:
        self.started: list[dict] = []
        self.raise_duplicate = raise_duplicate

    async def start_workflow(self, run, arg, *, id, task_queue, id_reuse_policy):  # noqa: A002
        if self.raise_duplicate:
            raise WorkflowAlreadyStartedError(id, "RunClaudeTask")
        self.started.append({"id": id, "task_queue": task_queue, "input": arg})
        return f"handle:{id}"


def _activity(number: int, labels, body: str = "", completed=()):
    issue = GitHubIssue(number=number, title="t", body=body, labels=tuple(labels))
    return plan_issue_activities([issue], completed)[0]


class PollerTests(unittest.IsolatedAsyncioTestCase):
    async def test_ready_activity_starts_with_deterministic_id(self) -> None:
        client = FakeClient()
        activity = _activity(1, ("team/backend",))

        started = await poller.submit(client, activity, model="fable", dry_run=False)

        self.assertTrue(started)
        self.assertEqual(client.started[0]["id"], "claude-backend-issue-1")
        self.assertEqual(client.started[0]["task_queue"], "claude-code-tasks-backend")
        self.assertEqual(client.started[0]["input"].team, "backend")
        self.assertEqual(client.started[0]["input"].model, "fable")

    async def test_blocked_activity_is_held(self) -> None:
        client = FakeClient()
        activity = _activity(11, ("team/backend",), body="Blocked by: #10")

        started = await poller.submit(client, activity, model=None, dry_run=False)

        self.assertFalse(started)
        self.assertEqual(client.started, [])  # nothing submitted while blocked

    async def test_blocker_closed_unblocks_activity(self) -> None:
        client = FakeClient()
        activity = _activity(11, ("team/backend",), body="Blocked by: #10", completed=(10,))

        self.assertTrue(await poller.submit(client, activity, model=None, dry_run=False))
        self.assertEqual(client.started[0]["id"], "claude-backend-issue-11")

    async def test_duplicate_submission_is_skipped(self) -> None:
        client = FakeClient(raise_duplicate=True)
        activity = _activity(1, ("team/backend",))

        started = await poller.submit(client, activity, model=None, dry_run=False)

        self.assertFalse(started)  # already-started rejection is swallowed

    async def test_dry_run_submits_nothing(self) -> None:
        client = FakeClient()
        activity = _activity(1, ("team/backend",))

        started = await poller.submit(client, activity, model=None, dry_run=True)

        self.assertFalse(started)
        self.assertEqual(client.started, [])

    async def test_submit_with_repo_sets_clone_and_branch(self) -> None:
        client = FakeClient()
        activity = _activity(1, ("team/backend",))

        await poller.submit(client, activity, repo="o/r", model=None, dry_run=False)

        task_input = client.started[0]["input"]
        self.assertEqual(task_input.repo, "o/r")
        self.assertEqual(task_input.branch, "claude/issue-1")

    async def test_merge_pull_request_reports_merged(self) -> None:
        import contextlib
        import io
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_put", return_value=(200, {"merged": True, "sha": "abc123"})), \
             contextlib.redirect_stdout(io.StringIO()):
            result = await poller.merge_pull_request(MergeInput(repo="o/r", number=5))
        self.assertTrue(result.merged)
        self.assertEqual(result.sha, "abc123")
        self.assertEqual(result.number, 5)

    async def test_merge_conflict_sets_conflict_flag(self) -> None:
        import contextlib
        import io
        import urllib.error
        err = urllib.error.HTTPError("http://x", 405, "Method Not Allowed", {},
                                     io.BytesIO(b'{"message":"Pull Request has merge conflicts"}'))
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_put", side_effect=err), \
             contextlib.redirect_stdout(io.StringIO()):
            # the activity's operator print ("MERGE PR #5: FAILED 405") is
            # expected here; keep it out of a green suite's output
            result = await poller.merge_pull_request(MergeInput(repo="o/r", number=5))
        self.assertFalse(result.merged)
        self.assertTrue(result.conflict)  # 405 -> conflict, the self-heal trigger

    async def test_review_activity_sets_pr_number_and_head_branch(self) -> None:
        client = FakeClient()
        event = PullRequestEvent(number=42, title="p", action="ready_for_review",
                                 draft=False, head_ref="claude/issue-9")
        activity = plan_pr_review_activity(event)

        await poller.submit(client, activity, repo="o/r", model=None, dry_run=False)

        ti = client.started[0]["input"]
        self.assertEqual(ti.team, "review")
        self.assertEqual(ti.source, "pr-42")

    def test_review_source_is_keyed_by_head_sha(self) -> None:
        """Every new push is a NEW review job: without the sha key, a completed
        review blocked re-review after a conflict-resolve push and cascade
        conflicts never converged (observed live on PRs #21-#23)."""
        event = PullRequestEvent(number=42, title="t", action="ready_for_review",
                                 draft=False, head_ref="claude/issue-9",
                                 head_sha="abcdef1234567890")
        activity = plan_pr_review_activity(event)
        self.assertEqual(activity.source, "pr-42-abcdef1")
        self.assertEqual(poller.workflow_id_for(activity), "claude-review-pr-42-abcdef1")
        ti = poller._task_input_for(activity, repo="o/r", model=None)
        self.assertEqual(ti.pr_number, 42)          # parsed despite the suffix
        self.assertEqual(ti.source, "pr-42-abcdef1")
        self.assertEqual(ti.pr_number, 42)
        self.assertEqual(ti.branch, "claude/issue-9")   # checks out the PR's branch

    async def test_post_pr_review_approve_posts_comment(self) -> None:
        captured = {}
        def fake_post(path, token, body):
            captured.update(path=path, body=body)
            return (200, {})
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_post", side_effect=fake_post):
            r = await poller.post_pr_review(PostReviewInput(repo="o/r", number=7, approve=True, body="lgtm"))
        self.assertTrue(r.posted)
        self.assertEqual(r.event, "COMMENT")          # can't APPROVE own PR -> COMMENT
        self.assertIn("/pulls/7/reviews", captured["path"])
        self.assertEqual(captured["body"]["event"], "COMMENT")

    def test_issue_number_from_branch(self) -> None:
        self.assertEqual(poller._issue_number_from_branch("claude/issue-7"), 7)
        self.assertEqual(poller._issue_number_from_branch("claude/issue-42"), 42)
        self.assertIsNone(poller._issue_number_from_branch("feature/x"))
        self.assertIsNone(poller._issue_number_from_branch(""))

    async def test_escalate_conflict_starts_resolve_job_on_owning_team(self) -> None:
        client = FakeClient()

        async def fake_connect(addr, *, namespace):
            self.assertEqual(namespace, "backend")  # owning team's namespace
            return client

        issue = {"number": 1, "labels": [{"name": "team/backend"}]}
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_get", return_value=issue), \
             mock.patch.object(poller, "_gh_post", return_value=(201, {})), \
             mock.patch.object(poller.Client, "connect", side_effect=fake_connect):
            result = await poller.escalate_conflict(
                ConflictEscalationInput(repo="o/r", pr_number=4, branch="claude/issue-1")
            )

        self.assertTrue(result.started)
        self.assertEqual(result.team, "backend")
        self.assertEqual(result.workflow_id, "claude-backend-resolve-pr-4")
        started = client.started[0]
        self.assertEqual(started["id"], "claude-backend-resolve-pr-4")
        self.assertEqual(started["task_queue"], "claude-code-tasks-backend")
        ti = started["input"]
        self.assertEqual(ti.source, "resolve-pr-4")
        self.assertEqual(ti.pr_number, 4)
        self.assertEqual(ti.branch, "claude/issue-1")
        self.assertEqual(ti.team, "backend")

    async def test_escalate_conflict_duplicate_is_noop(self) -> None:
        client = FakeClient(raise_duplicate=True)

        async def fake_connect(addr, *, namespace):
            return client

        issue = {"number": 1, "labels": [{"name": "team/frontend"}]}
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_get", return_value=issue), \
             mock.patch.object(poller, "_gh_post", return_value=(201, {})), \
             mock.patch.object(poller.Client, "connect", side_effect=fake_connect):
            result = await poller.escalate_conflict(
                ConflictEscalationInput(repo="o/r", pr_number=9, branch="claude/issue-1")
            )

        self.assertFalse(result.started)          # already-running resolve job → no-op
        self.assertEqual(result.workflow_id, "claude-frontend-resolve-pr-9")

    def test_namespace_per_team(self) -> None:
        self.assertEqual(namespace_for_team("backend"), "backend")
        self.assertEqual(namespace_for_team("Service-Design"), "service-design")

    # --- review-driven fix loop --------------------------------------------

    async def test_read_pr_review_state_latest_changes_requested(self) -> None:
        reviews = [
            {"state": "COMMENTED", "body": "nit", "user": {"login": "a"}},
            {"state": "APPROVED", "body": "", "user": {"login": "b"}},
            {"state": "CHANGES_REQUESTED", "body": "rename x", "user": {"login": "rushik"}},
        ]
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_get", return_value=reviews):
            state = await poller.read_pr_review_state("o/r", 4)
        self.assertTrue(state.requests_changes)          # latest decisive state wins
        self.assertEqual(state.body, "rename x")
        self.assertEqual(state.reviewer, "rushik")

    async def test_read_pr_review_state_ignores_comments_and_bot(self) -> None:
        # Only COMMENTED reviews (our bot's own kind) → no human request.
        reviews = [{"state": "COMMENTED", "body": "🤖 automated", "user": {"login": "bot"}}]
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_get", return_value=reviews):
            state = await poller.read_pr_review_state("o/r", 4)
        self.assertFalse(state.requests_changes)
        self.assertEqual(state.state, "")

    async def test_escalate_fix_starts_fix_job_on_owning_team(self) -> None:
        client = FakeClient()

        async def fake_connect(addr, *, namespace):
            self.assertEqual(namespace, "backend")
            return client

        issue = {"number": 1, "labels": [{"name": "team/backend"}]}
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_get", return_value=issue), \
             mock.patch.object(poller, "_gh_post", return_value=(201, {})), \
             mock.patch.object(poller.Client, "connect", side_effect=fake_connect):
            result = await poller.escalate_fix(FixEscalationInput(
                repo="o/r", pr_number=4, branch="claude/issue-1",
                feedback="tests failed: empty case", fix_round=2, require_approval=True))

        self.assertTrue(result.started)
        self.assertEqual(result.team, "backend")
        self.assertEqual(result.workflow_id, "claude-backend-fix-pr-4-r2")
        ti = client.started[0]["input"]
        self.assertEqual(ti.source, "fix-pr-4-r2")
        self.assertEqual(ti.fix_round, 2)
        self.assertTrue(ti.enable_fix_loop)
        self.assertTrue(ti.require_approval)
        self.assertIn("empty case", ti.task)                  # feedback in the prompt

    async def test_escalate_fix_duplicate_round_is_noop(self) -> None:
        client = FakeClient(raise_duplicate=True)

        async def fake_connect(addr, *, namespace):
            return client

        issue = {"number": 1, "labels": [{"name": "team/backend"}]}
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(poller, "_gh_get", return_value=issue), \
             mock.patch.object(poller.Client, "connect", side_effect=fake_connect):
            result = await poller.escalate_fix(FixEscalationInput(
                repo="o/r", pr_number=4, branch="claude/issue-1", feedback="x", fix_round=1))
        self.assertFalse(result.started)                      # same round already running → no-op

    async def test_escalate_review_starts_followup_on_review_lane(self) -> None:
        client = FakeClient()

        async def fake_connect(addr, *, namespace):
            self.assertEqual(namespace, "review")
            return client

        with mock.patch.object(poller.Client, "connect", side_effect=fake_connect):
            result = await poller.escalate_review(ReviewEscalationInput(
                repo="o/r", pr_number=4, branch="claude/issue-1", fix_round=1, require_approval=True))

        self.assertTrue(result.started)
        self.assertEqual(result.workflow_id, "claude-review-pr-4-r1")
        ti = client.started[0]["input"]
        self.assertEqual(ti.team, "review")
        self.assertEqual(ti.source, "pr-4-r1")
        self.assertEqual(ti.fix_round, 1)
        self.assertTrue(ti.require_approval)

    async def test_task_input_review_cfg_applied_to_pr_jobs_only(self) -> None:
        client = FakeClient()
        event = PullRequestEvent(number=42, title="p", action="ready_for_review",
                                 draft=False, head_ref="claude/issue-9")
        activity = plan_pr_review_activity(event)
        cfg = {"enable_fix_loop": True, "max_fix_rounds": 5,
               "require_approval": True, "approval_timeout_h": 12.0}

        await poller.submit(client, activity, repo="o/r", model=None, dry_run=False, review_cfg=cfg)

        ti = client.started[0]["input"]
        self.assertTrue(ti.enable_fix_loop)
        self.assertEqual(ti.max_fix_rounds, 5)
        self.assertTrue(ti.require_approval)
        self.assertEqual(ti.approval_timeout_h, 12.0)

        # An issue job ignores review_cfg (fix loop is a review-lane concern).
        client2 = FakeClient()
        issue_activity = _activity(1, ("team/backend",))
        await poller.submit(client2, issue_activity, repo="o/r", model=None, dry_run=False, review_cfg=cfg)
        self.assertFalse(client2.started[0]["input"].enable_fix_loop)

    async def test_run_poll_submits_into_team_namespaces(self) -> None:
        open_issues = [
            GitHubIssue(number=1, title="a", body="", labels=("team/backend",)),
            GitHubIssue(number=3, title="c", body="", labels=("team/frontend",)),
            GitHubIssue(number=2, title="b", body="Blocked by: #99", labels=("team/testing",)),
        ]
        seen_ns: list[str] = []
        clients: dict[str, FakeClient] = {}

        async def connect(ns):
            seen_ns.append(ns)
            clients[ns] = FakeClient()
            return clients[ns]

        with mock.patch.object(poller, "list_open_issues", return_value=open_issues), \
             mock.patch.object(poller, "list_closed_issue_numbers", return_value=set()), \
             mock.patch.object(poller, "list_reviewable_prs", return_value=[]):
            summary = await poller.run_poll(connect, "o/r", "tok", model="fable", dry_run=False)

        self.assertEqual(summary.started, 2)   # backend + frontend; testing is blocked
        self.assertEqual(sorted(seen_ns), ["backend", "frontend"])
        self.assertEqual(clients["backend"].started[0]["id"], "claude-backend-issue-1")
        self.assertEqual(clients["frontend"].started[0]["id"], "claude-frontend-issue-3")


if __name__ == "__main__":
    unittest.main()
