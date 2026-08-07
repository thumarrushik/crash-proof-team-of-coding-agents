# SECURITY-PASS — every new boundary, every review

Run this pass on every diff that adds or moves a boundary: a new input, a new
external call, a new file or process touch, a new query. Security review is
not a special occasion — it is a standing lane of the inspect phase, and its
findings are blocking by default.

## 1. Inputs — trust nothing you didn't construct

For every value that originates outside this process — request bodies, query
params, headers, file uploads, message payloads, webhook bodies, data read
back from stores that users can write to:

- Is it validated (type, range, length, format) before use?
- Is the validation at the boundary, or scattered hopefully downstream?
- Does the code trust a client-supplied identifier to scope data access
  (tenant IDs, user IDs, object keys) without checking authorization?

Unvalidated external input reaching logic is a finding; reaching a sink
(below) is a blocking one.

## 2. Secrets — env only, never literals

Grep the diff for anything that smells like a credential: `key`, `token`,
`secret`, `password`, `Bearer`, base64 blobs, PEM headers, connection
strings with embedded passwords. Any secret literal in code, test fixtures,
or config committed to the repo is a blocking finding — tests included,
because "test credentials" have a way of being real. Secrets enter through
the environment or a secret store; the diff may reference names, never
values.

Also check the exhaust: does new logging, error text, or debug output print
a secret, a full request, or a token-bearing header?

## 3. Sinks — user input reaching paths, shells, SQL

A blocking issue, no exceptions, when user- or network-supplied data reaches:

- **Filesystem paths** — path joins with user segments (`../` traversal),
  user-named files, archive extraction to user-controlled paths.
- **Shell commands** — string-built commands, `shell=True`, backticks,
  interpolated arguments. Argument arrays and no shell, or it is a finding.
- **SQL** — string-formatted queries of any kind. Parameterized queries
  only; an ORM used with raw fragments counts as raw.

The same shape applies to newer sinks: user input into HTML without
escaping, into deserializers (`pickle`, `yaml.load`), into `eval`/`exec`, or
into an LLM prompt that carries privileged instructions.

## 4. The "pre-existing pattern" refusal

"The code next to it does the same thing" is not a defense — it is a second
finding. A diff that extends an injection-shaped or secret-leaking pattern
gets blocked on its own merits; note the pre-existing instance separately so
it gets an issue of its own. Waving through a vulnerability because it has
company is how the pattern becomes load-bearing.

## Writing security findings

State the boundary, the tainted path from source to sink with file:line at
each hop, and the concrete attack it permits. "This looks unsafe" invites
debate; "user-supplied `filename` reaches `os.path.join` at x.py:41 and
escapes the upload dir via `..`" ends it.

## Grounding

- SmartBear, "Best Practices for Peer Code Review": checklist review catches
  the omission-class defects — missing validation is an omission.
- Google eng-practices, "What to look for": security is part of every
  review's functionality pass, not a separate late gate.
