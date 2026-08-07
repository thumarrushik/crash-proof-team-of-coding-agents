# DEPRECATION — version beside, sunset, then delete

A breaking change never edits the served shape. It ships as a new version
served beside the old, and the old version keeps serving through a stated
window. Deprecated is a phase of service, not a synonym for gone.

## The lifecycle, in order

1. **Serve both.** The new shape goes up under the next version (`/v0` →
   `/v1` per house convention). The old version keeps serving unchanged —
   same shape, same codes, same tests.
2. **Mark the old.** Every response from the deprecated version or route
   carries `Deprecation` and `Sunset` headers (below). Headers reach the
   one audience docs never do: the running client.
3. **Announce.** The contract doc names the replacement, gives a
   field-by-field migration mapping (old field → new field, old code → new
   code), and states the sunset date. "See the new version" is not a
   migration mapping.
4. **Wait out the window.** Watch traffic on the deprecated surface. The
   window ends by calendar *and* by evidence: sunset date passed, and
   consumers confirmed off (traffic at zero, or every known caller
   migrated and acknowledged).
5. **Delete** — its own change, reviewed like any other. Deleting early
   because "nobody should be using it" is how outages are written.

## The headers (RFC 8594)

- `Sunset: Sat, 01 Nov 2026 00:00:00 GMT` — the HTTP-date after which the
  resource is expected to stop serving (RFC 8594).
- `Deprecation: true` (or a date) — the surface is deprecated now, before
  the sunset arrives.
- Serve both on every deprecated response, plus a `Link` to the migration
  doc where practical. Contract tests for a deprecated version assert the
  headers are present — an unmarked deprecation is unshipped.

## What the majors do — steal the shape, not the scale

- **Stripe** pins each account to the API version current at its first
  request, forever, and lets any single request override via a
  `Stripe-Version` header. Internally, core code targets only the latest
  shape; a chain of per-version transformation modules rewrites responses
  down to each pinned version. The lesson: old versions should cost a
  translation layer at the edge, never a fork of business logic.
- **GitHub** names REST versions by date (`2022-11-28`), selected with the
  `X-GitHub-Api-Version` header; breaking changes ship only in a new
  version; each version is supported for a published minimum window
  (24 months); retiring surfaces get Deprecation/Sunset headers. The
  lesson: publish the support window as standing policy, so no deletion is
  a per-consumer negotiation.

## Sizing the window

Proportional to consumer count and deploy cadence. For internal teams the
floor is: at least one full deploy cycle of every consuming service after
the announcement, plus explicit confirmation from each named consumer. For
anything external or unenumerable, the window is calendar-published policy,
not a judgment call per change.

## While both versions serve

- The old version is frozen: bug fixes that restore documented behavior
  only — never new fields, never shape edits.
- Both versions run the full contract-test suite (CONTRACT-TESTS.md); the
  old version's suite is deleted with the version, not before.
- New consumers are pointed at the new version from day one; the contract
  doc marks the old one deprecated at the top.

## Grounding

- AIP-185 Versioning (multiple versions served concurrently) — google.aip.dev/185
- "APIs as infrastructure: future-proofing Stripe with versioning" — stripe.com
- GitHub REST API date versions with Deprecation/Sunset headers (RFC 8594) — docs.github.com
