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

    def test_all(self):
        '''Group.all returns all the groups.'''
        def execute(*args, **kwargs):
            expected = [{'webhook': u'abcdef', 'groupId': '1'}]
            return defer.succeed(expected)
        self.client.execute.side_effect = execute

        d = models.Group.all(self.client)

        def _assert(result):
            self.assertEqual(len(result), 1)
            group = result[0]
            self.assertEqual(group['webhook'], u'abcdef')
        d.addCallback(_assert)
        return d

    def test_new(self):
        self.client.execute.return_value = defer.succeed(None)

        d = models.Group.new(self.client, 'group-b', 'tenant-a')

        def _assert(result):
            self.client.execute.assert_called_once_with(
                'INSERT INTO groups ("groupId", "tenantId") VALUES (:groupId, :tenantId);',
                {'groupId': 'group-b', 'tenantId': 'tenant-a'},
                1)
            self.assertTrue(isinstance(result, models.Group))
        return d.addCallback(_assert)

    def test_delete(self):
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        group = models.Group(self.client, 'group-x', 'tenant-y')
        d = group.delete()

        def _assert(_):
            self.client.execute.assert_called_once_with(
                'DELETE FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;',
                {'tenantId': 'tenant-y', 'groupId': 'group-x'},
                1)
        d.addCallback(_assert)
        return d

    def test_view_notification(self):
        self.client.execute.return_value = defer.succeed('notification-abcdef')

        group = models.Group(self.client, 'group-x', 'tenant-y')
        d = group.view_notification()

        def _assert(result):
            self.client.execute.assert_called_once_with(
                'SELECT notification FROM groups WHERE "groupId"=:groupId AND"tenantId"=:tenantId',
                {'groupId': 'group-x', 'tenantId': 'tenant-y'},
                1)
            self.assertEqual(result, 'notification-abcdef')
        d.addCallback(_assert)
        return d

    def test_view_notification_plan(self):
        self.client.execute.return_value = defer.succeed('plan-fedcba')

        group = models.Group(self.client, 'group-x', 'tenant-y')
        d = group.view_notification_plan()

        def _assert(result):
            self.client.execute.assert_called_once_with(
                'SELECT notificationPlan FROM groups WHERE "groupId"=:groupId AND"tenantId"=:tenantId',
                {'groupId': 'group-x', 'tenantId': 'tenant-y'},
                1)
            self.assertEqual(result, 'plan-fedcba')
        d.addCallback(_assert)
        return d


class ServerTestCase(DBTestCase):
    '''Tests for bobby.models.Server.'''

    def test_all(self):
        '''Server.all returns all the groups.'''
        def execute(*args, **kwargs):
            expected = [
                {'serverId': '2', 'groupId': 'y', 'state': 'OK'},
                {'serverId': '1', 'groupId': 'x', 'state': 'OK'}]
            return defer.succeed(expected)
        self.client.execute.side_effect = execute

        d = models.Server.all(self.client)

        def _assert(result):
            self.assertEqual(len(result), 2)
            group = result[0]
            self.assertEqual(group['serverId'], u'2')
            self.assertEqual(group['groupId'], u'y')
            self.assertEqual(group['state'], u'OK')
        d.addCallback(_assert)
        return d

    def test_new(self):
        self.client.execute.return_value = defer.succeed(None)

        d = models.Server.new(self.client, 'server-a', 'entity-b', 'group-c')

        def _assert(result):
            self.client.execute.assert_called_once_with(
                'INSERT INTO server ("serverId", "entityId", "groupId") VALUES (:serverId, :entityId, :groupId);',
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
