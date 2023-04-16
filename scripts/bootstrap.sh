#!/usr/bin/env bash
set -eo pipefail

if [[ -n "$KUBERNETES" ]]; then
  source /vault/secrets/secrets.txt
fi

# handle int & kill signals as non-errors until final "exec" runs
# trap "{ exit 0; }" TERM INT

if [ -z "$APP_COMPONENT" ]; then
  echo "Please set APP_COMPONENT"
  exit 1
fi

cd /srv/root

# await connected service availability
/scripts/await-service.sh $DB_HOST $DB_PORT $SERVICE_READINESS_TIMEOUT

# ensure database exists
/scripts/init-db.sh

# run sql database migrations
/scripts/migrate-db.sh up

case $APP_COMPONENT in
  "api")
    exec /scripts/run-api.sh
    ;;

  *)
    echo "'$APP_COMPONENT' is not a known value for APP_COMPONENT"
    ;;
esac
