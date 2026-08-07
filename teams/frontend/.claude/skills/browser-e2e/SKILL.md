---
name: browser-e2e
description: Playwright-grounded browser verification — role-based locators, web-first assertions, isolated tests of user stories. Use when proving anything a user clicks, types, or reads.
---

# browser-e2e

Test the way users use it: a user finds a button by its name, not by its CSS
path — and never "waits 2000 ms".

## Phases — in order

1. **Test the story, not the DOM.** One test per user journey you changed:
   load -> act (click, type) -> assert the visible outcome the user came
   for. Assert rendered text and state, never internals or class names.
2. **Locate like a user (and like assistive tech).** Priority: getByRole
   with accessible name -> getByLabel / getByPlaceholder -> getByText ->
   getByTestId as a deliberate escape hatch. Raw CSS/XPath chains are a
   last resort and a smell. If getByRole cannot find it, the markup has an
   accessibility bug — fix the markup, not the locator.
3. **Web-first assertions only.** `await expect(locator).toBeVisible()`,
   `.toHaveText()`, `.toHaveURL()` auto-retry until the app is ready.
   Never `waitForTimeout` or sleeps; wait on conditions, not clocks.
4. **Isolate every test.** Own browser context, own storage state, own data
   (seeded via API or fixtures, not via other tests' leftovers). Every test
   must pass alone, in parallel, and in any order.
5. **Assert the sad path.** When the story has an error state, drive it
   (route/mock the failing response) and assert the user-facing message.
6. **Fall back honestly.** No browser runner in this workspace? Render and
   assert on output as the minimum bar — and say so in the report.

## Blocked on sight

- `waitForTimeout` / sleep as synchronization.
- Brittle selectors: `.card > div:nth-child(2)`, auto-generated classes.
- Tests sharing a login, account, or record that another test mutates.
- Retries or widened timeouts papering over flake.
- Asserting implementation details (store state, class names) instead of
  what the user sees.

## Grounding

- Playwright docs, "Best Practices": test user-visible behavior, web-first
  assertions, locator priority (role first), test isolation.
- Testing Library Guiding Principles: "The more your tests resemble the way
  your software is used, the more confidence they can give you."
- Google Testing Blog flaky-test analyses: async waiting is the dominant
  flake cause — hence conditions, never clocks.
