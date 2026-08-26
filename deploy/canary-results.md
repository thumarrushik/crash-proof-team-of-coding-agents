# Economics canary — the published measurements as a scheduled probe

**Code:** `src/canary.py` (probes + bands + `EconomicsCanary` workflow +
schedule CLI), registered on the poller worker (`src/worker.py`). **Evidence:**
`experiment-results-canary/history.jsonl` (longitudinal, one line per pass).
**Bands:** unit-tested pure logic (`tests/test_canary_bands.py`), roughly 3×
around the published values in `deploy/*-results.md`. **Date:** 2026-07-29.

## Why

Every number this project has published is a snapshot of provider behavior:
cache TTLs, pricing tiers, resume and fork semantics. Those change without
notice. Production LLM monitoring watches *your traffic*; nothing watches the
*mechanics* the way an uptime canary watches an endpoint. This canary probes
five invariants directly, for about **$0.09 and ~25 seconds per pass**:

| Probe | Invariant guarded | Band (USD) | Mechanistic check |
|---|---|---|---|
| seed | a tiny session can be built at all | 0.004–0.08 | subtype success |
| warm_resume | same-model resume is a cheap cache READ | 0.0008–0.02 | cache_read ≥ 5k |
| handoff_tax | cross-model resume pays a cache WRITE (caches are per-model) | 0.02–0.25 | cache_write ≥ 5k |
| fork_warmth | fork-resume is cheap and mints a NEW session id | 0.002–0.06 | new sid |
| integrity | a fork recalls planted conversation memory, tools forbidden | 0.002–0.06 | marker recalled |

A vanished handoff tax alerts too: cross-model cache sharing appearing
overnight would be exactly the kind of silent regime change worth knowing
about (it would obsolete the relay article's central caveat).

## First three passes (2026-07-29)

All green. Totals $0.0941 / $0.0932 / $0.0938. Live values vs published:
warm_resume $0.0030–0.0031 (published $0.0035), handoff_tax $0.0632–0.0638
(published $0.0729), fork_warmth $0.0030 + new sid (smoke-test reference
$0.0185 — that probe rode a fatter session; both in band), integrity recalled
3/3. The canary independently reproduced the article numbers on its first
flight. Figure: `assets/diagrams/canary-bands.png`
(`assets/plot-src/canary-plot.py`, generated from the history file).

## Pass four and five (2026-08-20)

Both green, run three weeks after the first flight during the article-family
review loop. Totals $0.0938 / $0.0938 (identical to the third first-flight
pass to the fourth decimal). Live values vs published: warm_resume $0.0031
(published $0.0035), handoff_tax $0.0639 (in band), fork_warmth $0.0030 +
new sid, integrity recalled 2/2. Five weeks of provider evolution moved
nothing: the published economics still reproduce.

## Operating it

- One pass, no infra: `uv run src/canary.py --once` (exit 1 on alert — CI-able).
- On the harness: the poller worker now hosts `EconomicsCanary`;
  `uv run src/canary.py --schedule [--interval-hours 24]` creates the
  Temporal Schedule on the poller queue. Every pass is then a durable,
  retried, queryable workflow run, and its typed `CanaryReport` lives in the
  event history; the JSONL is the longitudinal dataset
  (`CANARY_HISTORY_DIR` overrides where it lands; ship it to the corpus
  bucket in deployments).
- Alerts today: workflow log warning + nonzero exit in `--once` mode. Next
  step when needed: an alert activity filing a GitHub issue through the same
  harness credentials the team lanes use.

## Scheduling tiers (pick one)

1. **AdaptiveCanary (recommended):** `uv run src/canary.py --adaptive` starts a
   self-scheduling workflow — alerts tighten cadence to 1h, near-band values
   to 6h, a 7-pass clean streak stretches to 48h; sleeps + continue-as-new
   with a bounded history window. Cadence logic is pure and unit-tested
   (`next_interval_hours`, `near_band_edge`).
2. **Fixed Temporal Schedule:** `uv run src/canary.py --schedule
   [--interval-hours 24]`.
3. **Plain cron (no Temporal at all):** `.github/workflows/economics-canary.yml`
   runs `--once` daily on GitHub Actions cron; a band violation fails the run
   (GitHub notifications = alerts), history uploaded as an artifact. Fallback
   tier: no retries, no durable memory, dies silently if disabled — the exact
   failure mode the harness exists to remove.

## Caveats

- Bands are generous by design (regime detector, not a price tracker); n=3 so
  far — the value compounds with the schedule.
- Probes cost real money ($0.09/pass); daily cadence ≈ $33/year, hourly ≈
  $790/year. Pick cadence accordingly.
- The seed probe's cost includes workspace variance (system prompt cache
  state on the machine); its band is the widest for that reason.
