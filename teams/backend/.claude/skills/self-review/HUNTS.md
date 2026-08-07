# HUNTS — the ordered passes, with grep recipes

Run on the final diff, in order. Every hunt is a search you execute, not a
memory you consult — Google's review guidance says look at every line and
think about the context the diff doesn't show; these greps are how.

## 1. Callers

For every function, endpoint, or shape whose signature or semantics
changed, enumerate the change surface, then grep every call site:

    git diff main --name-only            # what moved
    git diff main -U0 | grep '^[-+]def\|^[-+].*route\|^[-+].*class '

- Changed symbol: `grep -rn "symbol_name" --include="*.py" .`
- Changed route: `grep -rn "/v0/things" .` across this service, sibling
  services, and the frontend tree.
- Changed/renamed JSON field: grep it *as a string* — `grep -rn
  '"field_name"' .` plus the frontend's `src/` — serializers and TS types
  don't share a symbol table with Python.

Every caller found is updated in this diff, or the change is reclassified
as a contract change and put through [[api-contracts]]. Zero hits on a
served field is not proof — check the contract doc before believing it.

## 2. Error paths

Walk each new branch's failure side to its end: every one must land in the
canonical envelope with a real `code`. Then hunt swallows in the diff:

    git diff main | grep -n 'except\|catch'
    grep -rn 'except Exception\|except:' --include="*.py" <changed files>
    grep -rn 'pass$\|return None\|return \[\]\|return {}' # inside excepts
    git diff main | grep -in 'log.*error' # log-and-continue candidates

A broad except that logs and returns a default is the silent fallback —
the house's number-one blocked pattern. Fail loud or map to the envelope.

## 3. Query and perf edges

- N+1: any query or HTTP call inside a loop — read every `for` in the
  diff and look one level into what it calls.
- Bounds: any list read without pagination or LIMIT — `git diff main |
  grep -n '\.all()\|SELECT'` and check each for a bound.
- Indexes: a new filter/order predicate on a large table needs an index —
  if none exists, the pairing migration belongs in this diff.
- Walk each new path at 0 rows (empty-state correctness), 1 row, and a
  million rows (latency, memory, payload size).

## 4. Tenant scope

Every new or changed query is tenant-scoped. Fetching by bare ID is a
cross-tenant read even when the ID "couldn't be guessed":

    git diff main | grep -n 'get(\|filter(\|where\|SELECT'

For each hit, find the tenant predicate in the same statement or the
scoped-session mechanism around it ([[lean-service]] TENANCY.md). Missing
scope is a blocker, not a nit. (Why it matters: SECURITY-PASS.md, BOLA.)

## 5. Migration pairing

Code that reads a new column, table, or seed ships with its migration in
the same diff — on the rail, idempotent, numbered after head, never ad-hoc
DDL. Grep the diff for new identifiers and confirm each appears in a
migration file in this same diff. Then check both deploy orders: old code
on the new schema, and new code before the migration runs, must both
survive (the expand-contract invariant from [[data-migrations]]).

## 6. Leftovers and scope

Only intended files changed. Hunt:

    git status --short                   # scratch files
    git diff main | grep -n 'print(\|console\.log\|debugger\|breakpoint()'
    git diff main | grep -n 'TODO\|FIXME\|XXX\|HACK'
    git diff main | grep -n '^+\s*#.*=\|^+\s*//' # commented-out code

No debug prints, no commented-out code, no "while I was here" refactors —
unrelated improvements go in their own diff.

## Close out

Run the full suite on the final state of the branch and read the output —
counts, failures, and skips (a skip spike is a red flag, not a pass).
Record anything you could not verify in REPORT.md as residual risk.

## Grounding

- "What to look for in a code review" — google.github.io/eng-practices
