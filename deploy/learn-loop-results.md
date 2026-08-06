# The corpus improves the system — measured

Every run exports a transcript + `hook-log.jsonl` (every tool call) + `REPORT.md`.
Collected, they are a corpus of how the agents actually worked. Here that corpus
is analyzed for a recurring mistake, the lesson is codified into workspace policy,
and the effect is measured before/after. Date: 2026-07-15. Agent model: `haiku`.

## 1. Corpus → bucket

The six cost-experiment runs' artifacts were pushed to a real object store:

```
gs://temporal-claude-corpus-213476/baseline/   # 6 runs × {transcript, hook-log, report}
```

Pointing the export at a bucket is a one-activity change; the point is that every
conversation is centrally retained and analyzable, not trapped on a worker.

## 2. Learner (Opus 4.8) finding

Reading the hook-logs across all six runs, the reviewer found one consistent,
measurable waste: **redundant filesystem re-orientation** — running `ls` to
re-confirm files the agent had *just* created (the Write/Edit response already
proves they exist), and re-running already-green tests. The leanest runs did the
task in 8–9 tool calls; the worst burned 24, dominated by this re-checking.

## 3. Codified guardrail (rides every run and every retry)

Two encodings, added to the workspace bootstrap in `src/activities.py`:

- **A CLAUDE.md rule** (behavioral nudge): "Trust tool responses… do not run `ls`
  to confirm a file you just created… run the suite once."
- **A `PostToolUse` hook** (`flag-orientation.py`): deterministically flags any
  orientation-only `ls` into `.claude/orientation-flags.log`.

## 4. Before / after

Six runs re-run with the guardrail in place, scored from the hook-logs:

| | mean orientation-`ls` / run | mean total tool calls / run |
|---|--:|--:|
| before (baseline) | 2.50 | 15.5 |
| after (guardrail) | 2.00 | 18.5 |

- The **soft rule** produced only a **modest ~20%** drop in the targeted anti-pattern,
  and one run ignored it entirely. Total tool calls did not fall — that count is
  dominated by chunk-boundary re-orientation and agent nondeterminism.
- The **hook fired 12 times**, flagging every remaining instance regardless of
  whether the agent complied.

## Reading — the honest lesson

The self-improvement loop works end to end (corpus → analysis → codified guardrail
→ re-run → measurement), and it lands exactly on the article's own thesis: **a
prompt rule is probabilistic; a hook is law.** The nudge helped a little; the
deterministic hook is the part you can trust for governance. The reliable win
isn't "the agent got better" — it's "the mistake is now caught, every time."

## Reproduce

```bash
# baseline corpus already gathered under experiment-results/corpus/
gsutil -m cp -r experiment-results/corpus/* gs://<your-bucket>/baseline/
# guardrail is in src/activities.py; re-run and re-score:
TRIALS=3 MODEL=haiku OUT=experiment-results-after ./deploy/cost-experiment.sh
```
