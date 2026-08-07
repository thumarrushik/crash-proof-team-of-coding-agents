#!/usr/bin/env python3
"""Hand-drawn (xkcd) cost figure, from the FULL measured experiment.
Regenerate: uv run --with matplotlib python assets/plot-src/plots.py

Data: deploy/full-experiment.py -> deploy/full-experiment-results.md (haiku, all
observed, run sequentially). Two honest panels:
  A) a crash/resume is a cheap cache-READ (cents), not a re-run;
  B) fine chunking's cost is unpredictable: a tight turn cap can send the agent
     into many more chunks, and cost balloons with boundary count (measured $0.03 ->
     $2.13 across 1 -> 14 chunks, ~63x; the worst run ~19x the continuous base).
     Coarse-by-default is about predictability,
     not a per-boundary cache tax (that stays cheap at ~$0.0035/boundary).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "assets/diagrams"
INDIGO, GREEN, RED, PURPLE = "#4f46e5", "#16a34a", "#dc2626", "#7c3aed"

# --- measured (deploy/full-experiment-results.md) ---
CONT = [0.0582, 0.1320, 0.1493]          # continuous, 3-9 turns
C = sum(CONT) / len(CONT)                 # ~0.113
R_WARM = 0.00354                          # warm boundary (cache-read), mean of 5
R_COLD = 0.0206                           # cold first-touch after 65 min (partial cache-write)
CHUNKED = [(1, 0.0344), (8, 0.2496), (14, 2.1250)]   # (chunks, total cost)


def figure():
    with plt.xkcd():
        # 12.8 x 5.6 in at dpi 125 = 1600 x 700 px: matches the diagrams' fixed
        # 1600px width (assets/diagram-src/render.sh) with a natural landscape
        # height, so the figure set shares a width without forced whitespace.
        fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.8, 5.6))

        # Panel A: an interrupted+resumed run is the BASE plus a few cents, so its
        # bar sits slightly ABOVE the continuous bar (the resume is a small cap on top).
        labels = ["Continuous\nrun", "Interrupted +\nwarm resume", "Interrupted +\ncold resume"]
        adds = [0.0, R_WARM, R_COLD]
        cap_colors = [INDIGO, GREEN, RED]
        x = list(range(len(labels)))
        axA.bar(x, [C, C, C], color=INDIGO, edgecolor="#334155", linewidth=1.5, zorder=3)
        axA.bar(x, adds, bottom=[C, C, C], color=cap_colors, edgecolor="#334155", linewidth=1.5, zorder=4)
        axA.set_xticks(x); axA.set_xticklabels(labels)
        for i, a in enumerate(adds):
            axA.text(i, C + a + 0.004, f"${C + a:.3f}", ha="center", va="bottom", fontsize=11)
        # Aim arrows at the LEFT side of each bar's cap so the arrowhead clears
        # the centered $value label sitting on top of the bar.
        axA.annotate("+$0.0035 warm\n(cache-read, 0.1×)", xy=(0.7, C + R_WARM), xytext=(0.4, 0.178),
                     ha="center", fontsize=9.5, color=GREEN, arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.6))
        axA.annotate("+$0.021 cold\n(partial write)", xy=(1.7, C + R_COLD - 0.004), xytext=(1.45, 0.202),
                     ha="center", fontsize=9.5, color=RED, arrowprops=dict(arrowstyle="->", color=RED, lw=1.6))
        axA.set_ylabel("cost (USD)")
        axA.set_ylim(0, 0.23)
        axA.set_title("An interrupted run = the base\nplus a few cents to resume")
        axA.spines[["top", "right"]].set_visible(False)

        # Panel B: fine chunking ADDS cost over the continuous base, unpredictably.
        base = sum(CONT) / len(CONT)
        xs = [c for c, _ in CHUNKED]
        ys = [d for _, d in CHUNKED]
        axB.axhline(base, color=INDIGO, lw=2, ls="--", zorder=1)
        axB.text(0.2, base * 0.66, f"continuous base ~${base:.2f}", fontsize=9, color=INDIGO)
        axB.plot(xs, ys, color=PURPLE, lw=2, zorder=2)
        axB.scatter(xs, ys, s=120, color=PURPLE, edgecolors="#334155", linewidths=1.5, zorder=3)
        for c, d in CHUNKED:
            # Match the article's number precision exactly: the sub-$0.10 value keeps
            # 3 decimals ($0.034, not $0.03); larger values round to cents with a nudge
            # so $2.125 -> $2.13 (not matplotlib's float-repr $2.12).
            # Escape the dollar signs: a label with a PAIR of "$" (e.g. "$0.25 (+$0.14)")
            # triggers matplotlib mathtext, which eats both signs; "\$" renders literally.
            money = f"\\${d:.3f}" if d < 0.1 else f"\\${d + 5e-4:.2f}"
            lbl = money + (f"  (+\\${d - base:.2f})" if d - base > 0.05 else "")
            axB.text(c, d * 1.5, lbl, ha="center", fontsize=10, color=PURPLE)
        # No "→" here: the xkcd/Comic Sans font has no glyph for it (renders as tofu).
        axB.annotate("14 chunks / 28 turns to finish\nwhat one session did in 9 turns\n+$2.0 over the base",
                     xy=(14, 2.125), xytext=(4.3, 0.85), fontsize=9.5, color=RED,
                     arrowprops=dict(arrowstyle="->", color=RED, lw=1.8))
        axB.set_yscale("log")
        axB.set_xlabel("chunks the agent took (fine chunking)")
        axB.set_ylabel("run cost (USD, log)")
        axB.set_xticks([1, 8, 14])
        axB.set_xlim(0, 16)
        axB.set_title("Fine chunking adds cost,\nunpredictably (+\\$0 to +\\$2)")
        axB.spines[["top", "right"]].set_visible(False)

        fig.suptitle("Same TDD task, haiku, measured: a resume is cheap; fine chunking is unpredictable",
                     fontsize=13)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(f"{OUT}/cost-comparison.png", dpi=125)  # 12.8*125 x 8*125 = 1600x1000
        plt.close(fig)
        print(f"  {OUT}/cost-comparison.png")
        print(f"  C=${C:.4f}  R_warm=${R_WARM:.5f}  R_cold=${R_COLD:.4f}  "
              f"chunked {CHUNKED[0][1]:.3f}->{CHUNKED[-1][1]:.3f} over {CHUNKED[0][0]}->{CHUNKED[-1][0]} chunks")


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    figure()
    print("plots rendered")
