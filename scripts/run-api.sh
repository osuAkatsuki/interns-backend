#!/usr/bin/env bash
set -e

if [ -z "$APP_ENV" ]; then
    echo "Please set APP_ENV"
    exit 1
fi

if ["$APP_ENV" == "local" ]; then
    EXTRA_PARAMS="--reload"
else
    EXTRA_PARAMS=""
fi

exec uvicorn main:app \
    --host $APP_HOST \
    --port $APP_PORT \
    --reload \
    --no-server-header \
    --no-date-header
