# Deploy target. Override any value with an environment variable of the same name.
DEPLOY_HOST="${DEPLOY_HOST:-103.82.192.19}"
DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
SITE_URL="${SITE_URL:-https://nguvancohang.com}"

SSH_OPTS=(-o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new)

# Uses the SSH key when one is installed (see setup-ssh-key.sh). Otherwise
# DEPLOY_SSH_PASSWORD + sshpass, or an interactive password prompt.
remote() {
  if [[ -n "${DEPLOY_SSH_PASSWORD:-}" ]]; then
    SSHPASS="$DEPLOY_SSH_PASSWORD" sshpass -e ssh "${SSH_OPTS[@]}" "$DEPLOY_USER@$DEPLOY_HOST" "$@"
  else
    ssh "${SSH_OPTS[@]}" "$DEPLOY_USER@$DEPLOY_HOST" "$@"
  fi
}
