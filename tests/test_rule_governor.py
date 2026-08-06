import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from activities import (
    DEFAULT_RULES,
    TEAM_RULES,
    _FLAG_RULES_SCRIPT,
    _count_rule_flags,
    _read_rule_flags,
)
from shared import TaskInput, corrective_instruction, model_for_chunk, unanimous_failures


class CorrectiveInstructionTest(unittest.TestCase):
    def test_no_flags_no_instruction(self):
        self.assertIsNone(corrective_instruction({}))

    def test_names_every_rule_and_count(self):
        note = corrective_instruction({"redundant_orientation_ls": 3, "review_lane_edits_code": 1})
        self.assertIn("redundant_orientation_ls ×3", note)
        self.assertIn("review_lane_edits_code ×1", note)


class FlagPressureLadderTest(unittest.TestCase):
    def test_escalated_overrides_chunk_threshold(self):
        inp = TaskInput(task="t", model="haiku",
                        escalate_model="sonnet", escalate_after_chunks=5)
        self.assertEqual(model_for_chunk(inp, 1, escalated=False), "haiku")
        self.assertEqual(model_for_chunk(inp, 1, escalated=True), "sonnet")

    def test_escalated_without_ladder_is_inert(self):
        inp = TaskInput(task="t", model="haiku")
        self.assertEqual(model_for_chunk(inp, 1, escalated=True), "haiku")


class UnanimityRuleTest(unittest.TestCase):
    def test_unanimous_failure_indicts_the_referee(self):
        forks = [
            {"test_a::one", "test_a::edge"},
            {"test_a::edge"},
            {"test_a::edge", "test_a::other"},
        ]
        self.assertEqual(unanimous_failures(forks), {"test_a::edge"})

    def test_disagreement_clears_the_referee(self):
        forks = [{"test_a::one"}, {"test_a::two"}, set()]
        self.assertEqual(unanimous_failures(forks), set())

    def test_single_candidate_cannot_indict(self):
        self.assertEqual(unanimous_failures([{"test_a::edge"}]), set())

    def test_all_green_is_all_clear(self):
        self.assertEqual(unanimous_failures([set(), set(), set()]), set())


class FlagTallyTest(unittest.TestCase):
    def _workspace(self, lines):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".claude").mkdir()
        if lines is not None:
            (tmp / ".claude" / "rule-flags.jsonl").write_text(
                "".join(json.dumps(l) + "\n" for l in lines)
            )
        return tmp

    def test_missing_log_is_empty(self):
        tmp = self._workspace(None)
        self.assertEqual(_count_rule_flags(tmp), 0)
        self.assertEqual(_read_rule_flags(tmp, 0), {})

    def test_skip_isolates_this_chunks_flags(self):
        tmp = self._workspace([
            {"rule": "redundant_orientation_ls"},          # previous chunk
            {"rule": "redundant_orientation_ls"},          # this chunk
            {"rule": "review_lane_edits_code"},            # this chunk
        ])
        self.assertEqual(_count_rule_flags(tmp), 3)
        self.assertEqual(
            _read_rule_flags(tmp, 1),
            {"redundant_orientation_ls": 1, "review_lane_edits_code": 1},
        )


class FlagRulesHookTest(unittest.TestCase):
    """Run the actual hook script the bootstrap installs, as Claude Code would:
    hook event JSON on stdin, rules.json in .claude/, flags appended to
    .claude/rule-flags.jsonl."""

    def _run_hook(self, rules, events):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".claude").mkdir()
        (tmp / ".claude" / "rules.json").write_text(json.dumps(rules))
        script = tmp / ".claude" / "flag-rules.py"
        script.write_text(_FLAG_RULES_SCRIPT)
        for event in events:
            subprocess.run([sys.executable, str(script)], input=json.dumps(event),
                           text=True, cwd=tmp, check=True, timeout=30)
        flag_file = tmp / ".claude" / "rule-flags.jsonl"
        if not flag_file.exists():
            return []
        return [json.loads(l) for l in flag_file.read_text().splitlines()]

    def test_bash_regex_rule_flags_ls_even_behind_cd(self):
        flags = self._run_hook(DEFAULT_RULES, [
            {"tool_name": "Bash", "tool_input": {"command": "ls -la"}},
            {"tool_name": "Bash", "tool_input": {"command": "cd /tmp && ls"}},
            {"tool_name": "Bash", "tool_input": {"command": "pytest -q"}},
            {"tool_name": "Write", "tool_input": {"file_path": "a.py"}},
        ])
        self.assertEqual([f["rule"] for f in flags],
                         ["redundant_orientation_ls", "redundant_orientation_ls"])

    def test_review_lane_tool_rule_flags_edits(self):
        rules = DEFAULT_RULES + TEAM_RULES["review"]
        flags = self._run_hook(rules, [
            {"tool_name": "Edit", "tool_input": {"file_path": "src/app.py"}},
            {"tool_name": "Read", "tool_input": {"file_path": "src/app.py"}},
            {"tool_name": "Write", "tool_input": {"file_path": "src/app.py"}},
        ])
        self.assertEqual([f["rule"] for f in flags],
                         ["review_lane_edits_code", "review_lane_edits_code"])

    def test_malformed_input_never_fails(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".claude").mkdir()
        (tmp / ".claude" / "rules.json").write_text(json.dumps(DEFAULT_RULES))
        script = tmp / ".claude" / "flag-rules.py"
        script.write_text(_FLAG_RULES_SCRIPT)
        p = subprocess.run([sys.executable, str(script)], input="not json",
                           text=True, cwd=tmp, timeout=30)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
