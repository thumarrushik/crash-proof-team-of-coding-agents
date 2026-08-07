---
name: repro-first
description: Reproduce and minimize a reported bug before touching code, then freeze the repro as a failing test. Use when working any bug-shaped issue, before planning a fix.
---

# repro-first

A fix without a reproduction is a guess with a commit message. Stack
Overflow's bar for even *asking* about a bug is a minimal reproducible
example; the bar for fixing one is not lower.

## How to use this skill

1. Read this file when picking up any bug-shaped issue, before reading the
   suspect code.
2. Open the topic file for the phase you are in (below): reproduce and
   minimize, freeze, or the honest exit when the bug won't show.

## Topic map (load on demand)

| Task | File |
|---|---|
| Reproduce exactly, then minimize to the smallest failing repro | **[MRE.md](MRE.md)** |
| Freeze the repro as a failing test, then open the fix loop | **[FREEZE.md](FREEZE.md)** |
| Can't reproduce — the trail deliverable, and the missing-feature trap | **[NOT-REPRODUCIBLE.md](NOT-REPRODUCIBLE.md)** |

## The rules in one breath

1. Reproduce exactly, first: run the issue's own steps in this workspace and
   record command plus observed wrong behavior verbatim, before reading the
   suspect code.
2. Minimize: shrink input, steps, and components, re-running after each cut
   and keeping only cuts that preserve the failure. Complete and minimal —
   and readable beats short.
3. Freeze the repro as a failing test in the repo's suite; watch it fail for
   the reported reason, not a setup error. That test is the acceptance line.
4. Only then open the fix loop (tdd skill): smallest change that greens the
   frozen test, then the full suite.
5. If you cannot reproduce, the trail is the deliverable — commands,
   environment, observations, hypothesis. Never ship a code change for a
   failure you never saw.
6. If the code the bug describes does not exist, the issue is blocked on the
   feature that ships it — report the missing module and stop. Never build
   the feature to have something to fix.

**Blocked on sight:** a code edit before any recorded reproduction attempt ·
a "fix" for a bug never observed failing in this workspace · a repro test
that passes before the fix, or fails for a setup reason · "could not
reproduce" with no command trail behind it · building the missing feature to
have something to fix.
