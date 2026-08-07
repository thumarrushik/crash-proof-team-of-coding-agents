# INSPECTION — the six concerns, in order

Work the diff top-down through these concerns. Order matters: a design
finding invalidates everything below it (there is no point polishing tests on
code that should not exist here), so settle each level before descending.

## The bar you are holding

Approve when the change **definitely improves the overall code health of the
system, even if it isn't perfect**. This is Google's Standard of Code Review,
and it cuts both ways:

- Never block on polish you would not stake a merge on. Demanding perfection
  stalls better-than-today code out of the tree.
- Never approve a change that degrades code health because it "works", is
  urgent, or will be "cleaned up later". Code health only ever decays through
  a series of individually approved CLs.

## 1. Design

Does this change belong here at all, and does it integrate with the system or
fight it? Ask: is this the right place in the codebase, the right layer, the
right abstraction? Does it duplicate a mechanism that already exists? A CL
that degrades system code health is not accepted, whatever its local quality.

## 2. Functionality

Does the code do what the PR description claims — for its users, not just its
happy path? Walk the edges deliberately: empty input, missing input,
duplicates, concurrent callers, an unavailable dependency. Think about what
the *user* of this code (end user or calling developer) experiences when each
edge fires. If you cannot determine behavior by reading, that is a `question`
finding, not a shrug.

## 3. Complexity

Could it be simpler? Would the next reader understand it without archaeology?
Over-engineering is a complexity finding: speculative generality, hooks for
futures nobody scheduled, configurability with one caller. Flag complexity
now — it is far cheaper than flagging the bugs it breeds later.

## 4. Tests

Tests must be correct, behavioral, and adversarial:

- They would fail if the change were reverted — a test that passes against
  the old code tests nothing.
- They cover the failure branches, not only the happy path.
- They make claims about behavior, not implementation trivia that any honest
  refactor would break.

A diff that changes behavior with no test movement is a finding.

## 5. Naming and comments

Names say what a thing is — full words, not abbreviations that force the
reader to hold a glossary. Comments say *why*, not what: a comment restating
the code is noise; a comment the diff just made stale is a finding, because
it will actively mislead the next reader.

## 6. Consistency

The diff must match surrounding conventions — error handling, layering,
naming style, test structure. A diff importing its own style is a design
finding, not taste: it makes the file bimodal and every future edit costlier.

## Grounding

- Google eng-practices: "What to look for in a code review" and "The Standard
  of Code Review" (google.github.io/eng-practices).
