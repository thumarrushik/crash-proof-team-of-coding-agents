#!/usr/bin/env python3
"""Static end-to-end check: real GitHub issues -> real router -> real phases.

No Temporal workflow is started. This pulls the live issues from the app repo,
routes each through the same team_for_labels the poller uses, and prints the
phase task list that lane's phase gate would enforce — proving that each kind
of work gets its own kind of steps. Exits non-zero on any mismatch.

Usage: python3 deploy/issue-routing-check.py [owner/repo]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from team_service.orchestration import team_for_labels  # noqa: E402

APP_REPO = sys.argv[1] if len(sys.argv) > 1 else "thumarrushik/linkbox"

# What each issue SHOULD do, by its team label (unlabeled -> default lane).
EXPECTED_LANE = {
    "team/backend": "backend", "team/frontend": "frontend",
    "team/testing": "testing", "team/issues": "issues",
    "team/service-design": "service-design",
}


def phases_for(team: str) -> list[str]:
    gate = REPO_ROOT / "teams" / team / ".claude" / "phase-gate.py"
    declared = re.search(r"PHASES = \[(.*?)\]", gate.read_text(), re.S)
    return re.findall(r"'([^']+)'", declared.group(1))


def main() -> int:
    raw = subprocess.run(
        ["gh", "issue", "list", "-R", APP_REPO, "--state", "open",
         "--limit", "50", "--json", "number,title,labels"],
        capture_output=True, text=True, check=True).stdout
    issues = sorted(json.loads(raw), key=lambda i: i["number"])
    failures = []
    seen_phase_sets = {}
    for issue in issues:
        labels = [l["name"] for l in issue["labels"]]
        lane = team_for_labels(labels)
        team_labels = [l for l in labels if l.startswith("team/")]
        want = EXPECTED_LANE[team_labels[0]] if team_labels else "issues"
        phases = phases_for(lane)
        seen_phase_sets[lane] = phases
        ok = lane == want
        if not ok:
            failures.append(f"#{issue['number']} routed to {lane}, wanted {want}")
        print(f"#{issue['number']:>3} {'OK ' if ok else 'BAD'} -> {lane:<15} "
              f"[{' > '.join(phases)}]  {issue['title'][:48]}")
    distinct = {tuple(p) for p in seen_phase_sets.values()}
    print(f"\nlanes exercised: {len(seen_phase_sets)}; "
          f"distinct phase lists among them: {len(distinct)}")
    if len(distinct) < len(seen_phase_sets):
        failures.append("two lanes share an identical phase list — steps are "
                        "not differentiated by kind of work")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"ALL PASS ({len(issues)} issues routed; every lane's steps are its own)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
