#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Usage: ./migrate-db.sh <up/down/create>"
fi

MIGRATIONS_PATH=/srv/root/migrations
MIGRATIONS_SCHEMA_TABLE=schema_migrations

FULL_DB_NAME=$DB_NAME

if [[ "$APP_COMPONENT" == "tests" ]]; then
  FULL_DB_NAME="${WRITE_DB_NAME}_test"
fi

DB_DSN="${DB_SCHEME}://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${FULL_DB_NAME}?x-migrations-table=${MIGRATIONS_SCHEMA_TABLE}"
if [[ $DB_USE_SSL == "true" ]]; then
  DB_DSN="${DB_DSN}&sslmode=require"
else
  DB_DSN="${DB_DSN}&sslmode=disable"
fi

case "$1" in
  up)
    echo "Running migrations (up)"
    go-migrate -source "file://${MIGRATIONS_PATH}" -database $DB_DSN $@
    echo "Ran migrations successfully"
  ;;

  down)
    echo "Running migrations (down)"
    go-migrate -source "file://${MIGRATIONS_PATH}" -database $DB_DSN $@
    echo "Ran migrations successfully"
  ;;

  create)
    raw_input=$2
    lower_input=${raw_input,,}
    cleaned_input=${lower_input// /_}

    echo "Creating migration"
    go-migrate create -ext sql -dir $MIGRATIONS_PATH -seq $cleaned_input
    echo "Created migration successfully"
  ;;

  *)
    echo "'$1' is not a known value for the first parameter"
  ;;
esac
