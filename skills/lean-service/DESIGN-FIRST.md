# DESIGN-FIRST (for big features)

For a substantial new surface — a frontend, a new service, a cross-cutting capability — **design before you
build**. Write the design as markdown in the repo, fix the contracts, then implement against them. Skip this
for a single endpoint or a small change; use it when the work spans many pages/modules or several people (or
agents) will build in parallel.

## The flow

1. **Design through multiple lenses, then synthesize.** Think the feature through from several distinct
   viewpoints — e.g. **product manager** (what problem, what flows, success criteria), **UX designer** (every
   user journey incl. empty/loading/error states, no dead ends), **UI designer** (layout, component
   inventory, visual system), **engineer** (data shapes, API contracts, failure modes), **skeptic** (what
   breaks, what's faked, what's unverifiable). Capture each lens, then **synthesize one coherent design doc** —
   don't ship five disjoint opinions.
2. **Write it to markdown in the repo** (`DESIGN.md` next to the surface, or `docs/`). The doc is the
   contract, reviewable in git — not a throwaway.
3. **Enumerate the pieces explicitly**: every page/route, every component (with its loading / loaded-empty /
   error / populated states), every API call (request + response shape), every nav target. A reader should
   see the whole surface before any code exists.
4. **Fix the contracts before building**: API request/response shapes, the component library's props, the
   route table, the error envelope. Parallel work (or parallel agents) only stays coherent if the seams are
   nailed down first.
5. **Build to the doc, then verify against it** — clear the TESTING.md bar (real infra, fail-loud asserted),
   then walk **every line of the design / PRD** and confirm the built thing matches: each page renders, each
   button works, each flow completes, each error surfaces. Nothing faked, no dead ends.

## What a good design doc pins down

- **Flows** — each user journey end to end, including the empty, loading, and error states (not just the
  happy path). Every nav target resolves to a real route or an explicit provision/empty state.
- **Component inventory** — layout, primitives, data-display, feedback, composites; each with its four states.
- **Route/page table** — every URL, its guard (tenancy/auth), what it renders, where it links.
- **API contracts** — every call's request + response shape and its fail-loud cases (the codes/statuses it
  surfaces). Verify field names against the **real** payload; don't assume.
- **Visual system** — tokens (color/spacing/type), so the build is consistent and not re-litigated per page.

## Building it in parallel (optional)

A large design decomposes cleanly: once the contracts are fixed, pages/modules are independent. You can fan
the build out (e.g. one agent per page against the shared component library + API client), then do one
integration pass — build, wire, and run the full e2e suite. This only works because step 4 fixed the seams;
without fixed contracts, parallel builds diverge. See the workflow patterns in the Workflow tool for fan-out.

## The bar still applies

Design-first does not relax anything in HARD-RULES.md or TESTING.md — it front-loads the thinking so the
build is coherent. The feature isn't done until every line of the design/PRD is satisfied and verified
against real infrastructure, with the fail-loud paths asserted.
