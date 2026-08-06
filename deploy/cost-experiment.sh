#!/usr/bin/env bash
# Controlled chunk-cost experiment — measure what a completed-chunk boundary costs.
#
# The claim under test: durable crash-recovery does NOT require chunking (the
# heartbeat-session path recovers mid-chunk from the on-disk transcript), and
# completed-chunk boundaries are a SEPARATE, optional dial that costs extra
# Claude tokens — a cache-write premium paid on the re-anchored session prefix
# at every resume. To isolate that premium, run the SAME task two ways through
# the real RunClaudeTask workflow:
#
#   coarse : one big chunk    (--max-turns-per-chunk 40, --max-chunks 8)
#   fine   : many small chunks (--max-turns-per-chunk 2,  --max-chunks 30)
#
# Same task, same model, N trials each. The delta in recorded cost — and, from
# the per-chunk usage log the activity already writes, the delta in
# cache_creation (cache-write) tokens — is the boundary tax. Temporal adds zero
# Claude tokens, so this number is identical on a laptop and on a fleet.
#
# Prereqs (real harness, no token/GCP needed — the worker uses your logged-in
# `claude` CLI):
#   docker compose up -d                       # Temporal infra + team namespaces
#   uv run src/worker.py --team backend &      # host worker (local login)
# Then:
#   TRIALS=3 MODEL=haiku ./deploy/cost-experiment.sh
set -euo pipefail
cd "$(dirname "$0")/.."

TEAM="${TEAM:-backend}"
MODEL="${MODEL:-haiku}"
TRIALS="${TRIALS:-3}"
COARSE_TURNS="${COARSE_TURNS:-40}"
COARSE_CHUNKS="${COARSE_CHUNKS:-8}"
FINE_TURNS="${FINE_TURNS:-2}"
FINE_CHUNKS="${FINE_CHUNKS:-30}"
OUT="${OUT:-experiment-results}"

# One fixed, bounded, multi-turn TDD task. Small enough to be cheap; structured
# enough that fine chunking splits it into several completed chunks; identical
# across every run so the only variable is the chunk granularity.
read -r -d '' TASK <<'EOF' || true
Build a small self-contained Python module `roman.py` with two functions:
`to_roman(n: int) -> str` for 1..3999 and `from_roman(s: str) -> int`, each
raising ValueError on out-of-range or malformed input. Follow strict TDD: write
pytest tests in `test_roman.py` FIRST covering the base symbols, the subtractive
cases (4, 9, 40, 90, 400, 900), several round-trips, and the error cases; run
them and watch them fail; then implement `roman.py` until every test passes. Do
not weaken the tests to fit a wrong implementation. Keep it to these two files —
do not scaffold a web service or app. Finish with the required structured report.
EOF

mkdir -p "$OUT/usage" "$OUT/stdout"
RUNS_TSV="$OUT/runs.tsv"
printf 'mode\ttrial\tworkflow_id\tdone\tchunks\tcost_usd\n' > "$RUNS_TSV"

run_one() {  # mode  turns  chunks  trial
  local mode="$1" turns="$2" chunks="$3" trial="$4"
  local log="$OUT/stdout/${mode}-${trial}.log"
  echo ">>> ${mode} trial ${trial}: --max-turns-per-chunk ${turns} --max-chunks ${chunks} --model ${MODEL}"
  uv run src/client.py \
      --team "$TEAM" --model "$MODEL" \
      --max-turns-per-chunk "$turns" --max-chunks "$chunks" \
      "$TASK" | tee "$log"

  local wid done chunks_done cost workspace
  wid=$(grep -m1 '^Started workflow ' "$log" | awk '{print $3}')
  done=$(grep -m1 '^done=' "$log" | sed -E 's/^done=([^ ]+).*/\1/')
  chunks_done=$(grep -m1 '^done=' "$log" | sed -E 's/.*chunks=([0-9]+).*/\1/')
  cost=$(grep -m1 '^done=' "$log" | sed -E 's/.*cost=\$([0-9.]+).*/\1/')
  workspace=$(grep -m1 '^workspace: ' "$log" | sed -E 's/^workspace: //')
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$mode" "$trial" "$wid" "$done" "$chunks_done" "$cost" >> "$RUNS_TSV"

  # Copy this run's per-chunk usage breakdown out of its workspace (the activity
  # wrote it there — same host, so a plain read works).
  if [ -n "$workspace" ] && [ -f "$workspace/usage-log.jsonl" ]; then
    cp "$workspace/usage-log.jsonl" "$OUT/usage/${wid}.jsonl"
  else
    echo "  (no usage-log at ${workspace:-<unknown>})"
  fi
}

for t in $(seq 1 "$TRIALS"); do
  run_one coarse "$COARSE_TURNS" "$COARSE_CHUNKS" "$t"
  run_one fine   "$FINE_TURNS"   "$FINE_CHUNKS"   "$t"
done

echo
echo "=== runs.tsv ==="
cat "$RUNS_TSV"
echo
uv run deploy/cost_report.py "$OUT" --model "$MODEL" || true
