# CLASSIFICATION — additive or breaking, decided before code

Write the full shape first — fields, types, optionality, enums with all
values, pagination, every error case — then classify the delta against what
is currently served. The classification decides the whole shipping procedure
(in place, or through DEPRECATION.md), so it comes before any handler code.

## Additive — ship in place, no new version

- A new endpoint or operation.
- A new *optional* request field whose absence preserves today's behavior
  exactly. If the field's default changes behavior, it is not additive.
- A new response field. State in the contract that clients must tolerate
  unknown response fields — that tolerant-reader statement is what makes
  response additions safe at all.
- A new enum value in a field clients only *send*. A new value in a field
  clients *receive* is breaking unless the contract already tells them to
  handle unknown values — check the contract doc before assuming.
- A new error `code` for a genuinely new failure mode, in the canonical
  envelope.

Additive changes never bump the version. Version inflation trains clients to
fear upgrades — AIP-180's core stance is that compatibility is the default
and new versions are the exception, not the routine.

## Breaking — requires a new version served beside the old

- Removing or renaming a served field, route, or enum value. A rename is
  remove-plus-add: keep the old, add the new, deprecate the old.
- Changing a field's type — including "compatible-looking" widenings
  (int → string, int32 → int64). Generated clients, validators, and typed
  consumers break even when the wire format tolerates it (AIP-180).
- Changing a field's meaning, unit, format, or default; changing an ID or
  timestamp format that clients may have parsed.
- Making an optional request field required, or tightening validation on
  input that used to be accepted — previously valid requests now fail.
- Changing a status code, or changing/removing an error `code`, that
  consumers branch on.
- Changing observable behavior of an existing call — ordering, pagination
  semantics, side effects, idempotency — even with the shape unchanged.
  Semantics are contract too (AIP-180).

## The tie-breaker

When unsure, treat it as breaking. The cost of an unnecessary version is one
extra file served for a window; the cost of a mis-shipped break is every
consumer's pager. You never decide on consumers' behalf that a change is
harmless — the catalog above decides, and silence means breaking.

## Errors are contract; prose is not

Every failure path maps to the canonical envelope with a stable machine
`code`. Clients branch on HTTP status + `code` only. The `message` text is
for humans and may change freely — the moment a client parses a message or
an ID format, that string has become contract you never agreed to serve.
Head this off in the contract doc: status + code are the only stable error
surface.

Under this rule: adding a new `code` for a new failure is additive; changing
which `code` or status an existing failure returns is breaking. No bare
500s, no 200-with-failure-inside — unknown exceptions become the envelope's
500, logged loud.

## Grounding

- AIP-180 Backwards Compatibility — google.aip.dev/180
- AIP-185 Versioning — google.aip.dev/185
