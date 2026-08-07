# REPORT-SHAPE.md — the review report, verdict-first

Write REPORT.md at the workspace root with exactly these sections, in this
order:

```
# Review Report
## Verdict
## Blocking issues
## Non-blocking notes
## Coverage
## Evidence
```

## Verdict

One unambiguous sentence, first thing in the file: **approve** or **block**,
with the single deciding reason named. A workflow and a human both read this
line first; it must stand alone. No hedging ("looks mostly fine"), no
process narration before it.

## Blocking issues

The must-fix list, first because it is what matters. "None." if there are
none. Each blocker:
- **file:line** — where;
- **what is wrong** — the defect, concretely;
- **the consequence** — what breaks, for whom (this is what makes it
  blocking rather than a preference);
- **what fixed looks like**, where you can say it.

A blocker the author cannot act on without asking you a question is not
finished.

## Non-blocking notes

Suggestions and nitpicks, labeled (Conventional Comments: `suggestion`,
`nitpick`, `question`), clearly separated from the blockers. Pre-existing
problems you noticed but that this diff did not introduce go here, never in
the blocker list.

## Coverage

Every file in `git diff main...HEAD --stat`, each either reviewed (and
discussed above) or named here as consciously not reviewed, with why. A
file you never opened and never disclosed is concealment, not brevity.

## Evidence

The exact suite command(s) you ran and the final summary lines
(passed/failed/errored/skipped), run as your last workspace action. This is
what backs `tests_passed` — see [VERDICT.md](VERDICT.md).
