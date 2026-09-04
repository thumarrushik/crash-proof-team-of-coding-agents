#!/usr/bin/env bash
# Protect the target repo's main branch — the governance the platform itself
# owns, beside the workspace deny floor the harness owns. After this runs,
# NOBODY pushes main directly (agent or harness, admins included): work lands
# by pull request only, force pushes and deletion of main are refused, and the
# harness's merge stays what it already is — an API call on a PR, recorded in
# the durable history. Work branches stay unprotected on purpose: the commit
# mirror and the PR activities push them freely.
#
# Uses a repository RULESET (not classic branch protection) so requiring a PR
# does not force requiring an approving review: review count 0 keeps the
# autonomous loop legal, and raising it to 1 is the production human gate.
#
# Prereqs: gh authed with admin on the target repo.
# Usage:   ./deploy/protect-main.sh <owner/repo> [branch]
set -euo pipefail

REPO="${1:?usage: protect-main.sh <owner/repo> [branch]}"
BRANCH="${2:-main}"
NAME="protect-${BRANCH}"

# Idempotent-ish: replace an existing ruleset of the same name.
EXISTING=$(gh api "/repos/${REPO}/rulesets" --jq \
  ".[] | select(.name == \"${NAME}\") | .id" 2>/dev/null || true)
if [ -n "${EXISTING}" ]; then
  gh api -X DELETE "/repos/${REPO}/rulesets/${EXISTING}" >/dev/null
  echo "replaced existing ruleset ${NAME} (#${EXISTING})"
fi

gh api -X POST "/repos/${REPO}/rulesets" --input - <<JSON >/dev/null
{
  "name": "${NAME}",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": { "include": ["refs/heads/${BRANCH}"], "exclude": [] }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    }
  ]
}
JSON

echo "${REPO}: ${BRANCH} is protected — PRs only, no direct or force pushes."
echo "Production dial: raise required_approving_review_count to 1 for a human gate."
