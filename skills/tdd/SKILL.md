---
name: tdd
description: Test-driven workflow for writing new code. Use whenever implementing new functions, commands, or features.
---

For each new piece of behavior:

1. Write the test first and run it to watch it fail.
2. Implement the minimum code to make it pass.
3. Re-run the whole suite before moving to the next behavior.

Never mark work finished with a failing or unrun test suite. A bug fix starts
with a failing test that reproduces the bug, then the fix that turns it green.
