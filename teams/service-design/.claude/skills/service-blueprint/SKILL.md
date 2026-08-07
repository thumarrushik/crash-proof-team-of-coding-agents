---
name: service-blueprint
description: Design a new service or major capability as a decision-complete blueprint — bounded-context boundary, one writer per fact, per-dependency failure modes, capacity arithmetic, and alternatives considered — before any contract or code exists; use when a task introduces a new service, splits one, or adds a major capability.
---

# service-blueprint

The blueprint is the design doc a building team implements without the author
in the room. Field-level request/response shapes belong downstream in
CONTRACT.md — the blueprint decides what deserves a contract at all, and why.
Write these sections in order — each has a falsifiable bar.

1. **Context and scope; goals and non-goals.** Non-goals are plausible goals
   deliberately rejected, one line of why each — not negated platitudes
   ("shouldn't crash" is not a non-goal).
2. **Boundary as a bounded context.** Name the domain terms this service
   owns and what each means *here*. The same word meaning two things is two
   contexts — never share a model across them. List owned capabilities, and
   the near-misses a peer owns, by name.
3. **Data ownership: one writer per fact.** For every entity and derived
   fact, name the single service that writes it. Everyone else reads through
   its API or consumes its events — never its tables. If the design needs
   two writers for one fact, the boundary is wrong: redraw before going on.
4. **Contract surface, summary level.** Operations and events exposed,
   versioned, consumers named, house envelope assumed ([[lean-service]]).
   Field-by-field detail is CONTRACT.md's job, not this doc's.
5. **Failure modes, per dependency, enumerated.** For each dependency: down,
   slow, and wrong — three rows, each with the chosen response: fail loud,
   degrade (state the degraded behavior exactly), or queue (state the bound
   and the behavior when full). "Retry" without a budget and a give-up
   behavior is not a response. Never silently wrong.
6. **Capacity with arithmetic.** Expected request rate and data volume,
   growth assumption, back-of-envelope math down to the first bottleneck,
   and the metric that will show that bottleneck approaching. Numbers, not
   adjectives — "should scale fine" is a blocked phrase.
7. **Alternatives considered.** The strongest rejected design and the
   trade-off that killed it. Irreversible or constraining choices get an
   ADR ([[adr]]), cited by number where the decision appears.

## Blocked on sight

- Two writers for one fact, or any consumer reading a peer's tables.
- A failure section reading "handle errors gracefully".
- Capacity described in adjectives with no arithmetic.
- A boundary drawn along the org chart or tech layers instead of the domain.
- Field-level payload minutiae crowding out decisions (that's CONTRACT.md).

## Grounding

- "Design Docs at Google" — industrialempathy.com
- BoundedContext (Evans's DDD; Fowler bliki) — martinfowler.com
- Non-Abstract Large System Design (NALSD) — sre.google/workbook
- Database-per-service and data ownership — learn.microsoft.com (Azure Architecture Center)
