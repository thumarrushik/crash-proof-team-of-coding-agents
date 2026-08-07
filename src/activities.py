"""The one activity: run a bounded chunk of a headless Claude Code session.

Each chunk is capped at ``max_turns_per_chunk`` agentic turns. When Claude runs
out of turns mid-task the result subtype is ``error_max_turns``; the workflow
then schedules another chunk that resumes the same session. Completed chunks
are workflow-visible checkpoints. During a chunk, heartbeat details also carry
Claude's in-flight session ID so an activity retry can resume the same session
even if the worker dies before the chunk returns.

The workspace is bootstrapped with its own ``.claude/`` project config, so the
agent runs under *workspace-owned* policy rather than whatever is on the worker
machine: a settings.json with deny rules and a PostToolUse audit hook, and a
``final-report`` skill the agent invokes when asked for a report.
"""

import asyncio
import json
import os
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Sequence

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage, SystemMessage
from temporalio import activity
from temporalio.exceptions import ApplicationError

from shared import (
    ChunkInput,
    ChunkResult,
    OpenPRInput,
    OpenPRResult,
    PushBranchInput,
    PushBranchResult,
    DEFAULT_TEAM,
    TranscriptExportInput,
    TranscriptExportResult,
    UpdateBranchInput,
    UpdateBranchResult,
    normalize_team,
)

# Workspace scratch that must never land in a pushed branch/PR.
_PR_EXCLUDE = "\n".join([
    ".claude/", "CLAUDE.md", "REPORT.md",
    "usage-log.jsonl", "recovery-log.jsonl", "hook-log.jsonl", "audit/",
]) + "\n"

# Every chunk must end with a schema-validated status report. On success the
# SDK returns it in ResultMessage.structured_output.
REPORT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "files_created": {"type": "array", "items": {"type": "string"}},
            "tests_passed": {"type": "boolean"},
        },
        "required": ["summary", "files_created", "tests_passed"],
        "additionalProperties": False,
    },
}



# Workspace-owned policy: destructive commands denied even though Bash is
# allowed; every tool call is appended to an audit log by a `*` PostToolUse hook
# (the hook receives the event as JSON on stdin; `cat` persists it); and a second
# `*` PostToolUse hook checks every call against the lane's rules.json.

