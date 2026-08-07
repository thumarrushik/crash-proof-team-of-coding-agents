# SIZE-AND-PASSES — read everything, in bites review can digest

Two obligations pull against each other: you must read every line you were
assigned, and human-calibrated evidence says defect discovery collapses when
a single pass gets too big. Resolve it with passes, never with skimming.

## Read every line

Never scan a hunk and assume it is fine — especially a human-written one,
which carries no generator's regularity. The bugs reviews exist to catch live
in the lines that "look routine": the copy-pasted block with one variable
unrenamed, the inverted guard, the off-by-one in the boring loop. A verdict
covers exactly the lines you actually read; if you did not read a file, you
did not review the PR.

## The evidence on pass size

The SmartBear/Cisco study (2,500 reviews, 3.2M LOC) found:

- A pass of **200-400 changed lines over 60-90 minutes** yields 70-90% defect
  discovery.
- Effectiveness falls off sharply past ~400 lines per pass — reviewers stop
  finding defects, not because the defects thin out, but because attention
  does.
- Inspection rates faster than ~500 LOC/hour show collapsing defect density:
  speed reads as thoroughness but measures as blindness.

Treat these numbers as your operating envelope, not trivia.

## Reviewing a large diff

1. Partition the diff into coherent 200-400 line passes — by subsystem, by
   layer, or by commit if the commits are honest units.
2. Start each pass from the design level (see INSPECTION.md), not from
   line one of the alphabetically first file: read the contract or interface
   changes first, then the implementations against them.
3. Between passes, write down open questions and cross-file suspicions while
   they are fresh; carry them into the next pass instead of trusting recall.
4. Do not average your attention across the whole diff to finish in one
   sitting. A shallow full read is worse than deep passes, because it
   produces the same approval with none of the scrutiny.

## The oversized diff is itself a finding

If a PR arrives so large or so unfocused that no sequence of honest passes
can cover it — mixed concerns, refactors braided with behavior changes,
generated churn burying the real edit — record that as a finding on the PR:
the diff resisted review. An unreviewable change is a process defect even
when every line happens to be correct, because the next one won't be.

Do not silently downgrade your standard to fit the diff. Either the passes
cover everything, or the verdict says they could not.

## Grounding

- SmartBear/Cisco study (2,500 reviews, 3.2M LOC): 200-400 LOC per pass over
  60-90 minutes finds 70-90% of defects; defect density drops past ~500
  LOC/hour.
