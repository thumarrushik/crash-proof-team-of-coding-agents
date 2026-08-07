#!/usr/bin/env bash
# Pilot: ephemeral Temporal dev server + two lane workers + exactly one issue.
# No poller schedule is created — the other issues are never swept.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="${1:-thumarrushik/linkbox}"
export GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token)}"

temporal server start-dev --headless --log-level warn \
  --namespace backend --namespace review \
  > deploy/pilot-server.log 2>&1 &
SERVER=$!
cleanup() { kill "${WB:-0}" "${WR:-0}" "$SERVER" 2>/dev/null || true; }
trap cleanup EXIT

for _ in $(seq 1 30); do
  temporal operator namespace describe backend >/dev/null 2>&1 && break
  sleep 1
done
temporal operator namespace describe backend >/dev/null 2>&1 || { echo "server not ready"; exit 1; }
echo "dev server up (namespaces: backend, review)"

uv run --with temporalio --with claude-agent-sdk python src/worker.py --team backend \
  > deploy/pilot-worker-backend.log 2>&1 &
WB=$!
uv run --with temporalio --with claude-agent-sdk python src/worker.py --team review \
  > deploy/pilot-worker-review.log 2>&1 &
WR=$!
sleep 3
echo "workers up (backend, review)"

uv run --with temporalio python deploy/pilot-issue1.py "$REPO"