def _log_usage(work_dir: Path, message) -> None:
    """Append this chunk's token/cost breakdown to usage-log.jsonl. Used to
    measure the economics of chunked resume (cache reads vs fresh input vs
    output). Best-effort — never fails the chunk."""
    try:
        usage = getattr(message, "usage", None)
        if not isinstance(usage, dict):
            usage = {}
        row = {
            "ts": time.time(),
            "session_id": message.session_id,
            "subtype": message.subtype,
            "num_turns": message.num_turns,
            "cost_usd": message.total_cost_usd or 0.0,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        }
        with (work_dir / "usage-log.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def _count_rule_flags(work_dir: Path) -> int:
    """Lines already in the flag log (previous chunks of this workspace)."""
    try:
        with (work_dir / ".claude" / "rule-flags.jsonl").open() as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


def _read_rule_flags(work_dir: Path, skip: int) -> dict[str, int]:
    """Tally the flags the rules hook appended after line `skip` — i.e. this
    chunk's violations, by rule name. This is how hook verdicts become typed
    data the workflow can act on."""
    flags: dict[str, int] = {}
    try:
        with (work_dir / ".claude" / "rule-flags.jsonl").open() as f:
            for i, line in enumerate(f):
                if i < skip:
                    continue
                try:
                    name = json.loads(line).get("rule", "unknown")
                except Exception:
                    name = "unknown"
                flags[name] = flags.get(name, 0) + 1
    except FileNotFoundError:
        pass
    return flags


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    """Best-effort local evidence log; never fails the activity."""
    try:
        with path.open("a") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def _session_id_from_heartbeat(details: Sequence[Any]) -> str | None:
    """Recover the latest in-flight Claude session ID from heartbeat details.

    Activity retries receive the last heartbeat details from the failed attempt.
    Capturing Claude's init session ID there lets a retry resume the in-flight
    session even if the activity died before returning a completed chunk result.
    """
    for detail in reversed(details):
        if not isinstance(detail, dict):
            continue
        session_id = detail.get("session_id")
        if isinstance(session_id, str) and session_id:
            return session_id
    return None




def _write_team_memory(work_dir: Path, claude_dir: Path, team: str, installed: dict[str, str]) -> None:
    """The workspace memory IMPORTS the live team mandate (teams/<team>/CLAUDE.md)
    rather than copying it — the owning team's edits reach the next chunk with no
    re-stamp. Only the task-local appendix is written here."""
    repo_root = Path(__file__).resolve().parents[1]
    mandate_file = repo_root / "teams" / team / "CLAUDE.md"
    if not mandate_file.exists():
        mandate_file = repo_root / "teams" / DEFAULT_TEAM / "CLAUDE.md"
    skills = "\n".join(f"- {name}: {source}" for name, source in installed.items())
    memory = (
        f"Team: `{team}` — this workspace is bound to its owning team's folder.\n\n"
        f"@{mandate_file}\n\n"
        f"## Installed skills (this worker)\n\n{skills}\n"
    )
    (work_dir / "CLAUDE.md").write_text(memory)
    (claude_dir / "CLAUDE.md").write_text(memory)


def _bootstrap_workspace(work_dir: Path, team: str) -> None:
    """Write the workspace-owned .claude/ config. Idempotent — runs every chunk
    so retries and resumed chunks always see the same policy."""
    team = normalize_team(team)
    claude_dir = work_dir / ".claude"
    skills_dir = claude_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    # BINDING, not copying: the task checks out into the team, the team is
    # never photocopied into the task.
    #   knowledge (mandate, skills)  -> bound LIVE to teams/<team>/ (an @import
    #       and a symlink), so the owning team's edits reach the very next chunk
    #   policy (settings, rules, hook) -> STAMPED per chunk on purpose: an
    #       immutable snapshot the agent can scribble on but never keep — and
    #       the stamp injects absolute-path denies so nothing in the workspace
    #       can write through into the teams/ source itself.
    repo_root = Path(__file__).resolve().parents[1]
    team_dir = repo_root / "teams" / team
    if not team_dir.is_dir():
        team_dir = repo_root / "teams" / DEFAULT_TEAM
    team_claude = team_dir / ".claude"

    # -- policy: stamp, with deployment-specific source protection injected --
    settings = json.loads((team_claude / "settings.json").read_text())
    deny = settings.setdefault("permissions", {}).setdefault("deny", [])
    for guard in (f"Write(//{team_dir.parent}/**)", f"Edit(//{team_dir.parent}/**)"):
        if guard not in deny:
            deny.append(guard)
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))
    for name in ("flag-rules.py", "rules.json", "phase-gate.py"):
        (claude_dir / name).write_text((team_claude / name).read_text())
    # Fresh chunk, fresh deadlock budget: without this, a run that burned its
    # 3 phase-gate blocks leaves every later chunk with a disarmed gate.
    (claude_dir / "phase-gate-blocks").unlink(missing_ok=True)

    # -- knowledge: bind live --
    ws_skills = claude_dir / "skills"
    if ws_skills.is_symlink() or ws_skills.is_file():
        ws_skills.unlink()
    elif ws_skills.is_dir():
        shutil.rmtree(ws_skills)
    ws_skills.symlink_to(team_claude / "skills", target_is_directory=True)

    installed = {d.name: f"live:{d}" for d in sorted((team_claude / "skills").iterdir())
                 if (d / "SKILL.md").exists()}
    _write_team_memory(work_dir, claude_dir, team, installed)


