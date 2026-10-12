#!/usr/bin/env bash
# One-time: install this machine's SSH key on the server so deploys need no password.
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

key="$HOME/.ssh/id_ed25519"
[[ -f $key ]] || ssh-keygen -t ed25519 -f "$key" -N "" -C "$(whoami)@$(hostname -s) deploy"
ssh-copy-id -i "$key.pub" "${SSH_OPTS[@]}" "$DEPLOY_USER@$DEPLOY_HOST"
ssh -o BatchMode=yes "${SSH_OPTS[@]}" "$DEPLOY_USER@$DEPLOY_HOST" true && echo "SSH key login works."
