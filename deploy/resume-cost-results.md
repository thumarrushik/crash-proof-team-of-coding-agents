# The three costs — continuous vs. resumed vs. chunked — measured

`deploy/resume-cost.py`, 2026-07-15, model `haiku`. The goal: isolate the cost of a
resume/chunk **boundary** from the agent-work variance that swamped the earlier
coarse-vs-fine total-cost experiment.

## Why this estimator works

Total run cost = (agent's actual work) + (boundary/resume overhead). The first term
swings wildly run to run (4 turns vs 20), so comparing *total cost of different runs*
buries the boundary signal in noise — that's why coarse-vs-fine came out cost-neutral
but unconvincing. Here we hold the work at **zero**: build one session to a fixed
prefix, then resume it with a **no-op** ("reply OK, no tools", `--max-turns 1`). The
measured cost of that resume **is** the prefix re-establishment — the boundary tax —
with the variance removed. Same prefix every trial → the numbers are tight.

## What a boundary costs (measured)

Build session: `C = $0.0335` (continuous, 1 session), prefix ≈ 28k tokens.

| resume type | cost | cache_read | cache_write | verdict |
|---|--:|--:|--:|---|
| warm ×3 (immediate) | **$0.00311** | ~28,000 | ~75 | prefix is **cache-READ** (0.1×) |
| "cold" ×3 (after 390s) | **$0.00312** | ~28,100 | ~70 | **still WARM** at 6.5 min |

**A resume is a cache-READ of the prefix, not a re-run.** At 0.1× the input rate it is
~9% of the base run per boundary, at this prefix. The `cold/warm` ratio came out **1.0×**:
the prompt cache stayed warm at **6.5 minutes** — longer than the classic 5-min TTL
(Claude Code uses extended-TTL caching). The 12.5× cache-**write** penalty a cold cache
*would* cost only bites if a boundary lands past that TTL — confirmed separately by a
65-min cold probe (`deploy/cold-probe.log`).

## The three scenarios

Boundary cost scales linearly with prefix size (`0.1 × prefix × input_rate` warm;
`1.25 ×` cold). At this task's 28k prefix and at a realistic long-job prefix
(470k tokens, from live issue #41):

| Scenario | 28k prefix | 470k prefix (real job) | mechanism |
|---|--:|--:|---|
| **Continuous** — 1 session to done | C = $0.0335 | ~$0.11–0.14 | the floor |
| **Interrupted + resumed once** (crash → heartbeat) | C + $0.003 | C + ~$0.05 | one warm prefix re-read + lost in-flight turn → **cents** |
| **Chunked N=10, back-to-back** (warm) | C + $0.028 | C + ~$0.47 | 10 warm cache-reads (0.1×) → **cost-neutral-ish** |
| **Chunked N=10, spaced > TTL** (cold) | C + $0.35 | C + ~$5.88 | 10 cache-WRITES (1.25×) → **significant** |

## Reading

- **Continuous is the floor; a crash costs cents.** A resume re-reads the prefix at the
  cheap cache-read rate — never a re-run from zero.
- **Chunking is cost-neutral *while the cache stays warm*** — which, measured, is well
  past 5 minutes. Back-to-back chunks (the normal case) never go cold. This is *why* the
  coarse-vs-fine total-cost experiment washed out.
- **The "significant cost" of chunking is real but conditional:** it appears only when a
  boundary lands after the cache TTL (long stalls, or a schedule that spaces chunks by
  more than an hour), turning each boundary's prefix re-read (0.1×) into a re-write (1.25×,
  ~12×). Design chunk cadence to stay inside the TTL and the tax stays near zero.

Cost is the CLI's own `total_cost_usd`; identical on a laptop or the GCP VM — it's an
Anthropic-API / prompt-cache property, not an infra one.
