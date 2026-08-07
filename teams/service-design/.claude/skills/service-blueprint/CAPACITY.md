# CAPACITY — arithmetic to the first bottleneck (NALSD)

Numbers, not adjectives. "Should scale fine" is a blocked phrase; so are
"fast", "large", and "high volume" standing where a number belongs. The
method is Google's Non-Abstract Large System Design: a design isn't done
until its arithmetic closes, and the arithmetic is deliberately rough —
powers of ten, not benchmarks.

## The method, in order

1. **State the inputs.** Expected request rate (reads and writes
   separately), payload sizes, entity counts, retention. Every number
   carries its source: measured, contracted, or assumed — and assumptions
   are labeled as assumptions.
2. **State the growth assumption.** One line: "2× yearly, re-check at
   10× current". Growth changes which bottleneck arrives first.
3. **Multiply out the derived quantities.** Storage per day/year,
   bandwidth, QPS at peak (peak factor stated — 3× mean is a workable
   default when unmeasured), working-set size, connection counts.
4. **Walk the design's resources until one runs out first.** Compare each
   derived quantity against a rounded capacity constant: what one node,
   one disk, one Postgres, one queue partition handles. The first
   resource to run out is **the bottleneck** — name it explicitly in the
   doc.
5. **Name the metric that shows the bottleneck approaching,** with its
   threshold — the design's tripwire, watched from day one. A bottleneck
   without a metric is a surprise scheduled for later.
6. **Iterate NALSD's four questions:** Is it possible at all? Can we do
   better? Does it survive at 10× scale? Is it resilient when a piece
   fails? If 10× breaks the design, say where — "shard by tenant at
   ~50 req/s sustained" is a design statement, not a failure.

## Worked example — the shape to copy

Audit-log capability: 200 writes/s peak × 1 KB event = 200 KB/s in →
~17 GB/day → ~6 TB/year at current rate; 2× yearly growth assumption →
~18 TB by year two. Single-Postgres comfort for this shape ~ low TB, so
the first bottleneck is **storage, not write QPS** (200 inserts/s is well
inside one node). Response: monthly partitions + 13-month retention caps
live data ~2 TB. Metric: total table size, alert at 70% of provisioned
disk. Reads are rare (compliance pulls): no read replica in v1 — a
non-goal with its reason, back in section 1.

Six sentences of arithmetic; a reviewer can redo every step. That
redo-ability is the falsifiable bar for the whole section.

## Rules of thumb for the arithmetic

- Round aggressively: 86,400 s/day is 10⁵; precision beyond one
  significant figure is fake at design time.
- Compute peak, not mean — services die at peak.
- When a needed constant is unknown, write it as a **named unknown** with
  a measurement plan ("assume 5k inserts/s/node; verify week 1"). An
  admitted gap is a design input; a hidden one is a landmine.
- Do the math per bottleneck candidate: storage, IOPS, bandwidth, QPS,
  memory, connections. The one that runs out first wins the section.

## Grounding

- Non-Abstract Large System Design (NALSD) — sre.google/workbook
