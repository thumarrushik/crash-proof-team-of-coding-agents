import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json
import tempfile
import unittest
from pathlib import Path

from activities import _bootstrap_workspace
from shared import known_teams, task_queue_for_team

REPO = Path(__file__).resolve().parent.parent
TEAMS = REPO / "teams"
sys.path.insert(0, str(TEAMS))
from validate import ORG_FLOOR_DENY, MANDATE_SECTIONS, validate  # noqa: E402


class TeamSelfSufficiencyTests(unittest.TestCase):
    """Each teams/<team>/ is owned by an engineering team and self-sufficient:
    mandate + OWNERS + settings + rules + hook + skills, all in the folder.
    Central code only discovers folders and enforces the org floor."""

    def test_discovery_finds_the_team_folders(self) -> None:
        self.assertEqual(sorted(known_teams()),
                         sorted(d.name for d in TEAMS.iterdir()
                                if d.is_dir() and (d / "CLAUDE.md").exists()))
        self.assertIn("backend", known_teams())
        self.assertIn("review", known_teams())

    def test_validator_passes_every_folder(self) -> None:
        self.assertEqual(validate(), 0)

    def test_every_team_folder_is_complete(self) -> None:
        for team in known_teams():
            with self.subTest(team=team):
                folder = TEAMS / team
                text = (folder / "CLAUDE.md").read_text()
                for section in MANDATE_SECTIONS:
                    self.assertIn(section, text)
                self.assertIn(f"Team: `{team}`", text)
                self.assertIn("Owner:", (folder / "OWNERS.md").read_text())
                settings = json.loads((folder / ".claude" / "settings.json").read_text())
                for rule in ORG_FLOOR_DENY:
                    self.assertIn(rule, settings["permissions"]["deny"])
                rules = json.loads((folder / ".claude" / "rules.json").read_text())
                self.assertIsInstance(rules, list)
                self.assertTrue((folder / ".claude" / "flag-rules.py").exists())
                owned = list((folder / ".claude" / "skills").glob("*/SKILL.md"))
                self.assertTrue(owned, f"{team} owns no skills")
                self.assertEqual(task_queue_for_team(team), f"claude-code-tasks-{team}")

    def test_bootstrap_installs_the_team_folder(self) -> None:
        for team in known_teams():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)
                _bootstrap_workspace(work_dir, team)
                memory = (work_dir / "CLAUDE.md").read_text()
                mandate = (TEAMS / team / "CLAUDE.md").read_text()
                self.assertTrue(memory.startswith(mandate))
                self.assertIn("## Installed skills (this worker)", memory)
                ws_settings = json.loads((work_dir / ".claude" / "settings.json").read_text())
                self.assertEqual(ws_settings,
                                 json.loads((TEAMS / team / ".claude" / "settings.json").read_text()))
                for owned in (TEAMS / team / ".claude" / "skills").glob("*/SKILL.md"):
                    name = owned.parent.name
                    self.assertTrue((work_dir / ".claude" / "skills" / name / "SKILL.md").exists(),
                                    f"{team} did not install {name}")

    def test_team_specific_policy_reaches_the_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "review")
            settings = json.loads((work_dir / ".claude" / "settings.json").read_text())
            self.assertIn("Bash(git commit:*)", settings["permissions"]["deny"])
            rules = json.loads((work_dir / ".claude" / "rules.json").read_text())
            self.assertIn("review_lane_edits_code", [r["name"] for r in rules])
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "frontend")
            settings = json.loads((work_dir / ".claude" / "settings.json").read_text())
            self.assertNotIn("Bash(git commit:*)", settings["permissions"]["deny"])
            self.assertTrue((work_dir / ".claude" / "skills" / "design-ui" / "SKILL.md").exists())
            self.assertTrue((work_dir / ".claude" / "skills" / "lean-service" / "HARD-RULES.md").exists())

    def test_unknown_team_borrows_the_default_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "no-such-team")
            memory = (work_dir / "CLAUDE.md").read_text()
            self.assertIn("Team: `no-such-team`", memory)
            settings = json.loads((work_dir / ".claude" / "settings.json").read_text())
            for rule in ORG_FLOOR_DENY:
                self.assertIn(rule, settings["permissions"]["deny"])


if __name__ == "__main__":
    unittest.main()
