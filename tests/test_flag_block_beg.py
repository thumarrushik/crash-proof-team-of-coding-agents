"""Deterministic, offline tests for the flag/block hook scripts used by the
`Flag, Block, or Beg` experiment (deploy/flag-block-beg.py). We run the REAL
hook scripts the experiment installs, as Claude Code would: the tool event as
JSON on stdin, the script's `.claude/` working dir present, and we assert on
its stdout decision and its side-effect log. This is the E4 regression guard —
if a hook silently stops flagging or blocking, a test goes red instead of the
mistake going quiet ("a deleted crontab line makes no sound").
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Single source of truth: load the hook-script constants straight from the
# experiment runner (its `if __name__ == "__main__"` guard means exec won't run
# the experiment).
_ns: dict = {}
exec(compile((ROOT / "deploy" / "flag-block-beg.py").read_text(), "flag-block-beg.py", "exec"), _ns)
FLAG_LS = _ns["FLAG_LS"]
BLOCK_LS = _ns["BLOCK_LS"]


def _run_hook(script: str, event, raw: str | None = None):
    """Run a hook script with `event` (dict) as stdin JSON, in a temp workspace
    that has a `.claude/` dir. Returns (stdout, claude_dir)."""
    d = tempfile.mkdtemp(prefix="hook-test-")
    (Path(d) / "h.py").write_text(script)
    (Path(d) / ".claude").mkdir(exist_ok=True)
    payload = raw if raw is not None else json.dumps(event)
    proc = subprocess.run([sys.executable, "h.py"], cwd=d, input=payload,
                          capture_output=True, text=True)
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout.strip(), Path(d) / ".claude"


def _bash(cmd: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


class BlockHookTest(unittest.TestCase):
    def test_denies_orientation_ls(self):
        out, claude = _run_hook(BLOCK_LS, _bash("ls -la"))
        decision = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertEqual(len((claude / "block-log.jsonl").read_text().splitlines()), 1)

    def test_denies_ls_even_behind_cd(self):
        out, _ = _run_hook(BLOCK_LS, _bash("cd /tmp && ls"))
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allows_real_work(self):
        for cmd in ("python3 -m pytest -q", "echo hi", "lscpu", "grep ls file"):
            out, claude = _run_hook(BLOCK_LS, _bash(cmd))
            self.assertEqual(out, "", f"{cmd!r} should not be denied")
            self.assertFalse((claude / "block-log.jsonl").exists())

    def test_ignores_non_bash_tools(self):
        out, _ = _run_hook(BLOCK_LS, {"tool_name": "Write", "tool_input": {"file_path": "ls.txt"}})
        self.assertEqual(out, "")

    def test_malformed_input_never_blocks(self):
        out, _ = _run_hook(BLOCK_LS, None, raw="not json{{")
        self.assertEqual(out, "")  # fails open — never wedge the agent on a parse error


class FlagHookTest(unittest.TestCase):
    def test_flags_orientation_ls_and_only_that(self):
        _, claude = _run_hook(FLAG_LS, _bash("ls"))
        self.assertEqual(len((claude / "flag-log.jsonl").read_text().splitlines()), 1)
        _, claude2 = _run_hook(FLAG_LS, _bash("python3 -m pytest -q"))
        self.assertFalse((claude2 / "flag-log.jsonl").exists())

    def test_flag_never_blocks(self):
        # detection only: a PostToolUse-style flag emits no decision, ever.
        out, _ = _run_hook(FLAG_LS, _bash("ls -la"))
        self.assertEqual(out, "")

    def test_malformed_input_never_fails(self):
        out, _ = _run_hook(FLAG_LS, None, raw="")
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
