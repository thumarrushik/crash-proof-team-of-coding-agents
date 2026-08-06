"""Materialize each team's skill bundle: teams/<team>/.claude/skills/<name>/.

The canonical skill sources live in skills/ (one place to edit); TEAM_PROFILES
in src/shared.py says which skills each team carries. This script copies each
team's bundle into its folder so the team directory is the complete, physical
"who we are and how we work" unit the bootstrap installs. Run it after editing
any skill or profile:

    python3 teams/sync.py

tests/test_team_profiles.py fails if a team folder drifts from its sources, so
an un-synced edit goes red instead of shipping stale playbooks. Skills that
resolve from the operator's machine (e.g. lean-service, from ~/.claude/skills)
are intentionally NOT materialized — the bootstrap resolves them at run time so
the operator override keeps working.
"""
import shutil
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

CANONICAL = ROOT / "skills"
TEAMS = ROOT / "teams"


def repo_skills() -> set[str]:
    return {p.name for p in CANONICAL.iterdir() if (p / "SKILL.md").exists()}


def sync() -> int:
    import json
    available = repo_skills()
    for team, names in TEAM_PROFILES.items():
        claude_dir = TEAMS / team / ".claude"
        dest = claude_dir / "skills"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        # the team's full governance unit, human-committed and team-specific:
        # settings (base policy + the lane's overlay), the lane's behavioral
        # rules, and the hook script that enforces them on every tool call
        (claude_dir / "settings.json").write_text(json.dumps(settings_for_team(team), indent=2) + "\n")
        (claude_dir / "rules.json").write_text(json.dumps(DEFAULT_RULES + TEAM_RULES.get(team, []), indent=2) + "\n")
        (claude_dir / "flag-rules.py").write_text(FLAG_RULES_SCRIPT)
        print(f"  {team}: settings.json + rules.json + flag-rules.py")
        for name in names:
            if name not in available:
                print(f"  {team}: {name} (operator-resolved at run time; not materialized)")
                continue
            shutil.copytree(CANONICAL / name, dest / name)
            print(f"  {team}: {name} <- skills/{name}")
        if not (TEAMS / team / "CLAUDE.md").exists():
            print(f"  WARNING: teams/{team}/CLAUDE.md missing — every team needs a mandate")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(sync())
