"""GitHub poller: find work, submit Temporal jobs — and run *on* Temporal.

Each poll lists a repo's open issues and open pull requests, routes them with
``team_service`` (labels -> team, ``Blocked by: #n`` -> hold), and starts a
``RunClaudeTask`` workflow per item.

The trick that keeps this tiny: workflow IDs are **deterministic**
(``claude-<team>-<source>``) and started with ``ALLOW_DUPLICATE_FAILED_ONLY``. Re-polling
the same issue is a no-op — Temporal rejects the duplicate — so the poller keeps
**no state of its own**. Temporal is the queue and the dedup. A blocked issue is
skipped each poll until its blocker issue is *closed* on GitHub.

The poll itself runs on Temporal: a **Schedule** fires ``PollGitHubWorkflow``
(defined in ``workflows.py``), which runs the ``poll_github_activity`` below on a
dedicated ``claude-code-poller`` queue. So the poll loop is durable, retried, and
visible in the Temporal UI — no external cron required.

    # one-time: create the schedule (needs a `worker.py --poller` running)
    uv run poller.py --schedule --interval 300 --repo owner/name

    # or run a single poll locally, no worker needed (handy for cron / dry-run)
    uv run poller.py --once --repo owner/name [--dry-run]

Auth: the poll worker needs GITHUB_TOKEN (or GH_TOKEN); local `--once` reads it
from your shell. A `worker.py --team <t>` per lane must run so jobs execute.
"""

import argparse
import asyncio
import json
import os
import re
import urllib.error
import urllib.request
from datetime import timedelta

from temporalio import activity
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
)
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from shared import (
    DEFAULT_NAMESPACE,
    POLLER_TASK_QUEUE,
    TEMPORAL_ADDRESS,
    ConflictEscalationInput,
    ConflictEscalationResult,
    FixEscalationInput,
    FixEscalationResult,
    HumanReviewState,
    MergeInput,
    MergeResult,
    PollInput,
    PollSummary,
    PostReviewInput,
    PostReviewResult,
    ReviewEscalationInput,
    ReviewEscalationResult,
    TaskInput,
    namespace_for_team,
    task_queue_for_team,
)
from team_service import (
    GitHubIssue,
    PullRequestEvent,
    plan_issue_activities,
    plan_pr_review_activity,
    team_for_labels,
)

GITHUB_API = "https://api.github.com"


# --- GitHub reads (the only place we touch GitHub) -------------------------


def _gh_get(path: str, token: str) -> list:
    request = urllib.request.Request(
        f"{GITHUB_API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "temporal-claude-poller",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def _gh_put(path: str, token: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"{GITHUB_API}{path}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "temporal-claude-poller",
        },
    )
    with urllib.request.urlopen(request) as response:
        raw = response.read().decode()
        return response.status, (json.loads(raw) if raw else {})


def _gh_post(path: str, token: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"{GITHUB_API}{path}",
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "temporal-claude-poller",
        },
    )
    with urllib.request.urlopen(request) as response:
        raw = response.read().decode()
        return response.status, (json.loads(raw) if raw else {})


def _labels(node: dict) -> tuple[str, ...]:
    return tuple(label["name"] for label in node.get("labels", []) if label.get("name"))


def list_open_issues(repo: str, token: str) -> list[GitHubIssue]:
    """Open issues (the /issues endpoint also returns PRs — skip those)."""
    issues: list[GitHubIssue] = []
    for item in _gh_get(f"/repos/{repo}/issues?state=open&per_page=100", token):
        if "pull_request" in item:
            continue
        issues.append(
            GitHubIssue(
                number=item["number"],
                title=item.get("title", ""),
                body=item.get("body") or "",
                labels=_labels(item),
                state=item.get("state", "open"),
            )
        )
    return issues


def list_closed_issue_numbers(repo: str, token: str) -> set[int]:
    """Closed issue numbers — a closed blocker unblocks its dependents."""
    return {
        item["number"]
        for item in _gh_get(f"/repos/{repo}/issues?state=closed&per_page=100", token)
        if "pull_request" not in item
    }


