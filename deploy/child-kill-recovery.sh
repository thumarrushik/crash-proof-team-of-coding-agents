#!/usr/bin/env bash
# Contrast experiment to heartbeat-recovery.sh: kill ONLY the Claude child
# process mid-chunk and leave the worker ALIVE. Question under test: when the
# agent subprocess dies but its worker does not, how does the run recover, and
# from where does the resumed session id come?
#
# Prediction (to be confirmed or refuted): the SDK sees the CLI die, the activity
# raises a retryable error, Temporal retries it fast (5s backoff, no 2-minute
# heartbeat-timeout wait), and the retry resumes the SAME session from the id in
# heartbeat details — the same recovery path as a worker crash, just triggered by
# a fast activity failure instead of a slow liveness timeout. If instead the SDK
# hangs, the dumb 30s timer keeps heartbeating "alive" and only the 15-minute
# chunk ceiling would catch it (a very different, and notable, outcome).
#
# Prereq: a Temporal server on :7233 with the TEAM namespace (default 'testing')
# and a logged-in `claude` CLI. Same rig as heartbeat-recovery.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
TEAM="${TEAM:-testing}"
MODEL="${MODEL:-haiku}"
OUT="${OUT:-experiment-results/child-kill}"
export HEARTBEAT_THROTTLE_SECONDS="${HEARTBEAT_THROTTLE_SECONDS:-3}"
FLUSH_MARGIN="${FLUSH_MARGIN:-8}"     # seconds after first file-write before the kill
RECOVER_WAIT="${RECOVER_WAIT:-240}"   # cap on how long we watch for recovery
mkdir -p "$OUT"; WLOG="$OUT/worker.log"; CLOG="$OUT/client.log"; : > "$WLOG"; : > "$CLOG"
WORK_ROOT="${TMPDIR:-/tmp}/temporal-claude"

descendants() { local p="$1" c; for c in $(pgrep -P "$p" 2>/dev/null); do echo "$c"; descendants "$c"; done; }
start_worker() { uv run src/worker.py --team "$TEAM" >>"$WLOG" 2>&1 & echo $!; }

# Kill only the Claude CLI subtree beneath the worker; never the worker itself.
kill_claude_child() {
  local root="$1" pid cmd killed=0
  echo "[ck] worker process tree before the kill:"
  for pid in "$root" $(descendants "$root"); do
    printf '      %s  %s\n' "$pid" "$(ps -o command= -p "$pid" 2>/dev/null | cut -c1-90)"
  done
  for pid in $(descendants "$root"); do
    cmd=$(ps -o command= -p "$pid" 2>/dev/null || true)
    case "$cmd" in
      *worker.py*) : ;;                       # never the worker/uv/python
      *claude*)                               # the Claude CLI (node) child
        for gc in $(descendants "$pid"); do kill -9 "$gc" 2>/dev/null || true; done
        kill -9 "$pid" 2>/dev/null || true
        echo "[ck] KILLED claude child pid=$pid :: $(echo "$cmd" | cut -c1-90)"
        killed=1 ;;
    esac
  done
  [ "$killed" = 1 ] || echo "[ck] WARNING: no claude child found to kill (nothing matched)"
}

echo "[ck] fresh worker on lane '$TEAM' (heartbeat throttle=${HEARTBEAT_THROTTLE_SECONDS}s)"
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true; sleep 2
WPID=$(start_worker); echo "[ck] worker pid=$WPID"; sleep 8

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

echo "[ck] start task in background"
PYTHONUNBUFFERED=1 uv run src/client.py --team "$TEAM" --model "$MODEL" \
  --max-turns-per-chunk 40 --max-chunks 8 "$TASK" >"$CLOG" 2>&1 &
CPID=$!

echo "[ck] waiting for workflow id..."
WID=""
for _ in $(seq 1 60); do
  WID=$(grep -m1 '^Started workflow ' "$CLOG" 2>/dev/null | awk '{print $3}') || true
  [ -n "$WID" ] && break; sleep 1
done
echo "[ck] workflow: ${WID:-<none>}"
WS="$WORK_ROOT/$WID"

echo "[ck] waiting until the agent starts writing (session live + heartbeated)..."
for _ in $(seq 1 120); do
  ls "$WS"/*.py >/dev/null 2>&1 && { echo "[ck] agent is writing — mid-chunk"; break; }
  grep -q '^done=' "$CLOG" && { echo "[ck] WARNING: task finished before we could kill it"; break; }
  sleep 1
done
echo "[ck] flush margin ${FLUSH_MARGIN}s (persist the session id), then kill the CHILD only..."
sleep "$FLUSH_MARGIN"

KILL_TS=$(date +%s)
echo "[ck] === KILL ONLY THE CLAUDE CHILD (worker stays alive) @ $(date +%T) ==="
kill_claude_child "$WPID"

# Assert the worker survived the kill.
if kill -0 "$WPID" 2>/dev/null; then echo "[ck] worker pid=$WPID STILL ALIVE after the child kill (as intended)"
else echo "[ck] UNEXPECTED: worker pid=$WPID died"; fi

echo "[ck] watching for recovery (cap ${RECOVER_WAIT}s); NOT restarting the worker..."
DONE=""; RECOVER_TS=""
for _ in $(seq 1 "$RECOVER_WAIT"); do
  if [ -z "$RECOVER_TS" ] && [ -f "$WS/recovery-log.jsonl" ]; then
    RECOVER_TS=$(date +%s); echo "[ck] recovery-log.jsonl appeared @ $(date +%T) (+$((RECOVER_TS-KILL_TS))s)"
  fi
  if grep -q '^done=' "$CLOG"; then DONE=1; break; fi
  sleep 1
done
END_TS=$(date +%s)

echo "[ck] === client result ==="
grep -E '^(Started workflow|done=|session:|workspace:)' "$CLOG" || tail -6 "$CLOG"
WS2=$(grep -m1 '^workspace: ' "$CLOG" | sed -E 's/^workspace: //') || true; WS2="${WS2:-$WS}"

echo "[ck] === recovery evidence ==="
if [ -f "$WS2/recovery-log.jsonl" ]; then
  cat "$WS2/recovery-log.jsonl"; cp "$WS2/recovery-log.jsonl" "$OUT/recovery-log.jsonl"
fi
echo "[ck] worker.log retry/exception trail:"
grep -niE "attempt|retry|resume|error|Claude Code (API|error)|activity" "$WLOG" | tail -20 || true

echo "[ck] --- summary ---"
if kill -0 "$WPID" 2>/dev/null; then echo "[ck] worker survived: pid=$WPID unchanged (never restarted)"; fi
[ -n "$RECOVER_TS" ] && echo "[ck] time kill -> recovery-log: $((RECOVER_TS-KILL_TS))s"
if [ -n "$DONE" ]; then echo "[ck] task COMPLETED $((END_TS-KILL_TS))s after the child kill"
else echo "[ck] task NOT done within ${RECOVER_WAIT}s (possible SDK-hang / ceiling path — investigate)"; fi

kill "$CPID" 2>/dev/null || true
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true
echo "[ck] done"
