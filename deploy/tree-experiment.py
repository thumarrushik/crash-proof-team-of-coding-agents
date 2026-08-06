#!/usr/bin/env python3
"""CONVERSATION TREE experiment — fork one durable session into N parallel
futures, judge, merge the winner. Everything OBSERVED, nothing modeled.

The claim under test: a forked session tournament is cache-warm BY
CONSTRUCTION. Public case studies show naive parallel fan-out on a shared
context stampedes the prompt cache (every branch pays its own cache WRITE
because none can read a cache that doesn't exist yet); the documented fix is a
synchronous warm-up call. A durable conversation IS that warm-up — the trunk
session wrote the cache while doing real work (investigating + authoring the
test suite), so the forks fan out onto cache READS.

Arms (same spec everywhere; model: haiku, judge: sonnet):
  SOLO     one continuous run of the whole task (cost floor / quality floor)
  TREE     trunk (red phase: tests + STRATEGIES.md, no implementation)
           -> git commit -> 3 CONCURRENT `--resume --fork-session` branches,
           one git worktree + one strategy each -> harness pytest per branch
           -> sonnet judge (itself a fork of the tree: it already knows the
           spec cache-warm) -> git merge of the winning branch
  INDEP    3 CONCURRENT independent runs of the whole task from scratch —
           the naive best-of-N everyone builds first (no shared trunk)

Measured: per-run cost/turns/cache read/write, per-batch wall clock, pytest
verdicts per candidate tree, judge verdict, merge result. Transcript lookup
for a fork inside a worktree relies on resume being scoped to the project
directory AND its git worktrees; a fallback copies the trunk transcript into
the worktree's project slug if that lookup misses (logged when used).

Run:  uv run python deploy/tree-experiment.py           (~30-50 min)
      uv run python deploy/tree-experiment.py --smoke   (fork mechanics, ~2 min)
"""
import concurrent.futures
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

MODEL, JUDGE_MODEL = "haiku", "sonnet"
N_FORKS = 3
TRUNK_TURNS, FORK_TURNS, FULL_TURNS = 12, 25, 40
ROOT = pathlib.Path("/tmp/tree-exp")
REPO = pathlib.Path(__file__).resolve().parent.parent
EVID = REPO / "experiment-results-tree"

SPEC = (
    "A Python virtualenv with pytest is ready at .venv — run tests with "
    ".venv/bin/pytest. The library to build: an event-sourced key-value store, "
    "module `eskv.py`, class `ESKV`:\n"
    "- set(key, value), get(key), delete(key) with KeyError on missing get/delete\n"
    "- history(key) -> list of (version, value) tuples, oldest first, where each "
    "set bumps that key's version starting at 1; delete appends a tombstone "
    "recorded as (version, None) and get on a deleted key raises KeyError\n"
    "- restore(key, version) -> re-sets the key to that version's value (raises "
    "ValueError for a tombstone or unknown version) and records it as a new set\n"
    "- keys() -> live (non-deleted) keys, insertion-ordered by first-ever set\n"
)
TRUNK_TASK = (
    "You are in an empty scratch git repository. RED PHASE ONLY — do not "
    "implement the library.\n" + SPEC +
    "Deliverables now:\n"
    "1. test_eskv.py — a thorough, implementation-agnostic (black-box, public "
    "API only) pytest suite for the whole spec, including edge cases.\n"
    "2. STRATEGIES.md — three MATERIALLY different internal designs that could "
    "all satisfy the spec (e.g. different core data layouts), numbered 1-3, "
    "each with its trade-offs in 3-4 sentences.\n"
    "Run the tests once to confirm they fail (no eskv.py yet), then stop."
)
# The first run of this experiment taught us the hard rule below: a forked
# conversation inherits the trunk's ABSOLUTE paths from its memory, and all
# three forks raced their implementations into the trunk checkout. The fork
# prompt must re-anchor the agent in its own worktree explicitly.
FORK_TASK = (
    "IMPORTANT: your working directory has CHANGED. You are now in {cwd}, a "
    "fresh git worktree of the same repository on branch strategy-{n}. "
    "STRATEGIES.md and test_eskv.py from the trunk commit are already present "
    "HERE. Work ONLY inside {cwd} using relative paths. Never read from, write "
    "to, or cd into the old trunk checkout, and do not create new worktrees or "
    "branches.\n"
    "Task: implement `eskv.py` in this directory following STRATEGY {n} from "
    "STRATEGIES.md exactly. Do NOT modify test_eskv.py or STRATEGIES.md. "
    "Iterate until the whole suite passes with .venv/bin/pytest, then stop."
)
FULL_TASK = (
    "You are in an empty scratch directory.\n" + SPEC +
    "Follow strict TDD: write a thorough black-box pytest suite test_eskv.py "
    "first, watch it fail, then implement eskv.py and iterate to 100% pass. "
    "Finish with a short REPORT.md."
)
SETTINGS = {"permissions": {"deny": ["Bash(rm -rf:*)", "Bash(sudo:*)", "Bash(git push:*)"]}}
GITIGNORE = ".venv/\n.claude/\n__pycache__/\n.pytest_cache/\n"


