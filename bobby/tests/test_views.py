# Copyright 2013 Rackspace, Inc.
"""Tests for bobby.views."""
import json
import StringIO

import mock
from twisted.internet import defer
from twisted.trial import unittest
from twisted.web.test.requesthelper import DummyRequest

from bobby import views
from bobby.worker import BobbyWorker


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

        self.worker = mock.create_autospec(BobbyWorker)
        self.bobby._worker = self.worker

    def test_create_server(self):
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
        self.worker.create_server.return_value = defer.succeed(server)

        request_json = {
            'server': {
                'id': 'server-abc'
            }
        }
        request = BobbyDummyRequest('/101010/groups/group-uvw/servers/',
                                    content=json.dumps(request_json))
        request.method = 'POST'

        d = self.bobby.create_server(request, '101010', server['groupId'])

        self.successResultOf(d)
        result = json.loads(request.written[0])
        self.assertEqual(result, expected)

        self.worker.create_server.assert_called_once_with(
            '101010', 'group-uvw', request_json['server'])

    def test_delete_server(self):
        """Deletes a server and returns 402."""
        self.worker.delete_server.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz/servers/opqrst')
        request.method = 'DELETE'
        d = self.bobby.delete_server(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        self.worker.delete_server.assert_called_once_with(
            '101010', 'uvwxyz', 'opqrst')

    def test_create_group(self):
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
        self.worker.create_group.return_value = defer.succeed(group)

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
        self.worker.create_group.assert_called_once_with('010101', 'uvwxyz')

    def test_delete_group(self):
        """Deletes a server, returning a 204."""
        self.worker.delete_group.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz')
        d = self.bobby.delete_group(request, '101010', 'uvwxyz')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        self.worker.delete_group.assert_called_once_with('101010', 'uvwxyz')

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

        self.worker.execute_policy.assert_called_once_with('policy-abcdef')

    @mock.patch('bobby.cass.check_quorum_health')
    @mock.patch('bobby.cass.alter_alarm_state')
    def test_alarm_still_healthy(self, alter_alarm_state, check_quorum_health):
        """Updates the status of an alarm for a server, but still sees the group as healthy."""
        alter_alarm_state.return_value = defer.succeed(('policy-abcdef', 'server-abc'))
        check_quorum_health.return_value = defer.succeed(False)

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

        self.assertFalse(self.worker.execute_policy.called)


class TestCreatePolicy(ViewTest):
    """Test POST /{tenantId}/groups/{groupId}/policies"""

    @mock.patch('bobby.cass.create_policy')
    def test_create_policy(self, create_policy):
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


class TestDeletePolicy(ViewTest):
    """Test DELETE /{tenantId}/groups/{groupId}/policiess/{policyId}"""

    @mock.patch('bobby.cass.delete_policy')
    def test_delete_policy(self, delete_policy):
        """Deletes a policy and returns 402."""
        delete_policy.return_value = defer.succeed(None)

        request = BobbyDummyRequest('/101010/groups/uvwxyz/policies/opqrst')
        d = self.bobby.delete_policy(request, '101010', 'uvwxyz', 'opqrst')

        self.successResultOf(d)
        self.assertEqual(request.responseCode, 204)
        delete_policy.assert_called_once_with(self.db, 'uvwxyz', 'opqrst')