def list_reviewable_prs(repo: str, token: str) -> list[PullRequestEvent]:
    """Open pull requests, as review events (draft PRs are marked draft)."""
    events: list[PullRequestEvent] = []
    for pr in _gh_get(f"/repos/{repo}/pulls?state=open&per_page=100", token):
        events.append(
            PullRequestEvent(
                number=pr["number"],
                title=pr.get("title", ""),
                action="ready_for_review" if not pr.get("draft") else "opened",
                draft=bool(pr.get("draft")),
                labels=_labels(pr),
                head_ref=(pr.get("head") or {}).get("ref", ""),
            )
        )
    return events


# --- routing + submit ------------------------------------------------------


def workflow_id_for(activity_plan) -> str:
    """Deterministic, idempotent workflow ID for a routed activity."""
    return f"claude-{activity_plan.team}-{activity_plan.source}"


def plan(repo: str, token: str):
    """Read GitHub and route it into a list of TeamActivity plans."""
    issues = list_open_issues(repo, token)
    completed = list_closed_issue_numbers(repo, token)
    prs = list_reviewable_prs(repo, token)
    activities = plan_issue_activities(issues, completed)
    for pr in prs:
        review = plan_pr_review_activity(pr)
        if review is not None:
            activities.append(review)
    return issues, prs, activities


def _task_input_for(activity_plan, repo: str | None, model: str | None,
                    review_cfg: dict | None = None) -> TaskInput:
    """Build the TaskInput for a routed activity.

    Issue lanes clone the repo and work a fresh ``claude/issue-<n>`` branch, then
    open a PR. The review lane checks out the PR's own head branch and, on
    approval, merges PR #<n>. ``review_cfg`` (poll-level fix-loop + human-gate
    settings) is applied only to review-lane (``pr-``) jobs, so a not-approved
    PR can start the fix loop and re-ask a human.
    """
    source = activity_plan.source or ""
    if source.startswith("pr-"):
        pr_number = int(source.split("-")[-1])
        branch = getattr(activity_plan, "head_ref", "") or None
        cfg = review_cfg or {}
        return TaskInput(task=activity_plan.prompt, team=activity_plan.team, model=model,
                         repo=repo, branch=branch, source=source, pr_number=pr_number,
                         enable_fix_loop=cfg.get("enable_fix_loop", False),
                         max_fix_rounds=cfg.get("max_fix_rounds", 3),
                         require_approval=cfg.get("require_approval", False),
                         approval_timeout_h=cfg.get("approval_timeout_h", 24.0))
    return TaskInput(task=activity_plan.prompt, team=activity_plan.team, model=model,
                     repo=repo, branch=f"claude/{source}" if repo else None, source=source)


async def submit(client, activity_plan, *, repo: str | None = None, model: str | None,
                 dry_run: bool, review_cfg: dict | None = None) -> bool:
    """Start the workflow for one activity on ``client`` (already connected to
    the activity's team namespace). Returns True iff it started now."""
    workflow_id = workflow_id_for(activity_plan)
    if not activity_plan.ready:
        blockers = ", ".join(f"#{n}" for n in activity_plan.blocked_by)
        print(f"  hold  {workflow_id}: blocked by {blockers}")
        return False
    if dry_run:
        print(f"  plan  {workflow_id} -> {namespace_for_team(activity_plan.team)}/{activity_plan.task_queue}")
        return False
    # Lazy import keeps this module free of a workflows<->poller import cycle.
    from workflows import RunClaudeTask

    try:
        await client.start_workflow(
            RunClaudeTask.run,
            _task_input_for(activity_plan, repo, model, review_cfg),
            id=workflow_id,
            task_queue=activity_plan.task_queue,
            # Idempotent against running/completed work, but a FAILED
            # attempt may retry on a later sweep — REJECT_DUPLICATE
            # deadlocked an issue forever after one transient failure.
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
        )
        print(f"  START {workflow_id} -> {namespace_for_team(activity_plan.team)}/{activity_plan.task_queue}")
        return True
    except WorkflowAlreadyStartedError:
        print(f"  skip  {workflow_id}: already submitted")
        return False


