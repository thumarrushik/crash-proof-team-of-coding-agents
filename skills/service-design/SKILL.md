---
name: service-design
description: How the service-design team works a task in the multi-team delivery pipeline (service-design → backend → frontend → testing → review → issues) — turn ambiguous product intent into a small, implementable contract (user + job-to-be-done, service boundary, data contract with a single error envelope, enumerated failure modes, verifiable success metric) written as a CONTRACT.md that the backend, frontend, and testing teams build against in parallel without asking questions. Use when working any service-design or team-service-design issue.
---

# service-design

The service-design team sits **upstream of everyone**. Its output is the CONTRACT — the one document
the backend, frontend, and testing teams build against independently and in parallel. Get the contract
wrong or leave it ambiguous, and every downstream team builds the wrong thing, confidently.

## The steps

Work every service-design issue in this order. Don't reorder, don't skip.

1. **Name the user, the job-to-be-done, and the workflow.** Who calls this service (end user, another
   service, an operator), what they are trying to accomplish, and the end-to-end workflow step by step —
   including where this service enters and exits it. If you can't name the user, stop: the issue is not
   ready to design.
2. **Define the service boundary.** Explicitly list what is **in scope** (the capabilities this service
   owns) and what is **out of scope** (owned by a peer, deferred, or deliberately excluded). One sentence
   per exclusion saying *why* — the boundary is what stops scope creep downstream.
3. **Define the data contract.** Every operation's request and response shape, field by field: names,
   types, required/optional, enums with all their values, and formats (IDs, timestamps, pagination).
   Routes are versioned (`/v0/...`). Errors use **one single error envelope** —
   `{data: …}` or `{error: {code, message, field, component}}` — no per-endpoint error shapes.
4. **Enumerate failure modes and their exact responses.** For each operation: what can go wrong
   (bad input, missing entity, conflict/duplicate, dependency down, unauthorized) and the exact
   response — status code, error `code`, and which `field`/`component` the envelope names. If a
   failure mode has no contracted response, downstream teams will each invent a different one.
5. **State the success metric and how it's verified.** One concrete, checkable statement of what
   "this service works" means (e.g. "a created order is retrievable by ID within the same request
   cycle and appears in the list endpoint") — phrased so the testing team can turn it into an
   assertion, not a vibe.
6. **Write it as a contract doc (CONTRACT.md).** Everything above goes into one markdown file in the
   repo, next to the service (or `docs/`). The bar: **unambiguous** — two engineers reading it
   independently would build the same thing. Concrete example payloads for every operation, happy
   path and error. No "TBD", no "probably", no prose where a table or example payload would do.
7. **Spell out what EACH downstream team needs from the contract.** End the doc with a per-team
   section — backend, frontend, testing (see below) — so the dependent issues can be unblocked the
   moment the contract lands, without anyone re-reading the whole doc to find their part.

## Hand-off to the teams

Dependent issues **stay blocked until the contract lands** in the repo. Each team starts from:

- **Backend** — the route table (versioned paths + methods), request/response shapes field-by-field,
  the error envelope with per-failure status codes, and the service boundary (what NOT to build).
- **Frontend** — the same shapes as concrete example payloads (populated, empty, and error), the
  enums to render, and which error `code`s the UI must surface to the user versus retry.
- **Testing** — the success metric as a verifiable statement, the enumerated failure modes with their
  exact contracted responses, and the example payloads to assert against, field-for-field.

If a downstream team finds an ambiguity, that's a service-design bug: fix the contract, don't let
teams patch around it with local interpretations.

## Definition of done

- [ ] User, job-to-be-done, and end-to-end workflow are named — no anonymous "the user".
- [ ] Service boundary written: in-scope list and out-of-scope list, each exclusion justified.
- [ ] Data contract complete: every operation's request/response shapes, types, enums, versioned
      routes, and the single error envelope.
- [ ] Every failure mode enumerated with its exact response (status, code, field/component).
- [ ] Success metric stated and phrased so the testing team can verify it mechanically.
- [ ] Two engineers reading the contract independently would build the same thing.
- [ ] Per-team downstream needs (backend/frontend/testing) listed so dependent issues unblock.
- [ ] CONTRACT.md written to the repo — the doc is the deliverable, not a chat summary.
- [ ] No invented architecture: the contract pins behavior and shapes, not the implementation.
