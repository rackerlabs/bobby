"""Tests for bobby.worker."""
import json

import mock
from twisted.internet import defer
from twisted.trial import unittest
from silverberg.client import CQLClient

from bobby import worker
from bobby.ele import MaasClient


class _WorkerTestCase(unittest.TestCase):
    """Abstract DB test case."""

    def setUp(self):
        """Patch CQLClient."""
        self.client = mock.create_autospec(CQLClient)


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

    @mock.patch('bobby.worker.ele.MaasClient')
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

        example_check_template = json.dumps({
            'type': 'agent.plugin',
            'details': {'file': 'blah',
                        'args': 'blah'}
        })
        self.client.execute.return_value = defer.succeed(None)

        d = worker.add_policy_to_server(self.client, 't1', 'p1', 's1', 'enOne',
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


class TestCreateGroup(_WorkerTestCase):
    """ Test that we can add a policy to a server """

    @mock.patch('bobby.worker.ele.MaasClient')
    def test_create_group(self, FakeMaasClient):
        """ Basic success case """
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

        d = worker.create_group(self.client, '101010', 'g1')

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


class TestAddServer(_WorkerTestCase):
    """ Test that we can add a server (which will add multiple policies) """

    @mock.patch('bobby.worker.ele.MaasClient')
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

        d = worker.apply_policies_to_server(self.client, '101010', 'group-abc', 'server1', 'enOne', 'npBlah')
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


class TestAddPolicy(_WorkerTestCase):
    """ Test that we can add a server (which will add multiple policies) """

    @mock.patch('bobby.worker.ele.MaasClient')
    def test_add_policy(self, FakeMaasClient):
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

        example_check_template = {
            'type': 'agent.plugin',
            'details': {'file': 'blah',
                        'args': 'blah'}
        }

        d = worker.apply_policy(self.client, '101010', 'group-abc', 'policy1', example_check_template,
                                'ALARM DSL', 'npBlah')

        result = self.successResultOf(d)
        self.assertEqual(result, None)

        self.assertEqual(self.client.execute.mock_calls, [
            mock.call(
                'SELECT * FROM servers WHERE "groupId"=:groupId;',
                {'groupId': 'group-abc'},
                1),
            mock.call(
                'INSERT INTO serverpolicies ("serverId", "policyId", '
                '"alarmId", "checkId", state) VALUES (:serverId, :policyId, '
                ':alarmId, :checkId, false);',
                {'checkId': u'check-abc', 'serverId': 'server-abc',
                 'policyId': 'policy1', 'alarmId': 'alAAAA'},
                1),
            mock.call(
                'INSERT INTO serverpolicies ("serverId", "policyId", '
                '"alarmId", "checkId", state) VALUES (:serverId, :policyId, '
                ':alarmId, :checkId, false);',
                {'checkId': u'check-abc', 'serverId': 'server-xyz',
                 'policyId': 'policy1', 'alarmId': 'alAAAA'},
                1)])
