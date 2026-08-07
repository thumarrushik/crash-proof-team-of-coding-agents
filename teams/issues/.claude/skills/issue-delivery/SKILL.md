---
name: issue-delivery
description: The issues lane's end-to-end playbook from reading the issue to the structured report that ends the run. Use when working any issue in this workspace.
---

# issue-delivery

This workspace is owned by a Temporal workflow: the harness stamps governance,
owns git (never `git push` — it is denied), and reads your structured report
as data. Your run ends at a clean working tree plus REPORT.md; the harness
commits, opens the PR, and a review agent whose verdict gates the merge will
re-derive every claim you make. Deliver accordingly.

## How to use this skill

1. Read this file at the start of every issue, before touching any code.
2. Open the topic file for what you need (below): the step-by-step playbook,
   or the contract with the harness that owns this workspace.

## Topic map (load on demand)

| Task | File |
|---|---|
| Work the issue end to end: the seven steps in order | **[PLAYBOOK.md](PLAYBOOK.md)** |
| What the harness owns, denies, and reads from your run | **[HARNESS-CONTRACT.md](HARNESS-CONTRACT.md)** |

## The rules in one breath

1. Understand first: read the issue in full, locate the real code, establish
   what "done" observably means — never pattern-match the title.
2. Bug-shaped: repro-first before any fix. Feature-shaped: find the
   insertion point; the surrounding code is the spec.
3. Plan the smallest correct change (scope-control); implement test-first
   (tdd); no placeholders, no TODOs, no stubs.
4. Test all layers, once, at the end — every suite the repo ships — and make
   that green run your last workspace action; the review lane checks
   exactly this.
5. Self-review the final diff: only intended files, edges probed, no scratch
   files, debug prints, or secrets.
6. Report, then stop: REPORT.md with the acceptance line mapped to its shown
   check, `tests_passed` set to the literal final-run result. No commits, no
   pushes, no PRs — the harness performs those.

**Blocked on sight:** any `git push`, or manual commit/PR plumbing the
harness owns · editing before the issue's code was located and read ·
declaring done with an unrun suite, or `tests_passed` set from memory · work
continuing after REPORT.md, or a report the harness cannot parse.
