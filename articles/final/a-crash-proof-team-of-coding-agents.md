# A Crash-Proof Team of Coding Agents

### Kill the worker mid-task and the agent finishes the job anyway — same session, four cents. This is what durability buys when one coding agent becomes a governed team.

---

![A Crash-Proof Team of Coding Agents — an amber core marked with a spark (Claude Code, the judgment work) sits inside one indigo orbit carrying eight satellite jobs, nine in all; a red Kill -9 bolt snaps the orbit and a green heartbeat weld re-closes it; a luminous thread woven from an amber strand (the durable conversation) and an indigo strand (the durable job) enters the system from the headline side and leaves it to a merged ring, over a faint event-history tick line](../../assets/medium-heroes/a-crash-proof-team-of-coding-agents.png)

A long headless run of an AI coding agent (headless: one command in a terminal, no chat window) gets interrupted routinely: a worker restarts, the API returns an overload error, a stream drops. There is a moment in every infrastructure demo where you stop trusting the slides and ask the presenter to pull the plug, so we opened this project by pulling it ourselves.

We killed the worker's whole process tree three minutes into a task, with no completed result saved anywhere. A different process on a restarted worker picked up the same half-finished conversation and ran it to completion as the same session.

That is the durability half of this article, and it is the smaller half. The bigger half is what durability buys: a durable team of nine single-purpose jobs, split into lanes with a real division of labor and one clear mandate apiece. One of the nine runs Claude Code itself, and it does all the judgment work: building the feature, reviewing the diff, resolving the conflict. The other eight carry the delivery pipeline around it, from opening the pull request to pushing a resolved branch. Each lane's agent is equipped with its team's skills: actual playbook files it discovers and invokes, not adjectives in a prompt. It is governed by hooks and deny rules the workspace re-asserts before every chunk (one bounded slice of a run, capped at a fixed number of agent turns): an org-wide floor identical for every lane, every retry, every resume, plus the watched rules and finish gate each team commits for itself. That team carried a filed GitHub issue all the way to a merged pull request, resolving a real merge conflict along the way, with no human decision in the loop.

*The fine print, up front: one engineer ran everything here, and the "we" throughout is editorial. The agent model in every measured run is `haiku`, Claude's cheap fast tier, in July 2026; the tasks are benchmark-sized and the run counts are single-digit, so every number is a point estimate, not a distribution. Every number also traces to an evidence file in the public repository, [thumarrushik/temporal-claude-demo](https://github.com/thumarrushik/temporal-claude-demo), with the runners under `deploy/`. The dollar figures are haiku-priced, too: on a stronger model tier, every absolute number here scales up roughly an order of magnitude.*

## Claude Code Is Already Half a Durable System

Run Claude Code headless and it executes the whole agent (reading files, editing them, running the tests), prints a result, and exits. That result carries a **session ID**. Hand the ID back later with a resume flag and the agent reopens that exact conversation with everything it had learned, because the transcript is an ordinary file on disk, filed under the directory the agent ran in. The *conversation* is already durable. And this is not a toy mode: the official GitHub Action ships this same headless agent into continuous integration, where it reviews pull requests and fixes failing checks, an Action built on the very agent framework this project uses.[^1][^2]

It also ships a real guardrail harness: the part that matters the moment you hand an agent a shell. The dangerous commands are denied by the tool itself, not merely discouraged in a prompt: deleting a tree, escalating privileges, pushing to a remote. A hook fires after every single tool call and can veto it and log it. The operating system sandboxes what the process can touch. Skills and a required output schema shape what the agent does and what it must return.[^3] A line in a prompt is a suggestion. A deny rule is a fact, identical on the first attempt and the sixth.

That is one half of a durable system, and it is the hard, conversational half. The other half its own documentation quietly concedes. A resumed session is local to the machine and the directory it was born in. There is no way to move it to another box, no lease, nothing that notices the machine died and carries the work elsewhere.[^4] The agent remembers the conversation. **Nothing remembers the job.**

