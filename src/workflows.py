"""Durable agent-task workflow: run Claude Code in bounded, resumable chunks."""

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from activities import (
        export_claude_session_transcript,
        open_pull_request,
        push_branch,
        run_claude_chunk,
        update_pr_branch,
    )
    from poller import (
        escalate_conflict,
        escalate_fix,
        escalate_review,
        merge_pull_request,
        poll_github_activity,
        post_pr_review,
        read_pr_review_state,
    )
    from shared import (
        ApprovalDecision,
        ChunkInput,
        ConflictEscalationInput,
        FixEscalationInput,
        HumanReviewState,
        MergeInput,
        OpenPRInput,
        PollInput,
        PollSummary,
        PostReviewInput,
        PushBranchInput,
        ReviewEscalationInput,
        TaskInput,
        TaskProgress,
        TaskResult,
        TranscriptExportInput,
        UpdateBranchInput,
        corrective_instruction,
        model_for_chunk,
        normalize_team,
        pin_queue,
    )

CONTINUE_PROMPT = (
    "Continue the task. Pick up exactly where you left off; "
    "check the state of the working directory before redoing anything."
)


@workflow.defn
class RunClaudeTask:
    def __init__(self) -> None:
        self.progress = TaskProgress()
        self.pending_instructions: list[str] = []
        self._gate: dict | None = None
        self._decision: ApprovalDecision | None = None

    @workflow.query
    def get_progress(self) -> TaskProgress:
        return self.progress

    @workflow.query
    def get_pending_approval(self) -> dict | None:
        """What the workflow is blocked on, or None. The operator CLI's inbox."""
        return self._gate

    @workflow.update
    def decide(self, decision: ApprovalDecision) -> str:
        """The human decides. An UPDATE, not a signal: the validator below
        rejects malformed or unsolicited decisions before anything enters the
        history, and the caller gets a definitive result back."""
        self._decision = decision
        return f"recorded: {'approved' if decision.approved else 'rejected'} by {decision.decided_by}"

    @decide.validator
    def _decide_validator(self, decision: ApprovalDecision) -> None:
        if self._gate is None:
            raise ApplicationError("no approval is pending on this workflow")
        if not decision.decided_by:
            raise ApplicationError("decided_by is required — decisions are attributable")

    async def _human_gate(self, action: str, detail: str, input: TaskInput) -> bool:
        """The human as a durable construct: open a gate, wait for a validated
        decision with a deadline, deny-safe on timeout. The wait survives
        worker crashes and deploys — waiting is what workflows are for."""
        if not input.require_approval:
            return True
        self._gate = {"action": action, "detail": detail,
                      "timeout_h": input.approval_timeout_h}
        self.progress.awaiting_approval = True
        try:
            await workflow.wait_condition(
                lambda: self._decision is not None,
                timeout=timedelta(hours=input.approval_timeout_h),
            )
        except asyncio.TimeoutError:
            # The deadline is part of the contract: an unattended gate closes
            # itself on the safe side, attributably.
            self._decision = ApprovalDecision(
                approved=False, decided_by="deadline",
                note=f"auto-denied after {input.approval_timeout_h}h",
            )
        self.progress.awaiting_approval = False
        self.progress.approval = self._decision
        approved = self._decision.approved
        self._gate, self._decision = None, None  # re-arm for any later gate
        return approved

    @workflow.signal
    def steer(self, instruction: str) -> None:
        """Mid-run steering: queued instructions are injected into the prompt
        of the next chunk, where the resumed session picks them up."""
        self.pending_instructions.append(instruction)
        self.progress.steer_count += 1

    def _next_prompt(self, base: str) -> str:
        if not self.pending_instructions:
            return base
        instructions = "\n".join(f"- {i}" for i in self.pending_instructions)
        self.pending_instructions = []
        return (
            f"{base}\n\nNew instructions from the operator or the workspace "
            f"governor (arrived while you were working — fold them into the task):\n{instructions}"
        )

    _POST = dict(
        start_to_close_timeout=timedelta(minutes=3),
        retry_policy=RetryPolicy(maximum_attempts=3),
    )

    async def _merge_with_self_heal(self, input: TaskInput) -> None:
        """Merge the PR; if it conflicts because the branch is stale, update the
        branch with base and retry once. A real content conflict is escalated to
        the owning team's agent (escalate_conflict), which resolves it and
        re-merges — fully autonomous."""
        headline = f"Merge PR #{input.pr_number} (auto-approved)"
        result = await workflow.execute_activity(
            merge_pull_request,
            MergeInput(repo=input.repo, number=input.pr_number, commit_headline=headline),
            **self._POST,
        )
        if result.merged or not result.conflict or not input.branch:
            return
        # Stale branch — bring it up to date with base, then retry the merge.
        upd = await workflow.execute_activity(
            update_pr_branch,
            UpdateBranchInput(repo=input.repo, branch=input.branch,
                              number=input.pr_number, base=input.base_branch),
            **self._POST,
        )
        if upd.updated:
            await workflow.sleep(timedelta(seconds=10))  # let GitHub recompute mergeability
            retry = await workflow.execute_activity(
                merge_pull_request,
                MergeInput(repo=input.repo, number=input.pr_number, commit_headline=headline),
                **self._POST,
            )
            if not retry.merged and retry.conflict:
                # Base moved again during the update window — a real conflict
                # now; hand it to the owning team instead of dropping it.
                await workflow.execute_activity(
                    escalate_conflict,
                    ConflictEscalationInput(repo=input.repo, pr_number=input.pr_number,
                                            branch=input.branch, base=input.base_branch,
                                            model=input.model),
                    **self._POST,
                )
        elif upd.conflict:
            # Real content conflict — loop the owning team's agent back in to
            # resolve it (merge base, fix conflicts, test). Its post-completion
            # pushes the resolved branch and re-merges the PR. Fully autonomous.
            await workflow.execute_activity(
                escalate_conflict,
                ConflictEscalationInput(repo=input.repo, pr_number=input.pr_number,
                                        branch=input.branch, base=input.base_branch,
                                        model=input.model),
                **self._POST,
            )

    @staticmethod
    def _review_feedback(report: dict, human: HumanReviewState) -> str:
        """The feedback a fix job must address: the reviewer's summary plus any
        human Request-Changes note."""
        parts = []
        summary = (report.get("summary") or "").strip()
        if summary:
            parts.append(f"Review summary: {summary}")
        if human.requests_changes and human.body:
            parts.append(f"Human ({human.reviewer or 'reviewer'}) requested changes: {human.body}")
        elif human.requests_changes:
            parts.append("A human requested changes on this PR.")
        return "\n\n".join(parts)

    async def _escalate_fix(self, input: TaskInput, feedback: str) -> None:
        """Hand a not-approved PR to the owning team's lane to fix, re-validate,
        and push. The fix job's post-completion re-reviews and re-asks the human.
        Bounded by max_fix_rounds (checked by the caller)."""
        await workflow.execute_activity(
            escalate_fix,
            FixEscalationInput(
                repo=input.repo, pr_number=input.pr_number, branch=input.branch or "",
                feedback=feedback, fix_round=input.fix_round + 1, base=input.base_branch,
                model=input.model, require_approval=input.require_approval,
                approval_timeout_h=input.approval_timeout_h, max_fix_rounds=input.max_fix_rounds),
            **self._POST,
        )

    async def _post_completion(self, input: TaskInput, team: str, work_dir: str, report: dict) -> None:
        """After a successful run: open a PR (issue lanes) or post the review
        verdict + merge on approval (review lane)."""
        if not input.repo:
            return
        source = input.source or ""
        if source.startswith("fix-") and input.branch and input.pr_number:
            # A fix job finished: the owning team's agent addressed the feedback
            # and re-ran the tests. Push the fix, then re-review + re-ask the human
            # (escalate_review). The loop closes there, bounded by max_fix_rounds.
            await workflow.execute_activity(
                push_branch,
                PushBranchInput(repo=input.repo, branch=input.branch, work_dir=work_dir),
                **self._POST,
            )
            await workflow.sleep(timedelta(seconds=10))  # let GitHub see the push
            await workflow.execute_activity(
                escalate_review,
                ReviewEscalationInput(
                    repo=input.repo, pr_number=input.pr_number, branch=input.branch,
                    fix_round=input.fix_round, base=input.base_branch, model=input.model,
                    require_approval=input.require_approval,
                    approval_timeout_h=input.approval_timeout_h,
                    enable_fix_loop=input.enable_fix_loop, max_fix_rounds=input.max_fix_rounds),
                **self._POST,
            )
            return
        if source.startswith("resolve-") and input.branch and input.pr_number:
            # A resolve job finished: the owning team's agent merged base into the
            # branch and fixed the conflict. Push the resolved branch, then merge
            # the PR directly (the change was already reviewed before it conflicted).
            await workflow.execute_activity(
                push_branch,
                PushBranchInput(repo=input.repo, branch=input.branch, work_dir=work_dir),
                **self._POST,
            )
            await workflow.sleep(timedelta(seconds=10))  # let GitHub recompute mergeability
            await workflow.execute_activity(
                merge_pull_request,
                MergeInput(repo=input.repo, number=input.pr_number,
                           commit_headline=f"Merge PR #{input.pr_number} (conflict auto-resolved)"),
                **self._POST,
            )
            return
        if team == "review" and input.pr_number:
            tests_passed = bool(report.get("tests_passed"))
            # A human "Request Changes" review also blocks the merge. Our own bot
            # only posts COMMENT reviews, so any CHANGES_REQUESTED state is a human.
            human = HumanReviewState()
            if input.enable_fix_loop:
                human = await workflow.execute_activity(
                    read_pr_review_state, args=[input.repo, input.pr_number], **self._POST)
            approved = tests_passed and not human.requests_changes

            at_cap = not (input.enable_fix_loop and input.fix_round < input.max_fix_rounds)
            body = report.get("summary", "")
            if not approved and input.enable_fix_loop and at_cap:
                body += (f"\n\n⛔ Automated fix loop reached its limit "
                         f"({input.max_fix_rounds} rounds) without passing. Handing off to a human.")
            await workflow.execute_activity(
                post_pr_review,
                PostReviewInput(repo=input.repo, number=input.pr_number,
                                approve=approved, body=body),
                **self._POST,
            )

            if not approved:
                # Not approved (red suite or human Request-Changes): fix it in the
                # owning lane if we still have rounds; otherwise stop and await a human.
                if input.enable_fix_loop and not at_cap:
                    await self._escalate_fix(input, self._review_feedback(report, human))
                return

            # Approved: gate the merge on a human. A denial that carries a note is
            # itself a change request — fix it (under the cap) instead of just stopping.
            if await self._human_gate("merge", f"PR #{input.pr_number} on {input.repo}", input):
                await self._merge_with_self_heal(input)
            else:
                decision = self.progress.approval
                if (input.enable_fix_loop and input.fix_round < input.max_fix_rounds
                        and decision is not None and not decision.approved
                        and decision.decided_by != "deadline" and decision.note):
                    await self._escalate_fix(
                        input, f"A human requested changes at the merge gate: {decision.note}")
            return
        if input.branch and source.startswith("issue-"):
            issue_n = int(source.split("-")[-1])
            title = (input.task.strip().splitlines() or [f"Issue #{issue_n}"])[0][:100]
            await workflow.execute_activity(
                open_pull_request,
                OpenPRInput(repo=input.repo, branch=input.branch, work_dir=work_dir,
                            issue_number=issue_n, title=title, base=input.base_branch),
                **self._POST,
            )

    @workflow.run
    async def run(self, input: TaskInput) -> TaskResult:
        session_id: str | None = None
        work_dir = ""
        team = normalize_team(input.team)
        self.progress.team = team
        self.progress.fix_round = input.fix_round

        # Worker affinity: the first chunk runs on the lane queue (any worker);
        # once a chunk reports its stable per-worker queue, pin every later
        # chunk and the transcript export there, so a resume lands on the worker
        # that holds the session's local transcript and workspace. Off by
        # default (pinned == "" → pin_queue returns the lane queue), so a
        # single-worker lane is unchanged.
        lane_queue = workflow.info().task_queue
        pinned_queue = ""

        for chunk in range(input.max_chunks):
            base = input.task if chunk == 0 else CONTINUE_PROMPT
            prompt = self._next_prompt(base)

            result = await workflow.execute_activity(
                run_claude_chunk,
                ChunkInput(
                    prompt=prompt,
                    team=team,
                    session_id=session_id,
                    max_turns_per_chunk=input.max_turns_per_chunk,
                    model=model_for_chunk(input, chunk, self.progress.escalated),
                    repo=input.repo,
                    branch=input.branch,
                ),
                task_queue=pin_queue(lane_queue, pinned_queue),
                start_to_close_timeout=timedelta(minutes=15),
                heartbeat_timeout=timedelta(minutes=2),
                # Tuned for the common failure — API errors (429/529). Three
                # fast attempts don't survive an overload window; back off up
                # to 2 minutes and try longer before giving up.
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(minutes=2),
                    maximum_attempts=6,
                ),
            )

            # Resuming can mint a new session ID — always chain the latest one.
            session_id = result.session_id
            work_dir = result.work_dir
            # Pin to the worker that just held the session (first non-empty
            # wins and sticks); "" when affinity is off, leaving the lane queue.
            pinned_queue = pinned_queue or result.worker_queue
            self.progress.chunks_completed += 1
            self.progress.total_cost_usd += result.cost_usd
            self.progress.session_id = session_id

            # The governor: the workspace hooks flagged rule violations during
            # the chunk and the activity returned them as typed data. Steer a
            # correction into the next chunk, and let sustained flag pressure
            # climb the model ladder ahead of the chunk-count threshold.
            flags = result.rule_flags or {}
            if flags:
                self.progress.rule_flags_total += sum(flags.values())
                # Steer only while the run continues — a correction after the
                # final successful chunk would just buy a pointless extra chunk.
                note = corrective_instruction(flags)
                if note and result.subtype != "success":
                    self.pending_instructions.append(note)
                    self.progress.governor_steers += 1
                if (
                    input.escalate_model
                    and not self.progress.escalated
                    and input.escalate_on_flags is not None
                    and self.progress.rule_flags_total >= input.escalate_on_flags
                ):
                    self.progress.escalated = True

            if result.subtype == "success":
                # Steering that arrived during the final chunk hasn't been seen
                # by the agent — run one more chunk instead of finishing.
                if self.pending_instructions:
                    continue
                await workflow.execute_activity(
                    export_claude_session_transcript,
                    TranscriptExportInput(
                        session_id=session_id,
                        work_dir=work_dir,
                    ),
                    # The transcript is a local file on the worker that ran the
                    # session — read it on that same worker.
                    task_queue=pin_queue(lane_queue, pinned_queue),
                    start_to_close_timeout=timedelta(minutes=2),
                )
                # Close the loop: issue lanes open a PR; the review lane posts
                # its verdict and merges on approval.
                await self._post_completion(input, team, work_dir, result.structured or {})
                self.progress.done = True
                return TaskResult(
                    done=True,
                    result_text=result.text,
                    session_id=session_id,
                    work_dir=work_dir,
                    chunks=self.progress.chunks_completed,
                    total_cost_usd=self.progress.total_cost_usd,
                    team=team,
                    report=result.structured,
                )

            if result.subtype not in ("error_max_turns",
                                       "error_max_structured_output_retries"):
                # Only genuinely terminal subtypes reach here — API errors and
                # execution errors already raised inside the activity and were
                # retried. Structured-output exhaustion is NOT terminal: the
                # fleet run showed the work complete in the session every time
                # (REPORT.md written, conflict resolved) with only the report
                # handshake failing — so it resumes like error_max_turns and
                # the next chunk re-asks for the report with fresh attempts.
                detail = "; ".join(result.errors) if result.errors else result.subtype
                raise ApplicationError(
                    f"Claude Code failed: {detail}",
                    non_retryable=True,
                    type="ClaudeTaskError",
                )
            # error_max_turns → the task isn't finished; resume the session in
            # the next chunk.

        return TaskResult(
            done=False,
            result_text="",
            session_id=session_id,
            work_dir=work_dir,
            chunks=self.progress.chunks_completed,
            total_cost_usd=self.progress.total_cost_usd,
            team=team,
        )


@workflow.defn
class PollGitHubWorkflow:
    """One GitHub poll, run on Temporal. A Schedule fires this every interval, so
    the poll loop is durable and observable instead of a fragile external cron.

    The poll activity reads GitHub and submits ready issue/PR jobs, each into its
    team namespace. Opening the PR (issue lanes) and posting the review verdict +
    merge (review lane) happen inside each RunClaudeTask, closing the
    issue → work → PR → review → merge loop."""

    @workflow.run
    async def run(self, input: PollInput) -> PollSummary:
        return await workflow.execute_activity(
            poll_github_activity,
            input,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
