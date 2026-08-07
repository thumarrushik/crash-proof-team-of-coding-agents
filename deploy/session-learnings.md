# Session learnings — the fleet's corpus, mined (2026-08-07)

The corpus loop, run on the fleet: every workspace's audit logs, rule flags,
task boards, and usage records read together, and each finding landed as a
same-day commit. 37 workspaces, 60 chunks.

## The numbers

- **Total fleet cost: $53.53** (60 chunks, mean $0.89) — thirteen issues
  built, reviewed, conflict-resolved, and merged for about the price of
  lunch.
- **Cache economics at scale: 38,582,090 cache-read tokens vs 9,819 fresh
  input tokens.** The resume architecture pays for itself: essentially the
  whole conversation context rides the cache on every chunk.
- **Rule flags: 36 `redundant_orientation_ls`** across five lanes (frontend
  worst at 12) despite every mandate's written efficiency rule — beg loses
  at fleet scale exactly as it lost in the measured experiment; the flags
  caught every instance.
- **22 `review_lane_edits_code` flags — all false positives**: every one was
  the review lane writing its mandated REPORT.md.
- **37/37 workspaces show exactly one phase-gate block**: agents return the
  structured report and try to stop one beat before marking the final task
  completed.

## The fixes (landed the same day)

1. **Gate v3**: a returned structured report satisfies the Report phase —
   the universal +1 block (and its interference with the structured-output
   handshake) is gone. Pinned by test.
2. **`exclude_paths` on tool_use rules**: review's rule now carves out
   REPORT.md, so its flag stream contains only real violations. Pinned by
   test.
3. Mandate efficiency rules stay as written — the ls-flag data re-confirms
   flags-catch/prompts-don't; the block experiment already showed why we
   do not deny mid-flight.

## The corpus shipment

The July learn-loop shipped session corpora to
`gs://temporal-claude-corpus-213476/`. That bucket belongs to a different
Google account than the one currently active locally (403 on list). This
fleet's corpus is packaged at `deploy/fleet-corpus-2026-08-06.tar.gz`
(gitignored; audit logs, rule flags, usage logs, reports, exported
transcripts — no cloned repos). To ship it once on the owning account:

```bash
gcloud auth login <owning-account>
gsutil cp deploy/fleet-corpus-2026-08-06.tar.gz \
  gs://temporal-claude-corpus-213476/fleet-2026-08-06/
```
