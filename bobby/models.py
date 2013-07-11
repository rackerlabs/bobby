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
    """A Cassandra model representing a server.

    :ivar server_id: The nova instance id.
    :ivar server_id: ``str``

    :ivar entity_id: The MaaS entity id.
    :ivar entity_id: ``str``

    :ivar group_id: The group that owns this server.
    :ivar group_id: ``str``
    """

    def __init__(self, client, server_id, entity_id, group_id):
        self._client = client

        self.server_id = server_id
        # Do we have the entity id immediately?
        self.entity_id = entity_id
        self.group_id = group_id

    def delete(self):
        # TODO: also delete the entity in MaaS
        query = 'DELETE FROM servers WHERE "serverId"=:serverId AND "groupId"=:groupId;'
        return self._client.execute(query,
                                    {'serverId': self.server_id,
                                     'groupId': self.group_id},
                                    ConsistencyLevel.ONE)

    @classmethod
    def new(Class, client, server_id, entity_id, group_id):
        query = 'INSERT INTO server ("serverId", "entityId", "groupId") VALUES (:serverId, :entityId, :groupId);'

        d = client.execute(query,
                           {'serverId': server_id,
                            'entityId': entity_id,
                            'groupId': group_id},
                           ConsistencyLevel.ONE)

        def create_server(result):
            return defer.succeed(Class(client, server_id, entity_id, group_id))
        return d.addCallback(create_server)

    @staticmethod
    def all(client):
        query = 'SELECT * FROM SERVERS;'
        return client.execute(query, {}, ConsistencyLevel.ONE)