![Half a Durable System: Claude Code already ships a durable conversation (a transcript on disk, resumable by ID) and enforced guardrails (deny rules, audit hooks, an OS sandbox), but the job that drives it is machine-local and forgotten; Temporal supplies that missing half](../../assets/diagrams/half-a-system.png)
*Half a Durable System. Two of the three pieces already exist. The job is the piece Claude Code leaves on the floor: the thing that would notice a dead machine and move the work.*

## The Job Is the Half That Dies

The obvious way to drive a headless agent is a loop. Ask it to continue, refresh the session ID from the result, ask it to continue again:

```bash
while :; do claude -p "continue" --resume "$SID" --max-turns 6; done
```

The real thing parses each run's output to keep the session ID current, but that is the shape. It works right up until the process holding it dies. And when that process dies, exactly one thing survives, because it is a file on disk: the transcript. Everything else was memory. The current session ID. The retry count. The instruction someone typed an hour ago. The bare fact that a job was running at all.

An agent run is precisely the kind of job you cannot afford to forget. It runs for hours. It bills by the minute. It carries context it took real work to accumulate. It touches real systems. And it tends to fail while unattended. Remember it yourself and you end up hand-building durable state, a single-writer lock, a retry taxonomy, a liveness probe, and a status endpoint, until you own a distributed system you never meant to design. Or you can give the job the one thing the conversation already has: a record that outlives the process.

## The Missing Half Has a Name

Strip the agent out of that hand-built list and what is left over (durable state, one writer at a time, retries, timeouts, liveness, a way to see what happened) is not an AI problem at all. It is the standard checklist for any long job that has to outlive its own hardware, and the industry has a name for the answer: **durable execution**. Temporal, the engine we used, grew out of a system built at Uber to run exactly these long, crash-prone, many-step jobs.[^5]

The core move is a refusal to trust process memory. A database does not keep your data safe by keeping its process alive; it writes every change to a log and rebuilds after a crash by replaying it. Durable execution does the same thing for *program control flow*. Every step a job takes (a step scheduled, a result returned, a timer fired, a message received) is appended to a ledger on the server, the **event history**. Kill the process and a new one reads that history back and continues from exactly where the job was.

![Durable Execution: a mortal worker runs the job and appends every step to an append-only event history on the server; when the worker dies mid-job, any new worker replays the ledger and continues from exactly where the job was](../../assets/diagrams/durable-execution.png)
*Durable Execution. The worker is disposable on purpose. It appends every step to the history as it goes; when it dies, any other worker replays the ledger and picks up mid-job. No memory snapshot required.*

The trick that makes the reconstruction work is **deterministic replay**. Temporal never photographs memory. It re-runs the job's code from the first line, and at every step that already happened, it substitutes the recorded result instead of doing the work again. Same code, same recorded inputs, same decisions: the replay lands in the same state. The catch lives in the word *same*. One clock reading, one coin flip, one network call in the replayed layer, and the replay diverges from its own history and the whole trick breaks.

That constraint forces a clean split, and three plain words carry the rest of this article. A **workflow** is the code that decides what a job does next: the deterministic, replayable layer, the part that must never flip a coin. A **worker** is an ordinary process on some machine that physically does the work, and it is meant to be mortal. An **activity** is a single step that the engine treats as a sealed box: it may call the network, write files, roll dice, anything, because Temporal never replays an activity's insides. Each step retries under a policy you declare rather than code. And while a step runs, it can send **heartbeats**: small liveness pulses that may carry a little data with them, so that if the pulses stop for too long, the server declares that attempt dead and starts a retry that can read the last pulse the dead attempt sent.[^6]

That last capability, a retry that can read the dead attempt's final heartbeat, is the mechanism the rest of this design rests on.

## Put the Agent Where Non-Determinism Is Legal

One problem looks fatal at first. A workflow has to be deterministic, and an AI coding agent is the least deterministic software you will ever run: same prompt, different transcript, every time. Put the agent inside workflow code and the first replay diverges on the first token. That is a category error, not a knob you can tune.

But durable execution already has a room where non-determinism is not just tolerated but expected: the activity. Seal the entire agent inside an activity and the workflow never sees the chaos. All it sees is what crosses back as plain data: a session ID, an outcome, a dollar cost, a validated pass/fail report. Its own logic collapses to something a database could run: read a typed result, decide *continue or stop*, repeat. The tool calls and the token sampling never touch the replayable layer.

