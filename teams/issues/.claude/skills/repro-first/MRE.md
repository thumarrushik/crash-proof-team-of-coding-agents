# MRE — reproduce exactly, then minimize

The minimal reproducible example is the unit of bug work. Everything
downstream — the frozen test, the fix, the verdict — inherits its quality.
Build it in two phases: exact reproduction first, minimization second. Never
minimize a failure you haven't seen whole.

## Phase 1: reproduce exactly

Run the issue's **own steps**, in this workspace, before reading the suspect
code:

1. Follow the report literally — its commands, its inputs, its order. Do not
   substitute "equivalent" steps yet; equivalence is exactly what is in
   question.
2. Record the exact command you ran and the observed wrong behavior
   **verbatim** — the output, the traceback, the wrong value. Paste, don't
   paraphrase: "throws KeyError: 'user_id' at session.py:88" is evidence;
   "crashes on login" is a rumor.
3. Compare what you observed against what the issue claims. Same failure,
   same symptom? Then you have a reproduction. A *different* failure is a
   different bug — note it, but keep hunting the reported one.

Why before reading the code: pattern-matching the issue title to a likely
cause is how wrong fixes ship. The code will happily confirm whatever theory
you walked in with; the running failure cannot.

## Phase 2: minimize

Shrink toward the smallest input, shortest step sequence, and fewest
components that still fail:

- Cut flags and options one at a time.
- Halve inputs (bisect data files, truncate lists, shorten strings).
- Inline fixtures so the repro carries its own data.
- Drop services and dependencies out of the loop — if the failure survives
  without the database, the database was never part of the bug.

**Re-run after each cut. Keep only cuts that preserve the failure.** A cut
that makes the failure vanish is information — it just fingered a necessary
ingredient; put it back and note it.

The target is Stack Overflow's bar, both halves:

- **Complete** — the repro carries everything needed to fail on its own: a
  fresh workspace plus the repro reproduces the bug, nothing else required.
- **Minimal** — nothing more than that. Every remaining line either
  contributes to the failure or to readability.

And readability is not negotiable: a readable ten-line repro beats an
inscrutable three-line one. The repro's next job is to become a test that
future maintainers must understand at a glance (see FREEZE.md).

## What the finished MRE gives you

- The exact trigger conditions — which is most of a diagnosis.
- A fast inner loop for the fix (seconds, not the full original scenario).
- The direct input to FREEZE.md: a failing test is a frozen MRE.

## Grounding

- Stack Overflow, "How to create a Minimal, Reproducible Example": minimal,
  complete, reproducible — and verify the repro actually fails.