async def run_poll(connect, repo: str, token: str, *, model: str | None, dry_run: bool,
                   review_cfg: dict | None = None) -> PollSummary:
    """One poll: read GitHub, route, submit each job **into its team namespace**.

    ``connect`` is an async ``(namespace) -> client`` (None for dry-run); clients
    are created once per namespace and reused. ``review_cfg`` carries poll-level
    fix-loop + human-gate settings applied to review-lane jobs.
    """
    issues, prs, activities = plan(repo, token)
    summary = PollSummary(open_issues=len(issues), open_prs=len(prs), planned=len(activities))
    clients: dict[str, object] = {}
    for activity_plan in activities:
        if not activity_plan.ready:
            summary.held += 1
            print(f"  hold  {workflow_id_for(activity_plan)}: blocked by {activity_plan.blocked_by}")
            continue
        client = None
        if not dry_run:
            ns = namespace_for_team(activity_plan.team)
            if ns not in clients:
                clients[ns] = await connect(ns)
            client = clients[ns]
        if await submit(client, activity_plan, repo=repo, model=model, dry_run=dry_run,
                        review_cfg=review_cfg):
            summary.started += 1
            summary.started_ids.append(workflow_id_for(activity_plan))
    print(
        f"poll: {summary.open_issues} issues, {summary.open_prs} PRs -> "
        f"{summary.planned} planned, {summary.started} started, {summary.held} held"
    )
    return summary


@activity.defn
async def post_pr_review(input: PostReviewInput) -> PostReviewResult:
    """Post a GitHub review on a PR from the review lane. GitHub forbids
    APPROVE on your own PR, so we post COMMENT (approve) / REQUEST_CHANGES; the
    review workflow does the actual merge on approval."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("post_pr_review requires GITHUB_TOKEN in the worker env")
    # GitHub forbids APPROVE/REQUEST_CHANGES on your own PR, so post a COMMENT
    # review either way; the workflow gates the merge on `approve` separately.
    event = "COMMENT"
    body = ("✅ Automated review: approved.\n\n" if input.approve else "❌ Automated review: changes requested.\n\n") + input.body
    try:
        _gh_post(f"/repos/{input.repo}/pulls/{input.number}/reviews", token, {"event": event, "body": body})
        print(f"  REVIEW PR #{input.number}: {event}")
        return PostReviewResult(number=input.number, posted=True, event=event)
    except urllib.error.HTTPError as err:
        detail = err.read().decode()[:200]
        print(f"  REVIEW PR #{input.number}: FAILED {err.code} {detail}")
        return PostReviewResult(number=input.number, posted=False, event=event, message=f"{err.code} {detail}")


@activity.defn
async def merge_pull_request(input: MergeInput) -> MergeResult:
    """Merge an approved pull request via the GitHub API. This is how the
    pipeline closes the loop after the review lane signs off."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("merge_pull_request requires GITHUB_TOKEN in the worker env")
    body: dict = {"merge_method": input.method}
    if input.commit_headline:
        body["commit_title"] = input.commit_headline
    try:
        _, data = _gh_put(f"/repos/{input.repo}/pulls/{input.number}/merge", token, body)
        merged = bool(data.get("merged"))
        print(f"  MERGE PR #{input.number}: {'merged' if merged else 'not merged'} {data.get('sha', '')}")
        return MergeResult(
            number=input.number,
            merged=merged,
            sha=data.get("sha", ""),
            message=data.get("message", ""),
        )
    except urllib.error.HTTPError as err:
        detail = err.read().decode()[:200]
        print(f"  MERGE PR #{input.number}: FAILED {err.code} {detail}")
        # 405 = "Pull Request has merge conflicts" (branch is stale vs base).
        return MergeResult(number=input.number, merged=False,
                           message=f"{err.code} {detail}", conflict=(err.code == 405))


