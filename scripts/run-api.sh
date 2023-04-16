#!/usr/bin/env bash
set -euo pipefail

if [ -z "$APP_ENV" ]; then
  echo "Please set APP_ENV"
  exit 1
fi

if [ "$APP_ENV" == "local" ]; then
  EXTRA_ARGUMENTS="--reload"
else
  EXTRA_ARGUMENTS=""
fi

exec uvicorn server.main:app \
  --host $APP_HOST \
  --port $APP_PORT \
  --no-access-log \
  $EXTRA_ARGUMENTS
