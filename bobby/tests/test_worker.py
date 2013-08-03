"""Tests for bobby.worker."""

import mock
from twisted.internet import defer
from twisted.trial import unittest
from silverberg.client import CQLClient

from bobby import worker, cass


class _WorkerTestCase(unittest.TestCase):
    """Abstract DB test case."""

    def setUp(self):
        """Patch CQLClient."""
        self.client = mock.create_autospec(CQLClient)
        cass.set_client(self.client)


class TestCreateServerEntity(_WorkerTestCase):
    """ Test that we can add a server """
    @mock.patch('bobby.worker.ele.fetch_entity_by_uuid')
    @mock.patch('bobby.worker.apply_policies_to_server')
    def test_add_server(self, mock_apply_policies, mock_fetch_entity):
        """ Test create_server_entity call """
        mock_apply_policies.return_value = defer.succeed(None)
        mock_fetch_entity.return_value = defer.succeed(None)

        d = worker.create_server_entity('t1', 'p1', 's1')
        result = self.successResultOf(d)
        self.assertEqual(result, None)


class TestAddPolicyToServer(_WorkerTestCase):
    """ Test that we can add a policy to a server """
    @mock.patch('bobby.worker.ele.add_check')
    @mock.patch('bobby.worker.ele.add_alarm')
    def test_add_policy_to_server(self, mock_add_alarm, mock_add_check):
        """ Basic success case """

        example_check_template = {
            'type': 'agent.plugin',
            'details': {'file': 'blah',
                        'args': 'blah'}
        }
        mock_add_check.return_value = defer.succeed('chBlah')
        mock_add_alarm.return_value = defer.succeed('alBlah')
        self.client.execute.return_value = defer.succeed(None)

        d = worker.add_policy_to_server('t1', 'p1', 's1', 'enOne',
                                        example_check_template, "ALARM_DSL", "npBlah")

        result = self.successResultOf(d)
        self.assertEqual(result, None)

        mock_add_check.assert_called_once_with('t1', 'p1', 'enOne', example_check_template)
        mock_add_alarm.assert_called_once_with('t1', 'p1', 'enOne', 'chBlah', "ALARM_DSL", "npBlah")
        self.assertEqual(
            self.client.execute.mock_calls,
            [mock.call(('INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", '
                        '"checkId", state) VALUES (:serverId, :policyId, :alarmId, :checkId, false);'),
                       {'checkId': 'chBlah', 'serverId': 's1', 'policyId': 'p1', 'alarmId': 'alBlah'},
                       1)])


class TestCreateGroup(_WorkerTestCase):
    """ Test that we can add a policy to a server """
    @mock.patch('bobby.worker.ele.add_notification')
    @mock.patch('bobby.worker.ele.add_notification_plan')
    def test_create_group(self, mock_add_notification_plan, mock_add_notification):
        """ Basic success case """
        expected = {'groupId': 'g1',
                    'tenantId': '101010',
                    'notification': 'ntBlah',
                    'notificationPlan': 'npBlah'}

        def execute(query, data, consistency):
            if 'INSERT' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed([expected])
        self.client.execute.side_effect = execute

        mock_add_notification.return_value = defer.succeed('ntBlah')
        mock_add_notification_plan.return_value = defer.succeed('npBlah')

        d = worker.create_group('101010', 'g1')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)

        mock_add_notification.assert_called_once_with('101010')
        mock_add_notification_plan.assert_called_once_with('101010', 'ntBlah')


