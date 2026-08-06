#!/usr/bin/env bash
# Deploy the whole stack (Temporal + workers + poller) to a single GCP VM via
# docker-compose. Idempotent-ish: re-running re-copies the repo and restarts.
#
# Prereqs:
#   - gcloud authed to the target project (gcloud config set project ...)
#   - a .env file in the repo root with CLAUDE_CODE_OAUTH_TOKEN and GITHUB_TOKEN
#
# Usage:
#   PROJECT=my-proj ZONE=us-central1-a ./deploy/deploy-gce.sh
set -euo pipefail

PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
ZONE="${ZONE:-us-central1-a}"
VM="${VM:-temporal-claude}"
MACHINE="${MACHINE:-e2-standard-4}"      # 4 vCPU / 16GB — headroom for agents
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

[ -f "$REPO_ROOT/.env" ] || { echo "ERROR: create $REPO_ROOT/.env (CLAUDE_CODE_OAUTH_TOKEN, GITHUB_TOKEN)"; exit 1; }

echo "project=$PROJECT zone=$ZONE vm=$VM machine=$MACHINE"

# 1) Create the VM (Ubuntu + Docker) if it doesn't exist.
if ! gcloud compute instances describe "$VM" --zone "$ZONE" --project "$PROJECT" >/dev/null 2>&1; then
  echo "creating VM $VM ..."
  gcloud compute instances create "$VM" \
    --project "$PROJECT" --zone "$ZONE" --machine-type "$MACHINE" \
    --image-family ubuntu-2404-lts-amd64 --image-project ubuntu-os-cloud \
    --boot-disk-size 50GB \
    --metadata startup-script='#!/bin/bash
      set -e
      apt-get update && apt-get install -y docker.io docker-compose-plugin git
      systemctl enable --now docker'
fi

# 1b) Wait until docker is actually installed AND running — poll, don't guess.
# The startup-script installs docker asynchronously (and only on first create),
# so a fixed sleep races it; this also covers re-runs on an existing VM.
echo "waiting for docker to be ready on the VM ..."
for i in $(seq 1 40); do
  if gcloud compute ssh "$VM" --zone "$ZONE" --project "$PROJECT" \
       --command 'command -v docker >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1' >/dev/null 2>&1; then
    echo "docker ready (after ~$((i*15))s)"; break
  fi
  [ "$i" = 40 ] && { echo "ERROR: docker not ready after ~10 min"; exit 1; }
  sleep 15
done

# 2) Copy the repo (incl. .env) to the VM.
echo "copying repo to VM ..."
TMP_TAR=$(mktemp)
git -C "$REPO_ROOT" archive --format=tar HEAD > "$TMP_TAR"
gcloud compute scp "$TMP_TAR" "$VM:/tmp/app.tar" --zone "$ZONE" --project "$PROJECT"
gcloud compute scp "$REPO_ROOT/.env" "$VM:/tmp/.env" --zone "$ZONE" --project "$PROJECT"

# 3) Unpack, then build + start the stack.
gcloud compute ssh "$VM" --zone "$ZONE" --project "$PROJECT" --command '
  set -e
  sudo rm -rf ~/app && mkdir -p ~/app && tar -xf /tmp/app.tar -C ~/app && cp /tmp/.env ~/app/.env
  cd ~/app
  sudo docker compose build
  sudo docker compose up -d
  echo "--- services ---"
  sudo docker compose ps
'

IP=$(gcloud compute instances describe "$VM" --zone "$ZONE" --project "$PROJECT" \
       --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo ""
echo "Deployed. Temporal UI: http://$IP:8233  (open the firewall for tcp:8233 if needed)"
echo "Create the poll schedule on the VM:"
echo "  gcloud compute ssh $VM --zone $ZONE --command 'cd ~/app && sudo docker compose run --rm worker-poller src/poller.py --schedule --repo OWNER/NAME --model fable'"
