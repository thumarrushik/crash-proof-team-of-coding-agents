#!/usr/bin/env python3
"""Mirror signal (PostToolUse hook) — backend lane.

Studied from the work-issue habit of pushing every step: a commit is not done
until it is off the machine. The agent's env holds no credential and its
`git push` is denied, so this hook cannot push and does not try — it only
leaves a marker when a `git commit` lands. The harness activity, which holds
the worker's own token, watches for the marker and mirrors the work branch to
the remote in its own step. Human-committed in the team folder; stamped into
the workspace before every chunk. The agent never edits it.
"""
import json
import re
import sys


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return
    if event.get("tool_name") != "Bash":
        return
    command = (event.get("tool_input") or {}).get("command", "") or ""
    # A commit anywhere in the call (plain, or chained after `git add`).
    if re.search(r"\bgit\b[^|;&]*\bcommit\b", command):
        try:
            with open(".claude/mirror-request", "w") as marker:
                marker.write("commit\n")
        except OSError:
            pass  # no marker is only a delayed mirror — the chunk-end sweep catches it


if __name__ == "__main__":
    main()
