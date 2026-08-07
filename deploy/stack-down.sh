#!/usr/bin/env bash
# Explicit teardown for the stack: the ONLY place workers and the dev server die.
set -uo pipefail
pkill -f "worker.py --team" 2>/dev/null || true
pkill -f "worker.py --poller" 2>/dev/null || true
pkill -f "temporal server start-dev" 2>/dev/null || true
echo "stack down"
