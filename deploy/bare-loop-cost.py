#!/usr/bin/env python3
"""Measure the bare while-loop baseline: the same Roman task the chunk-cost
experiment used, run as a plain headless `claude -p` — no Temporal, no workspace
skill bundle, no structured-output schema, no resume. This is the "no durability"
row of the strategy table. Run: uv run --with claude-agent-sdk python deploy/bare-loop-cost.py [N]
(the repo's .venv already has claude-agent-sdk; `uv run python deploy/bare-loop-cost.py` works too).
"""
import asyncio
import sys
import tempfile
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage

TASK = (
    "Build a small self-contained Python module `roman.py` with two functions: "
    "`to_roman(n: int) -> str` for 1..3999 and `from_roman(s: str) -> int`, each "
    "raising ValueError on out-of-range or malformed input. Follow strict TDD: write "
    "pytest tests in `test_roman.py` FIRST covering the base symbols, the subtractive "
    "cases (4, 9, 40, 90, 400, 900), several round-trips, and the error cases; run them "
    "and watch them fail; then implement `roman.py` until every test passes. Do not "
    "weaken the tests to fit a wrong implementation. Keep it to these two files."
)


async def one_run() -> tuple[float, int, str]:
    workdir = tempfile.mkdtemp(prefix="bareloop-")
    opts = ClaudeAgentOptions(
        cwd=workdir, model="haiku", max_turns=40,
        permission_mode="acceptEdits",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "TodoWrite"],
        setting_sources=[],   # load NO settings — a truly bare run, no skill bundle
    )
    client = ClaudeSDKClient(options=opts)
    await client.connect()
    try:
        await client.query(TASK)
        async for m in client.receive_response():
            if isinstance(m, ResultMessage):
                return (m.total_cost_usd or 0.0), m.num_turns, m.subtype
        return 0.0, 0, "no-result"
    finally:
        await client.disconnect()


async def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    costs = []
    for i in range(n):
        cost, turns, sub = await one_run()
        print(f"run {i + 1}: ${cost:.4f}  turns={turns}  subtype={sub}", flush=True)
        costs.append(cost)
    print(f"\nbare while-loop: mean=${sum(costs) / len(costs):.4f}  "
          f"range=${min(costs):.4f}-${max(costs):.4f}  (n={len(costs)}, haiku)")


if __name__ == "__main__":
    asyncio.run(main())
