---
name: diff-forensics
description: Read a PR diff for what it does not show — hidden callers, unclaimed behavior deltas, the hunk that should exist but doesn't, unsafe inputs. Use during the inspect phase of every review.
---

# diff-forensics

The diff shows what changed. Defects hide in what changed *because of it* —
and omissions are the hardest defects to find, because you cannot review what
isn't there. Hunt both, read-only: Grep and Read, never Write or Edit.

## How to use this skill

1. Read this file during the inspect phase of every review, after the first
   pass over the hunks themselves.
2. Open the topic file for the hunt you are running (below). Don't read all
   of them at once — load what the diff demands.

## Topic map (load on demand)

| Task | File |
|---|---|
| Map callers and hunt unclaimed behavior deltas | **[BLAST-RADIUS.md](BLAST-RADIUS.md)** |
| Find what SHOULD be in the diff and is not | **[MISSING-HUNK.md](MISSING-HUNK.md)** |
| Sweep every new boundary: inputs, secrets, injection paths | **[SECURITY-PASS.md](SECURITY-PASS.md)** |

## The rules in one breath

1. Map the blast radius before judging the change: grep every edited symbol
   for callers and importers, and ask of each site whether the change holds.
2. A change correct at its definition and wrong at a caller is a blocking
   issue.
3. Any behavior delta the PR description never claimed is unintended until
   the code proves intent — and untested means unproven.
4. Ask what should be in this diff and is not: test deltas, docs, config,
   migrations, and the N-1 remaining call sites of anything reshaped.
5. Run the security pass on every new boundary — unvalidated input, secret
   literals, user input reaching paths, shells, or SQL.
6. Write forensic findings as evidence: file:line, what the diff omits or
   silently changes, and what breaks when it does.

**Blocked on sight:** reviewing only the hunks — no grep for callers of any
changed symbol · a behavior delta accepted because "tests still pass" when no
test exercises the delta · a schema or contract change with no migration and
no note · a secret or injection path waved through as "pre-existing pattern".
