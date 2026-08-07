"""Operator CLI for human gates: the approval inbox and the decision, codified.

The workflow side (workflows.py) models the human with four Temporal
primitives: a QUERY exposes what the run is blocked on, an UPDATE (with a
validator) records the decision attributably or rejects it before it enters
history, WAIT_CONDITION + a TIMER hold the gate open with a deny-safe
deadline. This CLI is the human's half of that contract:

    # what is waiting on me? (the inbox)
    uv run approvals.py --list [--namespace review]

    # decide, attributably
    uv run approvals.py --approve <workflow-id> --by rushik [--note "LGTM"]
    uv run approvals.py --reject  <workflow-id> --by rushik --note "not yet"

A decision on a workflow with no open gate is REJECTED by the update
validator server-side — you cannot approve something that isn't asking.
"""

import argparse
import asyncio
import sys

from temporalio.client import Client
from temporalio.service import RPCError

from shared import ApprovalDecision, TEMPORAL_ADDRESS

WORKFLOW_TYPE = "RunClaudeTask"


async def list_pending(namespace: str) -> int:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)
    pending = 0
    async for wf in client.list_workflows(
        f"WorkflowType = '{WORKFLOW_TYPE}' AND ExecutionStatus = 'Running'"
    ):
        handle = client.get_workflow_handle(wf.id)
        try:
            gate = await handle.query("get_pending_approval")
        except Exception:
            continue
        if gate:
            pending += 1
            print(f"{wf.id}\n  action: {gate.get('action')}  "
                  f"detail: {gate.get('detail')}  "
                  f"deadline: {gate.get('timeout_h')}h")
    if not pending:
        print(f"no gates waiting in namespace '{namespace}'")
    return pending


async def decide(namespace: str, workflow_id: str, approved: bool,
                 by: str, note: str) -> None:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=namespace)
    handle = client.get_workflow_handle(workflow_id)
    decision = ApprovalDecision(approved=approved, decided_by=by, note=note)
    # An update can transiently race a workflow task and come back
    # WorkflowNotReadyFailure ("Workflow Task in failed state"); that is a
    # retryable "try again in a moment", not a rejection by the validator.
    # A real rejection (no gate open, missing attribution) raises
    # WorkflowUpdateFailedError, which we do NOT retry — it is the answer.
    for attempt in range(6):
        try:
            print(await handle.execute_update("decide", decision))
            return
        except RPCError as e:
            if "Workflow Task in failed state" in str(e) and attempt < 5:
                await asyncio.sleep(0.5)
                continue
            raise


async def main() -> None:
    parser = argparse.ArgumentParser(description="Human gates: inbox + decisions")
    parser.add_argument("--namespace", default="review",
                        help="Lane to inspect (merges gate in the review lane)")
    parser.add_argument("--list", action="store_true", help="Show open gates")
    parser.add_argument("--approve", metavar="WORKFLOW_ID")
    parser.add_argument("--reject", metavar="WORKFLOW_ID")
    parser.add_argument("--by", default="", help="Who is deciding (required to decide)")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    if args.list:
        sys.exit((await list_pending(args.namespace), 0)[1])
    target = args.approve or args.reject
    if not target:
        parser.error("pass --list, --approve <id>, or --reject <id>")
    if not args.by:
        parser.error("--by is required: decisions are attributable")
    await decide(args.namespace, target, bool(args.approve), args.by, args.note)


if __name__ == "__main__":
    asyncio.run(main())
