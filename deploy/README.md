# deploy/ — runners, evidence, and the live stack

Every measured claim in the articles traces to a runner + `-results.md`
pair here. Agent-driven runners need the `claude` CLI logged in; the live
scripts start their own local `temporal server start-dev`.

- `stack-up.sh` / `stack-down.sh` — the full local stack: file-backed dev
  server (UI on :8233), one worker per team lane, the poller worker, and
  the schedule that keeps polling the app repo. `--fresh` restarts workers
  so code changes take effect. Teardown lives only in `stack-down.sh`.
- `pilot-issue1.sh` / `pilot-issue1.py` — exactly one issue end to end
  (build -> PR -> review -> merge) with no schedule created.
- Experiment pairs: `flag-block-beg`, `step-gate`, `self-grade`,
  `hitl-live` (+ `hitl-design.md`), `fixloop-live`, `issue-routing-check`,
  plus the cost, heartbeat-recovery, learn-loop, conflict-run, fleet-run,
  and session-learnings evidence files the articles cite.
- `deploy-gce.sh` / `gce-infra-startup.sh` — cloud-run scripts inherited
  from the lab repo ([temporal-claude-demo](https://github.com/thumarrushik/temporal-claude-demo));
  they expect that repo's `Dockerfile`/`docker-compose.yml` and are kept
  here as provenance for the GCP runs the articles mention.
