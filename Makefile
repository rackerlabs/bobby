CASSANDRA_HOST ?= localhost
CASSANDRA_PORT ?= 9160
CONTROL_KEYSPACE ?= BOBBY
SCRIPTSDIR=scripts

run:
	twistd -n -y app.tac

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
