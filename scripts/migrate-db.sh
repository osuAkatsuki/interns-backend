#!/usr/bin/env bash
set -e

if [[ $# -eq 0]]; then
    echo "Usage: ./migrate-db.sh <up/down/create>"
fi

MIGRATIONS_PATH=srv/root/migrations
MIGRATIONS_SCHEMA_TABLE=schema_migration

FULL_DB_NAME=$DB_NAME

DB_DSN="${DB_DRIVER}://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${FULL_DB_NAME}?x-migrations-table=${MIGRATIONS_SCHEMA_TABLE}&sslmode=disable"

case "$1" in
    up)
        echo "Running Migrations (up)"
        go-migrate -source "file://${MIGRATIONS_PATH}" -database $DB_DSN $@
        echo "Ran migrations successfully"
    ;;

    down)
        echo "Running Migrations (down)"
        go-migrate -source "file://${MIGRATIONS_PATH}" -database $DB_DSN $@
        echo "Ran migrations successfully"
    ;;

    *)
        echo "'$1' is not a known value for the first parameter"
    ;;
esac