# --- agent-resolves-conflict escalation ------------------------------------


def _issue_number_from_branch(branch: str) -> int | None:
    """Recover the issue number a PR branch was cut for (claude/issue-<n>)."""
    match = re.search(r"issue-(\d+)", branch or "")
    return int(match.group(1)) if match else None


def _resolve_prompt(repo: str, pr_number: int, branch: str, base: str, team: str) -> str:
    return f"""A pull request has a merge conflict that must be resolved automatically.

Repo: {repo}
PR: #{pr_number}
Branch (already checked out in your workspace): {branch}
Base branch: {base}
Team lane: {team}

`{branch}` conflicts with `{base}` and cannot be merged. Resolve it end to end:

1. Merge the base branch into your branch: `git merge origin/{base}`.
2. Resolve every conflict by hand. Open each conflicted file and keep BOTH the
   base's changes and this branch's intent — do not clobber either side — then
   remove all conflict markers.
3. Run the project's tests / checks and make them pass. Fix anything the merge
   broke.
4. Commit the resolution: `git add -A` then `git commit`. Do NOT push — the
   harness pushes the branch and re-merges the PR for you.
5. Write REPORT.md and return the required structured output. Set tests_passed
   to whether the tests actually pass after the resolution.

Use the installed team skills. Keep the change minimal and correct.
"""


@activity.defn
async def escalate_conflict(input: ConflictEscalationInput) -> ConflictEscalationResult:
    """A PR branch has a real content conflict with base that the automatic
    branch-update can't fix. Loop the owning team's agent back in: start a
    ``resolve-pr-<n>`` RunClaudeTask on that team's namespace/queue. The agent
    merges base, fixes the conflict, and tests; its post-completion pushes the
    branch and re-merges the PR — fully autonomous.

    The owning team is read from the issue the branch was cut for. A deterministic
    workflow ID + ALLOW_DUPLICATE_FAILED_ONLY make a re-escalation a no-op while the resolve
    job is already running (or has run)."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("escalate_conflict requires GITHUB_TOKEN in the worker env")

    issue_number = _issue_number_from_branch(input.branch)
    team = "issues"
    if issue_number is not None:
        try:
            issue = _gh_get(f"/repos/{input.repo}/issues/{issue_number}", token)
            team = team_for_labels(_labels(issue))
        except urllib.error.HTTPError as err:
            print(f"  ESCALATE PR #{input.pr_number}: can't read issue #{issue_number} ({err.code}); default team")

    source = f"resolve-pr-{input.pr_number}"
    workflow_id = f"claude-{team}-{source}"
    task_input = TaskInput(
        task=_resolve_prompt(input.repo, input.pr_number, input.branch, input.base, team),
        team=team,
        model=input.model,
        repo=input.repo,
        branch=input.branch,
        source=source,
        pr_number=input.pr_number,
        base_branch=input.base,
    )

    # Lazy import keeps this module free of a workflows<->poller import cycle.
    from workflows import RunClaudeTask

    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace_for_team(team))
    try:
        await client.start_workflow(
            RunClaudeTask.run,
            task_input,
            id=workflow_id,
            task_queue=task_queue_for_team(team),
            # Idempotent against running/completed work, but a FAILED
            # attempt may retry on a later sweep — REJECT_DUPLICATE
            # deadlocked an issue forever after one transient failure.
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
        )
    except WorkflowAlreadyStartedError:
        print(f"  ESCALATE PR #{input.pr_number}: resolve job {workflow_id} already running")
        return ConflictEscalationResult(started=False, workflow_id=workflow_id, team=team,
                                        message="resolve job already running")

    # Best-effort visibility on the PR itself — never fail the escalation for it.
    try:
        _gh_post(
            f"/repos/{input.repo}/issues/{input.pr_number}/comments",
            token,
            {"body": f"🔧 `{input.branch}` conflicts with `{input.base}`. Handed to the "
                     f"**{team}** lane to resolve automatically (`{workflow_id}`); "
                     f"it will re-merge once the conflict is fixed and tests pass."},
        )
    except urllib.error.HTTPError:
        pass

    print(f"  ESCALATE PR #{input.pr_number}: started resolve job {workflow_id} on team {team}")
    return ConflictEscalationResult(started=True, workflow_id=workflow_id, team=team,
                                    message="resolve job started")


# --- review-driven fix loop -------------------------------------------------


@activity.defn
async def read_pr_review_state(repo: str, pr_number: int) -> HumanReviewState:
    """The latest *human* review on a PR. Our own bot only ever posts COMMENT
    reviews (never CHANGES_REQUESTED / APPROVED), so any CHANGES_REQUESTED state
    is necessarily a human asking for changes — the fix-loop trigger. COMMENTED
    reviews are ignored; the latest APPROVED/CHANGES_REQUESTED wins."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("read_pr_review_state requires GITHUB_TOKEN in the worker env")
    try:
        reviews = _gh_get(f"/repos/{repo}/pulls/{pr_number}/reviews?per_page=100", token)
    except urllib.error.HTTPError as err:
        print(f"  REVIEW-STATE PR #{pr_number}: can't read reviews ({err.code}); assuming none")
        return HumanReviewState()
    latest = HumanReviewState()
    for review in reviews:
        state = (review.get("state") or "").upper()
        if state in ("CHANGES_REQUESTED", "APPROVED"):  # decisive states only
            latest = HumanReviewState(
                state=state,
                body=(review.get("body") or "").strip(),
                reviewer=((review.get("user") or {}).get("login") or ""),
            )
    return latest


