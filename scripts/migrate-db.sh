#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Usage: ./migrate-db.sh <up/down/create>"
fi

MIGRATIONS_PATH=/srv/root/database/migrations
MIGRATIONS_SCHEMA_TABLE=schema_migrations

FULL_WRITE_DB_NAME=$WRITE_DB_NAME

if [[ "$APP_COMPONENT" == "tests" ]]; then
  FULL_WRITE_DB_NAME="${WRITE_DB_NAME}_test"
fi

DB_DSN="${WRITE_DB_SCHEME}://${WRITE_DB_USER}:${WRITE_DB_PASS}@${WRITE_DB_HOST}:${WRITE_DB_PORT}/${FULL_WRITE_DB_NAME}?x-migrations-table=${MIGRATIONS_SCHEMA_TABLE}"
if [[ $WRITE_DB_USE_SSL == "true" ]]; then
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
