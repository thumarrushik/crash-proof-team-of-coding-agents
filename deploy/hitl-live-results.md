# Human Gate — Live Run on a Real Temporal Server

Reproduce: `deploy/hitl-live.sh` (starts an ephemeral `temporal server start-dev`, runs `deploy/hitl-live.py`). The RunClaudeTask workflow, the query inbox, the validated `decide` update, the durable wait + deadline timer, the operator CLI (`src/approvals.py`), and the event history below are all real. Four activities are stubbed (the agent chunk, the transcript export, the review post, and the merge) so the run needs no tokens and no live repo; the gate machinery itself is untouched.

### A. approve via CLI

- workflow id: `hitl-approve-d4963a8f`
- merges performed: `['pr-4']`
- decision: approved=`True` by=`rushik` note=`LGTM`
- gate seen by query: `{'action': 'merge', 'detail': 'PR #4 on o/r', 'timeout_h': 0.08333333333333333}`
- operator `--list` inbox:

```
hitl-approve-d4963a8f
  action: merge  detail: PR #4 on o/r  deadline: 0.08333333333333333h
```
- operator decision reply: `recorded: approved by rushik`
- event history: 36 events — update-accepted×1, update-completed×1, activity-completed×4, timer started×1/fired×0

### B. reject via CLI

- workflow id: `hitl-reject-731b920a`
- merges performed: `[]`
- decision: approved=`False` by=`rushik` note=`hold for security review`
- operator decision reply: `recorded: rejected by rushik`
- event history: 30 events — update-accepted×1, update-completed×1, activity-completed×3, timer started×1/fired×0

### C. nobody answers (5s deadline)

- workflow id: `hitl-deadline-c340e9ad`
- merges performed: `[]`
- decision: approved=`False` by=`deadline` note=`auto-denied after 0.001388888888888889h`
- event history: 28 events — update-accepted×0, update-completed×0, activity-completed×3, timer started×1/fired×1

## Checks

- PASS — A merged exactly PR #4
- PASS — A decider is the human
- PASS — A update entered history
- PASS — B did not merge
- PASS — B decision recorded, not approved
- PASS — B update entered history
- PASS — C did not merge
- PASS — C denied by deadline
- PASS — C recorded NO human update
- PASS — C timer fired

**ALL PASS** (10/10).
