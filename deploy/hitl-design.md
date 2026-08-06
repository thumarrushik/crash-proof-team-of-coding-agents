# Human-in-the-loop as Temporal primitives — design notes

The point of this document: "human in the loop" is not a UI feature bolted
onto an agent system. Modeled on durable-execution primitives, the human
becomes another **typed, durable, timeout-bounded participant** — with the
same properties the agents already have: attributable actions, crash-proof
waits, and an audit trail by construction. Below, every relevant primitive is
mapped to a human interaction pattern, with the trade-offs that made us pick
what we implemented.

## The primitive-by-primitive map

| Primitive | The human pattern | Properties | Trade-offs / when to use |
|---|---|---|---|
| **Query** | *The human reads.* `get_progress`, `get_pending_approval` | Read-only, never blocks, works mid-run | No consent semantics; purely observational. Already shipped (status queries). |
| **Signal** | *The human suggests.* Our `steer` signal folds instructions into the next chunk | Async, fire-and-forget, durable delivery | Unvalidated, no result to the sender, sender can't tell applied-from-ignored. Right for advice; **wrong for decisions.** |
| **Update + validator** | *The human decides.* Our `decide` update | Synchronous; the **validator rejects bad input before it enters history**; caller gets a definitive result | The decision primitive. A rejected update leaves no trace — you cannot "approve" a workflow that isn't asking, and every recorded decision is attributable (`decided_by` enforced). |
| **`wait_condition` + timer** | *The human is waited for, with a deadline.* Our `_human_gate` | The wait is **durable**: it survives worker crashes, deploys, and weeks of silence at zero cost; the timeout is part of the contract | Deadline policy is a design decision: we deny-safe (an unattended gate refuses the irreversible act). Escalate-then-deny is the next tier. |
| **Timer / Schedule** | *The human is reminded.* | A nudge activity at T/2 (comment, notification) is three lines in the gate | Not yet wired; the gate records `timeout_h` so a reminder has its deadline. |
| **Search attributes** | *The human finds the work.* `AwaitingHuman=true` → server-side inbox query | The approval inbox with no side database | Needs cluster-level attribute registration; our CLI ships the portable version instead (list running workflows, query each). Register the attribute at scale. |
| **Async activity completion** | *The human IS an activity.* Activity hands out a token; a person completes it later via the client | Retries/timeouts/heartbeats apply to the human like any activity; "human ignoring this" = heartbeat timeout | Powerful and honest, but no validator, and token plumbing pushes state to the outside world. We chose update+wait_condition; this is the pattern for external ticket systems. |
| **Child workflow** | *The approval as its own audit object.* An `ApprovalWorkflow` per decision | Self-contained history per decision, reusable across lanes | More moving parts; our gate lives in-workflow because one merge = one decision. Adopt when approvals grow policies of their own. |
| **Continue-as-new** | *The human's long-lived inbox / the standing meeting.* | Bounded history for perpetual loops | Used by AdaptiveCanary; an approvals-inbox workflow would use it the same way. |

## What we implemented (and where)

- **The merge gate** (`workflows.py::_human_gate`): when `TaskInput.require_approval`
  is set, the one outward irreversible act in the pipeline — the merge — blocks
  on a validated human decision with a deadline (`approval_timeout_h`, default
  24h, deny-safe on expiry, decision attributed to `"deadline"` so even the
  timeout is auditable). Gate state is queryable (`get_pending_approval`);
  the closing decision lands in `TaskProgress.approval`.
- **The decision** (`workflows.py::decide` + validator): a workflow update.
  Malformed or unsolicited decisions are rejected *before* they enter the
  event history.
- **The operator's side** (`src/approvals.py`): `--list` (the inbox: every
  running task blocked on a gate, what it wants, its deadline) and
  `--approve/--reject --by <who> --note`. Codified, no clicking.
- **Tests** (`tests/test_human_gate.py`): the real workflow against Temporal's
  time-skipping test server — approve → merge runs; silence → 24h deadline
  fires in milliseconds of wall clock → deny, no merge; unattributed decision
  → rejected by the validator, gate stays open.

## The ladder now ends at a person

This composes with everything before it. The model-escalation ladder climbs
haiku → sonnet on chunk count or hook-flag pressure; the gate is the rung
above sonnet. Retrying harder is a machine's answer; *waiting, durably,
deadline-bounded, for someone accountable* is the system's answer when the
action is irreversible or the strongest model is still failing. And because
the wait is a workflow primitive, the human's absence costs nothing: no
polling loop, no held worker slot, no state to lose — the gate simply exists
in the event history until someone answers it or the deadline does.

## Deliberate choices worth defending

1. **Deny-safe deadlines.** An unattended approval auto-refuses. The
   alternative (auto-approve on silence) turns every missed notification into
   consent. Timeouts are decisions and are recorded as such.
2. **Updates over signals for consent.** A signal cannot tell the sender "no."
   Consent needs a channel that can refuse.
3. **Attribution is enforced at the boundary.** `decided_by` is validated
   before recording, not culturally expected after.
4. **The gate defaults OFF.** The pipeline's no-human-in-the-loop behavior is
   unchanged unless a job opts in — autonomy stays the default, accountability
   becomes available.
