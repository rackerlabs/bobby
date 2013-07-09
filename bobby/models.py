# Copyright 2012 Rackspace Hosting, Inc.
"""
Cassandra models for bobby
"""
from silverberg.client import ConsistencyLevel


class Group(object):
    """A Cassandra model representing a scaling group."""

    group_id = None
    webhook = None

    def __init__(self, group_id, webhook):
        self.group_id = group_id
        self.webhook = webhook

    @staticmethod
    def all(client):
        query = 'SELECT * FROM GROUPS;'
        return client.execute(query, {}, ConsistencyLevel.ONE)


class Server(object):
    """A Cassandra model representing a server."""

    server_id = None
    group_id = None
    state = None

    def __init__(self, server_id, group_id, state):
        self.server_id = server_id
        self.group_id = group_id
        self.state = state

    @staticmethod
    def all(client):
        query = 'SELECT * FROM SERVERS;'
        return client.execute(query, {}, ConsistencyLevel.ONE)
