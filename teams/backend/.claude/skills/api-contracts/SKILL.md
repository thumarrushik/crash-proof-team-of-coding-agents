---
name: api-contracts
description: Treat every HTTP API as a versioned published contract — classify each change as additive or breaking, deprecate with a sunset window instead of editing in place, keep errors machine-stable, and prove shapes with contract tests; use when adding, changing, or removing any endpoint, field, enum value, or error response.
---

# api-contracts

An endpoint is a promise other teams build on. Change code freely; change the
promise only through this procedure. Route anatomy, `/v0`, and the canonical
envelope are defined in [[lean-service]] (BACKEND.md) — this skill governs how
a served contract is allowed to *change*.

## 1. Shape first

Write the full request/response shape — fields, types, optionality, enums with
all values, pagination, every error case — before the handler. Review happens
on the shape, not on 400 lines of handler.

## 2. Classify the change before writing code

**Additive (ship in place, no new version):** new endpoint; new *optional*
request field; new response field; new error `code` for a new failure. State
in the contract that clients must tolerate unknown response fields.

**Breaking (requires a new version):** removing or renaming a served field or
route (a rename is remove-plus-add — keep the old, add the new); changing a
field's type, meaning, or default; making optional required; tightening
validation on existing input; changing a status code or error `code` that
consumers branch on. When unsure, treat it as breaking.

## 3. Version and deprecate — never edit in place

A breaking change is a new version served beside the old. The old version
keeps serving through a stated window: mark it with `Deprecation` and `Sunset`
response headers, name the replacement in the contract doc, and delete only
after the sunset date passes with consumers confirmed off it. Additive changes
never bump the version — version inflation trains clients to fear upgrades.

## 4. Errors are contract; prose is not

Every failure path maps to the canonical envelope with a stable machine
`code`. The `message` text is for humans and may change freely — clients
branch on status + `code` only, never parse messages or ID formats. Unknown
exceptions become the envelope's 500, logged loud. No bare 500s, no
200-with-failure-inside.

## 5. Prove it with contract tests

Per operation, assert the consumer-visible shape field-by-field: the happy
path, and each enumerated failure's status + `code` + envelope. Tests must
fail when a served field disappears or changes type, and still pass when one
is added. Run them over real HTTP against the real service ([[lean-service]]
TESTING.md bar) — a mock of your own service verifies nothing.

## Blocked on sight

- Editing a served shape in place, including "just renaming" a field.
- A version bump for an additive change.
- Per-endpoint error shapes, or clients parsing `message` text.
- Removing a deprecated route with no Sunset window served and checked.
- Undocumented "temporary" fields in a served response.

## Grounding

- AIP-180 Backwards Compatibility, AIP-185 Versioning — google.aip.dev
- "APIs as infrastructure: future-proofing Stripe with versioning" — stripe.com
- GitHub REST API date versions with Deprecation/Sunset headers (RFC 8594) — docs.github.com
- Consumer-driven contract testing — pact.io
