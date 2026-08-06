# What chunk granularity costs — measured (and corrected)

> **Superseded — see `deploy/full-experiment-results.md`.** This earlier run (roman-numerals
> task) found fine ≈ coarse. A later, fuller experiment on a more open-ended task (kvstore)
> showed the chunking premium is **task-dependent**: the per-boundary cache tax stays cheap,
> but a tight turn cap can induce agent wandering (measured 1→14 chunks, $0.03→$2.13). Both
> are true; the newer file is the authority the article cites.

Runs of `deploy/cost-experiment.sh` + `deploy/cost_report.py`. Date: 2026-07-15.
Model: `haiku`. Harness: the real `RunClaudeTask` workflow / `run_claude_chunk`
activity, worker as a host process.

## Method

The same fixed TDD task (build `roman.py` + `test_roman.py`) run two ways, only
the chunk granularity varied:

- **coarse** — `--max-turns-per-chunk 40` → one chunk.
- **fine** — `--max-turns-per-chunk 2` → many chunks (mostly ~7).

Per-run cost is the SDK's `total_cost_usd`; per-chunk token breakdown from
`usage-log.jsonl`.

## Result — chunk granularity is cost-neutral

A first pass at **n=3** showed fine costing +68% more than coarse. **It did not
replicate.** A clean **n=6** run (sequential, no concurrency, no API-errored runs):

| mode | n | median | mean | range |
|---|--:|--:|--:|--:|
| coarse (1 chunk) | 6 | **$0.145** | $0.248 | $0.091–$0.793 |
| fine (~7 chunks) | 6 | **$0.113** | $0.148 | $0.074–$0.344 |

**Fine and coarse cost about the same — if anything fine is slightly cheaper**
(median −22%). The spread is enormous and driven by how much the agent *wanders*,
not by chunking: one coarse run rambled into a second chunk and cost **$0.79**,
more than any fine run, while fine's `max_turns=2` leashes exactly that wandering.
Aggregate cache-read tokens even flipped between batches (coarse 5.4M vs fine 2.9M
at n=6) — total work, not boundary count, dominates.

**The +68% was a small-sample (n=3) artifact.** The per-resume prefix re-read is
a real structural cost, but it is swamped by agent-wandering variance, so there is
no reliable total-dollar chunking premium.

## Reading

Chunk granularity is a **progress/steering dial, not a cost lever** — pick it for
how often you want workflow-visible progress and steering, not to save money. The
durable story is elsewhere and it holds:

- **Durability is ~free.** A coarse Temporal run costs the same as a bare loop
  (Temporal adds ~0 Claude tokens) — confirmed by the controlled trial and by a
  live end-to-end issue→PR pipeline job ($0.11, clean, zero retries).
- **A crash recovers for cents.** A worker killed mid-chunk resumes the same
  session from heartbeat details for ~$0.04 — a resume, not a re-run from zero
  (`deploy/heartbeat-recovery-results.md`).

## Bare-loop baseline (no durability)

The same task run as a plain headless `claude -p` — no Temporal, no workspace
skill bundle, no schema, no resume (`deploy/bare-loop-cost.py`) — measured **9
trials, haiku: mean $0.1751, median $0.1719, range $0.05–$0.30**. That ties the
coarse Temporal run within noise — **Temporal adds ~0 Claude tokens**. The bare
loop skips the skill bundle but, without the `tdd` skill guiding it, runs more
turns — roughly a wash.

## Reproduce

```bash
docker compose up -d                       # Temporal infra + team namespaces
uv run src/worker.py --team backend &      # host worker (uses local claude login)
TRIALS=6 MODEL=haiku ./deploy/cost-experiment.sh   # run SEQUENTIALLY — no concurrent jobs
uv run deploy/cost_report.py experiment-results --model haiku
uv run python deploy/bare-loop-cost.py 9   # bare-loop baseline (no Temporal)
```
