#!/usr/bin/make

build: # build all containers
	if [ -d "pgdata" ]; then sudo chmod -R 755 pgdata; fi
	docker build -t osu-server:latest -t osu-server:latest .

run-bg: # run all containers in the background
	docker-compose up -d \
		osu-server \
		postgres \
		redis

run: # run all containers in the foreground
	docker-compose up \
		osu-server \
		postgres \
		redis

stop: # stop all containers
	docker-compose down

logs: # attach to the containers live to view their logs
	docker-compose logs -f

test: # run the tests
	docker-compose exec osu-server /scripts/run-tests.sh

test-dbg: # run the tests in debug mode
	docker-compose exec osu-server /scripts/run-tests.sh --dbg

view-cov: # open the coverage report in the browser
	if grep -q WSL2 /proc/sys/kernel/osrelease; then \
		wslview tests/htmlcov/index.html; \
	else \
		xdg-open tests/htmlcov/index.html; \
	fi

up-migrations: # apply up migrations from current state
	docker-compose exec osu-server /scripts/migrate-db.sh up

down-migrations: # apply down migrations from current state
	docker-compose exec osu-server /scripts/migrate-db.sh down

up-seeds: # apply up seeds from current state
	docker-compose exec osu-server /scripts/seed-db.sh up

down-seeds: # apply down seeds from current state
	docker-compose exec osu-server /scripts/seed-db.sh down
