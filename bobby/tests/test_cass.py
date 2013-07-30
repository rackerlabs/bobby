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

        d = cass.create_group(expected['tenantId'], expected['groupId'],
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

        d = cass.delete_group('101010', 'group-abc')

        self.successResultOf(d)
        self.client.execute.assert_called_once_with(
            'DELETE FROM groups WHERE "groupId"=:groupId AND "tenantId"=:tenantId;',
            {'groupId': 'group-abc', 'tenantId': '101010'},
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

        d = cass.get_servers_by_group_id('101010', 'group-def')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM servers WHERE "groupId"=:groupId AND "tenantId"=:tenantId;',
            {'groupId': 'group-def', 'tenantId': '101010'},
            1)


class TestGetServerByServerId(_DBTestCase):
    """Test bobby.cass.get_server_by_server_id."""

    def test_get_server_by_server_id(self):
        """Return a single server dict, rather than a single item list."""
        expected = {'serverId': 'server-abc',
                    'groupId': 'group-def',
                    'entityId': 'entity-ghi'}
        self.client.execute.return_value = defer.succeed([expected])

        d = cass.get_server_by_server_id('101010', 'server-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM servers WHERE "serverId"=:serverId AND "tenantId"=:tenantId;',
            {'serverId': 'server-abc', 'tenantId': '101010'},
            1)

    def test_get_server_by_server_id_not_found(self):
        """Raises an error if no server is found."""
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_server_by_server_id('101010', 'server-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ResultNotFoundError))

    def test_get_server_by_id_integrity_problems(self):
        """Raises an error if more than one group is found."""
        self.client.execute.return_value = defer.succeed(['server-abc', 'server-def'])

        d = cass.get_server_by_server_id('101010', 'server-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ExcessiveResultsError))


class TestCreateServer(_DBTestCase):
    """Test bobby.cass.create_server."""

    def test_create_server(self):
        """Creates and returns a server dict."""
        expected = {'serverId': 'server-abc',
                    'groupId': 'group-def',
                    'entityId': 'entity-ghi',
                    'tenantId': '101010'}

        def execute(query, data, consistency):
            if 'INSERT' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed([expected])
        self.client.execute.side_effect = execute

        d = cass.create_server(expected['tenantId'], expected['serverId'], expected['entityId'],
                               expected['groupId'])

        result = self.successResultOf(d)
        self.assertEqual(result, expected)

        calls = [
            mock.call(
                ' '.join([
                    'INSERT INTO servers ("tenantId", "serverId", "entityId", "groupId")',
                    'VALUES (:tenantId, :serverId, :entityId, :groupId);']),
                {'serverId': 'server-abc',
                 'entityId': 'entity-ghi',
                 'groupId': 'group-def',
                 'tenantId':  '101010'},
                1),
            mock.call(
                'SELECT * FROM servers WHERE "serverId"=:serverId AND "tenantId"=:tenantId;',
                {'serverId': 'server-abc', 'tenantId':  '101010'},
                1)]
        self.assertEqual(self.client.execute.mock_calls, calls)


class TestDeleteServer(_DBTestCase):
    """Test bobby.cass.delete_server."""

    def test_delete_server(self):
        """Delete and cascade to delete associated server policies."""
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        d = cass.delete_server('101010', 'server-abc')

        self.successResultOf(d)

        calls = [
            mock.call(
                'DELETE FROM servers WHERE "serverId"=:serverId AND "tenantId"=:tenantId;',
                {'serverId': 'server-abc', 'tenantId': '101010'}, 1)
        ]
        self.assertEqual(calls, self.client.execute.mock_calls)


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
            'SELECT * FROM policies WHERE "groupId"=:groupId;',
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

        d = cass.get_policy_by_policy_id('101010', 'policy-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)
        self.client.execute.assert_called_once_with(
            'SELECT * FROM policies WHERE "policyId"=:policyId AND "groupId"=:groupId;',
            {'policyId': 'policy-abc', 'groupId': '101010'},
            1)

    def test_get_policy_by_policy_id_not_found(self):
        """Raises an error if no policy is found."""
        self.client.execute.return_value = defer.succeed([])

        d = cass.get_policy_by_policy_id('101010', 'policy-abc')

        result = self.failureResultOf(d)
        self.assertTrue(result.check(cass.ResultNotFoundError))

    def test_get_policy_by_policy_id_integrity_problems(self):
        """Raises an error if more than one policy is found."""
        self.client.execute.return_value = defer.succeed(['policy-abc', 'policy-def'])

        d = cass.get_policy_by_policy_id('101010', 'policy-abc')

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
                'SELECT * FROM policies WHERE "policyId"=:policyId AND "groupId"=:groupId;',
                {'policyId': 'policy-abc', 'groupId': 'group-def'},
                1)
        ]
        self.assertEqual(self.client.execute.mock_calls, calls)


class TestDeletePolicy(_DBTestCase):
    """Test bobby.cass.delete_policy."""

    def test_delete_policy(self):
        """Deletes a policy."""
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        d = cass.delete_policy('policy-abc')

        self.successResultOf(d)

        calls = [
            mock.call(
                'DELETE FROM policies WHERE "policyId"=:policyId;',
                {'policyId': 'policy-abc'}, 1),
        ]
        self.assertEqual(calls, self.client.execute.mock_calls)


class TestServerPoliciesCreateDestroy(_DBTestCase):
    """Test bobby.cass.register_policy_on_server and bobby.cass.deregister_policy_on_server."""

    def test_register_policy_on_server(self):
        """Registers a policy on a server and creates a serverpolicy record."""
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        d = cass.register_policy_on_server('policy-abc', 'server-abc', 'alABCD', 'chABCD')

        self.successResultOf(d)

        calls = [
            mock.call(
                ('INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", "checkId", state)'
                 ' VALUES (:serverId, :policyId, :alarmId, :checkId, false);'),
                {'policyId': 'policy-abc', 'serverId': 'server-abc',
                 'alarmId': 'alABCD', 'checkId': 'chABCD'}, 1),
        ]
        self.assertEqual(calls, self.client.execute.mock_calls)

    def test_deregister_policy_on_server(self):
        """Registers a policy on a server and creates a serverpolicy record."""
        def execute(*args, **kwargs):
            return defer.succeed(None)
        self.client.execute.side_effect = execute

        d = cass.deregister_policy_on_server('policy-abc', 'server-abc')

        self.successResultOf(d)

        calls = [
            mock.call(
                'DELETE FROM serverpolicies WHERE "policyId"=:policyId AND "serverId"=:serverId;',
                {'policyId': 'policy-abc', 'serverId': 'server-abc'}, 1),
        ]
        self.assertEqual(calls, self.client.execute.mock_calls)


class TestServerPolicies(_DBTestCase):
    """Test bobby.cass.register_policy_on_server and bobby.cass.deregister_policy_on_server."""

    def test_policy_state(self):
        """Registers a policy on a server and creates a serverpolicy record."""
        expected = [{'policyId': 'policy-abc',
                    'groupId': 'group-def',
                    'alarmId': 'alABCD',
                    'checkId': 'chABCD',
                    'state': 'false'}]
        self.client.execute.return_value = defer.succeed(expected)

        d = cass.get_policy_state('policy-abc')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)

        calls = [
            mock.call(
                'SELECT * FROM serverpolicies WHERE "policyId"=:policyId;',
                {'policyId': 'policy-abc'}, 1),
        ]
        self.assertEqual(calls, self.client.execute.mock_calls)


class TestAlterAlarmState(_DBTestCase):
    """Test bobby.cass.create_policy."""

    def test_alter_alarm_state(self):
        """Creates and returns a policy dict."""
        expected = {'policyId': 'policy-abc',
                    'serverId': 'server-def',
                    'alarmId': 'alghi',
                    'checkId': 'chjkl',
                    'state': True}

        def execute(query, data, consistency):
            if 'UPDATE' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed([expected])
        self.client.execute.side_effect = execute

        d = cass.alter_alarm_state(expected['alarmId'], False)
        result = self.successResultOf(d)

        self.assertEqual(result, ('policy-abc', 'server-def'))

        calls = [
            mock.call(
                'SELECT * FROM serverpolicies WHERE "alarmId"=:alarmId;',
                {'alarmId': 'alghi'},
                1),
            mock.call(
                ('UPDATE serverpolicies SET state=:state WHERE "policyId"=:policyId AND '
                 '"serverId"=:serverId;'),
                {'state': False,
                 'policyId': 'policy-abc',
                 'serverId': 'server-def'},
                1)
        ]
        self.assertEqual(self.client.execute.mock_calls, calls)


class TestCheckQuorumHealth(_DBTestCase):
    """Test bobby.cass.check_quorum_health."""

    def test_unhealthy(self):
        """Results in a False when the quorum is unhealthy."""
        def execute(query, data, consistency):
            return defer.succeed([
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-abc',
                 'state': 'OK'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-def',
                 'state': 'OK'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-ghi',
                 'state': 'Critical'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-jkl',
                 'state': 'Critical'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-mno',
                 'state': 'Critical'},
            ])

        self.client.execute.side_effect = execute

        d = cass.check_quorum_health('alarm-uvwxyz')

        result = self.successResultOf(d)
        self.assertFalse(result)

    def test_healthy(self):
        """Results in a False when the quorum is healthy."""
        def execute(query, data, consistency):
            return defer.succeed([
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-abc',
                 'state': 'OK'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-def',
                 'state': 'OK'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-ghi',
                 'state': 'OK'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-jkl',
                 'state': 'Critical'},
                {'policyId': 'policy-uvwxyz',
                 'serverId': 'server-mno',
                 'state': 'Critical'},
            ])

        self.client.execute.side_effect = execute

        d = cass.check_quorum_health('policy-uvwxyz')

        result = self.successResultOf(d)
        self.assertTrue(result)

        self.client.execute.assert_called_once_with(
            'SELECT * FROM serverpolicies WHERE "policyId"=:policyId;',
            {'policyId': 'policy-uvwxyz'}, 1)
