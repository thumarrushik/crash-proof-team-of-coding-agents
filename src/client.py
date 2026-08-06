"""Start a Claude Code task as a Temporal workflow and wait for the result."""

import argparse
import asyncio
import time
from pathlib import Path

from temporalio.client import Client

from shared import DEFAULT_TEAM, TEAM_PROFILES, TEMPORAL_ADDRESS, TaskInput, namespace_for_team, normalize_team, task_queue_for_team
from workflows import RunClaudeTask


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Claude Code task durably via Temporal")
    parser.add_argument("task", nargs="?", help="The task for Claude Code")
    parser.add_argument(
        "--task-file",
        help="Read the task prompt from a Markdown file, e.g. an exported GitHub issue body",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Temporal namespace (default: the team's own namespace)",
    )
    parser.add_argument(
        "--team",
        default=DEFAULT_TEAM,
        choices=sorted(TEAM_PROFILES),
        help="Team profile / task queue / skill bundle to use",
    )
    parser.add_argument("--max-chunks", type=int, default=8, help="Resume-chunks before giving up (default 8)")
    parser.add_argument(
        "--max-turns-per-chunk", type=int, default=40,
        help="Agentic turns per completed activity chunk (default 40)",
    )
    parser.add_argument(
        "--model", default=None,
        help="Model alias/ID for the agent (e.g. sonnet, opus, fable); default = Claude Code's default",
    )
    args = parser.parse_args()

    if args.task_file:
        task = Path(args.task_file).read_text()
    elif args.task:
        task = args.task
    else:
        parser.error("provide a task argument or --task-file")

    team = normalize_team(args.team)
    task_queue = task_queue_for_team(team)
    namespace = args.namespace or namespace_for_team(team)
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)
    workflow_id = f"claude-{team}-task-{int(time.time())}"
    handle = await client.start_workflow(
        RunClaudeTask.run,
        TaskInput(
            task=task,
            team=team,
            max_chunks=args.max_chunks,
            max_turns_per_chunk=args.max_turns_per_chunk,
            model=args.model,
        ),
        id=workflow_id,
        task_queue=task_queue,
    )
    print(f"Started workflow {workflow_id}")
    print(f"namespace:  {namespace}")
    print(f"team:       {team}")
    print(f"task queue: {task_queue}")
    print(f"Watch it: http://localhost:8233/namespaces/{namespace}/workflows/{workflow_id}")

    result = await handle.result()
    print("\n=== Result ===")
    print(result.result_text)
    if result.report:
        print("\n=== Structured report ===")
        import json
        print(json.dumps(result.report, indent=2))
    print(f"\ndone={result.done} team={result.team} chunks={result.chunks} cost=${result.total_cost_usd:.4f}")
    print(f"session:   {result.session_id}")
    print(f"workspace: {result.work_dir}")


if __name__ == "__main__":
    asyncio.run(main())
