---
name: testing-bar
description: Verification standard for testing-team work. Use when writing, fixing, or reviewing tests and quality gates.
---

Treat tests as executable evidence. Prefer behavior checks over implementation
checks, run the narrow test first, then run the wider suite or build gate that
would catch integration breakage. Report the exact command and result. If a
test is flaky, isolate the cause instead of widening timeouts blindly. Assert
the failure branches (422/404/409/503), not just the happy path — that is where
"nothing faked" is actually proven.
