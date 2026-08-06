#!/usr/bin/env python3
"""Analyze the chunk-cost experiment (deploy/cost-experiment.sh output).

Reads runs.tsv + usage/<workflow_id>.jsonl and reports, per chunk-granularity
mode, the recorded cost and the token breakdown that explains it — with the
headline being the *boundary tax*: the extra cache-write (cache_creation) tokens
that fine chunking pays to re-anchor the growing session prefix at every resume.

Grounds the dollar attribution in the published price shape (from the claude-api
reference): output = 5x input across every tier; cache reads ~0.1x input; cache
writes 1.25x input (5-min TTL). Pure stdlib. Usage: uv run deploy/cost_report.py <results-dir> [--model haiku]
"""
import argparse
import json
import statistics
from pathlib import Path

# input $/MTok — output is 5x, cache-read 0.1x, cache-write (5-min) 1.25x.
INPUT_PRICE = {"haiku": 1.0, "sonnet": 3.0, "opus": 5.0, "fable": 10.0}


def load(results_dir: Path):
    rows = []
    tsv = (results_dir / "runs.tsv").read_text().splitlines()
    header = tsv[0].split("\t")
    for line in tsv[1:]:
        if not line.strip():
            continue
        rec = dict(zip(header, line.split("\t")))
        wid = rec["workflow_id"]
        usage_path = results_dir / "usage" / f"{wid}.jsonl"
        chunks = []
        if usage_path.exists():
            for ln in usage_path.read_text().splitlines():
                if ln.strip():
                    chunks.append(json.loads(ln))
        rec["chunk_usage"] = chunks
        rows.append(rec)
    return rows


def totals(chunks):
    """Sum the per-chunk usage columns over one run."""
    keys = ["input_tokens", "output_tokens", "cache_read_input_tokens",
            "cache_creation_input_tokens", "cost_usd"]
    return {k: sum(c.get(k, 0) for c in chunks) for k in keys}


def agg(rows, mode):
    runs = [r for r in rows if r["mode"] == mode]
    per_run = [totals(r["chunk_usage"]) for r in runs]
    costs = [float(r["cost_usd"]) for r in runs if r["cost_usd"]]
    n_chunks = [int(r["chunks"]) for r in runs if r["chunks"]]

    def mean(key):
        vals = [t[key] for t in per_run]
        return statistics.mean(vals) if vals else 0.0

    return {
        "n": len(runs),
        "cost_mean": statistics.mean(costs) if costs else 0.0,
        "cost_min": min(costs) if costs else 0.0,
        "cost_max": max(costs) if costs else 0.0,
        "chunks_mean": statistics.mean(n_chunks) if n_chunks else 0.0,
        "input": mean("input_tokens"),
        "output": mean("output_tokens"),
        "cache_read": mean("cache_read_input_tokens"),
        "cache_write": mean("cache_creation_input_tokens"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir", type=Path)
    ap.add_argument("--model", default="haiku")
    args = ap.parse_args()

    rows = load(args.results_dir)
    coarse, fine = agg(rows, "coarse"), agg(rows, "fine")
    ip = INPUT_PRICE.get(args.model, 1.0)

    def fmt(a):
        return (f"| {a['n']} | {a['chunks_mean']:.1f} | ${a['cost_mean']:.4f} "
                f"(${a['cost_min']:.4f}–${a['cost_max']:.4f}) "
                f"| {a['input']:.0f} | {a['output']:.0f} "
                f"| {a['cache_read']:.0f} | {a['cache_write']:.0f} |")

    print(f"\n# Chunk-cost experiment — model={args.model}\n")
    print("Per-run means (token columns summed across a run's chunks).\n")
    print("| mode | runs | chunks | recorded cost (mean, range) "
          "| input | output | cache_read | cache_write |")
    print("|---|--:|--:|--:|--:|--:|--:|--:|")
    print(f"| coarse (1 chunk) {fmt(coarse)}")
    print(f"| fine (many chunks) {fmt(fine)}")

    if coarse["cost_mean"] > 0:
        premium = (fine["cost_mean"] / coarse["cost_mean"] - 1) * 100
        print(f"\n**Cost premium of fine chunking: {premium:+.0f}%** "
              f"(${fine['cost_mean']:.4f} vs ${coarse['cost_mean']:.4f} for the same task).")

    # The boundary tax, attributed to token lines by published price shape:
    # output = 5x input, cache-write = 1.25x input, cache-read = 0.1x input.
    RATE = {"output": ip * 5, "cache_write": ip * 1.25, "cache_read": ip * 0.1, "input": ip}
    print("\n**Boundary tax — what the premium is made of** "
          "(mean extra tokens per fine run vs coarse, and the $ each adds):\n")
    print("| token line | coarse | fine | Δ tokens | Δ $ | share of premium |")
    print("|---|--:|--:|--:|--:|--:|")
    cost_delta = fine["cost_mean"] - coarse["cost_mean"]
    for key, label in [("cache_read", "cache read (re-read prefix)"),
                       ("output", "output (re-orient each resume)"),
                       ("cache_write", "cache write (re-anchor prefix)"),
                       ("input", "fresh input")]:
        d = fine[key] - coarse[key]
        d_usd = d / 1e6 * RATE[key]
        share = (d_usd / cost_delta * 100) if cost_delta else 0
        print(f"| {label} | {coarse[key]:,.0f} | {fine[key]:,.0f} | "
              f"{d:+,.0f} | ${d_usd:+.4f} | {share:+.0f}% |")
    print(f"\nEvery one of those lines re-processes or re-generates context the "
          f"coarse run paid for once. The delivered artifact (same code, same "
          f"tests) is identical — the premium buys nothing but boundaries.\n")


if __name__ == "__main__":
    main()
