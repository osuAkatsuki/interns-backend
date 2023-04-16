#!/usr/bin/env bash
set -e

execDBStatement() {
  echo "$1" | PGPASSWORD=$DB_PASS psql \
    --host=$DB_HOST \
    --port=$DB_PORT \
    --username=$DB_USER \
    --dbname=postgres
}

# basically `CREATE DATABASE IF NOT EXISTS` for postgresql
execDBStatement "SELECT 'CREATE DATABASE ${DB_NAME}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec"
