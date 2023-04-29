#!/usr/bin/env bash
set -euo pipefail

execDBStatement() {
  if [[ $WRITE_DB_USE_SSL == "true" ]]; then
    SSL_ARGS="--set=sslmode=require"
  else
    SSL_ARGS=""
  fi
  echo "$1" | PGPASSWORD=$WRITE_DB_PASS psql \
    --host=$WRITE_DB_HOST \
    --port=$WRITE_DB_PORT \
    --username=$WRITE_DB_USER \
    --dbname=$INITIALLY_AVAILABLE_WRITE_DB \
    $SSL_ARGS
}

FULL_WRITE_DB_NAME="${WRITE_DB_NAME}"

if [[ "$APP_COMPONENT" == "tests" ]]; then
  FULL_WRITE_DB_NAME="${WRITE_DB_NAME}_test"
fi

# basically `CREATE DATABASE IF NOT EXISTS` for postgresql
execDBStatement "SELECT 'CREATE DATABASE ${FULL_WRITE_DB_NAME}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${FULL_WRITE_DB_NAME}')\gexec"
