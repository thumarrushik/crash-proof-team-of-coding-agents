#!/usr/bin/env python3
"""Confirm the COLD boundary cost by observing an actual cache-WRITE.

The warm/cold isolation run (deploy/resume-cost.py) found resumes were still
cache-READS at 6.5 min — the prompt cache stayed warm longer than the classic
5-min TTL. This probe waits well past any extended (1h) TTL, then resumes the
same built-up session with a no-op. If the prefix comes back as cache_creation
(a WRITE) instead of cache_read, we've observed the ~12x cold boundary directly.

Run:  uv run python deploy/cold-resume-probe.py <session_id> [wait_seconds]
"""
import json, subprocess, sys, time

SID = sys.argv[1] if len(sys.argv) > 1 else "caf8e55b-6f84-418d-a644-201869df0cdb"
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 3900  # 65 min > 1h extended TTL
NOOP = "Reply with exactly: OK. Do not use any tools. Do not do any work."


def run(args):
    p = subprocess.run(["claude", "-p", "--output-format", "json", "--model", "haiku"] + args,
                       capture_output=True, text=True, timeout=600)
    try:
        return json.loads(p.stdout.strip())
    except Exception:
        print("!! no json:", p.stdout[-300:], p.stderr[-200:], flush=True)
        return None


print(f"cold-probe: session={SID}  waiting {WAIT}s ({WAIT/60:.0f} min) for cache to go cold ...", flush=True)
time.sleep(WAIT)
o = run(["--resume", SID, "--max-turns", "1", NOOP])
if not o:
    sys.exit("resume failed")
u = o.get("usage", {}) or {}
cr = u.get("cache_read_input_tokens", 0)
cw = u.get("cache_creation_input_tokens", 0)
cost = o.get("total_cost_usd", 0.0)
verdict = "COLD (cache-WRITE — penalty observed)" if cw > cr else "still WARM (cache-read)"
print(f"cold-probe RESULT: cost=${cost:.5f}  cache_read={cr:,}  cache_write={cw:,}  -> {verdict}", flush=True)
print(json.dumps({"cost": cost, "cache_read": cr, "cache_write": cw, "wait_s": WAIT}), flush=True)
