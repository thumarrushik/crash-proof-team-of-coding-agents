---
name: final-report
description: The service-design lane's REPORT.md — what was designed, how it was verified with exact commands, every file accounted for. Use when ending any run in this lane.
---

# final-report (service-design lane)

The report is not a courtesy; it is data. The harness parses your
structured output, and a review agent re-derives every claim you make —
so the report's only job is to be checkable.

## How to use this skill

1. Read this file when the work is done and verified, before writing
   anything.
2. Write REPORT.md per **[REPORT-SHAPE.md](REPORT-SHAPE.md)**, then state
   your verification per **[EVIDENCE.md](EVIDENCE.md)** — the Evidence
   rules decide what `tests_passed` is allowed to say.

## Topic map (load on demand)

| Task | File |
|---|---|
| The sections, in order, and what each must contain | **[REPORT-SHAPE.md](REPORT-SHAPE.md)** |
| Stating verification: exact commands, output tails, the last-run rule | **[EVIDENCE.md](EVIDENCE.md)** |

## The rules in one breath

1. REPORT.md at the workspace root, exactly the shape in REPORT-SHAPE.md.
2. Factual, few sentences per section, no filler; the blueprint/contract/ADR decisions and their falsifiable bars.
3. The verification section names the exact command(s) and their literal
   result — run after your final edit, never from memory.
4. `tests_passed` in the structured output is the literal result of that
   final run; anything unrun is written as "not verified", never inferred.
5. Every created or modified file listed; anything you noticed but did
   not change goes under "Noticed, not changed".

**Blocked on sight:** a report with no exact command in its verification
section · `tests_passed` set from memory or from an earlier run · a
modified file missing from the Files list · filler prose standing where a
fact should be.
