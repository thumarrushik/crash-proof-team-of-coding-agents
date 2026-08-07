# SECTIONS — the seven, in order, each with a falsifiable bar

Write them in order: each section constrains the next, and a boundary drawn
after the contract surface is a boundary drawn around the code you already
wanted to write. A section passes only if its bar can be checked by someone
who is not you.

## 1. Context and scope; goals and non-goals

Enough context that a reader new to the area understands why this exists
now — the trigger, the surrounding systems, what changes. Goals are stated
so completion is checkable. **Non-goals are plausible goals deliberately
rejected**, one line of why each — the Google design-doc move that saves
the most downstream argument. "Shouldn't crash" is not a non-goal; "no
multi-region in v1: the two consumers are same-region, revisit at the
first cross-region tenant" is.
**Bar:** for every non-goal a reviewer can see the alternative world where
it was a goal, and the stated reason it isn't.

## 2. Boundary as a bounded context

Name the domain terms this service owns and what each means *here* — a
bounded context is a boundary of language before it is a boundary of code
(Evans; Fowler's bliki). The same word meaning two things is two contexts:
"account" in billing and "account" in auth must never share a model. List
the capabilities this service owns, and the near-misses a peer owns, by
name — the near-miss list is what stops scope creep at review time instead
of in a merge conflict.
**Bar:** every domain term in the doc is defined; no term's model is
shared across a boundary; each near-miss names its owning peer.

## 3. Data ownership: one writer per fact

For every entity and derived fact, name the single service that writes it.
Everyone else reads through its API or consumes its events — never its
tables (database-per-service: the schema is private; the contract is the
public surface). If the design needs two writers for one fact, the
boundary is wrong — redraw before going on; every downstream section would
inherit the flaw.
**Bar:** a table of fact → writing service, exactly one writer per row,
and no arrow in any diagram from a consumer into a peer's storage.

## 4. Contract surface, summary level

Operations and events exposed, versioned, with consumers named and the
house envelope assumed ([[lean-service]]). Enough that each consuming team
can say which operations it will call and what events it will consume.
Field-by-field detail is CONTRACT.md's job — payload minutiae here crowd
out the decisions this doc exists to make.
**Bar:** every operation has a named consumer; no field tables.

## 5. Failure modes, per dependency, enumerated

Open **FAILURE-MODES.md** and build the table: for each dependency — down,
slow, wrong — three rows, each with the chosen response.
**Bar:** rows × dependencies complete; every response is one of the
taxonomy's real responses, stated exactly.

## 6. Capacity with arithmetic

Open **CAPACITY.md** and run the NALSD method: expected rates and volumes,
growth assumption, back-of-envelope math down to the first bottleneck, and
the metric that will show that bottleneck approaching.
**Bar:** numbers with arithmetic a reviewer can redo; no adjectives
standing where numbers belong.

## 7. Alternatives considered

The strongest rejected design — the one a smart reviewer might actually
prefer — and the trade-off that killed it. This section is where design
review earns its keep (Google's design-doc practice treats it as the most
important one): a doc with no credible alternative documents a conclusion,
not a decision. Irreversible or constraining choices get an ADR ([[adr]]),
cited by number at the point in this doc where the decision appears.
**Bar:** at least one alternative with a real trade-off; every
irreversible choice carries an ADR number.

## Grounding

- "Design Docs at Google" — industrialempathy.com
- BoundedContext (Evans's DDD; Fowler bliki) — martinfowler.com
- Database-per-service and data ownership — learn.microsoft.com (Azure Architecture Center)
