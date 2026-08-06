#!/usr/bin/env bash
# Operator-local bootstrap (macOS): build .env from the Claude Code login already
# in your Keychain, so the Dockerized workers get CLAUDE_CODE_OAUTH_TOKEN without
# a separate `claude setup-token`. GITHUB_TOKEN comes from the gh CLI.
#
# Run it in YOUR interactive session so the Keychain approval dialog appears:
#   ! ./deploy/env-from-keychain.sh
# Click "Always Allow" when macOS asks about the "Claude Code-credentials" key.
#
# Prints only a masked confirmation — the token is never echoed. .env is gitignored.
set -euo pipefail
cd "$(dirname "$0")/.."

security find-generic-password -w -s "Claude Code-credentials" -a "$(whoami)" 2>/dev/null \
| GH_TOKEN_VAL="$(gh auth token 2>/dev/null || true)" python3 - <<'PY'
import json, os, re, sys
raw = sys.stdin.buffer.read().decode("utf-8", "replace").strip()
if not raw:
    sys.exit("EMPTY_READ: approve the Keychain dialog (click 'Always Allow') and re-run.")
if re.fullmatch(r"[0-9A-Fa-f]+", raw) and len(raw) % 2 == 0:      # security -w prints hex for binary
    raw = bytes.fromhex(raw).decode("utf-8", "replace").strip()
tok = None
try:
    data = json.loads(raw)
    def find(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and v.startswith("sk-ant") and "access" in k.lower(): return v
                r = find(v)
                if r: return r
        elif isinstance(o, list):
            for v in o:
                r = find(v)
                if r: return r
    tok = find(data)
except json.JSONDecodeError:
    pass
if not tok:
    m = re.search(r"sk-ant-[A-Za-z0-9_-]+", raw); tok = m.group(0) if m else None
if not tok:
    sys.exit(f"NO_TOKEN: keychain blob had no sk-ant token (len={len(raw)}, first3={raw[:3]!r}).")
gh = os.environ.get("GH_TOKEN_VAL", "")
open(".env", "w").write(f"CLAUDE_CODE_OAUTH_TOKEN={tok}\n" + (f"GITHUB_TOKEN={gh}\n" if gh else ""))
os.chmod(".env", 0o600)
print(f"OK wrote .env: CLAUDE_CODE_OAUTH_TOKEN={tok[:14]}…{tok[-4:]} (len {len(tok)}); "
      f"GITHUB_TOKEN={'set' if gh else 'MISSING (set it manually if you need GitHub ops)'}")
PY
