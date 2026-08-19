import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from team_service import (
    GitHubIssue,
    PullRequestEvent,
    plan_issue_activities,
    plan_pr_review_activity,
    team_for_labels,
)


class TeamOrchestrationTests(unittest.TestCase):
    def test_team_label_routes_to_known_team(self) -> None:
        self.assertEqual(team_for_labels(("team/backend",)), "backend")
        self.assertEqual(team_for_labels(("bug", "team/service-design")), "service-design")
        self.assertEqual(team_for_labels(("team/unknown",)), "issues")

    def test_issue_blockers_hold_activity_until_dependency_completed(self) -> None:
        service_contract = GitHubIssue(
            number=10,
            title="Define status contract",
            body="Create STATUS_CONTRACT.md",
            labels=("team/service-design",),
        )
        backend_work = GitHubIssue(
            number=11,
            title="Build status endpoint",
            body="Blocked by: #10\nImplement the backend endpoint.",
            labels=("team/backend",),
        )

        blocked = plan_issue_activities([service_contract, backend_work])
        self.assertEqual(blocked[0].team, "service-design")
        self.assertTrue(blocked[0].ready)
        self.assertEqual(blocked[1].team, "backend")
        self.assertEqual(blocked[1].blocked_by, (10,))
        self.assertEqual(blocked[1].task_queue, "claude-code-tasks-backend")
        self.assertEqual(blocked[1].activity_folder, "team-activities/backend/issue-11")

        unblocked = plan_issue_activities([backend_work], completed_issue_numbers=(10,))
        self.assertTrue(unblocked[0].ready)

    def test_transitive_chain_runs_strictly_serially(self) -> None:
        """A <- B <- C: each dependent becomes ready only after its own blocker
        CLOSES, so a declared chain executes serially across polls while
        anything undeclared-and-unblocked stays free to run in parallel."""
        a = GitHubIssue(number=1, title="A", body="first", labels=("team/backend",))
        b = GitHubIssue(number=2, title="B", body="Blocked by: #1", labels=("team/backend",))
        c = GitHubIssue(number=3, title="C", body="Blocked by: #2", labels=("team/backend",))
        free = GitHubIssue(number=9, title="unrelated", body="no deps", labels=("team/frontend",))
        issues = [a, b, c, free]

        poll1 = {p.source: p.ready for p in plan_issue_activities(issues)}
        self.assertEqual(poll1, {"issue-1": True, "issue-2": False,
                                 "issue-3": False, "issue-9": True})

        poll2 = {p.source: p.ready
                 for p in plan_issue_activities(issues, completed_issue_numbers=(1,))}
        self.assertEqual(poll2, {"issue-1": True, "issue-2": True,
                                 "issue-3": False, "issue-9": True})

        poll3 = {p.source: p.ready
                 for p in plan_issue_activities(issues, completed_issue_numbers=(1, 2))}
        self.assertTrue(poll3["issue-3"])

    def test_multiple_blockers_all_must_close(self) -> None:
        d = GitHubIssue(number=4, title="D", body="Blocked by: #1 #2",
                        labels=("team/backend",))
        self.assertFalse(plan_issue_activities([d], completed_issue_numbers=(1,))[0].ready)
        self.assertTrue(plan_issue_activities([d], completed_issue_numbers=(1, 2))[0].ready)

    def test_blocker_label_is_supported(self) -> None:
        issue = GitHubIssue(
            number=12,
            title="Frontend status panel",
            body="",
            labels=("team/frontend", "depends-on/10"),
        )

        activity = plan_issue_activities([issue])[0]

        self.assertEqual(activity.team, "frontend")
        self.assertEqual(activity.blocked_by, (10,))
        self.assertEqual(activity.activity_folder, "team-activities/frontend/issue-12")

    def test_ready_pr_creates_review_activity(self) -> None:
        event = PullRequestEvent(
            number=42,
            title="Add status service",
            action="ready_for_review",
            draft=False,
            labels=("team/backend",),
            linked_issues=(10, 11),
            head_ref="feature/status-service",
        )

        activity = plan_pr_review_activity(event)

        self.assertIsNotNone(activity)
        assert activity is not None
        self.assertEqual(activity.team, "review")
        self.assertEqual(activity.task_queue, "claude-code-tasks-review")
        self.assertEqual(activity.activity_folder, "team-activities/review/pr-42")
        self.assertIn("Review pull request #42", activity.prompt)

    def test_draft_pr_does_not_create_review_activity(self) -> None:
        event = PullRequestEvent(
            number=43,
            title="Draft status service",
            action="opened",
            draft=True,
        )

        self.assertIsNone(plan_pr_review_activity(event))


if __name__ == "__main__":
    unittest.main()