async def _git(args: list[str], cwd: str | None = None) -> tuple[int, str]:
    """Run one git command, returning (exit_code, combined_output)."""
    proc = await asyncio.create_subprocess_exec(
        "git", *args, cwd=cwd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return proc.returncode or 0, out.decode(errors="replace")


async def _prepare_repo(work_dir: Path, repo: str | None, branch: str | None) -> None:
    """Clone `repo` into the workspace and check out `branch`, before the agent
    runs — so it works on the real codebase, not an empty scratch dir.

    Idempotent: a retried/resumed chunk finds `.git` already present and skips
    the clone (the workspace is keyed by workflow ID, so it is stable). Uses
    GITHUB_TOKEN from the worker env for private repos; the token is scrubbed
    from any surfaced error text.
    """
    if not repo or (work_dir / ".git").exists():
        return
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    auth = f"x-access-token:{token}@" if token else ""
    code, out = await _git(["clone", f"https://{auth}github.com/{repo}.git", str(work_dir)])
    if code != 0:
        safe = out.replace(token, "***") if token else out
        raise ApplicationError(
            f"git clone failed for {repo}: {safe[-400:]}",
            type="GitCloneError", non_retryable=False,
        )
    # Scrub the token out of origin so the agent can't read it from .git/config;
    # the push in open_pull_request supplies auth explicitly.
    await _git(["remote", "set-url", "origin", f"https://github.com/{repo}.git"], cwd=str(work_dir))
    if branch:
        # Review jobs check out the PR's existing branch; issue jobs create a new
        # one off the default branch.
        code, _ = await _git(["checkout", branch], cwd=str(work_dir))
        if code != 0:
            await _git(["checkout", "-B", branch], cwd=str(work_dir))
    await _git(["config", "user.email", "claude-agent@users.noreply.github.com"], cwd=str(work_dir))
    await _git(["config", "user.name", "Claude Agent"], cwd=str(work_dir))


def _gh_post(path: str, token: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "temporal-claude-worker",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode()
        return response.status, (json.loads(raw) if raw else {})


@activity.defn
async def open_pull_request(input: OpenPRInput) -> OpenPRResult:
    """After an issue lane finishes: commit the agent's work, push the branch,
    and open a PR. The push/commit are done by the harness (not the agent, whose
    `git push` stays denied), authenticated with the worker's GITHUB_TOKEN."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return OpenPRResult(opened=False, message="no GITHUB_TOKEN in worker env")
    wd = input.work_dir

    # Keep the agent's workspace bootstrap/scratch out of the PR — commit only
    # the real code change, not .claude/, CLAUDE.md, REPORT.md, logs, or audit.
    try:
        (Path(wd) / ".git" / "info" / "exclude").write_text(_PR_EXCLUDE)
    except OSError:
        pass

    await _git(["add", "-A"], cwd=wd)
    _, status = await _git(["status", "--porcelain"], cwd=wd)
    if not status.strip():
        return OpenPRResult(opened=False, message="no changes — nothing to open a PR for")
    await _git(["commit", "-m", f"{input.title} (closes #{input.issue_number})"], cwd=wd)

    authed = f"https://x-access-token:{token}@github.com/{input.repo}.git"
    code, out = await _git(["push", "--force", authed, f"HEAD:{input.branch}"], cwd=wd)
    if code != 0:
        raise ApplicationError(
            f"git push failed: {out.replace(token, '***')[-300:]}",
            type="GitPushError", non_retryable=False,
        )

    body = f"Automated PR from the {input.branch} lane. Closes #{input.issue_number}."
    try:
        _, data = _gh_post(
            f"/repos/{input.repo}/pulls",
            token,
            {"title": input.title, "head": input.branch, "base": input.base, "body": body},
        )
        print(f"  OPEN PR #{data.get('number')} for issue #{input.issue_number} ({input.branch})")
        return OpenPRResult(opened=True, number=data.get("number", 0), url=data.get("html_url", ""))
    except urllib.error.HTTPError as err:
        detail = err.read().decode()[:200]
        # 422 usually means a PR already exists for this head — treat as non-fatal.
        print(f"  OPEN PR for issue #{input.issue_number}: {err.code} {detail}")
        return OpenPRResult(opened=False, message=f"{err.code} {detail}")


@activity.defn
async def update_pr_branch(input: UpdateBranchInput) -> UpdateBranchResult:
    """Bring a stale PR branch up to date by merging base into it (what GitHub's
    "Update branch" button does). Returns updated=True on a clean merge+push,
    conflict=True on a real content conflict that needs manual/agent resolution."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return UpdateBranchResult(updated=False, conflict=False, message="no GITHUB_TOKEN")
    authed = f"https://x-access-token:{token}@github.com/{input.repo}.git"
    tmp = Path(tempfile.mkdtemp(prefix="tc-rebase-")) / "repo"
    try:
        code, out = await _git(["clone", authed, str(tmp)])
        if code != 0:
            return UpdateBranchResult(False, False, f"clone failed: {out.replace(token, '***')[-200:]}")
        await _git(["config", "user.email", "claude-agent@users.noreply.github.com"], cwd=str(tmp))
        await _git(["config", "user.name", "Claude Agent"], cwd=str(tmp))
        code, out = await _git(["checkout", input.branch], cwd=str(tmp))
        if code != 0:
            return UpdateBranchResult(False, False, f"branch {input.branch} not found")
        code, out = await _git(
            ["merge", f"origin/{input.base}", "-m", f"Merge {input.base} into {input.branch}"],
            cwd=str(tmp),
        )
        if code != 0:
            await _git(["merge", "--abort"], cwd=str(tmp))
            print(f"  UPDATE-BRANCH {input.branch}: content conflict with {input.base}")
            return UpdateBranchResult(False, True, f"content conflict merging {input.base}")
        code, out = await _git(["push", "origin", f"HEAD:{input.branch}"], cwd=str(tmp))
        if code != 0:
            return UpdateBranchResult(False, False, f"push failed: {out.replace(token, '***')[-200:]}")
        print(f"  UPDATE-BRANCH {input.branch}: merged {input.base} in, pushed")
        return UpdateBranchResult(True, False, f"merged {input.base} into {input.branch}")
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)


@activity.defn
async def push_branch(input: PushBranchInput) -> PushBranchResult:
    """Push a resolve agent's workspace onto its PR branch (updating the PR).

    Used by the conflict-resolution lane: the agent merged base into the branch
    and fixed the conflict but its own ``git push`` is denied, so the harness
    commits anything left over and pushes with the worker's GITHUB_TOKEN. Same
    excludes as open_pull_request so workspace scratch never lands in the branch."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return PushBranchResult(pushed=False, message="no GITHUB_TOKEN in worker env")
    wd = input.work_dir
    try:
        (Path(wd) / ".git" / "info" / "exclude").write_text(_PR_EXCLUDE)
    except OSError:
        pass

    # A clean merge commit leaves nothing to stage; an unfinished resolution
    # gets committed now so the fix still ships.
    await _git(["add", "-A"], cwd=wd)
    _, status = await _git(["status", "--porcelain"], cwd=wd)
    if status.strip():
        await _git(["commit", "-m", f"Resolve conflicts on {input.branch}"], cwd=wd)

    authed = f"https://x-access-token:{token}@github.com/{input.repo}.git"
    code, out = await _git(["push", authed, f"HEAD:{input.branch}"], cwd=wd)
    if code != 0:
        raise ApplicationError(
            f"git push failed: {out.replace(token, '***')[-300:]}",
            type="GitPushError", non_retryable=False,
        )
    print(f"  PUSH {input.branch}: resolved branch pushed")
    return PushBranchResult(pushed=True, message=f"pushed {input.branch}")


def _claude_project_slug(cwd: str) -> str:
    """Claude Code stores transcripts under a cwd-derived project directory."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", cwd)


