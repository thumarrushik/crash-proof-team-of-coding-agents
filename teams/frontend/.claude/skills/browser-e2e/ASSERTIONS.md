# ASSERTIONS — wait on conditions, never on clocks

Google's flaky-test analyses put async waiting as the dominant cause of
flake: the test asserts before the app is ready, or sleeps long enough to
pass on this machine and fail on CI. Web-first assertions dissolve the
whole class — they retry the check until it holds or times out.

## Web-first or nothing

`await expect(locator).toBeVisible()`, `.toHaveText()`, `.toHaveValue()`,
`.toHaveURL()`, `.toHaveCount()` auto-retry. The assertion IS the wait —
no separate synchronization step exists or is needed.

- Never `waitForTimeout` / sleep as synchronization. A sleep is a guess
  about timing; every guess is wrong somewhere. If you feel the need for
  one, you are missing the condition to assert — find it.
- Don't pre-wait then assert (`waitForSelector` + `expect`) — the
  retrying assertion is both, in one line, without the race between them.
- Non-locator checks use `expect.poll()` / `expect().toPass()` so they
  retry too; a bare `expect(await page.title())...` is a one-shot race.

## Assert the outcome the user came for

Each journey ends by asserting what the user can see changed: the
confirmation text, the new row in the table, the URL after redirect, the
disabled state of the submitted button. Not: store contents, emitted
actions, class names, or network internals — those pass while the screen
is broken, and fail while the screen is fine.

Assert enough to pin the outcome, not the whole page: `toHaveText` on the
result region beats a full-page screenshot diff that fails on every
unrelated pixel.

## Assert the sad path

When the story has an error state, drive it and assert the user-facing
message:

- Force the failure deterministically — `page.route()` the API call to
  return 500 (or abort) so the error branch runs on every test run, not
  only when the backend cooperates.
- Assert the message the user reads and the way out (retry button
  visible, input preserved) — not merely "an error element exists".
- One sad-path test per designed error surface of the journey; empty
  state is its own branch, asserted with its designed content.

## Timeouts are a bar, not a dial

The default assertion timeout is the flake alarm. When a test misses it,
find what the app is actually waiting on — do not widen the timeout or
wrap in retries. A widened timeout papers over the same race, and a
passing retry converts a real signal into noise (see the flaky-hunt
skill's territory once it is in a suite).

## Grounding

- Playwright docs, "Best Practices" — web-first assertions; test
  user-visible behavior.
- Google Testing Blog flaky-test analyses — async waiting as the dominant
  flake cause; hence conditions, never clocks.
