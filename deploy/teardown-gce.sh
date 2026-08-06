#!/usr/bin/env bash
# Tear down the GCP cost components created for the Temporal + Claude stack:
# the VM (its boot disk auto-deletes with it) and the IAP firewall rule.
# Idempotent: skips anything already gone. Mirrors deploy-gce.sh's env vars.
#
# Prereqs:
#   - gcloud authed to the target project (gcloud config set project ...)
#
# Usage:
#   PROJECT=my-proj ZONE=us-central1-a ./deploy/teardown-gce.sh
set -euo pipefail

PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
ZONE="${ZONE:-us-central1-a}"
VM="${VM:-temporal-claude}"
FIREWALL="${FIREWALL:-temporal-claude-iap}"

echo "project=$PROJECT zone=$ZONE vm=$VM firewall=$FIREWALL"

# 1) Delete the VM (the boot disk auto-deletes with the instance).
if gcloud compute instances describe "$VM" --zone "$ZONE" --project "$PROJECT" >/dev/null 2>&1; then
  echo "deleting VM $VM ..."
  gcloud compute instances delete "$VM" --zone "$ZONE" --project "$PROJECT" --quiet
else
  echo "VM $VM already gone"
fi

# 2) Delete the IAP firewall rule (opened for the private-IP tunnel).
if gcloud compute firewall-rules describe "$FIREWALL" --project "$PROJECT" >/dev/null 2>&1; then
  echo "deleting firewall rule $FIREWALL ..."
  gcloud compute firewall-rules delete "$FIREWALL" --project "$PROJECT" --quiet
else
  echo "firewall rule $FIREWALL already gone"
fi

echo "teardown complete — no compute cost components remain for this stack"