def _find_claude_transcript(session_id: str, work_dir: Path) -> Path:
    projects_dir = Path.home() / ".claude" / "projects"
    slug_path = projects_dir / _claude_project_slug(str(work_dir)) / f"{session_id}.jsonl"
    if slug_path.exists():
        return slug_path
    matches = list(projects_dir.glob(f"*/{session_id}.jsonl"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Claude transcript not found for session {session_id}")


def _fence(text: Any, language: str = "") -> str:
    body = "" if text is None else str(text)
    ticks = "```"
    while ticks in body:
        ticks += "`"
    return f"{ticks}{language}\n{body}\n{ticks}"


def _render_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return "" if content is None else _fence(json.dumps(content, indent=2), "json")

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            parts.append(str(item))
            continue
        kind = item.get("type")
        if kind == "text":
            parts.append(item.get("text", ""))
        elif kind == "tool_use":
            parts.append(
                f"**Tool call `{item.get('name', 'Tool')}` "
                f"(`{item.get('id', 'unknown')}`):**\n\n"
                + _fence(json.dumps(item.get("input", {}), indent=2), "json")
            )
        elif kind == "tool_result":
            label = f"Tool result for `{item.get('tool_use_id', 'unknown')}`"
            if item.get("is_error"):
                label += " (error)"
            parts.append(f"**{label}:**\n\n" + _fence(item.get("content", "")))
        elif kind == "thinking":
            continue
        else:
            parts.append(_fence(json.dumps(item, indent=2), "json"))
    return "\n\n".join(part for part in parts if part)


def _render_transcript_event(index: int, event: dict[str, Any]) -> str | None:
    timestamp = event.get("timestamp", "unknown time")
    event_type = event.get("type", "event")
    message = event.get("message") or {}
    role = message.get("role")
    if role:
        heading = f"### {index}. {timestamp} - {role}"
    elif event_type == "queue-operation":
        heading = f"### {index}. {timestamp} - queue {event.get('operation', '')}"
    elif event_type == "attachment":
        heading = f"### {index}. {timestamp} - attachment `{(event.get('attachment') or {}).get('type', 'attachment')}`"
    else:
        heading = f"### {index}. {timestamp} - {event_type}"

    lines = [heading, ""]
    if event.get("sessionId"):
        lines.extend([f"Session: `{event['sessionId']}`", ""])
    if event.get("cwd"):
        lines.extend([f"CWD: `{event['cwd']}`", ""])

    if event_type == "queue-operation":
        lines.append(f"Operation: `{event.get('operation')}`")
        if event.get("content"):
            lines.extend(["", _fence(event["content"])])
    elif event_type in {"assistant", "user"}:
        rendered = _render_content(message.get("content"))
        if rendered:
            lines.append(rendered)
        elif event.get("toolUseResult") is not None:
            lines.extend(
                [
                    "**Tool use result:**",
                    "",
                    _fence(json.dumps(event["toolUseResult"], indent=2), "json"),
                ]
            )
    elif event_type == "attachment":
        attachment = event.get("attachment") or {}
        if attachment.get("type") == "structured_output":
            lines.extend(
                [
                    "**Structured output:**",
                    "",
                    _fence(json.dumps(attachment.get("data"), indent=2), "json"),
                ]
            )
        else:
            lines.append("_Metadata attachment omitted from readable export._")
    elif event_type == "last-prompt":
        lines.extend(["**Last prompt:**", "", _fence(event.get("lastPrompt", ""))])
    elif event_type == "ai-title":
        lines.append(f"AI title: **{event.get('aiTitle', '')}**")
    elif event_type == "mode":
        lines.append(f"Mode: `{event.get('mode', '')}`")
    else:
        return None

    return "\n".join(lines).rstrip()


@activity.defn
async def export_claude_session_transcript(
    input: TranscriptExportInput,
) -> TranscriptExportResult:
    """Release a readable Claude Code transcript into the workflow workspace."""
    work_dir = Path(input.work_dir)
    source = _find_claude_transcript(input.session_id, work_dir)
    events: list[dict[str, Any]] = []
    with source.open() as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    audit_dir = work_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    session_file_prefix = re.sub(r"[^A-Za-z0-9._-]", "_", input.session_id)
    output = audit_dir / f"{session_file_prefix}-claude-session.md"
    first_ts = next((e.get("timestamp") for e in events if e.get("timestamp")), "unknown")
    last_ts = next((e.get("timestamp") for e in reversed(events) if e.get("timestamp")), "unknown")
    lines = [
        f"# Claude Session Transcript: {input.session_id}",
        "",
        "Readable Markdown export emitted by the Temporal workflow after the Claude Code task finished.",
        "",
        "## Metadata",
        "",
        f"- Session ID: `{input.session_id}`",
        f"- Source transcript: `{source}`",
        f"- Workspace: `{work_dir}`",
        f"- First timestamp: `{first_ts}`",
        f"- Last timestamp: `{last_ts}`",
        f"- Event count: `{len(events)}`",
        "",
        "## Transcript",
        "",
    ]
    for index, event in enumerate(events, 1):
        rendered = _render_transcript_event(index, event)
        if rendered:
            lines.extend([rendered, ""])
    output.write_text("\n".join(lines).rstrip() + "\n")
    return TranscriptExportResult(
        markdown_path=str(output),
        source_jsonl_path=str(source),
        event_count=len(events),
    )


@activity.defn
async def run_claude_chunk(input: ChunkInput) -> ChunkResult:
    # One stable workspace per workflow, derived from the workflow ID so every
    # chunk (and every retry) lands in the same directory. Session transcripts
    # are keyed by cwd, so a stable cwd is what makes resume find the session.
    workflow_id = activity.info().workflow_id
    work_dir = (
        Path(tempfile.gettempdir())
        / "temporal-claude"
        / re.sub(r"[^A-Za-z0-9._-]", "_", workflow_id)
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    # Clone the target repo into the (empty) workspace before anything else, so
    # the agent works on the real codebase. No-op when no repo is configured or
    # the clone already exists (retry/resume).
    await _prepare_repo(work_dir, input.repo, input.branch)
    _bootstrap_workspace(work_dir, input.team)
    rule_flags_before = _count_rule_flags(work_dir)

    info = activity.info()
    heartbeat_session_id = _session_id_from_heartbeat(info.heartbeat_details)
    resume_session_id = heartbeat_session_id or input.session_id
    if heartbeat_session_id:
        _append_jsonl(
            work_dir / "recovery-log.jsonl",
            {
                "ts": time.time(),
                "event": "resume_session_from_heartbeat",
                "attempt": info.attempt,
                "activity_id": info.activity_id,
                "input_session_id": input.session_id,
                "heartbeat_session_id": heartbeat_session_id,
            },
        )

    options = ClaudeAgentOptions(
        cwd=str(work_dir),
        model=input.model,
        max_turns=input.max_turns_per_chunk,
        resume=resume_session_id,
        # bypassPermissions + resume in print mode is buggy
        # (anthropics/claude-code#36139) — allow-list instead, same approach
        # as demo/runner/settings.json.
        permission_mode="acceptEdits",
        allowed_tools=[
            "Read", "Write", "Edit", "Glob", "Grep", "Bash", "TodoWrite", "Skill",
        ],
        # Load ONLY the workspace's own .claude/ (settings, hooks, skills) —
        # nothing from the worker machine's user or enclosing-project config.
        setting_sources=["project"],
        output_format=REPORT_SCHEMA,
    )

    client = ClaudeSDKClient(options=options)
    await client.connect()

    heartbeat_state: dict[str, Any] = {
        "kind": "claude_chunk",
        "attempt": info.attempt,
        "activity_id": info.activity_id,
        "session_id": resume_session_id,
        "message_type": "starting",
    }

    def _heartbeat(message_type: str) -> None:
        heartbeat_state["message_type"] = message_type
        heartbeat_state["ts"] = time.time()
        activity.heartbeat(dict(heartbeat_state))

    async def _heartbeater() -> None:
        # Timer-based heartbeat: proves the *worker* is alive even while the
        # agent is silent inside a long tool call (npm install, a slow test
        # suite). If heartbeats depended only on streamed agent messages, a
        # silent chunk and a dead worker would be hard to distinguish. With the
        # timer, heartbeat timeout means true worker death; a genuinely wedged
        # agent is bounded by start_to_close_timeout instead.
        while True:
            _heartbeat("timer")
            await asyncio.sleep(30)

    heartbeater = asyncio.create_task(_heartbeater())
    try:
        await client.query(input.prompt)
        async for message in client.receive_response():
            if isinstance(message, SystemMessage) and message.subtype == "init":
                session_id = message.data.get("session_id")
                if isinstance(session_id, str) and session_id:
                    heartbeat_state["session_id"] = session_id
            # Per-message heartbeats add progress detail and the current
            # Claude session ID in the Temporal UI and retry heartbeat details.
            _heartbeat(f"{type(message).__name__}:{getattr(message, 'subtype', '')}")

            if isinstance(message, ResultMessage):
                if message.is_error and message.subtype == "success":
                    # API-level failure (429/500/529) — the most common way a
                    # headless run dies. Raise retryable; the workflow's
                    # RetryPolicy backs off and the retry resumes the session.
                    raise ApplicationError(
                        f"Claude Code API error (status={message.api_error_status})",
                        type="ClaudeApiError",
                        non_retryable=False,
                    )
                if message.subtype == "error_during_execution":
                    # Usually transient (API drop mid-run, tool crash). Retry
                    # the chunk — the session transcript survives, so the
                    # retry resumes rather than restarts.
                    raise ApplicationError(
                        "Claude Code error during execution: "
                        + ("; ".join(message.errors or []) or "unknown"),
                        type="ClaudeExecutionError",
                        non_retryable=False,
                    )
                _log_usage(work_dir, message)
                structured = (
                    message.structured_output
                    if isinstance(message.structured_output, dict)
                    else None
                )
                return ChunkResult(
                    session_id=message.session_id,
                    subtype=message.subtype,
                    text=(message.result or "") if message.subtype == "success" else "",
                    errors=message.errors or [],
                    cost_usd=message.total_cost_usd or 0.0,
                    num_turns=message.num_turns,
                    work_dir=str(work_dir),
                    structured=structured if message.subtype == "success" else None,
                    rule_flags=_read_rule_flags(work_dir, rule_flags_before),
                    model=input.model,
                )
        raise RuntimeError("Claude Code stream ended without a result message")
    except asyncio.CancelledError:
        # Temporal cancelled the activity — stop the agent cleanly, then let
        # the cancellation propagate. The session transcript survives, so a
        # later chunk can still resume it.
        try:
            await asyncio.wait_for(client.interrupt(), timeout=5)
        except Exception:
            pass
        raise
    finally:
        heartbeater.cancel()
        await client.disconnect()
