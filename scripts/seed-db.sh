#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Usage: ./seed-db.sh <up/down/create>"
fi

SEEDS_PATH=/srv/root/database/seeds
SEEDS_SCHEMA_TABLE=schema_seeds

FULL_DB_NAME=$DB_NAME

if [[ "$APP_COMPONENT" == "tests" ]]; then
  FULL_DB_NAME="${WRITE_DB_NAME}_test"
fi

DB_DSN="${DB_SCHEME}://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${FULL_DB_NAME}?x-migrations-table=${SEEDS_SCHEMA_TABLE}"
if [[ $DB_USE_SSL == "true" ]]; then
  DB_DSN="${DB_DSN}&sslmode=require"
else
  DB_DSN="${DB_DSN}&sslmode=disable"
fi

case "$1" in
  up)
    echo "Running seeds (up)"
    go-migrate -source "file://${SEEDS_PATH}" -database $DB_DSN $@
    echo "Ran seeds successfully"
  ;;

  down)
    echo "Running seeds (down)"
    go-migrate -source "file://${SEEDS_PATH}" -database $DB_DSN $@
    echo "Ran seeds successfully"
  ;;

  create)
    raw_input=$2
    lower_input=${raw_input,,}
    cleaned_input=${lower_input// /_}

    echo "Creating seed migration"
    go-migrate create -ext sql -dir $SEEDS_PATH -seq $cleaned_input
    echo "Created seed migration successfully"
  ;;

  *)
    echo "'$1' is not a known value for the first parameter"
  ;;
esac
