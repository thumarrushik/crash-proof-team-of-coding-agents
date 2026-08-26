#!/usr/bin/env bash
# The receipt still owed: MACHINE loss, not process loss.
#
# Two "machines" are simulated as disjoint workspace roots on one box: each
# worker gets its own TMPDIR (the harness derives workspaces from it). The
# transcript store keys projects by workspace path, so machine A's transcript
# lives in its own project dir. Worker A runs the chunk; mid-chunk its whole
# process tree is SIGKILLed and NEVER restarted. A one-shot copy to a staging
# dir plays the role of shared storage: A's workspace and A's transcript
# project are staged, then BOTH originals are deleted (A's workspace root and
# A's transcript project dir): machine A's disk is gone. The staged copies are
# restored at machine B's paths (the transcript project renamed to B's cwd
# slug, as a shared mount at B's path would present it). Worker B starts,
# Temporal retries after the heartbeat timeout, and the retry must resume the
# SAME session from the id in the dead attempt's last heartbeat. (A dying
# straggler of the killed tree can flush one last file to A's recreated path
# moments after the rm; B never reads it - the staged copy predates it - so
# the checks assert B's provenance, not A's emptiness.) (Auth is not
# part of the claim: a real machine B is provisioned with its own login, so
# both workers share this box's credentials.)
#
# Prereq: `temporal` CLI, `uv`, a logged-in `claude` CLI. Starts an ephemeral
# dev server on :7233 if none is up (namespace = the demo lane). Bills real
# tokens (a small TDD task on haiku, roughly $0.05-0.20).
set -euo pipefail
cd "$(dirname "$0")/.."
TEAM="${TEAM:-testing}"
MODEL="${MODEL:-haiku}"
OUT="${OUT:-experiment-results/machine-loss}"
export HEARTBEAT_THROTTLE_SECONDS="${HEARTBEAT_THROTTLE_SECONDS:-3}"
FLUSH_MARGIN="${FLUSH_MARGIN:-5}"
A_ROOT="/tmp/ml-machine-A"
B_ROOT="/tmp/ml-machine-B"
mkdir -p "$OUT"; WLOG_A="$OUT/worker-A.log"; WLOG_B="$OUT/worker-B.log"; CLOG="$OUT/client.log"
: > "$WLOG_A"; : > "$WLOG_B"; : > "$CLOG"

say() { echo "[ml] $*"; }
kill_tree() { local pid="$1" c; for c in $(pgrep -P "$pid" 2>/dev/null); do kill_tree "$c"; done; kill -9 "$pid" 2>/dev/null || true; }

# --- server (borrow :7233 if up, else ephemeral) ---
port_up() { nc -z 127.0.0.1 7233 >/dev/null 2>&1; }
STARTED_SERVER=0
if ! port_up; then
  say "starting ephemeral Temporal dev server on :7233 (namespace '$TEAM')"
  temporal server start-dev --headless --log-level error --namespace "$TEAM" \
    >"$OUT/devserver.log" 2>&1 &
  SERVER_PID=$!; STARTED_SERVER=1
  for _ in $(seq 1 30); do port_up && break; sleep 1; done
  port_up || { echo "dev server did not come up" >&2; exit 1; }
else
  temporal operator namespace describe "$TEAM" >/dev/null 2>&1 \
    || temporal operator namespace create --retention 24h "$TEAM"
