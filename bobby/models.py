# Copyright 2012 Rackspace Hosting, Inc.
"""
Cassandra models for bobby
"""
from silverberg.client import ConsistencyLevel
from twisted.internet import defer


class Group(object):
    """A Cassandra model representing a group of servers.

    :ivar group_id: The otter scaling group id.
    :type group_id: ``str``

    :ivar tenant_id: The id of the group owner.
    :type tenant_id: ``str``
    """

    def __init__(self, client, group_id=None, tenant_id=None):
        self._client = client

        self.group_id = group_id
        self.tenant_id = tenant_id

    def view_notification(self):
        query = 'SELECT notification FROM groups WHERE "groupId"=:groupId AND"tenantId"=:tenantId'
        return self._client.execute(query,
                                    {'groupId': self.group_id,
                                     'tenantId': self.tenant_id},
                                    ConsistencyLevel.ONE)

    def view_notification_plan(self):
        query = 'SELECT notificationPlan FROM groups WHERE "groupId"=:groupId AND"tenantId"=:tenantId'
        return self._client.execute(query,
                                    {'groupId': self.group_id,
                                     'tenantId': self.tenant_id},
                                    ConsistencyLevel.ONE)

    def delete(self):
        query = 'DELETE FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;'
        return self._client.execute(query,
                                    {'groupId': self.group_id,
                                     'tenantId': self.tenant_id},
                                    ConsistencyLevel.ONE)

    @classmethod
    def new(Class, client, group_id, tenant_id, notification=None, notification_plan=None):
        to_set = [
            ('groupId', group_id),
            ('tenantId', tenant_id)]
        if notification:
            to_set.append(('notification', notification))
        if notification_plan:
            to_set.append(('notification_plan', notification_plan))
        fields = ['"{0}"'.format(field) for field, val in to_set]
        values = [':{0}'.format(field) for field, val in to_set]
        query = 'INSERT INTO groups ({0}) VALUES ({1});'.format(
            ", ".join(fields), ", ".join(values))

        data = {}
        for key, val in to_set:
            data[key] = val

        d = client.execute(query, data, ConsistencyLevel.ONE)

        def create_instance(result):
            return defer.succeed(Class(client, group_id, tenant_id))
        return d.addCallback(create_instance)

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
