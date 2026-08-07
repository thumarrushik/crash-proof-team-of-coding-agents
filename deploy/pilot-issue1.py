#!/usr/bin/env python3
"""Pilot: run exactly ONE issue through the real system, end to end.

Stage 1  issue #1 -> owning lane's durable job -> Claude Code builds -> PR
Stage 2  the new PR -> review lane's durable job -> verdict -> merge
Stage 3  verify on GitHub: PR merged, code on main

Uses only production paths (plan/submit/workflow), constrained to one issue —
the poller schedule is never created, so the other issues stay untouched.

Usage: uv run --with temporalio python deploy/pilot-issue1.py [owner/repo]
"""
import asyncio
import dataclasses
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import poller  # noqa: E402
from shared import namespace_for_team  # noqa: E402

REPO = sys.argv[1] if len(sys.argv) > 1 else "thumarrushik/linkbox"
ISSUE_SOURCE = "issue-1"


async def wait_result(client, workflow_id: str):
    handle = client.get_workflow_handle(workflow_id)
    return await handle.result()


async def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("set GITHUB_TOKEN"); return 1

    print(f"== stage 1: build {ISSUE_SOURCE} ==")
    _, _, activities = poller.plan(REPO, token)
    build = next((a for a in activities if a.source == ISSUE_SOURCE), None)
    if build is None:
        print(f"no plan for {ISSUE_SOURCE} (already closed?)"); return 1
    if not build.ready:
        print(f"{ISSUE_SOURCE} blocked by {build.blocked_by}"); return 1
    client = await poller._connect(namespace_for_team(build.team))
    await poller.submit(client, build, repo=REPO, model=None, dry_run=False)
    result = await wait_result(client, poller.workflow_id_for(build))
    print(f"build result: {dataclasses.asdict(result) if dataclasses.is_dataclass(result) else result}")

    print("== stage 2: review the PR ==")
    review = None
    for _ in range(24):  # PR appears right after the build workflow completes
        _, _, activities = poller.plan(REPO, token)
        review = next((a for a in activities
                       if a.source.startswith("pr-")
                       and getattr(a, "head_ref", "") == f"claude/{ISSUE_SOURCE}"),
                      None)
        if review is not None:
            break
        await asyncio.sleep(5)
    if review is None:
        print("no reviewable PR found for the build"); return 1
    rclient = await poller._connect(namespace_for_team(review.team))
    await poller.submit(rclient, review, repo=REPO, model=None, dry_run=False)
    rresult = await wait_result(rclient, poller.workflow_id_for(review))
    print(f"review result: {dataclasses.asdict(rresult) if dataclasses.is_dataclass(rresult) else rresult}")

    print("== stage 3: verify on GitHub ==")
    pr_number = int(review.source.split("-")[1])
    pr = poller._gh_get(f"/repos/{REPO}/pulls/{pr_number}", token)
    merged = bool(pr.get("merged")) if isinstance(pr, dict) else False
    print(f"PR #{pr_number} merged: {merged}")
    tree = poller._gh_get(f"/repos/{REPO}/git/trees/main?recursive=1", token)
    files = [t["path"] for t in tree.get("tree", []) if t["type"] == "blob"] if isinstance(tree, dict) else []
    code = [f for f in files if f.endswith(".py")]
    print(f"files on main: {len(files)}; python files: {code}")
    ok = merged and code
    print("PILOT PASS" if ok else "PILOT FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
