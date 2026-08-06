"""Economics canary: the article-series measurements as a scheduled probe.

Every load-bearing number this project has published — the cheap same-model
warm resume, the one-time cross-model handoff tax, fork inheritance, session
recall — is an invariant of the provider's current behavior (cache TTLs,
pricing tiers, resume semantics). Those change silently. This module turns
each invariant into a tiny typed probe with a generous band derived from the
published measurements, so a regime change trips an alert instead of quietly
turning the write-ups into fiction. A full canary run is ~$0.15 and a couple
of minutes.

Modes (mirrors poller.py):
    # create the Temporal Schedule (recommended; runs on the poller queue)
    uv run canary.py --schedule [--interval-hours 24]

    # one local run, no worker needed
    uv run canary.py --once

Probes, in order, all against one throwaway session:
    seed          haiku writes one marker word to a file (the substrate)
    warm_resume   haiku no-op resume        -> cheap, cache-read dominated
    handoff_tax   sonnet no-op resume       -> one-time cache WRITE at sonnet rates
    fork_warmth   haiku no-op fork-resume   -> cheap, mints a NEW session id
    integrity     a fork recalls the marker word with tools forbidden

Bands are deliberately generous (roughly 3x around the measured values in
deploy/*-results.md): the canary is for regime changes, not noise.
"""

import argparse
import asyncio
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
)
from temporalio.common import RetryPolicy

from shared import (
    DEFAULT_NAMESPACE,
    POLLER_TASK_QUEUE,
    TEMPORAL_ADDRESS,
    CanaryReport,
)

CHEAP, SMART = "haiku", "sonnet"
MARKER = "juniper"
NOOP = "Reply with exactly: OK. Do not use any tools. Do not do any work."
RECALL = ("Without using any tools, answer from conversation memory only: what "
          "word did you write into note.txt? Reply with just the word.")

# name -> (cost_min, cost_max, extra-check key). Extra checks are mechanistic
# invariants, sturdier than dollar bands: cache direction, new session id,
# marker recall.
BANDS: dict[str, tuple[float, float, str | None]] = {
    "seed":        (0.004,  0.08, None),
    "warm_resume": (0.0008, 0.02, "cache_read_min_5k"),
    "handoff_tax": (0.02,   0.25, "cache_write_min_5k"),
    "fork_warmth": (0.002,  0.06, "new_session_id"),
    "integrity":   (0.002,  0.06, "recalled_marker"),
}


# Adaptive cadence: the canary decides its own next run from what it just
# measured. Alerts investigate (1h); a value near a band edge watches (6h);
# a long clean streak stretches toward the cap. Pure functions, so the
# workflow can call them deterministically and tests can pin them.
BASE_INTERVAL_H, MIN_INTERVAL_H, MAX_INTERVAL_H = 24.0, 1.0, 48.0
CLEAN_STREAK_TO_STRETCH = 7


def near_band_edge(name: str, m: dict) -> bool:
    """Within 1.5x of either band edge — healthy, but worth watching."""
    cost = m.get("cost")
    if cost is None:
        return False
    lo, hi, _ = BANDS[name]
    return cost < lo * 1.5 or cost > hi / 1.5


def next_interval_hours(history: list[dict]) -> float:
    """History = oldest-first pass summaries ({'alerts': [...], 'probes': {...}})."""
    if not history:
        return BASE_INTERVAL_H
    last = history[-1]
    if last.get("alerts"):
        return MIN_INTERVAL_H
    if any(near_band_edge(n, (last.get("probes") or {}).get(n, {})) for n in BANDS):
        return 6.0
    clean = 0
    for entry in reversed(history):
        if entry.get("alerts"):
            break
        clean += 1
    if clean >= CLEAN_STREAK_TO_STRETCH:
        return MAX_INTERVAL_H
    return BASE_INTERVAL_H


