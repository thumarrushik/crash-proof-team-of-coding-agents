# Issue-routing check — real issues, real router, real phases

`python3 deploy/issue-routing-check.py` against `thumarrushik/linkbox`
(2026-08-06). No Temporal workflow started: the live GitHub issues are routed
through the same `team_for_labels` the poller uses, and each lane's phase list
is read from its own `phase-gate.py` — the list the Stop hook enforces.

```
#  1 OK  -> backend         [Understand > Contract > Implement > Test > Self-review > Report]  Backend: links store with tests
#  2 OK  -> backend         [Understand > Contract > Implement > Test > Self-review > Report]  Export: markdown list of saved links
#  4 OK  -> backend         [Understand > Contract > Implement > Test > Self-review > Report]  Tags on links: add, list, filter
#  5 OK  -> backend         [Understand > Contract > Implement > Test > Self-review > Report]  API: dates must be ISO 8601 (breaking change)
#  6 OK  -> backend         [Understand > Contract > Implement > Test > Self-review > Report]  Track click counts per link (schema change + bac
#  7 OK  -> issues          [Understand > Reproduce > Plan > Implement > Test > Self-review > Report]  Bug: markdown export breaks on ] in link titles
#  8 OK  -> frontend        [Understand > Design > Implement > Verify > Self-review > Report]  Links list page with all four render states
#  9 OK  -> frontend        [Understand > Design > Implement > Verify > Self-review > Report]  Optimistic add-link with rollback
# 10 OK  -> testing         [Understand > Plan > Author > Run > Self-review > Report]  Regression suite for the links store
# 11 OK  -> testing         [Understand > Plan > Author > Run > Self-review > Report]  Flaky: recency test fails near midnight
# 12 OK  -> service-design  [Understand > Blueprint > Decide > Verify > Self-review > Report]  Design: link-preview fetcher service
# 13 OK  -> issues          [Understand > Reproduce > Plan > Implement > Test > Self-review > Report]  Improve duplicate link handling
# 14 OK  -> issues          [Understand > Reproduce > Plan > Implement > Test > Self-review > Report]  README: document how to run the tests

lanes exercised: 5; distinct phase lists among them: 5
ALL PASS (13 issues routed; every lane's steps are its own)
```

Issue #14 carries no team label on purpose — it proves the default route
(`issues`). Five lanes exercised, five distinct phase lists: each kind of work
gets its own kind of steps.
