# Conversation-tree experiment — fork one session into N futures, measured

**Runner:** `deploy/tree-experiment.py` (bare `claude -p`; forks via
`--resume <trunk> --fork-session`, one git worktree per fork, forks and the
independent baseline each launched 3-way CONCURRENT). **Evidence:**
`experiment-results-tree/` (raw CLI JSON per run, `runs.tsv`, `result.json`;
run-1 evidence preserved as `run1-workspace-race.*`). **Models:** `haiku`
everywhere, `sonnet` judge. **Date:** 2026-07-29. All numbers observed.

**Task:** one fixed spec (event-sourced KV store `ESKV`: set/get/delete,
per-key version history with tombstones, restore, ordered keys). TREE trunk
writes a black-box pytest suite + `STRATEGIES.md` (3 materially different
designs) and no implementation; each fork implements one strategy against the
shared suite, forbidden from editing tests. Baselines: SOLO (one continuous
TDD run) and INDEP (3 concurrent independent TDD runs — naive best-of-N,
each writing and grading its own suite).

## Mechanics

- Fork-in-worktree works natively: smoke run inherited trunk memory, minted a
  new session ID, and the transcript lookup crossed the worktree boundary
  without the fallback copy.
- **Run 1 failure (kept as a finding):** a forked conversation inherits the
  trunk's ABSOLUTE paths from memory. All three forks raced their
  implementations into the trunk checkout; every tournament worktree ended
  without an `eskv.py`, caught by the harness pytest check. Fix: the fork
  prompt re-anchors the agent in its worktree explicitly. **A session fork is
  a conversation fork plus a workspace fork; forget the second and the
  branches collide.**

## Run 2 (clean), measured

| Run | Cost | Turns | Wall | Verdict |
|---|---|---|---|---|
| SOLO | $0.0724 | 6 | 72s | 45/45 (its own suite) |
| TREE trunk | $0.0710 | 4 | 67s | suite of 46 + 3 strategies |
| TREE fork1 | $0.2475 | 17 | 206s | 45 pass, **1 fail** |
| TREE fork2 | $0.1272 | 5 | 115s | 45 pass, **1 fail** |
| TREE fork3 | $0.0878 | 3 | 79s | 45 pass, **1 fail** |
| TREE judge (sonnet fork) | $0.1166 | 1 | 10s | picked strategy 1 on simplicity |
| INDEP run1/2/3 | $0.0982 / $0.1202 / $0.1117 | 8/9/12 | batch 128s | 42 / 36 / 37 pass (self-graded) |

Totals: **TREE $0.650** (fork batch wall 212s) vs **INDEP $0.330** vs
**SOLO $0.072**.

## Findings

1. **The tournament audited its own referee.** All three diverse
   implementations failed the SAME single test, `test_complex_workflow`,
   whose comment claims "set, set, delete, set" (4 events) while its code
   performs set, delete, set (3). The implementations were right; the trunk's
   test was wrong. Unanimous failure across N independent designs is evidence
   against the test, not the code — a signal that self-graded best-of-N
   (INDEP's clean-looking 42/36/37) structurally cannot produce, because an
   implementation and the suite it wrote for itself co-evolve until they
   agree.
2. **The harness refused to merge, correctly.** No fork had a green tree, so
   the winner was overridden to none and no merge ran, judge preference
   notwithstanding. Red suite, no merge — even when the red is the suite's
   own fault (that distinction is the human-readable part of the story).
3. **The tree cost 2× the naive baseline here, not less.** $0.650 vs $0.330.
   Drivers: the sonnet judge ($0.117), and fork1 burning 17 turns/18.2k
   output tokens fighting the unwinnable test it was (rightly) forbidden to
   edit. The forks did start cache-warm on the trunk's ~108k context, but —
   consistent with the chunking and relay experiments — **mechanical costs
   stayed in cents while behavior moved the dollars.**
4. **Concurrency worked.** 3 forks + 3 independents ran as true parallel
   batches (fork batch wall 212s ≈ slowest fork, not the sum).

## What we'd change next

- **Unanimity rule for the governor:** if all N forks fail the same test,
  flag the referee, stop the fight (a typed-data rule for the workflow, like
  the team-rules flags).
- Validate the trunk suite before forking (cheap sanity implementation, or a
  turn-capped self-review pass).
- Cap "fight turns" per failing test so one bad test cannot 3× a fork's bill.
