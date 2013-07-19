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


class TestGetGroupsByTenantId(_DBTestCase):
    '''Test bobby.cass.get_groups_by_tenant_id.'''

    def test_get_grous_by_tenant_id(self):
        '''Return all the groups by a given tenant id.'''
        expected = []
        self.client.execute.return_value = defer.succeed(expected)

        d = cass.get_groups_by_tenant_id(self.client, '101010')

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

        d = cass.get_group_by_id(self.client, 'group-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM groups WHERE "groupId"=:groupId;',
            {'groupId': 'group-abc'},
            1)

    def test_get_group_by_id_no_such_id(self):
        '''Raises an error if no group is found.'''
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_group_by_id(self.client, 'group-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.GroupNotFound))

    def test_get_group_by_id_integrity_problems(self):
        '''Raises an error if more than one group is found.'''
        self.client.execute.return_value = defer.succeed(['group1', 'group2'])

        d = cass.get_group_by_id(self.client, 'group-abc')

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

        d = cass.create_group(self.client, expected['groupId'], expected['tenantId'],
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

        d = cass.delete_group(self.client, 'group-abc')

        self.successResultOf(d)
        self.client.execute.assert_called_once_with(
            'DELETE FROM groups WHERE "groupId"=:groupId;',
            {'groupId': 'group-abc'},
            1)
