# BUG-TO-TEST — the repair procedure, red first

A defect repair starts with a red test that reproduces it (Kent Beck,
TDD: By Example). The order is the discipline: reproduce, then fix, then
sweep. Skipping to the fix produces a patch that treats the symptom you
guessed at, verified by nothing.

## 1. Reproduce as a failing test first

Before touching the fix, write a test that fails **on current code, for
the same reason the user saw** — same input shape, same observable wrong
outcome.

- Run it and read the failure. The message must match the report: the
  wrong value, the missing 401, the crash. A test failing on a setup
  error or an import reproduces your typo, not the bug.
- **If you cannot make it fail, you have not found the bug — stop and
  diagnose.** The gap is usually environmental (config, data, timing,
  version) and is itself the finding. A fix written without a red test
  is a guess wearing a diff.
- Reproduce at the outermost boundary that exhibits it (HTTP endpoint,
  CLI, public function), then optionally add a narrower unit test once
  the mechanism is understood — the boundary test is the one that
  guards the promise.

## 2. Fix until green — and everything else stays green

- Minimum change to turn the red test green. Resist the drive-by
  refactor inside a bug fix; it widens the blast radius of review.
- Run the narrow test first, then the **full suite**. A fix that greens
  one test and reds two others has relocated the bug, not removed it.
- Never loosen or delete an existing regression test to let the fix
  pass — that test is a previous bug's return ticket being reissued.
  If it truly asserts an obsolete promise, changing it is a contract
  decision to make explicitly, not a casualty of getting green.

## 3. Sweep the neighborhood

Bugs cluster. The off-by-one you just fixed usually has siblings in the
same function and its copy-paste cousins:

- Apply the testing-bar edge-case taxonomy (EDGE-TAXONOMY.md there) to
  the function that broke: empty/null, boundaries, duplicates, hostile
  strings, concurrency — the class of the bug tells you which rows to
  press hardest.
- Grep for the pattern that broke (`limit +`, the misused API, the
  copy-pasted block) and add the sibling cases where it recurs.
- Each sweep test is a normal behavior test with a full assertion — the
  sweep extends the spec, it does not just pad the incident.

## Grounding

- Kent Beck, Test-Driven Development: By Example — a defect repair
  starts with a red test that reproduces it.
- Martin Fowler, "Self-Testing Code" — the suite you can trust after
  every change is what makes the fix safe to ship.