![The Seam: on the left, a deterministic, replayable agent-task workflow whose only decision is to read a typed result and run another chunk or stop; on the right, the non-deterministic agent sealed inside an activity; only typed data (session ID, outcome, cost, report) crosses back](../../assets/diagrams/seam.png)
*The Seam. The workflow stays replayable because the agent is sealed inside an activity. Only typed data crosses the line, so the workflow's own decisions never depend on anything the agent did unpredictably.*

Two details make resume survive that boundary. First, each run gets one stable working directory, derived from the job's own identity, so every attempt lands in the same folder, and because the agent files its transcript under the directory it ran in, landing in the same folder is exactly what lets a retry find the same conversation again. Second, the workflow always chains forward the latest session ID an activity hands back, because a resume can mint a fresh one. What the job's ledger actually stores is a *pointer* into the conversation's transcript. That pointer is very nearly the entire integration.

## Recovering a Crashed Run from Its Last Heartbeat

This is where the sealed box earns its place.

While the agent works, a timer inside the activity fires a heartbeat every thirty seconds no matter what the agent is doing. Deliberately dumb: a pulse tied to the agent's own output would make a long, silent tool call (a slow test suite, a dependency install) look identical to a dead worker. A timer removes the ambiguity. If the heartbeats stop, the worker's event loop actually stopped, and the two-minute heartbeat timeout trips. The opposite failure, an agent still alive and still pulsing but wedged in a loop or a hung tool, never trips that timeout, so a separate, longer ceiling on the whole chunk bounds that case instead: two timeouts for two distinct ways to be stuck. Every pulse carries the latest known session ID, which the agent announces at the very start of a run.

Now kill the worker. The pulses stop. After the heartbeat timeout the server declares the attempt dead and schedules a retry, and the retry reads the session ID straight out of the dead attempt's last heartbeat and relaunches the agent with a resume. No completed checkpoint is required; the last heartbeat serves as the checkpoint.

