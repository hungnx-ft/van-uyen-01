#!/usr/bin/env bash
# Check the public site from this machine. Exits non-zero if anything is down.
set -uo pipefail
cd "$(dirname "$0")" || exit
source ./config.sh

status=0
for path in / /health /api/v1/health; do
  # -L: generated pages such as /health redirect to /health/.
  code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 15 "$SITE_URL$path")
  if [[ $code == 200 ]]; then echo "OK   $code $SITE_URL$path"; else echo "FAIL $code $SITE_URL$path"; status=1; fi
done
exit $status
