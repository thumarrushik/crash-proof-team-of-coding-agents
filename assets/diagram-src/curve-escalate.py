#!/usr/bin/env python3
"""Curve the conflict diagram's dashed "Escalate" connection.

D2's grid layout draws the top-right -> bottom-left handoff as a straight
diagonal; this rewrites that one connection's path (identified by its unique
dashed purple stroke #7c3aed) into a gently bowed cubic bezier between the same
endpoints. Robust to layout changes: the control points are derived from the
actual endpoints, not hard-coded. Usage: curve-escalate.py <svg-in-place>
"""
import re
import sys

BOW = 0.05  # perpendicular bow as a fraction of the connection length

def _curve(m: re.Match) -> str:
    x1, y1, x2, y2 = (float(v) for v in m.groups())
    dx, dy = x2 - x1, y2 - y1
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    px, py = -dy / length, dx / length      # unit perpendicular
    if py > 0:                              # bow UPWARD (-y is up): the bottom row
        px, py = -px, -py                   # is dense, so arc into the open band
    off = BOW * length
    c1x, c1y = x1 + dx / 3 + px * off, y1 + dy / 3 + py * off
    c2x, c2y = x1 + 2 * dx / 3 + px * off, y1 + 2 * dy / 3 + py * off
    return (f'd="M {x1:.3f} {y1:.3f} C {c1x:.3f} {c1y:.3f}, '
            f'{c2x:.3f} {c2y:.3f}, {x2:.3f} {y2:.3f}"')

def main() -> None:
    path = sys.argv[1]
    svg = open(path).read()
    # the escalate path is the straight "M x1 y1 L x2 y2" whose tag then carries
    # stroke="#7c3aed" (the dashed handoff). Only that connection is rewritten.
    pat = re.compile(
        r'd="M ([\d.]+) ([\d.]+) L ([\d.]+) ([\d.]+)"(?=[^>]*stroke="#7c3aed")'
    )
    svg, n = pat.subn(_curve, svg)
    open(path, "w").write(svg)
    print(f"  curved {n} escalate connection(s)")

if __name__ == "__main__":
    main()
