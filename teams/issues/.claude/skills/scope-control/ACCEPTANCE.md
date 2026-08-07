# ACCEPTANCE — the scope contract, written first and closed last

Scope is not a feeling of restraint while editing. It is one sentence
written before the first edit and one shown check that closes it in the
report. Everything in the diff must trace to the sentence; the sentence must
trace to the check.

## Write the contract before editing

Restate the issue in one sentence, ending with its acceptance line:

> "done when <observable check> passes"

The check must be observable — a test that greens, a command whose output
changes, an endpoint that returns the corrected shape. Examples:

- "Fix the pagination off-by-one — done when the last-page test returns 7
  items, not 6."
- "Reject empty tenant IDs at the boundary — done when POST with an empty
  tenant_id returns 422 with code `invalid_tenant`."

**If you cannot write the sentence, the issue is ambiguous.** Do not resolve
ambiguity by picking the most interesting interpretation and building it —
flag the ambiguity in the report as the deliverable. Guessed scope produces
diffs the review gate cannot judge, because nobody can say what they were
supposed to do.

## Smallest correct change — correct first, small second

The contract bounds the change; inside the bound, choose the smallest change
that is fully correct:

- **Fewest files.** Every additional touched file widens review surface —
  and defect discovery collapses beyond ~400 changed lines, so scope creep
  literally makes your bugs harder to catch.
- **Edit existing functions over adding parallel ones.** A `do_thing_v2`
  beside `do_thing` doubles the maintenance surface to dodge one merge.
- **Reuse existing abstractions over inventing new ones.** The issue asked
  for a fix, not a framework.

But small **never means half a fix**: handling the reported case while
leaving its obvious sibling broken is small and wrong. If the bug fires on
`None` and identically on `""`, the correct change covers both — that is
one fix, complete, not scope creep. The line: siblings of the reported case
are in scope; features adjacent to the reported case are not.

## Close the loop in the report

The acceptance sentence from before the first edit must map to a shown
check in the report: the test name and its green run, or the command and
its corrected output — pasted, not narrated.

An acceptance line with no check beside it means the issue is not resolved —
merely edited. This closing step is also your self-review's scope audit:
walk the diff hunk by hunk and tie each one to the sentence. A hunk you
cannot tie to it is either a sibling of the fix (say so) or scope creep
(revert it, note it under "Noticed, not changed" — see YAGNI.md).

## Grounding

- Google eng-practices, "Small CLs": small changes review faster, more
  thoroughly, and breed fewer bugs.
- SmartBear/Cisco: defect discovery collapses beyond ~400 changed lines —
  scope creep literally makes your bugs harder to catch.
