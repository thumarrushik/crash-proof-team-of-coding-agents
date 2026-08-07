# ERROR-SURFACES — fail loud, recover visibly

Nothing dies silently in the console. Every way the UI can fail — fetch,
mutation, render — has a surface the user can see and a way out they can
take. An error the user cannot see is a bug you chose not to show them.

## Every failure reaches the user with a way out

Per Nielsen Norman Group's error-message guidelines, a good error surface
says three things in plain language:

1. **What happened** — human words, not `Error: 500` or a raw API message.
2. **Why it matters to what they were doing** — "your changes were not
   saved", not "request failed".
3. **A way out** — a retry action, the corrected input highlighted, or a
   fallback path. A dead-end error message is half an error message.

Match the surface to the blast radius: a failed background revalidation
can be a quiet inline notice next to still-usable stale data; a failed
save is prominent and blocking until acknowledged; a failed page load is
a full error state with retry. Never a spinner that spins forever —
every loading state has an error exit.

## The three failure planes

- **Queries:** render the cache's `isError` branch with the message and a
  retry that refetches. Empty is not error — a well-formed empty state
  ("no results, here's how to add one") is its own branch, designed, not
  a blank region.
- **Mutations:** on failure, tell the user and preserve their input —
  a failed submit that clears the form punishes the user for your outage.
  If the mutation was optimistic, roll back the cache AND say so
  (SERVER-STATE.md); the rollback without the message looks like the app
  ate their change.
- **Render crashes:** an error boundary above every independent region of
  the page, so one crashed widget degrades that widget — with a reset
  action — instead of white-screening the app. The boundary logs/reports;
  it never swallows.

## Fail loud in code, not just in UI

- No `catch (e) {}` and no console-only handling. Every catch either
  surfaces to the user, rethrows to something that will, or reports to
  monitoring — stated explicitly, chosen deliberately.
- Do not catch broadly "to be safe". Catch where you can actually recover
  or present; let the rest hit the boundary. A swallowed exception turns
  a loud bug into a silent data bug.
- Error text shown to users is written for users; the raw error object
  goes to the log/reporter, not the screen.

## Prove the branches

Error and empty rendering get tests with the same weight as success: for
each query surface, a test that the error branch renders the message and
the retry works, and a test that the empty state renders its designed
content. A branch without a test is a branch that will silently regress
into a blank div.

## Grounding

- Nielsen Norman Group, "Error-Message Guidelines" — visible, human
  language, constructive way out.
- React docs — error boundaries for render crashes.
- TanStack Query docs — error/status branches on queries and mutations;
  rollback messaging on failed optimistic updates.
