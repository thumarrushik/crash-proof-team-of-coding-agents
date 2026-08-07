---
name: self-review
description: Attack your own design artifact before downstream teams inherit its gaps — hunt unstated failure modes, capacity hand-waves, boundary leaks, and ambiguity, then dry-run the doc as each consuming team; Use when declaring any blueprint, contract, or ADR done.
---

# self-review

A bug in a design ships as three teams' bugs, built confidently and in
parallel. The review team exists to catch what a careful author could not
see — not what you didn't look for. Attack the finished artifact
(blueprint, CONTRACT.md, ADR) before declaring done.

## How to use this skill

1. Run the hostile passes in **[PASSES.md](PASSES.md)** over the finished
   artifact, in order — each comes with concrete grep-for phrases; search
   the doc, don't skim it.
2. Then run **[DRY-RUN.md](DRY-RUN.md)** once per consuming team. Done is
   only claimable after both.

## Topic map (load on demand)

| Task | File |
|---|---|
| The hostile passes: failure modes, capacity hand-waves, boundary leaks, ambiguity — with grep-for phrases | **[PASSES.md](PASSES.md)** |
| The per-consuming-team walkthrough: method and per-team checklists | **[DRY-RUN.md](DRY-RUN.md)** |

## The passes in one breath

1. Kill each dependency in your head — down, slow, wrong — and find the
   sentence that says what happens; no sentence means the doc is
   incomplete, not that the failure is unlikely.
2. Grep for adjectives standing where numbers belong; replace each with an
   estimate, its arithmetic, and the verifying metric — or a named
   unknown. An admitted gap is a design input; a hidden one is a landmine.
3. Hunt boundary leaks: two writers for a fact, reads into a peer's
   tables, joins across the boundary in disguise, contract shapes exposing
   internal storage.
4. The two-engineer test: would two engineers, reading independently,
   build identical behavior? Every ambiguity found later is a design bug
   you chose not to find now.
5. Dry-run the doc once per consuming team: can they start without asking
   you anything? Answer every found question in the doc, not in a reply.
6. Record residual unknowns in the doc and REPORT.md — unverified
   assumptions, and deferred decisions with the trigger that forces them.

**Blocked on sight:** "will be defined during implementation" for behavior
the contract owns · a capacity claim with no arithmetic behind it · a
failure mode listed without its contracted response · declaring done
without the per-team dry-run.
