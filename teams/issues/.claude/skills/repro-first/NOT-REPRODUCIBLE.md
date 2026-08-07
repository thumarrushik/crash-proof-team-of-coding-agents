# NOT-REPRODUCIBLE — the honest exits when the bug won't show

Two situations end a bug issue without a fix: the failure will not reproduce,
or the code the bug describes does not exist. Both have a correct deliverable
that is not a patch. Shipping code anyway is the failure mode this file
exists to block.

## The trail is the deliverable

"Works for me" is a legitimate triage resolution — but only when the attempt
trail is documented. If you ran the issue's steps and the failure did not
appear, report:

1. **Exactly what you ran** — every command, verbatim, in order.
2. **The environment** — versions of the runtime, the package, key
   dependencies; OS; relevant config values; how the workspace was set up.
3. **What you observed instead** — the actual output where the failure was
   supposed to be. "It worked" is weaker than pasting the correct output.
4. **Your best hypothesis for the gap** — the usual suspects, checked and
   named: data the reporter has and you don't, a version skew, a config
   difference, a race or timing window, an environment-specific path.

That report lets the reporter close the gap — send the data, name the
version — and lets the next investigator start from your trail instead of
from zero. An honest "not reproducible, with this evidence" advances the
issue; a speculative patch mortgages it.

**Never ship a code change for a failure you never saw.** A patch for an
unobserved bug cannot be verified fixed (nothing failed before it) and can
be verified harmful (something may fail because of it). If the code clearly
looks wrong even though the repro won't fire, say that in the report — as a
hypothesis with the evidence gap named, not as a fix.

## The missing-feature trap

Sometimes the reason you cannot reproduce is structural: **the code the bug
describes does not exist in this repo.** A bug filed against an export
feature, in a repo with no export feature, is not an invitation to write
one.

This is not hypothetical. A live run in this workflow showed an agent
implementing a **whole export feature** in order to "fix" a bug filed
against it — racing the real implementation, which was being built under its
own issue, straight into a merge conflict. Two costs, both certain: the
duplicated work, and the collision with the team's actual plan for that
feature.

The rule: if the module, endpoint, or command the issue names is absent,
the issue is **blocked on the feature that ships it**. Your deliverable is
the block report:

1. Name the missing module or surface, with the greps/paths that prove its
   absence.
2. If known, name the issue or branch where the feature is actually being
   built.
3. Mark this issue blocked on it, and stop.

Building the feature "so there is something to fix" fails every discipline
at once: no reproduction (repro-first), no acceptance criterion for a
feature nobody specified (scope-control), and unreviewable scope in a
bug-sized issue.

## Blocked on sight, restated for this exit

- "Could not reproduce" with no command trail behind it.
- A patch attached to an unobserved failure "just in case".
- Any new feature surface appearing in a bug issue's diff.

## Grounding

- Bug-triage practice: works-for-me is a legitimate resolution only when
  the attempt trail is documented.
- This workflow's live run: an agent built a missing export feature to
  "fix" a bug filed against it, ending in duplicated work and a merge
  conflict — the incident behind the missing-feature rule.
