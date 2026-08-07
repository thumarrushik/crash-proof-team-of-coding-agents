---
name: flaky-hunt
description: Diagnose-before-fix workflow for nondeterministic tests, grounded in Google's flaky-test research. Use whenever a test passes sometimes or fails only in CI.
---

# flaky-hunt

Google measured ~1.5% of all test runs flaky, ~16% of tests affected,
and 84% of pass->fail transitions caused by flakes rather than real
breakage. Every tolerated flake trains the team to ignore red. The
workflow is convict, diagnose, deflake, prove — never fix by weakening.

## How to use this skill

1. Read this file whenever a test passes sometimes or fails only in
   CI — before rerunning it into a green you cannot trust.
2. Convict with data first: rerun the suspect at least 10x — alone,
   inside the full suite, and in randomized order; record failure rate
   and conditions before touching anything.
3. Open TAXONOMY.md to pin the named cause; open DEFLAKE.md for the
   cause-matched fix, the proof battery, and quarantine rules.

## Topic map (load on demand)

| Task | File |
|---|---|
| Diagnose to a named cause — the six flake classes with their telltale symptoms | **[TAXONOMY.md](TAXONOMY.md)** |
| Fix by cause, prove with reruns, quarantine with an owner | **[DEFLAKE.md](DEFLAKE.md)** |

## The rules in one breath

1. Convict with data: 10x reruns alone, in-suite, and in randomized
   order — record the rate before touching anything.
2. No fix without a diagnosis: name the cause from the taxonomy (async
   wait, concurrency, order/shared state, time, randomness,
   environment).
3. Deflake by cause, never by assertion — conditions not sleeps, fake
   clocks, seeded randomness, fresh fixtures, real completion signals.
4. Prove the fix: rerun the same 10x-or-more battery; record zero
   failures alongside the diagnosis.
5. Quarantine with an owner when it cannot be fixed now — skip with the
   diagnosis, an owner, and a link. A silent skip or a deleted test is
   a deleted guardrail.

**Blocked on sight:** widening timeouts or tolerances to turn red
green · auto-retries presented as a fix · weakening or removing the
assertion that flaked · `sleep(n)` as synchronization; "fixed" without
recorded reruns.
