from twisted.enterprise.adbapi import ConnectionPool
from twisted.internet import defer


SCHEMA = (
    'CREATE TABLE IF NOT EXISTS GROUPS ("group_id" TEXT PRIMARY KEY NOT NULL, webhook TEXT);',
    'CREATE TABLE IF NOT EXISTS SERVERS ("id" TEXT PRIMARY KEY NOT NULL, "state" TEXT, "group_id" TEXT);'

)

class SqlitePool:
    '''Sqlite DB pool'''

    def __init__(self, filename):
        self.connection_pool = ConnectionPool('sqlite3', filename)

    def create(self):
        queries = []
        for query in SCHEMA:
            queries.append(self.query(query))
        return defer.DeferredList(queries)

    def query(self, query):
        return self.connection_pool.runQuery(query)
