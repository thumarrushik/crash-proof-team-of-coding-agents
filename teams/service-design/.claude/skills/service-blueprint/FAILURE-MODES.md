# FAILURE-MODES — down, slow, wrong, per dependency

List every dependency — databases, peer services, external APIs, queues,
object stores. For each, write three rows: **down**, **slow**, **wrong**.
Every row gets exactly one response from the taxonomy below, stated
precisely. An unfilled cell is an undesigned outage.

## The three modes

- **Down** — connection refused, 5xx, DNS gone. The obvious one; still
  needs a stated response per dependency, not a global "we retry".
- **Slow** — the underrated killer. A dependency at 30s is worse than one
  that is down: down fails fast, slow ties up every worker until *your*
  service is down too (the cascading-failure pattern in Google's SRE
  book). Every outbound call therefore has a timeout, and your timeout is
  shorter than your caller's — otherwise the caller gives up first and
  your work is wasted load.
- **Wrong** — responds 200 with bad data: stale, inconsistent, garbage.
  State what validation you apply (schema, bounds, sanity checks) and what
  happens on failure. **Never silently wrong**: a wrong answer served as
  right is the only failure mode with unbounded blast radius.

## The response taxonomy — pick one per row

- **Fail loud.** Propagate as the envelope's 5xx with a machine `code`.
  The default, and the right answer far more often than it feels: honest
  unavailability beats invented data.
- **Degrade.** Serve reduced behavior, *stated exactly*: which fields go
  missing, which feature disappears, what the response says about its own
  degradation. "Degrade gracefully" with no stated degraded behavior is a
  blocked phrase — if you can't write the degraded response down, you
  haven't designed it.
- **Queue.** Accept and defer, with the bound stated (size or age) and the
  behavior when full (reject loud? shed oldest?). An unbounded queue is an
  outage with a delay timer attached.

"Retry" is not a fourth response — it is a *decoration* on one of the
three, and only counts when it states: budget (how many attempts, how much
total time), backoff with jitter, and the terminal behavior when the
budget is spent (which must be one of the three above). Unbudgeted retries
amplify a partial outage into a total one — retry storms are how one slow
dependency takes down a fleet (SRE book, cascading failures).

## Worked example — one dependency, three rows

| billing-service | Response |
|---|---|
| Down | Fail loud: 503, `code=billing_unavailable`; no cached prices — checkout is wrong without live tax |
| Slow | 800ms timeout (caller budget 2s), 2 retries w/ jitter within it, then the down row |
| Wrong | Validate: total ≥ 0, currency in allowlist; on violation fail loud `code=billing_invalid` + alert — never render a negative invoice |

Three sentences per dependency, decided at design time for the price of a
table row — versus the same three decisions made ad hoc at 3am, per
incident, by whoever is paged.

## Bar for the section

Rows × dependencies complete; each response taken from the taxonomy with
its parameters (timeouts, budgets, bounds, degraded shape) written down;
no cell reading "handle errors gracefully".

## Grounding

- "Addressing Cascading Failures" — sre.google/sre-book
- Non-Abstract Large System Design (resilience is designed, not hoped) — sre.google/workbook