fi
cleanup() {
  pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true
  [ "$STARTED_SERVER" = 1 ] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# --- machine roots: fresh ---
SHARED="/tmp/ml-shared-storage"
rm -rf "$A_ROOT" "$B_ROOT" "$SHARED"
mkdir -p "$A_ROOT/tmp" "$B_ROOT/tmp" "$SHARED"

start_worker() { # $1 = root, $2 = log
  TMPDIR="$1/tmp" uv run src/worker.py --team "$TEAM" >>"$2" 2>&1 & echo $!
}
slug() { echo "$1" | sed 's/[^A-Za-z0-9]/-/g'; }

say "machine A comes up (workspaces under $A_ROOT/tmp; its transcript project will be deleted with it)"
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true; sleep 2
APID=$(start_worker "$A_ROOT" "$WLOG_A"); say "worker A pid=$APID"; sleep 8

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

say "start task"
PYTHONUNBUFFERED=1 uv run src/client.py --team "$TEAM" --model "$MODEL" \
  --max-turns-per-chunk 40 --max-chunks 8 "$TASK" >"$CLOG" 2>&1 &
CPID=$!

WID=""
for _ in $(seq 1 60); do
  WID=$(grep -m1 '^Started workflow ' "$CLOG" 2>/dev/null | awk '{print $3}') || true
  [ -n "$WID" ] && break; sleep 1
done
say "workflow: ${WID:-<none>}"; [ -n "$WID" ] || { echo "no workflow started" >&2; exit 1; }
A_WS="$A_ROOT/tmp/temporal-claude/$WID"
B_WS="$B_ROOT/tmp/temporal-claude/$WID"

say "waiting until the agent is mid-work on A (audit log records tool calls)..."
for _ in $(seq 1 120); do
  N=$(wc -l < "$A_WS/usage-log.jsonl" 2>/dev/null || echo 0)
  [ "${N:-0}" -ge 2 ] && { say "agent is mid-work on A ($N tool calls logged)"; break; }
  grep -q '^done=' "$CLOG" && { say "WARNING: task finished before the crash"; break; }
  sleep 1
done
say "flush margin ${FLUSH_MARGIN}s, then machine A dies"
sleep "$FLUSH_MARGIN"

say "=== SIGKILL machine A's whole worker tree; A is NEVER restarted ==="
kill_tree "$APID"
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true

say "=== shared storage: stage A's workspace + transcript project ==="
SLUG_A=$(slug "/private$A_WS")
SLUG_B=$(slug "/private$B_WS")
A_TR="$HOME/.claude/projects/$SLUG_A"
B_TR="$HOME/.claude/projects/$SLUG_B"
[ -d "$A_TR" ] || A_TR="$HOME/.claude/projects/$(slug "$A_WS")"   # non-macOS: no /private
rsync -a "$A_WS/" "$SHARED/workspace/"
rsync -a "$A_TR/" "$SHARED/transcript/"

say "=== machine A's disk is deleted: workspace root AND its transcript project ==="
rm -rf "$A_ROOT" "$A_TR"

say "=== restore from shared storage at machine B's paths ==="
mkdir -p "$B_WS" "$B_TR"
rsync -a "$SHARED/workspace/" "$B_WS/"
rsync -a "$SHARED/transcript/" "$B_TR/"

say "machine B comes up (has NEVER seen A's filesystem)"
BPID=$(start_worker "$B_ROOT" "$WLOG_B"); say "worker B pid=$BPID"

say "waiting for recovery + completion (~2m heartbeat timeout + resume on B)..."
wait "$CPID" 2>/dev/null || true

say "=== client result ==="
grep -E '^(Started workflow|done=|session:|workspace:)' "$CLOG" || tail -6 "$CLOG"

PASS=0; FAIL=0
check() { if eval "$2"; then say "  [PASS] $1"; PASS=$((PASS+1)); else say "  [FAIL] $1"; FAIL=$((FAIL+1)); fi; }
check "task completed"                     "grep -q '^done=True' '$CLOG'"
check "completed on machine B's workspace" "grep -q '^workspace: /tmp/ml-machine-B' '$CLOG'"
check "machine A transcript project gone"  "[ ! -e \"$A_TR\" ]"
check "recovery log exists on machine B"   "[ -f '$B_WS/recovery-log.jsonl' ]"
check "retry resumed from heartbeat id"    "grep -q 'resume_session_from_heartbeat' '$B_WS/recovery-log.jsonl' 2>/dev/null"
check "input session id was null"          "grep -q '\"input_session_id\": null' '$B_WS/recovery-log.jsonl' 2>/dev/null"
SES=$(grep -m1 '^session:' "$CLOG" | awk '{print $2}') || true
check "same session finished"              "grep -q \"$SES\" '$B_WS/recovery-log.jsonl' 2>/dev/null"

say "=== recovery-log.jsonl (machine B) ==="
cat "$B_WS/recovery-log.jsonl" 2>/dev/null | tee "$OUT/recovery-log.jsonl" || true
say "$PASS passed, $FAIL failed"
[ "$FAIL" = 0 ] && say "RESULT: MACHINE-LOSS RESUME CONFIRMED (two filesystems, A deleted)" || say "RESULT: NOT confirmed"
[ "$FAIL" = 0 ]
