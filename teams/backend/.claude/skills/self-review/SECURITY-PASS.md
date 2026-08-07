# SECURITY-PASS — OWASP-grounded checks on the diff

Run over the final diff whenever it touches boundary input, queries, authz,
files, or configuration. Each check maps to an OWASP class; the greps find
candidates — you still read each hit in context.

## Inputs — validate everything that crosses the boundary

Every value from outside — body, path, query, header, cookie, upload — is
validated before use: type, bounds, length, allowlisted values.

- New endpoint params: does each land in a typed, constrained schema, or
  is anything read raw (`request.args`, `request.json[...]`) and used?
- **Mass assignment** (OWASP API3): never bind request JSON straight onto
  a model — grep the diff for dict-splat/`**` into constructors and
  update loops over user-supplied keys; bind through an explicit schema.
- Uploads: size limit, content-type check, and never trust the client
  filename — no path built from user input without normalization
  (`grep -n 'os.path.join\|open(' on changed files`).

## Injection — no strings become code

- SQL: parameterized always. Hunt string-built queries:
  `git diff main | grep -n 'f".*SELECT\|f".*WHERE\|+ *"SELECT\|% *(.*SELECT\|format(.*SELECT'`
- Shell: argument arrays, never concatenated commands:
  `git diff main | grep -n 'subprocess\|os.system\|shell=True'`
- Code: no `eval`/`exec`/`pickle.loads` on anything user-reachable — the
  house rule is safe-AST allowlist ([[lean-service]] LLM.md):
  `git diff main | grep -n 'eval(\|exec(\|pickle.loads'`

## Authorization — object-level, every request

- **BOLA** (OWASP API1, the top API risk): every object access checks the
  requester may reach *that* object. In this house that means tenant
  scoping on every query (HUNTS.md pass 4) — a bare-ID fetch is a
  cross-tenant read regardless of how unguessable the ID looks.
- Function-level (API5): new admin/maintenance/migrate-style endpoints
  gated the same way existing privileged routes are — copy the existing
  guard, don't improvise one.

## Resource consumption (API4)

Unbounded work is a security defect, not just a perf bug: pagination
bounds on list reads, request-size limits on bodies and uploads, timeouts
on every new outbound HTTP call. Grep new client calls for a timeout arg.

## Secrets

None in code, none in logs, none in error responses. Config via env only
([[lean-service]] hard rule).

    git diff main | grep -in 'api_key\|apikey\|secret\|password\|token\s*='
    git diff main | grep -n 'logger.*request\|print(.*request'  # dumped payloads

Watch the second class: logging a whole request/headers object leaks auth
tokens into logs even though no literal secret is in the code. Error
messages returned to clients must not echo internals (connection strings,
file paths, stack traces) — the envelope's `message` stays generic; detail
goes to server logs.

## Close out

Each finding is fixed in this diff or recorded in REPORT.md as an explicit
residual risk with its OWASP class — never silently accepted.

## Grounding

- Secure Code Review Cheat Sheet — cheatsheetseries.owasp.org
- OWASP API Security Top 10 (object-level authz, input validation) — owasp.org
