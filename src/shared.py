"""Shared types between the workflow, activity, worker, and client."""

from dataclasses import dataclass, field
import os
import re
from pathlib import Path
from typing import Any

# Env-overridable so the same image runs locally (localhost) and on GCP
# (e.g. temporal:7233 in compose, or a Temporal Cloud endpoint).
TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
DEFAULT_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
BASE_TASK_QUEUE = "claude-code-tasks"
DEFAULT_TEAM = "backend"
# Dedicated task queue for the GitHub poll workflow/activity (see poller.py).
POLLER_TASK_QUEUE = "claude-code-poller"

# Teams are DISCOVERED from teams/<team>/ folders — each folder is owned by an
# engineering team and is self-sufficient (mandate, skills, settings, rules,
# hook, OWNERS). Adding a team = adding a folder; no central edit required.
TEAMS_DIR = Path(__file__).resolve().parents[1] / "teams"


def known_teams() -> tuple[str, ...]:
    """The teams that exist: one folder each under teams/. Falls back to the
    legacy profile keys if the folders are unavailable (e.g. odd cwd)."""
    try:
        found = tuple(sorted(
            d.name for d in TEAMS_DIR.iterdir()
            if d.is_dir() and (d / "CLAUDE.md").exists()
        ))
        if found:
            return found
    except OSError:
        pass
    return (DEFAULT_TEAM,)


# The org-wide policy FLOOR: every team may extend its own settings.json but
# these denies are non-negotiable and validated by teams/validate.py + tests.
ORG_FLOOR_DENY: tuple[str, ...] = ("Bash(rm -rf:*)", "Bash(sudo:*)", "Bash(git push:*)")



def normalize_team(team: str | None) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", (team or DEFAULT_TEAM).lower()).strip("-")
    return normalized or DEFAULT_TEAM


def task_queue_for_team(team: str | None) -> str:
    return f"{BASE_TASK_QUEUE}-{normalize_team(team)}"


def model_for_chunk(input: "TaskInput", chunk: int, escalated: bool = False) -> str | None:
    """Which model a given chunk runs on. Pure function of replayed state, so
    the workflow can call it deterministically: the ladder escalates the brain
    while the durable session carries the memory. `escalated` is the governor's
    flag-pressure override — once true, the ladder has already been climbed."""
    if input.escalate_model and (escalated or chunk >= input.escalate_after_chunks):
        return input.escalate_model
    return input.model


def unanimous_failures(per_candidate_failures: list[set[str]]) -> set[str]:
    """The unanimity rule, from the conversation-tree experiment: tests that
    EVERY candidate implementation failed. With two or more diverse candidates,
    a unanimous failure indicts the referee (the shared test), not the players
    — the signal self-graded best-of-N structurally cannot produce. Pure, so
    tournament runners and workflows alike can apply it."""
    if len(per_candidate_failures) < 2:
        return set()
    common = set(per_candidate_failures[0])
    for failures in per_candidate_failures[1:]:
        common &= failures
    return common


def corrective_instruction(flags: dict[str, int]) -> str | None:
    """The governor's self-steer: turn one chunk's rule flags into a corrective
    instruction for the next chunk. Pure, so the workflow can build it during
    replay. Returns None when there is nothing to correct."""
    if not flags:
        return None
    listed = ", ".join(f"{name} ×{count}" for name, count in sorted(flags.items()))
    return (
        "The workspace policy hooks flagged rule violations in your previous "
        f"turns: {listed}. Stop the flagged pattern immediately: trust your tool "
        "results, do not re-check finished work, and stay within your lane's "
        "discipline."
    )


def namespace_for_team(team: str | None) -> str:
    """Each team lane runs in its own Temporal namespace (backend issues in the
    ``backend`` namespace, review jobs in ``review``, etc.) — not all in
    ``default``. The namespaces are created declaratively by temporal-init."""
    return normalize_team(team)


@dataclass
class ApprovalDecision:
    """A human's answer to an open gate. Arrives as a workflow UPDATE, so it is
    validated before it is recorded and the caller gets a definitive result —
    the difference between a decision and a suggestion (a signal)."""

    approved: bool
    decided_by: str = ""
    note: str = ""


