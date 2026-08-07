#!/usr/bin/env bash
# Regenerate every diagram in assets/diagrams/ from its committed source.
# Two source types live side by side in this directory:
#   *.d2    : compiled with d2, font-swapped to the hand-drawn look, and
#             rasterized by rsvg-convert to a FIXED WIDTH (CANVAS_W px) with
#             natural height, so the set shares one column width without
#             letterboxed whitespace. D2 embeds fonts under generated names
#             rsvg-convert can't resolve, so the SVG's font-family is rewritten
#             to a name fontconfig knows. widen-label-masks.py re-cuts D2's
#             edge-label mask holes for the wider font; curve-escalate.py is a
#             conflict.d2-only path tweak.
#   *.html  : screenshot by headless Chrome at 2x, sizes per-file below.
# The cost figure is separate: uv run --with matplotlib python assets/plot-src/plots.py
# (run from the repo root). Requires: d2, rsvg-convert, python3, Chrome.
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(cd ../diagrams && pwd)"
rc=0

# --- D2 sources ---
THEME="${THEME:-0}"           # 0 = light "paper"; 200 = dark
CANVAS_W="${CANVAS_W:-1600}"  # every D2 diagram is exported exactly CANVAS_W px wide
BG="${BG:-white}"             # background (Medium is light)
FONT_FAMILY="${FONT_FAMILY:-Comic Sans MS}"  # matches matplotlib xkcd fallback
for f in *.d2; do
  [ -e "$f" ] || continue
  name="${f%.d2}"
  out="$OUT/$name.png"
  if d2 --theme "$THEME" --pad 40 "$f" "/tmp/$name.svg" 2>"/tmp/$name.err" \
     && sed -E "s/font-family:[^;}]*/font-family:\"$FONT_FAMILY\"/g" "/tmp/$name.svg" > "/tmp/$name.font.svg" \
     && python3 widen-label-masks.py "/tmp/$name.font.svg" \
     && { [ "$name" != conflict ] || python3 curve-escalate.py "/tmp/$name.font.svg"; } \
     && rsvg-convert -w "$CANVAS_W" -b "$BG" "/tmp/$name.font.svg" -o "$out"; then
    echo "  ok  diagrams/$name.png"
  else
    echo "  FAIL $f"; sed 's/^/       /' "/tmp/$name.err"; rc=1
  fi
done

# --- HTML sources ---
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
size() { case "$1" in chunk-exits) echo 1400,760;; fix-loop) echo 1400,800;; *) echo 1400,800;; esac; }
for html in *.html; do
  [ -e "$html" ] || continue
  name="${html%.html}"
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 --window-size="$(size "$name")" \
    --screenshot="$OUT/$name.png" "file://$(pwd)/$html" 2>/dev/null
  echo "  ok  diagrams/$name.png"
done
exit $rc