class TestAddServer(_WorkerTestCase):
    """ Test that we can add a server (which will add multiple policies) """
    @mock.patch('bobby.worker.ele.add_check')
    @mock.patch('bobby.worker.ele.add_alarm')
    def test_add_policy_to_server(self, mock_add_alarm, mock_add_check):
        """ Basic success case """
        expected = [{'policyId': 'policy-abc',
                     'groupId': 'group-def',
                     'alarmTemplate': 'alarmTemplate-ghi',
                     'checkTemplate': 'checkTemplate-jkl'},
                    {'policyId': 'policy-xyz',
                     'groupId': 'group-def',
                     'alarmTemplate': 'alarmTemplate-uvw',
                     'checkTemplate': 'checkTemplate-rst'}]

        def execute(query, data, consistency):
            if 'INSERT' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed(expected)
        self.client.execute.side_effect = execute

        def add_check(tenant_id, policy_id, entity_id, check_template):
            return defer.succeed('ch{}{}'.format(entity_id, policy_id))

        def add_alarm(tenant_id, policy_id, entity_id, check_id, alarm_template, nplan_id):
            return defer.succeed('al{}{}'.format(entity_id, policy_id))
        mock_add_alarm.side_effect = add_alarm
        mock_add_check.side_effect = add_check

        d = worker.apply_policies_to_server('101010', 'group-abc', 'server1', 'enOne', 'npBlah')
        result = self.successResultOf(d)
        self.assertEqual(result, None)

        self.assertEqual(
            self.client.execute.mock_calls,
            [mock.call('SELECT * FROM policies WHERE "groupId"=:groupId;',
                       {'groupId': 'group-abc'},
                       1),
             mock.call(('INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", "checkId", '
                       'state) VALUES (:serverId, :policyId, :alarmId, :checkId, false);'),
                       {'checkId': 'chenOnepolicy-abc', 'serverId': 'server1',
                        'policyId': 'policy-abc', 'alarmId': 'alenOnepolicy-abc'},
                       1),
             mock.call(
                 ('INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", "checkId", state) '
                  'VALUES (:serverId, :policyId, :alarmId, :checkId, false);'),
                 {'checkId': 'chenOnepolicy-xyz', 'serverId': 'server1',
                  'policyId': 'policy-xyz', 'alarmId': 'alenOnepolicy-xyz'},
                 1)])


class TestAddPolicy(_WorkerTestCase):
    """ Test that we can add a server (which will add multiple policies) """
    @mock.patch('bobby.worker.ele.add_check')
    @mock.patch('bobby.worker.ele.add_alarm')
    def test_add_policy(self, mock_add_alarm, mock_add_check):
        """ Basic success case """
        expected = [{'serverId': 'server-abc',
                     'groupId': 'group-def',
                     'entityId': 'entity-ghi'},
                    {'serverId': 'server-xyz',
                     'groupId': 'group-def',
                     'entityId': 'entity-uvw'}]

        def execute(query, data, consistency):
            if 'INSERT' in query:
                return defer.succeed(None)
            elif 'SELECT' in query:
                return defer.succeed(expected)
        self.client.execute.side_effect = execute

        def add_check(tenant_id, policy_id, entity_id, check_template):
            return defer.succeed('ch{}{}'.format(entity_id, policy_id))

        def add_alarm(tenant_id, policy_id, entity_id, check_id, alarm_template, nplan_id):
            return defer.succeed('al{}{}'.format(entity_id, policy_id))
        mock_add_alarm.side_effect = add_alarm
        mock_add_check.side_effect = add_check

        example_check_template = {
            'type': 'agent.plugin',
            'details': {'file': 'blah',
                        'args': 'blah'}
        }

        d = worker.apply_policy('101010', 'group-abc', 'policy1', example_check_template,
                                'ALARM DSL', 'npBlah')

        result = self.successResultOf(d)
        self.assertEqual(result, None)

        self.assertEqual(
            self.client.execute.mock_calls,
            [mock.call('SELECT * FROM servers WHERE "groupId"=:groupId;',
                       {'groupId': 'group-abc'},
                       1),
             mock.call(('INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", "checkId", '
                       'state) VALUES (:serverId, :policyId, :alarmId, :checkId, false);'),
                       {'checkId': 'chentity-ghipolicy1', 'serverId': 'server-abc',
                        'policyId': 'policy1', 'alarmId': 'alentity-ghipolicy1'},
                       1),
             mock.call(
                 ('INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", "checkId", state) '
                  'VALUES (:serverId, :policyId, :alarmId, :checkId, false);'),
                 {'checkId': 'chentity-uvwpolicy1', 'serverId': 'server-xyz',
                  'policyId': 'policy1', 'alarmId': 'alentity-uvwpolicy1'},
                 1)])
