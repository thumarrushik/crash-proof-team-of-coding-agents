---
name: service-blueprint
description: Design a new service or major capability as a decision-complete blueprint — bounded-context boundary, one writer per fact, per-dependency failure modes, capacity arithmetic, and alternatives considered — before any contract or code exists; use when a task introduces a new service, splits one, or adds a major capability.
---

# service-blueprint

The blueprint is the design doc a building team implements without the
author in the room. Field-level request/response shapes belong downstream
in CONTRACT.md — the blueprint decides what deserves a contract at all, and
why. Seven sections, written in order, each with a falsifiable bar.

## How to use this skill

1. Read this file, then write the sections in order from
   **[SECTIONS.md](SECTIONS.md)** — every section, no skipping, each
   cleared against its bar.
2. When you reach section 5, open **[FAILURE-MODES.md](FAILURE-MODES.md)**;
   at section 6, open **[CAPACITY.md](CAPACITY.md)**. Load on demand.

## Topic map (load on demand)

| Task | File |
|---|---|
| The seven sections, in order, each with its falsifiable bar | **[SECTIONS.md](SECTIONS.md)** |
| Enumerate down/slow/wrong per dependency; pick a real response | **[FAILURE-MODES.md](FAILURE-MODES.md)** |
| Capacity by arithmetic — the NALSD method, to the first bottleneck | **[CAPACITY.md](CAPACITY.md)** |

## The seven sections in one breath

1. Context and scope; goals and non-goals — non-goals are plausible goals
   deliberately rejected, one line of why each.
2. Boundary as a bounded context — the same word meaning two things is two
   contexts; never share a model across them.
3. Data ownership — one writer per fact; two writers means the boundary is
   wrong: redraw before going on.
4. Contract surface at summary level — operations, events, versions,
   consumers named; field detail is CONTRACT.md's job.
5. Failure modes per dependency — down, slow, wrong; each row with a chosen
   response ("retry" without a budget and give-up behavior is not one).
6. Capacity with arithmetic — numbers to the first bottleneck plus the
   metric that shows it approaching; "should scale fine" is blocked.
7. Alternatives considered — the strongest rejected design and the
   trade-off that killed it; irreversible choices get an ADR ([[adr]]),
   cited by number where the decision appears.

**Blocked on sight:** two writers for one fact, or any consumer reading a
peer's tables · a failure section reading "handle errors gracefully" ·
capacity described in adjectives with no arithmetic · a boundary drawn
along the org chart or tech layers instead of the domain · field-level
payload minutiae crowding out decisions (that's CONTRACT.md).
