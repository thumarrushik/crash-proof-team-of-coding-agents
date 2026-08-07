# LOCATORS — find elements the way a user does

A user finds the submit button by its visible name; a screen reader finds
it by its accessible role and name. A locator that works any other way is
coupled to markup accidents and breaks on refactors that change nothing
the user can see.

## The priority ladder

Work down this list; each step down is a concession you should be able to
justify in review (Playwright "Best Practices", locator priority):

1. **`getByRole` with accessible name** —
   `page.getByRole('button', { name: 'Save' })`. Resilient to DOM
   restructuring, and doubles as an accessibility assertion.
2. **`getByLabel` / `getByPlaceholder`** — form fields the way users read
   them: `getByLabel('Email address')`.
3. **`getByText`** — non-interactive content the user reads:
   `getByText('No results found')`.
4. **`getByTestId`** — a deliberate escape hatch for elements with no
   user-facing handle (a canvas region, a decorative wrapper you must
   scope into). Adding a `data-testid` is an explicit statement: "no user
   semantics exist here." Say it honestly, not out of convenience.
5. **Raw CSS/XPath** — last resort and a smell. `.card > div:nth-child(2)`
   and auto-generated class names break on every markup or styling change
   and verify nothing about what users experience.

## getByRole failing is a finding, not an obstacle

If `getByRole('button', { name: 'Save' })` cannot find your save button,
the markup has an accessibility bug — a `<div onClick>` instead of a
`<button>`, a missing accessible name, an icon button with no label.
**Fix the markup, not the locator.** Dropping to a test-id here buries a
real defect that assistive-tech users will hit in production. This is the
Testing Library principle operating as a lint: tests that resemble real
use surface real problems.

## Scoping and disambiguation

- Two "Save" buttons? Scope by container first:
  `page.getByRole('dialog').getByRole('button', { name: 'Save' })` —
  still user-shaped ("the Save button in the dialog").
- Prefer `filter({ hasText })` / `filter({ has })` over nth-child
  arithmetic. `.nth(2)` encodes an ordering nobody promised.
- Exact-match names (`{ name: 'Save', exact: true }`) when a substring
  could match a sibling ("Save" vs "Save as draft").

## Grounding

- Playwright docs, "Best Practices" — locator priority, role-first,
  test-ids as escape hatch.
- Testing Library Guiding Principles — "The more your tests resemble the
  way your software is used, the more confidence they can give you."