def evaluate_probe(name: str, m: dict) -> list[str]:
    """Pure band check: return the list of alert strings (empty = healthy)."""
    lo, hi, extra = BANDS[name]
    alerts: list[str] = []
    cost = m.get("cost")
    if cost is None:
        return [f"{name}: probe produced no result"]
    if not (lo <= cost <= hi):
        alerts.append(f"{name}: cost ${cost:.4f} outside band [${lo}, ${hi}]")
    if extra == "cache_read_min_5k" and m.get("cache_read", 0) < 5000:
        alerts.append(f"{name}: cache_read {m.get('cache_read')} < 5k — resume no longer warm?")
    if extra == "cache_write_min_5k" and m.get("cache_write", 0) < 5000:
        alerts.append(f"{name}: cache_write {m.get('cache_write')} < 5k — cross-model cache sharing?!")
    if extra == "new_session_id" and not m.get("new_session_id"):
        alerts.append(f"{name}: fork did not mint a new session id")
    if extra == "recalled_marker" and not m.get("recalled"):
        alerts.append(f"{name}: fork failed to recall the planted marker")
    return alerts


def _claude(ws, model, prompt, max_turns, resume=None, fork=False, timeout=420):
    args = ["claude", "-p", "--output-format", "json", "--model", model,
            "--max-turns", str(max_turns), "--permission-mode", "acceptEdits",
            "--allowedTools", "Bash,Read,Write,Edit"]
    if resume:
        args += ["--resume", resume]
    if fork:
        args += ["--fork-session"]
    t0 = time.time()
    p = subprocess.run(args, input=prompt, capture_output=True, text=True,
                       timeout=timeout, cwd=ws)
    out = p.stdout.strip()
    try:
        o = json.loads(out)
    except Exception:
        o = None
        for line in reversed(out.splitlines()):
            try:
                cand = json.loads(line)
                if "total_cost_usd" in cand:
                    o = cand
                    break
            except Exception:
                pass
    if not o:
        return None
    u = o.get("usage", {}) or {}
    return {
        "cost": o.get("total_cost_usd"),
        "sid": o.get("session_id"),
        "subtype": o.get("subtype"),
        "result": o.get("result"),
        "cache_read": u.get("cache_read_input_tokens", 0),
        "cache_write": u.get("cache_creation_input_tokens", 0),
        "wall_s": round(time.time() - t0, 1),
    }


def run_probes() -> CanaryReport:
    """One full canary pass. Plain function so `--once` needs no Temporal."""
    ws = pathlib.Path(tempfile.mkdtemp(prefix="canary-"))
    probes: dict[str, dict] = {}

    seed = _claude(ws, CHEAP, f"Create a file note.txt containing exactly the "
                              f"word: {MARKER}. Then stop.", 4)
    probes["seed"] = dict(seed or {}, ok=bool(seed))
    sid = (seed or {}).get("sid")

    if sid:
        warm = _claude(ws, CHEAP, NOOP, 1, resume=sid)
        probes["warm_resume"] = dict(warm or {})

        handoff = _claude(ws, SMART, NOOP, 1, resume=sid)
        probes["handoff_tax"] = dict(handoff or {})

        forked = _claude(ws, CHEAP, NOOP, 1, resume=sid, fork=True)
        probes["fork_warmth"] = dict(forked or {},
                                     new_session_id=bool(forked)
                                     and forked.get("sid") not in (None, sid))

        recall = _claude(ws, CHEAP, RECALL, 1, resume=sid, fork=True)
        probes["integrity"] = dict(recall or {},
                                   recalled=bool(recall)
                                   and MARKER in (recall.get("result") or "").lower())

    alerts: list[str] = []
    for name in BANDS:
        alerts += evaluate_probe(name, probes.get(name, {}))
    total = sum(p.get("cost") or 0.0 for p in probes.values())
    report = CanaryReport(
        ts=time.time(),
        passed=not alerts,
        alerts=alerts,
        total_cost_usd=round(total, 5),
        probes={k: {kk: vv for kk, vv in v.items() if kk != "result"}
                for k, v in probes.items()},
    )
    _append_history(report)
    return report


