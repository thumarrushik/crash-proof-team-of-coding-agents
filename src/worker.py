"""Temporal worker: host the Claude Code workflow + activities.

Two modes:
  * ``--team <t>``  hosts RunClaudeTask + its activities on that lane's queue.
  * ``--poller``    hosts PollGitHubWorkflow + poll_github_activity on the
                    dedicated poller queue, so a Temporal Schedule can drive the
                    GitHub poll (see poller.py).
"""

import argparse
import asyncio
import logging
import os
from datetime import timedelta

from temporalio.client import Client
from temporalio.worker import Worker

# How often the worker is allowed to persist heartbeat details to the server.
# This matters for mid-chunk crash recovery: the in-flight Claude session id
# only becomes resumable once a heartbeat carrying it has been RECORDED, so the
# throttle must be short enough to flush it before a crash. (With a 2-minute
# heartbeat timeout, Temporal's default effective throttle is ~60s — too coarse
# to recover a short chunk. 15s records the session id promptly and is still
# cheap next to a Claude invocation.)
_HB_THROTTLE = timedelta(seconds=int(os.environ.get("HEARTBEAT_THROTTLE_SECONDS", "15")))

from activities import (
    export_claude_session_transcript,
    open_pull_request,
    push_branch,
    run_claude_chunk,
    update_pr_branch,
)
from canary import AdaptiveCanary, EconomicsCanary, run_canary_probes
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
    DEFAULT_NAMESPACE,
    DEFAULT_TEAM,
    POLLER_TASK_QUEUE,
    known_teams,
    TEMPORAL_ADDRESS,
    namespace_for_team,
    normalize_team,
    task_queue_for_team,
)
from workflows import PollGitHubWorkflow, RunClaudeTask


async def _run_poller_worker(namespace: str) -> None:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)
    worker = Worker(
        client,
        task_queue=POLLER_TASK_QUEUE,
        workflows=[PollGitHubWorkflow, EconomicsCanary, AdaptiveCanary],
        activities=[poll_github_activity, merge_pull_request, run_canary_probes],
    )
    print(
        f'Poller worker listening on namespace "{namespace}", '
        f'task queue "{POLLER_TASK_QUEUE}"'
    )
    print("Create the schedule with: uv run poller.py --schedule --repo owner/name")
    print("Create the canary schedule with: uv run canary.py --schedule")
    await worker.run()


async def _run_team_worker(namespace: str, team: str) -> None:
    task_queue = task_queue_for_team(team)
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[RunClaudeTask],
        activities=[
            run_claude_chunk,
            export_claude_session_transcript,
            open_pull_request,   # issue lanes: open a PR after the work
            post_pr_review,      # review lane: post the review verdict
            merge_pull_request,  # review lane: merge on approve
            update_pr_branch,    # review lane: self-heal a stale branch, then re-merge
            escalate_conflict,   # review lane: hand a real conflict to the owning team
            push_branch,         # resolve lane: push the agent's conflict fix, then re-merge
            read_pr_review_state,  # review lane: read a human "Request Changes" review
            escalate_fix,        # review lane: hand a not-approved PR to the owning team to fix
            escalate_review,     # fix lane: re-review + re-ask the human after a fix
        ],
        # Claude Code chunks are long-running subprocesses; keep concurrency
        # low so one worker doesn't fork-bomb the machine or the rate limits.
        # Tunable because a busy lane head-of-line blocks its own FAST
        # activities (post/merge/push) behind hour-class agent chunks —
        # observed live with 8 queued reviews on concurrency 2.
        max_concurrent_activities=int(os.environ.get("MAX_CONCURRENT_ACTIVITIES", "2")),
        # Persist heartbeat details (incl. the in-flight Claude session id)
        # promptly, so a mid-chunk crash can resume the session instead of
        # restarting from zero. The effective interval is
        # min(heartbeat_timeout * 0.8, max_heartbeat_throttle_interval).
        max_heartbeat_throttle_interval=_HB_THROTTLE,
        default_heartbeat_throttle_interval=_HB_THROTTLE,
    )
    print(
        f'Worker listening on namespace "{namespace}", '
        f'team "{team}", task queue "{task_queue}"'
    )
    print(f"Team folder: teams/{team} (self-sufficient: mandate + skills + policy)")
    await worker.run()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Claude Code Temporal worker")
    parser.add_argument(
        "--namespace",
        default=None,
        help="Temporal namespace (default: the team's own namespace; 'default' for --poller)",
    )
    parser.add_argument(
        "--team",
        default=DEFAULT_TEAM,
        choices=sorted(known_teams()),
        help="Team profile / task queue / skill bundle to host",
    )
    parser.add_argument(
        "--poller",
        action="store_true",
        help="Host the GitHub poll workflow/activity instead of a team lane",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.poller:
        await _run_poller_worker(args.namespace or DEFAULT_NAMESPACE)
    else:
        team = normalize_team(args.team)
        # Default the team worker into its own namespace (override with --namespace).
        await _run_team_worker(args.namespace or namespace_for_team(team), team)


if __name__ == "__main__":
    asyncio.run(main())