def _fix_prompt(repo: str, pr_number: int, branch: str, base: str, team: str,
                feedback: str, fix_round: int, max_rounds: int) -> str:
    return f"""A pull request was not approved and must be fixed automatically (fix round {fix_round} of {max_rounds}).

Repo: {repo}
PR: #{pr_number}
Branch (already checked out in your workspace): {branch}
Base branch: {base}
Team lane: {team}

The review did not pass. Address this feedback end to end:

--- review feedback ---
{feedback or "(the test suite failed; make it pass)"}
-----------------------

1. Read the feedback and the failing tests. Make the change that fixes them.
2. Run the project's tests / checks and make them pass — this is the validation
   step, do not skip it.
3. Commit the fix: `git add -A` then `git commit`. Do NOT push — the harness
   pushes the branch, then re-reviews the PR and re-asks the human.
4. Write REPORT.md and return the required structured output. Set tests_passed
   to whether the tests actually pass after your fix.

Use the installed team skills. Keep the change minimal and correct; do not
touch anything the feedback did not ask about.
"""


@activity.defn
async def escalate_fix(input: FixEscalationInput) -> FixEscalationResult:
    """A PR was not approved (red suite, or a human Request-Changes review, or a
    human gate denial with a note). Loop the owning team's agent back in: start a
    ``fix-pr-<n>-r<k>`` RunClaudeTask on that team's namespace/queue that fixes
    the feedback, re-runs the tests, and pushes. Its post-completion re-reviews
    the PR and re-asks the human. Deterministic ID + ALLOW_DUPLICATE_FAILED_ONLY make a
    re-escalation of the same round a no-op."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("escalate_fix requires GITHUB_TOKEN in the worker env")

    issue_number = _issue_number_from_branch(input.branch)
    team = "issues"
    if issue_number is not None:
        try:
            issue = _gh_get(f"/repos/{input.repo}/issues/{issue_number}", token)
            team = team_for_labels(_labels(issue))
        except urllib.error.HTTPError as err:
            print(f"  FIX PR #{input.pr_number}: can't read issue #{issue_number} ({err.code}); default team")

    source = f"fix-pr-{input.pr_number}-r{input.fix_round}"
    workflow_id = f"claude-{team}-{source}"
    task_input = TaskInput(
        task=_fix_prompt(input.repo, input.pr_number, input.branch, input.base, team,
                         input.feedback, input.fix_round, input.max_fix_rounds),
        team=team,
        model=input.model,
        repo=input.repo,
        branch=input.branch,
        source=source,
        pr_number=input.pr_number,
        base_branch=input.base,
        enable_fix_loop=True,
        max_fix_rounds=input.max_fix_rounds,
        require_approval=input.require_approval,
        approval_timeout_h=input.approval_timeout_h,
        fix_round=input.fix_round,
    )

    from workflows import RunClaudeTask

    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace_for_team(team))
    try:
        await client.start_workflow(
            RunClaudeTask.run,
            task_input,
            id=workflow_id,
            task_queue=task_queue_for_team(team),
            # Idempotent against running/completed work, but a FAILED
            # attempt may retry on a later sweep — REJECT_DUPLICATE
            # deadlocked an issue forever after one transient failure.
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
        )
    except WorkflowAlreadyStartedError:
        print(f"  FIX PR #{input.pr_number}: fix job {workflow_id} already running")
        return FixEscalationResult(started=False, workflow_id=workflow_id, team=team,
                                   fix_round=input.fix_round, message="fix job already running")

    try:
        _gh_post(
            f"/repos/{input.repo}/issues/{input.pr_number}/comments",
            token,
            {"body": f"🔧 Review did not pass. Handed to the **{team}** lane to fix "
                     f"automatically (round {input.fix_round}/{input.max_fix_rounds}, "
                     f"`{workflow_id}`); it will re-run the tests, push, and re-ask for approval."},
        )
    except urllib.error.HTTPError:
        pass

    print(f"  FIX PR #{input.pr_number}: started fix job {workflow_id} (round {input.fix_round}) on team {team}")
    return FixEscalationResult(started=True, workflow_id=workflow_id, team=team,
                               fix_round=input.fix_round, message="fix job started")


def _followup_review_prompt(repo: str, pr_number: int, branch: str, fix_round: int) -> str:
    return f"""Re-review pull request #{pr_number} after fix round {fix_round}.

