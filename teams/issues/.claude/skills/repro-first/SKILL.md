---
name: repro-first
description: Reproduce and minimize a reported bug before touching code, then freeze the repro as a failing test. Use when working any bug-shaped issue, before planning a fix.
---

# repro-first

A fix without a reproduction is a guess with a commit message. Stack
Overflow's bar for even *asking* about a bug is a minimal reproducible
example; the bar for fixing one is not lower.

1. **Reproduce exactly, first.** Run the issue's own steps in this workspace
   before reading the suspect code. Record the exact command and the observed
   wrong behavior — output, traceback, wrong value — verbatim. Pattern-
   matching the title to a likely cause is how wrong fixes ship.
2. **Minimize.** Shrink toward the smallest input, shortest step sequence,
   and fewest components that still fail: cut flags, halve inputs, inline
   fixtures, drop services from the loop — re-running after each cut and
   keeping only cuts that preserve the failure. Complete means the repro
   carries everything needed to fail on its own; minimal means nothing more.
   Do not sacrifice clarity for brevity — a readable ten-line repro beats an
   inscrutable three-line one.
3. **Freeze it as a failing test** in the repo's suite. Run it; watch it
   fail; confirm it fails for the reported reason (the right assertion or
   exception), not a setup error. This test is the issue's acceptance line:
   the fix greens it, and it pins the bug against regression permanently.
4. **Only now open the fix loop** (tdd skill): the smallest change that
   greens the frozen test, then the full suite.
5. **If you cannot reproduce, the trail is the deliverable.** Report exactly
   what you ran (commands, environment, versions), what you observed instead,
   and your best hypothesis for the gap (data, version, config, race). An
   honest "not reproducible, with this evidence" beats a speculative patch.
   Never ship a code change for a failure you never saw.

## Blocked on sight

- A code edit before any recorded reproduction attempt.
- A "fix" for a bug never observed failing in this workspace.
- A repro test that passes before the fix, or fails for a setup reason.
- "Could not reproduce" with no command trail behind it.
- **Building the missing feature to have something to fix.** If the code the
  bug describes does not exist in this repo, the issue is blocked on the
  feature that ships it — report that (name the missing module and, if known,
  the issue that builds it) and stop. A live run showed an agent implementing
  a whole export feature to "fix" a bug filed against it, racing the real
  implementation into a merge conflict.

## Grounding

- Stack Overflow, "How to create a Minimal, Reproducible Example": minimal,
  complete, reproducible — and verify the repro actually fails.
- TDD bug-fix practice: regression test first, watch it fail for the right
  reason, then fix.
- Bug-triage practice: works-for-me is a legitimate resolution only when the
  attempt trail is documented.
