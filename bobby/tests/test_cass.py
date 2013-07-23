"""
Tests for bobby.cass
"""
from bobby import cass

import mock
from silverberg.client import CQLClient
from twisted.internet import defer
from twisted.trial import unittest


class _DBTestCase(unittest.TestCase):
    """Abstract DB test case."""

    def setUp(self):
        """Patch CQLClient."""
        self.client = mock.create_autospec(CQLClient)
        cass.set_client(self.client)


class TestGetGroupsByTenantId(_DBTestCase):
    """Test bobby.cass.get_groups_by_tenant_id."""

    def test_get_grous_by_tenant_id(self):
        """Return all the groups by a given tenant id."""
        expected = []
        self.client.execute.return_value = defer.succeed(expected)

        d = cass.get_groups_by_tenant_id('101010')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM groups WHERE "tenantId"=:tenantId;',
            {'tenantId': '101010'},
            1)


class TestGetGroupById(_DBTestCase):
    """Test bobby.cass.get_group_by_id."""

    def test_get_group_by_id(self):
        """Returns a single dict, rather than a single item list."""
        expected = {'groupId': 'group-abc',
                    'tenantId': '101010',
                    'notification': 'notification-ghi',
                    'notificationPlan': 'notificationPlan-jkl'}
        self.client.execute.return_value = defer.succeed([expected])

        d = cass.get_group_by_id('101010', 'group-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM groups WHERE "groupId"=:groupId;',
            {'groupId': 'group-abc'},
            1)

    def test_get_group_by_id_no_such_id(self):
        """Raises an error if no group is found."""
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_group_by_id('101010', 'group-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ResultNotFoundError))

    def test_get_group_by_id_integrity_problems(self):
        """Raises an error if more than one group is found."""
        self.client.execute.return_value = defer.succeed(['group1', 'group2'])

        d = cass.get_group_by_id('101010', 'group-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ExcessiveResultsError))


class TestCreateGroup(_DBTestCase):
    """Test bobby.cass.create_group."""

    def test_create_group(self):
        """Creates a group in Cassandra."""
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
    """Test bobby.cass.delete_group."""

    def test_delete_group(self):
        """Deletes a group."""
        self.client.execute.return_value = defer.succeed(None)

        d = cass.delete_group('group-abc')

        self.successResultOf(d)
        self.client.execute.assert_called_once_with(
            'DELETE FROM groups WHERE "groupId"=:groupId;',
            {'groupId': 'group-abc'},
            1)


class TestGetServersByGroupId(_DBTestCase):
    """Test bobby.cass.get_servers_by_group_id."""

    def test_get_servers_by_group_id(self):
        """Returns all servers by a given group_id."""
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
    """Test bobby.cass.get_server_by_server_id."""

    def test_get_server_by_server_id(self):
        """Return a single server dict, rather than a single item list."""
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
        """Raises an error if no server is found."""
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_server_by_server_id('server-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ResultNotFoundError))

    def test_get_server_by_id_integrity_problems(self):
        """Raises an error if more than one group is found."""
        self.client.execute.return_value = defer.succeed(['server-abc', 'server-def'])

        d = cass.get_server_by_server_id('server-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ExcessiveResultsError))


class TestCreateServer(_DBTestCase):
    """Test bobby.cass.create_server."""

    def test_create_server(self):
        """Creates and returns a server dict."""
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
    """Test bobby.cass.delete_server."""

    def test_delete_server(self):
        """Delete and cascade to delete associated server policies."""
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


class TestGetServerPoliciesForServer(_DBTestCase):
    """Test bobby.cass.get_serverpolicies_for_server."""

    def test_get_serverpolicies_for_server(self):
        """Returns a list of serverpolicies for a server."""
        expected = [{'serverId': 'server-abc',
                     'policyId': 'policy-def',
                     'alarmId': 'alarm-ghi',
                     'checkId': 'check-jkl'},
                    {'serverId': 'server-abc',
                     'policyId': 'policy-xyz]',
                     'alarmId': 'alarm-uvw',
                     'checkId': 'check-rst'}]
        self.client.execute.return_value = defer.succeed(expected)

        d = cass.get_serverpolicies_for_server('server-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM serverpolicies WHERE "serverId"=:serverId;',
            {'serverId': 'server-abc'},
            1)


class TestGetPoliciesByGroupId(_DBTestCase):
    """Test bobby.cass.get_policies_by_group_id."""

    def test_get_policies_by_group_id(self):
        """Gets all policies from a provided group."""
        expected = [{'policyId': 'policy-abc',
                     'groupId': 'group-def',
                     'alarmTemplate': 'alarmTemplate-ghi',
                     'checkTemplate': 'checkTemplate-jkl'},
                    {'policyId': 'policy-xyz',
                     'groupId': 'group-def',
                     'alarmTemplate': 'alarmTemplate-uvw',
                     'checkTemplate': 'checkTemplate-rst'}]
        self.client.execute.return_value = defer.succeed(expected)

        d = cass.get_policies_by_group_id('group-def')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM policies WHERE "groupId"=:groupId ALLOW FILTERING;',
            {'groupId': 'group-def'},
            1)


class TestGetPolicyByPolicyId(_DBTestCase):
    """Test bobby.cass.get_policy_by_policy_id."""

    def test_get_policy_by_policy_id(self):
        """Return a single policy dict, rather than a single item list."""
        expected = {'policyId': 'policy-abc',
                    'groupId': 'group-def',
                    'alarmTemplate': 'alarmTemplate-ghi',
                    'checkTemplate': 'checkTemplate-jkl'}
        self.client.execute.return_value = defer.succeed([expected])

        d = cass.get_policy_by_policy_id('policy-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM policies WHERE "policyId"=:policyId ALLOW FILTERING;',
            {'policyId': 'policy-abc'},
            1)

    def test_get_policy_by_policy_id_not_found(self):
        """Raises an error if no policy is found."""
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_policy_by_policy_id('policy-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ResultNotFoundError))

    def test_get_policy_by_policy_id_integrity_problems(self):
        """Raises an error if more than one policy is found."""
        self.client.execute.return_value = defer.succeed(['policy-abc', 'policy-def'])

        d = cass.get_policy_by_policy_id('policy-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ExcessiveResultsError))


class TestCreatePolicy(_DBTestCase):
    """Test bobby.cass.create_policy."""

    def test_create_policy(self):
        """Creates and returns a policy dict."""
        expected = {'policyId': 'policy-abc',
                    'groupId': 'group-def',
                    'alarmTemplate': 'alarmTemplate-ghi',
                    'checkTemplate': 'checkTemplate-jkl'}

        def execute(query, data, consistency):
            if 'INSERT' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed([expected])
        self.client.execute.side_effect = execute

        d = cass.create_policy(expected['policyId'], expected['groupId'],
                               expected['alarmTemplate'],
                               expected['checkTemplate'])

        result = self.successResultOf(d)
        self.assertEqual(result, expected)

        calls = [
            mock.call(
                ' '.join([
                    'INSERT INTO policies',
                    '("policyId", "groupId", "alarmTemplate", "checkTemplate")',
                    'VALUES (:policyId, :groupId, :alarmTemplate, :checkTemplate);']),
                {'alarmTemplate': 'alarmTemplate-ghi',
                 'checkTemplate': 'checkTemplate-jkl',
                 'policyId': 'policy-abc',
                 'groupId': 'group-def'},
                1),
            mock.call(
                'SELECT * FROM policies WHERE "policyId"=:policyId ALLOW FILTERING;',
                {'policyId': 'policy-abc'},
                1)
        ]
        self.assertEqual(self.client.execute.mock_calls, calls)


class TestDeletePolicy(_DBTestCase):
    """Test bobby.cass.delete_policy."""

    def test_delete_policy(self):
        """Deletes a policy and cascades to associated serverpolicies."""
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        d = cass.delete_policy('policy-abc')

        self.successResultOf(d)

        # TODO: re-enable this. See implementation for why it's currently
        # disabled.
        calls = [
            mock.call(
                'DELETE FROM policies WHERE "policyId"=:policyId;',
                {'policyId': 'policy-abc'}, 1),
            #mock.call(
            #    'DELETE FROM serverpolicies WHERE "policyId"=:policyId;',
            #    {'policyId': 'policy-abc'}, 1),
        ]
        self.assertEqual(calls, self.client.execute.mock_calls)
