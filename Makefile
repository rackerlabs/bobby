CODEDIR=bobby
CASSANDRA_HOST ?= localhost
CASSANDRA_PORT ?= 9160
CONTROL_KEYSPACE ?= BOBBY
SCRIPTSDIR=scripts
PYTHONLINT=${SCRIPTSDIR}/python-lint.py
PYDIRS=${CODEDIR} ${SCRIPTSDIR}

run:
	twistd -n -y app.tac

test:
	trial bobby.tests

schema: FORCE schema-setup schema-teardown

schema-setup:
	PATH=${SCRIPTSDIR}:${PATH} load_cql.py schema/setup --ban-unsafe --outfile schema/setup-dev.cql --replication 1 --keyspace ${CONTROL_KEYSPACE} --dry-run

schema-teardown:
	PATH=${SCRIPTSDIR}:${PATH} load_cql.py schema/teardown --outfile schema/teardown-dev.cql --replication 1 --keyspace ${CONTROL_KEYSPACE} --dry-run

load-dev-schema:
	PATH=${SCRIPTSDIR}:${PATH} load_cql.py schema/setup --ban-unsafe --outfile schema/setup-dev.cql --replication 1 --keyspace ${CONTROL_KEYSPACE} --host ${CASSANDRA_HOST} --port ${CASSANDRA_PORT}

teardown-dev-schema:
	PATH=${SCRIPTSDIR}:${PATH} load_cql.py schema/teardown --outfile schema/teardown-dev.cql --replication 1 --keyspace ${CONTROL_KEYSPACE} --host ${CASSANDRA_HOST} --port ${CASSANDRA_PORT}

clear-dev-schema: FORCE teardown-dev-schema load-dev-schema

FORCE:

lint:
	${PYTHONLINT} ${PYDIRS}

clean: 
	find . -name '*.pyc' -delete
	find . -name '.coverage' -delete
	find . -name '_trial_coverage' -print0 | xargs rm -rf
	find . -name '_trial_temp' -print0 | xargs rm -rf
	rm -rf dist build *.egg-info
	rm -rf schema/setup-*.cql
	rm -rf schema/migrations-*.cql
	rm -rf schema/teardown-*.cql

coverage:
	coverage run --source=${CODEDIR} --branch `which trial` ${CODEDIR} && coverage html -d _trial_coverage --omit="*/tests/*"
