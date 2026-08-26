# A Crash-Proof Team of Coding Agents

### Kill it. It finishes anyway.

*A crash-proof, self-governing team of coding agents: every claim measured, every number a receipt.*

**Claude Code remembers the conversation; Temporal remembers the job.** This
repo is the final publication kit and the running system behind it: a durable
delivery team of single-purpose Temporal activities (nine in the measured
runs; twelve today, the fix-loop members having arrived since) with Claude
Code doing the judgment work inside them, under skill playbooks, enforced
hooks, and human-controlled settings, plus every experiment the articles
cite, with its evidence and tests.

Curated from [temporal-claude-demo](https://github.com/thumarrushik/temporal-claude-demo)
(the full lab notebook, including earlier drafts and the v1 chapter series).

## Start here

See the lead claim happen for real, in one command. It kills a worker's whole
process tree mid-task and shows the **same** Claude Code session finish the job
on a restarted worker, resumed from its last heartbeat with no completed
checkpoint:

```bash
./deploy/quickstart.sh
```

It starts an ephemeral Temporal dev server, runs the SIGKILL-and-resume demo,
prints `recovery-log.jsonl` (the one line that proves the resume), and tears
everything down. Needs `uv`, the `temporal` CLI, and a logged-in `claude` CLI;
the run bills real tokens (4 to 20 cents on `haiku`, varying with how many turns the agent takes).

No credentials handy? Verify the whole system offline and for free: hooks, the
finish gate, scoring, the team folders, and the workflows on Temporal's
time-skipping test server:

```bash
uv run --with temporalio python -m unittest discover -s tests
```

Bring up the full always-on fleet (a worker per lane, the poller, the schedule
watching a repo) with `./deploy/stack-up.sh`, and tear it down with
`./deploy/stack-down.sh`.

## The family (`articles/final/`)

One flagship and six companions, meant to be read as a set and in this order:
the claim, then the mechanism, then the bill, then the three trust boundaries,
then the person. No two share a job. Each ships as canonical markdown + print
PDF + a Medium-paste variant, and every number traces to an evidence file in
`deploy/`.

| # | Article | Its job | The receipt |
|---|---|---|---|
| 1 | **A Crash-Proof Team of Coding Agents** (flagship) | the claim | kill -9 mid-task and the run finishes as the **same session** for four cents: resumed from its last heartbeat, not a saved checkpoint; a real merge conflict resolved with no human decision in the loop |
| 2 | **How It's Built** | the mechanism | chunk anatomy, lanes and namespaces, sticky-queue worker affinity, the audit plane, the corpus loop |
| 3 | **Mechanics Cost Cents, Behavior Costs Dollars** | the bill | every boundary priced: an ~11¢ task, a $0.0035 crash resume, the $0.03 to $2.13 fine-chunking spread, the bare-loop baseline, and the canary that re-probes it all on a schedule |
| 4 | **Flag, Block, or Beg** | the tool-call boundary | beg (prompt) vs flag (`PostToolUse`) vs block (`PreToolUse`) on one waste pattern: a mid-flight block prevented 5/5 but finished the task 1/5 |
| 5 | **Done Is Not a Claim** | the finish boundary | a `Stop`-hook gate on "done" forced the skipped step 5/5 where the mid-flight block derailed: it is not whether you block, it is where |
| 6 | **The Agent Grades Its Own Homework** | the verdict boundary | the self-reported `tests_passed` boolean vs ground truth: wrong 3 in 10 (all in the builder arm; the isolated reviewer arm was honest 5/5), every miss a false alarm; the harness re-run corrects both directions |
| 7 | **The Human Is a Durable Object** | the person | the human merge gate on four Temporal primitives (query, validated update, durable timer, deny-safe deadline), run live 10/10; plus the bounded review-driven fix loop |

The one thread through all seven: every durable-execution engine can resume a
*completed step*; this family resumes a coding agent's *live session*, and
proves, prices, and governs every part of it.

Regenerate outputs: `articles/final/render-pdf.sh` and
`articles/final/export-medium.sh` (canonical `.md` files are the source).
Every figure regenerates from committed sources too: `assets/diagram-src/render.sh`
(D2 + HTML diagrams), `assets/hero-src/render.sh` (Medium heroes), and
`uv run --with matplotlib python assets/plot-src/plots.py` (the cost figure).

## The teams (`teams/`)

Every lane is a physical folder, its identity in version control:

```
teams/<team>/
  CLAUDE.md          the team's mandate: every task follows named phases,
                     "do not skip", and each lane's phases are its OWN
                     (backend runs Contract, issues runs Reproduce, frontend
                     runs Design/Verify, service-design runs Blueprint/Decide,
                     testing runs Author/Run, review runs Inspect/Run), plus
                     the harness contract (the harness owns git)
  .claude/skills/    the team's skills, OWNED by the team folder; skills live
                     here and NOWHERE else (no shared pool, no operator pool)
  .claude/           settings.json, rules.json, the flag-rules audit hook, and
                     phase-gate.py, a Stop hook enforcing the work-issue
                     discipline: every triggered run must create the SAME
                     phase task list (one task per mandated phase) and
                     complete it before the run is allowed to finish
```

Six lanes: `backend`, `frontend`, `testing`, `review`, `issues`,
`service-design`, discovered from the folders (adding a team = adding a
folder). At run time a task **checks out into its team**, it never copies the
team: the workspace `CLAUDE.md` `@import`s the live mandate and `.claude/skills`
is a symlink into the team folder, so the owning team's edits reach the very
next chunk. Only *policy* (`settings.json`, `rules.json`, the hook) is stamped
per chunk: an immutable, tamper-healing snapshot, with absolute-path denies
injected so no workspace can write through into `teams/` itself. Governance is edited directly in the owning team's folder; `python3 teams/validate.py` checks every folder (org floor, mandate sections, phase-gate parity) before it ships.

## The system (`src/`)

Two Temporal workflows conduct the delivery team's twelve single-purpose
activities; only one runs Claude Code, and it does all the judgment work
(build, review, resolve, fix).
Highlights: resume-from-heartbeat crash recovery, per-team namespaces and
queues, the review-driven fix loop (off by default), and the human approval
gate (off by default; operator CLI in `src/approvals.py`).

## The experiments (`deploy/`)

Runner + evidence pairs the articles cite, all reproducible:

- `flag-block-beg.py` / `-results.md`: the tool-call boundary
- `step-gate.py` / `-results.md`: the finish boundary (`Stop` gate)
- `self-grade.py` / `-results.md`: the self-reported boolean vs ground truth
- `hitl-live.sh` / `hitl-live-results.md`: the human gate on a real server
- `fixloop-live.sh` / `fixloop-live-results.md`: the fix loop end to end
- `machine-loss-live.sh` / `machine-loss-results.md`: two filesystems, machine
  A's disk deleted, machine B resumes the same session via shared storage
- `issue-routing-check.py` / `-results.md`: live issues through the real
  router: 13/13 to the intended lane, five distinct phase lists
- plus the cost, heartbeat-recovery, learn-loop, conflict-run, fleet-run,
  governor-live, relay, and session-learnings evidence, and the human
  gate's design doc (`hitl-design.md`)

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
