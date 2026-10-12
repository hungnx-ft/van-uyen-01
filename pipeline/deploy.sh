#!/usr/bin/env bash
# Deploy origin/main to production.
#   pipeline/deploy.sh          only rebuilds/restarts what changed since the last deploy
#   pipeline/deploy.sh --full   reinstalls deps, backs up + migrates, rebuilds and restarts everything
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

FULL=""
case "${1:-}" in
  "") ;;
  --full) FULL=--full ;;
  *) echo "Usage: $0 [--full]" >&2; exit 2 ;;
esac

git fetch -q origin "$DEPLOY_BRANCH"
echo "==> Deploying $(git log -1 --format='%h %s' "origin/$DEPLOY_BRANCH") to $DEPLOY_HOST"

# The server pulls first, then runs the remote script from the pulled commit,
# so the deploy steps always match the code being deployed.
remote bash -s -- "$DEPLOY_BRANCH" "$FULL" <<'REMOTE'
set -euo pipefail
branch=$1 full=${2:-} repo=/opt/van-uyen/app
exec 9>/run/vanuyen-deploy.lock
flock -n 9 || { echo "Another deploy is running." >&2; exit 1; }
cd "$repo"
old=$(sudo -u vanuyen git rev-parse HEAD)
sudo -u vanuyen git fetch -q origin "$branch"
sudo -u vanuyen git checkout -q "$branch"
sudo -u vanuyen git merge -q --ff-only "origin/$branch"
bash "$repo/pipeline/remote/deploy.sh" "$old" $full
REMOTE

"$(dirname "$0")/check.sh"
