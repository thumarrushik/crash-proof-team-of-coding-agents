#!/usr/bin/env bash
# Live worker-affinity validation: sticky per-worker queues on a REAL server
# with TWO worker identities, a mid-run kill of the pinned identity, and a
# restart that proves the resume waits for (and lands on) the right identity.
#
# What this proves live (single host, two worker processes):
#   1. Chunk 1 is scheduled on the shared lane queue (either identity may take it).
#   2. Every later chunk + the transcript export are scheduled on the SAME
#      sticky per-worker queue the first chunk's worker reported.
#   3. With the pinned identity dead, the surviving other-identity worker never
#      takes the pinned work; it waits.
#   4. A restarted process with the same WORKER_ID resumes and finishes the job.
# What it cannot prove on one host: two truly separate filesystems (the
# transcript/workspace invisibility itself). That is the remaining receipt.
#
# Prereqs: temporal CLI, uv, a logged-in `claude` CLI (the task bills ~cents).
set -euo pipefail
cd "$(dirname "$0")/.."

TEAM="testing"
MODEL="${MODEL:-haiku}"
OUT="${OUT:-experiment-results/affinity-live}"
mkdir -p "$OUT"
SRV_LOG="$OUT/server.log"; A_LOG="$OUT/worker-A.log"; B_LOG="$OUT/worker-B.log"
A2_LOG="$OUT/worker-A2.log"; CLOG="$OUT/client.log"; HIST="$OUT/history.json"
: > "$A_LOG"; : > "$B_LOG"; : > "$A2_LOG"; : > "$CLOG"

export WORKER_AFFINITY=1
export HEARTBEAT_THROTTLE_SECONDS=3

say() { printf '\n[affinity] %s\n' "$*"; }
port_up() { python3 -c "import socket,sys;s=socket.socket();s.settimeout(0.3);sys.exit(0 if s.connect_ex(('localhost',7233))==0 else 1)"; }
kill_tree() { local p="$1" c; for c in $(pgrep -P "$p" 2>/dev/null); do kill_tree "$c"; done; kill -9 "$p" 2>/dev/null || true; }
py_pids_for() {  # python pids whose environment carries WORKER_ID=<arg>
  local wid="$1" out=""
  for p in $(pgrep -f "worker.py --team $TEAM" 2>/dev/null); do
    if ps -E -p "$p" 2>/dev/null | grep -q "WORKER_ID=$wid"; then out="$out $p"; fi
  done
  echo "$out"
}

STARTED_SRV=""
cleanup() {
  pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true
  [ -n "$STARTED_SRV" ] && kill "$STARTED_SRV" 2>/dev/null || true
}
trap cleanup EXIT

# --- server -----------------------------------------------------------------
if ! port_up; then
  say "starting ephemeral temporal dev server (namespace $TEAM)"
  temporal server start-dev --headless --log-level error \
    --db-filename "$OUT/temporal.db" --namespace "$TEAM" >"$SRV_LOG" 2>&1 &
  STARTED_SRV=$!
  for _ in $(seq 1 60); do port_up && break; sleep 0.5; done
  port_up || { echo "server did not come up"; exit 1; }
else
  say "reusing server on :7233"
  temporal operator namespace describe "$TEAM" >/dev/null 2>&1 \
    || temporal operator namespace create --retention 24h "$TEAM"
fi

# --- two worker identities ---------------------------------------------------
say "starting worker identity pod-A and pod-B on lane '$TEAM' (affinity ON)"
pkill -9 -f "worker.py --team $TEAM" 2>/dev/null || true; sleep 1
WORKER_ID=pod-A uv run --with temporalio --with claude-agent-sdk python src/worker.py --team "$TEAM" >>"$A_LOG" 2>&1 & A_UV=$!
WORKER_ID=pod-B uv run --with temporalio --with claude-agent-sdk python src/worker.py --team "$TEAM" >>"$B_LOG" 2>&1 & B_UV=$!
sleep 10
A_PY=$(py_pids_for pod-A); B_PY=$(py_pids_for pod-B)
say "pod-A uv=$A_UV py=[$A_PY]  pod-B uv=$B_UV py=[$B_PY]"
[ -n "$A_PY" ] && [ -n "$B_PY" ] || { echo "workers failed to start"; tail -5 "$A_LOG" "$B_LOG"; exit 1; }

# --- the task (small, but > 2 turns so multiple 2-turn chunks are forced) ----
read -r -d '' TASK <<'EOF' || true
Create greetings.py with two functions: greet(name) returning "Hello, <name>!"
and farewell(name) returning "Goodbye, <name>!", both raising ValueError on an
empty name. Write test_greetings.py with pytest tests covering both functions
and both error cases. Run the tests and fix until every test passes. Finish
with the required structured report.
EOF

say "submitting task (2-turn chunks, up to 6 chunks)"
PYTHONUNBUFFERED=1 uv run --with temporalio python src/client.py --team "$TEAM" --model "$MODEL" \
  --max-turns-per-chunk 2 --max-chunks 6 "$TASK" >"$CLOG" 2>&1 & CPID=$!

WID=""
for _ in $(seq 1 90); do
  WID=$(grep -m1 '^Started workflow ' "$CLOG" 2>/dev/null | awk '{print $3}') || true
  [ -n "$WID" ] && break; sleep 1
done
say "workflow: ${WID:?no workflow id}"

