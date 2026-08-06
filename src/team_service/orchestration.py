"""Route GitHub issues and PR events into team-scoped Temporal activities."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from shared import known_teams, normalize_team, task_queue_for_team


TEAM_LABEL_PREFIX = "team/"
READY_FOR_REVIEW_ACTIONS = {"opened", "ready_for_review", "reopened", "synchronize"}


@dataclass(frozen=True)
class GitHubIssue:
    number: int
    title: str
    body: str
    labels: tuple[str, ...] = ()
    state: str = "open"
    completed: bool = False


@dataclass(frozen=True)
class PullRequestEvent:
    number: int
    title: str
    action: str
    draft: bool
    labels: tuple[str, ...] = ()
    linked_issues: tuple[int, ...] = ()
    head_ref: str = ""


@dataclass(frozen=True)
class TeamActivity:
    kind: str
    team: str
    source: str
    title: str
    trigger: str
    task_queue: str
    activity_folder: str
    prompt: str
    blocked_by: tuple[int, ...] = field(default_factory=tuple)
    # For PR-review activities: the PR's head branch, so the review job checks
    # out the PR's actual changes.
    head_ref: str = ""

    @property
    def ready(self) -> bool:
        return not self.blocked_by


def team_for_labels(labels: Iterable[str], default: str = "issues") -> str:
    for label in labels:
        normalized = label.strip().lower()
        if not normalized.startswith(TEAM_LABEL_PREFIX):
            continue
        team = normalize_team(normalized.removeprefix(TEAM_LABEL_PREFIX))
        if team in known_teams():
            return team
    return default


def _numbers_from_text(text: str) -> tuple[int, ...]:
    return tuple(int(match) for match in re.findall(r"#(\d+)", text))


def blockers_for_issue(issue: GitHubIssue) -> tuple[int, ...]:
    blockers: set[int] = set()
    for label in issue.labels:
        lower = label.lower()
        if lower.startswith(("blocked-by/", "depends-on/")):
            blockers.update(int(value) for value in re.findall(r"\d+", lower))

    for line in issue.body.splitlines():
        lower = line.lower().strip()
        if lower.startswith(("blocked by:", "depends on:", "depends-on:")):
            blockers.update(_numbers_from_text(line))

    blockers.discard(issue.number)
    return tuple(sorted(blockers))


def _folder(team: str, source: str) -> str:
    safe_source = re.sub(r"[^A-Za-z0-9._-]", "-", source).strip("-")
    return f"team-activities/{team}/{safe_source}"


def _issue_prompt(issue: GitHubIssue, team: str) -> str:
    return f"""GitHub issue #{issue.number}: {issue.title}

Team lane: {team}

Use the installed team skills. Work the issue end to end, keep changes in the
workflow workspace, run the relevant checks, write REPORT.md, and return the
required structured output.

Issue body:
{issue.body}
"""


def plan_issue_activities(
    issues: Iterable[GitHubIssue],
    completed_issue_numbers: Iterable[int] = (),
) -> list[TeamActivity]:
    completed = set(completed_issue_numbers)
    activities: list[TeamActivity] = []
    for issue in sorted(issues, key=lambda item: item.number):
        team = team_for_labels(issue.labels)
        blockers = tuple(number for number in blockers_for_issue(issue) if number not in completed)
        source = f"issue-{issue.number}"
        activities.append(
            TeamActivity(
                kind="github_issue",
                team=team,
                source=source,
                title=issue.title,
                trigger="github.issue.opened|labeled|reopened",
                task_queue=task_queue_for_team(team),
                activity_folder=_folder(team, source),
                prompt=_issue_prompt(issue, team),
                blocked_by=blockers,
            )
        )
    return activities


def plan_pr_review_activity(event: PullRequestEvent) -> TeamActivity | None:
    if event.action not in READY_FOR_REVIEW_ACTIONS or event.draft:
        return None

    team = "review"
    source = f"pr-{event.number}"
    linked = ", ".join(f"#{number}" for number in event.linked_issues) or "none"
    prompt = f"""Review pull request #{event.number}: {event.title}

Team lane: review
Head ref: {event.head_ref or "unknown"}
Linked issues: {linked}

The PR's branch is already checked out in your workspace. Inspect the diff with
`git diff main...HEAD` and run the project's tests. Use the pr-review,
self-review, and testing-bar skills to check correctness, security, and
operational risk, and write REPORT.md.

Approval decides the merge, so be decisive: if the change is correct, safe, and
its tests pass, **set tests_passed=true** — this approves and merges the PR. Only
set tests_passed=false if there is a real blocking problem (list it first with a
concrete file/line reference). Return the required structured output.
"""
    return TeamActivity(
        kind="pull_request_review",
        team=team,
        source=source,
        title=event.title,
        trigger=f"github.pull_request.{event.action}",
        task_queue=task_queue_for_team(team),
        activity_folder=_folder(team, source),
        prompt=prompt,
        head_ref=event.head_ref,
    )
