"""Tests for bobby.worker."""
import json

import mock
from twisted.internet import defer
from twisted.trial import unittest
from silverberg.client import CQLClient

from bobby import worker
from bobby.ele import MaasClient


class TestBobbyWorker(unittest.TestCase):
    """Test bobby.worker.BobbyWorker."""

    def setUp(self):
        """Mock CQLClient and MaasClient."""
        self.client = mock.create_autospec(CQLClient)

        self.maas_client = mock.create_autospec(MaasClient)
        patcher = mock.patch('bobby.worker.MaasClient')
        self.addCleanup(patcher.stop)
        _MaasClient = patcher.start()
        _MaasClient.return_value = self.maas_client

    @mock.patch('bobby.worker.cass')
    def test_create_server(self, cass):
        cass.create_server.return_value = defer.succeed(None)
        self.maas_client.create_entity.return_value = defer.succeed('entity-abc')
        server = {'uri': 'http://example.com/server-abc'}

        w = worker.BobbyWorker(self.client)
        d = w.create_server('tenant-abc', 'group-def', server)
        self.successResultOf(d)

        self.maas_client.create_entity.assert_called_once_with(server)
        cass.create_server.assert_called_once_with(
            self.client, 'tenant-abc', server['uri'], 'entity-abc', 'group-def')

    @mock.patch('bobby.worker.MaasClient')
    def test_apply_policies_to_server(self, FakeMaasClient):
        """Test BobbyWorker.apply_policies_to_server."""
        maas_client = mock.create_autospec(MaasClient)
        FakeMaasClient.return_value = maas_client
        new_check = {
            u'created_at': 1,
            u'details': {u'file': u'blah',
                         u'args': u'blah'},
            u'disabled': False,
            u'id': u'check-abc',
            u'label': u'Test check 1',
            u'period': 100,
            u'type': u'agent.plugin'}

        def add_check(*args):
            return defer.succeed(new_check)
        maas_client.add_check.side_effect = add_check

        new_alarm = {
            "id": "alAAAA",
            "check_id": "chAAAA",
            "criteria": "if (metric[\"duration\"] >= 2) { return new AlarmStatus(OK); } return new AlarmStatus(CRITICAL);"}

        def add_alarm(*args):
            return defer.succeed(new_alarm)
        maas_client.add_alarm.side_effect = add_alarm

        example_check_template = json.dumps({
            'type': 'agent.plugin',
            'details': {'file': 'blah',
                        'args': 'blah'}
        })
        self.client.execute.return_value = defer.succeed(None)

        w = worker.BobbyWorker(self.client)
        d = w.add_policy_to_server('t1', 'p1', 's1', 'enOne',
                                   example_check_template, "ALARM_DSL", "npBlah")

        result = self.successResultOf(d)
        self.assertEqual(result, None)

        maas_client.add_check.assert_called_once_with(
            'p1', 'enOne',
            '{"type": "agent.plugin", "details": {"args": "blah", "file": "blah"}}')

        self.client.execute.assert_called_once_with(
            'INSERT INTO serverpolicies ("serverId", "policyId", "alarmId", '
            '"checkId", state) VALUES (:serverId, :policyId, :alarmId, '
            ':checkId, false);',
            {'checkId': u'check-abc', 'serverId': 's1', 'policyId': 'p1',
             'alarmId': 'alAAAA'},
            1)

    @mock.patch('bobby.worker.MaasClient')
    def test_create_group(self, FakeMaasClient):
        """Test BobbyWorker.create_group."""
        maas_client = mock.create_autospec(MaasClient)
        maas_client._endpoint = 'http://0.0.0.0/'
        maas_client._auth_token = 'auth-xyz'
        maas_client.add_notification_and_plan.return_value = defer.succeed(
            ('notification-xyz', 'notificationPlan-abc'))
        FakeMaasClient.return_value = maas_client

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

        w = worker.BobbyWorker(self.client)
        d = w.create_group('101010', 'g1')

        result = self.successResultOf(d)
        self.assertEqual(result, expected)

        maas_client.add_notification_and_plan.assert_called_once_with()
        calls = [
            mock.call(
                'INSERT INTO groups ("tenantId", "groupId", "notification", '
                '"notificationPlan") VALUES (:tenantId, :groupId, '
                ':notification, :notificationPlan);',
                {'notificationPlan': 'notificationPlan-abc',
                 'notification': 'notification-xyz',
                 'groupId': '101010',
                 'tenantId': 'g1'},
                1),
            mock.call(
                'SELECT * FROM groups WHERE "tenantId"=:tenantId AND '
                '"groupId"=:groupId;',
                {'groupId': '101010', 'tenantId': 'g1'}, 1)]
        self.assertEqual(self.client.execute.mock_calls, calls)

    @mock.patch('bobby.worker.MaasClient')
    def test_add_policy_to_server(self, FakeMaasClient):
        """ Basic success case """
        maas_client = mock.create_autospec(MaasClient)
        FakeMaasClient.return_value = maas_client
        new_check = {
            u'created_at': 1,
            u'details': {u'file': u'blah',
                         u'args': u'blah'},
            u'disabled': False,
            u'id': u'check-abc',
            u'label': u'Test check 1',
            u'period': 100,
            u'type': u'agent.plugin'}

        def add_check(*args):
            return defer.succeed(new_check)
        maas_client.add_check.side_effect = add_check

        new_alarm = {
            "id": "alAAAA",
            "check_id": "chAAAA",
            "criteria": "if (metric[\"duration\"] >= 2) { return new AlarmStatus(OK); } return new AlarmStatus(CRITICAL);"}

        def add_alarm(*args):
            return defer.succeed(new_alarm)
        maas_client.add_alarm.side_effect = add_alarm

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

        w = worker.BobbyWorker(self.client)
        d = w.apply_policies_to_server('101010', 'group-abc', 'server1', 'enOne', 'npBlah')
        result = self.successResultOf(d)
        self.assertEqual(result, None)

        self.assertEqual(self.client.execute.mock_calls, [
            mock.call(
                'SELECT * FROM policies WHERE "groupId"=:groupId;',
                {'groupId': 'group-abc'}, 1),
            mock.call(
                'INSERT INTO serverpolicies ("serverId", "policyId", '
                '"alarmId", "checkId", state) VALUES (:serverId, :policyId, '
                ':alarmId, :checkId, false);',
                {'checkId': u'check-abc', 'serverId': 'server1',
                 'policyId': 'policy-abc', 'alarmId': 'alAAAA'},
                1),
            mock.call(
                'INSERT INTO serverpolicies ("serverId", "policyId", '
                '"alarmId", "checkId", state) VALUES (:serverId, :policyId, '
                ':alarmId, :checkId, false);',
                {'checkId': u'check-abc', 'serverId': 'server1',
                 'policyId': 'policy-xyz', 'alarmId': 'alAAAA'},
                1)])
