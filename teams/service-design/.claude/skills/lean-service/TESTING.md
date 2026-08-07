# TESTING (the verification bar)

"Done" means verified against **real** infrastructure, end to end, with the fail-loud paths asserted —
not a green unit run alone. Nothing faked.

## Bar

1. **Test against real infra** (real DB / object store), skipping cleanly with a clear reason if it's
   unreachable. Self-clean: provision throwaway tenants under a test prefix and **force-drop** them after
   (`DROP DATABASE ... WITH (FORCE)` / equivalent).
2. **Cross-service paths run through the live peers** (integration), not mocks — so envelope unwrapping +
   upstream-status propagation are exercised for real.
3. **Run suites 5×** for stability before declaring green (catches flakes/ordering/races).
4. **Live-verify the end-to-end flow through the built containers** — rebuild the image first so new
   migrations/code/seeds are baked, then exercise the real HTTP flow (and re-run to confirm `run_count`/
   idempotency-type behavior).
5. **Assert the fail-loud branches** (422 / 404 / 409 / 503), not just the happy path — that's where
   "nothing faked" is actually proven.
6. Clean up all test tenants at the end; confirm none leaked.

## LLM / optional-dep testing (no key, no cost)

- Unit-test the orchestration with an **injected deterministic mock** (no network/key) — covers
  generate → validate → refine → persist.
- Exercise the **real transport** against a **local OpenAI-compatible server** (a stub or a local model via
  `*_BASE_URL`) to prove request serialization + response parsing — without a paid call.
- Assert the **no-key path fails loud** (503) — the message names the missing dependency.

## Browser e2e

- Drive the real dockerized UI; assert **URLs + structured elements** (not JSON/log substrings).
- **`workers: 1`** when specs share one live backend — concurrent tenant creation contends and flakes.
- Migrate nav assertions to the real nav testids + URL checks.
- Re-confirm the UI-click pitfalls (label-wrapped checkbox double-toggle; sticky-header click interception;
  dispatch-click after a checkbox toggle) — see FRONTEND.md / HARD-RULES.md.

## Idempotency / seeds gotchas

- A migrate-idempotency test must assert on a **second** migrate run (pre-existing stores may legitimately
  apply the new version on the first).
- Seeding common entities means clients aren't "empty" — empty-state tests must target a resource with **no**
  seeds, and create flows must avoid colliding with seeded names.
