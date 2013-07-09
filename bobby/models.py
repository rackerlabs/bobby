# Copyright 2012 Rackspace Hosting, Inc.
"""
Cassandra models for bobby
"""
from silverberg.client import ConsistencyLevel


class Group(object):
    """A Cassandra model representing a scaling group."""

    group_id = None
    webhook = None

    def __init__(self, group_id, webhook, client):
        self.group_id = group_id
        self.webhook = webhook

        self._client = client

    def save(self):
        query = 'INSERT INTO groups ("groupId", "webhook") VALUES (:groupId, :webhook);'
        return self._client.execute(query,
                                    {'groupId': self.group_id,
                                     'webhook': self.webhook},
                                    ConsistencyLevel.ONE)

    def delete(self):
        query = 'DELETE FROM groups WHERE "groupId"=:groupId;'
        return self._client.execute(query,
                                    {'groupId': self.group_id,
                                     'webhook': self.webhook},
                                    ConsistencyLevel.ONE)

    @staticmethod
    def all(client):
        query = 'SELECT * FROM GROUPS;'
        return client.execute(query, {}, ConsistencyLevel.ONE)


class Server(object):
    """A Cassandra model representing a server."""

    server_id = None
    group_id = None
    state = None

    def __init__(self, server_id, group_id, state, client):
        self.server_id = server_id
        self.group_id = group_id
        self.state = state

        self._client = client

    def save(self):
        query = 'INSERT INTO servers ("serverId", "groupId", "state") VALUES (:serverId, :groupId, :webhook);'
        return self._client.execute(query,
                                    {'serverId': self.server_id,
                                     'groupId': self.group_id,
                                     'state': self.state},
                                    ConsistencyLevel.ONE)

    def delete(self):
        query = 'DELETE FROM servers WHERE "serverId"=:serverId;'
        return self._client.execute(query, {'serverId': self.server_id},
                                    ConsistencyLevel.ONE)

    def update(self):
        query = 'UPDATE servers SET "state"=:state WHERE "serverId"=:serverId AND "groupId"=:groupId;'
        return self._client.execute(query,
                                    {'serverId': self.server_id,
                                     'groupId': self.group_id,
                                     'state': self.state},
                                    ConsistencyLevel.ONE)

    @staticmethod
    def all(client):
        query = 'SELECT * FROM SERVERS;'
        return client.execute(query, {}, ConsistencyLevel.ONE)
