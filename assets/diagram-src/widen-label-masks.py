#!/usr/bin/env python3
"""Widen D2's edge-label mask holes for the Comic Sans font swap.

D2 hides the connection line behind each edge label by cutting a black rect
"hole" in an SVG mask, sized to the metrics of D2's default font. render.sh
then rewrites the SVG's font-family to Comic Sans MS, which renders wider, so
the label text overflows the hole and the line strikes through its ends.
This widens every black mask rect (the label holes; the mask's base rect is
white) enough to cover the wider glyphs. Usage: widen-label-masks.py <svg-in-place>
"""
import re
import sys

GROW = 0.30   # widen by 30% of the original hole width...
PAD = 8.0     # ...plus a fixed padding, split across both sides

def _widen(m: re.Match) -> str:
    x, w = float(m.group("x")), float(m.group("w"))
    extra = w * GROW + PAD
    return (f'<rect x="{x - extra / 2:.3f}" y={m.group("y")} '
            f'width="{w + extra:.3f}" height={m.group("h")} fill="black">')

def main() -> None:
    path = sys.argv[1]
    svg = open(path).read()
    pat = re.compile(
        r'<rect x="(?P<x>[-\d.]+)" y=(?P<y>"[-\d.]+") '
        r'width="(?P<w>[\d.]+)" height=(?P<h>"[\d.]+") fill="black">'
    )
    svg, n = pat.subn(_widen, svg)
    open(path, "w").write(svg)
    print(f"  widened {n} label mask hole(s)")

if __name__ == "__main__":
    main()
