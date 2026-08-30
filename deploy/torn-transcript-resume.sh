#!/usr/bin/env bash
# Does Claude Code's --resume tolerate a TORN transcript, i.e. the exact damage a
# kill mid-append leaves behind? The transcript is an append-only JSONL file; a
# crash during a write can leave a partial final line. We create a real session
# that memorizes two facts, corrupt its transcript two ways, and resume: does the
# CLI (a) still start, and (b) still remember the facts (context survived)?
#
# No Temporal here: this is a pure Claude Code CLI parser test. Bills a few cents.
set -uo pipefail
MODEL="${MODEL:-haiku}"
WD=$(mktemp -d "${TMPDIR:-/tmp}/torn-transcript.XXXXXX")
cd "$WD"
echo "[tt] workdir: $WD  model: $MODEL"

echo "[tt] === create a session with two memorable facts (no tools) ==="
CREATE=$(claude -p "Please remember two facts for later: my favorite fruit is mango, and my lucky number is 47. Acknowledge in one short sentence. Do not use any tools." \
  --model "$MODEL" --output-format json 2>"$WD/create.err")
SID=$(printf '%s' "$CREATE" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('session_id',''))" 2>/dev/null || true)
echo "[tt] session_id: ${SID:-<none>}"
[ -n "$SID" ] || { echo "[tt] FAIL: no session id"; sed 's/^/   /' "$WD/create.err" | head; exit 1; }

T=$(find "$HOME/.claude/projects" -name "$SID.jsonl" 2>/dev/null | head -1)
[ -n "${T:-}" ] || { echo "[tt] FAIL: transcript not found for $SID"; exit 1; }
cp "$T" "$WD/original.jsonl"
echo "[tt] transcript: $T  ($(wc -l < "$T" | tr -d ' ') lines, $(wc -c < "$T" | tr -d ' ') bytes)"
echo "[tt] last 1 line, tail 80 chars:"; tail -c 80 "$T" | sed 's/^/       /'

# Sanity: a CLEAN resume must remember the facts, or the test proves nothing.
probe() {  # $1=label ; corrupted transcript already at $T
  local label="$1" out rc
  out=$(cd "$WD" && claude -p "Without using any tools, answer in one short sentence: what is my favorite fruit and my lucky number?" \
    --resume "$SID" --model "$MODEL" --output-format json 2>"$WD/resume-$label.err"); rc=$?
  echo "[tt] --- resume [$label]: exit=$rc ---"
  if [ $rc -eq 0 ]; then
    printf '%s' "$out" | python3 -c "
import sys,json
d=json.load(sys.stdin)
r=(d.get('result') or '')
low=r.lower()
print('[tt]   is_error :', d.get('is_error'))
print('[tt]   result   :', r[:160].replace(chr(10),' '))
print('[tt]   remembers: mango=%s  47=%s' % ('mango' in low, '47' in low))
" 2>/dev/null || echo "[tt]   (unparseable output): $(printf '%s' "$out" | head -c 160)"
  else
    echo "[tt]   RESUME ERRORED:"; sed 's/^/         /' "$WD/resume-$label.err" | head -8
  fi
}

echo; echo "[tt] === baseline: clean resume (control) ==="
probe "0-clean"
cp "$WD/original.jsonl" "$T"   # resume may have appended; restore

echo; echo "[tt] === variant A: torn last line (truncate mid final line, no newline) ==="
python3 - "$WD/original.jsonl" "$T" <<'PY'
import sys
data=open(sys.argv[1],'rb').read()
nl=data.rstrip(b'\n').rfind(b'\n')          # start of last non-empty line
last=data[nl+1:].rstrip(b'\n')
keep=max(1,len(last)//2)
open(sys.argv[2],'wb').write(data[:nl+1]+last[:keep])   # half a JSON line, no newline
print(f"[tt]   tore final line: kept {keep}/{len(last)} bytes, no newline/close")
PY
tail -c 60 "$T" | sed 's/^/       torn-tail> /'
probe "A-truncated"
cp "$WD/original.jsonl" "$T"

echo; echo "[tt] === variant B: complete transcript + an appended partial fragment ==="
python3 - "$T" <<'PY'
import sys
frag=b'{"type":"assistant","uuid":"partial","message":{"role":"assistant","content":[{"type":"text","text":"this entry was cut sh'
open(sys.argv[1],'ab').write(frag)          # unterminated new line after a valid file
print(f"[tt]   appended {len(frag)}-byte partial fragment, no newline/close")
PY
probe "B-appended-partial"
cp "$WD/original.jsonl" "$T"

echo; echo "[tt] restored original transcript. workdir: $WD"
