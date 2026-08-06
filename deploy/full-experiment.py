#!/usr/bin/env python3
"""FULL cost experiment — everything OBSERVED, nothing modeled. Bare `claude -p`
(the same --resume the Temporal harness drives internally), run strictly
sequentially so no two agent runs overlap (concurrency contaminated an earlier
batch). Model: haiku. One substantial task -> a realistic prefix.

Measures the four scenarios the article needs:
  1. continuous C            — run the task to completion in one session (x3 for spread)
  2. warm boundary R_warm    — no-op resume of a fresh session, cache < 5 min (x5)
  3. chunked real total      — same task via N back-to-back --max-turns 2 resumes (x3),
                               so the multi-boundary total is measured, not N*R
  4. cold boundary R_cold    — no-op resume after a 65-min gap (> extended TTL) (x3),
                               so the cache-WRITE penalty is OBSERVED, not predicted

Order: all active runs first, the 65-min idle gap LAST, so nothing agent-heavy runs
during the wait. Writes JSON at the end (parsed by the article/plot step).

Run:  uv run python deploy/full-experiment.py   (~90 min incl. the cold gap)
"""
import json, subprocess, statistics, sys, time

MODEL = "haiku"
COLD_WAIT_S = 3900  # 65 min > any extended prompt-cache TTL
CHUNK_CAP = 20      # safety cap on chunk count

TASK = (
    "Implement kvstore.py: an in-memory key-value store class KVStore with methods "
    "get(key), set(key, value), delete(key), set_with_ttl(key, value, ttl_seconds) with "
    "lazy expiry on read, and LRU eviction when it exceeds max_size (constructor arg). "
    "Write a thorough pytest test_kvstore.py covering every method, TTL expiry, LRU "
    "eviction order, overwrite, missing keys, and the size limit. Follow strict TDD: "
    "write all the tests first, run them and watch them fail, then implement, and iterate "
    "until 100% pass. Finally write a short REPORT.md summarizing what you built."
)
CONT = "Continue where you left off. Keep following TDD until every test passes, then stop."
NOOP = "Reply with exactly: OK. Do not use any tools. Do not do any work."


