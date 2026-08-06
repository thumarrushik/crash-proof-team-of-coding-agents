# Flag, Block, or Beg — Measured

Model `claude-haiku-4-5-20251001`, 5 run(s)/arm, everything observed from the CLI's own JSON + the workspace audit log. Isolated headless runs (`--setting-sources project`), same task each arm. Point estimates, not distributions; stats are over non-error runs.

| arm | mechanism | non-error runs | mean cost | mean turns | orientation `ls` | flagged | blocked | **completed task** |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| control | none (baseline) | 5 | $0.0391 | 9.2 | 2.60 | 0.00 | 0.00 | 2/5 |
| beg | CLAUDE.md rule (persuasion) | 5 | $0.0391 | 8.2 | 2.60 | 0.00 | 0.00 | 3/5 |
| flag | PostToolUse (detection) | 3 | $0.0529 | 13.0 | 4.00 | 4.00 | 0.00 | 3/3 |
| block | PreToolUse deny (prevention) | 5 | $0.0292 | 6.6 | 0.00 | 0.00 | 1.20 | 1/5 |

**What the runs show** (each mechanism on its own terms):

- **beg** — persuasion is probabilistic: the rule was obeyed (zero orientation `ls`) in **0/5** runs.
- **flag** — detection is exact and never interferes: flagged every completed orientation `ls` (`flagged == completed` in **3/3** runs, 12/12 instances); prevents nothing; completed the task in **3/3** runs.
- **block** — prevention is total but not free: completed orientation `ls` was **zero in 5/5** runs, yet the task itself finished in only **1/5** — denying a step the agent was told to take derailed the run. Its low cost is that derailment, not efficiency.

**The one line.** A rule *asks* (and is ignored); a flag *records* (every time, interfering never); a block *prevents* (every time) — but a block is a hard *no*, and a hard no on an action the agent believed it needed costs the task, not just the tokens. Flag waste; block danger.
