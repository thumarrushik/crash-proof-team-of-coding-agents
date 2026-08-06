# The four costs — continuous / resumed / chunked — fully measured

`deploy/full-experiment.py`, 2026-07-15, model `haiku`, run strictly **sequentially**
(no two agent runs overlap — concurrency contaminated an earlier batch). One
substantial TDD task (build `kvstore.py` + tests) so the prefix is realistic. Cost is
the CLI's own `total_cost_usd` — identical on a laptop or a GCP VM (an Anthropic-API /
prompt-cache property, not an infra one). **Everything below is observed, not modeled.**

## Method

Total run cost = (agent's actual work) + (boundary/resume overhead). The first term
swings wildly, so to measure the *boundary* we hold work at zero: resume a fixed
session with a **no-op** (`--max-turns 1`, "reply OK, no tools") and read its cost.

| measurement | how |
|---|---|
| continuous **C** | run the task to completion in one session, ×3 (turns/prefix vary) |
| warm boundary **R_warm** | no-op resume, cache < 5 min, ×5 |
| cold boundary **R_cold** | no-op resume after a 65-min idle gap, ×3 |
| chunked total | same task via back-to-back `--max-turns 2` resumes, ×3 |

## Results (observed)

| quantity | value | notes |
|---|--:|---|
| **Continuous C** | **$0.113** | runs $0.058 / $0.132 / $0.149; 3–9 turns; prefix 84k–332k |
| **Warm boundary R_warm** | **$0.0035** | 5/5 cache-**reads** (~31k tok, 0.1×); ~3% of a base run |
| **Cold boundary R_cold** | **$0.0206** | first touch after 65 min paid a partial cache-**write** (14.9k tok), ~6× warm |
| **Chunked total** | **$0.034 / $0.25 / $2.13** | 1 / 8 / 14 chunks — **~63× spread** (worst ~19× the continuous base) |

## What each result means

1. **Continuous is the floor: ~$0.11**, with real run-to-run spread (the agent takes
   3–9 turns for the same task).

2. **A crash/resume is cents, not a re-run.** A warm resume re-reads the prefix at the
   cheap cache-read rate — **$0.0035**, ~3% of the base run. This is the heartbeat-recovery
   cost (a resume, not a restart from zero), confirmed independently at $0.04 on a live
   worker-kill (`deploy/heartbeat-recovery-results.md`).

3. **The cold penalty is real but modest — and hard to trigger.** After a 65-minute idle
   gap the first resume paid a *partial* cache-write (14.9k of ~32k tokens) → **$0.0206,
   ~6× warm** — then immediately re-warmed, so the next resumes were cheap again. Even at
   65 minutes the prefix was only *half* cold: Claude Code's extended-TTL caching keeps
   resumes cheap far longer than the classic 5-minute TTL. The full ~12× cold cache-write
   never fully materialized.

4. **Fine chunking's cost is unpredictable — this is the real reason to chunk coarse.**
   The same task fine-chunked cost **$0.034 (1 chunk), $0.25 (8), and $2.13 (14)** — a 19×
   spread. The blow-up is *not* a per-boundary cache tax (that stays ~$0.0035, a cache-read):
   it is **behavioral**. A tight `--max-turns 2` cap can send the agent to 14 chunks / 28
   turns to finish what continuous did in 9 — more turns, more output, and a prefix that
   grows and gets re-read at every boundary. Coarse chunks don't give the agent room to
   wander like that.

## The four scenarios

| Scenario | measured cost | mechanism |
|---|--:|---|
| **Continuous** — 1 session to done | **$0.113** | the floor |
| **Interrupted + resumed once** (warm crash → heartbeat) | **+$0.0035** | one warm cache-read → cents |
| **Interrupted + resumed once** (cold, > TTL) | **+$0.021** | partial cache-write, ~6× warm |
| **Fine chunked (N boundaries)** | **$0.03 – $2.13** | unpredictable; a tight cap can induce wandering |

**Bottom line:** durability is nearly free (a resume is cents; Temporal adds ~0 tokens),
and a crash recovers for cents. Chunk **coarse** — not because a boundary's cache-read is
expensive (it isn't), but because fine chunking makes total cost *unpredictable*.

Reproduce: `uv run python deploy/full-experiment.py` (~90 min incl. the 65-min cold gap).