Repo: {repo}
PR: #{pr_number}
Branch (already checked out in your workspace): {branch}
Team lane: review

A fix was just pushed to this PR. Inspect the diff with `git diff main...HEAD`
and run the project's tests. Use the pr-review, self-review, and testing-bar
skills, and write REPORT.md.

If the change is now correct, safe, and its tests pass, **set tests_passed=true**
— this approves and (behind the human gate) merges the PR. Only set
tests_passed=false if a real blocking problem remains (list it first with a
concrete file/line reference). Return the required structured output.
"""


@activity.defn
async def escalate_review(input: ReviewEscalationInput) -> ReviewEscalationResult:
    """A fix job finished and pushed. Start the follow-up review job on the
    review lane that re-runs the suite and re-asks the human. The mirror image
    of ``escalate_fix``; deterministic ID + ALLOW_DUPLICATE_FAILED_ONLY keep it idempotent."""
    team = "review"
    source = f"pr-{input.pr_number}-r{input.fix_round}"
    workflow_id = f"claude-{team}-{source}"
    task_input = TaskInput(
        task=_followup_review_prompt(input.repo, input.pr_number, input.branch, input.fix_round),
        team=team,
        model=input.model,
        repo=input.repo,
        branch=input.branch,
        source=source,
        pr_number=input.pr_number,
        base_branch=input.base,
        require_approval=input.require_approval,
        approval_timeout_h=input.approval_timeout_h,
        enable_fix_loop=input.enable_fix_loop,
        max_fix_rounds=input.max_fix_rounds,
        fix_round=input.fix_round,
    )

    from workflows import RunClaudeTask

    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace_for_team(team))
    try:
        await client.start_workflow(
            RunClaudeTask.run,
            task_input,
            id=workflow_id,
            task_queue=task_queue_for_team(team),
            # Idempotent against running/completed work, but a FAILED
            # attempt may retry on a later sweep — REJECT_DUPLICATE
            # deadlocked an issue forever after one transient failure.
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
        )
    except WorkflowAlreadyStartedError:
        print(f"  RE-REVIEW PR #{input.pr_number}: review job {workflow_id} already running")
        return ReviewEscalationResult(started=False, workflow_id=workflow_id,
                                      fix_round=input.fix_round, message="review job already running")

    print(f"  RE-REVIEW PR #{input.pr_number}: started review job {workflow_id} (round {input.fix_round})")
    return ReviewEscalationResult(started=True, workflow_id=workflow_id,
                                  fix_round=input.fix_round, message="review job started")


# --- the Temporal-native poll (activity; workflow lives in workflows.py) ----


async def _connect(namespace: str) -> Client:
    return await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)


@activity.defn
async def poll_github_activity(input: PollInput) -> PollSummary:
    """Run one poll from inside Temporal. Token comes from the worker's env."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("poll_github_activity requires GITHUB_TOKEN in the worker env")
    connect = None if input.dry_run else _connect
    review_cfg = {
        "enable_fix_loop": input.enable_fix_loop,
        "max_fix_rounds": input.max_fix_rounds,
        "require_approval": input.require_approval,
        "approval_timeout_h": input.approval_timeout_h,
    }
    return await run_poll(connect, input.repo, token, model=input.model,
                          dry_run=input.dry_run, review_cfg=review_cfg)


