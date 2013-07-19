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

    def __init__(self, client, group_id, tenant_id, notification, notification_plan):
        self._client = client

        self.group_id = group_id
        self.tenant_id = tenant_id
        self.notification = notification
        self.notification_plan = notification_plan

    def delete(self):
        query = 'DELETE FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;'
        return self._client.execute(query,
                                    {'groupId': self.group_id,
                                     'tenantId': self.tenant_id},
                                    ConsistencyLevel.ONE)

    @classmethod
    def get_all_by_tenant_id(Class, client, tenant_id):
        query = 'SELECT * FROM groups WHERE "tenantId"=:tenantId ALLOW FILTERING;'
        return client.execute(query, {'tenantId': tenant_id}, ConsistencyLevel.ONE)

    @classmethod
    def get_by_group_id(Class, client, tenant_id, group_id):
        query = 'SELECT * FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;'
        d = client.execute(query,
                           {'groupId': group_id,
                            'tenantId': tenant_id},
                           ConsistencyLevel.ONE)

        def create_object(results):
            group = results[0]
            return defer.succeed(Class(
                client, group['groupId'], group['tenantId'],
                group['notification'], group['notificationPlan']))
        return d.addCallback(create_object)

    @classmethod
    def new(Class, client, group_id, tenant_id, notification, notification_plan):
        query = ' '.join([
                'INSERT INTO groups',
                '("groupId", "tenantId", "notification", "notificationPlan")',
                'VALUES (:groupId, :tenantId, :notification, :notificationPlan);'])

        data = {'groupId': group_id,
                'tenantId': tenant_id,
                'notification': notification,
                'notificationPlan': notification_plan}

        d = client.execute(query, data, ConsistencyLevel.ONE)

        def create_instance(result):
            return defer.succeed(Class(
                client, group_id, tenant_id, notification, notification_plan))
        return d.addCallback(create_instance)


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

    def view_policies(self):
        query = 'SELECT * FROM serverpolicies WHERE "serverId"=:serverId;'
        return self._client.execute(query,
                                    {'serverId': self.server_id},
                                    ConsistencyLevel.ONE)

    @classmethod
    def get_all_by_group_id(Class, client, tenant_id, group_id):
        query = 'SELECT * FROM servers WHERE "groupId"=:groupId ALLOW FILTERING;'

        return client.execute(query,
                              {'groupId': group_id},
                              ConsistencyLevel.ONE)

    @classmethod
    def get_by_server_id(Class, client, server_id):
        query = 'SELECT * FROM servers WHERE "serverId"=:serverId;'

        d = client.execute(query, {'serverId': server_id},
                           ConsistencyLevel.ONE)

        def create_object(results):
            server = results[0]
            return defer.succeed(
                Class(client, server['serverId'], server['entityId'], server['groupId']))
        return d.addCallback(create_object)

    @classmethod
    def new(Class, client, server_id, entity_id, group_id, server_policies):
        # TODO: validate that the policies exist
        query = 'INSERT INTO servers ("serverId", "entityId", "groupId") VALUES (:serverId, :entityId, :groupId);'

        d = client.execute(query,
                           {'serverId': server_id,
                            'entityId': entity_id,
                            'groupId': group_id},
                           ConsistencyLevel.ONE)

        def add_server_policies(_):
            query = ' '.join([
                'INSERT INTO serverpolicies ("serverId", "policyId",',
                '"alarmId", "checkId", "state") VALUES (:serverId, :policyId,',
                ':alarmId, :checkId, :state);'])
            deferreds = []
            for server_policy in server_policies:
                d = client.execute(query, {'serverId': server_id,
                                           'policyId': server_policy['policyId'],
                                           'alarmId': server_policy['alarmId'],
                                           'checkId': server_policy['checkId'],
                                           'state': 'OK'},
                                   ConsistencyLevel.ONE)
                deferreds.append(d)
            return defer.DeferredList(deferreds)
        d.addCallback(add_server_policies)

        def create_server(_):
            return defer.succeed(Class(client, server_id, entity_id, group_id))
        return d.addCallback(create_server)


