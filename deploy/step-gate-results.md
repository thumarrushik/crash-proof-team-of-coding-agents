# Done Is Not a Claim — Measured

Model `claude-haiku-4-5-20251001`, 5 run(s)/arm; isolated headless runs (`--setting-sources project`), same checklist task each arm; everything observed. Point estimates, not distributions; stats over non-error runs. `step_done` = the skippable proof step actually happened (proof.txt = VERIFIED); `completed` = full task, same work every arm was asked for.

| arm | mechanism | non-error runs | mean cost | mean turns | Stop blocks | **step done** | **finished the task** |
|---|---|--:|--:|--:|--:|--:|--:|
| control | none (baseline) | 5 | $0.0320 | 6.4 | 0.00 | 3/5 | 3/5 |
| beg | CLAUDE.md rule (persuasion) | 5 | $0.0330 | 6.8 | 0.00 | 2/5 | 2/5 |
| stop-gate | Stop hook (finish-boundary block) | 5 | $0.0298 | 6.2 | 0.60 | 5/5 | 5/5 |

**What the runs show:**

- **control** — baseline: the skippable step was done in **3/5** runs with no enforcement.
- **beg** — a definition-of-done rule in prose: step done in **2/5** runs (persuasion, probabilistic).
- **stop-gate** — a Stop hook blocking the finish: step done in **5/5** runs, task finished in **5/5**; the gate blocked a premature stop 3 time(s) across the arm; 0 run(s) hit the block cap without ever satisfying the check (the 'check must be satisfiable' failure).

**The line.** A block at the tool boundary (flag-block-or-beg) can derail a run by denying a step the agent needs; a block at the *finish* boundary does the opposite — it holds the exit until the skipped step is actually done. It is not whether you block, it is where.
