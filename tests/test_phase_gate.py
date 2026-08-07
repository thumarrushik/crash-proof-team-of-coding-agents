import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from activities import _bootstrap_workspace
from shared import known_teams

REPO = Path(__file__).resolve().parent.parent
TEAMS = REPO / "teams"


def gate_phases(team: str) -> list[str]:
    text = (TEAMS / team / ".claude" / "phase-gate.py").read_text()
    declared = re.search(r"PHASES = \[(.*?)\]", text, re.S)
    return re.findall(r"'([^']+)'", declared.group(1))


def run_gate(team: str, work_dir: Path) -> dict | None:
    """Run the team's phase gate as the Stop hook would: cwd = workspace,
    hook input on stdin. Returns the parsed block decision, or None (allow)."""
    proc = subprocess.run(
        [sys.executable, str(TEAMS / team / ".claude" / "phase-gate.py")],
        input=json.dumps({"stop_hook_active": False}),
        capture_output=True, text=True, cwd=work_dir, timeout=30,
    )
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def log_todowrite(work_dir: Path, todos: list[dict]) -> None:
    (work_dir / ".claude").mkdir(exist_ok=True)
    with open(work_dir / ".claude" / "hook-log.jsonl", "a") as f:
        f.write(json.dumps({"tool_name": "TodoWrite",
                            "tool_input": {"todos": todos}}) + "\n")


def log_taskboard(work_dir: Path, names: list[str], completed: set[str]) -> None:
    """The other dialect, exactly as live runs log it: TaskCreate with the id
    in tool_response, then TaskUpdate status changes addressed by taskId."""
    (work_dir / ".claude").mkdir(exist_ok=True)
    with open(work_dir / ".claude" / "hook-log.jsonl", "a") as f:
        for i, name in enumerate(names, start=1):
            f.write(json.dumps({
                "tool_name": "TaskCreate",
                "tool_input": {"subject": name, "description": name},
                "tool_response": {"task": {"id": str(i), "subject": name}},
            }) + "\n")
            if name in completed:
                f.write(json.dumps({
                    "tool_name": "TaskUpdate",
                    "tool_input": {"taskId": str(i), "status": "completed"},
                }) + "\n")


