"""Deterministic, offline test for the Stop-gate hook used by the
`Done Is Not a Claim` experiment (deploy/step-gate.py). We run the REAL Stop
hook the experiment installs, as Claude Code would: the Stop event as JSON on
stdin, the workspace's `.claude/` present, and we assert its decision. This is
the regression guard: a gate that stops blocking (so "done" is no longer a
proven claim) turns a test red instead of letting a skipped step ship quietly.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Single source of truth: load the hook-script constant from the runner (its
# __main__ guard means exec won't launch the experiment).
_ns: dict = {}
exec(compile((ROOT / "deploy" / "step-gate.py").read_text(), "step-gate.py", "exec"), _ns)
STOP_GATE = _ns["STOP_GATE"]


def _run(marker_file_contents, stop_hook_active=False):
    """Run the Stop gate in a temp workspace; optionally seed proof.txt.
    Returns (stdout, exit_code)."""
    d = Path(tempfile.mkdtemp(prefix="stopgate-"))
    (d / ".claude").mkdir()
    (d / "stop-gate.py").write_text(STOP_GATE)
    if marker_file_contents is not None:
        (d / "proof.txt").write_text(marker_file_contents)
    event = json.dumps({"hook_event_name": "Stop", "stop_hook_active": stop_hook_active})
    proc = subprocess.run([sys.executable, "stop-gate.py"], cwd=str(d),
                          input=event, capture_output=True, text=True)
    return proc.stdout.strip(), proc.returncode, d


class StopGateTest(unittest.TestCase):
    def test_blocks_when_no_proof(self):
        out, code, _ = _run(marker_file_contents=None)
        self.assertEqual(code, 0)                 # exit 0 + JSON is how Stop hooks speak
        decision = json.loads(out)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("VERIFIED", decision["reason"])

    def test_blocks_when_proof_lacks_marker(self):
        out, _, _ = _run(marker_file_contents="in progress\n")
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_allows_when_marker_present(self):
        out, code, _ = _run(marker_file_contents="VERIFIED\n")
        self.assertEqual(out, "")                 # no output = allow the stop
        self.assertEqual(code, 0)

    def test_allows_marker_among_other_text(self):
        out, _, _ = _run(marker_file_contents="ran the tests\nVERIFIED\n")
        self.assertEqual(out, "")

    def test_logs_each_block(self):
        out, _, d = _run(marker_file_contents=None, stop_hook_active=True)
        self.assertEqual(json.loads(out)["decision"], "block")
        log = d / ".claude" / "gate-log.jsonl"
        self.assertEqual(len(log.read_text().splitlines()), 1)   # the block is recorded (auditable)

    def test_malformed_input_never_blocks(self):
        d = Path(tempfile.mkdtemp(prefix="stopgate-"))
        (d / ".claude").mkdir()
        (d / "stop-gate.py").write_text(STOP_GATE)
        proc = subprocess.run([sys.executable, "stop-gate.py"], cwd=str(d),
                              input="not json{{", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)      # fail open: never trap the agent on a parse error
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
