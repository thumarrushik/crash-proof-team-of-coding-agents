---
name: state-and-errors
description: Server-state vs client-state discipline with fail-loud, recoverable error handling. Use when writing any UI logic that fetches, caches, or mutates data.
---

# state-and-errors

The UI's job is to tell the truth about the data — including when it is
stale, missing, or failing. Every piece of state is either server state
(fetched, owned elsewhere, can go stale behind your back) or client state
(UI-only). They need different tools, and every failure needs a visible,
recoverable surface.

## How to use this skill

1. Read this file whenever UI logic fetches, caches, or mutates data —
   before writing the hook or store, not after.
2. Classify each piece of state first, then open the topic file for the
   side you are on. Load ERROR-SURFACES.md for any fetch, mutation, or
   render that can fail.

## Topic map (load on demand)

| Task | File |
|---|---|
| Fetch/cache/mutate remote data — query cache, invalidation, optimistic updates | **[SERVER-STATE.md](SERVER-STATE.md)** |
| UI-only state — minimize, single source of truth, derive at render | **[CLIENT-STATE.md](CLIENT-STATE.md)** |
| Fail loud, recover visibly — error paths, boundaries, testing the branches | **[ERROR-SURFACES.md](ERROR-SURFACES.md)** |

## The rules in one breath

1. Classify every piece of state: server state or client state — never
   mirror server responses into a client store.
2. Server state goes through a query cache (TanStack Query / SWR or the
   repo's equivalent); no hand-rolled useEffect + setState fetching.
3. Minimize client state: single source of truth per fact, derive at
   render instead of duplicating.
4. Fail loud, recover visibly: every fetch and mutation has an error path
   that reaches the user with what happened and a way out.
5. Optimistic updates earn their optimism: snapshot, roll back on error
   and tell the user, re-sync on settle. No rollback path = no optimism.
6. Prove the branches: error and empty rendering get tests with the same
   weight as success.

**Blocked on sight:** API responses copied into Redux/Zustand/context
"for convenience" · `catch (e) {}` or console-only error handling ·
hand-tracked loading/error flags sitting next to a query cache · an
optimistic mutation with no rollback; a spinner with no error exit.
