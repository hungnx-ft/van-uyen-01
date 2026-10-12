#!/usr/bin/env bash
# Runs on the server as root, after pipeline/deploy.sh has pulled the new commit.
#   remote/deploy.sh <previous-commit> [--full]
set -euo pipefail

REPO=/opt/van-uyen/app        # git checkout
SRC=$REPO/app                 # application code inside the checkout
VENV=$REPO/.venv              # kept at the checkout root: its scripts hard-code this path
WEB_ROOT=/var/www/vanuyen-root
BACKUP_DIR=/opt/van-uyen/backups
SERVICES=(vanuyen-api vanuyen-ai-worker)

OLD=$1
FULL=${2:-}
NEW=$(sudo -u vanuyen git -C "$REPO" rev-parse HEAD)
RESTART=""

log() { printf '\n==> %s\n' "$*"; }
as_app() { sudo -u vanuyen "$@"; }
# True when --full was given or any of the paths changed since the previous deploy.
needs() {
  [[ -n $FULL ]] && return 0
  ! as_app git -C "$REPO" diff --quiet "$OLD" "$NEW" -- "$@"
}

log "Commit $(as_app git -C "$REPO" log -1 --format='%h %s')"

# Code lives in app/ since the repo restructure. The app reads .env from its
# working directory, so link it there and point the services at $SRC.
# Both steps are no-ops once done.
if [[ ! -e $SRC/.env ]]; then
  log "Linking $SRC/.env to $REPO/.env"
  ln -s ../.env "$SRC/.env"
  RESTART=1
fi
reload=""
for svc in "${SERVICES[@]}"; do
  dropin=/etc/systemd/system/$svc.service.d/workdir.conf
  want=$'[Service]\nWorkingDirectory='"$SRC"
  if [[ "$(cat "$dropin" 2>/dev/null)" != "$want" ]]; then
    mkdir -p "$(dirname "$dropin")"
    printf '%s\n' "$want" >"$dropin"
    reload=1
  fi
done
if [[ -n $reload ]]; then
  log "Updated systemd WorkingDirectory to $SRC"
  systemctl daemon-reload
  RESTART=1
fi

if needs app/requirements.txt app/vendor; then
  log "Installing Python dependencies"
  if [[ ! -d $SRC/vendor/vanuyen-wheelhouse ]]; then
    (cd "$SRC/vendor" && sha256sum -c --quiet SHA256SUMS)
    as_app tar -xzf "$SRC/vendor/python-wheels-linux-x86_64-py312.tar.gz" -C "$SRC/vendor"
  fi
  as_app "$VENV/bin/pip" install -q --no-index --find-links "$SRC/vendor/vanuyen-wheelhouse" -r "$SRC/requirements.txt"
  as_app "$VENV/bin/pip" check
  RESTART=1
fi

if needs app/migrations; then
  db=$(sed -n 's#^DATABASE_URL=.*/\([^/?]*\).*#\1#p' "$REPO/.env")
  [[ -n $db ]] || { echo "Cannot read the database name from DATABASE_URL in $REPO/.env" >&2; exit 1; }
  file=$BACKUP_DIR/${db}_$(date +%F_%H%M%S).dump
  log "Backing up database $db to $file"
  install -d -m 700 "$BACKUP_DIR"
  # Root writes the file; postgres only needs to read the database.
  # shellcheck disable=SC2024
  sudo -u postgres pg_dump -Fc "$db" >"$file"
  log "Running migrations"
  (cd "$SRC" && as_app "$VENV/bin/alembic" upgrade head)
  RESTART=1
fi

if needs app/frontend || [[ ! -d $SRC/frontend/.output/public ]]; then
  log "Building frontend"
  cd "$SRC/frontend"
  if needs app/frontend/package-lock.json || [[ ! -d node_modules ]]; then
    as_app npm ci --no-audit --no-fund
  fi
  as_app env NUXT_PUBLIC_API_BASE=/api/v1 npm run generate
  rsync -a --delete .output/public/ "$WEB_ROOT/"
  chown -R root:www-data "$WEB_ROOT"
fi

if needs app/app || [[ -n $RESTART ]]; then
  log "Restarting ${SERVICES[*]}"
  systemctl restart "${SERVICES[@]}"
  for _ in $(seq 1 15); do
    curl -fsS -o /dev/null http://127.0.0.1:8000/health/ready && break
    sleep 2
  done
  if ! curl -fsS http://127.0.0.1:8000/health/ready || ! systemctl is-active --quiet "${SERVICES[@]}"; then
    echo
    journalctl -u vanuyen-api -u vanuyen-ai-worker -n 40 --no-pager
    echo "Deploy FAILED: services are not healthy. Previous commit: $OLD" >&2
    exit 1
  fi
  echo
fi

for old in "$REPO/frontend" "$REPO/vendor/vanuyen-wheelhouse"; do
  if [[ -e $old ]]; then echo "Note: $old is left over from the old layout and can be deleted."; fi
done
log "Deployed $(as_app git -C "$REPO" rev-parse --short HEAD)"
