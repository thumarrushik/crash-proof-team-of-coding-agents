#!/usr/bin/env bash
# Generate the Medium-paste variant of every article in this directory. Medium
# has no native markdown footnotes, so in-text [^id] citations become unicode
# superscript numbers (adjacent citations comma-joined, e.g. 1,2) and the
# footnote definitions become a plain "## Notes" numbered list at the end.
# Footnotes are numbered by first appearance, so canonical sources may use
# either numeric ([^1]) or named ([^inbox]) footnotes — both come out numbered.
# The canonical *.md files are the source (render-pdf.sh makes the PDFs);
# re-run this after any edit. Skips the generated *-medium.md files.
cd "$(dirname "$0")"
python3 - <<'EOF'
import glob, re

SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
DEF = re.compile(r"^\[\^([A-Za-z0-9_-]+)\]:\s*(.*)$")
REF = re.compile(r"\[\^([A-Za-z0-9_-]+)\]")

for src in sorted(glob.glob("*.md")):
    if src.endswith("-medium.md"):
        continue
    body_lines, defs = [], {}
    for line in open(src).read().split("\n"):
        m = DEF.match(line)
        (defs.__setitem__(m.group(1), m.group(2)) if m else body_lines.append(line))
    body = "\n".join(body_lines).rstrip() + "\n"

    order = []
    for m in REF.finditer(body):
        if m.group(1) not in order:
            order.append(m.group(1))
    assert set(order) == set(defs), f"{src}: ref/def mismatch {set(order) ^ set(defs)}"
    num = {name: i + 1 for i, name in enumerate(order)}

    body = REF.sub(lambda m: f"[^{num[m.group(1)]}]", body)      # names -> numbers
    prev = None                                                  # merge [^1][^2] -> [^1,2]
    while prev != body:
        prev = body
        body = re.sub(r"(\[\^[\d,]+)\]\[\^(\d+\])", r"\1,\2", body)
    body = re.sub(r"\[\^([\d,]+)\]", lambda m: m.group(1).translate(SUP), body)

    if order:
        notes = sorted((num[n], defs[n]) for n in order)
        body += "\n## Notes\n\n" + "\n".join(f"{n}. {t}" for n, t in notes) + "\n"
    assert "[^" not in body, f"{src}: unconverted footnote marker"

    out = src[:-3] + "-medium.md"
    open(out, "w").write(body)
    print(f"ok  {out}: {len(order)} notes")
EOF
