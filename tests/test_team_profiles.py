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

    def test_bootstrap_binds_the_team_folder_live(self) -> None:
        """Bind, don't copy: the workspace mandate IMPORTS the live team file,
        and skills are a symlink into the team folder — the owning team's edits
        reach the next chunk without any re-stamp."""
        for team in known_teams():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)
                _bootstrap_workspace(work_dir, team)
                memory = (work_dir / "CLAUDE.md").read_text()
                self.assertIn(f"Team: `{team}`", memory)
                self.assertIn(f"@{TEAMS / team / 'CLAUDE.md'}", memory)   # live import
                ws_skills = work_dir / ".claude" / "skills"
                self.assertTrue(ws_skills.is_symlink())
                self.assertTrue(ws_skills.resolve().samefile(TEAMS / team / ".claude" / "skills"))
                # policy is stamped (a real file, not a link) with source guards injected
                ws_settings = work_dir / ".claude" / "settings.json"
                self.assertFalse(ws_settings.is_symlink())
                settings = json.loads(ws_settings.read_text())
                deny = settings["permissions"]["deny"]
                self.assertTrue(any(d.startswith("Write(") and "teams" in d for d in deny))
                self.assertTrue(any(d.startswith("Edit(") and "teams" in d for d in deny))
                team_deny = json.loads((TEAMS / team / ".claude" / "settings.json").read_text())["permissions"]["deny"]
                for rule in team_deny:                      # team policy fully carried
                    self.assertIn(rule, deny)

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
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "backend")
            self.assertTrue((work_dir / ".claude" / "skills" / "lean-service" / "HARD-RULES.md").exists(),
                            "lean-service topic files should reach the backend workspace")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "testing")
            rules = json.loads((work_dir / ".claude" / "rules.json").read_text())
            self.assertIn("sleep_as_synchronization", [r["name"] for r in rules],
                          "testing lane's sleep rule should reach its workspace")

    def test_governance_is_tracked_by_git(self) -> None:
        """The team folders are only real if version control carries them: an
        unanchored `.claude/` gitignore once silently excluded every team's
        policy, gates, and skills from the pushed repo while local validation
        stayed green. Guard: git must track each team's governance unit."""
        import subprocess
        tracked = subprocess.run(
            ["git", "ls-files", "teams"], capture_output=True, text=True,
            cwd=REPO, check=True).stdout.splitlines()
        for team in known_teams():
            with self.subTest(team=team):
                prefix = f"teams/{team}/.claude/"
                unit = [p[len(prefix):] for p in tracked if p.startswith(prefix)]
                for required in ("settings.json", "rules.json",
                                 "flag-rules.py", "phase-gate.py"):
                    self.assertIn(required, unit,
                                  f"{team}: {required} is not tracked by git")
                self.assertTrue(any(p.endswith("SKILL.md") for p in unit),
                                f"{team}: no skill is tracked by git")

    def test_every_mandate_ref_resolves_to_an_owned_skill(self) -> None:
        """No dangling [[skill]] references: every skill a mandate tells the
        agent to apply must exist in that team's own folder — the working set
        and the mandate move together."""
        import re
        for team in known_teams():
            with self.subTest(team=team):
                mandate = (TEAMS / team / "CLAUDE.md").read_text()
                owned = {d.name for d in (TEAMS / team / ".claude" / "skills").iterdir()
                         if (d / "SKILL.md").exists()}
                for ref in set(re.findall(r"\[\[([a-z0-9-]+)\]\]", mandate)):
                    self.assertIn(ref, owned,
                                  f"teams/{team}/CLAUDE.md references [[{ref}]] "
                                  f"but the team does not own that skill")

    def test_unknown_team_borrows_the_default_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "no-such-team")
            memory = (work_dir / "CLAUDE.md").read_text()
            self.assertIn("Team: `no-such-team`", memory)
            self.assertIn("@", memory)                       # still binds a real mandate
            settings = json.loads((work_dir / ".claude" / "settings.json").read_text())
            for rule in ORG_FLOOR_DENY:
                self.assertIn(rule, settings["permissions"]["deny"])

if __name__ == "__main__":
    unittest.main()
