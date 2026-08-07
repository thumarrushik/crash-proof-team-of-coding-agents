---
name: api-contracts
description: Treat every HTTP API as a versioned published contract — classify each change as additive or breaking, deprecate with a sunset window instead of editing in place, keep errors machine-stable, and prove shapes with contract tests; use when adding, changing, or removing any endpoint, field, enum value, or error response.
---

# api-contracts

An endpoint is a promise other teams build on. Change code freely; change the
promise only through this procedure. Route anatomy, `/v0`, and the canonical
envelope are defined in [[lean-service]] (BACKEND.md) — this skill governs how
a served contract is allowed to *change*.

## How to use this skill

1. Read this file every time an endpoint, field, enum value, or error case is
   added, changed, or removed. Write the full shape before the handler.
2. Open the topic file for the step you are on (below). Don't read all of
   them — load what the change needs.

## Topic map (load on demand)

| Task | File |
|---|---|
| Decide additive vs breaking — the change catalog, errors-as-contract | **[CLASSIFICATION.md](CLASSIFICATION.md)** |
| Ship a breaking change: version beside, Deprecation/Sunset, delete | **[DEPRECATION.md](DEPRECATION.md)** |
| Prove the served shape with contract tests, field by field | **[CONTRACT-TESTS.md](CONTRACT-TESTS.md)** |

## The rules in one breath

1. Shape first: full request/response — fields, types, optionality, enums
   with all values, pagination, every error case — before the handler.
   Review happens on the shape, not on 400 lines of handler.
2. Classify every change additive or breaking before code; unsure = breaking.
3. Breaking = a new version served beside the old. Never edit a served shape
   in place — a rename is remove-plus-add.
4. Additive never bumps the version; clients must tolerate unknown fields.
5. Deprecate with `Deprecation` + `Sunset` headers and a stated window;
   delete only after the window passes with consumers confirmed off.
6. Errors are contract: stable machine `code` in the canonical envelope;
   `message` is prose and may change. Clients branch on status + `code` only.
7. Contract tests assert the served shape field-by-field over real HTTP.

**Blocked on sight:** editing a served shape in place, including "just
renaming" a field · a version bump for an additive change · per-endpoint
error shapes, or clients parsing `message` text · removing a deprecated route
with no Sunset window served and checked · undocumented "temporary" fields in
a served response.
