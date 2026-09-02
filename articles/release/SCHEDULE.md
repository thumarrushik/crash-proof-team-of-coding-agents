# Serialized release: one article a week, flagship first

Order is the family's own reading order. Dates are planned Mondays after week 1; if a week slips, everything shifts together, the order is what matters.

| week | planned date | article |
|---|---|---|
| 1 | 2026-09-01 | A Crash-Proof Team of Coding Agents (the flagship) |
| 2 | 2026-09-08 | How It's Built |
| 3 | 2026-09-15 | Mechanics Cost Cents, Behavior Costs Dollars |
| 4 | 2026-09-22 | Flag, Block, or Beg |
| 5 | 2026-09-29 | Done Is Not a Claim |
| 6 | 2026-10-06 | The Agent Grades Its Own Homework |
| 7 | 2026-10-13 | The Human Is a Durable Object |

Weekly checklist:

1. If canonicals changed this week: `cd articles/final && ./export-medium.sh` (and re-render the affected PDF).
2. `./stage-release.sh <slug>`; paste `articles/release/<slug>-medium-release.md` into Medium and upload the hero and diagrams by hand as usual.
3. Publish, then add the live URL to `articles/final/published-urls.tsv`.
4. Re-run `./stage-release.sh` for the earlier slugs the script names, and edit those live Medium posts so their links to the new article light up.

The release copies flatten links to not-yet-published siblings into plain text (titles stay, links drop) and point links to already-published siblings at their live URLs. The canonical articles and the plain `-medium.md` exports keep the full cross-links; only the `articles/release/` copies know about the schedule.