def _append_history(report: CanaryReport) -> None:
    hist_dir = pathlib.Path(os.environ.get(
        "CANARY_HISTORY_DIR",
        pathlib.Path(__file__).resolve().parents[1] / "experiment-results-canary"))
    hist_dir.mkdir(parents=True, exist_ok=True)
    with (hist_dir / "history.jsonl").open("a") as f:
        f.write(json.dumps({
            "ts": report.ts, "passed": report.passed, "alerts": report.alerts,
            "total_cost_usd": report.total_cost_usd, "probes": report.probes,
        }) + "\n")


@activity.defn
async def run_canary_probes() -> CanaryReport:
    return await asyncio.to_thread(run_probes)


@workflow.defn
class EconomicsCanary:
    """One scheduled canary pass: probe the published invariants, alert on
    band violations. The report (typed) is the workflow result, queryable
    forever in the event history — the longitudinal dataset is the history
    JSONL the activity appends."""

    @workflow.run
    async def run(self) -> CanaryReport:
        report = await workflow.execute_activity(
            run_canary_probes,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        if report.alerts:
            workflow.logger.warning(
                "ECONOMICS CANARY ALERT: %s", "; ".join(report.alerts)
            )
        return report


@workflow.defn
class AdaptiveCanary:
    """The schedule that sets its own alarm. One durable workflow replaces the
    cron line AND the fixed Temporal Schedule: it runs a pass, decides its own
    next interval from the typed results (alerts investigate hourly, near-band
    values watch 6-hourly, a clean week stretches to the 48h cap), sleeps, and
    continues-as-new carrying a bounded history window. Killing the cadence
    logic requires killing a durable workflow — not silently losing a crontab."""

    @workflow.run
    async def run(self, history: list[dict] | None = None) -> None:
        history = (history or [])[-14:]
        report = await workflow.execute_activity(
            run_canary_probes,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        if report.alerts:
            workflow.logger.warning(
                "ECONOMICS CANARY ALERT: %s", "; ".join(report.alerts)
            )
        history.append({"alerts": report.alerts, "probes": report.probes})
        interval = next_interval_hours(history)
        workflow.logger.info("adaptive canary: next pass in %.1fh", interval)
        await workflow.sleep(timedelta(hours=interval))
        workflow.continue_as_new(history[-14:])


async def _start_adaptive(namespace: str) -> None:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)
    await client.start_workflow(
        AdaptiveCanary.run,
        id="economics-canary-adaptive",
        task_queue=POLLER_TASK_QUEUE,
    )
    print(f"AdaptiveCanary started on {POLLER_TASK_QUEUE} — it schedules itself from here")


async def _create_schedule(namespace: str, schedule_id: str, hours: int) -> None:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)
    await client.create_schedule(
        schedule_id,
        Schedule(
            action=ScheduleActionStartWorkflow(
                EconomicsCanary.run,
                id="economics-canary-run",
                task_queue=POLLER_TASK_QUEUE,
            ),
            spec=ScheduleSpec(
                intervals=[ScheduleIntervalSpec(every=timedelta(hours=hours))]
            ),
        ),
    )
    print(f"Schedule '{schedule_id}' created: every {hours}h on {POLLER_TASK_QUEUE}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Economics canary for the agent harness")
    parser.add_argument("--once", action="store_true", help="Run the probes locally, no worker")
    parser.add_argument("--schedule", action="store_true", help="Create the fixed Temporal Schedule")
    parser.add_argument("--adaptive", action="store_true",
                        help="Start the self-scheduling AdaptiveCanary workflow instead")
    parser.add_argument("--schedule-id", default="economics-canary")
    parser.add_argument("--interval-hours", type=int, default=24)
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE)
    args = parser.parse_args()

    if args.adaptive:
        await _start_adaptive(args.namespace)
        return
    if args.schedule:
        await _create_schedule(args.namespace, args.schedule_id, args.interval_hours)
        return
    if args.once:
        report = await asyncio.to_thread(run_probes)
        print(json.dumps({
            "passed": report.passed, "alerts": report.alerts,
            "total_cost_usd": report.total_cost_usd, "probes": report.probes,
        }, indent=2))
        sys.exit(0 if report.passed else 1)
    parser.error("pass --once, --schedule, or --adaptive")


if __name__ == "__main__":
    asyncio.run(main())