# --- CLI -------------------------------------------------------------------


async def _create_schedule(client, input: PollInput, interval: int, schedule_id: str) -> None:
    from workflows import PollGitHubWorkflow

    action = ScheduleActionStartWorkflow(
        PollGitHubWorkflow.run,
        input,
        id=f"{schedule_id}-run",
        task_queue=POLLER_TASK_QUEUE,
    )
    spec = ScheduleSpec(intervals=[ScheduleIntervalSpec(every=timedelta(seconds=interval))])
    try:
        await client.create_schedule(schedule_id, Schedule(action=action, spec=spec))
        print(f"created schedule '{schedule_id}': poll {input.repo} every {interval}s on {POLLER_TASK_QUEUE}")
    except Exception as err:  # already exists / RPC error
        print(f"could not create schedule '{schedule_id}': {err}")
        print("(delete it first with: temporal schedule delete --schedule-id " + schedule_id + ")")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Poll GitHub and submit Temporal Claude jobs")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"),
                        help="owner/name (default: $GITHUB_REPOSITORY)")
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE, help="Temporal namespace")
    parser.add_argument("--model", default=None,
                        help="Agent model alias for submitted jobs (e.g. fable, sonnet, opus)")
    parser.add_argument("--schedule", action="store_true",
                        help="Create a Temporal Schedule that runs the poll on Temporal (recommended)")
    parser.add_argument("--schedule-id", default="github-poller", help="Schedule ID to create")
    parser.add_argument("--once", action="store_true",
                        help="Run a single poll locally and exit (default; handy for cron)")
    parser.add_argument("--loop", action="store_true", help="Poll repeatedly, locally")
    parser.add_argument("--interval", type=int, default=300,
                        help="Seconds between polls (schedule + --loop; default 300)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Route work but submit nothing (no Temporal needed)")
    args = parser.parse_args()

    if not args.repo:
        parser.error("provide --repo owner/name or set GITHUB_REPOSITORY")

    poll_input = PollInput(repo=args.repo, namespace=args.namespace, model=args.model, dry_run=args.dry_run)

    # Schedule mode: register the poll on Temporal, then exit.
    if args.schedule:
        client = await Client.connect(TEMPORAL_ADDRESS, namespace=args.namespace)
        await _create_schedule(client, poll_input, args.interval, args.schedule_id)
        return

    # Local modes: run the poll here (no worker needed).
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not token:
        parser.error("set GITHUB_TOKEN (or GH_TOKEN) to read the GitHub API")
    connect = None if args.dry_run else _connect

    try:
        while True:
            try:
                await run_poll(connect, args.repo, token, model=args.model, dry_run=args.dry_run)
            except urllib.error.HTTPError as err:
                print(f"github error: {err.code} {err.reason}")
            if not args.loop:
                return
            await asyncio.sleep(args.interval)
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    asyncio.run(main())
