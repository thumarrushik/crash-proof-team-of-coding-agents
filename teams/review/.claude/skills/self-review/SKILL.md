---
name: self-review
description: Final audit of your own review before submitting — findings, labels, and claims held to the bar you held the diff to. Use when about to write REPORT.md in the review lane.
---

# self-review

Your product is not code — it is findings plus a verdict that triggers or
blocks a merge. This lane cannot edit source, so a sloppy review is your only
way to ship a defect. Audit the review the way you audited the diff.

## How to use this skill

1. Read this file immediately before writing REPORT.md, after the review
   work itself is done.
2. Open the topic file for the step you are on (below): audit the findings
   first, then hold the report to its contract.

## Topic map (load on demand)

| Task | File |
|---|---|
| Audit findings, labels, claimed runs, coverage, and scope | **[AUDITS.md](AUDITS.md)** |
| Write REPORT.md the way the workflow will read it | **[REPORT-CONTRACT.md](REPORT-CONTRACT.md)** |

## The rules in one breath

1. Re-read every blocking finding as the author will — file:line, what is
   wrong, the consequence, and where possible what fixed looks like.
2. Audit severity labels: every blocker merge-stakeable, every nitpick
   genuinely ignorable. Relabel now, not after pushback.
3. For every "I ran X" in the draft, find the actual command in your
   transcript — or run it now, or rewrite the claim as "not verified".
4. The run backing `tests_passed` must be your LAST workspace action; if
   anything came after it, run again.
5. Compare the diff stat against the files your review discusses — a file
   you never opened is an unreviewed file; open it or disclose it.
6. Findings are about this diff; pre-existing problems go in a separated
   non-blocking note, never the blocker list.
7. The report parses, blockers come first, and the verdict sentence is
   unambiguous — approve or block, with the deciding reason named.

**Blocked on sight:** a blocker without file:line, or whose "why" amounts to
"I don't like it" · any claimed run with no matching command in the
transcript · `tests_passed` backed by a run that is not your final workspace
action · diff files neither reviewed nor disclosed as unreviewed.
