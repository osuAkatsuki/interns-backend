#!/usr/bin/make

build: # build all containers
	if [ -d "pgdata" ]; then sudo chmod -R 755 pgdata; fi
	docker build -t interns-backend:latest -t registry.digitalocean.com/akatsuki/interns-backend:latest .

run-bg: # run all containers in the background
	docker-compose up -d \
		interns-backend \
		postgres \
		redis

run: # run all containers in the foreground
	docker-compose up \
		interns-backend \
		postgres \
		redis

stop: # stop all containers
	docker-compose down

lint: # run pre-commit hooks
	pre-commit run -a

logs: # attach to the containers live to view their logs
	docker-compose logs -f

test: # run the tests
	docker-compose exec interns-backend /scripts/run-tests.sh

test-dbg: # run the tests in debug mode
	docker-compose exec interns-backend /scripts/run-tests.sh --dbg

view-cov: # open the coverage report in the browser
	if grep -q WSL2 /proc/sys/kernel/osrelease; then \
		wslview tests/htmlcov/index.html; \
	else \
		xdg-open tests/htmlcov/index.html; \
	fi

up-migrations: # apply up migrations from current state
	docker-compose exec interns-backend /scripts/migrate-db.sh up

down-migrations: # apply down migrations from current state
	docker-compose exec interns-backend /scripts/migrate-db.sh down

up-seeds: # apply up seeds from current state
	docker-compose exec interns-backend /scripts/seed-db.sh up

down-seeds: # apply down seeds from current state
	docker-compose exec interns-backend /scripts/seed-db.sh down

push:
	docker push registry.digitalocean.com/akatsuki/interns-backend:latest

install:
	helm install \
		--atomic \
		--wait --timeout 480s \
		--values chart/values.yaml \
		interns-backend-staging \
		../akatsuki/common-helm-charts/microservice-base/

uninstall:
	helm uninstall \
		--wait --timeout 480s \
		interns-backend-staging

upgrade:
	helm upgrade \
		--atomic \
		--wait --timeout 480s \
		--values chart/values.yaml \
		interns-backend-staging \
		../akatsuki/common-helm-charts/microservice-base/

diff:
	helm diff upgrade \
		--allow-unreleased \
		--values chart/values.yaml \
		interns-backend-staging \
		../akatsuki/common-helm-charts/microservice-base/
