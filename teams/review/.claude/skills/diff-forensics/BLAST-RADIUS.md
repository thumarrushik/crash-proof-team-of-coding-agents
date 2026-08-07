# BLAST-RADIUS — the change is judged everywhere it lands, not where it was made

A hunk is correct or incorrect only in the context of the whole system. Before
judging any edit, map where its effects travel — then hunt the behavior
changes the PR description never admitted to.

## Map the callers first

For every edited function, method, signature, constant, and config key in the
diff:

1. Grep the repo for its callers, importers, and readers. Include string
   references — config keys, env var names, and route paths are called by
   string, not by symbol.
2. Visit each site and ask one question: does the change still hold here?
   A new required parameter, a narrowed return, a changed default, a
   different error type — each caller either absorbs it or breaks on it.
3. A change correct at its definition and wrong at even one caller is a
   blocking issue. File it with the caller's file:line, not the definition's.

Do this before forming an opinion of the edit itself. An elegant change with
an unvisited caller is an unreviewed change.

## Hunt unclaimed behavior deltas

The PR description is a claim about what changed. The diff is what actually
changed. Your job is the difference. Sweep the hunks for:

- **Changed defaults** — a parameter, config value, or flag whose default
  moved. Every caller relying on the old default just changed behavior
  without a diff line of its own.
- **Widened or narrowed types** — including "harmless" ones; validators,
  serializers, and typed callers feel these.
- **Reordered operations** — a write moved before a validation, a lock
  acquired later, a side effect hoisted out of a conditional.
- **Altered error paths** — a raise became a return, a specific exception
  became a broad catch, a loud failure became a logged-and-swallowed one.
  Silenced failure is a behavior delta of the highest order.
- **Retry, timeout, and timing changes** — backoff constants, poll
  intervals, deadline math.
- **Changed serialization** — field order, date formats, null vs absent,
  enum casing. Anything a consumer might have parsed.

## The intent rule

For each delta found, ask two questions: *intended?* and *tested?*

- If the PR description does not mention it, treat it as **unintended until
  the code proves intent** — a deliberate structure, a named constant, a
  comment, a test asserting the new behavior. Absent proof, it is a
  `question` at minimum and an `issue (blocking)` on correctness-relevant
  paths.
- "Tests still pass" is not evidence when no test exercises the delta. A
  green suite that never touches the changed path proves only that the suite
  is blind there — say so in the finding.

## Write it as evidence

Every blast-radius finding states: the changed symbol and its file:line, the
affected site and its file:line, the delta in behavior, and what breaks when
it fires. "This might affect callers" is a hunch; a named caller with a named
break is a finding.

## Grounding

- Google eng-practices, "What to look for": every line, and the CL judged in
  the context of the whole system.
