#!/usr/bin/env bash
# Live human-gate demo on a REAL Temporal server. Starts an ephemeral
# `temporal server start-dev` (in-memory, headless) if one isn't already
# listening on :7233, runs the orchestrator, then tears the server down.
# No tokens, no GitHub: the agent chunk and the merge are stubbed; everything
# else (workflow, query, validated update, durable wait + deadline timer, the
# operator CLI, the event history) runs for real. Evidence -> hitl-live-results.md
set -euo pipefail
cd "$(dirname "$0")/.."

port_up() { python3 -c "import socket,sys; s=socket.socket(); s.settimeout(0.3); sys.exit(0 if s.connect_ex(('localhost',7233))==0 else 1)"; }

STARTED=""
if ! port_up; then
  command -v temporal >/dev/null || { echo "temporal CLI not found; install it or start a server on :7233"; exit 1; }
  echo "starting ephemeral temporal dev server on :7233 ..."
  temporal server start-dev --headless --log-level error \
    --dynamic-config-value frontend.enableUpdateWorkflowExecution=true \
    --dynamic-config-value frontend.enableUpdateWorkflowExecutionAsyncAccepted=true \
    >/tmp/hitl-devserver.log 2>&1 &
  STARTED=$!
  trap '[ -n "$STARTED" ] && kill "$STARTED" 2>/dev/null || true' EXIT
  for _ in $(seq 1 60); do port_up && break; sleep 0.25; done
  port_up || { echo "dev server did not come up; see /tmp/hitl-devserver.log"; exit 1; }
fi

uv run --with temporalio python deploy/hitl-live.py "$@"
