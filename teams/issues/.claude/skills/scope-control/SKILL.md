---
name: scope-control
description: Deliver the smallest correct change that fully resolves the issue and nothing else. Use when planning an issue's change and again when self-reviewing the diff.
---

# scope-control

Small diffs are not a style preference: they are reviewed faster, more
thoroughly, and carry fewer bugs — and this lane's diffs face a review gate
that treats out-of-scope changes as findings. The issue defines the blast
radius; stay inside it.

## How to use this skill

1. Read this file when planning an issue's change, and again when
   self-reviewing the diff before the report.
2. Open the topic file for the pressure you are under (below): pinning what
   done means, or resisting what the issue never asked for.

## Topic map (load on demand)

| Task | File |
|---|---|
| Pin the scope contract and close it with a shown check | **[ACCEPTANCE.md](ACCEPTANCE.md)** |
| Refuse presumptive code and drive-by refactors | **[YAGNI.md](YAGNI.md)** |

## The rules in one breath

1. Restate the issue in one sentence before editing, ending with its
   acceptance line: "done when <observable check> passes". Can't write it —
   the issue is ambiguous; flag it instead of guessing.
2. Choose the smallest correct change — correct first, small second. Small
   never means half a fix.
3. Build nothing presumptive: no parameter "for later", no extension point
   with one caller, no generalization the issue does not require.
4. No drive-by refactors — tempting cleanups go in REPORT.md under
   "Noticed, not changed". Sole exception: fix what your change itself makes
   wrong.
5. Close the loop: the acceptance line must map to a test or command output
   shown in your report — otherwise the issue was edited, not resolved.

**Blocked on sight:** diff hunks no sentence in the issue requires · a new
abstraction, parameter, or config key with exactly one user and a "we might
need it" justification · formatting or rename churn mixed into a functional
fix · a report whose acceptance line points at no shown check.
