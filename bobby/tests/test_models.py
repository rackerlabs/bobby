'''Tests for bobby.models.'''
import mock
from silverberg.client import CQLClient
from twisted.internet import defer
from twisted.trial import unittest

from bobby import models


class DBTestCase(unittest.TestCase):

    def setUp(self):
        self.client = mock.create_autospec(CQLClient)


class GroupTestCase(DBTestCase):
    '''Tests for bobby.models.Group.'''

    def test_new(self):
        self.client.execute.return_value = defer.succeed(None)

        d = models.Group.new(self.client, 'group-b', 'tenant-a',
                             'notification-c', 'notification_plan-d')

        def _assert(result):
            self.client.execute.assert_called_once_with(
                ' '.join([
                    'INSERT INTO groups ("groupId", "tenantId", "notification", "notificationPlan")',
                    'VALUES (:groupId, :tenantId, :notification, :notificationPlan);']),

                {'notificationPlan': 'notification_plan-d',
                 'notification': 'notification-c',
                 'groupId': 'group-b',
                 'tenantId': 'tenant-a'},
                1)
            self.assertTrue(isinstance(result, models.Group))
        return d.addCallback(_assert)

    def test_get_all_by_tenant_id(self):
        self.client.execute.return_value = defer.succeed(None)

        d = models.Group.get_all_by_tenant_id(self.client, 'tenant-a')

        self.successResultOf(d)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM groups WHERE "tenantId"=:tenantId ALLOW FILTERING;',
            {'tenantId': 'tenant-a'}, 1)

    def test_get_by_group_id(self):
        def execute(*args, **kwargs):
            result = [{'groupId': 'group-y',
                       'tenantId': 'tenant-x',
                       'notificationPlan': 'notificationPlan-w',
                       'notification': 'notification-z'}]
            return defer.succeed(result)
        self.client.execute.side_effect = execute

        d = models.Group.get_by_group_id(self.client, 'tenant-x', 'group-y')

        self.successResultOf(d)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;',
            {'groupId': 'group-y', 'tenantId': 'tenant-x'},
            1)

    def test_delete(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        group = models.Group(self.client, 'group-x', 'tenant-y',
                             'notification-z', 'notification_plan-w')
        d = group.delete()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;',
                {'tenantId': 'tenant-y', 'groupId': 'group-x'},
                1)
        d.addCallback(_assert)
        return d


class ServerTestCase(DBTestCase):
    '''Tests for bobby.models.Server.'''

    def test_new(self):
        self.client.execute.return_value = defer.succeed(None)

        d = models.Server.new(self.client, 'server-a', 'entity-b', 'group-c')

        def _assert(result):
            self.client.execute.assert_called_once_with(
                'INSERT INTO servers ("serverId", "entityId", "groupId") VALUES (:serverId, :entityId, :groupId);',
                {'serverId': 'server-a', 'entityId': 'entity-b', 'groupId': 'group-c'},
                1)
            self.assertTrue(isinstance(result, models.Server))
        return d.addCallback(_assert)

    def test_delete(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        server = models.Server(self.client, 'server-z', 'entity-y', 'group-x')
        d = server.delete()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM servers WHERE "serverId"=:serverId AND "groupId"=:groupId;',
                {'serverId': 'server-z', 'groupId': 'group-x'},
                1)
        d.addCallback(_assert)
        return d

    def test_view_policies(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        server = models.Server(self.client, 'server-l', 'entity-m', 'group-n')
        d = server.view_policies()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'SELECT * FROM serverpolicy WHERE "serverId"=:serverId AND "groupId"=:groupId;',
                {'serverId': 'server-l', 'groupId': 'group-n'},
                1)
        return d.addCallback(_assert)


class PolicyTestCase(DBTestCase):
    '''Tests for bobby.models.Policy.'''

    def test_new(self):
        self.client.execute.return_value = defer.succeed(None)

        d = models.Policy.new(self.client, 'policy-a', 'group-b', 'alarm-c', 'check-d')

        def _assert(result):
            query = ' '.join((
                'INSERT INTO policy ("policyId", "groupId", "alarmTemplateId", "checkTemplateId")',
                'VALUES (:policyId, :groupId, :alarmTemplateId, :checkTemplateId);',
            ))

            self.client.execute.assert_called_once_with(
                query,
                {'alarmTemplateId': 'alarm-c', 'checkTemplateId': 'check-d',
                 'policyId': 'policy-a', 'groupId': 'group-b'},
                1)
            self.assertTrue(isinstance(result, models.Policy))
        return d.addCallback(_assert)

    def test_delete(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        policy = models.Policy(self.client, 'policy-z', 'group-y', 'alarm-x', 'check-w')
        d = policy.delete()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM policy WHERE "policyId"=:policyId AND "groupId"=:groupId;',
                {'policyId': 'policy-z', 'groupId': 'group-y'},
                1)
        d.addCallback(_assert)
        return d


class ServerPolicyTestCase(DBTestCase):
    '''Tests for bobby.models.ServerPolicy.'''

    def test_new(self):
        self.client.execute.return_value = defer.succeed(None)

        d = models.ServerPolicy.new(self.client, 'server-a', 'policy-b', 'alarm-c', 'check-d', 'OK')

        def _assert(result):
            query = ' '.join((
                'INSERT INTO serverpolicy ("serverId", "policyId", "alarmTemplateId", "checkTemplateId", "state")',
                'VALUES (:serverId, :policyId, :alarmTemplateId, :checkTemplateId, :state);'
            ))

            self.client.execute.assert_called_once_with(
                query,
                {'checkId': 'check-d', 'serverId': 'server-a', 'state': 'OK',
                 'policyId': 'policy-b', 'alarmId': 'alarm-c'},
                1)
        return d.addCallback(_assert)

    def test_delete(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        server_policy = models.ServerPolicy(self.client, 'server-z', 'policy-y', 'alarm-x', 'check-w', 'OK')
        d = server_policy.delete()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM serverpolicy WHERE "serverId"=:serverId AND "policyId"=:policyId;',
                {'serverId': 'server-z', 'policyId': 'policy-y'},
                1)
        d.addCallback(_assert)
        return d
