# Copyright 2013 Rackspace, Inc.
"""Tests for bobby.views."""
import json
import StringIO

import mock
from twisted.internet import defer
from twisted.trial import unittest
from twisted.web.test.requesthelper import DummyRequest

from bobby import views


class BobbyDummyRequest(DummyRequest):
    """Dummy request object."""

    def __init__(self, postpath, session=None, content=''):
        super(BobbyDummyRequest, self).__init__(postpath, session)
        self.content = StringIO.StringIO()
        self.content.write(content)
        self.content.seek(0)
        self.clientproto = 'HTTP/1.1'

    def URLPath(self):
        """Fake URLPath object."""
        FakeURLPath = mock.Mock(spec=['path'])
        FakeURLPath.path = self.postpath
        return FakeURLPath


class ViewTest(unittest.TestCase):
    """A TestCase for testing views."""

    def setUp(self):
        self.db = mock.Mock()
        self.bobby = views.Bobby(self.db)


class TestGetGroups(ViewTest):
    """Test GET /{tenantId}/groups"""

    @mock.patch('bobby.cass.get_groups_by_tenant_id')
    def test_get_groups(self, get_groups_by_tenant_id):
        """Returns application/json of all groups."""
        groups = [
            {'groupId': 'abcdef',
             'links': [
                 {
                     'href': '/101010/groups/abcdef',
                     'rel': 'self'
                 }
             ],
             'notification': 'notification-ghi',
             'notificationPlan': 'notificationPlan-jkl',
             'tenantId': '101010'
             },

            {'groupId': 'fedcba',
             'links': [
                 {
                     'href': '/101010/groups/fedcba',
                     'rel': 'self'
                 }
             ],
             'notification': 'notification-igh',
             'notificationPlan': 'notificationPlan-lkj',
             'tenantId': '101010'
             }
        ]
        expected = {'groups': groups}
        get_groups_by_tenant_id.return_value = defer.succeed(groups)

        request = BobbyDummyRequest('/101010/groups')
        d = self.bobby.get_groups(request, '101010')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)
        get_groups_by_tenant_id.assert_called_once_with(self.db, '101010')


class TestCreateGroup(ViewTest):
    """Test POST /{tenantId}/groups"""

    @mock.patch('bobby.cass.create_group')
    def test_create_group(self, create_group):
        """POST to /{tenantId}/groups creates a new group."""
        expected = {
            'groupId': 'uvwxyz',
            'links': [{
                'href': '/101010/groups/uvwxyz',
                'rel': 'self'
            }],
            'notification': 'notification-abc',
            'notificationPlan': 'notification-def',
            'tenantId': 'tenant-ghi'
        }
        group = expected.copy()
        del group['links']
        create_group.return_value = defer.succeed(group)

        request_json = {
            'groupId': 'uvwxyz',
            'notification': 'notification-abc',
            'notificationPlan': 'notification-def'
        }
        request = BobbyDummyRequest('/101010/groups/',
                                    content=json.dumps(request_json))
        request.method = 'POST'

        d = self.bobby.create_group(request, '010101')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)
        create_group.assert_called_once_with(
            self.db, '010101', 'uvwxyz', 'notification-abc', 'notification-def')


class TestGetGroup(ViewTest):
    """Test GET /{tenantId}/groups/{groupId}"""

    @mock.patch('bobby.cass.get_group_by_id')
    def test_get_group(self, get_group_by_id):
        """Returns application/json of group representation."""
        expected = {
            'groupId': 'uvwxyz',
            'links': [{
                'href': '/101010/groups/uvwxyz',
                'rel': 'self'
            }],
            'notification': 'notification-abc',
            'notificationPlan': 'notification-def',
            'tenantId': 'tenant-ghi'
        }
        group = expected.copy()
        del group['links']
        get_group_by_id.return_value = defer.succeed(group)

        request = BobbyDummyRequest('/101010/groups/uvwxyz')
        d = self.bobby.get_group(request, '101010', 'uvwxyz')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestDeleteGroup(ViewTest):
    """Test DELETE /{tenantId}/groups/{groupId}"""

    @mock.patch('bobby.cass.delete_group')
    def test_delete_group(self, delete_group):
        """Deletes a server, returning a 204."""
        delete_group.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz')
        d = self.bobby.delete_group(request, '101010', 'uvwxyz')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        delete_group.assert_called_once_with(self.db, '101010', 'uvwxyz')


