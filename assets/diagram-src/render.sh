#!/usr/bin/env bash
# Render diagram-src HTMLs to assets/diagrams/ via headless Chrome.
# Sizes are per-file: chunk-exits 1400x760, fix-loop 1400x800.
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(cd ../diagrams && pwd)"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
size() { case "$1" in chunk-exits) echo 1400,760;; fix-loop) echo 1400,800;; *) echo 1400,800;; esac; }
for html in *.html; do
  name="${html%.html}"
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 --window-size="$(size "$name")" \
    --screenshot="$OUT/$name.png" "file://$(pwd)/$html" 2>/dev/null
  echo "  ok  diagrams/$name.png"
done