@dataclass
class TaskInput:
    task: str
    # Team profile controls the task queue and workspace skill bundle.
    team: str = DEFAULT_TEAM
    # How many resume-chunks to allow before giving up.
    max_chunks: int = 8
    # Agentic turns per completed activity chunk. In-flight session IDs are
    # also heartbeated for cheaper activity-retry recovery.
    max_turns_per_chunk: int = 40
    # Claude model alias/ID for the agent runs; None = Claude Code's default.
    model: str | None = None
    # Model-escalation ladder: when set, chunks numbered >= escalate_after_chunks
    # run on this model instead of `model`. The session ID keeps chaining, so the
    # stronger model resumes the same conversation — same skills, same policy,
    # only the brain changes. None = ladder disabled.
    escalate_model: str | None = None
    escalate_after_chunks: int = 3
    # Flag-pressure escalation: once the workspace rule hooks have flagged this
    # many violations across the run, the governor escalates immediately instead
    # of waiting for the chunk threshold (requires escalate_model). None = only
    # the chunk-count threshold escalates.
    escalate_on_flags: int | None = None
    # If set (owner/name), the activity clones this repo into the workspace and
    # works on `branch` before the agent starts. None = empty scratch workspace.
    repo: str | None = None
    branch: str | None = None
    # Human gate: when True, the outward irreversible act (the merge) blocks on
    # a validated human decision (workflow update), with a deadline. On
    # timeout the gate DENIES — the safe default for an unattended system.
    require_approval: bool = False
    approval_timeout_h: float = 24.0
    # What this job is: "issue-<n>" or "pr-<n>". Drives the post-completion step
    # (open a PR for issue lanes; post review + merge for the review lane).
    source: str | None = None
    # For review-lane jobs: the PR number being reviewed (and merged on approve).
    pr_number: int | None = None
    # Base branch that opened PRs target.
    base_branch: str = "main"
    # Review-driven fix loop: when enabled, a not-approved PR (red suite, or a
    # human "Request Changes" review) starts a fix job in the owning lane that
    # implements the fix, re-runs the tests, and pushes — which re-reviews and
    # re-asks the human. Bounded by max_fix_rounds, then it stops and awaits a
    # human. Off by default, like the gate.
    enable_fix_loop: bool = False
    max_fix_rounds: int = 3
    # For fix-lane jobs: which round this is, and the failing tests + human
    # comments the fix must address (folded into the agent's prompt).
    fix_round: int = 0
    review_feedback: str = ""


@dataclass
class ChunkInput:
    prompt: str
    max_turns_per_chunk: int
    team: str = DEFAULT_TEAM
    # Session to resume; None on the first chunk.
    session_id: str | None = None
    model: str | None = None
    # Repo to clone into the workspace before the agent runs (owner/name), and
    # the branch to work on. None = empty scratch workspace (original behavior).
    repo: str | None = None
    branch: str | None = None


@dataclass
class ChunkResult:
    session_id: str
    # "success" | "error_max_turns" | "error_during_execution" | ...
    subtype: str
    # Final text from Claude — only populated on success.
    text: str
    cost_usd: float
    num_turns: int
    work_dir: str
    errors: list[str] = field(default_factory=list)
    # Schema-validated report (see REPORT_SCHEMA) — only populated on success.
    structured: dict[str, Any] | None = None
    # This chunk's workspace rule violations, tallied by rule name from the
    # flag hook's log. Typed data: the workflow's governor reads it.
    rule_flags: dict[str, int] = field(default_factory=dict)
    # Which model actually ran this chunk — evidence for the escalation ladder.
    model: str | None = None


@dataclass
class TranscriptExportInput:
    session_id: str
    work_dir: str


@dataclass
class TranscriptExportResult:
    markdown_path: str
    source_jsonl_path: str
    event_count: int


@dataclass
class TaskProgress:
    team: str = DEFAULT_TEAM
    chunks_completed: int = 0
    total_cost_usd: float = 0.0
    session_id: str | None = None
    done: bool = False
    steer_count: int = 0
    # Governor state, queryable mid-run: cumulative rule violations the hooks
    # flagged, corrective self-steers issued, and whether flag pressure has
    # already climbed the model ladder.
    rule_flags_total: int = 0
    governor_steers: int = 0
    escalated: bool = False
    # Human-gate state, queryable mid-run: what (if anything) the workflow is
    # blocked on, and the decision that closed the last gate.
    awaiting_approval: bool = False
    approval: ApprovalDecision | None = None
    # Review-driven fix loop: which fix round this job belongs to (0 = the
    # original review), so the loop's depth is queryable and cap-bounded.
    fix_round: int = 0


@dataclass
class TaskResult:
    done: bool
    result_text: str
    work_dir: str
    chunks: int
    total_cost_usd: float
    team: str = DEFAULT_TEAM
    session_id: str | None = None
    report: dict[str, Any] | None = None


@dataclass
class CanaryReport:
    """One economics-canary pass: per-probe measurements, band verdicts."""

    ts: float
    passed: bool
    alerts: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    probes: dict[str, Any] = field(default_factory=dict)


