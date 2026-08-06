# Deploying to GCP

The whole system is one Docker image (`Dockerfile`) driven by
`docker-compose.yml`: Temporal (+ Postgres + UI), one worker per team lane, and
the poller worker. The image bundles **git** (the activity clones the target
repo), **Node** (the Claude Agent SDK's bundled CLI), and **uv**.

## What you must provide

1. **`CLAUDE_CODE_OAUTH_TOKEN`** — headless Claude in a container can't use the
   macOS Keychain, so it needs a token. Generate one from your Claude
   subscription (no API key required):

   ```bash
   claude setup-token          # prints a long-lived CLAUDE_CODE_OAUTH_TOKEN
   ```

   Put it, plus a GitHub token, in a `.env` file at the repo root:

   ```
   CLAUDE_CODE_OAUTH_TOKEN=...
   GITHUB_TOKEN=ghp_...        # repo scope: clone, poll, merge
   ```

   (If `ANTHROPIC_API_KEY` is set it takes precedence over the OAuth token, so
   leave it unset when using subscription auth.)

2. A **GCP project** (`gcloud config set project <id>`) and billing enabled.

## Option A — single VM with docker-compose (self-contained)

Everything (Temporal + workers + poller) runs on one VM. Simplest for a demo.

```bash
# from the repo root, with .env present
PROJECT=$(gcloud config get-value project) ZONE=us-central1-a ./deploy/deploy-gce.sh
```

The VM bootstrap (`deploy/gce-infra-startup.sh`) is idempotent and fully
declarative: it installs Docker, clones the repo, and runs the canonical
`docker-compose.yml`. Two layers, both codified — nothing is hand-run:

```bash
docker compose up -d                     # Temporal + UI + team NAMESPACES (temporal-init); no token
docker compose --profile workers up -d   # + every lane worker + the poller (needs .env token)
```

`temporal-init` creates one namespace per team lane (`backend`, `frontend`,
`testing`, `service-design`, `issues`, `review`) — declaratively, on every
`up`, idempotently. The team workers/poller live behind the `workers` profile so
the control plane comes up without any secret.

Create the poll schedule (after workers are up):

```bash
docker compose run --rm worker-poller src/poller.py --schedule --repo OWNER/NAME --model fable
```

The same compose runs on your laptop:

```bash
docker compose up -d                     # infra + namespaces
docker compose --profile workers up -d   # workers (needs .env)
```

## Option B — Cloud Run workers + Temporal Cloud (managed, scalable)

For production, use **Temporal Cloud** for the server and **Cloud Run** for the
workers (each lane a service with `--min-instances=1` and CPU always allocated,
since workers poll continuously). Sketch:

```bash
REGION=us-central1
REPO=temporal-claude
gcloud artifacts repositories create $REPO --repository-format=docker --location=$REGION
IMAGE=$REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO/worker:latest
gcloud builds submit --tag $IMAGE

# secrets
printf '%s' "$CLAUDE_CODE_OAUTH_TOKEN" | gcloud secrets create claude-oauth-token --data-file=-
printf '%s' "$GITHUB_TOKEN"            | gcloud secrets create github-token       --data-file=-

# one service per lane (+ poller); TEMPORAL_ADDRESS points at your Temporal Cloud endpoint
gcloud run deploy worker-backend --image $IMAGE --region $REGION --no-cpu-throttling \
  --min-instances=1 --max-instances=1 --no-allow-unauthenticated \
  --args=worker.py,--team,backend \
  --set-env-vars TEMPORAL_ADDRESS=<ns>.<acct>.tmprl.cloud:7233,TEMPORAL_NAMESPACE=<ns> \
  --set-secrets CLAUDE_CODE_OAUTH_TOKEN=claude-oauth-token:latest,GITHUB_TOKEN=github-token:latest
# ...repeat for frontend/testing/service-design/review/issues and --poller
```

Temporal Cloud uses mTLS; add the client cert/key (mount them and set the
`Client.connect(..., tls=...)` options) — the one code change deployment needs
beyond `TEMPORAL_ADDRESS`.

## Notes

- `TEMPORAL_ADDRESS` / `TEMPORAL_NAMESPACE` are read from the environment
  (`shared.py`), so the same image runs against localhost, compose, or Temporal
  Cloud with no code change.
- Scale a lane by running more replicas of that worker; Temporal load-balances
  the task queue across them.
- Cost: the agents do real work — size the VM/instances for your throughput and
  set `--max-chunks` / `--max-turns-per-chunk` to bound spend.
