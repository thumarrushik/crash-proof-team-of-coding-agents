# Review-Driven Fix Loop — Live Run on a Real Temporal Server

Reproduce: `deploy/fixloop-live.sh`. Real `RunClaudeTask` workflows drive the loop on a real `temporal server start-dev`; the agent chunk, the transcript export, the review post, the merge, the push, and the human-review read are stubbed, and the two escalation activities are stubbed to start the *real* sibling workflow (minus GitHub), so the cross-workflow chain, the human gate, and the operator CLI (`src/approvals.py`) are real.

### chain: red -> fix -> green -> approve -> merge

- run: `fl-37dfa2`
- fix jobs started: ['fl-37dfa2-backend-fix-pr-4-r1']
- fix pushes: `['claude/issue-1']`
- re-review jobs started: ['fl-37dfa2-review-pr-4-r1']
- merges: `['pr-4']`
- human-gate updates in history: 1
- operator reply: `recorded: approved by rushik`

### cap: red at max rounds -> no fix, await human

- run: `cap-a0781a`
- fix jobs started: []
- merges: `[]`

## Checks

- PASS — chain: red suite started exactly one fix (round 1)
- PASS — chain: the fix pushed the branch
- PASS — chain: a re-review (round 1) started
- PASS — chain: the re-review reached the human gate
- PASS — chain: operator approval merged PR #4
- PASS — cap: red at max rounds started NO fix
- PASS — cap: nothing merged

**ALL PASS** (7/7).
