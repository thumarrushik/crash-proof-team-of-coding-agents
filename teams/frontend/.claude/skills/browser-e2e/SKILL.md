---
name: browser-e2e
description: Playwright-grounded browser verification — role-based locators, web-first assertions, isolated tests of user stories. Use when proving anything a user clicks, types, or reads.
---

# browser-e2e

Test the way users use it: a user finds a button by its name, not by its
CSS path — and never "waits 2000 ms". One test per user journey you
changed: load -> act -> assert the visible outcome the user came for.

## How to use this skill

1. Read this file before writing or editing any browser test — one test
   per user story, asserting rendered text and state, never internals.
2. Open the topic file for the part you are writing: finding elements,
   asserting outcomes, or keeping tests independent. Load what the test
   needs, not all three.
3. No browser runner in this workspace? Render and assert on output as
   the minimum bar — and say so in the report.

## Topic map (load on demand)

| Task | File |
|---|---|
| Find elements like a user — role-first priority, escape hatches, a11y payoff | **[LOCATORS.md](LOCATORS.md)** |
| Assert outcomes — web-first auto-retrying assertions, sad paths, no clocks | **[ASSERTIONS.md](ASSERTIONS.md)** |
| Keep tests independent — own context, own data, parallel-safe, any order | **[ISOLATION.md](ISOLATION.md)** |

## The rules in one breath

1. Test the story, not the DOM: one test per user journey — load, act,
   assert the visible outcome. Never assert internals or class names.
2. Locate like a user (and like assistive tech): getByRole with accessible
   name first; getByTestId only as a deliberate escape hatch. If getByRole
   cannot find it, fix the markup, not the locator.
3. Web-first assertions only — they auto-retry until the app is ready.
   Wait on conditions, never on clocks.
4. Isolate every test: own browser context, own storage state, own data.
   Every test passes alone, in parallel, and in any order.
5. Assert the sad path: drive the error state and assert the user-facing
   message.
6. Fall back honestly when there is no browser runner — and say so.

**Blocked on sight:** `waitForTimeout` / sleep as synchronization ·
brittle selectors: `.card > div:nth-child(2)`, auto-generated classes ·
tests sharing a login, account, or record that another test mutates ·
retries or widened timeouts papering over flake · asserting implementation
details (store state, class names) instead of what the user sees.
