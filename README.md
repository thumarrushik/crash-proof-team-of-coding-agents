# A Crash-Proof Team of Coding Agents

**Claude Code remembers the conversation; Temporal remembers the job.** This
repo is the final publication kit and the running system behind it: a durable
delivery team of nine single-purpose Temporal jobs with Claude Code doing the
judgment work inside them, under skill playbooks, enforced hooks, and
human-controlled settings — plus every experiment the articles cite, with its
evidence and tests.

Curated from [temporal-claude-demo](https://github.com/thumarrushik/temporal-claude-demo)
(the full lab notebook, including earlier drafts and the v1 chapter series).

## The articles (`articles/final/`)

Each ships as canonical markdown + print PDF + a Medium-paste variant, and
every number traces to an evidence file in `deploy/`.

| Article | What it measures / builds |
|---|---|
| **A Crash-Proof Team of Coding Agents** (flagship) | kill -9 recovery as the same session for four cents; nine durable jobs carrying an issue from filed to merged; a real merge conflict resolved with no human decision in the loop |
| **The Human Is a Durable Object** | the human merge gate on four Temporal primitives (query, validated update, durable timer, deny-safe deadline), run live 10/10; plus the bounded review-driven fix loop |
| **Flag, Block, or Beg** | beg (prompt) vs flag (`PostToolUse`) vs block (`PreToolUse`) on one waste pattern — a mid-flight block prevented 5/5 but finished the task 1/5 |
| **Done Is Not a Claim** | a `Stop`-hook gate on "done" — forced the skipped step 5/5 where the mid-flight block derailed: it is not whether you block, it is where |
| **The Agent Grades Its Own Homework** | the merge switch's own `tests_passed` boolean vs ground truth — wrong 3 in 10, every miss a false alarm; the harness re-run corrects both directions |

Regenerate outputs: `articles/final/render-pdf.sh` and
`articles/final/export-medium.sh` (canonical `.md` files are the source).

## The teams (`teams/`)

Every lane is a physical folder — its identity in version control:

```
teams/<team>/
  CLAUDE.md          the team's mandate: every task follows named phases
                     (Understand -> Plan -> Implement -> Test -> Self-review
                     -> Report), "do not skip", per-lane duties, the harness
                     contract (the harness owns git)
  .claude/skills/    the team's skills — OWNED by the team folder (no shared
                     pool); plus settings.json, rules.json, and the flag-rules
                     hook, materialized from src/shared.py by teams/sync.py
                     (drift tests go red if they diverge)
```

Six lanes: `backend`, `frontend`, `testing`, `review`, `issues`,
`service-design`. The workspace bootstrap (`src/activities.py`) installs the
team folder into every run: the mandate becomes the workspace `CLAUDE.md`, the
bundle becomes `.claude/skills`, and the same deny rules + audit hooks are
re-stamped before every chunk. After editing the policy sources in `src/shared.py`: `python3 teams/sync.py`. Skills are edited directly in the owning team's folder.

## The system (`src/`)

Two Temporal workflows conduct nine single-purpose activities; only one runs
Claude Code, and it does all the judgment work (build, review, resolve, fix).
Highlights: resume-from-heartbeat crash recovery, per-team namespaces and
queues, the review-driven fix loop (off by default), and the human approval
gate (off by default; operator CLI in `src/approvals.py`).

## The experiments (`deploy/`)

Runner + evidence pairs the articles cite, all reproducible:

- `flag-block-beg.py` / `-results.md` — the tool-call boundary
- `step-gate.py` / `-results.md` — the finish boundary (`Stop` gate)
- `self-grade.py` / `-results.md` — the self-reported boolean vs ground truth
- `hitl-live.sh` / `hitl-live-results.md` — the human gate on a real server
- `fixloop-live.sh` / `fixloop-live-results.md` — the fix loop end to end
- plus the cost, heartbeat-recovery, and learn-loop evidence behind the flagship

Agent-driven runners need the `claude` CLI logged in; the live-demo scripts
start their own ephemeral `temporal server start-dev`.

## Test everything

```bash
uv run --with temporalio python -m unittest discover -s tests
```

Offline and deterministic (the hook scripts, the gate, the scoring taxonomies,
the team folders and their drift guard, workflow tests on Temporal's
time-skipping test server). No tokens, no network, no live server needed.

---

*Personal project; views are my own and not my employer's. Not affiliated with
or endorsed by Anthropic or Temporal.*
