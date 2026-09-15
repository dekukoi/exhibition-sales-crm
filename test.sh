#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

COMPOSE=(
  docker compose
  --project-directory "$SCRIPT_DIR"
  --file "$SCRIPT_DIR/compose.yml"
  --profile test
)

status=0
"${COMPOSE[@]}" run --rm --build backend-test || status=$?

"${COMPOSE[@]}" rm --force --stop --volumes test-db

exit "$status"
