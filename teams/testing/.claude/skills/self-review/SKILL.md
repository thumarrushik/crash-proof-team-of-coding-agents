---
name: self-review
description: Audit the suite you just wrote as the deliverable it is — every test seen red, assertions that would catch mutants, independence proven, names that read as spec. Use before declaring any testing task done.
---

# self-review (testing lane)

Your diff IS tests, so this review audits evidence quality: a weak suite
ships silent permission for other people's bugs. Audit what you wrote the
way you audited the code it tests.

## How to use this skill

1. Read this file when the suite feels done, before writing REPORT.md.
2. Load the topic file (below) and run its six audits in order over every
   test in the diff — each audit comes with a concrete method; run it,
   don't recall it.

## Topic map (load on demand)

| Task | File |
|---|---|
| Run the six audits: seen-red proof, mutation audit, change-detector hunt, independence proof, names-as-spec, leftovers + final run | **[AUDITS.md](AUDITS.md)** |

## The rules in one breath

1. Prove every new test was seen red — find the transcript moment it
   failed, or make it fail once now. Only-ever-green is unverified
   evidence.
2. Mutation-audit each assertion: name the small code change it would miss;
   if nothing would go red, the assertion is decoration — strengthen it.
3. Hunt your own change-detectors: expected values computed from the code
   under test, restated implementations, private-internal assertions.
4. Prove independence: new tests pass alone, in random order, and twice in
   a row; keep order randomization on where the runner supports it.
5. Read the names as a spec, filed by feature — names alone must teach what
   the system guarantees.
6. Sweep leftovers, then run the full suite as your final action and carry
   that literal result into `tests_passed` — remembered verdicts measured
   wrong 3 in 10 here.

**Blocked on sight:** a test in the diff that was never observed failing ·
a `.only`/focused test or an unexplained skip left in · expected values
derived from the implementation under test · declaring done from a
remembered or assumed run.
