---
name: self-review
description: Review your OWN work as a skeptical reviewer before declaring done — re-read the full diff as a stranger would, confirm only intended files changed (no scratch files, debug prints, or secrets), run the tests yourself and read the results, probe the failure/edge paths, check the task's definition of done, and record residual risk in REPORT.md — so the review team doesn't have to catch what you should have. Use before finishing any task, on every team.
---

# self-review

The last step of every task is a review you run on yourself, in the mindset of the most skeptical
reviewer on the team. The pipeline has a review team, but their job is to catch what a careful
author *couldn't* see — not what you didn't bother to look at. Anything on this list that reaches
review is a defect in your process, not theirs.

## The pass

Run these in order, before declaring done. Actually do each one — don't mentally check them off.

1. **Re-read your full diff as if reviewing a stranger's PR.** `git diff` the whole branch, top to
   bottom. Two questions, both must be yes: does it do what the issue asked, and does it do
   *nothing* the issue didn't ask? Drive-by refactors, "while I'm here" fixes, and speculative
   generality all fail the second question — pull them out.
2. **Confirm you changed ONLY the intended files.** Check `git status` and the diff's file list for
   scratch/workspace files, debug prints or leftover logging, commented-out code, and anything
   resembling a secret, token, or credential. If a file's presence in the diff needs an
   explanation, either write that explanation in REPORT.md or remove the file.
3. **Run the tests yourself and read the result.** Not "they should pass" — run the relevant
   suite(s) now, on the final state of the branch, and read the output: counts, failures, and
   especially skips. A large skip count is a red flag, not a pass. Never declare done from an
   assumed or remembered test run.
4. **Check the failure and edge paths, not just the happy path.** Invalid input, missing resource,
   empty result, unavailable dependency — do they fail loud with the contracted error, or fall
   through to something silent and fake? The happy path is where bugs hide least; a reviewer will
   go straight for the edges, so go there first.
5. **Verify you met the task's definition of done.** Re-read the issue (and the contract, if there
   is one) line by line against your diff. Every stated requirement is either satisfied or
   explicitly flagged as out of scope — "mostly done" is not a state.
6. **Write down residual risk in REPORT.md.** Anything you couldn't verify (a suite you couldn't
   run, an environment you couldn't reach, an assumption you couldn't test), plus known limitations
   and follow-ups. An honestly flagged gap is fine; a silently hidden one is the failure mode this
   skill exists to prevent.

## Definition of done

- [ ] Full diff re-read end to end; it does what the issue asked and nothing it didn't.
- [ ] Only intended files changed — no scratch files, debug prints, commented-out code, or secrets.
- [ ] Tests run by you, on the final branch state, output actually read; skips investigated.
- [ ] Failure/edge paths exercised and failing loud, not just the happy path.
- [ ] Every line of the task's definition of done is satisfied or explicitly flagged.
- [ ] REPORT.md records residual risk and everything you couldn't verify.
