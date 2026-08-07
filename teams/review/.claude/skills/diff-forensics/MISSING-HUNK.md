# MISSING-HUNK — review what isn't there

Omissions are the hardest defects to find: the diff cannot show you the hunk
that should exist. So you generate the expectation yourself — for each thing
the diff does, ask what else that action obligates — and then check each
obligation off against the diff. This is a checklist discipline precisely
because memory won't surface an absence on its own.

## The four hunts

### 1. A test delta for every behavior delta

If behavior changed and no test changed, the absence is a finding **by
default** — the author must argue it away, not you. Either a new test pins
the new behavior, an existing test was updated (proving it noticed), or the
PR explains why no test can see the change. No third option where the suite
stays green and silent through a behavior change without comment.

### 2. Docs and contracts that the change touches

- README, setup instructions, or usage examples that now lie.
- API contract files, OpenAPI specs, or schema docs for any reshaped
  endpoint or payload.
- Comments and docstrings adjacent to the changed code that the diff just
  made stale — a stale comment ships misinformation at the exact point of
  future edits.

### 3. Config, environment, migrations, seeds

Ask what the new code *expects to exist at runtime* that the old code did
not:

- A config key or env var read by new code — is it declared, defaulted,
  documented, and present in deploy config?
- A schema change — is the migration in the diff? A model edit with no
  migration is a production incident scheduled for deploy time.
- Seed or fixture data the code now assumes.

A schema or contract change with no migration and no note is blocked on
sight.

### 4. The remaining call sites of anything renamed or reshaped

Grep proves completeness; nothing else does. If a symbol was renamed, its
old name must grep to zero (excluding changelogs and deliberate compat
shims). If a signature changed, every caller must appear in the diff or
provably tolerate the change. **N-1 updated callers is a broken build in
hiding** — and in dynamic languages it hides until runtime.

## Working the hunts

1. Build the expectation list from the diff itself: each behavior delta,
   each renamed symbol, each new runtime dependency, each touched contract.
2. Check each expectation against the diff — present, or absent.
3. File each absence as a finding with what is missing, why the diff
   obligates it, and what breaks without it. An omission finding has no
   file:line in the diff — cite the hunk that creates the obligation.

## Grounding

- SmartBear, "Best Practices for Peer Code Review": omissions are the
  hardest defects to find; checklists exist to catch what isn't there.
- GitHub PR guidance: docs, config, and changelog move with the change.
