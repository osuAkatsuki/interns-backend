#!/usr/bin/env bash
set -euo pipefail

execDBStatement() {
  if [[ $DB_USE_SSL == "true" ]]; then
    SSL_ARGS="--set=sslmode=require"
  else
    SSL_ARGS=""
  fi
  echo "$1" | PGPASSWORD=$DB_PASS psql \
    --host=$DB_HOST \
    --port=$DB_PORT \
    --username=$DB_USER \
    --dbname=$INITIALLY_AVAILABLE_DB \
    $SSL_ARGS
}

FULL_DB_NAME="${DB_NAME}"

if [[ "$APP_COMPONENT" == "tests" ]]; then
  FULL_DB_NAME="${DB_NAME}_test"
fi

# basically `CREATE DATABASE IF NOT EXISTS` for postgresql
execDBStatement "SELECT 'CREATE DATABASE ${FULL_DB_NAME}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${FULL_DB_NAME}')\gexec"
