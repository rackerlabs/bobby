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
    def test_create_group(self, cass):
        """Test BobbyWorker.create_group."""
        expected = {'groupId': 'group-abc',
                    'tenantId': '101010',
                    'notification': 'notification-def',
                    'notificationPlan': 'notificationPlan-ghi'}

        self.maas_client.add_notification_and_plan.return_value = defer.succeed(
            (expected['notification'], expected['notificationPlan']))
        cass.create_group.return_value = defer.succeed(expected)

        w = worker.BobbyWorker(self.client)
        d = w.create_group(expected['tenantId'], expected['groupId'])

        result = self.successResultOf(d)
        self.assertEqual(result, expected)

        self.maas_client.add_notification_and_plan.assert_called_once_with()
        cass.create_group.assert_called_once_with(
            self.client, '101010', 'group-abc', 'notification-def', 'notificationPlan-ghi')

    @mock.patch('bobby.worker.cass')
    def test_delete_group(self, cass):
        """Test BobbyWorker.delete_group."""
        cass.get_group_by_id.return_value = defer.succeed({
            'notification': 'notification-abc',
            'notificationPlan': 'notificationPlan-def'})
        self.maas_client.remove_notification_and_plan.return_value = defer.succeed(None)
        cass.delete_group.return_value = defer.succeed(None)

        w = worker.BobbyWorker(self.client)
        d = w.delete_group('tenant-abc', 'group-def')
        self.successResultOf(d)

        cass.get_group_by_id.assert_called_once_with(self.client, 'tenant-abc', 'group-def')
        self.maas_client.remove_notification_and_plan.assert_called_once_with(
            'notification-abc', 'notificationPlan-def')
        cass.delete_group.assert_called_once_with(
            self.client, 'tenant-abc', 'group-def')

    @mock.patch('bobby.worker.cass')
    def test_create_server(self, cass):
        cass.get_server_by_server_id.return_value = defer.succeed({
            'serverId': 'server-abc', 'entityId': 'entity-abc'})
        cass.get_group_by_id.return_value = defer.succeed({
            'notificationPlan': 'plan-xyz'})
        cass.get_policies_by_group_id.return_value = defer.succeed([{
            'policyId': 'policy-abc',
            'checkTemplate': 'check-abc',
            'alarmTemplate': 'alarm-def'}])
        self.maas_client.add_check.return_value = defer.succeed({'id': 'check-xyz'})
        self.maas_client.add_alarm.return_value = defer.succeed({'id': 'alarm-xyz'})

        cass.create_server.return_value = defer.succeed(None)
        self.maas_client.create_entity.return_value = defer.succeed('entity-abc')
        server = {'uri': 'http://example.com/server-abc'}

        w = worker.BobbyWorker(self.client)
        d = w.create_server('tenant-abc', 'group-def', server)
        self.successResultOf(d)

        self.maas_client.create_entity.assert_called_once_with(server)
        cass.create_server.assert_called_once_with(
            self.client, 'tenant-abc', server['uri'], 'entity-abc', 'group-def')

        cass.get_server_by_server_id.assert_called_once_with('http://example.com/server-abc')
        cass.register_policy_on_server.assert_called_once_with(self.client, 'policy-abc', 'server-abc', 'alarm-xyz', 'check-xyz')

    @mock.patch('bobby.worker.cass')
    def test_delete_server(self, cass):
        cass.delete_server.return_value = defer.succeed(None)
        cass.get_server_by_server_id.return_value = defer.succeed({
            'serverId': 'server-abc', 'entityId': 'entity-abc'})
        self.maas_client.delete_entity.return_value = defer.succeed(None)

        w = worker.BobbyWorker(self.client)
        d = w.delete_server('tenant-abc', 'group-def', 'server-abc')
        self.successResultOf(d)

        cass.get_server_by_server_id.assert_called_once_with(
            self.client, 'tenant-abc', 'group-def', 'server-abc')
        self.maas_client.delete_entity.assert_called_once_with('entity-abc')
        cass.delete_server.assert_called_once_with(
            self.client, 'tenant-abc', 'group-def', 'server-abc')

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
                if 'groups' in query:
                    return defer.succeed([{
                        'groupId': 'group-abc',
                        'notificationPlan': 'plan-abc'}])
                elif 'policies' in query:
                    return defer.succeed(expected)
        self.client.execute.side_effect = execute

        w = worker.BobbyWorker(self.client)
        d = w.apply_policies_to_server('101010', 'group-abc', 'server1', 'enOne')
        result = self.successResultOf(d)
        self.assertEqual(result, None)

        self.assertEqual(self.client.execute.mock_calls, [
            mock.call(
                'SELECT * FROM groups WHERE "tenantId"=:tenantId AND "groupId"=:groupId;',
                {'groupId': 'group-abc', 'tenantId': '101010'},
                1),
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
