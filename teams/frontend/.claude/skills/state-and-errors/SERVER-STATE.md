# SERVER-STATE — remote data goes through a query cache

Server state is fetched over the network, owned by the backend, shared
between users, and can go stale behind your back. Treat it as a cache of
someone else's truth, never as your own state. TanStack Query's docs draw
this line explicitly: if it lives on the server and you only hold a
snapshot, it is server state.

## Route it through a query cache

Use TanStack Query / SWR or the repo's existing equivalent. The cache buys
you, for free and correctly:

- **Stale-while-revalidate** (the HTTP RFC 5861 model): render cached data
  instantly, revalidate in the background, swap in fresh data when it
  lands. The user never stares at a spinner for data you already have.
- **Request deduplication:** ten components asking for the same key issue
  one fetch.
- **Keyed invalidation:** after a mutation, invalidate the query keys it
  affects; the cache refetches. That is the whole consistency story — no
  manual "refresh" plumbing threaded through components.
- **Status flags derived, not tracked:** `isLoading` / `isError` come from
  the cache. Hand-tracked flags beside a query cache are a bug farm —
  they drift from the truth they mirror.

Do not hand-roll useEffect + setState fetching. The hand-rolled version
misses dedupe, races on unmount, forgets the error branch, and re-implements
staleness wrong. If the repo has no query cache, adding one is smaller than
writing the third bespoke fetch hook.

## Query keys are the contract

- One canonical key shape per resource (`['todos', filters]`), built by a
  shared helper — not string literals scattered across files.
- Everything the fetch depends on goes in the key. A filter that changes
  without changing the key serves stale data silently.
- Mutations name the keys they invalidate. "Invalidate everything" hides
  what the mutation actually touches.

## Optimistic updates earn their optimism

An optimistic update shows the mutation's result before the server
confirms. It is only allowed with the full three-step protocol (TanStack
Query's optimistic-updates guide):

1. **onMutate:** cancel in-flight refetches for the key, snapshot the
   previous cache value, apply the optimistic value.
2. **onError:** restore the snapshot and tell the user the change failed —
   a silent rollback is a lie followed by a haunting.
3. **onSettled:** invalidate/refetch the key so the cache re-syncs with
   the server's actual answer either way.

No rollback path = no optimistic update. Ship the pessimistic version;
it is honest and half the code.

## Never mirror into a client store

Copying API responses into Redux/Zustand/context "for convenience" creates
a second copy with no staleness model, no revalidation, and no
invalidation. It is guaranteed to drift (Kent C. Dodds, "Application State
Management with React": the server cache is not client state). Components
read from the query cache directly; if a value seems to need a store, it
is either derivable at render or it is client state — see CLIENT-STATE.md.

## Grounding

- TanStack Query docs — server-state definition; optimistic-updates guide
  (onMutate snapshot -> onError rollback -> onSettled invalidate).
- HTTP RFC 5861 stale-while-revalidate — the caching model behind SWR and
  TanStack Query.
- Kent C. Dodds, "Application State Management with React" — server cache
  is not client state.