class Policy(object):
    """A representation of an otter scaling policy.

    :ivar policyId: An otter scaling policy id.
    :type policyId: ``str``

    :ivar groupId: The group that owns this policy
    :type groupId: ``str``

    :ivar alarmTemplateId: The alarm template to apply to member servers.
    :type alarmTemplateId: ``str``

    :ivar checkTemplateId: The check template to apply to member servers.
    :type checkTemplateId: ``str``
    """

    def __init__(self, client, policy_id, group_id, alarm_template_id, check_template_id):
        self._client = client

        self.policy_id = policy_id
        self.group_id = group_id
        self.alarm_template_id = alarm_template_id
        self.check_template_id = check_template_id

    @classmethod
    def get_by_policy_id(Class, client, policy_id):
        query = 'SELECT * FROM policies WHERE "policyId"=:policyId ALLOW FILTERING;'

        d = client.execute(query, {'policyId': policy_id},
                           ConsistencyLevel.ONE)

        def create_object(results):
            data = results[0]
            policy = Class(client, data['policyId'], data['groupId'],
                           data['alarmTemplateId'], data['checkTemplateId'])
            return defer.succeed(policy)
        return d.addCallback(create_object)

    @classmethod
    def get_all_by_group_id(Class, client, group_id):
        query = 'SELECT * FROM policies WHERE "groupId"=:groupId;'
        return client.execute(query, {'groupId': group_id},
                              ConsistencyLevel.ONE)

    @classmethod
    def new(Class, client, policy_id, group_id, alarm_template_id, check_template_id):
        query = " ".join((
            'INSERT INTO policies ("policyId", "groupId", "alarmTemplateId", "checkTemplateId")',
            'VALUES (:policyId, :groupId, :alarmTemplateId, :checkTemplateId);'
        ))

        d = client.execute(query,
                           {'policyId': policy_id,
                            'groupId': group_id,
                            'alarmTemplateId': alarm_template_id,
                            'checkTemplateId': check_template_id},
                           ConsistencyLevel.ONE)

        def create_policy_object(_):
            return defer.succeed(
                Class(client, policy_id, group_id, alarm_template_id, check_template_id))
        return d.addCallback(create_policy_object)

    def delete(self):
        query = 'DELETE FROM policies WHERE "policyId"=:policyId AND "groupId"=:groupId;'

        return self._client.execute(query,
                                    {'policyId': self.policy_id,
                                     'groupId': self.group_id},
                                    ConsistencyLevel.ONE)


class ServerPolicy(object):
    """A server policy state representation.

    :ivar serverId: The server id.
    :type serverId: ``str``

    :ivar policyId: The policy id.
    :type policyId: ``str``

    :ivar alarmId: The alarm id.
    :type alarmId: ``str``

    :ivar checkId: The check id.
    :type checkId: ``str``

    :ivar state: The server state; either "OK" or "Critical"
    :type state: ``str``
    """

    def __init__(self, client, server_id, policy_id, alarm_id, check_id, state):
        self._client = client

        self.server_id = server_id
        self.policy_id = policy_id
        self.alarm_id = alarm_id
        self.check_id = check_id
        self.state = state

    @classmethod
    def new(Class, client, server_id, policy_id, alarm_id, check_id, state):
        query = " ".join((
            'INSERT INTO serverpolicies ("serverId", "policyId", "alarmTemplateId", "checkTemplateId", "state")',
            'VALUES (:serverId, :policyId, :alarmTemplateId, :checkTemplateId, :state);'
        ))

        d = client.execute(query,
                           {'serverId': server_id,
                            'policyId': policy_id,
                            'alarmId': alarm_id,
                            'checkId': check_id,
                            'state': state},
                           ConsistencyLevel.ONE)

        def create_serverpolicy(_):
            return defer.succeed(
                Class(client, server_id, policy_id, alarm_id, check_id, state))
        return d.addCallback(create_serverpolicy)

    def delete(self):
        query = 'DELETE FROM serverpolicies WHERE "serverId"=:serverId AND "policyId"=:policyId;'

        return self._client.execute(query,
                                    {'serverId': self.server_id,
                                     'policyId': self.policy_id},
                                    ConsistencyLevel.ONE)
