# RENDER-STATES.md — the four states, and error messages that help

Every data-driven surface has four states, not one. Shipping only the
success state is the most common frontend defect, because the happy path is
the only one you see while building.

## The four states — each gets a real rendering

1. **Loading.** Reserve the space the content will occupy so nothing jumps
   when data arrives (skeletons or fixed-size placeholders). A spinner that
   reflows the page on arrival is a layout bug.
2. **Empty.** Say *why* it is empty and offer the next action ("No links
   yet — add your first"). An empty state is an onboarding moment, not a
   blank div.
3. **Error.** Reached, visible, recoverable (see below). Never a silent
   console log; never a spinner that spins forever.
4. **Success.** The data, in the hierarchy LAYOUT.md set.

Each state gets a behavior assertion in the tests — error and empty carry
the same weight as success ([[browser-e2e]], [[tdd]]).

## Error messages (NN/g)

A good error message has three parts:
- **What happened**, in plain language — not an error code, not a stack
  trace.
- **Why**, when it is known ("the link couldn't be saved because it's
  already in your list").
- **What to do next** — a retry, a correction, a fallback path.

Tone: polite, precise, constructive. Never blame the user ("invalid input"
→ "enter a URL starting with http"). Form errors appear inline beside the
field, and the user's input is preserved — never cleared on error.

## Grounding

- Nielsen Norman Group, "Error-Message Guidelines" and "10 Design
  Guidelines for Reporting Errors in Forms".
- NN/g 10 Usability Heuristics #9: help users recognize, diagnose, and
  recover from errors.
- The four-states discipline is pinned in [[state-and-errors]] on the data
  side and [[tdd]] on the test side.
