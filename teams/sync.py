"""Materialize each team's governance files from the human-committed sources.

Skills LIVE in each team's folder (teams/<team>/.claude/skills/) — the team
owns its playbooks outright; there is no shared pool to sync from. What this
script keeps in sync are the three policy files whose single source of truth
is src/shared.py:

    settings.json   base policy + the lane's overlay (settings_for_team)
    rules.json      the lane's behavioral rules (DEFAULT_RULES + TEAM_RULES)
    flag-rules.py   the hook script that enforces rules.json on every call

Run after editing any of those sources:  python3 teams/sync.py
tests/test_team_profiles.py fails if a team's policy files drift.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from shared import (  # noqa: E402
    DEFAULT_RULES,
    FLAG_RULES_SCRIPT,
    TEAM_PROFILES,
    TEAM_RULES,
    settings_for_team,
)

TEAMS = ROOT / "teams"


def sync() -> int:
    for team, names in TEAM_PROFILES.items():
        claude_dir = TEAMS / team / ".claude"
        skills = claude_dir / "skills"
        if not (TEAMS / team / "CLAUDE.md").exists():
            print(f"  WARNING: teams/{team}/CLAUDE.md missing — every team needs a mandate")
            return 1
        missing = [n for n in names if not (skills / n / "SKILL.md").exists()]
        if missing:
            print(f"  WARNING: teams/{team} missing skills {missing} — the team folder owns them")
            return 1
        (claude_dir / "settings.json").write_text(json.dumps(settings_for_team(team), indent=2) + "\n")
        (claude_dir / "rules.json").write_text(json.dumps(DEFAULT_RULES + TEAM_RULES.get(team, []), indent=2) + "\n")
        (claude_dir / "flag-rules.py").write_text(FLAG_RULES_SCRIPT)
        print(f"  {team}: settings.json + rules.json + flag-rules.py (skills: {len(names)} team-owned)")
    return 0


if __name__ == "__main__":
    sys.exit(sync())
