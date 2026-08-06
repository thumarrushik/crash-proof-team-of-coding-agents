#!/usr/bin/env bash
# Fresh demonstration: failure -> heartbeat -> resume.
#
# Kill the worker's WHOLE PROCESS TREE mid-chunk (so the Claude child can't
# orphan-finish the work and mask the test), and show the retry resumes the SAME
# Claude session from the id carried in Temporal heartbeat details
# (recovery-log.jsonl records the resume). This is the lead durability claim:
# crash recovery needs no completed checkpoint — the heartbeat IS the checkpoint.
#
# Timing is driven by a real signal, not a guess: wait until the agent starts
# writing files (session live + heartbeated), add a short flush margin, then
# crash. Runs on a dedicated lane so it never disturbs other workers.
# Prereq: docker compose up -d (Temporal infra + namespaces).
set -euo pipefail
cd "$(dirname "$0")/.."
TEAM="${TEAM:-testing}"
MODEL="${MODEL:-haiku}"
OUT="${OUT:-experiment-results/heartbeat}"
# Record heartbeat details promptly so the in-flight session id is persisted
# before the crash (Temporal's default effective throttle is ~60s). See worker.py.
export HEARTBEAT_THROTTLE_SECONDS="${HEARTBEAT_THROTTLE_SECONDS:-3}"
FLUSH_MARGIN="${FLUSH_MARGIN:-8}"   # seconds after first file-write before the crash
mkdir -p "$OUT"; WLOG="$OUT/worker.log"; CLOG="$OUT/client.log"; : > "$WLOG"; : > "$CLOG"
WORK_ROOT="${TMPDIR:-/tmp}/temporal-claude"

kill_tree() {  # kill a pid and all descendants (uv -> python -> claude)
  local pid="$1" child
  for child in $(pgrep -P "$pid" 2>/dev/null); do kill_tree "$child"; done
  kill -9 "$pid" 2>/dev/null || true
}
start_worker() { uv run src/worker.py --team "$TEAM" >>"$WLOG" 2>&1 & echo $!; }

echo "[hb] fresh worker on lane '$TEAM' (heartbeat throttle=${HEARTBEAT_THROTTLE_SECONDS}s)"
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true; sleep 2
WPID=$(start_worker); echo "[hb] worker pid=$WPID"; sleep 8

read -r -d '' TASK <<'EOF' || true
Build a self-contained Python module `mathkit.py` with functions: add, subtract,
multiply, divide (ValueError on divide-by-zero), power, modulo (ValueError on
mod-by-zero), gcd, lcm, is_prime, and factorial (ValueError on negatives).
Follow strict TDD: FIRST write `test_mathkit.py` with pytest tests covering each
function including its error cases and several edge cases (at least ~20 test
cases total); run them and watch them fail; THEN implement `mathkit.py` until
every test passes. Do not weaken the tests. Keep it to these two files. Finish
with the required structured report.
EOF

echo "[hb] start task in background"
# PYTHONUNBUFFERED so 'Started workflow' hits the log immediately (block-buffered
# stdout would hide it until process exit, breaking the mid-chunk timing).
PYTHONUNBUFFERED=1 uv run src/client.py --team "$TEAM" --model "$MODEL" \
  --max-turns-per-chunk 40 --max-chunks 8 "$TASK" >"$CLOG" 2>&1 &
CPID=$!

echo "[hb] waiting for workflow id..."
WID=""
for _ in $(seq 1 60); do
  WID=$(grep -m1 '^Started workflow ' "$CLOG" 2>/dev/null | awk '{print $3}') || true
  [ -n "$WID" ] && break; sleep 1
done
echo "[hb] workflow: ${WID:-<none>}"
WS="$WORK_ROOT/$WID"

echo "[hb] waiting until the agent starts writing in the workspace (session live + heartbeated)..."
for _ in $(seq 1 120); do
  ls "$WS"/*.py >/dev/null 2>&1 && { echo "[hb] agent is writing — mid-chunk"; break; }
  grep -q '^done=' "$CLOG" && { echo "[hb] WARNING: task finished before we could crash it"; break; }
  sleep 1
done
echo "[hb] flush margin ${FLUSH_MARGIN}s (persist the session id), then crash..."
sleep "$FLUSH_MARGIN"

echo "[hb] === SIGKILL the worker PROCESS TREE mid-chunk (no orphan) ==="
kill_tree "$WPID"
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true

echo "[hb] restart worker; Temporal retries after the heartbeat timeout"
WPID2=$(start_worker); echo "[hb] restarted worker pid=$WPID2"

echo "[hb] waiting for recovery + completion (~2m heartbeat timeout + resume)..."
wait "$CPID" 2>/dev/null || true

echo "[hb] === client result ==="
grep -E '^(Started workflow|done=|session:|workspace:)' "$CLOG" || tail -6 "$CLOG"
WS2=$(grep -m1 '^workspace: ' "$CLOG" | sed -E 's/^workspace: //') || true; WS2="${WS2:-$WS}"
echo "[hb] === recovery-log.jsonl (heartbeat-resume evidence) ==="
if [ -f "$WS2/recovery-log.jsonl" ]; then
  cat "$WS2/recovery-log.jsonl"; cp "$WS2/recovery-log.jsonl" "$OUT/recovery-log.jsonl"
  echo "[hb] RESULT: heartbeat resume CONFIRMED"
else
  echo "[hb] RESULT: no recovery-log — heartbeat_session_id was empty on the retry."
fi
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true
echo "[hb] done"
