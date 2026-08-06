#!/usr/bin/env python3
"""RELAY experiment — swap the model mid-conversation, keep the durable session.
Everything OBSERVED, nothing modeled. Bare `claude -p --resume` (the same resume
the Temporal harness drives internally), run strictly sequentially so no two
agent runs overlap. The harness-side ladder this measures lives in
`shared.model_for_chunk` (escalate the brain, keep the memory).

Questions, in measurement order:
  1. mechanics  — does resuming a haiku session with sonnet work at all?
  2. handoff tax — first sonnet touch of a haiku conversation cannot reuse
     haiku's prompt cache (caches are per-model), so it pays a cache-WRITE at
     sonnet rates. Observed via no-op resumes: sonnet cold touch, sonnet second
     touch (warm?), then haiku again (is haiku's own cache still alive?).
  3. the two strategies at the escalation moment, same fixed task:
       relay   — haiku builds a 6-turn prefix, sonnet resumes and finishes
       restart — sonnet runs the whole task from scratch
     Plus the no-escalation control: haiku builds the same prefix and haiku
     finishes it. Cost, turns, and an artifact check (pytest run by the
     harness afterwards) per arm.
  4. demotion  — haiku no-op-resumes a sonnet conversation (the cheap direction).

Workspaces: one stable scratch dir per session under /tmp/relay-exp (same-dir
resume is what the Temporal activity does with its job-derived work_dir). Each
workspace gets a pytest venv and the harness's own deny rules in
.claude/settings.json, so the experiment runs under the same policy the team
lanes do. Evidence: raw CLI result JSON per run + runs.tsv under
experiment-results-relay/, RESULT_JSON on stdout at the end.

Run:  uv run python deploy/relay-experiment.py          (~60-90 min)
      uv run python deploy/relay-experiment.py --smoke  (mechanics only, ~2 min)
"""
import json, os, pathlib, shutil, subprocess, sys, time

CHEAP, SMART = "haiku", "sonnet"
PREFIX_TURNS = 6      # the haiku investigation phase, deliberately mid-flight
FINISH_TURNS = 40
ROOT = pathlib.Path("/tmp/relay-exp")
REPO = pathlib.Path(__file__).resolve().parent.parent
EVID = REPO / "experiment-results-relay"

TASK = (
    "You are working in an empty scratch directory. A Python virtualenv with pytest "
    "is ready at .venv — run tests with .venv/bin/pytest. Implement a small Python "
    "library in three modules, following strict TDD (write tests first, run them and "
    "watch them fail, then implement, iterate to 100% pass):\n"
    "1. kvstore.py — class KVStore with get(key), set(key, value), delete(key), "
    "set_with_ttl(key, value, ttl_seconds) with lazy expiry on read, and LRU "
    "eviction when it exceeds max_size (constructor arg).\n"
    "2. txn.py — TransactionalKV wrapping a KVStore with begin()/commit()/rollback() "
    "and support for nested transactions.\n"
    "3. snapshot.py — save_snapshot(store, path) and load_snapshot(path) persisting "
    "live keys (with remaining TTLs) to JSON and restoring them.\n"
    "Write thorough suites test_kvstore.py, test_txn.py, test_snapshot.py. Finish "
    "with a short REPORT.md summarizing design decisions and test counts."
)
FINISH = (
    "Continue the task exactly where the previous turns left off. Check the working "
    "directory state first; do not redo work that is already done and passing. "
    "Follow the same strict TDD until every test passes, then write REPORT.md and stop."
)
NOOP = "Reply with exactly: OK. Do not use any tools. Do not do any work."

# The same deny rules the team workspaces get (see src/activities.py) — the
# experiment runs under the policy it is measuring.
SETTINGS = {"permissions": {"deny": ["Bash(rm -rf:*)", "Bash(sudo:*)", "Bash(git push:*)"]}}


