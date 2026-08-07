---
name: final-report
description: The review lane's REPORT.md shape — verdict sentence first, blockers before everything, coverage disclosed, tests_passed cited. Use when ending any review run.
---

# final-report (review lane)

Your report is not a builder's changelog; it is a verdict the workflow
parses and an author will act on. Its shape is the review lane's own
report contract (see [[self-review]] REPORT-CONTRACT.md) — not the
builder lanes' what-was-built format.

Write REPORT.md with exactly these sections:

```
# Review Report
## Verdict            <- one unambiguous sentence: approve or block,
                         with the deciding reason named
## Blocking issues    <- first, or "None." Each: file:line, what is
                         wrong, the consequence, what fixed looks like
## Non-blocking notes <- suggestions and nitpicks, labeled, ignorable
## Coverage           <- every diff file reviewed or disclosed as not
## Evidence           <- the exact suite command + output tail backing
                         tests_passed, run as your LAST workspace action
```

Then return the structured output the harness requires: `summary` opens
with the verdict sentence; `tests_passed` is the literal result of the
Evidence run ([[verdict-discipline]]), never an impression.

**Blocked on sight:** a report opening with anything but the verdict ·
blockers below suggestions · a diff file neither reviewed nor disclosed ·
`tests_passed` without its Evidence line.
