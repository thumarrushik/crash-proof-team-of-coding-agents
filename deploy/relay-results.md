# Relay experiment — swap the model mid-session, measured

**Runner:** `deploy/relay-experiment.py` (strictly sequential; bare `claude -p`
with `--resume`, the same resume the Temporal harness drives). **Evidence:**
`experiment-results-relay/` (raw CLI result JSON per run, `runs.tsv`,
`result.json`) and `deploy/relay-experiment.log`. **Models:** `haiku` (cheap),
`sonnet` (smart). **Date:** 2026-07-29. Everything observed via the CLI's own
`total_cost_usd` and usage counters; nothing modeled.

**Task:** one fixed three-module TDD library (kvstore with TTL/LRU, nested
transactions, JSON snapshots) in an empty workspace with a seeded pytest venv
and the harness's own deny rules in `.claude/settings.json`. Haiku prefixes are
capped at 6 turns to manufacture identical half-finished sessions (all four
ended `error_max_turns` at 7 turns — mid-flight by construction, not by luck).

## Mechanics: a session is model-agnostic

Smoke test: haiku wrote a marker word and stopped; sonnet resumed the session
and, with tools forbidden, recalled the word from inherited conversation
memory. Cross-model resume works; the transcript belongs to the session, not
the model. (`experiment-results-relay/stdout/smoke-*.json`)

## The handoff tax (no-op resumes of one half-finished session)

| Probe | Cost | Usage signature |
|---|---|---|
| Haiku resuming its own session (article-1 baseline) | $0.0035 | cache read |
| **Sonnet's first touch (the handoff tax)** | **$0.0729** | cache **write** 17,850 at sonnet rates |
| Sonnet's second touch | $0.0115 | cache read 35,859 — the tax is one-time |
| Haiku again, after sonnet's visits | $0.0060 | cache read 35,322 — haiku's cache intact |
| Demotion: haiku's first touch of a sonnet session | $0.0290 | cache write 21,546 at haiku rates |

Prompt caches are per-model. A cross-model resume pays a one-time cache write of
the inherited context at the inheriting model's rates (~21× a same-model warm
resume for haiku→sonnet, ~2.5× cheaper in the demotion direction). The two
caches then coexist on one conversation.

## The escalation moment (prefix ~$0.084 mean, 4 runs $0.077–$0.089)

| Arm | Finish cost | Turns | Arm total | Harness-run pytest |
|---|---|---|---|---|
| RELAY (sonnet resumes H2) | $0.4326 | 15 | $0.5211 | 66 passed |
| RELAY (sonnet resumes H3) | $0.4880 | 11 | $0.5649 | 53 passed |
| RESTART (sonnet scratch S1) | $0.4340 | 14 | $0.4340 | 57 passed |
| RESTART (sonnet scratch S2) | $0.4040 | 15 | $0.4040 | 56 passed |
| CONTROL (haiku finishes H4) | $0.1178 | 15 | $0.2034 | 58 passed |

Pytest was run by the harness on each arm's final tree (never taken from the
agent's own report). Every completed arm passes its own suite.

## Findings

1. **Inheritance did not save tokens.** Sonnet's relay finish (~$0.46 mean,
   11–15 turns) ≈ sonnet from scratch (~$0.42 mean, 14–15 turns). It re-read
   and verified the inherited work instead of skipping it (relay cache reads
   461–606k vs 448–473k scratch). The relay's yield is **continuity** — the
   workspace, branch, and inherited tests survive — not a smaller bill.
2. **Cheap-first is a bet on the cheap model's win rate.** Win: $0.20 total
   (control), less than half of sonnet-only. Lose: $0.54 vs $0.42, a 29%
   penalty. Break-even at these prices: the cheap model must finish roughly
   **1 in 3** tasks alone (0.543 − 0.34p = 0.419 → p ≈ 0.365).
3. **Escalate once, not often.** The handoff tax is small but per-swap and
   one-way-warm; a ladder that ping-pongs between models re-pays it.
4. **Variance is behavioral, not mechanical.** Identical relay prompts ended at
   15 turns/66 tests vs 11 turns/53 tests. Model nondeterminism dwarfs every
   boundary cost measured here — same conclusion as the chunking experiment.

## Caveats

- One task, one model pair, n=2 per expensive arm. The break-even is an
  illustration of the arithmetic, not a universal constant.
- The prefixes were *capped*, not genuinely stuck. A truly wedged model may
  have polluted its context with wrong turns, which a relay inherits too —
  the flag-pressure trigger (see the team-rules governor in `src/`) exists
  because "how it is working" beats "how long it has worked."
- Test counts across arms are self-authored suites, a weak quality proxy;
  pass/fail on the arm's own tree is the only claim made.

## Harness codification

The ladder is live in the harness, off by default: `TaskInput.escalate_model` /
`escalate_after_chunks` / `escalate_on_flags`, decided per chunk by the pure,
replay-safe `shared.model_for_chunk`, with hook-flag pressure fed to the
workflow as typed `ChunkResult.rule_flags` (see `tests/test_model_ladder.py`,
`tests/test_rule_governor.py`).
