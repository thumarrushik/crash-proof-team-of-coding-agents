#!/usr/bin/env bash
# Render the final article(s) in this directory to a print-quality PDF (same
# pipeline as ../render-pdf.sh: pandoc gfm with tex_math_dollars OFF so dollar
# amounts never parse as TeX, print-styled page, headless-Chrome print-to-pdf).
# Figures resolve from ../../assets via absolute file:// paths. Run from anywhere.
cd "$(dirname "$0")"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
if [ ! -x "$CHROME" ]; then
  CHROME="$(command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)"
fi
[ -n "$CHROME" ] || { echo "no Chrome/Chromium found; set \$CHROME"; exit 1; }
ASSETS="file://$(cd ../../assets && pwd)"
rc=0
for md in *.md; do
  case "$md" in *-medium.md) continue;; esac  # Medium paste variant: no PDF needed
  name="${md%.md}"
  page="/tmp/final-$name.print.html"
  {
    cat <<'HTML'
<!doctype html><html><head><meta charset="utf-8"><style>
body{font-family:Georgia,'Times New Roman',serif;line-height:1.55;font-size:11.5pt;color:#1a1a1a;max-width:100%;margin:0}
h1{font-size:22pt;line-height:1.25;margin:0 0 6pt}
h2{font-size:15pt;margin:18pt 0 6pt}
h3{font-size:12pt;font-weight:normal;font-style:italic;color:#444;margin:4pt 0 10pt}
img{max-width:100%;display:block;margin:10pt auto}
figure,p:has(> img){page-break-inside:avoid}
em{color:#333}
table{border-collapse:collapse;font-size:10pt;margin:8pt 0}
td,th{border:1px solid #bbb;padding:4pt 8pt;text-align:left}
code{font-family:Menlo,monospace;font-size:9.5pt;background:#f4f4f4;padding:0 2pt}
pre{background:#f6f6f6;padding:8pt;font-size:9pt;overflow-x:hidden;white-space:pre-wrap;page-break-inside:avoid;border:1px solid #ddd}
pre code{background:none}
hr{border:none;border-top:1px solid #ccc;margin:14pt 0}
blockquote{margin:0 0 0 12pt;color:#555}
.footnotes{font-size:9pt;color:#444}
a{color:#1a4fa0;text-decoration:none}
li{margin-bottom:3pt}
</style></head><body>
HTML
    pandoc "$md" -f gfm-tex_math_dollars -t html | sed "s|src=\"../../assets/|src=\"$ASSETS/|g"
    echo '</body></html>'
  } > "$page"
  if "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
       --virtual-time-budget=15000 --print-to-pdf="$name.pdf" "file://$page" 2>/dev/null \
     && [ -s "$name.pdf" ]; then
    echo "  ok  articles/final/$name.pdf ($(du -h "$name.pdf" | cut -f1 | tr -d '[:space:]'))"
  else
    echo "  FAIL $md"; rc=1
  fi
done
echo done; exit $rc
