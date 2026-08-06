#!/usr/bin/env python3
"""Isolate the marginal cost of a session RESUME — the boundary/chunk tax — with
agent-work variance removed, decomposed by prompt-cache warmth.

Method (why this is a clean estimator, unlike total-cost-of-coarse-vs-fine):
  1. Build ONE real session to a realistic prefix P (a TDD task). Record its cost C.
  2. Resume that SAME session with a NO-OP prompt ("reply OK, no tools", --max-turns 1).
     The no-op does ~zero new work, so the measured cost IS the prefix re-establishment.
  3. Do the no-op resume WARM (immediately, cache < 5 min) and COLD (after > 5 min,
     cache TTL expired). Warm -> the prefix is cache-READ (0.1x). Cold -> cache-WRITE
     (1.25x, ~12x). We resume the ORIGINAL build session each time, so every trial
     sees the identical prefix P -> variance collapses.

Then the three scenarios the article needs fall straight out of C and R:
  - continuous (1 session, no boundary):      C
  - interrupted + resumed once (crash):       C + R_warm  (+ lost in-flight turn)
  - chunked N, back-to-back (warm):           C + N * R_warm   (~cost-neutral)
  - chunked N, spaced > 5 min (cold):         C + N * R_cold   (significant)

Cost is the CLI's own total_cost_usd (haiku); identical whether the worker runs on a
laptop or GCP — it's an Anthropic-API/prompt-cache property, not an infra one.

Run:  uv run python deploy/resume-cost.py        (takes ~9 min: builds, warm x3, sleep 6.5m, cold x3)
"""
import json, subprocess, sys, time, statistics

MODEL = "haiku"
COLD_WAIT_S = 390  # > 5 min so the 5-min prompt-cache TTL expires
BUILD_TASK = (
    "Build roman.py with two functions: int_to_roman(n) and roman_to_int(s), covering "
    "1..3999 both directions. Write a comprehensive pytest test_roman.py (base symbols, "
    "subtractive cases like 4/9/40/90, round-trips, and invalid input). Follow TDD: write "
    "the tests first, watch them fail, implement, iterate until all pass. Then summarize."
)
NOOP = "Reply with exactly: OK. Do not use any tools. Do not do any work."


def run_claude(args):
    p = subprocess.run(["claude", "-p", "--output-format", "json", "--model", MODEL] + args,
                       capture_output=True, text=True, timeout=600)
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
    print("!! no result json\nstdout tail:", out[-400:], "\nstderr:", p.stderr[-300:], flush=True)
    return None


def usage(o):
    u = o.get("usage", {}) or {}
    return (u.get("input_tokens", 0), u.get("output_tokens", 0),
            u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0))


def resume_noop(sid, tag):
    o = run_claude(["--resume", sid, "--max-turns", "1", NOOP])
    if not o:
        return None
    inp, out, cr, cw = usage(o)
    cost = o.get("total_cost_usd", 0.0)
    prefix = inp + cr + cw
    print(f"  [{tag}] cost=${cost:.5f}  prefix={prefix:,}  "
          f"cache_read={cr:,}  cache_write={cw:,}  out={out}  ({'WARM' if cr > cw else 'COLD'})",
          flush=True)
    return {"cost": cost, "prefix": prefix, "cache_read": cr, "cache_write": cw, "out": out}


def mean(xs):
    return statistics.mean(xs) if xs else 0.0


def main():
    print("=== 1) build a real session (measures C, the continuous base) ===", flush=True)
    b = run_claude([BUILD_TASK])
    if not b:
        sys.exit("build failed")
    sid = b.get("session_id")
    C = b.get("total_cost_usd", 0.0)
    bi, bo, bcr, bcw = usage(b)
    print(f"  session={sid}  C(continuous)=${C:.5f}  turns={b.get('num_turns')}  "
          f"prefix~={bi+bcr+bcw:,} (cache_read={bcr:,} cache_write={bcw:,})", flush=True)

    print("\n=== 2) WARM resumes (cache < 5 min) — the back-to-back-chunk / fast-crash case ===", flush=True)
    warm = [r for r in (resume_noop(sid, f"warm{i+1}") for i in range(3)) if r]

    print(f"\n=== 3) sleeping {COLD_WAIT_S}s so the 5-min prompt-cache TTL expires ===", flush=True)
    time.sleep(COLD_WAIT_S)

    print("=== 4) COLD resumes (cache > 5 min) — the spaced-chunk case ===", flush=True)
    cold = [r for r in (resume_noop(sid, f"cold{i+1}") for i in range(3)) if r]

    Rw = mean([r["cost"] for r in warm])
    Rc = mean([r["cost"] for r in cold])
    P = mean([r["prefix"] for r in (warm + cold)])
    print("\n" + "=" * 64, flush=True)
    print(f"C  (continuous, 1 session)     = ${C:.5f}", flush=True)
    print(f"R_warm (per boundary, cache<5m)= ${Rw:.5f}   (cache-read prefix ~{P:,.0f} tok)", flush=True)
    print(f"R_cold (per boundary, cache>5m)= ${Rc:.5f}   (cache-WRITE prefix)", flush=True)
    print(f"cold/warm ratio                = {Rc/Rw:.1f}x" if Rw else "n/a", flush=True)
    print("-" * 64, flush=True)
    print("Scenario cost (this task; N = boundary count):", flush=True)
    print(f"  continuous (1 session)              = ${C:.4f}", flush=True)
    print(f"  interrupted + resumed once (warm)   = ${C+Rw:.4f}  (C + R_warm)", flush=True)
    for N in (5, 10):
        print(f"  chunked N={N}, back-to-back (warm)   = ${C+N*Rw:.4f}  (C + {N}*R_warm)", flush=True)
        print(f"  chunked N={N}, spaced >5min (cold)   = ${C+N*Rc:.4f}  (C + {N}*R_cold)", flush=True)
    print("=" * 64, flush=True)
    print(json.dumps({"C": C, "R_warm": Rw, "R_cold": Rc, "prefix": P,
                      "warm": warm, "cold": cold}), flush=True)


if __name__ == "__main__":
    main()
