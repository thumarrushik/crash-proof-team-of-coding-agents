# REPORT-CONTRACT — write the report the way the workflow will read it

REPORT.md is not prose for a patient human. It is parsed by the workflow to
decide a merge, skimmed by the author for what to fix first, and audited
later against your transcript. Write for those three readers, in that order.

## The workflow reads structure

- The structured output must parse. A malformed report does not degrade
  gracefully — it either stalls the pipeline or gets misread as a verdict
  you did not intend.
- `tests_passed` must match the cited run exactly: the boolean, the command,
  and the output tail all agree, and the run is your last workspace action.
  A report whose prose says "one failure, environmental" while the boolean
  says true is lying to the machine in the field the machine reads.
- Every field the report contract defines is present. Empty sections are
  stated as empty ("no blocking findings"), never omitted — an absent
  section is indistinguishable from a forgotten one.

## The author reads order

- **Blockers first**, each complete per AUDITS.md step 1 — the author's fix
  loop starts at line one of the report, so line one carries the highest-
  stakes finding.
- Suggestions and nitpicks after, clearly labeled non-blocking, so nothing
  polish-shaped interrupts the path to a mergeable state.
- Pre-existing issues (outside this diff) in their own separated note at
  the end, explicitly marked as not part of the verdict.

## The verdict sentence

One sentence, unambiguous, near the top: **approve or block, with the
deciding reason named.**

- "Block: unvalidated upload path reaches the filesystem (handlers.py:41)."
- "Approve: behavior change is pinned by tests and the suite is green."

Not "mostly fine with some concerns", not "approve once the issues are
addressed" (that is a block), not a verdict the reader must infer from the
tone of the findings. If you cannot name the deciding reason in one
sentence, the review is not finished — go back to AUDITS.md.

## Coverage disclosure belongs in the report

The report states what was reviewed and what was not: files consciously
cleared, files disclosed as unreviewed with reasons, suites run and suites
"not verified". This is the report-side surface of AUDITS.md steps 3-4 —
the disclosure is worthless if it lives only in your head or your
transcript.

## Final pass before submitting

1. Parse check: structure valid, all fields present.
2. Consistency check: boolean matches evidence line matches transcript.
3. Order check: verdict sentence up top, blockers first, non-blocking
   material labeled, pre-existing notes separated.
4. Read it once cold, as the author: is the first action to take obvious?

## Grounding

- This repo's 3/10 tests_passed misreport finding: the boolean-evidence
  consistency check exists because the field was measurably wrong when
  unchecked.
- Conventional Comments: labels and decorations carry severity through the
  report unambiguously.
