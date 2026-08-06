#!/bin/bash
# Canonical VM bootstrap — everything the VM runs comes from committed files.
# Idempotent: safe to re-run. Installs Docker (once), then brings up the repo's
# docker-compose.yml infra profile: Temporal (+ Postgres + UI) and temporal-init,
# which declaratively creates one namespace per team lane. No secrets needed for
# the control plane; workers (the `workers` profile) are enabled separately with
# a .env (see deploy/README.md).
set -e
export DEBIAN_FRONTEND=noninteractive
REPO_URL="${REPO_URL:-https://github.com/thumarrushik/temporal-claude-demo.git}"

if ! command -v docker >/dev/null 2>&1; then
  apt-get update
  apt-get install -y docker.io docker-compose-v2 git
  systemctl enable --now docker
fi

# Retire any earlier ad-hoc inline stack.
[ -f /opt/temporal/docker-compose.yml ] && (cd /opt/temporal && docker compose down 2>/dev/null || true)

# Bring up the canonical stack from the repo.
if [ -d /opt/app/.git ]; then
  git -C /opt/app fetch --depth 1 origin main && git -C /opt/app reset --hard origin/main
else
  rm -rf /opt/app && git clone --depth 1 "$REPO_URL" /opt/app
fi
cd /opt/app
docker compose up -d          # infra + temporal-init (team namespaces)
echo "infra up; namespaces initialized by temporal-init"
