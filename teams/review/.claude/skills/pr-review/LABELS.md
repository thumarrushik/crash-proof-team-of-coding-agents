# LABELS — Conventional Comments, so severity is never ambiguous

Every finding carries a label and a decoration. The label tells the author —
and the merge gate — exactly what kind of claim you are making and whether it
stands between the PR and merge. Unlabeled prose findings are how blockers
get read as suggestions and nitpicks get read as blockers.

## The labels, blockers listed first

- `issue (blocking): file:line — what breaks and why` — must be fixed to
  merge. Both parts are mandatory: the location, and the stated consequence.
  An issue you cannot attach a consequence to is not an issue yet.
- `suggestion (non-blocking): ...` — a concrete improvement with reasoning.
  The author decides; you have stated your case, not issued an order.
- `nitpick (non-blocking): ...` — polish. Never blocks, and never pads a
  verdict: five nitpicks do not sum to one issue.
- `question: ...` — intent you could not determine from the diff. Ask it
  plainly; do not disguise an objection as a question or a question as an
  objection.

## Decorations are load-bearing

`(blocking)` / `(non-blocking)` is the merge gate's machine-readable bit.
Write it explicitly on every issue, suggestion, and nitpick. A bare `issue:`
forces the author to guess your severity — and guessed severity is how real
blockers slide through and how taste gets enforced as law.

## Escalation rules

- An unanswered `question` on correctness-relevant code escalates to
  `issue (blocking)`. If you could not determine whether the code is correct
  and the author will not or cannot say, the diff has not earned approval.
- A `suggestion` the author declines with reasoning is closed. A suggestion
  the author ignores on correctness-adjacent code becomes a question.
- Nitpicks never escalate. If it matters more than polish, it was mislabeled.

## What each finding must contain

1. Label and decoration, exactly as above.
2. `file:line` for anything anchored to the diff.
3. The observable consequence — what breaks, misleads, or decays if merged
   as-is. "I would not write it this way" is not a consequence.
4. For suggestions: the improvement itself, concretely, not "consider
   improving this".

## Anti-patterns, named

- **Taste laundering** — personal style filed under `issue` to make it
  blocking. If surrounding conventions do not demand it, it is at most a
  suggestion.
- **Verdict padding** — stacking nitpicks to make a review look thorough or
  a REQUEST_CHANGES look justified. Thoroughness lives in INSPECTION.md's
  concerns, not in comment count.
- **Severity mumbling** — hedged prose ("might be worth maybe looking at")
  where a label should be. Commit to a label; hedging transfers your job to
  the author.

## Grounding

- Conventional Comments (conventionalcomments.org): label + decoration
  format.
