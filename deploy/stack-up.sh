#!/usr/bin/env bash
# Full stack on the ephemeral dev server: every lane namespace, a worker per
# lane, the poller worker, and the Schedule that KEEPS POLLING the app repo —
# issues in, durable jobs out, continuously. Idempotent where possible: safe
# to run when the server (and some workers) are already up.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="${1:-thumarrushik/linkbox}"
INTERVAL="${2:-60}"
export GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token)}"

# --fresh: restart all workers so they pick up code changes. Learned live:
# a policy fix in poller.py did nothing until the running worker restarted.
if [ "${3:-}" = "--fresh" ] || [ "${1:-}" = "--fresh" ]; then
  pkill -f "worker.py --team" 2>/dev/null || true
  pkill -f "worker.py --poller" 2>/dev/null || true
  sleep 2
  echo "workers stopped (--fresh): restarting with current code"
fi

# Server: reuse a running one, else start fresh (all namespaces declared).
if ! temporal operator namespace describe default >/dev/null 2>&1; then
  temporal server start-dev --headless --log-level warn \
    --db-filename deploy/temporal-dev.db \
    --namespace backend --namespace frontend --namespace testing \
    --namespace review --namespace issues --namespace service-design \
    > deploy/stack-server.log 2>&1 &
  for _ in $(seq 1 30); do
    temporal operator namespace describe default >/dev/null 2>&1 && break
    sleep 1
  done
fi

# Namespaces: create any that are missing (dev server allows live creation).
for ns in backend frontend testing review issues service-design; do
  temporal operator namespace describe "$ns" >/dev/null 2>&1 \
    || temporal operator namespace create --retention 24h "$ns"
done
echo "namespaces ready"

# One worker per lane + the poller worker (skip lanes already being served).
for team in backend frontend testing review issues service-design; do
  if ! pgrep -f "worker.py --team $team" >/dev/null 2>&1; then
    uv run --with temporalio --with claude-agent-sdk python src/worker.py --team "$team" \
      > "deploy/stack-worker-$team.log" 2>&1 &
    echo "worker up: $team"
  else
    echo "worker already running: $team"
  fi
done
if ! pgrep -f "worker.py --poller" >/dev/null 2>&1; then
  uv run --with temporalio --with claude-agent-sdk python src/worker.py --poller \
    > deploy/stack-worker-poller.log 2>&1 &
  echo "worker up: poller"
fi
sleep 3

# The polling activity, on a Temporal Schedule: the system now WATCHES the repo.
uv run --with temporalio python src/poller.py --repo "$REPO" \
  --schedule --interval "$INTERVAL" || true
echo "stack up: schedule polls $REPO every ${INTERVAL}s"
