---
name: state-and-errors
description: Server-state vs client-state discipline with fail-loud, recoverable error handling. Use when writing any UI logic that fetches, caches, or mutates data.
---

# state-and-errors

The UI's job is to tell the truth about the data — including when it is
stale, missing, or failing.

## Phases — in order

1. **Classify every piece of state.** Server state is fetched, owned
   elsewhere, shared, and can go stale behind your back. Client state is
   UI-only: open panels, form drafts, toggles. They need different tools —
   never mirror server responses into a client store.
2. **Server state goes through a query cache** (TanStack Query / SWR or the
   repo's equivalent), which gives stale-while-revalidate: render cached
   data instantly, revalidate in the background, dedupe identical requests,
   and invalidate by key after mutations. Do not hand-roll useEffect +
   setState fetching with manual isLoading/isError flags.
3. **Minimize client state.** Single source of truth per fact; derive at
   render instead of duplicating; no two components each owning a copy of
   the same value. Most "global state" is server state wearing a disguise.
4. **Fail loud, recover visibly.** Every fetch and mutation has an error
   path that reaches the user with what happened and a way out (retry
   action, corrected input, fallback) per NN/g. Render crashes hit an error
   boundary. Nothing dies silently in the console.
5. **Optimistic updates earn their optimism.** Snapshot the previous cache
   before applying, roll back on error and tell the user, re-sync
   (invalidate/refetch) on settle. No rollback path = no optimistic update.
6. **Prove the branches.** Error and empty rendering get tests with the
   same weight as success.

## Blocked on sight

- API responses copied into Redux/Zustand/context "for convenience".
- `catch (e) {}` or console-only error handling.
- Hand-tracked loading/error flags sitting next to a query cache.
- An optimistic mutation with no rollback; a spinner with no error exit.

## Grounding

- TanStack Query docs: server-state definition; optimistic-updates guide
  (onMutate snapshot -> onError rollback -> onSettled invalidate).
- HTTP RFC 5861 stale-while-revalidate — the caching model behind
  SWR and TanStack Query.
- Kent C. Dodds, "Application State Management with React": server cache
  is not client state.
- Nielsen Norman Group, "Error-Message Guidelines".
