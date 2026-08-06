#!/usr/bin/env bash
# Regenerate the Medium hero(s) from HTML source via a headless-Chrome screenshot.
# HTML/CSS gives the editorial look (gradients, glow, an SVG motif) that a D2
# box-diagram can't. Output: assets/medium-heroes/<name>.png at 2x (3200x1280).
# Run from anywhere: it cd's to its own directory first.
set -euo pipefail
cd "$(dirname "$0")"
HERODIR="$(pwd)"
OUTDIR="$(cd .. && pwd)/medium-heroes"
mkdir -p "$OUTDIR"

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
if [ ! -x "$CHROME" ]; then
  CHROME="$(command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)"
fi
[ -n "$CHROME" ] || { echo "no Chrome/Chromium found; set \$CHROME"; exit 1; }

for html in *.html; do
  name="${html%.html}"
  out="$OUTDIR/$name.png"
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 --window-size=1600,640 \
    --screenshot="$out" "file://$HERODIR/$html" 2>/dev/null
  echo "  ok  medium-heroes/$name.png"
done
echo "done"
