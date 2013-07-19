'''
Tests for bobby.cass
'''
from bobby import cass

import mock
from silverberg.client import CQLClient
from twisted.internet import defer
from twisted.trial import unittest


class _DBTestCase(unittest.TestCase):

    def setUp(self):
        self.client = mock.create_autospec(CQLClient)
        cass.set_client(self.client)


class TestGetGroupsByTenantId(_DBTestCase):
    '''Test bobby.cass.get_groups_by_tenant_id.'''

    def test_get_grous_by_tenant_id(self):
        '''Return all the groups by a given tenant id.'''
        expected = []
        self.client.execute.return_value = defer.succeed(expected)

        d = cass.get_groups_by_tenant_id('101010')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM groups WHERE "tenantId"=:tenantId ALLOW FILTERING;',
            {'tenantId': '101010'},
            1)


class TestGetGroupById(_DBTestCase):
    '''Test bobby.cass.get_group_by_id.'''

    def test_get_group_by_id(self):
        '''Returns a single dict, rather than a single item list.'''
        expected = {'groupId': 'group-abc',
                    'tenantId': '101010',
                    'notification': 'notification-ghi',
                    'notificationPlan': 'notificationPlan-jkl'}
        self.client.execute.return_value = defer.succeed([expected])

        d = cass.get_group_by_id('group-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM groups WHERE "groupId"=:groupId;',
            {'groupId': 'group-abc'},
            1)

    def test_get_group_by_id_no_such_id(self):
        '''Raises an error if no group is found.'''
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_group_by_id('group-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ResultNotFoundError))

    def test_get_group_by_id_integrity_problems(self):
        '''Raises an error if more than one group is found.'''
        self.client.execute.return_value = defer.succeed(['group1', 'group2'])

        d = cass.get_group_by_id('group-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ExcessiveResultsError))


class TestCreateGroup(_DBTestCase):
    '''Test bobby.cass.create_group.'''

    def test_create_group(self):
        '''Creates a group in Cassandra.'''
        expected = {'groupId': 'group-abc',
                    'tenantId': '101010',
                    'notification': 'notification-ghi',
                    'notificationPlan': 'notificationPlan-jkl'}

        def execute(query, data, consistency):
            if 'INSERT' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed([expected])
        self.client.execute.side_effect = execute

        d = cass.create_group(expected['groupId'], expected['tenantId'],
                              expected['notification'], expected['notificationPlan'])

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.assertEqual(
            self.client.execute.mock_calls,
            [mock.call(
                ' '.join([
                    'INSERT INTO groups ("groupId", "tenantId", "notification", "notificationPlan")',
                    'VALUES (:groupId, :tenantId, :notification, :notificationPlan);']),
                {'notificationPlan': 'notificationPlan-jkl',
                 'notification': 'notification-ghi',
                 'groupId': 'group-abc',
                 'tenantId': '101010'},
                1),
             mock.call(
                 'SELECT * FROM groups WHERE "groupId"=:groupId;',
                 {'groupId': 'group-abc'},
                 1)])


class TestDeleteGroup(_DBTestCase):
    '''Test bobby.cass.delete_group.'''

    def test_delete_group(self):
        '''Deletes a group.'''
        self.client.execute.return_value = defer.succeed(None)

        d = cass.delete_group('group-abc')

        self.successResultOf(d)
        self.client.execute.assert_called_once_with(
            'DELETE FROM groups WHERE "groupId"=:groupId;',
            {'groupId': 'group-abc'},
            1)


class TestGetServersByGroupId(_DBTestCase):
    '''Test bobby.cass.get_servers_by_group_id.'''

    def test_get_servers_by_group_id(self):
        '''Returns all servers by a given group_id.'''
        expected = [{'serverId': 'server-abc',
                     'groupId': 'group-def',
                     'entityId': 'entity-ghi'},
                    {'serverId': 'server-xyz',
                     'groupId': 'group-def',
                     'entityId': 'entity-uvw'}]
        self.client.execute.return_value = defer.succeed(expected)

        d = cass.get_servers_by_group_id('group-def')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM servers WHERE "groupId"=:groupId ALLOW FILTERING;',
            {'groupId': 'group-def'},
            1)


class TestGetServerByServerId(_DBTestCase):
    '''Test bobby.cass.get_server_by_server_id.'''

    def test_get_server_by_server_id(self):
        expected = {'serverId': 'server-abc',
                    'groupId': 'group-def',
                    'entityId': 'entity-ghi'}
        self.client.execute.return_value = defer.succeed([expected])

        d = cass.get_server_by_server_id('server-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM servers WHERE "serverId"=:serverId;',
            {'serverId': 'server-abc'},
            1)

    def test_get_server_by_server_id_not_found(self):
        '''Raises an error if no server is found.'''
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_server_by_server_id('server-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ResultNotFoundError))

    def test_get_server_by_id_integrity_problems(self):
        '''Raises an error if more than one group is found.'''
        self.client.execute.return_value = defer.succeed(['server-abc', 'server-def'])

        d = cass.get_server_by_server_id('server-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ExcessiveResultsError))


class TestCreateServer(_DBTestCase):
    '''Test bobby.cass.create_server.'''

    def test_create_server(self):
        '''Creates and returns a server dict.'''
        expected = {'serverId': 'server-abc',
                    'groupId': 'group-def',
                    'entityId': 'entity-ghi'}
        expected_policy = {'serverId': 'server-abc',
                           'policyId': 'policy-def',
                           'alarmId': 'alarm-ghi',
                           'checkId': 'check-jkl'}

        def execute(query, data, consistency):
            if 'INSERT' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed([expected])
        self.client.execute.side_effect = execute

        d = cass.create_server(expected['serverId'], expected['entityId'],
                               expected['groupId'], [expected_policy])

        result = self.successResultOf(d)
        self.assertEqual(result, expected)

        calls = [
            mock.call(
                ' '.join([
                    'INSERT INTO servers ("serverId", "entityId", "groupId")',
                    'VALUES (:serverId, :entityId, :groupId);']),
                {'serverId': 'server-abc',
                 'entityId': 'entity-ghi',
                 'groupId': 'group-def'},
                1),
            mock.call(
                ' '.join([
                    'INSERT INTO serverpolicies',
                    '("serverId", "policyId", "alarmId", "checkId", "state")',
                    'VALUES (:serverId, :policyId, :alarmId, :checkId, :state);']),
                {'serverId': expected_policy['serverId'],
                 'policyId': expected_policy['policyId'],
                 'alarmId': expected_policy['alarmId'],
                 'checkId': expected_policy['checkId'],
                 'state': 'OK'},
                1),
            mock.call(
                'SELECT * FROM servers WHERE "serverId"=:serverId;',
                {'serverId': 'server-abc'},
                1)]
        self.assertEqual(self.client.execute.mock_calls, calls)


class TestDeleteServer(_DBTestCase):
    '''Test bobby.cass.delete_server.'''

    def test_delete_server(self):
        '''Delete and cascade to delete associated server policies.'''
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        d = cass.delete_server('server-abc')

        self.successResultOf(d)

        calls = [
            mock.call(
                'DELETE FROM servers WHERE "serverId"=:serverId;',
                {'serverId': 'server-abc'}, 1),
            mock.call(
                'DELETE FROM serverpolicies WHERE "serverId"=:serverId;',
                {'serverId': 'server-abc'}, 1),
        ]
        self.assertEqual(calls, self.client.execute.mock_calls)
