#!/usr/bin/env bash
# Stage one article's medium export for the serialized (one-a-week) release.
#
# Usage: ./stage-release.sh <slug>
#   e.g. ./stage-release.sh a-crash-proof-team-of-coding-agents
#
# Reads published-urls.tsv (slug<TAB>live-url). Cross-article links whose
# target is already live are rewritten to the live URL; links to articles
# not yet published are flattened to plain text. Output lands in
# ../release/<slug>-medium-release.md. Re-run after any canonical edit
# (export-medium.sh first) or after adding a URL to published-urls.tsv.
set -euo pipefail
cd "$(dirname "$0")"

slug="${1:?usage: ./stage-release.sh <slug>}"
python3 - "$slug" <<'PY'
import glob, os, re, sys

slug = sys.argv[1]
src = f"{slug}-medium.md"
if not os.path.exists(src):
    sys.exit(f"no such export: {src} (run ./export-medium.sh first)")

published = {}
if os.path.exists("published-urls.tsv"):
    for line in open("published-urls.tsv"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        s, url = line.split("\t", 1)
        published[s.strip()] = url.strip()

slugs = sorted(f[:-3] for f in glob.glob("*.md") if not f.endswith("-medium.md"))

text = open(src).read()
live, flattened = set(), set()

def rewrite(m):
    label, target = m.group(1), m.group(2)
    if target in published:
        live.add(target)
        return f"[{label}]({published[target]})"
    flattened.add(target)
    return label

pattern = re.compile(
    r"\[([^\]]+)\]\((" + "|".join(re.escape(s) for s in slugs) + r")\.md\)"
)
text = pattern.sub(rewrite, text)

os.makedirs("../release", exist_ok=True)
out = f"../release/{slug}-medium-release.md"
open(out, "w").write(text)

print(f"staged  {out}")
for t in sorted(live):
    print(f"  linked live: {t} -> {published[t]}")
for t in sorted(flattened):
    print(f"  flattened (not yet published): {t}")

# Live posts that mention this article: edit them on Medium once it publishes.
needle = f"({slug}.md)"
for p in sorted(published):
    pm = f"{p}-medium.md"
    if os.path.exists(pm) and needle in open(pm).read():
        print(f"  once this is live: re-stage '{p}' and update its Medium post to link here")
PY