def run(args, timeout=900):
    try:
        p = subprocess.run(["claude", "-p", "--output-format", "json", "--model", MODEL] + args,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("  !! timeout", flush=True)
        return None
    out = p.stdout.strip()
    try:
        return json.loads(out)
    except Exception:
        for line in reversed(out.splitlines()):
            try:
                o = json.loads(line)
                if "total_cost_usd" in o:
                    return o
            except Exception:
                pass
    print("  !! no json:", out[-300:], "| err:", p.stderr[-200:], flush=True)
    return None


def usage(o):
    u = o.get("usage", {}) or {}
    return (u.get("input_tokens", 0), u.get("cache_read_input_tokens", 0),
            u.get("cache_creation_input_tokens", 0), u.get("output_tokens", 0))


def prefix_of(o):
    inp, cr, cw, _ = usage(o)
    return inp + cr + cw


def continuous(tag):
    o = run(["--max-turns", "40", TASK])
    if not o:
        return None
    r = {"cost": o.get("total_cost_usd", 0.0), "sid": o.get("session_id"),
         "turns": o.get("num_turns"), "prefix": prefix_of(o), "subtype": o.get("subtype")}
    print(f"  [{tag}] cost=${r['cost']:.4f} turns={r['turns']} prefix={r['prefix']:,} {r['subtype']}", flush=True)
    return r


def chunked(tag):
    total, chunks, sid, per = 0.0, 0, None, []
    o = run(["--max-turns", "2", TASK])
    while o:
        chunks += 1
        c = o.get("total_cost_usd", 0.0)
        total += c
        sid = o.get("session_id")
        inp, cr, cw, out = usage(o)
        per.append({"cost": c, "cache_read": cr, "cache_write": cw})
        if o.get("subtype") == "success" or chunks >= CHUNK_CAP:
            break
        o = run(["--resume", sid, "--max-turns", "2", CONT])
    done = bool(o) and o.get("subtype") == "success"
    # boundary tax within this run = cache_read paid to re-establish prefix on resumes (chunks 2..N)
    boundary_read = sum(p["cache_read"] for p in per[1:])
    print(f"  [{tag}] total=${total:.4f} chunks={chunks} done={done} "
          f"boundary_cache_read={boundary_read:,}", flush=True)
    return {"total": total, "chunks": chunks, "done": done, "per": per, "boundary_read": boundary_read}


def resume_noop(sid, tag):
    o = run(["--resume", sid, "--max-turns", "1", NOOP], timeout=300)
    if not o:
        return None
    inp, cr, cw, out = usage(o)
    r = {"cost": o.get("total_cost_usd", 0.0), "cache_read": cr, "cache_write": cw, "prefix": inp + cr + cw}
    print(f"  [{tag}] cost=${r['cost']:.5f} cache_read={cr:,} cache_write={cw:,} "
          f"({'WARM' if cr > cw else 'COLD'})", flush=True)
    return r


def mean(xs):
    return statistics.mean(xs) if xs else 0.0


def main():
    print("=== 1) build session S + WARM resumes immediately (cache fresh) ===", flush=True)
    S = continuous("build/cont1")
    if not S:
        sys.exit("build failed")
    warm = [r for r in (resume_noop(S["sid"], f"warm{i+1}") for i in range(5)) if r]

    print("\n=== 2) continuous baseline x2 more (for C spread) ===", flush=True)
    conts = [S] + [c for c in (continuous(f"cont{i+2}") for i in range(2)) if c]

    print("\n=== 3) chunked real runs x3 (same task, back-to-back --max-turns 2) ===", flush=True)
    chunks = [c for c in (chunked(f"chunked{i+1}") for i in range(3)) if c]

    print(f"\n=== 4) idle {COLD_WAIT_S}s ({COLD_WAIT_S//60} min) so S's cache goes cold ===", flush=True)
    time.sleep(COLD_WAIT_S)

    print("=== 5) COLD resumes of S (observe the cache-WRITE) ===", flush=True)
    cold = [r for r in (resume_noop(S["sid"], f"cold{i+1}") for i in range(3)) if r]

    C = mean([c["cost"] for c in conts])
    Rw = mean([r["cost"] for r in warm])
    Rc = mean([r["cost"] for r in cold])
    chunk_total = mean([c["total"] for c in chunks])
    P = mean([r["prefix"] for r in (warm + cold)])
    n_boundaries = mean([c["chunks"] - 1 for c in chunks])
    result = {
        "model": MODEL, "prefix_tokens": P,
        "continuous": {"mean": C, "runs": [c["cost"] for c in conts], "prefix": mean([c["prefix"] for c in conts])},
        "warm_boundary": {"mean": Rw, "runs": [r["cost"] for r in warm], "cache_read": mean([r["cache_read"] for r in warm])},
        "cold_boundary": {"mean": Rc, "runs": [r["cost"] for r in cold],
                          "cache_read": mean([r["cache_read"] for r in cold]),
                          "cache_write": mean([r["cache_write"] for r in cold]),
                          "observed_cold": all(r["cache_write"] > r["cache_read"] for r in cold) if cold else False},
        "chunked": {"mean_total": chunk_total, "runs": [c["total"] for c in chunks],
                    "mean_boundaries": n_boundaries, "detail": chunks},
    }
    print("\n" + "=" * 66, flush=True)
    print(f"prefix ~{P:,.0f} tokens (haiku)", flush=True)
    print(f"C  continuous          = ${C:.4f}   runs={[round(c['cost'],4) for c in conts]}", flush=True)
    print(f"R_warm  per boundary   = ${Rw:.5f}  (cache-read)", flush=True)
    print(f"R_cold  per boundary   = ${Rc:.5f}  ({'cache-WRITE observed' if result['cold_boundary']['observed_cold'] else 'still warm?'})", flush=True)
    print(f"cold/warm ratio        = {Rc/Rw:.1f}x" if Rw else "n/a", flush=True)
    print(f"chunked real total     = ${chunk_total:.4f}  (~{n_boundaries:.0f} boundaries)  runs={[round(c['total'],4) for c in chunks]}", flush=True)
    print("=" * 66, flush=True)
    print("RESULT_JSON " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
