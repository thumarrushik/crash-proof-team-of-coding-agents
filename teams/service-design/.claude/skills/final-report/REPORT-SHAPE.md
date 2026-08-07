# REPORT-SHAPE.md — the sections, in order

Write REPORT.md at the workspace root with exactly these sections:

```
# Task Report
## What was designed
## How it was verified
## Files
## Noticed, not changed
```

## What was designed

Two to five sentences: the blueprint/contract/ADR decisions and their falsifiable bars. State any assumption you made on an
ambiguous requirement — the assumption is part of the deliverable
(assume-and-note, never stall). No process narration ("first I read the
code..."); outcomes only.

## How it was verified

The evidence section — its rules live in [EVIDENCE.md](EVIDENCE.md).
Minimum content: every command you ran to verify, verbatim, each with its
literal result line. For this lane that means the checks or examples the design ships with.

## Files

A bullet list of every file created or modified, workspace-relative.
The reviewer diffs this list against `git status` — a missing file reads
as concealment, not oversight.

## Noticed, not changed

Cleanups, refactors, or problems you saw and deliberately left — one
line each. This converts scope discipline into triage input for the
humans and keeps every diff line explainable.

## House rules

- Few sentences per section; factual; no filler.
- The report is read by a parser first and a human second: keep the
  headings exact, keep claims one-per-sentence.
- This file is scratch-excluded from the PR (the harness strips it from
  the pushed branch) — write for the workflow, not for the repo history.