@dataclass
class PollInput:
    """Input to one GitHub poll (the scheduled PollGitHubWorkflow)."""

    repo: str
    namespace: str = DEFAULT_NAMESPACE
    # Model alias applied to every job this poll submits (None = CC default).
    model: str | None = None
    # Route and count work but submit nothing.
    dry_run: bool = False
    # Review-lane policy applied to the PRs this poll routes: when enabled, a
    # not-approved PR starts the fix loop, and the merge waits on a human gate.
    # Off by default preserves the current autonomous behavior.
    enable_fix_loop: bool = False
    max_fix_rounds: int = 3
    require_approval: bool = False
    approval_timeout_h: float = 24.0


@dataclass
class PollSummary:
    """What one poll saw and did — returned by the workflow/activity."""

    open_issues: int = 0
    open_prs: int = 0
    planned: int = 0
    started: int = 0
    held: int = 0
    started_ids: list[str] = field(default_factory=list)
    # PR numbers that are approved + mergeable — the poll workflow merges these.
    to_merge: list[int] = field(default_factory=list)


@dataclass
class MergeInput:
    """Input to the merge_pull_request activity."""

    repo: str
    number: int
    method: str = "squash"  # squash | merge | rebase
    commit_headline: str = ""


@dataclass
class MergeResult:
    number: int
    merged: bool
    sha: str = ""
    message: str = ""
    # True when the merge was refused because the branch conflicts with base
    # (HTTP 405) — the signal to try updating the branch and re-merging.
    conflict: bool = False


@dataclass
class UpdateBranchInput:
    """Bring a stale PR branch up to date by merging base into it."""

    repo: str
    branch: str
    number: int
    base: str = "main"


@dataclass
class UpdateBranchResult:
    updated: bool         # base merged into the branch cleanly + pushed
    conflict: bool        # a real content conflict — needs manual/agent resolution
    message: str = ""


@dataclass
class ConflictEscalationInput:
    """Escalate a real content conflict: start a resolve job on the owning team."""

    repo: str
    pr_number: int
    branch: str
    base: str = "main"
    model: str | None = None


@dataclass
class ConflictEscalationResult:
    """What the escalate_conflict activity did — start a resolve job (or not)."""

    started: bool
    workflow_id: str = ""
    team: str = ""
    message: str = ""


@dataclass
class HumanReviewState:
    """The latest human (non-bot) review on a PR, read from GitHub. `state` is
    the GitHub review state: CHANGES_REQUESTED, APPROVED, COMMENTED, or "" when
    no human has reviewed. Only CHANGES_REQUESTED triggers a fix."""

    state: str = ""
    body: str = ""
    reviewer: str = ""

    @property
    def requests_changes(self) -> bool:
        return self.state == "CHANGES_REQUESTED"


@dataclass
class FixEscalationInput:
    """Escalate a not-approved PR (red suite or human Request-Changes): start a
    fix job on the owning team that implements the fix, re-tests, and pushes."""

    repo: str
    pr_number: int
    branch: str
    feedback: str          # failing tests + human comments the fix must address
    fix_round: int         # the round this fix will run as (1-based)
    base: str = "main"
    model: str | None = None
    require_approval: bool = False
    approval_timeout_h: float = 24.0
    max_fix_rounds: int = 3


@dataclass
class FixEscalationResult:
    """What the escalate_fix activity did — start a fix job (or not)."""

    started: bool
    workflow_id: str = ""
    team: str = ""
    fix_round: int = 0
    message: str = ""


@dataclass
class ReviewEscalationInput:
    """A fix job finished: start the follow-up review job (review lane) that
    re-runs the suite and re-asks the human. The other half of escalate_fix."""

    repo: str
    pr_number: int
    branch: str
    fix_round: int         # the round just completed; the review runs at it
    base: str = "main"
    model: str | None = None
    require_approval: bool = False
    approval_timeout_h: float = 24.0
    enable_fix_loop: bool = True
    max_fix_rounds: int = 3


@dataclass
class ReviewEscalationResult:
    started: bool
    workflow_id: str = ""
    fix_round: int = 0
    message: str = ""


@dataclass
class PushBranchInput:
    """Commit + push the current work_dir onto its branch (updates the PR)."""

    repo: str
    branch: str
    work_dir: str


@dataclass
class PushBranchResult:
    pushed: bool
    message: str = ""


@dataclass
class OpenPRInput:
    """Input to open_pull_request: commit + push the branch, open a PR."""

    repo: str
    branch: str
    work_dir: str
    issue_number: int
    title: str
    base: str = "main"


@dataclass
class OpenPRResult:
    opened: bool
    number: int = 0
    url: str = ""
    message: str = ""


@dataclass
class PostReviewInput:
    """Input to post_pr_review: post a GitHub PR review from the review lane."""

    repo: str
    number: int
    approve: bool
    body: str = ""


@dataclass
class PostReviewResult:
    number: int
    posted: bool
    event: str = ""  # APPROVE | REQUEST_CHANGES | COMMENT
    message: str = ""