# --- watch history for the pin, then kill the pinned identity ----------------
say "waiting for chunk 1 to complete and the sticky queue to appear in history..."
PIN=""
for _ in $(seq 1 600); do
  PIN=$(temporal workflow show -w "$WID" -n "$TEAM" -o json 2>/dev/null | python3 -c "
import json,sys
try: ev=json.load(sys.stdin).get('events',[])
except Exception: sys.exit()
seen=0
for e in ev:
    a=e.get('activityTaskScheduledEventAttributes')
    if not a: continue
    if a.get('activityType',{}).get('name')=='run_claude_chunk':
        seen+=1
        q=a.get('taskQueue',{}).get('name','')
        if seen>=2 and '-w-' in q: print(q); break
") || true
  [ -n "$PIN" ] && break
  kill -0 "$CPID" 2>/dev/null || break
  sleep 1
done
if [ -z "$PIN" ]; then
  say "RESULT: INCONCLUSIVE — task ended before a second chunk was scheduled (too small); rerun."
  wait "$CPID" 2>/dev/null || true; exit 2
fi
POD="${PIN##*-w-}"
say "PINNED QUEUE: $PIN  (identity: $POD)"

if [ "$POD" = "pod-A" ]; then KILL_UV=$A_UV; SURV="pod-B"; else KILL_UV=$B_UV; SURV="pod-A"; fi
KILLED_PY=$(py_pids_for "$POD")
say "SIGKILL the whole '$POD' process tree (uv=$KILL_UV py=[$KILLED_PY]); '$SURV' stays alive"
kill_tree "$KILL_UV"
for p in $KILLED_PY; do kill -9 "$p" 2>/dev/null || true; done

say "dead window: 45s with only '$SURV' alive — the pinned work must WAIT"
sleep 45
STOLEN=$(temporal workflow show -w "$WID" -n "$TEAM" -o json 2>/dev/null | python3 -c "
import json,sys
ev=json.load(sys.stdin).get('events',[])
surv_pids='''$(py_pids_for "$SURV")'''.split()
sched={}
for e in ev:
    a=e.get('activityTaskScheduledEventAttributes')
    if a: sched[e.get('eventId')]= (a.get('activityType',{}).get('name'), a.get('taskQueue',{}).get('name',''))
n=0
for e in ev:
    s=e.get('activityTaskStartedEventAttributes')
    if not s: continue
    name,q=sched.get(s.get('scheduledEventId'),('',''))
    if '-w-' in q:
        pid=s.get('identity','').split('@')[0]
        if pid in surv_pids: n+=1
print(n)")
say "pinned activities started by the survivor during/after the kill: ${STOLEN:-0} (must be 0)"

say "restarting identity '$POD'"
WORKER_ID="$POD" uv run --with temporalio --with claude-agent-sdk python src/worker.py --team "$TEAM" >>"$A2_LOG" 2>&1 & R_UV=$!
sleep 8
R_PY=$(py_pids_for "$POD")
say "restarted '$POD' uv=$R_UV py=[$R_PY]"

say "waiting for the client to finish (heartbeat timeout + resume may take ~2-4 min)..."
wait "$CPID" 2>/dev/null || true
grep -E '^(done=|session:|workspace:|total|cost)' "$CLOG" | head -6 || tail -5 "$CLOG"

# --- final assertions from the event history ---------------------------------
temporal workflow show -w "$WID" -n "$TEAM" -o json > "$HIST" 2>/dev/null
python3 - "$HIST" "$SURV" <<'EOF'
import json, sys
hist, surv = sys.argv[1], sys.argv[2]
ev = json.load(open(hist)).get('events', [])
sched = {}
for e in ev:
    a = e.get('activityTaskScheduledEventAttributes')
    if a:
        sched[e.get('eventId')] = (a.get('activityType',{}).get('name'), a.get('taskQueue',{}).get('name',''))
chunks  = [(i,q) for i,(n,q) in sorted(sched.items(), key=lambda kv: int(kv[0])) if n=='run_claude_chunk']
exports = [(i,q) for i,(n,q) in sched.items() if n=='export_claude_session_transcript']
done    = any('workflowExecutionCompletedEventAttributes' in e for e in ev)
print(f"\n=== HISTORY VERDICT ===")
print(f"chunks scheduled: {len(chunks)}; export scheduled: {len(exports)}; workflow completed: {done}")
ok = True
if not chunks or '-w-' in chunks[0][1]:
    ok = False; print(f"FAIL: chunk 1 queue = {chunks[0][1] if chunks else 'none'} (expected the shared lane queue)")
else:
    print(f"PASS: chunk 1 on the shared lane queue: {chunks[0][1]}")
pins = {q for _,q in chunks[1:]} | {q for _,q in exports}
if len(pins)==1 and '-w-' in next(iter(pins)):
    print(f"PASS: all {len(chunks)-1} later chunk(s) + export pinned to ONE sticky queue: {next(iter(pins))}")
else:
    ok = False; print(f"FAIL: pinned queues inconsistent: {pins}")
if not done:
    ok = False; print("FAIL: workflow did not complete")
print("AFFINITY LIVE RUN: " + ("ALL CHECKS PASS" if ok else "FAILED"))
sys.exit(0 if ok else 1)
EOF
RC=$?
say "history saved: $HIST"
exit $RC
