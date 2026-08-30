# Torn transcript: does resume survive a kill mid-append?

Runner: `deploy/torn-transcript-resume.sh`. Date: 2026-08-30. Model: `haiku`.
No Temporal here: a pure Claude Code CLI parser test.

## The question

The session transcript is an append-only JSONL file. A crash mid-write can leave
a partial final line. The flagship's "What This Doesn't Solve" raised this as
untested: does `--resume` choke on a torn transcript, and does context survive?

## Method

1. Create a session that memorizes two facts (favorite fruit = mango, lucky
   number = 47), no tools.
2. Locate its transcript (`~/.claude/projects/<slug>/<session>.jsonl`, 11 lines).
3. Corrupt it two ways and `--resume` after each, asking (no tools) for the two
   facts. Full context surviving = the parser tolerated the damage.
   - **A, torn last line:** truncate the final JSONL entry to half its bytes,
     no newline or close (143 of 287 bytes kept).
   - **B, appended partial:** keep the whole valid transcript, then append an
     unterminated partial entry (122 bytes, no newline or close).
4. A clean resume (no corruption) is the control.

## Result: resume tolerates both

| resume | exit | is_error | remembered mango + 47 |
|---|---|---|---|
| clean (control) | 0 | false | yes |
| A: torn last line | 0 | false | yes |
| B: appended partial | 0 | false | yes |

Every resume succeeded and answered "mango / 47." The CLI skips a torn or partial
final line and reconstructs context from the intact entries. Session id
`505410a1-0f48-4c77-b76d-385c5ca7704d`.

## Scope and honest edges

- Proved: a torn or partial *final* line does not break resume, and context in
  the earlier intact lines survives. The two facts lived in an earlier turn, so
  tearing the last line could not lose them, which is the realistic case (a torn
  write is content that was never fully committed anyway).
- Not the same as the workspace gap: this tests the transcript's JSONL parse, not
  a completed transcript entry describing a file write the crash cut short. That
  transcript-versus-working-tree mismatch is the filesystem / at-least-once gap
  the flagship still lists, and it is unchanged by this result.
- One model, one CLI version (v2.1.220), a single run per variant. Re-check if
  the transcript format or the parser changes.

## Reproduce

```bash
MODEL=haiku ./deploy/torn-transcript-resume.sh
# → clean / torn-last-line / appended-partial all resume with full context
```
