import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json
import tempfile
import unittest
from pathlib import Path

from activities import _bootstrap_workspace
from shared import TEAM_PROFILES, task_queue_for_team

REPO = Path(__file__).resolve().parent.parent
TEAMS = REPO / "teams"
CANONICAL = REPO / "skills"


class TeamProfileTests(unittest.TestCase):
    def test_every_team_installs_policy_memory_and_skills(self) -> None:
        for team, skills in TEAM_PROFILES.items():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)

                _bootstrap_workspace(work_dir, team)

                settings = json.loads((work_dir / ".claude" / "settings.json").read_text())
                self.assertIn("PostToolUse", settings["hooks"])
                self.assertEqual(
                    "cat >> .claude/hook-log.jsonl",
                    settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"],
                )

                memory = (work_dir / "CLAUDE.md").read_text()
                self.assertIn(f"Team: `{team}`", memory)
                self.assertIn("Temporal workflow", memory)
                self.assertEqual(memory, (work_dir / ".claude" / "CLAUDE.md").read_text())

                for skill in skills:
                    self.assertTrue(
                        (work_dir / ".claude" / "skills" / skill / "SKILL.md").exists(),
                        f"{team} missing {skill}",
                    )

                self.assertEqual(task_queue_for_team(team), f"claude-code-tasks-{team}")


class TeamFolderTests(unittest.TestCase):
    """Every team is a physical folder: a CLAUDE.md mandate (every task's
    phases, work-issue style) plus its own .claude/skills bundle, kept in sync
    with the canonical skills/ pool by teams/sync.py."""

    def test_every_team_has_a_folder_with_mandate_and_skills(self) -> None:
        for team in TEAM_PROFILES:
            with self.subTest(team=team):
                mandate = TEAMS / team / "CLAUDE.md"
                self.assertTrue(mandate.exists(), f"teams/{team}/CLAUDE.md missing")
                text = mandate.read_text()
                self.assertIn(f"Team: `{team}`", text)
                # The mandate is a phase checklist the agent must not skip.
                self.assertIn("do not skip", text)
                self.assertIn("**Report.**", text)
                self.assertIn("Harness contract", text)
                self.assertTrue((TEAMS / team / ".claude" / "skills").is_dir(),
                                f"teams/{team}/.claude/skills missing")
                # Every team carries its settings.json, in sync with the
                # human-committed constant (teams/sync.py materializes it).
                import json as _json
                from shared import WORKSPACE_SETTINGS
                team_settings = TEAMS / team / ".claude" / "settings.json"
                self.assertTrue(team_settings.exists(),
                                f"teams/{team}/.claude/settings.json missing; run teams/sync.py")
                self.assertEqual(_json.loads(team_settings.read_text()), WORKSPACE_SETTINGS,
                                 f"teams/{team} settings drifted; run teams/sync.py")
                self.assertIn("settings.json", text)   # the mandate names its policy

    def test_team_bundles_match_canonical_sources(self) -> None:
        """Drift guard: an edit to skills/ without running teams/sync.py (or a
        hand-edit inside a team bundle) goes red here instead of shipping
        stale playbooks."""
        for team, names in TEAM_PROFILES.items():
            for name in names:
                src = CANONICAL / name
                if not (src / "SKILL.md").exists():
                    continue  # operator-resolved (e.g. lean-service): not materialized
                dst = TEAMS / team / ".claude" / "skills" / name
                with self.subTest(team=team, skill=name):
                    self.assertTrue((dst / "SKILL.md").exists(),
                                    f"teams/{team} missing {name}; run teams/sync.py")
                    for p in src.rglob("*"):
                        if p.is_file():
                            rel = p.relative_to(src)
                            self.assertEqual(
                                p.read_text(), (dst / rel).read_text(),
                                f"teams/{team}/{name}/{rel} drifted; run teams/sync.py")

    def test_bootstrap_memory_is_the_team_mandate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "review")
            memory = (work_dir / "CLAUDE.md").read_text()
            mandate = (TEAMS / "review" / "CLAUDE.md").read_text()
            self.assertTrue(memory.startswith(mandate))          # mandate first, verbatim
            self.assertIn("## Installed skills (this worker)", memory)
            # The review lane's mandate carries the self-grade lesson: the
            # verdict is the latest actual run, reported after phase 3.
            self.assertIn("latest actual run", mandate)

    def test_unknown_team_still_gets_a_mandate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "no-such-team")
            memory = (work_dir / "CLAUDE.md").read_text()
            self.assertIn("Team: `no-such-team`", memory)
            self.assertIn("REPORT.md", memory)


if __name__ == "__main__":
    unittest.main()
