# PROPERTIES — laws over examples for structured inputs

Where the input domain is structured — parsers, serializers, validators,
calculations, converters — example tests sample a handful of points from
a space with millions of corners. A property states a law that must hold
for ALL inputs and lets the framework (Hypothesis, fast-check) hunt the
corners for you. Example-only coverage of such a domain is blocked on
sight in this lane.

## The three property shapes

Almost every useful property is one of these:

1. **Roundtrip:** `decode(encode(x)) == x` for all x. The workhorse for
   serializers, parsers/printers, converters, ORM save/load. Also the
   asymmetric variants: `normalize(normalize(x)) == normalize(x)`
   (idempotence), `parse(render(parse(s))) == parse(s)`.
2. **Invariant:** a fact preserved by the operation — sort preserves
   length and multiset of elements; a money transfer conserves the
   total; a filter's output is a subset; output ordering is
   monotonic. State the invariant, not the full output.
3. **Oracle:** compare against an independent reference — the brute-
   force O(n²) version, the standard library's implementation, the
   previous system. `fast_path(x) == slow_obvious_path(x)` for all x is
   a complete spec wherever an oracle exists.

If none of the three fits, you can still property-test the contract's
edges: "never throws for any valid input", "always terminates", "output
always validates against the schema".

## Strategies: generate the whole domain, not the comfortable middle

- Build generators (`@given` strategies, fast-check arbitraries) from
  the input's real shape: optional fields sometimes absent, strings
  from full unicode not `[a-z]`, collections including empty and huge,
  numbers including 0, negatives, extremes.
- Constrain with `assume`/filters only for genuinely invalid inputs —
  over-constrained strategies quietly shrink the tested domain back to
  the examples you would have written by hand.
- The edge taxonomy (testing-bar EDGE-TAXONOMY.md) is the review
  checklist for a strategy: could this generator ever produce an empty
  string? A duplicate? If not, why not?

## Shrinking and seeds — make every failure a deliverable

- When a property fails, the framework shrinks to a **minimal
  counterexample** — that minimal case is the bug report. Paste it into
  the failure narrative and pin it as a permanent example test
  (regression-suite: the return-ticket rule applies to property
  finds too).
- **Record the failing seed** so the repro is deterministic: Hypothesis
  prints it (and its database replays it); fast-check reports
  `{seed, path}`. A property failure without its seed is a flake report
  (flaky-hunt TAXONOMY.md, randomness class); with the seed it is a
  reproducible red test.
- Keep runs deterministic in CI by replaying stored failures first;
  never "fix" a property failure by re-running until green.

## Grounding

- Hypothesis documentation — @given strategies, invariant and roundtrip
  properties, shrinking to minimal counterexamples, the example
  database.
- fast-check documentation — arbitraries, seed/path reproduction.
- Claessen & Hughes, "QuickCheck" (ICFP 2000) — the origin of
  property-based testing and shrinking.
