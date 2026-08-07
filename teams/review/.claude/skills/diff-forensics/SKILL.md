---
name: diff-forensics
description: Read a PR diff for what it does not show — hidden callers, unclaimed behavior deltas, the hunk that should exist but doesn't, unsafe inputs. Use during the inspect phase of every review.
---

# diff-forensics

The diff shows what changed. Defects hide in what changed *because of it* —
and omissions are the hardest defects to find, because you cannot review what
isn't there. Hunt both, read-only: Grep and Read, never Write or Edit.

1. **Map the blast radius before judging the change.** For every edited
   function, signature, constant, and config key, grep for callers and
   importers. Ask of each call site: does the change still hold here? A
   change correct at its definition and wrong at a caller is a blocking issue.
2. **Hunt behavior deltas the description never claimed.** Changed defaults,
   widened or narrowed types, reordered operations, altered error paths
   (raise became return, loud became swallowed), retry/timing changes,
   changed serialization. For each: intended? tested? If the PR description
   does not mention it, treat it as unintended until the code proves intent.
3. **Find the missing hunk.** Ask what SHOULD be in this diff and is not:
   - a test delta for every behavior delta (its absence is a finding by
     default);
   - docs, README, or API contract the change touches;
   - config, env vars, migration, or seed data the code now expects;
   - the remaining call sites of anything renamed or reshaped — grep proves
     completeness; N-1 updated callers is a broken build in hiding.
4. **Run the security pass on every new boundary.**
   - Inputs: anything user- or network-supplied trusted without validation?
   - Secrets: any token, key, or credential literal in the diff? Env only.
   - Paths: user input reaching filesystem paths, shell commands, or SQL
     unsanitized is a blocking issue, no exceptions.
5. **Write forensic findings as evidence**: file:line, what the diff omits or
   silently changes, and what breaks when it does.

## Blocked on sight

- Reviewing only the hunks — no grep for callers of any changed symbol.
- A behavior delta accepted because "tests still pass" when no test
  exercises the delta.
- A schema or contract change with no migration and no note.
- A secret or injection path waved through as "pre-existing pattern".

## Grounding

- SmartBear, "Best Practices for Peer Code Review": omissions are the hardest
  defects to find; checklists exist to catch what isn't there.
- Google eng-practices, "What to look for": every line, and the CL judged in
  the context of the whole system.
- GitHub PR guidance: docs, config, and changelog move with the change.
