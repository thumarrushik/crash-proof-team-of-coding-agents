"""Validate that every team folder is SELF-SUFFICIENT.

Each teams/<team>/ is owned by an engineering team and carries everything its
lane runs under: CLAUDE.md (the mandate), OWNERS.md, and .claude/ with
settings.json, rules.json, flag-rules.py, and skills/. Nothing is generated
centrally; teams edit their own files. This validator (and the mirror tests in
tests/test_team_profiles.py) enforces only the org-wide contract:

  - the mandate exists and keeps its required sections
  - OWNERS.md names an owner
  - settings.json is valid JSON and its deny list includes the ORG FLOOR
  - rules.json is a valid list of rules
  - flag-rules.py compiles
  - the team owns at least one skill

Run:  python3 teams/validate.py
"""
import json
import py_compile
import sys
import tempfile
from pathlib import Path

TEAMS = Path(__file__).resolve().parent

# The org-wide, non-negotiable policy floor. Teams may EXTEND their deny list;
# they may not drop these.
ORG_FLOOR_DENY = ("Bash(rm -rf:*)", "Bash(sudo:*)", "Bash(git push:*)")

MANDATE_SECTIONS = ("do not skip", "**Report.**", "Harness contract", "settings.json", "rules.json")


def validate() -> int:
    failures = []
    teams = sorted(d for d in TEAMS.iterdir()
                   if d.is_dir() and (d / "CLAUDE.md").exists())
    if not teams:
        print("no team folders found"); return 1
    for team in teams:
        name = team.name
        claude = team / ".claude"
        text = (team / "CLAUDE.md").read_text()
        for section in MANDATE_SECTIONS:
            if section not in text:
                failures.append(f"{name}: mandate missing {section!r}")
        owners = team / "OWNERS.md"
        if not owners.exists() or "Owner:" not in owners.read_text():
            failures.append(f"{name}: OWNERS.md missing or lacks an Owner: line")
        try:
            settings = json.loads((claude / "settings.json").read_text())
            deny = settings.get("permissions", {}).get("deny", [])
            for rule in ORG_FLOOR_DENY:
                if rule not in deny:
                    failures.append(f"{name}: settings.json drops org-floor deny {rule}")
        except Exception as e:
            failures.append(f"{name}: settings.json invalid ({e})")
        try:
            rules = json.loads((claude / "rules.json").read_text())
            assert isinstance(rules, list) and all("name" in r and "kind" in r for r in rules)
        except Exception as e:
            failures.append(f"{name}: rules.json invalid ({e})")
        for script in ("flag-rules.py", "phase-gate.py"):
            hook = claude / script
            if not hook.exists():
                failures.append(f"{name}: {script} missing")
            else:
                try:
                    py_compile.compile(str(hook), cfile=tempfile.mktemp(), doraise=True)
                except Exception as e:
                    failures.append(f"{name}: {script} does not compile ({e})")
        gate = claude / "phase-gate.py"
        if gate.exists():
            import re as _re
            declared = _re.search(r"PHASES = \[(.*?)\]", gate.read_text(), _re.S)
            gate_phases = _re.findall(r"'([^']+)'", declared.group(1)) if declared else []
            mandate_phases = _re.findall(r"^\d+\. \*\*([A-Za-z-]+)\.\*\*",
                                         text, _re.M)
            if gate_phases != mandate_phases:
                failures.append(f"{name}: phase-gate phases {gate_phases} != mandate phases {mandate_phases}")
        skills = claude / "skills"
        owned = [d.name for d in skills.iterdir() if (d / "SKILL.md").exists()] if skills.is_dir() else []
        if not owned:
            failures.append(f"{name}: owns no skills")
        if not failures or all(not f.startswith(name + ":") for f in failures):
            print(f"  {name}: OK ({len(owned)} skills, phase gate, org floor intact)")
    for f in failures:
        print(f"  FAIL {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(validate())
