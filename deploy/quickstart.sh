#!/usr/bin/env bash
# START HERE. One command to watch the lead durability claim happen for real:
# kill a worker's whole process tree mid-task and the SAME Claude Code session
# finishes the job on a restarted worker, resumed from its last heartbeat with
# no completed checkpoint. See the flagship article's "Recovering a Crashed Run".
#
#   ./deploy/quickstart.sh
#
# What it does, end to end, with nothing left running afterward:
#   1. starts an ephemeral `temporal server start-dev` on :7233 (if none is up),
#      with the one namespace the demo needs, and tears it down on exit;
#   2. runs deploy/heartbeat-recovery.sh (the SIGKILL-and-resume demo);
#   3. prints recovery-log.jsonl — the one line that proves the resume.
#
# Prerequisites (this demo runs a REAL agent, so it needs real credentials):
#   - `uv`            (https://docs.astral.sh/uv/) — runs the Python with deps
#   - `temporal`      the Temporal CLI (https://docs.temporal.io/cli)
#   - `claude`        the Claude Code CLI, logged in — the agent bills real tokens
#                     (a whole run is ~4 cents on haiku; see the economics companion)
#
# No credentials handy? You can still verify everything offline and for free:
#   uv run --with temporalio python -m unittest discover -s tests
# (hooks, the finish gate, scoring, the team folders, and the workflows on
# Temporal's time-skipping test server — no tokens, no network, no live server.)
set -euo pipefail
cd "$(dirname "$0")/.."

TEAM="${TEAM:-testing}"      # the lane the demo runs on (its own namespace)
MODEL="${MODEL:-haiku}"      # Claude's cheap fast tier — a full run is ~$0.04

say() { printf '\n\033[1m[quickstart]\033[0m %s\n' "$*"; }
port_up() { python3 -c "import socket,sys; s=socket.socket(); s.settimeout(0.3); sys.exit(0 if s.connect_ex(('localhost',7233))==0 else 1)"; }

# --- prereq checks, with actionable messages ------------------------------
missing=0
for tool in uv temporal claude; do
  command -v "$tool" >/dev/null 2>&1 || { echo "  missing: $tool"; missing=1; }
done
if [ "$missing" = 1 ]; then
  cat >&2 <<'MSG'

Install the missing tool(s) above, then re-run. If you only want to confirm the
system is real without spending tokens, run the offline suite instead:
  uv run --with temporalio python -m unittest discover -s tests
MSG
  exit 1
fi
if ! claude --version >/dev/null 2>&1; then
  echo "  the 'claude' CLI is installed but may not be logged in; run 'claude' once to authenticate." >&2
fi

# --- ephemeral Temporal dev server (started only if none is listening) -----
STARTED=""
if ! port_up; then
  say "starting an ephemeral Temporal dev server on :7233 (namespace '$TEAM')"
  temporal server start-dev --headless --log-level error \
    --namespace "$TEAM" \
    --db-filename "${TMPDIR:-/tmp}/quickstart-temporal.db" \
    >"${TMPDIR:-/tmp}/quickstart-devserver.log" 2>&1 &
  STARTED=$!
  trap '[ -n "$STARTED" ] && kill "$STARTED" 2>/dev/null || true' EXIT
  for _ in $(seq 1 60); do port_up && break; sleep 0.25; done
  port_up || { echo "dev server did not come up; see ${TMPDIR:-/tmp}/quickstart-devserver.log" >&2; exit 1; }
else
  say "reusing the Temporal server already listening on :7233"
  # ensure the demo's namespace exists on the borrowed server
  temporal operator namespace describe "$TEAM" >/dev/null 2>&1 \
    || temporal operator namespace create --retention 24h "$TEAM"
fi

# --- the demo: crash mid-task, recover the same session --------------------
say "running the kill -9 recovery demo (this launches a real agent; ~1-3 min)"
TEAM="$TEAM" MODEL="$MODEL" ./deploy/heartbeat-recovery.sh

say "done. If you saw 'heartbeat resume CONFIRMED' above, a SIGKILLed worker's"
say "in-flight session finished as the same session — the last heartbeat was the checkpoint."