class TestGetServers(ViewTest):
    """Test GET /{tenantId}/groups/{groupId}."""

    @mock.patch('bobby.cass.get_servers_by_group_id')
    def test_get_servers(self, get_servers_by_group_id):
        """Returns application/json of all servers owned by a group."""
        servers = [
            {'entityId': 'entity-abc',
             'groupId': 'group-def',
             'links': [
                 {
                     'href': '/101010/groups/group-def/servers/server-ghi',
                     'rel': 'self'
                 }
             ],
             'serverId': 'server-ghi'},
            {'entityId': 'entity-jkl',
             'groupId': 'group-def',
             'links': [
                 {
                     'href': '/101010/groups/group-def/servers/server-mno',
                     'rel': 'self'
                 }
             ],
             'serverId': 'server-mno'},
        ]
        expected = {'servers': servers}
        get_servers_by_group_id.return_value = defer.succeed(servers)

        request = BobbyDummyRequest('/101010/groups/group-def/servers')
        d = self.bobby.get_servers(request, '101010', 'group-def')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestCreateServer(ViewTest):
    """Test POST /{tenantId}/groups"""

    @mock.patch('bobby.cass.create_server')
    def test_create_server(self, create_server):
        """POSTing application/json creates a server."""
        expected = {
            'entityId': 'entity-xyz',
            'groupId': 'group-uvw',
            'links': [
                {
                    'href': '/101010/groups/group-uvw/servers/server-rst',
                    'rel': 'self'
                }
            ],
            'serverId': 'server-rst',
        }
        server = expected.copy()
        del server['links']
        create_server.return_value = defer.succeed(server)

        request_json = {
            'entityId': 'entity-xyz',
            'serverId': 'server-rst',
            'serverPolicies': [
                {'policyId': 'policy-xyz',
                 'alarmId': 'alarm-rst',
                 'checkId': 'check-uvw'}
            ]
        }
        request = BobbyDummyRequest('/101010/groups/group-uvw/servers/',
                                    content=json.dumps(request_json))
        request.method = 'POST'

        d = self.bobby.create_server(request, '101010', server['groupId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestGetServer(ViewTest):
    """Test GET /{tenantId}/groups/{groupId}/servers/{serverId}"""

    @mock.patch('bobby.cass.get_server_by_server_id')
    def test_get_server(self, get_server_by_server_id):
        """Return application/json server representation."""
        expected = {
            'entityId': 'entity-xyz',
            'groupId': 'group-uvw',
            'links': [
                {
                    'href': '/101010/groups/group-uvw/servers/server-rst',
                    'rel': 'self'
                }
            ],
            'serverId': 'server-rst'
        }
        server = expected.copy()
        del server['links']
        get_server_by_server_id.return_value = defer.succeed(server)

        request = BobbyDummyRequest('/101010/groups/group-uvw/servers/server-rst')
        d = self.bobby.get_server(request, '101010', server['groupId'], server['serverId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestDeleteServer(ViewTest):
    """Test DELETE /{tenantId}/groups/{groupId}/servers/{serverId}"""

    @mock.patch('bobby.cass.delete_server')
    def test_delete_server(self, delete_server):
        """Deletes a server and returns 402."""
        delete_server.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz/servers/opqrst')
        d = self.bobby.delete_server(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        delete_server.assert_called_once_with(self.db, '101010', 'uvwxyz', 'opqrst')


class TestGetPolicies(ViewTest):
    """Test GET /{tenantId}/groups/{groupId}."""

    @mock.patch('bobby.cass.get_policies_by_group_id')
    def test_get_policies(self, get_policies_by_group_id):
        """Returns application/json of all policies owned by a group."""
        policies = [
            {
                'alarmTemplate': '{alarmTemplate1}',
                'checkTemplate': '{checkTemplate1}',
                'groupId': '{groupId}',
                'links': [
                    {
                        'href':
                        '{url_root}/v1.0/{tenantId}/groups/{groupId}/policies/{policyId1}',
                        'rel': 'self'
                    }
                ],
                'policyId': '{policyId1}'
            },
            {
                'alarmTemplate': '{alarmTemplate2}',
                'checkTemplate': '{checkTemplate2}',
                'groupId': '{groupId}',
                'links': [
                    {
                        'href':
                        '{url_root}/v1.0/{tenantId}/groups/{groupId}/policies/{policyId2}',
                        'rel': 'self'
                    }
                ],
                'policyId': '{policyId2}'
            }
        ]
        expected = {'policies': policies}
        get_policies_by_group_id.return_value = defer.succeed(policies)

        request = BobbyDummyRequest('/101010/groups/group-def/policies')
        d = self.bobby.get_policies(request, '101010', 'group-def')

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestCreatePolicy(ViewTest):
    """Test POST /{tenantId}/groups/{groupId}/policies"""

    @mock.patch('bobby.cass.create_policy')
    def test_create_server(self, create_policy):
        """POSTing application/json creates a policy."""
        expected = {
            'alarmTemplate': 'alarm-template-jkl',
            'checkTemplate': 'check-template-ghi',
            'groupId': 'group-def',
            'links': [
                {
                    'href':
                    '/101010/groups/group-def/policies/policy-abc',
                    'rel': 'self'
                }
            ],
            'policyId': 'policy-abc'
        }
        policy = expected.copy()
        del policy['links']
        create_policy.return_value = defer.succeed(policy)

        request_json = {
            'alarmTemplate': 'alarm-template-jkl',
            'checkTemplate': 'check-template-ghi',
            'policyId': 'policy-abc'
        }
        request = BobbyDummyRequest('/101010/groups/group-def/policies/',
                                    content=json.dumps(request_json))
        request.method = 'POST'

        d = self.bobby.create_policy(request, '101010', policy['groupId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestGetPolicy(ViewTest):
    """Test GET /{tenantId}/groups/{groupId}/policies/{serverId}"""

    @mock.patch('bobby.cass.get_policy_by_policy_id')
    def test_get_server(self, get_policy_by_policy_id):
        """Return application/json policy representation."""
        expected = {
            'alarmTemplate': 'alarm-template-jkl',
            'checkTemplate': 'check-template-ghi',
            'groupId': 'group-def',
            'links': [
                {
                    'href':
                    '/101010/groups/group-def/policies/policy-abc',
                    'rel': 'self'
                }
            ],
            'policyId': 'policy-abc'
        }
        policy = expected.copy()
        del policy['links']
        get_policy_by_policy_id.return_value = defer.succeed(policy)

        request = BobbyDummyRequest('/101010/groups/group-def/policies/policy-abc')
        d = self.bobby.get_policy(request, '101010', policy['groupId'], policy['policyId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)


class TestDeletePolicy(ViewTest):
    """Test DELETE /{tenantId}/groups/{groupId}/policiess/{policyId}"""

    @mock.patch('bobby.cass.delete_policy')
    def test_delete_server(self, delete_policy):
        """Deletes a policy and returns 402."""
        delete_policy.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz/policies/opqrst')
        d = self.bobby.delete_policy(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        delete_policy.assert_called_once_with(self.db, 'uvwxyz', 'opqrst')


class TestAlarm(ViewTest):
    """Test MaaS alarm endpoint."""

    @mock.patch('bobby.cass.check_quorum_health')
    @mock.patch('bobby.cass.alter_alarm_state')
    def test_alarm(self, alter_alarm_state, check_quorum_health):
        """Updates the status of an alarm for a server."""
        alter_alarm_state.return_value = defer.succeed(('policy-abcdef', 'server-abc'))
        check_quorum_health.return_value = defer.succeed(True)

        data = {
            "event_id": "acOne:enOne:alOne:chOne:1326910500000:WARNING",
            "log_entry_id": "6da55310-4200-11e1-aaaf-cd4c8801b6b1",
            "details": {
                "target": None,
                "timestamp": 1326905540481,
                "metrics": {
                    "tt_firstbyte": {
                        "type": "I",
                        "data": 2,
                        "unit": "milliseconds"
                    },
                    "duration": {
                        "type": "I",
                        "data": 2,
                        "unit": "milliseconds"
                    },
                    "bytes": {
                        "type": "i",
                        "data": 17,
                        "unit": "bytes"
                    },
                    "tt_connect": {
                        "type": "I",
                        "data": 0,
                        "unit": "milliseconds"
                    },
                    "code": {
                        "type": "s",
                        "data": "200",
                        "unit": "unknown"
                    }
                },
                "state": "WARNING",
                "status": "warn.",
                "txn_id": "sometransaction",
                "collector_address_v4": "127.0.0.1",
                "collector_address_v6": None,
                "observations": [
                    {
                        "monitoring_zone_id": "mzOne",
                        "state": "WARNING",
                        "status": "warn.",
                        "timestamp": 1326905540481
                    }
                ]
            },
            "entity": {
                "id": "enOne",
                "label": "entity one",
                "ip_addresses": {
                    "default": "127.0.0.1"
                },
                "metadata": None,
                "managed": False,
                "uri": None,
                "agent_id": None,
                "created_at": 1326905540481,
                "updated_at": 1326905540481
            },
            "check": {
                "id": "chOne",
                "label": "ch a",
                "type": "remote.http",
                "details": {
                    "url": "http://www.foo.com",
                    "body": "b",
                    "method": "GET",
                    "follow_redirects": True,
                    "include_body": False
                },
                "monitoring_zones_poll": [
                    "mzOne"
                ],
                "timeout": 60,
                "period": 150,
                "target_alias": "default",
                "target_hostname": "",
                "target_resolver": "",
                "disabled": False,
                "metadata": None,
                "created_at": 1326905540481,
                "updated_at": 1326905540481
            },
            "alarm": {
                "id": "alOne",
                "label": "Alarm 1",
                "check_type": "remote.http",
                "check_id": None,
                "criteria": "if (metric[\"t\"] >= 2.1) { return WARNING } return WARNING",
                "disabled": False,
                "notification_plan_id": "npOne",
                "metadata": None,
                "created_at": 1326905540481,
                "updated_at": 1326905540481
            },
            "tenant_id": "91111"
        }
        request = BobbyDummyRequest('/alarm', content=json.dumps(data))
        request.method = 'POST'
        d = self.bobby.alarm(request)

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 200)

        alter_alarm_state.assert_called_once_with(
            self.db, data['alarm']['id'], data['details']['state'])
        check_quorum_health.assert_called_once_with(self.db, 'policy-abcdef')