class PhaseGateTests(unittest.TestCase):
    """The work-issue discipline, enforced mechanically: every triggered run
    must create the SAME phase task list and complete it before it can stop."""

    def test_gate_phases_match_the_mandate_exactly(self) -> None:
        for team in known_teams():
            with self.subTest(team=team):
                mandate_phases = re.findall(
                    r"^\d+\. \*\*([A-Za-z-]+)\.\*\*",
                    (TEAMS / team / "CLAUDE.md").read_text(), re.M)
                self.assertEqual(gate_phases(team), mandate_phases,
                                 f"{team}: gate and mandate phases drifted")

    def test_each_lane_owns_distinct_phases(self) -> None:
        """Each kind of work needs its own kind of steps: no two lanes may
        share an identical phase list, every lane self-reviews, and every
        lane's last phase is Report (the harness reads what Report produces)."""
        all_phases = {team: gate_phases(team) for team in known_teams()}
        as_tuples = {tuple(p) for p in all_phases.values()}
        self.assertEqual(len(as_tuples), len(all_phases),
                         f"lanes share a phase list: {all_phases}")
        for team, phases in all_phases.items():
            self.assertIn("Self-review", phases, f"{team} never self-reviews")
            self.assertEqual(phases[-1], "Report",
                             f"{team} must end at Report, got {phases[-1]}")

    def test_no_task_list_blocks_the_stop(self) -> None:
        for team in known_teams():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)
                (work_dir / ".claude").mkdir()
                decision = run_gate(team, work_dir)
                self.assertIsNotNone(decision, f"{team}: empty run must block")
                self.assertEqual(decision["decision"], "block")
                for phase in gate_phases(team):     # the fix is in the reason
                    self.assertIn(phase, decision["reason"])

    def test_complete_phase_list_allows_the_stop(self) -> None:
        for team in known_teams():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)
                log_todowrite(work_dir, [
                    {"content": f"{p} the task", "status": "completed"}
                    for p in gate_phases(team)])
                self.assertIsNone(run_gate(team, work_dir),
                                  f"{team}: completed list must allow")

    def test_missing_phase_blocks_and_names_it(self) -> None:
        for team in known_teams():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)
                phases = gate_phases(team)
                log_todowrite(work_dir, [
                    {"content": f"{p} the task", "status": "completed"}
                    for p in phases if p != "Self-review"])
                decision = run_gate(team, work_dir)
                self.assertEqual(decision["decision"], "block")
                self.assertIn("Self-review", decision["reason"])

    def test_phase_must_lead_the_task_name(self) -> None:
        """The mandate says tasks are NAMED for the phases — a task that only
        mentions a phase word mid-sentence ("run the tests…") must not satisfy
        that phase. Substring matching allowed exactly that; prefix matching
        is the contract."""
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            phases = gate_phases("backend")
            todos = [{"content": f"{p} the task", "status": "completed"}
                     for p in phases if p != "Test"]
            todos.append({"content": "run the tests and show output",
                          "status": "completed"})
            log_todowrite(work_dir, todos)
            decision = run_gate("backend", work_dir)
            self.assertIsNotNone(decision, "mid-sentence 'tests' must not count")
            self.assertEqual(decision["decision"], "block")
            self.assertIn("Test", decision["reason"])

    def test_unfinished_phase_blocks_until_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            phases = gate_phases("backend")
            todos = [{"content": f"{p} the task", "status": "completed"}
                     for p in phases]
            todos[-1]["status"] = "in_progress"
            log_todowrite(work_dir, todos)
            decision = run_gate("backend", work_dir)
            self.assertEqual(decision["decision"], "block")
            self.assertIn("Report", decision["reason"])
            # the agent completes the last phase; the gate lets go
            log_todowrite(work_dir, [{"content": f"{p} the task",
                                      "status": "completed"} for p in phases])
            self.assertIsNone(run_gate("backend", work_dir))

    def test_taskcreate_dialect_complete_board_allows(self) -> None:
        """Live runs showed agents building the phase list with TaskCreate/
        TaskUpdate instead of TodoWrite — the pilot's backend agent created
        exactly its six phases and completed all of them, and the gate still
        blocked because it only spoke TodoWrite. Both dialects must pass."""
        for team in known_teams():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)
                phases = gate_phases(team)
                log_taskboard(work_dir, phases, completed=set(phases))
                self.assertIsNone(run_gate(team, work_dir),
                                  f"{team}: completed task board must allow")

    def test_taskcreate_dialect_unfinished_phase_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            phases = gate_phases("backend")
            log_taskboard(work_dir, phases, completed=set(phases) - {"Report"})
            decision = run_gate("backend", work_dir)
            self.assertEqual(decision["decision"], "block")
            self.assertIn("Report", decision["reason"])

    def test_taskcreate_dialect_missing_phase_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            phases = [p for p in gate_phases("backend") if p != "Self-review"]
            log_taskboard(work_dir, phases, completed=set(phases))
            decision = run_gate("backend", work_dir)
            self.assertEqual(decision["decision"], "block")
            self.assertIn("Self-review", decision["reason"])

    def test_returned_report_satisfies_the_report_phase(self) -> None:
        """Fleet learning: every run was blocked exactly once because agents
        stop at the moment they return structured output — one beat before
        marking the final task. The report IS the Report phase's completion."""
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            phases = gate_phases("backend")
            # all phases completed except Report, but StructuredOutput returned
            log_taskboard(work_dir, phases, completed=set(phases) - {"Report"})
            with open(work_dir / ".claude" / "hook-log.jsonl", "a") as f:
                f.write(json.dumps({"tool_name": "StructuredOutput",
                                    "tool_input": {}}) + "\n")
            self.assertIsNone(run_gate("backend", work_dir),
                              "returned report must satisfy the Report phase")

    def test_deadlock_guard_allows_after_three_blocks(self) -> None:
        """The gate never wedges a run: past MAX_BLOCKS it allows and leaves
        the miss in the audit trail (the Stop-gate article's ~8-block lesson)."""
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            (work_dir / ".claude").mkdir()
            for _ in range(3):
                self.assertIsNotNone(run_gate("backend", work_dir))
            self.assertIsNone(run_gate("backend", work_dir),
                              "fourth stop must be allowed through")

    def test_bootstrap_resets_the_deadlock_budget_each_chunk(self) -> None:
        """A chunk that burned its 3 blocks must not disarm the gate for the
        next chunk — the per-chunk policy stamp clears the counter."""
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            _bootstrap_workspace(work_dir, "backend")
            (work_dir / ".claude" / "phase-gate-blocks").write_text("3")
            self.assertIsNone(run_gate("backend", work_dir))   # gate disarmed
            _bootstrap_workspace(work_dir, "backend")          # next chunk
            decision = run_gate("backend", work_dir)
            self.assertIsNotNone(decision, "fresh chunk must re-arm the gate")
            self.assertEqual(decision["decision"], "block")

    def test_bootstrap_stamps_the_gate_and_wires_the_stop_hook(self) -> None:
        for team in known_teams():
            with self.subTest(team=team), tempfile.TemporaryDirectory() as tmp:
                work_dir = Path(tmp)
                _bootstrap_workspace(work_dir, team)
                stamped = work_dir / ".claude" / "phase-gate.py"
                self.assertTrue(stamped.exists(), f"{team}: gate not stamped")
                self.assertEqual(
                    stamped.read_text(),
                    (TEAMS / team / ".claude" / "phase-gate.py").read_text())
                settings = json.loads(
                    (work_dir / ".claude" / "settings.json").read_text())
                stop = settings["hooks"]["Stop"][0]["hooks"][0]["command"]
                self.assertEqual(stop, "python3 .claude/phase-gate.py")


if __name__ == "__main__":
    unittest.main()
