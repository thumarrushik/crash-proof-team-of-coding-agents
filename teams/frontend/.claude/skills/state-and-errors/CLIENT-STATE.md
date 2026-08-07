# CLIENT-STATE — minimize, own once, derive the rest

Client state is UI-only: open panels, form drafts, toggles, the selected
tab. It never leaves the browser and nobody else can change it behind your
back. That makes it cheap — and that cheapness is why it accumulates until
the app is a web of copies. The discipline is subtraction.

## Classify before you create

Before adding any state, ask: could this value change on the server
without this component knowing? If yes, it is server state — route it
through the query cache (SERVER-STATE.md), full stop. Most "global state"
in aging apps is server state wearing a disguise: a user object copied
into context, a list mirrored into a store. Strip those and what remains
as genuine client state is usually small enough for local `useState` plus
one small store or context for the truly shared bits.

## Single source of truth per fact

- Each fact is owned by exactly one place. No two components each holding
  a copy of the same value and "syncing" via effects — the sync is where
  the bugs live.
- **Derive at render instead of duplicating.** `selectedItem` is
  `items.find(i => i.id === selectedId)` computed at render — store the
  `selectedId`, never a second copy of the item. Stored derived values go
  stale the moment their source changes.
- If a derivation is expensive, memoize it; memoization is still
  derivation. Copying is not.

## Keep state as local as it can be

- Start with `useState` in the component that renders it. Lift only when
  a second component genuinely needs it — and lift to the lowest common
  ancestor, not to a global store by reflex.
- URL-shaped state (active tab, filters, page) belongs in the URL. It
  survives refresh, is shareable, and the router already owns it —
  a store copy of it is a second source of truth.
- Form drafts belong to the form (component state or the form library),
  not to a global store that outlives the form and leaks stale drafts.

## Smells that route back here

- A `useEffect` whose only job is copying one piece of state into
  another — that is a derived value or a lifted owner, not an effect.
- A store field whose comment says "kept in sync with X".
- Context holding a server response "so we don't refetch" — the query
  cache already deduplicates and caches; the copy only adds staleness.

## Grounding

- Kent C. Dodds, "Application State Management with React" — colocate
  state; most global state is server state in disguise.
- TanStack Query docs — server-state definition (the classification
  boundary this file's rules stand on).