![Recovering a Crashed Run: worker attempt 1 runs the agent mid-chunk with no completed result, heartbeating the live session ID every 30 seconds; a SIGKILL kills the whole worker; after the heartbeat timeout Temporal retries; attempt 2 reads the session ID out of the dead attempt's last heartbeat and resumes the same conversation, finishing in one chunk](../../assets/diagrams/heartbeat.png)
*Recovering a Crashed Run from Its Last Heartbeat. Attempt 2 recovers the session ID from the dead attempt's final pulse, no completed result required, and resumes the same conversation. A re-read, not a re-run.*

We proved it the blunt way. We started a run, waited until the agent was mid-task and actively writing files (the session live, its ID already heartbeated), and then killed the worker's **entire process tree** with an unblockable signal, leaving no completed result to fall back on. A restarted worker was already polling. After the timeout, Temporal retried the step, and the evidence of what happened is a single line the recovered run left in its workspace:[^7]

```json
{"event": "resume_session_from_heartbeat", "attempt": 2,
 "input_session_id": null, "heartbeat_session_id": "698c432a-…"}
```

The input session ID is null: the workflow had no completed chunk to hand back. The ID came *only* from the heartbeat. The run finished as the **same** session in one chunk. Its total cost was $0.0404, and that figure is not a recovery penalty; it is the ordinary cost of the resumed session re-reading its own accumulated context at the cache rate and then finishing the work. (One accounting honesty: whatever the dead attempt burned before the kill never returned a result, so it appears in no ledger; the figure is the surviving attempt's bill.) The durability machinery itself added no tokens.

Three things have to be right, and each is a caveat worth stealing. **The heartbeat has to be recorded before the crash.** The SDK worker throttles how often heartbeat details are actually recorded to the server, and the default throttle is too coarse to catch a short chunk, so this project's worker tightens it on purpose.[^8] **The worker has to die as a whole group.** Kill only the parent and the agent's child process is orphaned, finishes the work anyway, and *masks* the recovery: our first recovery demos "succeeded" exactly this way, and they were lying, more than once, before we caught it. **And the crash has to land while the chunk is genuinely in flight.** Get those right and a dead worker becomes one line in the history that the workflow code never even mentions.

The everyday value is not that deliberate kill; a worker rarely dies outright. What actually stops a headless run is the API on the other end: an overload during a busy hour, a rate limit, a dropped stream. The agent surfaces those on its result; the activity raises them as typed, retryable failures; the retry policy backs off (five seconds, doubling to a two-minute cap, six attempts) and every retry *resumes* the conversation instead of restarting the task. An overload window becomes added latency rather than a failed run.

Point that same machinery at a whole repository and it does something bigger. The heartbeat, the resume, and the declared retries that just carried one agent through a crash are what will carry a whole *team* of agents from a filed issue to a merged pull request, resolving a real merge conflict along the way. That team is the back half of this article. But every agent on it runs inside the same sealed box you just watched recover, so it is worth opening that box to see exactly how one is built.

## What Durability Actually Costs

So we measured all of it directly: the same fixed test-driven task, on a small fast model, everything **observed rather than modeled**, run strictly one at a time. Three numbers matter: what a **continuous** run costs, what a **resume** adds when a crash interrupts one, and what **fine chunking** costs when you slice the run into many boundaries.

![What Durability Costs: two measured panels, everything relative to the roughly eleven-cent continuous base. Left panel: an interrupted run is the base plus a few cents to resume — plus $0.0035 warm ($0.117 total), plus $0.021 cold ($0.134 total). Right panel: fine-chunking the same task adds from near-zero to about two dollars ($0.034, $0.25, $2.13 at 1, 8, and 14 chunks), ballooning with the number of boundaries](../../assets/diagrams/cost-comparison.png)
*What Durability Costs (measured, small model). Everything sits on top of the roughly eleven-cent continuous base. Left: after a crash, resuming only re-reads the accumulated context at the cache rate: the session's own cost, not a durability charge. Right: fine chunking adds anywhere from near-zero to two dollars, unpredictably, because a tight turn cap can send the agent to fourteen chunks to finish what one session did in nine turns.*

**A continuous run costs about eleven cents (`deploy/chunk-cost-results.md`)**: three runs came in at six, thirteen, and fifteen cents, with the agent taking anywhere from three to nine turns for the identical task. **Durability adds no tokens; a resume only re-reads context.** After a crash, resuming re-reads the accumulated conversation at the cheap cache-read rate: about a third of a cent warm, roughly 3% of the base run. Even a *cold* first touch after leaving the session idle for sixty-five minutes paid only a partial cache-write, about two cents, and then re-warmed. The API's extended-lifetime prompt caching keeps resumes cheap far past the usual five-minute window. That third-of-a-cent figure *is* the heartbeat-recovery number: a resume, not a restart from zero. (The live worker-kill from earlier, a separate and smaller task, landed at four cents total.)[^10]

**Fine chunking is where the bill gets dangerous.** The same task, sliced into back-to-back two-turn chunks, cost $0.034, $0.25, and $2.13 across runs that took one, eight, and fourteen chunks: identical task, identical code, a sixty-three-fold spread, with the worst run costing nineteen times the continuous base. And the culprit is not the mechanism we expected. The per-boundary cache re-read is *not* it; it stays a cheap fraction of a cent. The culprit is **behavioral**: a tight turn cap can send the agent to fourteen chunks and twenty-eight turns to finish what a continuous run did in nine. More turns, more output, and a prefix re-read at every seam. Coarse chunks simply do not hand it that much room to wander.

So the rule is **large chunks by default**: fine chunking is the only lever that meaningfully moves the total, and it moves it unpredictably. The baseline worth remembering is the bare loop with no durability at all: it pays the same eleven cents while nothing breaks, but a crash costs a full re-run, because the session ID died with the process. The durable coarse run pays the same bill and recovers for a fraction of a cent; a live issue-to-pull-request job confirmed it again, coming in at a clean eleven cents. The durability itself is effectively free. And notice what every number in this section has in common, because the pattern recurs across everything we measured: **the mechanics cost cents; the behavior costs dollars.** Resuming, recovering, chunking at a boundary are all pennies. The two-dollar surprise was something a model *chose to do with its turns*. Small chunks earn their keep for a different job entirely, which is next.

One more honesty note: "effectively free" is a pricing snapshot, not an architecture property — it leans on cache-read rates and cache lifetimes that can change under you. The repo runs an economics canary that re-probes exactly these invariants on a schedule; its latest pass held every one (`deploy/canary-results.md`, about nine cents a pass).

## When Bare Claude Code Is Enough

Durability is insurance, and you do not insure a cheap errand. The alternative to this harness is not a lousy while-loop; it is Claude Code's own considerable durability, and sometimes that is the right answer.

- **The task is cheap to re-run from scratch.** A one-chunk, two-minute job needs a retry button, not an engine. The plain headless command plus your CI's retry is the correct architecture.
- **One developer, one machine, interactive.** The transcript plus a resume by hand *is* the durability layer. A workflow engine on a laptop is ceremony.
- **You would rather buy the orchestration than own it.** If owning the loop is not strategic for you, a managed agent runner is a legitimate answer to the same problem.

The threshold is crisp. The moment a task **outlives the process that started it** (an overnight run, a queue of issues, anything a deploy or a crash can interrupt, anything whose re-run from zero is a real bill), something has to remember the job. Then you have exactly three options: lose the state and eat the tokens; hand-build the state machine and debug it by incident; or use an engine whose entire product is that state machine.

## The Team, in One Breath

Everything above is one durable agent. The other half of this project is what
happens when you scale that agent into a delivery team, and the short version
fits in a breath. The work is split into single-purpose durable jobs — nine in
the runs measured here; the repo now ships twelve activities across six team
lanes — and only one of them runs Claude Code. It does all the judgment work:
building the feature, reviewing the diff, resolving the conflict. The rest are
plumbing with receipts: open the PR, push the branch, merge on a green verdict.

Each team is its own queue on the workflow engine, and that sentence is doing
more work than it looks like. A backend worker is trusted to do backend work
not because its prompt says *act like a backend engineer*, but because it
listens on the backend queue, runs under the backend team's own committed
playbooks, emits backend audit artifacts, and answers to the same retry and
cost machinery as every other lane. **It is trusted by the queue it polls, not
by the prompt it was handed.** The formula for a team member is four files in
version control: a mandate (the one job it owns), skills (the playbooks it
actually follows), hooks (rules enforced on every tool call), and a settings
file stamped from human-committed sources — none of it lives in the model.

The full anatomy — lanes and namespaces, the chunk mechanics, the audit
plane, how a filed issue becomes a merged PR — is one click away in the
engineering companion, [How It's Built](how-its-built.md). What belongs here
is the one story that proves the team is real.

## The Conflict That Resolved Itself

Every piece of that machinery was about to be needed at once, so we built a real target for it: a full-stack "snippets" web app, backend and frontend and browser tests, wired to a live deployment with a namespace per team and the poller on a schedule.

Two backend issues landed in the same poll window and collided by construction. Both edited the same region of the same backend file: one added search, the other added an endpoint for deleting a snippet. Each got its own branch, its own job, its own pull request. Search merged first, and the platform immediately marked the delete request as conflicting. This is the exact spot where autonomy usually ends quietly: a "needs a manual rebase" comment, and a human inheriting the mess in the morning.

![The Conflict That Resolved Itself: an eight-step comic strip across two lanes. Top row, the review lane: 1 approves PR #4 (the change was fine, only the merge wasn't); 2 the merge is refused with HTTP 405 because the branch is stale; 3 merging the base in and retrying; 4 a real content conflict, since two PRs edited the same lines and no re-merge decides which side wins. Bottom row, the backend lane: 5 handed to the team that owns the code via a client start from inside an activity; 6 its agent keeps both changes and the tests pass ten of ten; 7 the agent can't push so the harness does, then re-merges; 8 the issue closes itself and the blocked frontend feature ships on the next poll](../../assets/diagrams/conflict.png)
*The Conflict That Resolved Itself. Read it top row then bottom row. Detection lives in the review lane; the fix lives in the lane that owns the code. The escalation is the same cross-namespace client call the scheduled poll uses.*

What happened instead, every step a durable activity in the history: the review lane approved the pull request on its merits, because the change itself was fine and only the merge was not. The merge attempt was refused. The workflow's first response was the boring, correct one (merge the base branch in and retry), and that surfaced a **real content conflict**: two pull requests had edited the same lines, and no amount of re-merging the base decides which side should win. That is a judgment call, and judgment is what the agent is for.

So the review workflow escalated, not to a human but to the team that owns the code. It read the issue number out of the branch name, looked up that issue's team, left a comment naming the resolve job, and started that job **in the backend namespace, on the backend queue**, the same client-from-inside-an-activity call the scheduled poll uses. The backend agent that picked it up was nothing special: same skill bundle, same policy, same durable harness, only the prompt was different. It merged the current base, kept both the base's changes and the branch's intent, ran the tests green on the merged tree (ten of ten), and, its own push denied by policy, left the harness to push the branch and re-merge it. *"Merge PR #4 (conflict auto-resolved)."* The issue closed itself a moment later.

Two properties keep this from being a party trick. The loop cannot run away: the resolve job's ID is deterministic (keyed by the PR *and* its current head commit, so a resolved push gets a fresh review and cascading conflicts converge), and duplicates of a live or finished job are refused by the server — a second escalation ten seconds later is a no-op. And nothing traded durability for the cleverness: the escalation is a workflow starting a workflow, subject to the same crash recovery and the same hard limits as everything else. Then the part that turns an incident into a system. A frontend issue had been sitting in the queue the whole time, marked *blocked by* the very issue that just closed. On the next poll the hold released itself; the frontend agent built a delete button against the exact endpoint the resolution had just landed, added a browser test, and opened a pull request the review lane merged. From collision to shipped downstream feature, the chain ran without a human decision in it, one mechanical asterisk included.[^11]

## What This Doesn't Solve

Six real gaps, told plainly, because the honest ones are the load-bearing ones.

- **Worker affinity.** The transcript and the workspace are local files, and resume only works where they are visible. The engine can recover the *workflow* anywhere, but a retried chunk has to land where the *session* lives. The fixes escalate: one worker per lane; a per-worker queue chosen on the first chunk; shared storage for the transcript directory and the workspace.
- **The filesystem is not checkpointed, and steps run at-least-once.** The orchestration state is durable and the transcript survives, but the working directory is neither versioned nor rolled back, so a retried chunk resumes against a directory the dead attempt half-mutated. It converged in every test here, but *converges in practice* is not *idempotent by construction*. Any outward action (a push, a comment, a merge) wants an idempotency key, and the structural fix is a fresh git worktree per chunk: commit on success, reset on retry.
- **A hard kill can orphan the agent.** Kill the worker and the agent's child process may finish its chunk anyway, racing the retry: the exact effect that masked our first recovery attempts. Production workers belong in a process group or a container that takes their children down with them.
- **Workflow code is a compatibility surface.** Deterministic replay cuts both ways: reorder the steps while runs are in flight and replaying an old history against new code can wedge the run. Evolving an orchestration in production is a versioning discipline, not just editing a function.
- **A permissions landmine.** The agent's most permissive mode combined with resume in headless mode was broken upstream and has since been marked fixed;[^13] re-check it against your version. This project sidesteps it entirely with a mode that auto-accepts file edits but still enforces an explicit allow-list for everything else.
- **The merge gate is an agent's verdict.** Approve-and-merge here is gated on a single schema-validated boolean: the review agent's tests-pass verdict. For this demo repository, that is the point; for production, it is a placeholder, not a posture. A real deployment should insert its human gate exactly there: a protected branch that requires human review, or a durable approval step the workflow waits in. That durable approval step is actually built and verified against a live server, modeling the person on the same query, update, and timer primitives as everything else, deny-safe when nobody answers; the companion piece [*The Human Is a Durable Object*](the-human-is-a-durable-object.md) is the walkthrough and the live run.

## Defaults Worth Stealing

If you build any version of this, on any stack, these are the settled defaults this project would hand you. Each one was paid for above.

- **Big chunks by default.** A tight turn cap is a slot machine: the same task ran $0.034 to $2.13 on identical code. Chunk for visibility and steering, never for durability.
- **Heartbeat a resume handle, not just liveness.** The last pulse is a free checkpoint; a retry that can read it never starts from zero.
- **Kill, and deploy, by process group.** An orphaned agent child finishes the work anyway and lies to you about whether your recovery works.
- **Deny `git push` to every agent.** The harness, with its own credentials, in its own recorded step, is the only hand that touches the outside world.
- **Route by queue, not by prompt.** A lane's queue and skill bundle are an identity a worker cannot drift out of; a persona in a prompt is not.
- **Deterministic job IDs, duplicates allowed only after failure.** Running and completed jobs are refused, so the poller needs no memory and the escalation loop cannot run away; failed jobs may retry on a later sweep, so one transient error cannot deadlock an issue forever. (A live fleet run found the stricter refuse-everything version of this rule doing exactly that; `deploy/fleet-run-results.md` has the evidence.)
- **Write the rule as a hook, not a prompt.** The written rule nudged the waste pattern down ~20% and was ignored once; the hook flagged twelve of twelve.

## The Harness Was the Hard Part All Along

One practitioner teardown of Claude Code's own codebase estimates that roughly **1.6%** of it is the AI decision logic. The other **98.4%** is operational harness: permissions, state, recovery, tools.[^14] Set that number next to the hand-build list from the start of this article and the overlap is hard to miss. The harness every agent team is rebuilding is, almost line for line, what durable-execution engines have provided for a decade.

The two sides are already circling each other. Temporal's own AI cookbook wraps model *API calls* in activities; a production write-up wraps the agent framework the same stateless way; another project built durable checkpointing around whole Claude Code runs on its own runtime.[^15][^16][^17] Each holds one half of the seam. In the sources we checked, none composes the two the way this project does: headless Claude Code *sessions*, with the session ID carried in heartbeat details mid-chunk and in workflow state after a completed one. That is a claim with a short shelf life, so re-check it before you build.

The practical takeaway is narrow. Once a task outlives the process that starts it, the durable-execution engine is the part worth adopting, and the agent belongs inside it rather than inside a hand-built loop.

But the composition is the natural one, and the seam really is small. Claude Code brings the durable conversation. Temporal brings the durable job. The agent could always remember the conversation; everything in this article is what became possible the moment something remembered the job.

---

*Disclaimer: the views and opinions expressed in this article are my own and do not necessarily reflect those of my employer. This is a personal project, not affiliated with or endorsed by Anthropic or Temporal.*

## Sources

- **Claude Code headless mode, sessions, CI action, permissions, sandboxing**: code.claude.com/docs (headless, sessions, github-actions, permissions, hooks, sandboxing, agent-sdk). *Vendor/canonical.* Checked 2026-07-15.
- **Temporal durable execution, activities, signals/queries, heartbeats, heartbeat throttling, workflow versioning**: docs.temporal.io and python.temporal.io. *Vendor/canonical.*
- **Measured runs.** The four-cost experiment (continuous ~$0.11; warm resume $0.0035; cold resume $0.021; fine-chunked $0.034–$2.13), the failure→heartbeat→resume recovery, and the corpus/learn-loop before/after are reproducible from the public repo, [github.com/thumarrushik/temporal-claude-demo](https://github.com/thumarrushik/temporal-claude-demo): `deploy/full-experiment-results.md`, `deploy/heartbeat-recovery-results.md`, `deploy/learn-loop-results.md`, with runners and analyzers under `deploy/`. Agent model `haiku`, 2026-07-15.
- **Most-permissive mode + resume bug**: github.com/anthropics/claude-code issue #36139. *Vendor issue tracker.* Re-check before reuse.
- **1.6% / 98.4% harness split**: *Dive into Claude Code* teardown, arXiv 2604.14228. *Practitioner/academic.*
- **Temporal AI cookbook (model API in activities); agent-framework × Temporal production guide; durable Claude Code checkpointing on another runtime**: docs.temporal.io/ai-cookbook; claudelab.net (2026-04-22); zenml.io/blog (2026-06-01). *Vendor + practitioner.*

[^1]: Claude Code headless mode: `--output-format json` returns `session_id`, cost, and (with a JSON schema) structured output; `--resume <id>` continues a stored session; transcripts are stored under `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, the working-directory path with non-alphanumerics replaced. Checked 2026-07-15. *Vendor/canonical.*

[^2]: `anthropics/claude-code-action@v1` (GA) runs headless Claude Code on `pull_request`/cron and on `@claude` mentions, with automatic PR review; the docs note it is built on the Claude Agent SDK. Checked 2026-07-15. *Vendor/canonical.*

[^3]: Claude Code permissions are evaluated deny → ask → allow (a deny is unoverridable) and "enforced by Claude Code, not by the model"; `PostToolUse` hooks receive the tool event as JSON and can block a call; Bash sandboxing uses Seatbelt (macOS) / bubblewrap (Linux). Checked 2026-07-15. *Vendor/canonical.*

[^4]: Claude Code sessions: resume lookup "is scoped to the current project directory and its git worktrees"; there is no documented cross-machine session transport or leasing: the gap an external orchestrator must fill. Checked 2026-07-15. *Vendor/canonical.*

[^5]: Temporal docs: durable execution persists workflow progress as an event history; workflows must be deterministic so history replay reconstructs state; activities host side effects and are retried by policy; Temporal descends from Cadence, built at Uber. *Vendor/canonical.*

[^6]: Temporal Python SDK: `activity.heartbeat(*details)` sends heartbeat details, and `activity.info().heartbeat_details` exposes the previous attempt's details to a retry. The worker throttles how often details are persisted (`max_heartbeat_throttle_interval` / `default_heartbeat_throttle_interval`). Checked 2026-07-15. *Vendor/canonical.*

[^7]: `deploy/heartbeat-recovery.sh`, 2026-07-15: the worker's whole process tree was SIGKILLed mid-chunk before any completed result; attempt 2 recovered the heartbeat session ID (with the input session ID null) and relaunched with resume; it completed as one chunk, $0.0404, the same session. Requires a heartbeat throttle short enough to persist the ID, and a process-group kill so the agent child can't orphan-finish the work.

[^8]: With a heartbeat timeout set, the effective throttle is `min(heartbeat_timeout × 0.8, max_heartbeat_throttle_interval)`; the worker sets both throttle knobs from an environment variable (default 15s) so the in-flight session ID is recorded promptly. See `src/worker.py`.

[^10]: `deploy/full-experiment.py`, 2026-07-15, model `haiku`, run strictly sequentially; everything observed, not modeled. Continuous measured ×3 ($0.058/$0.132/$0.149); warm boundary via no-op resume ×5 ($0.0035, cache-read); cold boundary via no-op resume after a 65-min idle gap ($0.021, partial cache-write); fine-chunked totals ×3 ($0.034/$0.25/$2.13 at 1/8/14 chunks). Cost is the CLI's own `total_cost_usd`, identical on a laptop or a cloud VM. Full write-up: `deploy/full-experiment-results.md`.

[^11]: The asterisk: that frontend pull request predated the escalation code, so its review was re-triggered against the new code, and the final polls were hand-triggered rather than waited out on the timer. The scheduled poll and the first-pass routing are proven across the other recorded runs; this run isolates the resolution chain. Evidence file: `deploy/conflict-run-results.md`.

[^13]: anthropics/claude-code#36139: bypass-permissions mode misbehaves with `--resume` in print mode; reported and marked resolved (re-check against your installed version). This project uses an accept-edits mode plus an allow-list plus workspace deny rules instead. *Vendor issue tracker.*

[^14]: *Dive into Claude Code* (arXiv 2604.14228): ~1.6% of the codebase is AI decision logic; ~98.4% operational harness. *Practitioner/academic.*

[^15]: Temporal AI cookbook: the "Basic agentic loop with Claude" uses model Messages API calls as activities; no Claude Code CLI, no session resume. *Vendor/canonical.*

[^16]: "Building fault-tolerant long-running AI workflows with Claude Agent SDK × Temporal.io," claudelab.net (2026-04-22): wraps API messages in activities; no headless sessions, no cross-activity resume. *Practitioner.*

[^17]: "Don't make Claude do the same work twice," zenml.io (2026-06-01): durable checkpointing of Claude Agent SDK runs on ZenML's own runtime, not Temporal. *Practitioner.*

