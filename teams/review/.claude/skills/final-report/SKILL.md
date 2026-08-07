---
name: final-report
description: The review lane's REPORT.md — verdict sentence first, blockers before everything, coverage disclosed, tests_passed cited. Use when ending any review run.
---

# final-report (review lane)

Your report is not a builder's changelog; it is a verdict the workflow
parses and an author will act on. Its shape is the review lane's own report
contract — not the builder lanes' what-was-built format — because the review
lane's deliverable is findings plus a merge decision.

## How to use this skill

1. Read this file when the review work is done, before writing REPORT.md.
2. Write the report per **[REPORT-SHAPE.md](REPORT-SHAPE.md)**; set the
   verdict per **[VERDICT.md](VERDICT.md)** — the Verdict rules decide what
   `tests_passed` is allowed to say. The [[verdict-discipline]] and
   [[self-review]] skills are the upstream discipline this report records.

## Topic map (load on demand)

| Task | File |
|---|---|
| The report sections, in order, verdict-first | **[REPORT-SHAPE.md](REPORT-SHAPE.md)** |
| Setting tests_passed and the merge decision from evidence | **[VERDICT.md](VERDICT.md)** |

## The rules in one breath

1. REPORT.md opens with the verdict sentence: approve or block, with the
   deciding reason named. Nothing precedes it.
2. Blocking issues come first — each with file:line, what is wrong, the
   consequence, and where possible what fixed looks like.
3. Non-blocking notes (suggestions, nitpicks) are separated and labeled;
   nitpicks never pad a verdict.
4. Coverage is disclosed: every file of `git diff main...HEAD` is reviewed
   or explicitly named as not reviewed.
5. The Evidence line pastes the exact suite command and its output tail,
   run as your LAST workspace action.
6. `tests_passed` is the literal result of that run; nuance lives in prose,
   never in the boolean.

**Blocked on sight:** a report opening with anything but the verdict ·
blockers below suggestions · a diff file neither reviewed nor disclosed as
unreviewed · `tests_passed` without its Evidence line · a blocker whose
"why" amounts to "I don't like it".