def workspace(tag):
    ws = ROOT / tag
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    (ws / ".claude").mkdir()
    (ws / ".claude" / "settings.json").write_text(json.dumps(SETTINGS, indent=2))
    subprocess.run([sys.executable, "-m", "venv", str(ws / ".venv")], check=True,
                   capture_output=True)
    subprocess.run([str(ws / ".venv" / "bin" / "pip"), "install", "-q", "pytest"],
                   check=True, capture_output=True)
    return ws


def run(tag, ws, model, prompt, max_turns, resume=None, timeout=1800):
    args = ["claude", "-p", "--output-format", "json", "--model", model,
            "--max-turns", str(max_turns), "--permission-mode", "acceptEdits",
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep"]
    if resume:
        args += ["--resume", resume]
    # Prompt goes via stdin: --allowedTools is variadic and would swallow a
    # trailing positional prompt.
    t0 = time.time()
    try:
        p = subprocess.run(args, input=prompt, capture_output=True, text=True,
                           timeout=timeout, cwd=ws)
    except subprocess.TimeoutExpired:
        print(f"  [{tag}] !! timeout", flush=True)
        return None
    out = p.stdout.strip()
    o = None
    try:
        o = json.loads(out)
    except Exception:
        for line in reversed(out.splitlines()):
            try:
                cand = json.loads(line)
                if "total_cost_usd" in cand:
                    o = cand
                    break
            except Exception:
                pass
    if not o:
        print(f"  [{tag}] !! no json: {out[-300:]} | err: {p.stderr[-300:]}", flush=True)
        return None
    o["_wall_s"] = round(time.time() - t0, 1)
    (EVID / "stdout" / f"{tag.replace('/', '-')}.json").write_text(json.dumps(o, indent=2))
    u = o.get("usage", {}) or {}
    print(f"  [{tag}] {model} cost=${o.get('total_cost_usd', 0):.4f} "
          f"turns={o.get('num_turns')} {o.get('subtype')} "
          f"cache_read={u.get('cache_read_input_tokens', 0):,} "
          f"cache_write={u.get('cache_creation_input_tokens', 0):,} "
          f"wall={o['_wall_s']}s", flush=True)
    return o


def pytest_check(tag, ws):
    """Artifact check, run by the harness not the agent: does the arm's final
    tree actually pass its own suite?"""
    p = subprocess.run([str(ws / ".venv" / "bin" / "pytest"), "-q", "--tb=no"],
                       capture_output=True, text=True, timeout=300, cwd=ws)
    tail = (p.stdout.strip().splitlines() or ["no output"])[-1]
    print(f"  [{tag}] pytest: {tail}", flush=True)
    return {"exit": p.returncode, "summary": tail}


def row(o, arm, model, phase):
    u = (o or {}).get("usage", {}) or {}
    return {
        "arm": arm, "phase": phase, "model": model,
        "cost": (o or {}).get("total_cost_usd"), "turns": (o or {}).get("num_turns"),
        "subtype": (o or {}).get("subtype"), "sid": (o or {}).get("session_id"),
        "input": u.get("input_tokens"), "cache_read": u.get("cache_read_input_tokens"),
        "cache_write": u.get("cache_creation_input_tokens"),
        "output": u.get("output_tokens"), "wall_s": (o or {}).get("_wall_s"),
    }


def main():
    smoke = "--smoke" in sys.argv
    (EVID / "stdout").mkdir(parents=True, exist_ok=True)
    rows = []

    if smoke:
        print("=== SMOKE: cross-model resume mechanics only ===", flush=True)
        ws = workspace("smoke")
        a = run("smoke/build", ws, CHEAP, "Create a file named marker.txt containing "
                "exactly the word: pineapple. Then stop.", 4, timeout=300)
        if not a:
            sys.exit("smoke build failed")
        b = run("smoke/xresume", ws, SMART, "Without using any tools, answer from "
                "conversation memory only: what word did you write into marker.txt? "
                "Reply with just the word.", 1, resume=a["session_id"], timeout=300)
        ok = bool(b) and "pineapple" in (b.get("result") or "").lower()
        print(f"SMOKE {'PASS' if ok else 'FAIL'}: cross-model resume "
              f"{'inherited the conversation' if ok else 'did NOT inherit'}", flush=True)
        sys.exit(0 if ok else 1)

    print("=== 1) haiku builds 4 identical 6-turn prefixes (H1 probes, H2+H3 relay, "
          "H4 control) ===", flush=True)
    builds = {}
    for tag in ("H1", "H2", "H3", "H4"):
        ws = workspace(tag)
        o = run(f"{tag}/build", ws, CHEAP, TASK, PREFIX_TURNS)
        if not o:
            sys.exit(f"build {tag} failed")
        if o.get("subtype") == "success":
            print(f"  [{tag}] !! calibration miss: finished within the prefix cap", flush=True)
        builds[tag] = {"ws": ws, "o": o}
        rows.append(row(o, tag, CHEAP, "build"))

    print("\n=== 2) handoff-tax probes on H1 (no-op resumes) ===", flush=True)
    h1 = builds["H1"]
    p1 = run("H1/sonnet-noop-1", h1["ws"], SMART, NOOP, 1,
             resume=h1["o"]["session_id"], timeout=300)
    if not p1:
        sys.exit("cross-model resume failed — aborting before the expensive arms")
    p2 = run("H1/sonnet-noop-2", h1["ws"], SMART, NOOP, 1,
             resume=p1["session_id"], timeout=300)
    p3 = run("H1/haiku-noop", h1["ws"], CHEAP, NOOP, 1,
             resume=(p2 or p1)["session_id"], timeout=300)
    rows += [row(p1, "H1", SMART, "noop-cold"), row(p2, "H1", SMART, "noop-warm"),
             row(p3, "H1", CHEAP, "noop-back")]

    print("\n=== 3) RELAY: sonnet resumes H2 and H3 and finishes ===", flush=True)
    checks = {}
    for tag in ("H2", "H3"):
        b = builds[tag]
        o = run(f"{tag}/relay-finish", b["ws"], SMART, FINISH, FINISH_TURNS,
                resume=b["o"]["session_id"])
        rows.append(row(o, tag, SMART, "relay-finish"))
        checks[tag] = pytest_check(tag, b["ws"])

    print("\n=== 4) CONTROL: haiku resumes H4 and finishes (no escalation) ===", flush=True)
    b = builds["H4"]
    o = run("H4/haiku-finish", b["ws"], CHEAP, FINISH, FINISH_TURNS,
            resume=b["o"]["session_id"])
    rows.append(row(o, "H4", CHEAP, "haiku-finish"))
    checks["H4"] = pytest_check("H4", b["ws"])

    print("\n=== 5) RESTART: sonnet runs the whole task from scratch x2 ===", flush=True)
    sonnet_sid = None
    for tag in ("S1", "S2"):
        ws = workspace(tag)
        o = run(f"{tag}/scratch", ws, SMART, TASK, FINISH_TURNS)
        rows.append(row(o, tag, SMART, "scratch"))
        checks[tag] = pytest_check(tag, ws)
        if o and not sonnet_sid:
            sonnet_sid = o["session_id"]
            sonnet_ws = ws

    print("\n=== 6) DEMOTION probe: haiku no-op-resumes the S1 sonnet session ===", flush=True)
    if sonnet_sid:
        d = run("S1/haiku-noop", sonnet_ws, CHEAP, NOOP, 1, resume=sonnet_sid, timeout=300)
        rows.append(row(d, "S1", CHEAP, "noop-demote"))

    cols = list(rows[0].keys())
    with open(EVID / "runs.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")
    result = {"rows": rows, "pytest": checks, "prefix_turns": PREFIX_TURNS,
              "models": {"cheap": CHEAP, "smart": SMART}}
    (EVID / "result.json").write_text(json.dumps(result, indent=2))
    print("\nRESULT_JSON " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