def sh(args, cwd, check=True, timeout=120):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"{args} failed in {cwd}: {p.stdout[-200:]} {p.stderr[-200:]}")
    return p


def seed_venv(ws):
    subprocess.run([sys.executable, "-m", "venv", str(ws / ".venv")], check=True,
                   capture_output=True)
    subprocess.run([str(ws / ".venv" / "bin" / "pip"), "install", "-q", "pytest"],
                   check=True, capture_output=True)


def workspace(tag, git=False):
    ws = ROOT / tag
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    (ws / ".claude").mkdir()
    (ws / ".claude" / "settings.json").write_text(json.dumps(SETTINGS, indent=2))
    (ws / ".gitignore").write_text(GITIGNORE)
    seed_venv(ws)
    if git:
        sh(["git", "init", "-q", "-b", "main"], ws)
        sh(["git", "-c", "user.email=exp@local", "-c", "user.name=exp",
            "commit", "-q", "--allow-empty", "-m", "init"], ws)
    return ws


def _slug(path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def _ensure_transcript_visible(trunk_ws, fork_ws, sid):
    """Fallback for fork-in-worktree resume: if the worktree's project slug has
    no copy of the trunk transcript, copy it in. Logged when actually used."""
    projects = pathlib.Path.home() / ".claude" / "projects"
    src = projects / _slug(trunk_ws) / f"{sid}.jsonl"
    dst_dir = projects / _slug(fork_ws)
    dst = dst_dir / f"{sid}.jsonl"
    if src.exists() and not dst.exists():
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def run(tag, ws, model, prompt, max_turns, resume=None, fork=False, timeout=1800):
    args = ["claude", "-p", "--output-format", "json", "--model", model,
            "--max-turns", str(max_turns), "--permission-mode", "acceptEdits",
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep"]
    if resume:
        args += ["--resume", resume]
    if fork:
        args += ["--fork-session"]
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
    p = subprocess.run([str(ws / ".venv" / "bin" / "pytest"), "-q", "--tb=no"],
                       capture_output=True, text=True, timeout=300, cwd=ws)
    tail = (p.stdout.strip().splitlines() or ["no output"])[-1]
    failed = sorted(line.split()[1] for line in p.stdout.splitlines()
                    if line.startswith("FAILED "))
    print(f"  [{tag}] pytest: {tail}", flush=True)
    return {"exit": p.returncode, "summary": tail, "failed": failed}


def row(o, arm, phase, model=MODEL):
    u = (o or {}).get("usage", {}) or {}
    return {
        "arm": arm, "phase": phase, "model": model,
        "cost": (o or {}).get("total_cost_usd"), "turns": (o or {}).get("num_turns"),
        "subtype": (o or {}).get("subtype"), "sid": (o or {}).get("session_id"),
        "cache_read": u.get("cache_read_input_tokens"),
        "cache_write": u.get("cache_creation_input_tokens"),
        "output": u.get("output_tokens"), "wall_s": (o or {}).get("_wall_s"),
    }


def fork_branch(trunk_ws, trunk_sid, n):
    """One tournament branch: worktree + venv + fork-resume + implement."""
    tag = f"TREE/fork{n}"
    fork_ws = ROOT / f"fork{n}"
    if fork_ws.exists():
        sh(["git", "worktree", "remove", "--force", str(fork_ws)], trunk_ws, check=False)
        shutil.rmtree(fork_ws, ignore_errors=True)
    sh(["git", "worktree", "add", "-q", "-b", f"strategy-{n}", str(fork_ws)], trunk_ws)
    (fork_ws / ".claude").mkdir(exist_ok=True)
    (fork_ws / ".claude" / "settings.json").write_text(json.dumps(SETTINGS, indent=2))
    seed_venv(fork_ws)
    copied = _ensure_transcript_visible(trunk_ws, fork_ws, trunk_sid)
    if copied:
        print(f"  [{tag}] transcript fallback copy used", flush=True)
    o = run(tag, fork_ws, MODEL, FORK_TASK.format(n=n, cwd=fork_ws), FORK_TURNS,
            resume=trunk_sid, fork=True)
    in_place = (fork_ws / "eskv.py").exists()
    if not in_place:
        print(f"  [{tag}] !! eskv.py missing from worktree (workspace escape?)", flush=True)
    return n, fork_ws, o, copied, in_place


def main():
    smoke = "--smoke" in sys.argv
    (EVID / "stdout").mkdir(parents=True, exist_ok=True)
    rows, meta = [], {}

    if smoke:
        print("=== SMOKE: fork-session in a worktree inherits the conversation ===", flush=True)
        ws = workspace("smoke", git=True)
        a = run("smoke/trunk", ws, MODEL, "Create marker.txt containing exactly the "
                "word: tangerine. Commit it with `git add -A && git commit -m marker` "
                "using -c user.email=exp@local -c user.name=exp. Then stop.", 6,
                timeout=300)
        if not a:
            sys.exit("smoke trunk failed")
        fw = ROOT / "smoke-fork"
        if fw.exists():
            sh(["git", "worktree", "remove", "--force", str(fw)], ws, check=False)
        sh(["git", "worktree", "add", "-q", "-b", "smoke-branch", str(fw)], ws)
        copied = _ensure_transcript_visible(ws, fw, a["session_id"])
        b = run("smoke/fork", fw, MODEL, "Without using any tools, answer from "
                "conversation memory only: what word did you write into marker.txt? "
                "Reply with just the word.", 1, resume=a["session_id"], fork=True,
                timeout=300)
        ok = bool(b) and "tangerine" in (b.get("result") or "").lower()
        distinct = bool(b) and b.get("session_id") != a.get("session_id")
        print(f"SMOKE {'PASS' if ok and distinct else 'FAIL'}: inherited={ok} "
              f"new_sid={distinct} fallback_copy={copied}", flush=True)
        sys.exit(0 if ok and distinct else 1)

    print("=== 1) SOLO baseline: one continuous run ===", flush=True)
    solo_ws = workspace("solo")
    o = run("SOLO/run", solo_ws, MODEL, FULL_TASK, FULL_TURNS)
    rows.append(row(o, "SOLO", "full"))
    meta["solo_pytest"] = pytest_check("SOLO", solo_ws)

    print("\n=== 2) TREE: trunk red phase (tests + strategies, no impl) ===", flush=True)
    trunk_ws = workspace("trunk", git=True)
    t = run("TREE/trunk", trunk_ws, MODEL, TRUNK_TASK, TRUNK_TURNS)
    if not t:
        sys.exit("trunk failed")
    rows.append(row(t, "TREE", "trunk"))
    sh(["git", "-c", "user.email=exp@local", "-c", "user.name=exp", "add", "-A"], trunk_ws)
    sh(["git", "-c", "user.email=exp@local", "-c", "user.name=exp",
        "commit", "-q", "-m", "trunk: tests + strategies"], trunk_ws)

    print(f"\n=== 3) TREE: {N_FORKS} CONCURRENT fork-session branches ===", flush=True)
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(N_FORKS) as ex:
        futures = [ex.submit(fork_branch, trunk_ws, t["session_id"], n)
                   for n in range(1, N_FORKS + 1)]
        forks = [f.result() for f in futures]
    meta["tree_fork_batch_wall_s"] = round(time.time() - t0, 1)
    print(f"  [TREE] fork batch wall={meta['tree_fork_batch_wall_s']}s", flush=True)
    fork_results = {}
    for n, fork_ws, o, copied, in_place in forks:
        rows.append(row(o, "TREE", f"fork{n}"))
        fork_results[n] = {"ws": fork_ws,
                           "pytest": pytest_check(f"TREE/fork{n}", fork_ws),
                           "fallback_copy": copied, "in_place": in_place}

    # The unanimity rule (shared.unanimous_failures): tests every diverse fork
    # failed indict the REFEREE, not the players — stop the fight, name the
    # suspect tests, and never merge against an indicted suite.
    sys.path.insert(0, str(REPO / "src"))
    from shared import unanimous_failures
    suspect_tests = sorted(unanimous_failures(
        [set(fork_results[n]["pytest"]["failed"]) for n in sorted(fork_results)]
    ))
    meta["referee_suspect_tests"] = suspect_tests
    if suspect_tests:
        print(f"  [TREE] UNANIMITY RULE: all forks failed {suspect_tests} — "
              f"the referee is indicted; routing the tests for review, no merge",
              flush=True)

    print("\n=== 4) TREE: judge (a sonnet fork of the same tree) ===", flush=True)
    diffs = []
    for n in range(1, N_FORKS + 1):
        d = sh(["git", "diff", "--stat", "main", f"strategy-{n}"], trunk_ws, check=False)
        diffs.append(f"--- STRATEGY {n} (pytest: {fork_results[n]['pytest']['summary']})\n"
                     f"{d.stdout[-600:]}")
    judge_prompt = (
        "You are judging the tournament you set up earlier in this session. Three "
        "worktree branches each implemented one of your STRATEGIES.md designs "
        "against your own test suite. Harness-run pytest verdicts and diffstats:\n\n"
        + "\n".join(diffs) +
        "\n\nWithout using any tools, pick the strongest candidate on correctness "
        "first (pytest), then simplicity/maintainability from the strategy "
        "trade-offs you wrote. Reply with EXACTLY two lines:\n"
        "WINNER: <1|2|3>\nWHY: <one sentence>"
    )
    j = run("TREE/judge", trunk_ws, JUDGE_MODEL, judge_prompt, 1,
            resume=t["session_id"], fork=True, timeout=600)
    rows.append(row(j, "TREE", "judge", model=JUDGE_MODEL))
    winner = None
    if j:
        m = re.search(r"WINNER:\s*([123])", j.get("result") or "")
        winner = int(m.group(1)) if m else None
    if winner is None or fork_results[winner]["pytest"]["exit"] != 0:
        passing = [n for n in fork_results if fork_results[n]["pytest"]["exit"] == 0]
        winner = passing[0] if passing else None
        meta["judge_overridden"] = True
    meta["winner"] = winner
    meta["judge_verdict"] = (j or {}).get("result")
    print(f"  [TREE] winner: strategy-{winner}", flush=True)

    if winner and not suspect_tests:
        print("\n=== 5) TREE: merge the winner into main ===", flush=True)
        mg = sh(["git", "-c", "user.email=exp@local", "-c", "user.name=exp",
                 "merge", "-q", "--no-ff", f"strategy-{winner}",
                 "-m", f"Merge strategy-{winner} (tournament winner)"],
                trunk_ws, check=False)
        meta["merged"] = mg.returncode == 0
        meta["trunk_pytest_after_merge"] = pytest_check("TREE/merged", trunk_ws)

    print(f"\n=== 6) INDEP: {N_FORKS} CONCURRENT independent runs (naive best-of-N) ===",
          flush=True)
    t0 = time.time()

    def indep(n):
        ws = workspace(f"indep{n}")
        return n, ws, run(f"INDEP/run{n}", ws, MODEL, FULL_TASK, FULL_TURNS)

    with concurrent.futures.ThreadPoolExecutor(N_FORKS) as ex:
        futures = [ex.submit(indep, n) for n in range(1, N_FORKS + 1)]
        indeps = [f.result() for f in futures]
    meta["indep_batch_wall_s"] = round(time.time() - t0, 1)
    print(f"  [INDEP] batch wall={meta['indep_batch_wall_s']}s", flush=True)
    for n, ws, o in indeps:
        rows.append(row(o, "INDEP", f"run{n}"))
        meta[f"indep{n}_pytest"] = pytest_check(f"INDEP/run{n}", ws)

    cols = list(rows[0].keys())
    with open(EVID / "runs.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")
    result = {"rows": rows, "meta": meta,
              "fork_pytest": {n: fork_results[n]["pytest"] for n in fork_results},
              "models": {"model": MODEL, "judge": JUDGE_MODEL}, "n_forks": N_FORKS}
    (EVID / "result.json").write_text(json.dumps(result, indent=2))
    print("\nRESULT_JSON " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
