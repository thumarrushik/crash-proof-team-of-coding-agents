"""The commit mirror: the mirror-signal hook (agent side, no credential) only
leaves a marker; _mirror_branch (harness side, its own step) pushes the work
branch. A commit is never only on this machine."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import asyncio
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from activities import _bootstrap_workspace, _mirror_branch, _PR_EXCLUDE
from shared import known_teams

REPO = Path(__file__).resolve().parent.parent
TEAMS = REPO / "teams"


def run_signal(team: str, work_dir: Path, event: dict | str) -> None:
    """Run the team's mirror-signal hook as PostToolUse would: cwd = the
    workspace, the tool event as JSON on stdin."""
    payload = event if isinstance(event, str) else json.dumps(event)
    subprocess.run(
        [sys.executable, str(TEAMS / team / ".claude" / "mirror-signal.py")],
        input=payload, capture_output=True, text=True, cwd=work_dir, timeout=30,
        check=True,
    )


def git(work_dir: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=work_dir, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


class MirrorSignalHookTests(unittest.TestCase):
    """The agent-side half: a marker on `git commit`, nothing else, no push."""

    def setUp(self) -> None:
        self.work_dir = Path(tempfile.mkdtemp())
        (self.work_dir / ".claude").mkdir()
        self.marker = self.work_dir / ".claude" / "mirror-request"

    def _bash(self, command: str) -> dict:
        return {"tool_name": "Bash", "tool_input": {"command": command}}

    def test_git_commit_leaves_the_marker(self) -> None:
        run_signal("backend", self.work_dir, self._bash('git commit -m "phase: test green"'))
        self.assertTrue(self.marker.exists())

    def test_chained_add_and_commit_leaves_the_marker(self) -> None:
        run_signal("backend", self.work_dir, self._bash("git add -A && git commit -m checkpoint"))
        self.assertTrue(self.marker.exists())

    def test_other_bash_calls_do_not(self) -> None:
        for command in ("ls -la", "git status", "git log --oneline", "echo commit"):
            run_signal("backend", self.work_dir, self._bash(command))
            self.assertFalse(self.marker.exists(), command)

    def test_other_tools_do_not(self) -> None:
        run_signal("backend", self.work_dir,
                   {"tool_name": "Write", "tool_input": {"content": "git commit"}})
        self.assertFalse(self.marker.exists())

    def test_garbage_stdin_is_harmless(self) -> None:
        run_signal("backend", self.work_dir, "not json{")
        self.assertFalse(self.marker.exists())


class EveryTeamCarriesTheMirrorTests(unittest.TestCase):
    """The hook is org floor: every team folder carries its own copy and
    registers it on Bash calls (the review lane too — its `git commit` deny
    just means the hook never fires there)."""

    def test_every_team_has_script_and_registration(self) -> None:
        for team in known_teams():
            with self.subTest(team=team):
                claude = TEAMS / team / ".claude"
                self.assertTrue((claude / "mirror-signal.py").exists())
                settings = json.loads((claude / "settings.json").read_text())
                commands = [hook["command"]
                            for entry in settings["hooks"]["PostToolUse"]
                            for hook in entry["hooks"]]
                self.assertIn("python3 .claude/mirror-signal.py", commands)

    def test_bootstrap_stamps_the_hook(self) -> None:
        work_dir = Path(tempfile.mkdtemp())
        _bootstrap_workspace(work_dir, "backend")
        self.assertTrue((work_dir / ".claude" / "mirror-signal.py").exists())

    def test_bootstrap_stamps_the_scratch_exclusion_into_git(self) -> None:
        # With commits mirrored as they land, the exclusion must hold from the
        # first commit — bootstrap writes it whenever the workspace has a .git.
        work_dir = Path(tempfile.mkdtemp())
        git(work_dir, "init")
        _bootstrap_workspace(work_dir, "backend")
        self.assertEqual((work_dir / ".git" / "info" / "exclude").read_text(), _PR_EXCLUDE)


class MirrorBranchTests(unittest.TestCase):
    """The harness-side half, against a local bare remote."""

    def setUp(self) -> None:
        self.work_dir = Path(tempfile.mkdtemp())
        self.remote = Path(tempfile.mkdtemp()) / "remote.git"
        git(self.remote.parent, "init", "--bare", str(self.remote))
        git(self.work_dir, "init")
        (self.work_dir / "a.txt").write_text("one\n")
        git(self.work_dir, "add", "-A")
        git(self.work_dir, "commit", "-m", "one")

    def _mirror(self, last_head: str) -> str:
        return asyncio.run(
            _mirror_branch(self.work_dir, str(self.remote), "work", last_head)
        )

    def test_first_mirror_creates_the_remote_branch(self) -> None:
        head = git(self.work_dir, "rev-parse", "HEAD")
        self.assertEqual(self._mirror(""), head)
        self.assertEqual(git(self.remote, "rev-parse", "work"), head)

    def test_nothing_new_is_a_no_op(self) -> None:
        head = git(self.work_dir, "rev-parse", "HEAD")
        self.assertEqual(self._mirror(head), head)

    def test_each_new_commit_reaches_the_remote(self) -> None:
        first = self._mirror("")
        (self.work_dir / "a.txt").write_text("two\n")
        git(self.work_dir, "add", "-A")
        git(self.work_dir, "commit", "-m", "two")
        head = git(self.work_dir, "rev-parse", "HEAD")
        self.assertNotEqual(head, first)
        self.assertEqual(self._mirror(first), head)
        self.assertEqual(git(self.remote, "rev-parse", "work"), head)

    def test_failed_push_never_raises_and_leaves_a_log_row(self) -> None:
        gone = str(self.remote) + "-missing"
        result = asyncio.run(_mirror_branch(self.work_dir, gone, "work", "stale"))
        self.assertEqual(result, "stale")
        rows = [json.loads(line) for line in
                (self.work_dir / "recovery-log.jsonl").read_text().splitlines()]
        self.assertTrue(any(r["event"] == "mirror_push_failed" for r in rows))


if __name__ == "__main__":
    unittest.main()
