#!/usr/bin/env bash
set -e

source .env

case $APP_COMPONENT in
    "api")
    exec /scripts/run-api.sh
    ;;

    *)
    echo "'$APP_COMPONENT' is a not a known value for APP_COMPONENT"
    ;;
esac
